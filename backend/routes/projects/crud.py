import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from models.project import (
    ProjectCategory,
    ProjectCreateRequest,
    ProjectPriority,
    ProjectResponse,
    ProjectStatus,
    ProjectUpdateRequest,
)
from models.user import User
from routes.dependencies import get_current_user
from services.infrastructure.project_service import ProjectService
from utils.error_handling import SafeHTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Projects - CRUD"])

project_service = ProjectService()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Creating project for user: {current_user.username}")

        project = await project_service.create_project(project_data, str(current_user.id))
        logger.info(f"Project created successfully: {project.name}")

        project_dict = project.model_dump()
        project_dict["id"] = str(project.id)
        return ProjectResponse.model_validate(project_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise SafeHTTPException.internal_error("Project creation", e)


@router.get("/", response_model=Dict[str, Any])
async def get_user_projects(
    status_filter: Optional[ProjectStatus] = Query(None),
    category: Optional[ProjectCategory] = Query(None),
    priority: Optional[ProjectPriority] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    try:
        projects, total = await project_service.get_user_projects(
            user_id=str(current_user.id),
            status_filter=status_filter,
            category_filter=category,
            priority_filter=priority,
            search_query=search,
            skip=skip,
            limit=limit
        )

        project_summaries = [project.to_dict_summary() for project in projects]

        return {
            "projects": project_summaries,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total
            }
        }
    except Exception as e:
        raise SafeHTTPException.internal_error("Fetching projects", e)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    project = await project_service.get_project_by_id(project_id, str(current_user.id))
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    project_dict = project.model_dump()
    project_dict["id"] = str(project.id)
    return ProjectResponse.model_validate(project_dict)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        project = await project_service.update_project(
            project_id, update_data, str(current_user.id)
        )
        project_dict = project.model_dump()
        project_dict["id"] = str(project.id)
        return ProjectResponse.model_validate(project_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise SafeHTTPException.internal_error("Project update", e)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        await project_service.delete_project(project_id, str(current_user.id))
    except HTTPException:
        raise
    except Exception as e:
        raise SafeHTTPException.internal_error("Project deletion", e)
