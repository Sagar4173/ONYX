from fastapi import APIRouter

from .frameworks import router as frameworks_router
from .reports import router as reports_router

router = APIRouter(prefix="/compliance", tags=["Compliance"])
router.include_router(reports_router)
router.include_router(frameworks_router)

__all__ = ["router"]
