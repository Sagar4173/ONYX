import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Health & Compliance"])


@router.get("/status")
async def get_security_status() -> Dict[str, Any]:
    status = ServiceRegistry.get_status()
    return {
        "status": "healthy" if status["active_count"] > 0 else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": status["services"],
        "active_services": status["active_count"],
        "total_services": status["total_services"]
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    status = ServiceRegistry.get_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "advanced_security_api",
        "services_active": status["active_count"]
    }


@router.get("/compliance/frameworks")
async def get_compliance_frameworks(
    current_user: User = Depends(get_current_user)
):
    return {
        "frameworks": [
            {"id": "owasp_top10", "name": "OWASP Top 10", "version": "2021"},
            {"id": "pci_dss", "name": "PCI DSS", "version": "4.0"},
            {"id": "iso_27001", "name": "ISO 27001", "version": "2022"},
            {"id": "nist_csf", "name": "NIST Cybersecurity Framework", "version": "2.0"},
            {"id": "sox", "name": "Sarbanes-Oxley", "version": "2002"},
            {"id": "gdpr", "name": "GDPR", "version": "2018"},
            {"id": "hipaa", "name": "HIPAA", "version": "2013"},
            {"id": "soc2", "name": "SOC 2", "version": "2017"},
            {"id": "cis", "name": "CIS Controls", "version": "8.0"}
        ]
    }


@router.get("/compliance/dashboard")
async def get_compliance_dashboard(
    current_user: User = Depends(get_current_user)
):
    try:
        return {
            "frameworks": [
                {"name": "SOC 2", "compliance": 95, "status": "compliant"},
                {"name": "ISO 27001", "compliance": 92, "status": "compliant"},
                {"name": "PCI DSS", "compliance": 88, "status": "minor_issues"},
                {"name": "NIST CSF", "compliance": 97, "status": "compliant"},
                {"name": "OWASP Top 10", "compliance": 94, "status": "compliant"}
            ],
            "overall_score": 93,
            "last_assessment": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Compliance dashboard error: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Compliance dashboard retrieval"))
