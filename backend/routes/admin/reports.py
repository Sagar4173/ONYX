import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as fastapi_status

from models.report import ScanReport
from models.user import User
from routes.dependencies import require_admin
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/reports/all")
async def get_all_reports_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        query_filters = {}

        if status:
            query_filters["status"] = status

        if query_filters:
            query = ScanReport.find(query_filters)
        else:
            query = ScanReport.find_all()

        if search:
            query = ScanReport.find({
                **query_filters,
                "project_name": {"$regex": search, "$options": "i"}
            })

        if severity:
            severity_key = f"findings_by_severity.{severity}"
            query = query.find({severity_key: {"$gt": 0}})

        total = await query.count()

        sort_direction = -1 if sort_order == "desc" else 1
        reports = await query.sort([(sort_by, sort_direction)]).skip(skip).limit(limit).to_list()

        enriched_reports = []
        for r in reports:
            user = None
            if r.user_id:
                user = await User.find_one(User.id == r.user_id)

            report_data = {
                "id": str(r.id),
                "scan_id": r.scan_id,
                "project_name": r.project_name,
                "project_id": r.project_id,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                "total_findings": r.total_findings,
                "findings_by_severity": r.findings_by_severity,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds,
                "repository_url": r.git_metadata.repository_url if r.git_metadata else None,
                "branch": r.git_metadata.branch if r.git_metadata else None,
                "user": {
                    "id": str(user.id) if user else None,
                    "username": user.username if user else "Unknown",
                    "email": user.email if user else None
                } if user else None,
                "user_id": r.user_id
            }
            enriched_reports.append(report_data)

        return {
            "reports": enriched_reports,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(enriched_reports) < total
            }
        }

    except Exception as e:
        logger.error(f"Error fetching reports for admin: {e}")
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to fetch reports")
        )
