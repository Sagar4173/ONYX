"""
Authentication Routes for SecureDevOps AI Platform
Handles user registration, login, logout, password management
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials

from models.user import (
    User, UserRole, UserStatus, APIToken,
    LoginRequest, LoginResponse, UserResponse,
    UserCreate, UserUpdate, UserPasswordChange,
    PasswordResetRequest, PasswordResetConfirm,
    EmailVerificationRequest,
    APITokenCreate, APITokenResponse, TokenResponse
)
from services.auth_service import auth_service
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
        
    except Exception as e:
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
    # First, try to find user with the token (regardless of status)
    user = await User.find_one({
        "email_verification_token": request.token
    })
    
    if user:
        # Token found and user is pending verification
        if user.status == UserStatus.PENDING_VERIFICATION and not user.is_email_verified:
            user.is_email_verified = True
            user.email_verification_token = None
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.utcnow()
            await user.save()
            return {"message": "Email verified successfully. Your account is now active."}
        
        # Token found but user is already verified
        elif user.is_email_verified:
            return {"message": "Email is already verified. Your account is active."}
        
        # Token found but user has different status
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account verification failed. Please contact support."
            )
    
    # No user found with this token - check if there's a verified user with this email pattern
    # This could happen if the token was already used and cleared
    if len(request.token) > 10:  # Basic token format check
        # Look for any users that might have been verified recently
        recently_verified_user = await User.find_one({
            "is_email_verified": True,
            "status": UserStatus.ACTIVE,
            "email_verification_token": None
        }, sort=[("updated_at", -1)])
        
        if recently_verified_user:
            # Check if this was updated recently (within last 5 minutes)
            time_diff = datetime.utcnow() - recently_verified_user.updated_at
            if time_diff.total_seconds() < 300:  # 5 minutes
                return {"message": "Email is already verified. Your account is active."}
    
    # Invalid or expired token
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token"
    )


@router.post("/resend-verification")
async def resend_verification_email(
    current_user: User = Depends(auth_service.get_current_user_for_verification)
):
    """
    Resend email verification token
    Allows both ACTIVE and PENDING_VERIFICATION users
    """
    if current_user.is_email_verified:
        return {"message": "Email is already verified"}
    
    # Generate new verification token
    import secrets
    current_user.email_verification_token = secrets.token_urlsafe(32)
    await current_user.save()
    
    # Send verification email
    await auth_service.send_verification_email(
        current_user.email, 
        current_user.email_verification_token
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
            subject="🧪 Test Email - SecureDevOps Platform",
            html_body="""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4F46E5;">✅ Email Configuration Test</h2>
                <p>Congratulations! Your email configuration is working correctly.</p>
                <p>This test email was sent from the SecureDevOps Platform.</p>
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
