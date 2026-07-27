from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from models.user import User, UserRole, UserStatus
from services.auth.auth_service import auth_service

from .admin_users import list_users as _list_users
from .admin_users import router as admin_router
from .profile import router as profile_router
from .security import router as security_router

router = APIRouter(prefix="/users", tags=["User Management"])
router.include_router(profile_router)
router.include_router(admin_router)
router.include_router(security_router)


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
    return await _list_users(
        skip=skip, limit=limit, role=role, status=status,
        search=search, sort_by=sort_by, sort_order=sort_order,
        current_user=current_user
    )


__all__ = ["router"]
