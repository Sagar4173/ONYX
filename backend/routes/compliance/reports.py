import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.report import ComplianceFramework
from services.compliance.compliance_analyzer import ComplianceAnalysisService
from utils.datetime_utils import utc_now
from utils.error_handling import get_safe_error_detail

from .helpers import _get_recent_scan_reports, _get_scan_reports_by_ids

logger = logging.getLogger(__name__)

router = APIRouter(tags=["compliance - reports"])

_compliance_service_instance = None


async def get_compliance_service() -> ComplianceAnalysisService:
    global _compliance_service_instance
    if _compliance_service_instance is None:
        _compliance_service_instance = ComplianceAnalysisService()
    return _compliance_service_instance


class ComplianceReportRequest(BaseModel):
    framework: ComplianceFramework
    scan_report_ids: Optional[List[str]] = None
    date_range_days: Optional[int] = 30


class ComplianceReportResponse(BaseModel):
    framework: ComplianceFramework
    total_findings: int
    mapped_findings: int
    compliance_score: float
    control_coverage: Dict[str, Any]
    risk_summary: Dict[str, int]
    recommendations: List[str]
    generated_at: datetime


@router.post("/report", response_model=ComplianceReportResponse)
async def generate_compliance_report(request: ComplianceReportRequest) -> ComplianceReportResponse:
    try:
        if request.scan_report_ids:
            scan_reports = await _get_scan_reports_by_ids(request.scan_report_ids)
        else:
            cutoff_date = utc_now() - timedelta(days=request.date_range_days or 30)
            scan_reports = await _get_recent_scan_reports(cutoff_date)

        if not scan_reports:
            raise HTTPException(status_code=404, detail="No scan reports found")

        all_findings = []
        for report in scan_reports:
            if hasattr(report, 'findings') and report.findings:
                all_findings.extend(report.findings)

        svc = await get_compliance_service()
        report = await svc.generate_compliance_report(
            findings=all_findings,
            framework=request.framework
        )

        return ComplianceReportResponse(
            framework=request.framework,
            total_findings=report['total_findings'],
            mapped_findings=report['mapped_findings'],
            compliance_score=report['compliance_score'],
            control_coverage=report['control_coverage'],
            risk_summary=report['risk_summary'],
            recommendations=report['recommendations'],
            generated_at=utc_now()
        )

    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
