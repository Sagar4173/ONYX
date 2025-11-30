"""
Authentication Routes for ONYX Security Intelligence Platform
Handles user registration, login, logout, password management
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError, BaseModel

from models.user import (
    User, UserRole, UserStatus, APIToken, UserSession,
    LoginRequest, LoginResponse, UserResponse,
    UserCreate, UserUpdate, UserPasswordChange,
    PasswordResetRequest, PasswordResetConfirm,
    EmailVerificationRequest, NotificationPreferencesUpdate,
    TwoFactorSetupResponse, TwoFactorVerifyRequest, SessionResponse,
    APITokenCreate, APITokenResponse, TokenResponse
)
from services.auth_service import auth_service
from services.email_service import email_service
from config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user)
):
    """
    Register a new user
    
    - **Admin users**: Can create users with any role
    - **Regular users**: Can only create Viewer accounts (self-registration)
    """
    # Check if registration is allowed
    if not settings.allow_registration and not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Please contact an administrator."
        )
    
    # Role restrictions
    if current_user:
        # Existing user creating another user
        if current_user.role != UserRole.ADMIN and user_data.role != UserRole.VIEWER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create users with elevated roles"
            )
        created_by = current_user.id
    else:
        # Self-registration - force to Viewer role
        user_data.role = UserRole.VIEWER
        created_by = None
    
    try:
        user = await auth_service.create_user(user_data, created_by)
        
        # Send email verification
        if user.email_verification_token:
            await auth_service.send_verification_email(user.email, user.email_verification_token)
        
        # Send welcome email for new users (not created by admin)
        if not current_user:  # Self-registration
            await auth_service.send_welcome_email(user.email, user.username or user.email.split('@')[0])
        
        return UserResponse(**user.dict())
        
    except ValidationError as e:
        # Return structured validation errors
        errors = []
        for error in e.errors():
            field = error['loc'][-1] if error['loc'] else 'field'
            message = error['msg']
            errors.append({"field": field, "message": message})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors}
        )
    except Exception as e:
        # Handle other exceptions
        error_msg = str(e)
        # If it's a ValueError from validators, extract clean message
        if "must be at least" in error_msg or "must be less than" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """
    Login user and create session
    
    Returns access token and refresh token for authentication
    """
    try:
        response = await auth_service.login(login_data, request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    """
    try:
        response = await auth_service.refresh_access_token(refresh_token)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
):
    """
    Logout current user session
    """
    success = await auth_service.logout(credentials.credentials)
    if success:
        return {"message": "Successfully logged out"}
    else:
        return {"message": "Session not found or already logged out"}


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Logout user from all sessions
    """
    count = await auth_service.logout_all_sessions(current_user.id)
    return {"message": f"Logged out from {count} sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get current user information
    """
    return UserResponse(**current_user.dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Update current user profile
    """
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    current_user.last_updated_by = current_user.id
    
    await current_user.save()
    
    return UserResponse(**current_user.dict())


# ===== NOTIFICATION PREFERENCES =====

@router.get("/me/notifications")
async def get_notification_preferences(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get current user's notification preferences
    """
    return current_user.notification_preferences


@router.put("/me/notifications")
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Update notification preferences
    """
    # Update only provided preferences
    update_data = preferences.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        current_user.notification_preferences[key] = value
    
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    return {
        "message": "Notification preferences updated",
        "preferences": current_user.notification_preferences
    }


# ===== TWO-FACTOR AUTHENTICATION =====

@router.post("/me/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Initialize 2FA setup - generates secret and QR code
    """
    import pyotp
    import secrets
    
    # Generate a new secret
    secret = pyotp.random_base32()
    
    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    
    # Store the secret temporarily (not enabled yet)
    current_user.two_factor_secret = secret
    current_user.two_factor_backup_codes = backup_codes
    await current_user.save()
    
    # Generate provisioning URI for QR code
    totp = pyotp.TOTP(secret)
    qr_code_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="ONYX"
    )
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_url=qr_code_url,
        backup_codes=backup_codes
    )


