from fastapi import APIRouter

from .baselines import router as baselines_router
from .health import router as health_router
from .intelligence import router as intelligence_router
from .metrics import router as metrics_router
from .policies import router as policies_router
from .rules import router as rules_router
from .scanning import router as scanning_router

router = APIRouter(prefix="/advanced-security", tags=["Advanced Security"])
router.include_router(health_router)
router.include_router(intelligence_router)
router.include_router(metrics_router)
router.include_router(rules_router)
router.include_router(baselines_router)
router.include_router(policies_router)
router.include_router(scanning_router)

__all__ = ["router"]
