"""
Authentication Service for ONYX Security Intelligence Platform
Handles JWT token generation, validation, password management, and user sessions
"""
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
import pyotp
import requests as requests_lib
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.oauth2 import id_token as google_id_token
from pymongo.errors import DuplicateKeyError

from config import settings
from models.user import (
    APIToken,
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    User,
    UserCreate,
    UserPasswordChange,
    UserResponse,
    UserRole,
    UserSession,
    UserStatus,
)

# Import timezone-aware UTC datetime helper
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with comprehensive security features"""
    
    def __init__(self):
        self.security = HTTPBearer()
        self.optional_security = HTTPBearer(auto_error=False)
        self.algorithm = "HS256"
        self.access_token_expire = settings.access_token_expire_minutes  # minutes
        self.refresh_token_expire = settings.refresh_token_expire_days  # days
        self.max_failed_attempts = settings.max_failed_login_attempts
        self.lockout_duration = settings.account_lockout_duration_minutes  # minutes
    
    # Password Management
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    # Token Management
    
    def create_access_token(self, user_id: str, additional_claims: Dict[str, Any] = None) -> str:
        """Create JWT access token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire),
            "type": "access",
            "jti": str(uuid.uuid4())  # Unique token ID
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, settings.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire),
            "type": "refresh",
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, settings.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    # User Authentication
    
    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user by username/email and password"""
        # Check if Beanie ODM is initialized (prevents CollectionWasNotInitialized crash)
        from database import beanie_initialized
        if not beanie_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not available. Please try again in a few moments."
            )
        
        # Find user by username or email
        user = await User.find_one({
            "$or": [
                {"username": username_or_email.lower()},
                {"email": username_or_email.lower()}
            ]
        })
        
        if not user:
            return None
        
        # Check if account is locked - BRUTE FORCE PROTECTION
        if user.is_account_locked():
            remaining_time = user.locked_until - utc_now()
            minutes_remaining = max(1, int(remaining_time.total_seconds() / 60))
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked due to too many failed attempts. Try again in {minutes_remaining} minutes."
            )

        # Check if account is active
        if user.status not in [UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or inactive"
            )

        # Verify password
        if not self.verify_password(password, user.hashed_password):
            # Increment failed attempts - BRUTE FORCE PROTECTION
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = utc_now() + timedelta(minutes=self.lockout_duration)
                logger.warning(f"Account {user.email} locked due to {user.failed_login_attempts} failed attempts")
            
            await user.save()
            return None

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = utc_now()
        await user.save()
        
        return user
    
    async def login(self, login_data: LoginRequest, request: Request):
        """Login user and create session - supports 2FA flow"""
        user = await self.authenticate_user(
            login_data.username_or_email, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Email verification gate - enforce only for PENDING_VERIFICATION
        # accounts so legacy/admin-activated (ACTIVE) users are not locked out.
        if (
            settings.require_email_verification
            and user.status == UserStatus.PENDING_VERIFICATION
            and not user.is_email_verified
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required. Please verify your email to log in, or request a new verification link."
            )

        # Check if 2FA is enabled for this user
        if user.two_factor_enabled:
            if not login_data.two_factor_code:
                # Return 2FA required response - user needs to provide code
                # Generate a temporary token for 2FA verification
                temp_token = self._generate_2fa_temp_token(user.id)
                return {
                    "requires_2fa": True,
                    "message": "Two-factor authentication required",
                    "temp_token": temp_token,
                    "user_email": self._mask_email(user.email)
                }
            
            # Verify 2FA code
            totp = pyotp.TOTP(user.two_factor_secret)
            is_valid = totp.verify(login_data.two_factor_code, valid_window=1)
            
            # Also check backup codes if TOTP fails
            if not is_valid and login_data.two_factor_code.upper() in user.two_factor_backup_codes:
                is_valid = True
                # Remove used backup code
                user.two_factor_backup_codes.remove(login_data.two_factor_code.upper())
                logger.info(f"Backup code used for user {user.email}")
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid two-factor authentication code"
                )
        
        # Update last_login time
        user.last_login = utc_now()
        await user.save()
        
        return await self._build_login_response(user, request)
    
    async def _build_login_response(self, user: User, request: Request) -> LoginResponse:
        """Create tokens + session for an authenticated user (shared by password and SSO logins)"""
        # Create tokens
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)
        
        # Create session
        expires_at = utc_now() + timedelta(minutes=self.access_token_expire)
        refresh_expires_at = utc_now() + timedelta(days=self.refresh_token_expire)
        
        session = UserSession(
            user_id=str(user.id),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            ip_address=getattr(request.client, 'host', None),
            user_agent=request.headers.get('user-agent'),
            device_info={
                "user_agent": request.headers.get('user-agent'),
                "accept_language": request.headers.get('accept-language'),
                "platform": self._extract_platform(request.headers.get('user-agent', ''))
            }
        )
        
        await session.insert()
        
        # Send login notification email (async, don't block login)
        try:
            from services.notifications.notification_service import notification_service
            user_agent = request.headers.get('user-agent', 'Unknown')
            parsed_ua = self._parse_user_agent(user_agent)
            await notification_service.send_login_alert(
                user_id=str(user.id),
                login_time=utc_now().strftime("%B %d, %Y at %I:%M %p UTC"),
                location="Unknown",  # Would need IP geolocation service
                device=parsed_ua.get("device", "Unknown"),
                browser=parsed_ua.get("browser", "Unknown"),
                ip_address=getattr(request.client, 'host', 'Unknown')
            )
        except Exception as notify_error:
            logger.warning(f"Failed to send login notification: {notify_error}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire * 60,  # Convert to seconds
            user=UserResponse(**user.dict())
        )
    
    # Google SSO
    
    def verify_google_id_token(self, id_token_str: str, nonce: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify a Google Identity Services ID token.
        Validates signature, audience, issuer, email_verified, and optional nonce.
        Returns the decoded claims dict or raises HTTPException.
        """
        if not settings.google_sso_enabled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Google SSO is not configured"
            )

        try:
            info = google_id_token.verify_oauth2_token(
                id_token_str,
                requests_lib.Request(),
                settings.google_client_id
            )
        except ValueError as e:
            logger.warning(f"Invalid Google ID token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google authentication token"
            )
        except Exception as e:
            logger.error(f"Google ID token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed"
            )

        # Issuer check (defense in depth; google-auth checks audience + signature)
        if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token issuer"
            )

        # Only accept email-verified Google accounts
        if not info.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Google account email is not verified"
            )

        email = (info.get("email") or "").lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token is missing an email address"
            )

        # Nonce check binds the token to the login page session that requested it,
        # preventing replay of captured ID tokens from other sessions.
        if nonce:
            if not info.get("nonce") or info.get("nonce") != nonce:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google token nonce mismatch"
                )

        # Optional domain allowlist
        allowed_domains = [d.strip().lower() for d in settings.google_allowed_domains.split(",") if d.strip()]
        if allowed_domains and email.split("@")[-1] not in allowed_domains:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your Google account domain is not allowed to sign in"
            )

        return info

    async def google_login(self, id_token_str: str, two_factor_code: Optional[str], request: Request, nonce: Optional[str] = None):
        """
        Log in (or auto-register) a user via a verified Google ID token.
        Returns LoginResponse, or a requires_2fa dict when the user has 2FA enabled.
        """
        # Check if Beanie ODM is initialized (prevents CollectionWasNotInitialized crash)
        from database import beanie_initialized
        if not beanie_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not available. Please try again in a few moments."
            )

        info = self.verify_google_id_token(id_token_str, nonce)
        email = (info.get("email") or "").lower()

        user = await User.find_one({"email": email})

        if not user:
            # Auto-provisioning is gated the same way as password registration,
            # so enabling SSO can never silently re-open self-registration.
            if not settings.allow_registration:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Registration is disabled. Contact your administrator for an account."
                )

            # Auto-provision a Google SSO account. Google already verified the email,
            # so the account is ACTIVE immediately with a non-guessable placeholder
            # password that can never authenticate (bcrypt hash of random bytes).
            username = await self._derive_username(email)
            user = User(
                email=email,
                username=username,
                full_name=(info.get("name") or "").strip() or username,
                hashed_password=self.hash_password(secrets.token_urlsafe(32)),
                auth_provider="google",
                role=UserRole.VIEWER,
                status=UserStatus.ACTIVE,
                is_email_verified=True,
                avatar_url=info.get("picture"),
                last_login=utc_now(),
            )
            try:
                await user.insert()
            except DuplicateKeyError:
                # Rare username race with concurrent SSO signups for the same email;
                # retry once with a random suffix.
                user.username = f"{username}{secrets.randbelow(9999)}"
                await user.insert()
            logger.info(f"Auto-provisioned Google SSO account for {email}")
            return await self._build_login_response(user, request)

        # Existing account: enforce the same gates as password login
        if user.status not in [UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or inactive"
            )
        if user.is_account_locked():
            remaining_time = user.locked_until - utc_now()
            minutes_remaining = max(1, int(remaining_time.total_seconds() / 60))
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked due to too many failed attempts. Try again in {minutes_remaining} minutes."
            )

        # Email verification gate: a PENDING_VERIFICATION account (e.g. self-registered,
        # admin-created) must verify its email before it can be bound to a Google login.
        if (
            settings.require_email_verification
            and user.status == UserStatus.PENDING_VERIFICATION
            and not user.is_email_verified
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required. Please verify your email to log in, or request a new verification link."
            )

        # 2FA gate: SSO identity is verified, but the user may still require a TOTP code
        if user.two_factor_enabled:
            if not two_factor_code:
                temp_token = self._generate_2fa_temp_token(user.id)
                return {
                    "requires_2fa": True,
                    "message": "Two-factor authentication required",
                    "temp_token": temp_token,
                    "user_email": self._mask_email(user.email)
                }

            totp = pyotp.TOTP(user.two_factor_secret)
            is_valid = totp.verify(two_factor_code, valid_window=1)
            if not is_valid and two_factor_code.upper() in user.two_factor_backup_codes:
                is_valid = True
                user.two_factor_backup_codes.remove(two_factor_code.upper())

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid two-factor authentication code"
                )

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = utc_now()
        await user.save()

        return await self._build_login_response(user, request)

    async def _derive_username(self, email: str) -> str:
        """Derive a unique username from an email address (e.g. jane.doe@x.com -> jane.doe)"""
        base = email.split("@")[0].strip().lower() or "user"
        base = "".join(c for c in base if c.isalnum() or c in "-_")[:30]
        # The username validator requires >= 3 chars; pad short local parts
        if len(base) < 3:
            base = f"{base}{secrets.randbelow(100)}" if base else f"user{secrets.randbelow(1000)}"
        candidate = base
        suffix = 1
        while True:
            try:
                existing = await User.find_one({"username": candidate})
            except Exception:
                return candidate
            if existing is None:
                return candidate
            suffix += 1
            candidate = f"{base}{suffix}"

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload["sub"]
        
        # Find and validate session
        session = await UserSession.find_one({
            "user_id": user_id,
            "refresh_token": refresh_token,
            "is_active": True
        })
        
        if not session or session.refresh_expires_at < utc_now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user
        user = await User.get(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not active"
            )
        
        # Create new access token
        new_access_token = self.create_access_token(user_id)
        
        # Update session
        session.access_token = new_access_token
        session.expires_at = utc_now() + timedelta(minutes=self.access_token_expire)
        session.last_activity = utc_now()
        await session.save()
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire * 60
        }
    
    async def logout(self, access_token: str) -> bool:
        """Logout user by invalidating session"""
        session = await UserSession.find_one({
            "access_token": access_token,
            "is_active": True
        })
        
        if session:
            session.is_active = False
            session.logged_out_at = utc_now()
            await session.save()
            return True
        
        return False
    
    async def logout_all_sessions(self, user_id: str) -> int:
        """Logout user from all sessions"""
        sessions = await UserSession.find({
            "user_id": user_id,
            "is_active": True
        }).to_list()
        
        count = 0
        for session in sessions:
            session.is_active = False
            session.logged_out_at = utc_now()
            await session.save()
            count += 1
        
        return count
    
    # User Management
    
    async def create_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """Create new user account"""
        # Normalize to lowercase so SSO lookups (which always lowercase) match
        normalized_email = str(user_data.email).lower()

        # Check if email exists
        existing_email = await User.find_one({"email": normalized_email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username exists
        existing_username = await User.find_one({"username": user_data.username.lower()})
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Create user
        user = User(
            email=normalized_email,
            username=user_data.username.lower(),
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            organization=user_data.organization,
            department=user_data.department,
            status=UserStatus.PENDING_VERIFICATION,
            email_verification_token=secrets.token_urlsafe(32),
            email_verification_expires=utc_now() + timedelta(hours=2),
            created_by=created_by,
            last_updated_by=created_by
        )
        
        await user.insert()
        return user
    
    async def change_password(self, user_id: str, password_data: UserPasswordChange) -> bool:
        """Change user password"""
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not self.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        user.hashed_password = self.hash_password(password_data.new_password)
        user.last_password_change = utc_now()
        user.updated_at = utc_now()
        
        await user.save()
        
        # Logout all sessions to force re-login
        await self.logout_all_sessions(user_id)
        
        return True
    
    async def request_password_reset(self, email: str) -> bool:
        """Request password reset"""
        user = await User.find_one({"email": email})
        if not user:
            # Don't reveal if email exists
            return True
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_expires = utc_now() + timedelta(hours=1)
        
        await user.save()
        
        # Send password reset email
        await self.send_password_reset_email(user.email, reset_token)
        
        return True
    
    async def reset_password(self, reset_data: PasswordResetConfirm) -> bool:
        """Reset password using token"""
        user = await User.find_one({
            "password_reset_token": reset_data.token,
            "password_reset_expires": {"$gt": utc_now()}
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        user.hashed_password = self.hash_password(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.last_password_change = utc_now()
        user.updated_at = utc_now()
        
        await user.save()
        
        # Logout all sessions
        await self.logout_all_sessions(user.id)
        
        return True
    
    # Token Dependency
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Get current user from JWT token"""
        token = credentials.credentials
        payload = self.verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = payload["sub"]
        user = await User.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        
        # Verify session is still active
        session = await UserSession.find_one({
            "user_id": user_id,
            "access_token": token,
            "is_active": True
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired"
            )
        
        # Update last activity
        session.last_activity = utc_now()
        await session.save()
        
        return user
    
    async def get_current_active_user(self, current_user: User = Depends(get_current_user)) -> User:
        """Get current active user (wrapper for dependency injection)"""
        return current_user

    async def get_optional_current_user(self, 
                                      credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
        """Get current user from JWT token (optional - for endpoints that allow anonymous access)"""
        if not credentials:
            return None
            
        try:
            token = credentials.credentials
            payload = self.verify_token(token, "access")
            
            if not payload:
                return None
            
            user_id = payload["sub"]
            user = await User.get(user_id)
            
            if not user or user.status != UserStatus.ACTIVE:
                return None
            
            # Verify session is still active
            session = await UserSession.find_one({
                "user_id": user_id,
                "access_token": token,
                "is_active": True
            })
            
            if not session:
                return None
            
            # Update last activity
            session.last_activity = utc_now()
            await session.save()
            
            return user
        except Exception:
            # If anything goes wrong with authentication, just return None for optional auth
            return None
    
    async def get_current_user_for_verification(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Get current user for verification-related operations (allows PENDING_VERIFICATION users)"""
        token = credentials.credentials
        payload = self.verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = payload["sub"]
        user = await User.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Allow both ACTIVE and PENDING_VERIFICATION users for verification operations
        if user.status not in [UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not accessible"
            )
        
        # Verify session is still active
        session = await UserSession.find_one({
            "user_id": user_id,
            "access_token": token,
            "is_active": True
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired"
            )
        
        # Update last activity
        session.last_activity = utc_now()
        await session.save()
        
        return user
    
    def require_role(self, required_role: UserRole):
        """Dependency to require specific user role"""
        def role_checker(current_user: User = Depends(self.get_current_user)) -> User:
            if current_user.role != required_role and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires {required_role} role"
                )
            return current_user
        return role_checker
    
    def require_permission(self, permission: str):
        """Dependency to require specific permission"""
        def permission_checker(current_user: User = Depends(self.get_current_user)) -> User:
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires {permission} permission"
                )
            return current_user
        return permission_checker
    
    # Utility Methods
    
    def _generate_2fa_temp_token(self, user_id: str) -> str:
        """Generate a temporary token for 2FA verification step"""
        # This token is short-lived (5 minutes) and only for 2FA verification
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "2fa_temp",
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, settings.secret_key, algorithm=self.algorithm)
    
    def _verify_2fa_temp_token(self, token: str) -> Optional[str]:
        """Verify 2FA temporary token and return user_id"""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            if payload.get("type") != "2fa_temp":
                return None
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _mask_email(self, email: str) -> str:
        """Mask email for privacy (e.g., t***@example.com)"""
        if not email or '@' not in email:
            return "***@***.***"
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = local[0] + "***"
        else:
            masked_local = local[0] + "***" + local[-1]
        return f"{masked_local}@{domain}"
    
    def _extract_platform(self, user_agent: str) -> str:
        """Extract platform from user agent"""
        user_agent = user_agent.lower()
        if 'windows' in user_agent:
            return 'Windows'
        elif 'mac' in user_agent:
            return 'macOS'
        elif 'linux' in user_agent:
            return 'Linux'
        elif 'android' in user_agent:
            return 'Android'
        elif 'iphone' in user_agent or 'ipad' in user_agent:
            return 'iOS'
        else:
            return 'Unknown'
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """Parse user agent to extract device and browser info"""
        ua_lower = user_agent.lower()
        
        # Detect browser
        browser = "Unknown Browser"
        if 'firefox' in ua_lower:
            browser = "Firefox"
        elif 'edg' in ua_lower:
            browser = "Microsoft Edge"
        elif 'chrome' in ua_lower:
            browser = "Chrome"
        elif 'safari' in ua_lower:
            browser = "Safari"
        elif 'opera' in ua_lower or 'opr' in ua_lower:
            browser = "Opera"
        
        # Detect device/platform
        device = "Unknown Device"
        if 'windows' in ua_lower:
            device = "Windows PC"
        elif 'macintosh' in ua_lower or 'mac os' in ua_lower:
            device = "Mac"
        elif 'linux' in ua_lower:
            device = "Linux PC"
        elif 'android' in ua_lower:
            device = "Android Device"
        elif 'iphone' in ua_lower:
            device = "iPhone"
        elif 'ipad' in ua_lower:
            device = "iPad"
        
        return {
            "browser": browser,
            "device": device,
            "platform": self._extract_platform(user_agent)
        }
    
    # API Token Management
    
    async def create_api_token(self, user_id: str, name: str, scopes: list = None, expires_in_days: int = None) -> str:
        """Create API token for programmatic access"""
        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        prefix = token[:8]
        
        expires_at = None
        if expires_in_days:
            expires_at = utc_now() + timedelta(days=expires_in_days)
        
        api_token = APIToken(
            user_id=user_id,
            name=name,
            token_hash=token_hash,
            prefix=prefix,
            scopes=scopes or [],
            expires_at=expires_at,
            created_by=user_id
        )
        
        await api_token.insert()
        return token
    
    async def verify_api_token(self, token: str) -> Optional[User]:
        """Verify API token and return associated user"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        api_token = await APIToken.find_one({
            "token_hash": token_hash,
            "is_active": True
        })
        
        if not api_token:
            return None
        
        # Check expiration
        if api_token.expires_at and api_token.expires_at < utc_now():
            return None
        
        # Update usage stats
        api_token.last_used = utc_now()
        api_token.usage_count += 1
        await api_token.save()
        
        # Get user
        user = await User.get(api_token.user_id)
        return user

    # Email Services
    
    async def send_verification_email(self, email: str, verification_token: str):
        """Send email verification link"""
        try:
            from services.notifications.service import email_service
            success = await email_service.send_verification_email(email, verification_token)
            
            if success:
                logger.info(f"Verification email sent to {email}")
            else:
                logger.error(f"Failed to send verification email to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            # Don't raise exception - user registration should still succeed
    
    async def send_password_reset_email(self, email: str, reset_token: str):
        """Send password reset link"""
        try:
            from services.notifications.service import email_service
            success = await email_service.send_password_reset_email(email, reset_token)
            
            if success:
                logger.info(f"Password reset email sent to {email}")
            else:
                logger.error(f"Failed to send password reset email to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            # Don't raise exception
    
    async def send_welcome_email(self, email: str, user_name: str):
        """Send welcome email to new users"""
        try:
            from services.notifications.service import email_service
            success = await email_service.send_welcome_email(email, user_name)
            
            if success:
                logger.info(f"Welcome email sent to {email}")
            else:
                logger.error(f"Failed to send welcome email to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            # Don't raise exception - user registration should still succeed


# Global instance
auth_service = AuthService()

