from fastapi import APIRouter

from .results import router as results_router
from .scans import router as scans_router
from .suppressions import router as suppressions_router

router = APIRouter(prefix="/api/advanced-scanning", tags=["Advanced Scanning"])
router.include_router(scans_router)
router.include_router(suppressions_router)
router.include_router(results_router)

__all__ = ["router"]
