import logging

from fastapi import APIRouter, Depends, HTTPException

from database import scan_reports_collection
from models.report import ScanReport
from models.user import User
from routes.dependencies import get_current_user
from services.rules.policy_engine import policy_service
from services.scanning.baseline import baseline_service
from utils.datetime_utils import utc_now
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(tags=["security - combined"])


@router.post("/full-security-analysis")
async def full_security_analysis(
    scan_report_id: str,
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: str = "main",
    commit_hash: str = "HEAD",
    environment: str = "development",
    create_baseline: bool = False
):
    try:
        scan_report_doc = await scan_reports_collection.find_one({"report_id": scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")

        scan_report = ScanReport(**scan_report_doc)

        analysis_result = {
            "scan_report_id": scan_report_id,
            "repository_url": repository_url,
            "branch": branch,
            "commit_hash": commit_hash,
            "analysis_timestamp": utc_now().isoformat()
        }

        try:
            drift = await baseline_service.compare_with_baseline(
                current_scan=scan_report,
                repository_url=repository_url,
                branch=branch
            )
            analysis_result["drift_analysis"] = drift.dict() if drift else None
        except Exception as e:
            logger.warning(f"Drift analysis failed: {e}")
            analysis_result["drift_analysis"] = {"error": str(e)}

        try:
            policy_results = await policy_service.evaluate_all_policies(
                scan_report=scan_report,
                repository_url=repository_url,
                branch=branch,
                commit_hash=commit_hash,
                environment=environment
            )
            analysis_result["policy_evaluation"] = [result.dict() for result in policy_results]
        except Exception as e:
            logger.warning(f"Policy evaluation failed: {e}")
            analysis_result["policy_evaluation"] = {"error": str(e)}

        if create_baseline:
            try:
                baseline = await baseline_service.create_baseline(
                    scan_report=scan_report,
                    repository_url=repository_url,
                    branch=branch,
                    commit_hash=commit_hash,
                    created_by="api",
                    tags=["automated"]
                )
                analysis_result["new_baseline"] = baseline.dict()
            except Exception as e:
                logger.warning(f"Baseline creation failed: {e}")
                analysis_result["new_baseline"] = {"error": str(e)}

        recommendations = []

        if "drift_analysis" in analysis_result and isinstance(analysis_result["drift_analysis"], dict):
            drift_data = analysis_result["drift_analysis"]
            if drift_data.get("drift_severity") in ["critical", "high"]:
                recommendations.append("Significant security drift detected - review recent changes")
            if drift_data.get("new_findings"):
                recommendations.append(f"{len(drift_data['new_findings'])} new vulnerabilities found")

        if "policy_evaluation" in analysis_result and isinstance(analysis_result["policy_evaluation"], list):
            for policy_result in analysis_result["policy_evaluation"]:
                if not policy_result.get("compliant", True):
                    recommendations.append(f"Policy violation: {policy_result.get('policy_id')}")

        analysis_result["recommendations"] = recommendations

        return analysis_result

    except Exception as e:
        logger.error(f"Error in full security analysis: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
