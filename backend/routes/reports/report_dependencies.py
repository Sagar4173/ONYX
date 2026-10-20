"""Shared dependencies for report route modules."""
import logging
from typing import List, Optional

from bson import ObjectId

from models.project import Project
from services.infrastructure.project_service import ProjectService

logger = logging.getLogger(__name__)

AUTO_FIX_WRITE_PERMISSION = "scan"


async def get_user_project_ids(user_id: str) -> List[str]:
    """Get list of project IDs accessible to the user"""
    projects = await Project.find(
        {
            "$or": [
                {"owner_id": user_id},
                {"team_members.user_id": user_id},
            ]
        }
    ).to_list()
    return [str(p.id) for p in projects]


async def get_accessible_scan_report(scan_id: str, user_id: str) -> Optional[object]:
    """
    Fetch a ScanReport only if the user owns it or belongs to its project.

    Mirrors the access logic in routes/reports/detail.py so AI chat, auto-fix,
    and triage enforce the same data isolation as the report endpoints.
    Returns None when the report does not exist or the user has no access.
    """
    from bson import ObjectId
    from models.report import ScanReport

    report = None
    if ObjectId.is_valid(scan_id):
        try:
            report = await ScanReport.get(ObjectId(scan_id))
        except Exception:
            report = None

    if not report:
        try:
            report = await ScanReport.find_one({"scan_id": scan_id})
        except Exception:
            report = None

    if not report:
        return None

    accessible_project_ids = await get_user_project_ids(user_id)
    report_user_id = getattr(report, "user_id", None)
    report_project_id = getattr(report, "project_id", None)

    has_access = (
        report_user_id == user_id
        or (report_project_id and report_project_id in accessible_project_ids)
    )
    return report if has_access else None


async def user_can_write_auto_fix(report, user_id: str) -> bool:
    """Check whether a user may run auto-fix write actions on a report."""
    project_id = getattr(report, "project_id", None)
    if not project_id:
        return getattr(report, "user_id", None) == user_id

    project = None
    try:
        if ObjectId.is_valid(str(project_id)):
            project = await Project.get(ObjectId(str(project_id)))
        else:
            project = await Project.find_one({"project_id": str(project_id)})
    except Exception:
        logger.warning(
            "Auto-fix permission lookup failed for report %s",
            getattr(report, "scan_id", "unknown"),
            exc_info=True,
        )
        return False

    if project is None:
        return getattr(report, "user_id", None) == user_id

    return await ProjectService().user_has_permission(
        project, user_id, AUTO_FIX_WRITE_PERMISSION
    )
