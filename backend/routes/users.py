"""
User Management Routes for ONYX Security Intelligence Platform
Comprehensive user administration and profile management
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from models.user import (
    User, UserRole, UserStatus,
    UserUpdate, UserPasswordChange, UserResponse,
    APITokenCreate, APITokenResponse
)
from services.auth_service import auth_service
from services.user_service import user_service


router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user's profile"""
    return await user_service._user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Update current user's profile"""
    return await user_service.update_user_profile(
        current_user.id,
        update_data,
        current_user.id
    )


@router.post("/me/change-password")
async def change_current_user_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Change current user's password"""
    await user_service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}


@router.get("/me/sessions")
async def get_current_user_sessions(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user's active sessions"""
    sessions = await user_service.get_user_sessions(current_user.id)
    return {"sessions": sessions}


@router.delete("/me/sessions/{session_id}")
async def revoke_current_user_session(
    session_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Revoke a specific session"""
    await user_service.revoke_user_session(
        current_user.id,
        session_id,
        current_user.id
    )
    return {"message": "Session revoked successfully"}


@router.get("/me/api-tokens")
async def get_current_user_api_tokens(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user's API tokens"""
    tokens = await user_service.get_user_api_tokens(current_user.id)
    return {"tokens": tokens}


@router.post("/me/api-tokens", response_model=APITokenResponse)
async def create_current_user_api_token(
    token_data: APITokenCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Create a new API token for current user"""
    return await user_service.create_api_token(
        current_user.id,
        token_data,
        current_user.id
    )


@router.delete("/me/api-tokens/{token_id}")
async def revoke_current_user_api_token(
    token_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Revoke an API token"""
    await user_service.revoke_api_token(
        current_user.id,
        token_id,
        current_user.id
    )
    return {"message": "API token revoked successfully"}


@router.get("/me/activity")
async def get_current_user_activity(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user's activity log"""
    activities = await user_service.get_user_activity_log(current_user.id, limit)
    return {"activities": activities}


# Admin-only routes
@router.get("", response_model=Dict[str, Any])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
    """
    List all users with filtering and pagination (Admin/Security Manager only)
    """
    # Convert string parameters to enums, handling empty strings
    role_filter = None
    if role and role.strip():
        try:
            role_filter = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {role}. Valid roles: {[r.value for r in UserRole]}"
            )
    
    status_filter = None
    if status and status.strip():
        try:
            status_filter = UserStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid statuses: {[s.value for s in UserStatus]}"
            )
    
    return await user_service.list_users(
        skip=skip,
        limit=limit,
        role=role_filter,
        status=status_filter,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/statistics")
async def get_user_statistics(
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Get user statistics for admin dashboard"""
    stats = await user_service.get_user_statistics()
    return stats


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
    """Get user by ID (Admin/Security Manager only)"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return await user_service._user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Update user profile (Admin only)"""
    return await user_service.update_user_profile(
        user_id,
        update_data,
        current_user.id
    )


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Update user role (Admin only)"""
    # Prevent admin from changing their own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    user = await user_service.update_user_role(user_id, new_role, current_user.id)
    return {"message": f"User role updated to {new_role}", "user": user}


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Update user status (Admin only)"""
    # Prevent admin from changing their own status
    if user_id == current_user.id and new_status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own account status"
        )
    
    user = await user_service.update_user_status(user_id, new_status, current_user.id)
    return {"message": f"User status updated to {new_status}", "user": user}


@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Get user's active sessions (Admin only)"""
    sessions = await user_service.get_user_sessions(user_id)
    return {"sessions": sessions}


@router.delete("/{user_id}/sessions/{session_id}")
async def revoke_user_session(
    user_id: str,
    session_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Revoke user's session (Admin only)"""
    await user_service.revoke_user_session(user_id, session_id, current_user.id)
    return {"message": "Session revoked successfully"}


@router.delete("/{user_id}/sessions")
async def revoke_all_user_sessions(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Revoke all user's sessions (Admin only)"""
    await auth_service.logout_all_sessions(user_id)
    return {"message": "All sessions revoked successfully"}


@router.get("/{user_id}/api-tokens")
async def get_user_api_tokens(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Get user's API tokens (Admin only)"""
    tokens = await user_service.get_user_api_tokens(user_id)
    return {"tokens": tokens}


@router.delete("/{user_id}/api-tokens/{token_id}")
async def revoke_user_api_token(
    user_id: str,
    token_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Revoke user's API token (Admin only)"""
    await user_service.revoke_api_token(user_id, token_id, current_user.id)
    return {"message": "API token revoked successfully"}


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Get user's activity log (Admin only)"""
    activities = await user_service.get_user_activity_log(user_id, limit)
    return {"activities": activities}


@router.post("/bulk-update")
async def bulk_update_users(
    user_ids: List[str],
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Bulk update multiple users (Admin only)"""
    update_data = {}
    if role is not None:
        update_data["role"] = role
    if status is not None:
        update_data["status"] = status
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    # Prevent admin from updating themselves in bulk operations
    if current_user.id in user_ids:
        user_ids.remove(current_user.id)
    
    result = await user_service.bulk_update_users(user_ids, update_data, current_user.id)
    return result


@router.get("/export/data")
async def export_users(
    format: str = Query("json"),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Export users data (Admin only)"""
    filters = {}
    if role:
        filters["role"] = role
    if status:
        filters["status"] = status
    
    data = await user_service.export_users(format, filters)
    
    if format == "json":
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f"attachment; filename=users_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    """Delete user account (Admin only)"""
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Logout all sessions
    await auth_service.logout_all_sessions(user_id)
    
    # Delete user (consider soft delete in production)
    await user.delete()
    
    return {"message": "User account deleted successfully"}


# Security Manager routes (limited user management)
@router.get("/security/overview")
async def get_security_overview(
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
    """Get security overview for security managers"""
    stats = await user_service.get_user_statistics()
    
    # Add security-specific metrics
    now = datetime.utcnow()
    
    # Users with failed login attempts
    users_with_failed_logins = await User.find(
        User.failed_login_attempts > 0
    ).count()
    
    # Locked accounts
    locked_accounts = await User.find(
        User.locked_until > now
    ).count()
    
    # Unverified emails
    unverified_emails = await User.find(
        User.is_email_verified == False
    ).count()
    
    return {
        **stats,
        "security_metrics": {
            "users_with_failed_logins": users_with_failed_logins,
            "locked_accounts": locked_accounts,
            "unverified_emails": unverified_emails
        }
    }


@router.get("/security/suspicious-activity")
async def get_suspicious_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
    """Get suspicious user activity"""
    # Find users with multiple failed login attempts
    suspicious_users = await User.find(
        User.failed_login_attempts >= 3
    ).sort([("failed_login_attempts", -1)]).limit(limit).to_list()
    
    activities = []
    for user in suspicious_users:
        activities.append({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "failed_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until,
            "last_login": user.last_login,
            "status": user.status
        })
    
    return {"suspicious_activities": activities}
