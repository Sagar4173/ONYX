from fastapi import APIRouter

from .sbom import router as sbom_router
from .scan_comparison import router as scan_comparison_router
from .trends import router as trends_router
from .vulnerabilities import router as vulnerabilities_router

router = APIRouter(prefix="/enterprise-security", tags=["Enterprise Security"])
router.include_router(vulnerabilities_router)
router.include_router(sbom_router)
router.include_router(trends_router)
router.include_router(scan_comparison_router)

__all__ = ["router"]
