from fastapi import APIRouter

from .activity import router as activity_router
from .dashboard import router as dashboard_router
from .projects import router as projects_router
from .reports import router as reports_router
from .users import router as users_router
from .webhook import router as webhook_router

router = APIRouter(prefix="/admin", tags=["Administration"])
router.include_router(dashboard_router)
router.include_router(users_router)
router.include_router(projects_router)
router.include_router(reports_router)
router.include_router(activity_router)
router.include_router(webhook_router)

__all__ = ["router"]
