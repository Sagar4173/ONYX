import logging

from fastapi import APIRouter, Depends, HTTPException

from models.user import User, UserRole
from routes.dependencies import auth_service, get_current_user
from routes.enterprise.dependencies import get_database
from routes.enterprise.schemas import RetentionPolicyCreate
from services.analytics.data_retention_service import (
    RetentionAction,
    RetentionPolicyType,
    get_retention_service,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/retention/policies")
async def create_retention_policy(
    policy: RetentionPolicyCreate,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN)),
    db=Depends(get_database),
):
    try:
        retention_service = get_retention_service(db)

        result = await retention_service.create_retention_policy(
            policy_type=RetentionPolicyType(policy.policy_type),
            retention_days=policy.retention_days,
            action=RetentionAction(policy.action),
            enabled=policy.enabled,
            metadata=policy.metadata,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/retention/policies/{policy_id}/execute")
async def execute_retention_policy(
    policy_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN)),
    db=Depends(get_database),
):
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.execute_retention_policy(policy_id)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/retention/policies/execute-all")
async def execute_all_retention_policies(
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN)),
    db=Depends(get_database),
):
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.execute_all_policies()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/retention/statistics")
async def get_retention_statistics(
    current_user: User = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.get_retention_statistics()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/retention/initialize-defaults")
async def initialize_default_retention_policies(
    current_user: User = Depends(auth_service.require_role(UserRole.ADMIN)),
    db=Depends(get_database),
):
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.initialize_default_policies()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
