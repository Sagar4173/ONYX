import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as fastapi_status

from models.project import Project
from models.report import ScanReport
from models.user import User
from routes.dependencies import require_admin
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/projects/all")
async def get_all_projects_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        query_filters = {}

        if status:
            query_filters["status"] = status

        if category:
            query_filters["category"] = category

        if query_filters:
            query = Project.find(query_filters)
        else:
            query = Project.find_all()

        if search:
            query = Project.find({
                **query_filters,
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            })

        total = await query.count()

        sort_direction = -1 if sort_order == "desc" else 1
        projects = await query.sort([(sort_by, sort_direction)]).skip(skip).limit(limit).to_list()

        enriched_projects = []
        for p in projects:
            owner = await User.find_one(User.id == p.owner_id) if p.owner_id else None

            project_scans = await ScanReport.find(
                ScanReport.project_id == str(p.id)
            ).to_list()

            total_scans = len(project_scans)
            total_findings = sum(s.total_findings or 0 for s in project_scans)
            critical_findings = sum(
                (s.findings_by_severity or {}).get('critical', 0)
                for s in project_scans
            )

            last_scan = None
            if project_scans:
                sorted_scans = sorted(project_scans, key=lambda x: x.created_at or datetime.min, reverse=True)
                if sorted_scans:
                    last_scan = {
                        "id": str(sorted_scans[0].id),
                        "status": sorted_scans[0].status.value if hasattr(sorted_scans[0].status, 'value') else str(sorted_scans[0].status),
                        "created_at": sorted_scans[0].created_at.isoformat() if sorted_scans[0].created_at else None,
                        "total_findings": sorted_scans[0].total_findings
                    }

            project_data = {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category.value if hasattr(p.category, 'value') else str(p.category) if p.category else None,
                "status": p.status.value if hasattr(p.status, 'value') else str(p.status) if p.status else None,
                "priority": p.priority.value if hasattr(p.priority, 'value') else str(p.priority) if p.priority else None,
                "repository_url": p.repository.url if p.repository else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                "owner": {
                    "id": str(owner.id) if owner else None,
                    "username": owner.username if owner else "Unknown",
                    "email": owner.email if owner else None
                } if owner else None,
                "owner_id": p.owner_id,
                "total_scans": total_scans,
                "total_findings": total_findings,
                "critical_findings": critical_findings,
                "last_scan": last_scan,
                "team_member_count": len(p.team_members) if p.team_members else 0
            }
            enriched_projects.append(project_data)

        return {
            "projects": enriched_projects,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(enriched_projects) < total
            }
        }

    except Exception as e:
        logger.error(f"Error fetching projects for admin: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to fetch projects")
        )


@router.delete("/projects/{project_id}")
async def delete_project_admin(
    project_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    try:
        project = await Project.find_one(Project.id == project_id)
        if not project:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        project_name = project.name
        await project.delete()

        await ScanReport.find(ScanReport.project_id == project_id).delete()

        logger.info(f"Admin {current_user.username} deleted project {project_name}")

        return {"message": f"Project {project_name} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to delete project")
        )
