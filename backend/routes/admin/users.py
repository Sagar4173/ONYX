import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as fastapi_status

from models.project import Project
from models.report import ScanReport
from models.user import User, UserRole, UserStatus
from routes.dependencies import require_admin
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/users/all")
async def get_all_users_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        query_filters = {}

        if role and role.strip():
            query_filters["role"] = role

        if status and status.strip():
            query_filters["status"] = status

        if query_filters:
            query = User.find(query_filters)
        else:
            query = User.find_all()

        if search:
            query = User.find({
                **query_filters,
                "$or": [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ]
            })

        total = await query.count()

        sort_direction = -1 if sort_order == "desc" else 1
        users = await query.sort([(sort_by, sort_direction)]).skip(skip).limit(limit).to_list()

        enriched_users = []
        for u in users:
            project_count = await Project.find(Project.owner_id == str(u.id)).count()

            scan_count = await ScanReport.find(ScanReport.user_id == str(u.id)).count()

            user_data = {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
                "status": u.status.value if hasattr(u.status, 'value') else str(u.status),
                "organization": u.organization,
                "department": u.department,
                "avatar_url": u.avatar_url,
                "is_email_verified": u.is_email_verified,
                "two_factor_enabled": u.two_factor_enabled,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                "failed_login_attempts": u.failed_login_attempts,
                "locked_until": u.locked_until.isoformat() if u.locked_until else None,
                "project_count": project_count,
                "scan_count": scan_count,
                "created_by": u.created_by
            }
            enriched_users.append(user_data)

        return {
            "users": enriched_users,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(enriched_users) < total
            }
        }

    except Exception as e:
        logger.error(f"Error fetching users for admin: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to fetch users")
        )


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    try:
        if user_id == str(current_user.id):
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.role == UserRole.ADMIN and user_id != str(current_user.id):
            admin_count = await User.find(User.role == UserRole.ADMIN).count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )

        await user.delete()
        logger.info(f"Admin {current_user.username} deleted user {user.username}")

        return {"message": f"User {user.username} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to delete user")
        )


@router.put("/users/{user_id}/role")
async def update_user_role_admin(
    user_id: str,
    role_data: Dict[str, str],
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    try:
        new_role = role_data.get("role")
        if not new_role:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail="Role is required"
            )

        try:
            role_enum = UserRole(new_role)
        except ValueError:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {new_role}"
            )

        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.role == UserRole.ADMIN and role_enum != UserRole.ADMIN:
            admin_count = await User.find(User.role == UserRole.ADMIN).count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the last admin user"
                )

        user.role = role_enum
        user.updated_at = datetime.now(timezone.utc)
        user.last_updated_by = str(current_user.id)
        await user.save()

        logger.info(f"Admin {current_user.username} updated {user.username}'s role to {new_role}")

        return {"message": f"User role updated to {new_role}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to update user role")
        )


@router.put("/users/{user_id}/status")
async def update_user_status_admin(
    user_id: str,
    status_data: Dict[str, str],
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )

        try:
            status_enum = UserStatus(new_status)
        except ValueError:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {new_status}"
            )

        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user_id == str(current_user.id) and status_enum in [UserStatus.SUSPENDED, UserStatus.INACTIVE]:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail="Cannot suspend or deactivate your own account"
            )

        user.status = status_enum
        user.updated_at = datetime.now(timezone.utc)
        user.last_updated_by = str(current_user.id)
        await user.save()

        logger.info(f"Admin {current_user.username} updated {user.username}'s status to {new_status}")

        return {"message": f"User status updated to {new_status}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to update user status")
        )
