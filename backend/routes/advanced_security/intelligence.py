import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

from .schemas import PentestRequest, VulnerabilityScanRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Intelligence"])


@router.get("/threat-intel/feeds")
async def get_threat_intelligence_feeds(
    current_user: User = Depends(get_current_user)
):
    try:
        threat_intel = ServiceRegistry.get_threat_intelligence()
        if threat_intel:
            feeds = await threat_intel.get_available_feeds()
            return {"feeds": feeds, "status": "active"}
        return {"feeds": [], "status": "unavailable", "message": "Threat intelligence service not initialized"}
    except Exception as e:
        logger.error(f"Error getting threat intel feeds: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Threat intelligence feed retrieval"))


@router.post("/threat-intel/analyze")
async def analyze_threat_intelligence(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    try:
        threat_intel = ServiceRegistry.get_threat_intelligence()
        if threat_intel:
            indicators = request.get("indicators", [])
            results = await threat_intel.analyze_indicators(indicators)
            return {"results": results, "analyzed_count": len(indicators)}
        return {"results": [], "analyzed_count": 0, "message": "Threat intelligence service not initialized"}
    except Exception as e:
        logger.error(f"Error analyzing threat intel: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Threat intelligence analysis"))


@router.get("/vulnerabilities/dashboard")
async def get_vulnerability_dashboard(
    current_user: User = Depends(get_current_user)
):
    try:
        vuln_manager = ServiceRegistry.get_vulnerability_manager()
        if vuln_manager:
            dashboard_data = await vuln_manager.get_dashboard_data()
            return dashboard_data
        return {"vulnerabilities": [], "metrics": {}, "trends": [], "message": "Vulnerability manager not initialized"}
    except Exception as e:
        logger.error(f"Error getting vulnerability dashboard: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Vulnerability dashboard retrieval"))


@router.post("/vulnerabilities/scan")
async def initiate_vulnerability_scan(
    request: VulnerabilityScanRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        vuln_manager = ServiceRegistry.get_vulnerability_manager()
        if vuln_manager:
            result = await vuln_manager.initiate_scan(request.config)
            return {"scan_id": result.get("scan_id"), "status": "initiated"}
        return {"scan_id": None, "status": "unavailable", "message": "Vulnerability manager not initialized"}
    except Exception as e:
        logger.error(f"Error initiating vulnerability scan: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Vulnerability scan initiation"))


@router.post("/pentest/execute")
async def execute_penetration_test(
    request: PentestRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        pentest_engine = ServiceRegistry.get_penetration_testing()
        if pentest_engine:
            result = await pentest_engine.execute_tests(request.config)
            return {"test_id": result.get("test_id"), "status": "executing"}
        return {"test_id": None, "status": "unavailable", "message": "Penetration testing engine not initialized"}
    except Exception as e:
        logger.error(f"Error executing penetration test: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Penetration test execution"))