@router.post("/me/2fa/enable")
async def enable_two_factor(
    verify_data: TwoFactorVerifyRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Enable 2FA after verifying the code
    """
    import pyotp
    
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call /me/2fa/setup first."
        )
    
    # Verify the code
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(verify_data.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Enable 2FA
    current_user.two_factor_enabled = True
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    # Send email notification
    asyncio.create_task(email_service.send_2fa_enabled_email(
        email=current_user.email,
        user_name=current_user.full_name or current_user.username,
        enabled_at=datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    ))
    
    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/me/2fa/disable")
async def disable_two_factor(
    verify_data: TwoFactorVerifyRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Disable 2FA after verifying the code
    """
    import pyotp
    
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Verify the code or check backup codes
    totp = pyotp.TOTP(current_user.two_factor_secret)
    is_valid = totp.verify(verify_data.code, valid_window=1)
    
    # Check backup codes if TOTP fails
    if not is_valid and verify_data.code.upper() in current_user.two_factor_backup_codes:
        is_valid = True
        # Remove used backup code
        current_user.two_factor_backup_codes.remove(verify_data.code.upper())
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Disable 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_backup_codes = []
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    # Send email notification
    asyncio.create_task(email_service.send_2fa_disabled_email(
        email=current_user.email,
        user_name=current_user.full_name or current_user.username,
        disabled_at=datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    ))
    
    return {"message": "Two-factor authentication disabled successfully"}


@router.get("/me/2fa/status")
async def get_two_factor_status(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get 2FA status
    """
    return {
        "enabled": current_user.two_factor_enabled,
        "backup_codes_remaining": len(current_user.two_factor_backup_codes) if current_user.two_factor_enabled else 0
    }


# ===== SESSION MANAGEMENT =====

@router.get("/me/sessions")
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get all active sessions for current user
    """
    from user_agents import parse as parse_ua
    
    # Get current token to identify current session
    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    
    sessions = await UserSession.find({
        "user_id": current_user.id,
        "is_active": True
    }).to_list()
    
    result = []
    for session in sessions:
        # Parse user agent
        user_agent_str = session.user_agent or "Unknown"
        try:
            ua = parse_ua(user_agent_str)
            device = f"{ua.device.brand or ''} {ua.device.model or ua.device.family}".strip() or "Unknown Device"
            browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
        except:
            device = "Unknown Device"
            browser = "Unknown Browser"
        
        # Determine location
        location = "Unknown Location"
        if session.location:
            city = session.location.get("city", "")
            country = session.location.get("country", "")
            location = f"{city}, {country}".strip(", ") if city or country else "Unknown Location"
        
        result.append({
            "session_id": session.session_id,
            "device": device,
            "browser": browser,
            "location": location,
            "ip_address": session.ip_address or "Unknown",
            "is_current": session.access_token == current_token,
            "last_active": session.last_activity,
            "created_at": session.created_at
        })
    
    return result


@router.delete("/me/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Revoke a specific session
    """
    # Get current token to prevent revoking current session
    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    
    session = await UserSession.find_one({
        "session_id": session_id,
        "user_id": current_user.id,
        "is_active": True
    })
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.access_token == current_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke current session. Use logout instead."
        )
    
    session.is_active = False
    session.logged_out_at = datetime.utcnow()
    await session.save()
    
    return {"message": "Session revoked successfully"}


@router.delete("/me/sessions")
async def revoke_all_other_sessions(
    request: Request,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Revoke all sessions except the current one
    """
    # Get current token
    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    
    # Revoke all other sessions
    result = await UserSession.find({
        "user_id": current_user.id,
        "is_active": True,
        "access_token": {"$ne": current_token}
    }).update_many({
        "$set": {
            "is_active": False,
            "logged_out_at": datetime.utcnow()
        }
    })
    
    return {"message": f"Revoked {result.modified_count} other sessions"}


# ===== AVATAR UPLOAD =====

class AvatarUpdate(BaseModel):
    avatar_url: Optional[str] = ""  # Empty string or None to remove avatar

@router.post("/me/avatar")
async def upload_avatar(
    avatar_data: AvatarUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Update avatar URL (accepts base64, URL, or empty string to remove)
    """
    avatar_url = (avatar_data.avatar_url or "").strip()
    
    # Allow empty string to remove avatar
    if not avatar_url:
        current_user.avatar_url = None
        current_user.updated_at = datetime.utcnow()
        await current_user.save()
        return {
            "message": "Avatar removed successfully",
            "avatar_url": None
        }
    
    # Validate URL or base64
    if not avatar_url.startswith(("http://", "https://", "data:image/")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid avatar format. Provide a URL or base64 data URI."
        )
    
    # Limit base64 size (5MB max)
    if avatar_url.startswith("data:image/") and len(avatar_url) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar image too large. Maximum size is 5MB."
        )
    
    current_user.avatar_url = avatar_url
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    return {
        "message": "Avatar updated successfully",
        "avatar_url": avatar_url
    }


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Change current user password
    """
    success = await auth_service.change_password(current_user.id, password_data)
    if success:
        # Send email notification
        asyncio.create_task(email_service.send_password_changed_email(
            email=current_user.email,
            user_name=current_user.full_name or current_user.username,
            changed_at=datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
        ))
        return {"message": "Password changed successfully. Please log in again."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/request-password-reset")
async def request_password_reset(reset_request: PasswordResetRequest):
    """
    Request password reset via email
    """
    await auth_service.request_password_reset(reset_request.email)
    return {
        "message": "If the email address is registered, you will receive password reset instructions."
    }


@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm):
    """
    Reset password using reset token
    """
    success = await auth_service.reset_password(reset_data)
    if success:
        return {"message": "Password reset successfully. Please log in with your new password."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest):
    """
    Verify email address using verification token
    """
    # Find user with the token and check if not expired
    user = await User.find_one({
        "email_verification_token": request.token
    })
    
    if user:
        # Check if token has expired (if expiration is set)
        if user.email_verification_expires and datetime.utcnow() > user.email_verification_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired. Please request a new verification email."
            )
        
        # Token found and user is pending verification
        if user.status == UserStatus.PENDING_VERIFICATION and not user.is_email_verified:
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.utcnow()
            await user.save()
            return {"message": "Email verified successfully. Your account is now active."}
        
        # Token found but user is already verified
        elif user.is_email_verified:
            # Clear the old token since email is already verified
            user.email_verification_token = None
            user.email_verification_expires = None
            await user.save()
            return {"message": "Email is already verified. Your account is active."}
        
        # Token found but user has different status
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account verification failed. Please contact support."
            )
    
    # Invalid or expired token (token not found - could be old link after resend)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification link. Please request a new verification email."
    )


class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email"""
    email: str


@router.post("/resend-verification")
async def resend_verification_email(
    request_data: Optional[ResendVerificationRequest] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(auth_service.optional_security)
):
    """
    Resend email verification token
    
    Supports two modes:
    1. Authenticated: Uses the token to identify the user
    2. Unauthenticated: Uses the email from request body (for post-registration)
    
    Note: When a new verification email is sent, the old token becomes invalid.
    """
    import secrets
    from datetime import timedelta
    
    user = None
    
    # Try authenticated mode first
    if credentials and credentials.credentials:
        try:
            user = await auth_service.get_current_user_for_verification(credentials)
        except HTTPException:
            # Authentication failed, fall back to email-based lookup
            pass
    
    # Fall back to email-based lookup
    if not user and request_data and request_data.email:
        user = await User.find_one({"email": request_data.email.lower()})
        if not user:
            # Return error - email not found in system
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address. Please check the email or create a new account."
            )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for unauthenticated requests"
        )
    
    if user.is_email_verified:
        return {"message": "Email is already verified"}
    
    # Generate new verification token (this invalidates the old token)
    user.email_verification_token = secrets.token_urlsafe(32)
    user.email_verification_expires = datetime.utcnow() + timedelta(hours=2)
    await user.save()
    
    # Send verification email
    await auth_service.send_verification_email(
        user.email, 
        user.email_verification_token
    )
    
    return {"message": "Verification email sent successfully"}


@router.post("/test-email")
async def test_email_configuration(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Test email configuration by sending a test email to the current user
    Only available to admin users
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test email configuration"
        )
    
    try:
        from services.email_service import email_service
        
        # Test SMTP connection first
        connection_ok = await email_service.test_connection()
        if not connection_ok:
            return {
                "message": "Email connection test failed",
                "success": False,
                "error": "Could not connect to SMTP server"
            }
        
        # Send test email
        success = await email_service.send_email(
            to_email=current_user.email,
            subject="🧪 Test Email - ONYX Platform",
            html_body="""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4F46E5;">✅ Email Configuration Test</h2>
                <p>Congratulations! Your email configuration is working correctly.</p>
                <p>This test email was sent from the ONYX Platform.</p>
                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    Test performed at: {datetime.utcnow().isoformat()}
                </p>
            </body>
            </html>
            """.format(datetime=datetime)
        )
        
        if success:
            return {
                "message": f"Test email sent successfully to {current_user.email}",
                "success": True
            }
        else:
            return {
                "message": "Failed to send test email",
                "success": False
            }
            
    except Exception as e:
        return {
            "message": f"Email test failed: {str(e)}",
            "success": False,
            "error": str(e)
        }


# API Token Management

@router.post("/api-tokens", response_model=APITokenResponse)
async def create_api_token(
    token_data: APITokenCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Create API token for programmatic access
    """
    # Validate scopes
    allowed_scopes = [
        "read:reports", "write:reports", "read:scans", "write:scans",
        "read:projects", "write:projects", "read:analytics"
    ]
    
    invalid_scopes = [scope for scope in token_data.scopes if scope not in allowed_scopes]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {invalid_scopes}"
        )
    
    token = await auth_service.create_api_token(
        user_id=current_user.id,
        name=token_data.name,
        scopes=token_data.scopes,
        expires_in_days=token_data.expires_in_days
    )
    
    # Get the created token record
    api_token = await APIToken.find_one({
        "user_id": current_user.id,
        "name": token_data.name
    })
    
    return APITokenResponse(
        token_id=api_token.token_id,
        name=api_token.name,
        token=token,  # Only returned on creation
        prefix=api_token.prefix,
        scopes=api_token.scopes,
        expires_at=api_token.expires_at,
        created_at=api_token.created_at
    )


