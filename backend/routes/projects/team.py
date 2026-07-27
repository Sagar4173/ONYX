import logging

from fastapi import APIRouter, Depends, HTTPException

from models.project import ProjectResponse, TeamMemberRequest
from models.user import User
from routes.dependencies import get_current_user
from services.infrastructure.project_service import ProjectService
from utils.error_handling import SafeHTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Projects - Team"])

project_service = ProjectService()


@router.post("/{project_id}/team", response_model=ProjectResponse)
async def add_team_member(
    project_id: str,
    member_data: TeamMemberRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        project = await project_service.add_team_member(
            project_id, member_data, str(current_user.id)
        )
        return ProjectResponse.model_validate(project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise SafeHTTPException.internal_error("Failed to add team member", e)


@router.delete("/{project_id}/team/{member_user_id}", response_model=ProjectResponse)
async def remove_team_member(
    project_id: str,
    member_user_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        project = await project_service.remove_team_member(
            project_id, member_user_id, str(current_user.id)
        )
        return ProjectResponse.model_validate(project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise SafeHTTPException.internal_error("Failed to remove team member", e)
