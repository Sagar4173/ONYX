"""
Project Management API Routes for ONYX Platform
Handles project CRUD operations, team management, and analytics
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.project import (
    Project, ProjectCreateRequest, ProjectUpdateRequest, 
    TeamMemberRequest, ProjectResponse, ProjectStatus,
    ProjectCategory, ProjectPriority
)
from models.user import User
from services.infrastructure.project_service import ProjectService
from services.auth.auth_service import AuthService

router = APIRouter(prefix="/projects", tags=["Projects"])
security = HTTPBearer()

# Initialize services
project_service = ProjectService()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project
    
    - **name**: Project name (unique per user)
    - **description**: Optional project description
    - **category**: Project category (web_application, api_service, etc.)
    - **priority**: Project priority (low, medium, high, critical)
    - **repository**: Repository configuration
    - **scan_config**: Optional scan configuration
    - **tags**: Optional project tags
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🚀 Creating project with data: {project_data.model_dump()}")
        logger.info(f"👤 Current user: {current_user.username} (ID: {current_user.id})")
        
        project = await project_service.create_project(project_data, str(current_user.id))
        logger.info(f"✅ Project created successfully: {project.name}")
        
        # Convert to response with proper ID serialization
        project_dict = project.model_dump()
        project_dict["id"] = str(project.id)
        return ProjectResponse.model_validate(project_dict)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Project creation failed: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
async def get_user_projects(
    status_filter: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    category: Optional[ProjectCategory] = Query(None, description="Filter by project category"),
    priority: Optional[ProjectPriority] = Query(None, description="Filter by project priority"),
    search: Optional[str] = Query(None, description="Search in project name, description, or tags"),
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of projects to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's projects with optional filtering and pagination
    
    Returns projects owned by the user or where user is a team member.
    """
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
        
        # Convert to summary format for list view
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed project information by ID
    
    Returns full project details including team members, scan configuration, and statistics.
    """
    project = await project_service.get_project_by_id(project_id, str(current_user.id))
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Convert to response with proper ID serialization
    project_dict = project.model_dump()
    project_dict["id"] = str(project.id)
    return ProjectResponse.model_validate(project_dict)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update project information
    
    Requires 'manage_settings' permission on the project.
    """
    try:
        project = await project_service.update_project(
            project_id, update_data, str(current_user.id)
        )
        # Convert to response with proper ID serialization
        project_dict = project.model_dump()
        project_dict["id"] = str(project.id)
        return ProjectResponse.model_validate(project_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete project (soft delete)
    
    Only the project owner can delete a project.
    """
    try:
        await project_service.delete_project(project_id, str(current_user.id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


@router.post("/{project_id}/team", response_model=ProjectResponse)
async def add_team_member(
    project_id: str,
    member_data: TeamMemberRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Add a team member to the project
    
    Requires 'manage_team' permission on the project.
    
    - **email**: Email of the user to add
    - **role**: Role in the project (admin, developer, viewer, scanner)
    - **permissions**: List of specific permissions
    """
    try:
        project = await project_service.add_team_member(
            project_id, member_data, str(current_user.id)
        )
        return ProjectResponse.model_validate(project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team member: {str(e)}"
        )


@router.delete("/{project_id}/team/{member_user_id}", response_model=ProjectResponse)
async def remove_team_member(
    project_id: str,
    member_user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Remove a team member from the project
    
    Requires 'manage_team' permission on the project.
    Cannot remove the project owner.
    """
    try:
        project = await project_service.remove_team_member(
            project_id, member_user_id, str(current_user.id)
        )
        return ProjectResponse.model_validate(project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}"
        )


@router.get("/{project_id}/stats", response_model=Dict[str, Any])
async def get_project_statistics(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed project statistics and analytics
    
    Includes vulnerability trends, security scores, team information, and recent activity.
    """
    try:
        stats = await project_service.get_project_stats(project_id, str(current_user.id))
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project statistics: {str(e)}"
        )


@router.get("/analytics/overview", response_model=Dict[str, Any])
async def get_projects_analytics(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's overall project analytics
    
    Provides overview of all projects, including:
    - Total projects and scans
    - Vulnerability distribution
    - Security score averages
    - Category and priority distributions
    - Recent activity
    """
    try:
        analytics = await project_service.get_project_analytics(str(current_user.id))
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )


@router.get("/templates", response_model=Dict[str, Any])
async def get_project_templates():
    """
    Get project templates and categories
    
    Returns available project categories, default configurations, and role templates.
    """
    return {
        "categories": [
            {
                "value": "web_application",
                "label": "Web Application",
                "description": "Frontend and full-stack web applications",
                "default_scanners": ["sast", "secrets", "container"]
            },
            {
                "value": "mobile_application", 
                "label": "Mobile Application",
                "description": "iOS and Android mobile applications",
                "default_scanners": ["sast", "secrets"]
            },
            {
                "value": "api_service",
                "label": "API Service",
                "description": "REST APIs and microservices",
                "default_scanners": ["sast", "secrets", "container", "infrastructure"]
            },
            {
                "value": "infrastructure",
                "label": "Infrastructure",
                "description": "Infrastructure as Code (IaC) projects",
                "default_scanners": ["infrastructure", "secrets"]
            },
            {
                "value": "microservice",
                "label": "Microservice", 
                "description": "Individual microservice components",
                "default_scanners": ["sast", "secrets", "container"]
            },
            {
                "value": "library",
                "label": "Library/Package",
                "description": "Reusable libraries and packages",
                "default_scanners": ["sast", "secrets"]
            },
            {
                "value": "other",
                "label": "Other",
                "description": "Other types of projects",
                "default_scanners": ["sast", "secrets"]
            }
        ],
        "priorities": [
            {"value": "low", "label": "Low", "color": "#10b981"},
            {"value": "medium", "label": "Medium", "color": "#f59e0b"},
            {"value": "high", "label": "High", "color": "#ef4444"},
            {"value": "critical", "label": "Critical", "color": "#dc2626"}
        ],
        "roles": [
            {
                "value": "admin",
                "label": "Project Admin",
                "permissions": ["scan", "view_reports", "manage_settings", "manage_team"],
                "description": "Full project management access"
            },
            {
                "value": "developer",
                "label": "Developer", 
                "permissions": ["scan", "view_reports", "manage_settings"],
                "description": "Development and scanning access"
            },
            {
                "value": "viewer",
                "label": "Viewer",
                "permissions": ["view_reports"],
                "description": "Read-only access to reports"
            },
            {
                "value": "scanner",
                "label": "Scanner",
                "permissions": ["scan", "view_reports"],
                "description": "Can run scans and view results"
            }
        ],
        "scan_types": [
            {
                "value": "sast",
                "label": "Static Analysis (SAST)",
                "description": "Static code analysis for vulnerabilities"
            },
            {
                "value": "secrets",
                "label": "Secret Detection", 
                "description": "Detect exposed secrets and credentials"
            },
            {
                "value": "container",
                "label": "Container Security",
                "description": "Container and image vulnerability scanning"
            },
            {
                "value": "infrastructure",
                "label": "Infrastructure as Code",
                "description": "IaC security configuration scanning"
            }
        ]
    }


@router.get("/templates/categories", response_model=Dict[str, Any])
async def get_project_template_categories():
    """
    Get project template categories (backward compatibility)
    """
    # Reuse the same data from get_project_templates
    templates_data = await get_project_templates()
    return templates_data
