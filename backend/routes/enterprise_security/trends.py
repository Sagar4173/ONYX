import logging
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.security.security_trends import (
    TrendPeriod,
    get_security_trends_service,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trends", tags=["Enterprise Security - Trends"])


class TrendPeriodEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"


@router.get("/dashboard")
async def get_trends_dashboard(
    project_id: Optional[str] = Query(None, description="Filter by project")
):
    try:
        trends_service = get_security_trends_service()
        dashboard_data = await trends_service.get_dashboard_data(project_id)

        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/severity")
async def get_severity_trends(
    project_id: Optional[str] = Query(None),
    period: TrendPeriodEnum = Query(TrendPeriodEnum.weekly),
    limit: int = Query(12, ge=1, le=52)
):
    try:
        trends_service = get_security_trends_service()

        trend_period = TrendPeriod(period.value)

        trends = await trends_service.get_severity_trends(
            project_id=project_id,
            period=trend_period,
            limit=limit
        )

        return {
            "success": True,
            "period": period.value,
            "data_points": len(trends.data_points),
            "direction": trends.direction.value,
            "improvement_percentage": trends.improvement_percentage,
            "avg_security_score": trends.avg_security_score,
            "projected_score_30d": trends.projected_security_score_30d,
            "time_to_target": trends.time_to_target_score,
            "trends": [
                {
                    "date": dp.timestamp.isoformat(),
                    "security_score": dp.security_score,
                    "risk_score": dp.risk_score,
                    "severity_counts": dp.severity_counts.to_dict(),
                    "fixed": dp.fixed_count,
                    "new": dp.new_count
                }
                for dp in trends.data_points
            ],
            "notable_changes": trends.notable_changes
        }
    except Exception as e:
        logger.error(f"Error fetching severity trends: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/metrics")
async def get_current_metrics(
    project_id: Optional[str] = Query(None)
):
    try:
        trends_service = get_security_trends_service()
        metrics = await trends_service.get_current_metrics(project_id)

        return {
            "success": True,
            "timestamp": metrics.timestamp.isoformat(),
            "security_score": metrics.security_score,
            "risk_score": metrics.risk_score,
            "severity_counts": metrics.severity_counts.to_dict(),
            "open_findings": metrics.open_findings,
            "fixed_last_7d": metrics.fixed_last_7d,
            "fixed_last_30d": metrics.fixed_last_30d,
            "new_last_7d": metrics.new_last_7d,
            "new_last_30d": metrics.new_last_30d,
            "mttr_hours": metrics.mttr_hours,
            "compliance_rate": metrics.compliance_rate,
            "coverage_percentage": metrics.coverage_percentage
        }
    except Exception as e:
        logger.error(f"Error fetching current metrics: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/comparison")
async def get_period_comparison(
    project_id: Optional[str] = Query(None)
):
    try:
        trends_service = get_security_trends_service()
        comparison = await trends_service.get_comparison_report(project_id)

        return {
            "success": True,
            "data": comparison
        }
    except Exception as e:
        logger.error(f"Error fetching period comparison: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
