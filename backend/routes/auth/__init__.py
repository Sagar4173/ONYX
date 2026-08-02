from fastapi import APIRouter, Depends

from database import require_beanie

from .api_tokens import router as api_tokens_router
from .email_verification import router as email_verification_router
from .notifications import router as notifications_router
from .password import router as password_router
from .profile import router as profile_router
from .registration import router as registration_router
from .sessions import router as sessions_router
from .sso import router as sso_router
from .two_factor import router as two_factor_router

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[Depends(require_beanie)]
)
router.include_router(registration_router)
router.include_router(sessions_router)
router.include_router(sso_router)
router.include_router(profile_router)
router.include_router(notifications_router)
router.include_router(two_factor_router)
router.include_router(password_router)
router.include_router(email_verification_router)
router.include_router(api_tokens_router)

__all__ = ["router"]
