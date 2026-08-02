"""
User Models for ONYX Security Intelligence Platform
Handles user authentication, roles, and profile management
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field, validator
from pymongo import IndexModel

# Import shared enums and utilities from the single source of truth
from .base import UserRole, UserStatus, utc_now


class User(Document):
    """User document model"""
    
    # Basic Information
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: Indexed(EmailStr, unique=True)
    username: Indexed(str, unique=True)
    full_name: str
    
    # Authentication
    hashed_password: str
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    
    # Profile Information
    avatar_url: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = "UTC"
    
    # Security & Access
    is_email_verified: bool = False
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    
    # Two-Factor Authentication
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    two_factor_backup_codes: List[str] = Field(default_factory=list)
    
    # Preferences
    notification_preferences: dict = Field(default_factory=lambda: {
        "email_notifications": True,
        "push_notifications": True,
        "security_alerts": True,
        "product_updates": False,
        "marketing": False
    })

    # User settings (security, notifications, scanning, API preferences)
    settings: dict = Field(default_factory=dict)
    
    # Permissions & Projects
    project_permissions: List[str] = Field(default_factory=list)  # Project IDs user has access to
    api_tokens: List[str] = Field(default_factory=list)  # API token IDs
    
    # Audit Trail
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: Optional[str] = None  # User ID who created this user
    last_updated_by: Optional[str] = None
    
    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", 1)], unique=True),
            IndexModel([("username", 1)], unique=True),
            IndexModel([("role", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("created_at", -1)]),
            IndexModel([("last_login", -1)]),
        ]
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name"""
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Full name must be less than 100 characters')
        return v.strip()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        role_permissions = {
            UserRole.ADMIN: ["*"],  # All permissions
            UserRole.SECURITY_MANAGER: [
                "view_all_reports", "manage_scans", "manage_projects", 
                "view_analytics", "manage_notifications"
            ],
            UserRole.DEVELOPER: [
                "view_assigned_reports", "trigger_scans", "view_own_projects"
            ],
            UserRole.VIEWER: [
                "view_assigned_reports", "view_own_projects"
            ]
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return "*" in user_permissions or permission in user_permissions
    
    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False
    
    def can_access_project(self, project_id: str) -> bool:
        """Check if user can access a specific project"""
        if self.role == UserRole.ADMIN:
            return True
        if self.role == UserRole.SECURITY_MANAGER:
            return True
        return project_id in self.project_permissions


class UserSession(Document):
    """User session tracking for security and analytics"""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Session Info
    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime
    
    # Security Info
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[dict] = None
    location: Optional[dict] = None
    
    # Status
    is_active: bool = True
    logged_out_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=utc_now)
    last_activity: datetime = Field(default_factory=utc_now)
    
    class Settings:
        name = "user_sessions"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("session_id", 1)], unique=True),
            IndexModel([("access_token", 1)], unique=True),
            IndexModel([("refresh_token", 1)], unique=True),
            IndexModel([("expires_at", 1)]),
            IndexModel([("is_active", 1)]),
            IndexModel([("created_at", -1)]),
        ]


class APIToken(Document):
    """API tokens for programmatic access"""
    
    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str  # Human-readable name for the token
    
    # Token Info
    token_hash: str  # Hashed version of the actual token
    prefix: str  # First 8 characters for identification
    
    # Permissions & Scope
    scopes: List[str] = Field(default_factory=list)  # Specific permissions
    allowed_ips: List[str] = Field(default_factory=list)  # IP restrictions
    
    # Lifecycle
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    # Audit
    created_at: datetime = Field(default_factory=utc_now)
    created_by: str
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    
    class Settings:
        name = "api_tokens"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("token_id", 1)], unique=True),
            IndexModel([("token_hash", 1)], unique=True),
            IndexModel([("is_active", 1)]),
            IndexModel([("expires_at", 1)]),
            IndexModel([("created_at", -1)]),
        ]


# Pydantic Models for API Requests/Responses

class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.VIEWER
    organization: Optional[str] = None
    department: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        
        # Check for complexity
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Password must contain at least one uppercase letter, lowercase letter, digit, and special character')
        
        return v


class UserUpdate(BaseModel):
    """Model for updating user information"""
    full_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    notification_preferences: Optional[dict] = None


class NotificationPreferencesUpdate(BaseModel):
    """Model for updating notification preferences"""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    security_alerts: Optional[bool] = None
    product_updates: Optional[bool] = None
    marketing: Optional[bool] = None


class TwoFactorSetupResponse(BaseModel):
    """Model for 2FA setup response"""
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class TwoFactorVerifyRequest(BaseModel):
    """Model for 2FA verification"""
    code: str


class SessionResponse(BaseModel):
    """Model for session information"""
    session_id: str
    device: str
    browser: str
    location: str
    ip_address: str
    is_current: bool
    last_active: datetime
    created_at: datetime


class UserPasswordChange(BaseModel):
    """Model for changing password"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Password must contain at least one uppercase letter, lowercase letter, digit, and special character')
        
        return v


class UserResponse(BaseModel):
    """Model for user data in API responses"""
    id: str
    email: str
    username: str
    full_name: str
    role: UserRole
    status: UserStatus
    avatar_url: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    timezone: str
    is_email_verified: bool
    two_factor_enabled: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    notification_preferences: dict


class LoginRequest(BaseModel):
    """Model for login request"""
    username_or_email: str
    password: str
    remember_me: bool = False
    two_factor_code: Optional[str] = None  # Required if user has 2FA enabled


class LoginResponse(BaseModel):
    """Model for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    requires_2fa: bool = False  # Indicates if 2FA was required and verified


class TwoFactorRequiredResponse(BaseModel):
    """Response when 2FA is required but code not provided"""
    requires_2fa: bool = True
    message: str = "Two-factor authentication required"
    user_id: str  # Temporary token for 2FA verification


class PasswordResetRequest(BaseModel):
    """Model for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class EmailVerificationRequest(BaseModel):
    """Model for email verification request"""
    token: str


class TokenResponse(BaseModel):
    """Model for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Model for refresh token request"""
    refresh_token: str


class APITokenCreate(BaseModel):
    """Model for creating API tokens"""
    name: str
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = None  # None means no expiration
    allowed_ips: List[str] = Field(default_factory=list)


class APITokenResponse(BaseModel):
    """Model for API token response"""
    token_id: str
    name: str
    token: str  # Only returned on creation
    prefix: str
    scopes: List[str]
    expires_at: Optional[datetime]
    created_at: datetime
