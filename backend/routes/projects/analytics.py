import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.infrastructure.project_service import ProjectService
from utils.error_handling import SafeHTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Projects - Analytics"])

project_service = ProjectService()


@router.get("/{project_id}/stats", response_model=Dict[str, Any])
async def get_project_statistics(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        stats = await project_service.get_project_stats(project_id, str(current_user.id))
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise SafeHTTPException.internal_error("Failed to fetch project statistics", e)


@router.get("/analytics/overview", response_model=Dict[str, Any])
async def get_projects_analytics(
    current_user: User = Depends(get_current_user)
):
    try:
        analytics = await project_service.get_project_analytics(str(current_user.id))
        return analytics
    except Exception as e:
        raise SafeHTTPException.internal_error("Failed to fetch analytics", e)
