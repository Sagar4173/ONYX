"""
Shared dependencies for ONYX route modules.
Consolidates authentication, authorization, and common utilities
to eliminate copy-pasted boilerplate across 10 route files.
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.user import User, UserRole
from services.auth.auth_service import AuthService

logger = logging.getLogger(__name__)

security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get current authenticated user from bearer token."""
    return await auth_service.get_current_user(credentials)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    try:
        return await auth_service.get_current_user(credentials)
    except Exception:
        return None


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Require admin role for access."""
    user = await auth_service.get_current_user(credentials)
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
