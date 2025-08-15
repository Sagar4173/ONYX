"""
Compliance reporting endpoints for security scan results
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from models.report import ScanReport, VulnerabilityFinding, ComplianceFramework
from services.compliance_analyzer import ComplianceAnalysisService
from database import scan_reports_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])
compliance_service = ComplianceAnalysisService()


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


class FrameworkControlStatus(BaseModel):
    control_id: str
    control_name: str
    description: str
    status: str  # "compliant", "non_compliant", "partial", "not_tested"
    findings_count: int
    critical_findings: int
    recommendations: List[str]


@router.get("/frameworks", response_model=List[str])
async def get_supported_frameworks():
    """Get list of supported compliance frameworks"""
    return [framework.value for framework in ComplianceFramework]


@router.post("/report", response_model=ComplianceReportResponse)
async def generate_compliance_report(request: ComplianceReportRequest):
    """
    Generate compliance report for specific framework
    """
    try:
        # Get scan reports based on criteria
        if request.scan_report_ids:
            scan_reports = await _get_scan_reports_by_ids(request.scan_report_ids)
        else:
            # Get recent scan reports
            cutoff_date = datetime.utcnow() - timedelta(days=request.date_range_days or 30)
            scan_reports = await _get_recent_scan_reports(cutoff_date)
        
        if not scan_reports:
            raise HTTPException(status_code=404, detail="No scan reports found")
        
        # Collect all findings from scan reports
        all_findings = []
        for report in scan_reports:
            if hasattr(report, 'findings') and report.findings:
                all_findings.extend(report.findings)
        
        # Generate compliance analysis
        report = await compliance_service.generate_compliance_report(
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
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/framework/{framework}/controls", response_model=List[FrameworkControlStatus])
async def get_framework_control_status(
    framework: ComplianceFramework,
    scan_report_ids: Optional[str] = Query(None, description="Comma-separated scan report IDs"),
    date_range_days: Optional[int] = Query(30, description="Number of days to look back")
):
    """
    Get detailed control status for a specific compliance framework
    """
    try:
        # Parse scan report IDs if provided
        report_ids = []
        if scan_report_ids:
            report_ids = [id.strip() for id in scan_report_ids.split(',')]
        
        # Get scan reports
        if report_ids:
            scan_reports = await _get_scan_reports_by_ids(report_ids)
        else:
            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
            scan_reports = await _get_recent_scan_reports(cutoff_date)
        
        # Collect findings
        all_findings = []
        for report in scan_reports:
            if hasattr(report, 'findings') and report.findings:
                all_findings.extend(report.findings)
        
        # Get control status
        control_status = await compliance_service.get_framework_control_status(
            findings=all_findings,
            framework=framework
        )
        
        # Convert to response format
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-summary")
async def get_risk_summary(
    scan_report_ids: Optional[str] = Query(None, description="Comma-separated scan report IDs"),
    date_range_days: Optional[int] = Query(30, description="Number of days to look back")
):
    """
    Get aggregated risk summary across all compliance frameworks
    """
    try:
        # Parse scan report IDs if provided
        report_ids = []
        if scan_report_ids:
            report_ids = [id.strip() for id in scan_report_ids.split(',')]
        
        # Get scan reports
        if report_ids:
            scan_reports = await _get_scan_reports_by_ids(report_ids)
        else:
            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
            scan_reports = await _get_recent_scan_reports(cutoff_date)
        
        # Collect findings
        all_findings = []
        for report in scan_reports:
            if hasattr(report, 'findings') and report.findings:
                all_findings.extend(report.findings)
        
        # Generate risk summary
        risk_summary = await compliance_service.generate_risk_summary(all_findings)
        
        return risk_summary
        
    except Exception as e:
        logger.error(f"Error generating risk summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_compliance_trends(
    framework: Optional[ComplianceFramework] = Query(None, description="Specific framework"),
    days: int = Query(90, description="Number of days for trend analysis")
):
    """
    Get compliance trends over time
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get historical scan reports
        scan_reports = await _get_scan_reports_since(cutoff_date)
        
        # Generate trends analysis
        trends = await compliance_service.generate_compliance_trends(
            scan_reports=scan_reports,
            framework=framework,
            days=days
        )
        
        return trends
        
    except Exception as e:
        logger.error(f"Error generating compliance trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def _get_scan_reports_by_ids(report_ids: List[str]) -> List[ScanReport]:
    """Get scan reports by their IDs"""
    try:
        reports = []
        for report_id in report_ids:
            report = await scan_reports_collection.find_one({"_id": report_id})
            if report:
                reports.append(ScanReport(**report))
        return reports
    except Exception as e:
        logger.error(f"Error fetching scan reports by IDs: {e}")
        return []


async def _get_recent_scan_reports(cutoff_date: datetime) -> List[ScanReport]:
    """Get scan reports created after cutoff date"""
    try:
        cursor = scan_reports_collection.find({
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", -1)
        
        reports = []
        async for report_doc in cursor:
            reports.append(ScanReport(**report_doc))
        
        return reports
    except Exception as e:
        logger.error(f"Error fetching recent scan reports: {e}")
        return []


async def _get_scan_reports_since(cutoff_date: datetime) -> List[ScanReport]:
    """Get all scan reports since cutoff date for trends analysis"""
    try:
        cursor = scan_reports_collection.find({
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", 1)  # Ascending for trends
        
        reports = []
        async for report_doc in cursor:
            reports.append(ScanReport(**report_doc))
        
        return reports
    except Exception as e:
        logger.error(f"Error fetching scan reports for trends: {e}")
        return []
