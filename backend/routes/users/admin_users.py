from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from models.user import User, UserResponse, UserRole, UserStatus, UserUpdate
from services.auth.auth_service import auth_service
from services.auth.user_service import user_service
from utils.datetime_utils import utc_now

router = APIRouter(tags=["User Management - Admin"])


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
    stats = await user_service.get_user_statistics()
    return stats


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
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
    sessions = await user_service.get_user_sessions(user_id)
    return {"sessions": sessions}


@router.delete("/{user_id}/sessions/{session_id}")
async def revoke_user_session(
    user_id: str,
    session_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    await user_service.revoke_user_session(user_id, session_id, current_user.id)
    return {"message": "Session revoked successfully"}


@router.delete("/{user_id}/sessions")
async def revoke_all_user_sessions(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    await auth_service.logout_all_sessions(user_id)
    return {"message": "All sessions revoked successfully"}


@router.get("/{user_id}/api-tokens")
async def get_user_api_tokens(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    tokens = await user_service.get_user_api_tokens(user_id)
    return {"tokens": tokens}


@router.delete("/{user_id}/api-tokens/{token_id}")
async def revoke_user_api_token(
    user_id: str,
    token_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    await user_service.revoke_api_token(user_id, token_id, current_user.id)
    return {"message": "API token revoked successfully"}


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
    activities = await user_service.get_user_activity_log(user_id, limit)
    return {"activities": activities}


@router.post("/bulk-update")
async def bulk_update_users(
    user_ids: List[str],
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN))
):
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
                "Content-Disposition": f"attachment; filename=users_export_{utc_now().strftime('%Y%m%d_%H%M%S')}.json"
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

    await auth_service.logout_all_sessions(user_id)
    await user.delete()

    return {"message": "User account deleted successfully"}