@router.get("/api-tokens")
async def list_api_tokens(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    List user's API tokens (without actual token values)
    """
    tokens = await APIToken.find({
        "user_id": current_user.id,
        "is_active": True
    }).to_list()
    
    return [
        {
            "token_id": token.token_id,
            "name": token.name,
            "prefix": token.prefix,
            "scopes": token.scopes,
            "expires_at": token.expires_at,
            "last_used": token.last_used,
            "usage_count": token.usage_count,
            "created_at": token.created_at
        }
        for token in tokens
    ]


@router.delete("/api-tokens/{token_id}")
async def revoke_api_token(
    token_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Revoke (delete) API token
    """
    token = await APIToken.find_one({
        "token_id": token_id,
        "user_id": current_user.id,
        "is_active": True
    })
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API token not found"
        )
    
    token.is_active = False
    token.revoked_at = datetime.utcnow()
    token.revoked_by = current_user.id
    await token.save()
    
    return {"message": "API token revoked successfully"}


# Admin Routes

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """
    List all users (Admin only)
    """
    query = {}
    if role:
        query["role"] = role
    if status:
        query["status"] = status
    
    users = await User.find(query).skip(skip).limit(limit).to_list()
    
    return [UserResponse(**user.dict()) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """
    Get specific user details (Admin only)
    """
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user.dict())


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """
    Update user details (Admin only)
    """
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    user.last_updated_by = current_user.id
    
    await user.save()
    
    return UserResponse(**user.dict())


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """
    Update user role (Admin only)
    """
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admins from removing their own admin role
    if user.id == current_user.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role"
        )
    
    user.role = new_role
    user.updated_at = datetime.utcnow()
    user.last_updated_by = current_user.id
    
    await user.save()
    
    return {"message": f"User role updated to {new_role}"}


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """
    Update user status (Admin only)
    """
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admins from suspending themselves
    if user.id == current_user.id and new_status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own account status"
        )
    
    user.status = new_status
    user.updated_at = datetime.utcnow()
    user.last_updated_by = current_user.id
    
    await user.save()
    
    # If user is suspended, logout all their sessions
    if new_status in [UserStatus.SUSPENDED, UserStatus.INACTIVE]:
        await auth_service.logout_all_sessions(user.id)
    
    return {"message": f"User status updated to {new_status}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """
    Delete user account (Admin only)
    """
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admins from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Logout all sessions
    await auth_service.logout_all_sessions(user.id)
    
    # Delete user (consider soft delete in production)
    await user.delete()
    
    return {"message": "User account deleted successfully"}
