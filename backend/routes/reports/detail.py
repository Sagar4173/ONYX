"""Report detail and summary endpoints."""
import logging
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from models.report import ScanReport, ScanStatus
from models.user import User
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_user_project_ids
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_risk_level(risk_assessment: str) -> Optional[str]:
    """Extract risk level from AI risk assessment text"""
    if not risk_assessment:
        return None
    risk_assessment_lower = risk_assessment.lower()
    if "critical" in risk_assessment_lower:
        return "CRITICAL"
    elif "high" in risk_assessment_lower:
        return "HIGH"
    elif "medium" in risk_assessment_lower:
        return "MEDIUM"
    elif "low" in risk_assessment_lower:
        return "LOW"
    return None


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get detailed scan report by ID"""
    try:
        report = None
        user_id = str(current_user.id)

        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
            except Exception as db_error:
                logger.warning(f"Database error when fetching report by ObjectId {report_id}: {db_error}")

        if not report:
            try:
                report = await ScanReport.find_one(ScanReport.scan_id == report_id)
            except Exception as db_error:
                logger.warning(f"Database error when fetching report by scan_id {report_id}: {db_error}")

        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        accessible_project_ids = await get_user_project_ids(user_id)
        report_user_id = getattr(report, "user_id", None)
        report_project_id = getattr(report, "project_id", None)

        has_access = (
            report_user_id == user_id
            or (report_project_id and report_project_id in accessible_project_ids)
        )

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this report")

        response_data = {
            "id": str(report.id),
            "project_name": report.project_name,
            "scan_id": report.scan_id,
            "status": report.status.value,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "started_at": report.started_at.isoformat() if report.started_at else None,
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
            "duration_seconds": report.duration_seconds,
            "git_metadata": {
                "repository_url": report.git_metadata.repository_url if report.git_metadata else "",
                "branch": report.git_metadata.branch if report.git_metadata else "",
                "commit_hash": report.git_metadata.commit_hash if report.git_metadata else "",
                "commit_message": report.git_metadata.commit_message if report.git_metadata else "",
                "commit_author": report.git_metadata.commit_author if report.git_metadata else "",
                "commit_timestamp": report.git_metadata.commit_timestamp.isoformat() if report.git_metadata and report.git_metadata.commit_timestamp else None,
                "pr_number": report.git_metadata.pr_number if report.git_metadata else None,
                "event_type": report.git_metadata.event_type if report.git_metadata else "",
            },
            "summary": {
                "total_findings": report.total_findings,
                "findings_by_severity": report.findings_by_severity,
                "scanners_run": len(report.scan_results) if report.scan_results else 0,
                "successful_scans": len([r for r in report.scan_results if r.status == ScanStatus.COMPLETED]) if report.scan_results else 0,
                "failed_scans": len([r for r in report.scan_results if r.status == ScanStatus.FAILED]) if report.scan_results else 0,
            },
            "scan_results": [],
            "tags": report.tags if report.tags else [],
            "metadata": report.metadata if report.metadata else {},
        }

        if report.scan_results:
            for scan_result in report.scan_results:
                scanner_data = {
                    "scanner": scan_result.scanner.value,
                    "status": scan_result.status.value,
                    "started_at": scan_result.started_at.isoformat() if scan_result.started_at else None,
                    "completed_at": scan_result.completed_at.isoformat() if scan_result.completed_at else None,
                    "duration_seconds": scan_result.duration_seconds,
                    "summary": scan_result.summary,
                    "error_message": scan_result.error_message,
                    "findings_count": len(scan_result.findings) if scan_result.findings else 0,
                    "findings": [],
                }

                if scan_result.findings:
                    for finding in scan_result.findings:
                        finding_data = {
                            "id": finding.id,
                            "title": finding.title,
                            "description": finding.description,
                            "severity": finding.severity.value if hasattr(finding.severity, "value") else finding.severity,
                            "confidence": finding.confidence if isinstance(finding.confidence, str) else (finding.confidence.value if finding.confidence and hasattr(finding.confidence, "value") else finding.confidence),
                            "category": getattr(finding, "category", None),
                            "file_path": getattr(finding, "file_path", "") or (finding.location.file_path if hasattr(finding, "location") and finding.location else ""),
                            "line_number": getattr(finding, "line_start", None) or (finding.location.line_number if hasattr(finding, "location") and finding.location else None),
                            "column_number": getattr(finding, "column_start", None) or (finding.location.column_number if hasattr(finding, "location") and finding.location else None),
                            "code_snippet": getattr(finding, "code_snippet", "") or (finding.location.code_snippet if hasattr(finding, "location") and finding.location else ""),
                            "remediation": getattr(finding, "remediation", None),
                            "cwe_id": getattr(finding, "cwe_id", None),
                            "cve_id": getattr(finding, "cve_id", None),
                            "owasp_category": getattr(finding, "owasp_category", None),
                            "references": getattr(finding, "references", []),
                        }
                        scanner_data["findings"].append(finding_data)

                response_data["scan_results"].append(scanner_data)

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/{report_id}/summary")
async def get_report_summary(
    report_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get summary information for a specific report"""
    try:
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")

        report = await ScanReport.get(ObjectId(report_id))
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        user_id = str(current_user.id)
        accessible_project_ids = await get_user_project_ids(user_id)
        report_user_id = getattr(report, "user_id", None)
        report_project_id = getattr(report, "project_id", None)

        has_access = (
            report_user_id == user_id
            or (report_project_id and report_project_id in accessible_project_ids)
        )

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this report")

        return {
            "id": str(report.id),
            "project_name": report.project_name,
            "scan_id": report.scan_id,
            "status": report.status.value,
            "repository_url": report.git_metadata.repository_url,
            "branch": report.git_metadata.branch,
            "commit_hash": report.git_metadata.commit_hash,
            "created_at": report.created_at,
            "completed_at": report.completed_at,
            "duration_seconds": report.duration_seconds,
            "total_findings": report.total_findings,
            "findings_by_severity": report.findings_by_severity,
            "scanners_summary": [
                {
                    "scanner": result.scanner.value,
                    "status": result.status.value,
                    "findings_count": len(result.findings),
                    "duration_seconds": result.duration_seconds,
                }
                for result in report.scan_results
            ],
            "has_ai_analysis": report.ai_analysis is not None,
            "ai_risk_level": _extract_risk_level(report.ai_analysis.risk_assessment) if report.ai_analysis else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report summary {report_id}: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
