from fastapi import APIRouter

from .baselines import router as baselines_router
from .combined import router as combined_router
from .policies import router as policies_router
from .rules import router as rules_router

router = APIRouter(prefix="/security", tags=["Security"])
router.include_router(rules_router)
router.include_router(baselines_router)
router.include_router(policies_router)
router.include_router(combined_router)

__all__ = ["router"]
