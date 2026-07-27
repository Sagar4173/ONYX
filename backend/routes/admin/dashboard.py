import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from models.project import Project
from models.report import ScanReport
from models.user import User
from routes.dependencies import require_admin
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


def ensure_tz_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        all_users = await User.find_all().to_list()
        total_users = len(all_users)

        users_by_role = {}
        users_by_status = {}
        new_users_24h = 0
        new_users_7d = 0
        new_users_30d = 0
        active_users_24h = 0

        for u in all_users:
            role = u.role.value if hasattr(u.role, 'value') else str(u.role)
            users_by_role[role] = users_by_role.get(role, 0) + 1

            user_status = u.status.value if hasattr(u.status, 'value') else str(u.status)
            users_by_status[user_status] = users_by_status.get(user_status, 0) + 1

            created_at = ensure_tz_aware(u.created_at)
            if created_at:
                if created_at >= last_24h:
                    new_users_24h += 1
                if created_at >= last_7d:
                    new_users_7d += 1
                if created_at >= last_30d:
                    new_users_30d += 1

            last_login = ensure_tz_aware(u.last_login)
            if last_login and last_login >= last_24h:
                active_users_24h += 1

        all_projects = await Project.find_all().to_list()
        total_projects = len(all_projects)

        projects_by_category = {}
        projects_by_status = {}
        projects_by_priority = {}

        for p in all_projects:
            cat = p.category.value if hasattr(p.category, 'value') else str(p.category) if p.category else 'unknown'
            projects_by_category[cat] = projects_by_category.get(cat, 0) + 1

            proj_status = p.status.value if hasattr(p.status, 'value') else str(p.status) if p.status else 'unknown'
            projects_by_status[proj_status] = projects_by_status.get(proj_status, 0) + 1

            priority = p.priority.value if hasattr(p.priority, 'value') else str(p.priority) if p.priority else 'unknown'
            projects_by_priority[priority] = projects_by_priority.get(priority, 0) + 1

        all_scans = await ScanReport.find_all().to_list()
        total_scans = len(all_scans)

        scans_by_status = {}
        scans_24h = 0
        scans_7d = 0
        total_findings = 0
        findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for scan in all_scans:
            scan_status = scan.status.value if hasattr(scan.status, 'value') else str(scan.status)
            scans_by_status[scan_status] = scans_by_status.get(scan_status, 0) + 1

            scan_created_at = ensure_tz_aware(scan.created_at)
            if scan_created_at:
                if scan_created_at >= last_24h:
                    scans_24h += 1
                if scan_created_at >= last_7d:
                    scans_7d += 1

            total_findings += scan.total_findings or 0
            if scan.findings_by_severity:
                for sev, count in scan.findings_by_severity.items():
                    if sev in findings_by_severity:
                        findings_by_severity[sev] += count or 0

        active_user_ratio = active_users_24h / max(total_users, 1)
        completed_scans = scans_by_status.get('completed', 0)
        failed_scans = scans_by_status.get('failed', 0)
        scan_success_rate = completed_scans / max(completed_scans + failed_scans, 1)
        critical_ratio = findings_by_severity['critical'] / max(total_findings, 1)

        health_score = min(100, max(0, int(
            (scan_success_rate * 40) +
            ((1 - critical_ratio) * 30) +
            (min(active_user_ratio * 100, 30))
        )))

        return {
            "users": {
                "total": total_users,
                "by_role": users_by_role,
                "by_status": users_by_status,
                "new_24h": new_users_24h,
                "new_7d": new_users_7d,
                "new_30d": new_users_30d,
                "active_24h": active_users_24h,
                "admin_count": users_by_role.get('admin', 0),
                "pending_verification": users_by_status.get('pending_verification', 0)
            },
            "projects": {
                "total": total_projects,
                "by_category": projects_by_category,
                "by_status": projects_by_status,
                "by_priority": projects_by_priority
            },
            "scans": {
                "total": total_scans,
                "by_status": scans_by_status,
                "last_24h": scans_24h,
                "last_7d": scans_7d,
                "total_findings": total_findings,
                "findings_by_severity": findings_by_severity,
                "success_rate": round(scan_success_rate * 100, 1)
            },
            "system": {
                "health_score": health_score,
                "last_updated": now.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to fetch admin statistics")
        )
