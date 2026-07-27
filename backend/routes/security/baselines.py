import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from database import scan_reports_collection
from models.report import ScanReport
from models.user import User
from routes.dependencies import get_current_user
from services.scanning.baseline import baseline_service
from utils.error_handling import get_safe_error_detail

from .schemas import BaselineCreateRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Security - Baselines"])


@router.post("/baselines")
async def create_baseline(request: BaselineCreateRequest, current_user: User = Depends(get_current_user), created_by: str = "api") -> Dict[str, Any]:
    try:
        scan_report_doc = await scan_reports_collection.find_one({"report_id": request.scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")

        scan_report = ScanReport(**scan_report_doc)

        baseline = await baseline_service.create_baseline(
            scan_report=scan_report,
            repository_url=request.repository_url,
            branch=request.branch,
            commit_hash=request.commit_hash,
            created_by=created_by,
            tags=request.tags
        )

        return {"success": True, "baseline": baseline.dict()}

    except Exception as e:
        logger.error(f"Error creating baseline: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/baselines")
async def get_baselines(
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    try:
        baselines = await baseline_service.get_baselines_for_repository(
            repository_url, branch, limit
        )
        return [baseline.dict() for baseline in baselines]

    except Exception as e:
        logger.error(f"Error getting baselines: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/drift-analysis")
async def analyze_drift(
    scan_report_id: str,
    current_user: User = Depends(get_current_user),
    baseline_id: Optional[str] = None,
    repository_url: Optional[str] = None,
    branch: Optional[str] = None
):
    try:
        scan_report_doc = await scan_reports_collection.find_one({"report_id": scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")

        scan_report = ScanReport(**scan_report_doc)

        drift = await baseline_service.compare_with_baseline(
            current_scan=scan_report,
            baseline_id=baseline_id,
            repository_url=repository_url,
            branch=branch
        )

        if not drift:
            raise HTTPException(status_code=404, detail="No baseline found for comparison")

        return drift.dict()

    except Exception as e:
        logger.error(f"Error analyzing drift: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/drift-history")
async def get_drift_history(
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    try:
        drift_analyses = await baseline_service.get_drift_analysis(
            repository_url, branch, days
        )
        return [drift.dict() for drift in drift_analyses]

    except Exception as e:
        logger.error(f"Error getting drift history: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/regression-alerts")
async def get_regression_alerts(
    repository_url: str,
    current_user: User = Depends(get_current_user),
    branch: Optional[str] = None,
    days: int = Query(7, ge=1, le=30)
):
    try:
        alerts = await baseline_service.get_regression_alerts(
            repository_url, branch, days
        )
        return [alert.dict() for alert in alerts]

    except Exception as e:
        logger.error(f"Error getting regression alerts: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/trends")
async def get_security_trends(
    repository_url: str,
    branch: str,
    current_user: User = Depends(get_current_user),
    days: int = Query(90, ge=7, le=365)
):
    try:
        trends = await baseline_service.generate_trend_analysis(
            repository_url, branch, days
        )
        return trends

    except Exception as e:
        logger.error(f"Error getting security trends: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
