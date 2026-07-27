import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from database import scan_reports_collection
from models.report import ScanReport
from models.user import User
from routes.dependencies import get_current_user
from services.rules.policy_engine import (
    policy_service,
)
from utils.datetime_utils import utc_now
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(tags=["security - policies"])


@router.get("/policies")
async def get_policies(
    current_user: User = Depends(get_current_user),
    repository_url: Optional[str] = None,
    branch: str = "main",
    environment: str = "development"
):
    try:
        if repository_url:
            policies = await policy_service.get_applicable_policies(
                repository_url, branch, environment
            )
        else:
            policies = list(policy_service.policies_cache.values())
            if not policies:
                await policy_service.load_policies()
                policies = list(policy_service.policies_cache.values())

        return [policy.dict() for policy in policies]

    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/policies/evaluate")
async def evaluate_policies(
    scan_report_id: str,
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: str = "main",
    commit_hash: str = "HEAD",
    environment: str = "development"
):
    try:
        scan_report_doc = await scan_reports_collection.find_one({"report_id": scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")

        scan_report = ScanReport(**scan_report_doc)

        results = await policy_service.evaluate_all_policies(
            scan_report=scan_report,
            repository_url=repository_url,
            branch=branch,
            commit_hash=commit_hash,
            environment=environment
        )

        return [result.dict() for result in results]

    except Exception as e:
        logger.error(f"Error evaluating policies: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/policy-violations")
async def get_policy_violations(
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    status: str = Query("open", pattern="^(open|resolved|all)$")
):
    try:
        if not policy_service.violations_collection:
            raise HTTPException(status_code=503, detail="Database not available")

        query = {"repository_url": repository_url}
        if branch:
            query["branch"] = branch

        if status != "all":
            query["status"] = status

        since_date = utc_now() - timedelta(days=days)
        query["detected_at"] = {"$gte": since_date}

        cursor = policy_service.violations_collection.find(query).sort("detected_at", -1)
        violations = []

        async for violation_doc in cursor:
            violations.append(violation_doc)

        return violations

    except Exception as e:
        logger.error(f"Error getting policy violations: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/policy-compliance-report")
async def get_policy_compliance_report(
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: str = "main",
    days: int = Query(30, ge=1, le=365)
):
    try:
        report = await policy_service.get_policy_compliance_report(
            repository_url, branch, days
        )
        return report

    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/policies/update-from-git")
async def update_policies_from_git(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        background_tasks.add_task(policy_service.update_policy_from_git)
        return {"success": True, "message": "Policy update initiated"}

    except Exception as e:
        logger.error(f"Error updating policies from Git: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
