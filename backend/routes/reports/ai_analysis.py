"""AI analysis endpoint for scan reports."""
import logging
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from models.report import ScanReport
from models.user import User
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_user_project_ids
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{report_id}/ai-analysis")
async def get_ai_analysis(
    report_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get AI analysis for a specific report"""
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
            raise HTTPException(status_code=404, detail="Report not found")

        accessible_project_ids = await get_user_project_ids(user_id)
        report_user_id = getattr(report, "user_id", None)
        report_project_id = getattr(report, "project_id", None)

        has_access = (
            report_user_id == user_id
            or (report_project_id and report_project_id in accessible_project_ids)
        )

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this report")

        if not report.ai_analysis:
            return {
                "has_analysis": False,
                "message": "AI analysis not available for this report",
                "report_id": report_id,
            }

        ai_data = report.ai_analysis

        findings_analysis = {}
        if report.scan_results:
            for scan_result in report.scan_results:
                if scan_result.findings:
                    for i, finding in enumerate(scan_result.findings):
                        finding_id = getattr(finding, "id", f"{scan_result.scanner.value}_{i}")
                        findings_analysis[finding_id] = {
                            "ai_explanation": f"This {finding.severity.value if hasattr(finding.severity, 'value') else finding.severity} severity issue requires attention.",
                            "risk_context": ai_data.risk_assessment[:200] if ai_data.risk_assessment else "Risk context not available",
                            "remediation_priority": "high" if finding.severity.value in ["critical", "high"] else "medium",
                            "secure_code_example": ai_data.secure_code_examples.get(finding.title, "") if ai_data.secure_code_examples else "",
                        }

        return {
            "has_analysis": True,
            "report_id": report_id,
            "model_used": ai_data.model_used,
            "generated_at": ai_data.generated_at.isoformat() if ai_data.generated_at else None,
            "executive_summary": ai_data.executive_summary,
            "overall_risk_assessment": ai_data.risk_assessment,
            "risk_score": getattr(ai_data, "risk_score", None),
            "risk_level": getattr(ai_data, "risk_level", None),
            "security_score": getattr(ai_data, "security_score", None),
            "priority_findings": ai_data.priority_findings,
            "priority_recommendations": ai_data.recommendations,
            "secure_code_examples": ai_data.secure_code_examples,
            "compliance_impact": ai_data.compliance_impact,
            "estimated_fix_time": ai_data.estimated_fix_time,
            "attack_vectors": getattr(ai_data, "attack_vectors", []),
            "threat_categories": getattr(ai_data, "threat_categories", {}),
            "remediation_roadmap": getattr(ai_data, "remediation_roadmap", []),
            "findings_analysis": findings_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AI analysis for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
