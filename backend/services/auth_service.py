"""
Authentication Service for SecureDevOps AI Platform
Handles JWT token generation, validation, password management, and user sessions
"""
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import uuid
import jwt
import bcrypt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, Depends

from config import settings
from models.user import (
    User, UserSession, APIToken, UserRole, UserStatus,
    LoginRequest, LoginResponse, UserResponse, 
    PasswordResetRequest, PasswordResetConfirm,
    UserCreate, UserPasswordChange
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with comprehensive security features"""
    
    def __init__(self):
        self.security = HTTPBearer()
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
        # Find user by username or email
        user = await User.find_one({
            "$or": [
                {"username": username_or_email.lower()},
                {"email": username_or_email.lower()}
            ]
        })
        
        if not user:
            return None
        
        # Check if account is locked (TEMPORARILY DISABLED)
        # if user.is_account_locked():
        #     raise HTTPException(
        #         status_code=status.HTTP_423_LOCKED,
        #         detail=f"Account is locked until {user.locked_until}. Please try again later."
        #     )

        # Check if account is active
        if user.status not in [UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or inactive"
            )

        # Verify password
        if not self.verify_password(password, user.hashed_password):
            # Increment failed attempts (TEMPORARILY DISABLED)
            # user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts (TEMPORARILY DISABLED)
            # if user.failed_login_attempts >= self.max_failed_attempts:
            #     user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration)
            
            # await user.save()
            return None

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        await user.save()
        
        return user
    
    async def login(self, login_data: LoginRequest, request: Request) -> LoginResponse:
        """Login user and create session"""
        user = await self.authenticate_user(
            login_data.username_or_email, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last_login time
        user.last_login = datetime.utcnow()
        await user.save()
        
        # Create tokens
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)
        
        # Create session
        expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        refresh_expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire)
        
        session = UserSession(
            user_id=user.id,
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
            from services.notification_service import notification_service
            user_agent = request.headers.get('user-agent', 'Unknown')
            parsed_ua = self._parse_user_agent(user_agent)
            await notification_service.send_login_alert(
                user_id=str(user.id),
                login_time=datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC"),
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
        
        if not session or session.refresh_expires_at < datetime.utcnow():
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
        session.expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        session.last_activity = datetime.utcnow()
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
            session.logged_out_at = datetime.utcnow()
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
            session.logged_out_at = datetime.utcnow()
            await session.save()
            count += 1
        
        return count
    
    # User Management
    
    async def create_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """Create new user account"""
        # Check if email exists
        existing_email = await User.find_one({"email": user_data.email})
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
            email=user_data.email,
            username=user_data.username.lower(),
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            organization=user_data.organization,
            department=user_data.department,
            status=UserStatus.PENDING_VERIFICATION,
            email_verification_token=secrets.token_urlsafe(32),
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
        user.last_password_change = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
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
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        await user.save()
        
        # TODO: Send email with reset link
        # await send_password_reset_email(user.email, reset_token)
        await self.send_password_reset_email(user.email, reset_token)
        
        return True
    
    async def reset_password(self, reset_data: PasswordResetConfirm) -> bool:
        """Reset password using token"""
        user = await User.find_one({
            "password_reset_token": reset_data.token,
            "password_reset_expires": {"$gt": datetime.utcnow()}
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
        user.last_password_change = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
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
        session.last_activity = datetime.utcnow()
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
            session.last_activity = datetime.utcnow()
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
        session.last_activity = datetime.utcnow()
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
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
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
        if api_token.expires_at and api_token.expires_at < datetime.utcnow():
            return None
        
        # Update usage stats
        api_token.last_used = datetime.utcnow()
        api_token.usage_count += 1
        await api_token.save()
        
        # Get user
        user = await User.get(api_token.user_id)
        return user

    # Email Services
    
    async def send_verification_email(self, email: str, verification_token: str):
        """Send email verification link"""
        try:
            from services.email_service import email_service
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
            from services.email_service import email_service
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
            from services.email_service import email_service
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
