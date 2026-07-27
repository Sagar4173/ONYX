from fastapi import APIRouter

from .events import router as events_router
from .scan_operations import router as scan_operations_router

router = APIRouter(prefix="/webhook", tags=["Webhook"])
router.include_router(scan_operations_router)
router.include_router(events_router)

__all__ = ["router"]
