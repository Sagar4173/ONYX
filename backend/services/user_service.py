"""
User Management Service for ONYX Security Intelligence Platform
Comprehensive user administration and profile management
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

# Helper function to get timezone-aware UTC datetime (replaces deprecated utc_now())
def utc_now() -> datetime:
    return datetime.now(timezone.utc)
from pymongo import DESCENDING
import hashlib
import secrets

from models.user import (
    User, UserRole, UserStatus, UserSession, APIToken,
    UserCreate, UserUpdate, UserPasswordChange, UserResponse,
    APITokenCreate, APITokenResponse
)
from services.auth_service import auth_service
from config import settings


class UserService:
    """Service for user management operations"""
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await User.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await User.find_one(User.email == email)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await User.find_one(User.username == username)
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List users with filtering, pagination, and search
        """
        query = {}
        
        # Apply filters
        if role:
            query["role"] = role
        if status:
            query["status"] = status
        
        # Search functionality
        if search:
            search_regex = {"$regex": search, "$options": "i"}
            query["$or"] = [
                {"username": search_regex},
                {"full_name": search_regex},
                {"email": search_regex},
                {"organization": search_regex}
            ]
        
        # Sort configuration
        sort_direction = DESCENDING if sort_order == "desc" else 1
        sort_field = sort_by if sort_by in ["created_at", "last_login", "username", "email"] else "created_at"
        
        # Execute queries
        total_query = User.find(query)
        users_query = User.find(query).sort([(sort_field, sort_direction)]).skip(skip).limit(limit)
        
        total = await total_query.count()
        users = await users_query.to_list()
        
        return {
            "users": [await self._user_to_response(user) for user in users],
            "total": total,
            "page": (skip // limit) + 1,
            "total_pages": (total + limit - 1) // limit,
            "has_next": skip + limit < total,
            "has_previous": skip > 0
        }
    
    async def update_user_profile(
        self, 
        user_id: str, 
        update_data: UserUpdate,
        updated_by: str
    ) -> UserResponse:
        """Update user profile information"""
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        user.updated_at = utc_now()
        user.last_updated_by = updated_by
        
        await user.save()
        return await self._user_to_response(user)
    
    async def change_password(
        self,
        user_id: str,
        password_data: UserPasswordChange
    ) -> bool:
        """Change user password"""
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not auth_service.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = auth_service.hash_password(password_data.new_password)
        user.last_password_change = utc_now()
        user.updated_at = utc_now()
        
        await user.save()
        
        # Logout all other sessions for security
        await auth_service.logout_all_sessions(user_id, exclude_current=True)
        
        return True
    
    async def update_user_role(
        self,
        user_id: str,
        new_role: UserRole,
        updated_by: str
    ) -> UserResponse:
        """Update user role (Admin only)"""
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.role = new_role
        user.updated_at = utc_now()
        user.last_updated_by = updated_by
        
        await user.save()
        return await self._user_to_response(user)
    
    async def update_user_status(
        self,
        user_id: str,
        new_status: UserStatus,
        updated_by: str
    ) -> UserResponse:
        """Update user status"""
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.status = new_status
        user.updated_at = utc_now()
        user.last_updated_by = updated_by
        
        await user.save()
        
        # If user is suspended/inactive, logout all sessions
        if new_status in [UserStatus.SUSPENDED, UserStatus.INACTIVE]:
            await auth_service.logout_all_sessions(user_id)
        
        return await self._user_to_response(user)
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        sessions = await UserSession.find(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).sort([("last_activity", DESCENDING)]).to_list()
        
        return [
            {
                "session_id": session.session_id,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "device_info": session.device_info,
                "location": session.location,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "expires_at": session.expires_at
            }
            for session in sessions
        ]
    
    async def revoke_user_session(
        self,
        user_id: str,
        session_id: str,
        revoked_by: str
    ) -> bool:
        """Revoke a specific user session"""
        session = await UserSession.find_one(
            UserSession.user_id == user_id,
            UserSession.session_id == session_id,
            UserSession.is_active == True
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.is_active = False
        session.logged_out_at = utc_now()
        await session.save()
        
        return True
    
    async def get_user_api_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API tokens for a user"""
        tokens = await APIToken.find(
            APIToken.user_id == user_id,
            APIToken.is_active == True
        ).sort([("created_at", DESCENDING)]).to_list()
        
        return [
            {
                "token_id": token.token_id,
                "name": token.name,
                "prefix": token.prefix,
                "scopes": token.scopes,
                "allowed_ips": token.allowed_ips,
                "expires_at": token.expires_at,
                "last_used": token.last_used,
                "usage_count": token.usage_count,
                "created_at": token.created_at
            }
            for token in tokens
        ]
    
    async def create_api_token(
        self,
        user_id: str,
        token_data: APITokenCreate,
        created_by: str
    ) -> APITokenResponse:
        """Create a new API token for user"""
        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        prefix = token[:8]
        
        # Set expiration
        expires_at = None
        if token_data.expires_in_days:
            expires_at = utc_now() + timedelta(days=token_data.expires_in_days)
        
        # Create token document
        api_token = APIToken(
            user_id=user_id,
            name=token_data.name,
            token_hash=token_hash,
            prefix=prefix,
            scopes=token_data.scopes,
            allowed_ips=token_data.allowed_ips,
            expires_at=expires_at,
            created_by=created_by
        )
        
        await api_token.insert()
        
        # Update user's token list
        user = await User.get(user_id)
        if user:
            user.api_tokens.append(api_token.token_id)
            await user.save()
        
        return APITokenResponse(
            token_id=api_token.token_id,
            name=api_token.name,
            token=token,  # Only returned on creation
            prefix=prefix,
            scopes=api_token.scopes,
            expires_at=expires_at,
            created_at=api_token.created_at
        )
    
    async def revoke_api_token(
        self,
        user_id: str,
        token_id: str,
        revoked_by: str
    ) -> bool:
        """Revoke an API token"""
        token = await APIToken.find_one(
            APIToken.user_id == user_id,
            APIToken.token_id == token_id,
            APIToken.is_active == True
        )
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API token not found"
            )
        
        token.is_active = False
        token.revoked_at = utc_now()
        token.revoked_by = revoked_by
        await token.save()
        
        return True
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics for admin dashboard"""
        total_users = await User.find().count()
        active_users = await User.find(User.status == UserStatus.ACTIVE).count()
        pending_users = await User.find(User.status == UserStatus.PENDING_VERIFICATION).count()
        suspended_users = await User.find(User.status == UserStatus.SUSPENDED).count()
        
        # Users by role
        role_stats = {}
        for role in UserRole:
            count = await User.find(User.role == role).count()
            role_stats[role.value] = count
        
        # Recent registrations (last 30 days)
        thirty_days_ago = utc_now() - timedelta(days=30)
        recent_registrations = await User.find(
            User.created_at >= thirty_days_ago
        ).count()
        
        # Active sessions
        active_sessions = await UserSession.find(
            UserSession.is_active == True,
            UserSession.expires_at > utc_now()
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_users": pending_users,
            "suspended_users": suspended_users,
            "role_distribution": role_stats,
            "recent_registrations": recent_registrations,
            "active_sessions": active_sessions
        }
    
    async def get_user_activity_log(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user activity log"""
        # Get recent sessions
        sessions = await UserSession.find(
            UserSession.user_id == user_id
        ).sort([("created_at", DESCENDING)]).limit(limit).to_list()
        
        activities = []
        
        for session in sessions:
            activities.append({
                "type": "login" if session.is_active else "logout",
                "timestamp": session.created_at,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "device_info": session.device_info
            })
        
        return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    async def bulk_update_users(
        self,
        user_ids: List[str],
        update_data: Dict[str, Any],
        updated_by: str
    ) -> Dict[str, Any]:
        """Bulk update multiple users"""
        updated_count = 0
        failed_updates = []
        
        for user_id in user_ids:
            try:
                user = await User.get(user_id)
                if user:
                    for field, value in update_data.items():
                        if hasattr(user, field):
                            setattr(user, field, value)
                    
                    user.updated_at = utc_now()
                    user.last_updated_by = updated_by
                    await user.save()
                    updated_count += 1
                else:
                    failed_updates.append({"user_id": user_id, "error": "User not found"})
            except Exception as e:
                failed_updates.append({"user_id": user_id, "error": str(e)})
        
        return {
            "updated_count": updated_count,
            "total_requested": len(user_ids),
            "failed_updates": failed_updates
        }
    
    async def export_users(
        self,
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Export users data"""
        query = filters or {}
        users = await User.find(query).to_list()
        
        exported_data = []
        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "status": user.status.value,
                "organization": user.organization,
                "department": user.department,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_email_verified": user.is_email_verified
            }
            exported_data.append(user_data)
        
        return exported_data
    
    async def _user_to_response(self, user: User) -> UserResponse:
        """Convert User document to UserResponse"""
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            avatar_url=user.avatar_url,
            organization=user.organization,
            department=user.department,
            timezone=user.timezone,
            is_email_verified=user.is_email_verified,
            last_login=user.last_login,
            created_at=user.created_at,
            notification_preferences=user.notification_preferences
        )


# Global service instance
user_service = UserService()

