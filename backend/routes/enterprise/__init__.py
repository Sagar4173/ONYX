from fastapi import APIRouter

from routes.dependencies import get_current_user
from services.analytics.audit_logging_service import get_audit_service
from services.analytics.data_retention_service import get_retention_service
from services.compliance.advanced_compliance_service import get_compliance_service

from .audit_logs import router as audit_logs_router
from .compliance import router as compliance_router
from .dependencies import get_database
from .health import router as health_router
from .retention import router as retention_router

router = APIRouter(prefix="/api/enterprise", tags=["Enterprise Features"])
router.include_router(audit_logs_router)
router.include_router(retention_router)
router.include_router(compliance_router)
router.include_router(health_router)

__all__ = ["router", "get_database", "get_current_user", "get_audit_service", "get_retention_service", "get_compliance_service"]
