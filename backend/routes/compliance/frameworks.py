import logging
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from models.report import ComplianceFramework
from utils.datetime_utils import utc_now
from utils.error_handling import get_safe_error_detail

from .helpers import _get_recent_scan_reports, _get_scan_reports_by_ids, _get_scan_reports_since
from .reports import get_compliance_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Compliance - Frameworks"])


class FrameworkControlStatus(BaseModel):
    control_id: str
    control_name: str
    description: str
    status: str
    findings_count: int
    critical_findings: int
    recommendations: List[str]


@router.get("/frameworks", response_model=List[str])
async def get_supported_frameworks() -> List[str]:
    return [framework.value for framework in ComplianceFramework]


@router.get("/framework/{framework}/controls", response_model=List[FrameworkControlStatus])
async def get_framework_control_status(
    framework: ComplianceFramework,
    scan_report_ids: Optional[str] = Query(None),
    date_range_days: Optional[int] = Query(30)
):
    try:
        report_ids = []
        if scan_report_ids:
            report_ids = [id.strip() for id in scan_report_ids.split(',')]

        if report_ids:
            scan_reports = await _get_scan_reports_by_ids(report_ids)
        else:
            cutoff_date = utc_now() - timedelta(days=date_range_days)
            scan_reports = await _get_recent_scan_reports(cutoff_date)

        all_findings = []
        for report in scan_reports:
            if hasattr(report, 'findings') and report.findings:
                all_findings.extend(report.findings)

        svc = await get_compliance_service()
        control_status = await svc.get_framework_control_status(
            findings=all_findings,
            framework=framework
        )

        result = []
        for control_id, status_data in control_status.items():
            result.append(FrameworkControlStatus(
                control_id=control_id,
                control_name=status_data['name'],
                description=status_data['description'],
                status=status_data['status'],
                findings_count=status_data['findings_count'],
                critical_findings=status_data['critical_findings'],
                recommendations=status_data['recommendations']
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting framework control status: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/risk-summary")
async def get_risk_summary(
    scan_report_ids: Optional[str] = Query(None),
    date_range_days: Optional[int] = Query(30)
):
    try:
        report_ids = []
        if scan_report_ids:
            report_ids = [id.strip() for id in scan_report_ids.split(',')]

        if report_ids:
            scan_reports = await _get_scan_reports_by_ids(report_ids)
        else:
            cutoff_date = utc_now() - timedelta(days=date_range_days)
            scan_reports = await _get_recent_scan_reports(cutoff_date)

        all_findings = []
        for report in scan_reports:
            if hasattr(report, 'findings') and report.findings:
                all_findings.extend(report.findings)

        risk_summary = await (await get_compliance_service()).generate_risk_summary(all_findings)

        return risk_summary

    except Exception as e:
        logger.error(f"Error generating risk summary: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/trends")
async def get_compliance_trends(
    framework: Optional[ComplianceFramework] = Query(None),
    days: int = Query(90)
):
    try:
        cutoff_date = utc_now() - timedelta(days=days)

        scan_reports = await _get_scan_reports_since(cutoff_date)

        svc = await get_compliance_service()
        trends = await svc.generate_compliance_trends(
            scan_reports=scan_reports,
            framework=framework,
            days=days
        )

        return trends

    except Exception as e:
        logger.error(f"Error generating compliance trends: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
