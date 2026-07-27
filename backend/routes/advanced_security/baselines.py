import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Baselines"])


@router.get("/baseline/status")
async def get_baseline_status(
    repository: Optional[str] = Query(None),
    branch: Optional[str] = Query("main"),
    current_user: User = Depends(get_current_user)
):
    baseline_manager = ServiceRegistry.get_baseline_manager()
    if not baseline_manager:
        raise HTTPException(status_code=503, detail="Baseline manager not initialized")

    try:
        if repository:
            response = await baseline_manager.get_status(repository, branch)
        else:
            response = await baseline_manager.get_all_status()
        return response
    except Exception as e:
        logger.error(f"Error getting baseline status: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Baseline status retrieval"))
