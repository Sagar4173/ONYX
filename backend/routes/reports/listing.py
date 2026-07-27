"""Report listing endpoints."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.report import ScanReport, ScanStatus, SeverityLevel
from models.user import User
from routes.dependencies import get_current_user
from routes.reports.dependencies import get_user_project_ids
from utils.error_handling import SafeHTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_reports(
    limit: int = Query(50, ge=1, le=1000, description="Number of reports to return"),
    skip: int = Query(0, ge=0, description="Number of reports to skip"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    status: Optional[ScanStatus] = Query(None, description="Filter by scan status"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    severity_filter: Optional[SeverityLevel] = Query(None, description="Filter by minimum severity"),
    days_back: Optional[int] = Query(None, ge=1, le=365, description="Filter by days back from now"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """List scan reports with filtering and pagination"""
    try:
        user_id = str(current_user.id)
        accessible_project_ids = await get_user_project_ids(user_id)

        filters = {}
        if accessible_project_ids:
            filters["$or"] = [
                {"project_id": {"$in": accessible_project_ids}},
                {"user_id": user_id},
            ]
        else:
            filters["user_id"] = user_id

        if project_id:
            if project_id not in accessible_project_ids:
                raise HTTPException(status_code=403, detail="You don't have access to this project")
            filters["project_id"] = project_id
            filters.pop("$or", None)

        if project_name:
            filters["project_name"] = {"$regex": project_name, "$options": "i"}
        if status:
            filters["status"] = status.value if hasattr(status, "value") else status
        if branch:
            filters["git_metadata.branch"] = branch
        if days_back:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            filters["created_at"] = {"$gte": cutoff_date}
        if severity_filter:
            severity_key = f"findings_by_severity.{severity_filter.value if hasattr(severity_filter, 'value') else severity_filter}"
            filters[severity_key] = {"$gt": 0}

        try:
            db_reports = await ScanReport.find(filters).sort([("created_at", -1)]).skip(skip).limit(limit).to_list()
            total = await ScanReport.find(filters).count()

            formatted_reports = []
            for report in db_reports:
                formatted_reports.append({
                    "id": str(report.id),
                    "project_name": report.project_name,
                    "scan_id": report.scan_id,
                    "repository_url": report.git_metadata.repository_url if report.git_metadata else "",
                    "branch": report.git_metadata.branch if report.git_metadata else "main",
                    "status": report.status.value if hasattr(report.status, "value") else report.status,
                    "created_at": report.created_at.isoformat() if report.created_at else datetime.now(timezone.utc).isoformat(),
                    "total_findings": report.total_findings,
                    "findings_by_severity": report.findings_by_severity,
                    "duration_seconds": report.duration_seconds or 0,
                    "commit_hash": report.git_metadata.commit_hash if report.git_metadata else "",
                })

            if formatted_reports:
                return {
                    "reports": formatted_reports,
                    "pagination": {
                        "total": total,
                        "skip": skip,
                        "limit": limit,
                        "has_more": skip + len(formatted_reports) < total,
                    },
                    "filters": {
                        "project_id": project_id,
                        "project_name": project_name,
                        "status": status,
                        "branch": branch,
                        "severity_filter": severity_filter,
                        "days_back": days_back,
                    },
                }
        except Exception as db_error:
            logger.warning(f"Database error: {db_error}")

        return {
            "reports": [],
            "pagination": {"total": 0, "skip": skip, "limit": limit, "has_more": False},
            "filters": {
                "project_id": project_id,
                "project_name": project_name,
                "status": status,
                "branch": branch,
                "severity_filter": severity_filter,
                "days_back": days_back,
            },
        }
    except Exception as e:
        raise SafeHTTPException.internal_error("Failed to retrieve reports", e)


@router.get("/project/{project_name}")
async def get_project_reports(
    project_name: str,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all reports for a specific project"""
    try:
        user_id = str(current_user.id)
        accessible_project_ids = await get_user_project_ids(user_id)

        from beanie.operators import In, Or

        user_access_conditions = [ScanReport.user_id == user_id]
        if accessible_project_ids:
            user_access_conditions.append(In(ScanReport.project_id, accessible_project_ids))

        query = ScanReport.find(
            ScanReport.project_name == project_name,
            Or(*user_access_conditions),
        )

        total = await query.count()
        reports = await query.sort(-ScanReport.created_at).skip(skip).limit(limit).to_list()

        if not reports:
            raise HTTPException(status_code=404, detail="No reports found for this project")

        latest_report = reports[0]
        recent_reports = reports[:10]
        trend_data = [
            {
                "scan_date": report.created_at,
                "total_findings": report.total_findings,
                "critical_count": report.findings_by_severity.get("critical", 0),
                "high_count": report.findings_by_severity.get("high", 0),
            }
            for report in recent_reports
        ]

        return {
            "project_name": project_name,
            "project_statistics": {
                "total_scans": total,
                "latest_scan": {
                    "id": str(latest_report.id),
                    "created_at": latest_report.created_at,
                    "status": latest_report.status.value,
                    "total_findings": latest_report.total_findings,
                    "findings_by_severity": latest_report.findings_by_severity,
                },
            },
            "recent_trend": trend_data,
            "reports": [
                {
                    "id": str(report.id),
                    "scan_id": report.scan_id,
                    "created_at": report.created_at,
                    "status": report.status.value,
                    "branch": report.git_metadata.branch,
                    "commit_hash": report.git_metadata.commit_hash,
                    "total_findings": report.total_findings,
                    "findings_by_severity": report.findings_by_severity,
                }
                for report in reports
            ],
            "pagination": {"total": total, "limit": limit, "skip": skip},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project reports for {project_name}: {e}")
        raise SafeHTTPException.internal_error("Failed to retrieve project reports", e)
