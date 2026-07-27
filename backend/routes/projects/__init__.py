from fastapi import APIRouter

from .analytics import router as analytics_router
from .crud import router as crud_router
from .team import router as team_router
from .templates import router as templates_router

router = APIRouter(prefix="/projects", tags=["Projects"])
router.include_router(crud_router)
router.include_router(team_router)
router.include_router(analytics_router)
router.include_router(templates_router)

__all__ = ["router"]
