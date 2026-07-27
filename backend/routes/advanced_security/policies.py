import logging

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

from .schemas import PolicyEnforceRequest, PolicyEvaluationRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Policies"])


@router.post("/policy/evaluate")
async def evaluate_policy(
    request: PolicyEvaluationRequest,
    current_user: User = Depends(get_current_user)
):
    policy_engine = ServiceRegistry.get_policy_engine()
    if not policy_engine:
        raise HTTPException(status_code=503, detail="Policy engine not initialized")

    try:
        if not request.repository or not request.commit_hash:
            raise HTTPException(status_code=400, detail="Repository and commit_hash are required")

        response = await policy_engine.evaluate(
            repository=request.repository,
            commit_hash=request.commit_hash,
            policies=request.policies
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating policy: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Policy evaluation"))


@router.post("/policy/enforce")
async def enforce_security_policy(
    request: PolicyEnforceRequest,
    current_user: User = Depends(get_current_user)
):
    policy_engine = ServiceRegistry.get_policy_engine()
    if not policy_engine:
        raise HTTPException(status_code=503, detail="Policy engine not initialized")

    try:
        enforcement_result = await policy_engine.enforce_policy(request.policy)
        return {
            "enforcement_result": enforcement_result,
            "status": "enforced"
        }
    except Exception as e:
        logger.error(f"Policy enforcement error: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Policy enforcement"))
