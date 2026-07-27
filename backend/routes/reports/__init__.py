"""
Reports route package.
Split from the monolithic reports.py for better maintainability.
"""
from fastapi import APIRouter

from routes.dependencies import auth_service, get_current_user

from .ai_analysis import router as ai_analysis_router
from .analytics import router as analytics_router
from .detail import router as detail_router
from .export import router as export_router
from .listing import router as listing_router

router = APIRouter(tags=["Reports"])
router.include_router(listing_router)
router.include_router(detail_router)
router.include_router(export_router)
router.include_router(ai_analysis_router)
router.include_router(analytics_router)

__all__ = ["router"]
