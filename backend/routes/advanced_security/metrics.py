import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Metrics"])


@router.get("/metrics/security-score")
async def get_security_score(
    current_user: User = Depends(get_current_user)
):
    try:
        metrics_engine = ServiceRegistry.get_security_metrics()
        if metrics_engine:
            score_data = await metrics_engine.calculate_security_score()
            return score_data
        return {"score": 0, "metrics": {}, "recommendations": [], "message": "Metrics engine not initialized"}
    except Exception as e:
        logger.error(f"Error getting security score: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Security score calculation"))


@router.get("/metrics/dashboard")
async def get_security_metrics_dashboard(
    current_user: User = Depends(get_current_user)
):
    try:
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }

        rule_parser = ServiceRegistry.get_rule_parser()
        rule_tester = ServiceRegistry.get_rule_tester()
        baseline_manager = ServiceRegistry.get_baseline_manager()
        policy_engine = ServiceRegistry.get_policy_engine()

        if rule_parser:
            try:
                metrics["rule_parser_stats"] = await rule_parser.get_stats()
            except Exception:
                metrics["rule_parser_stats"] = {}

        if rule_tester:
            try:
                metrics["testing_stats"] = await rule_tester.get_stats()
            except Exception:
                metrics["testing_stats"] = {}

        if baseline_manager:
            try:
                metrics["baseline_stats"] = await baseline_manager.get_stats()
            except Exception:
                metrics["baseline_stats"] = {}

        if policy_engine:
            try:
                metrics["policy_stats"] = await policy_engine.get_stats()
            except Exception:
                metrics["policy_stats"] = {}

        return metrics
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Security metrics retrieval"))
