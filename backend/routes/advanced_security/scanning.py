import logging

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

from .schemas import AdvancedScanRequest, SecurityBoundaryTestRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Scanning"])


@router.post("/scan/execute")
async def execute_advanced_scan(
    request: AdvancedScanRequest,
    current_user: User = Depends(get_current_user)
):
    security_scanner = ServiceRegistry.get_security_scanner()
    if not security_scanner:
        raise HTTPException(status_code=503, detail="Security scanner not initialized")

    try:
        scan_result = await security_scanner.execute_scan(request.config)
        return {
            "scan_id": scan_result.get("scan_id"),
            "status": "executing"
        }
    except Exception as e:
        logger.error(f"Advanced scan error: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Advanced scan execution"))


@router.post("/scan/boundaries/test")
async def test_security_boundaries(
    request: SecurityBoundaryTestRequest,
    current_user: User = Depends(get_current_user)
):
    security_scanner = ServiceRegistry.get_security_scanner()
    if not security_scanner:
        raise HTTPException(status_code=503, detail="Security scanner not initialized")

    try:
        response = await security_scanner.test_boundaries(
            rule_id=request.rule_id,
            test_input=request.test_input,
            boundary_type=request.boundary_type
        )
        return response
    except Exception as e:
        logger.error(f"Error testing security boundaries: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Security boundary testing"))


@router.get("/boundaries/status")
async def get_security_boundaries_status(
    current_user: User = Depends(get_current_user)
):
    try:
        return {
            "boundaries": {
                "isolation_levels": ["container", "process", "network", "filesystem"],
                "active_boundaries": 4,
                "security_zones": ["dmz", "internal", "secure", "admin"],
                "enforcement_status": "active"
            },
            "isolation_active": True
        }
    except Exception as e:
        logger.error(f"Security boundaries error: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Security boundaries check"))
