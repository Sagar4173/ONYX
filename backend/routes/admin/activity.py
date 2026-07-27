import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from models.project import Project
from models.report import ScanReport
from models.user import User
from routes.admin.dashboard import ensure_tz_aware
from routes.dependencies import require_admin
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/activity/recent")
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        activities = []
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        recent_users = await User.find_all().sort([("created_at", -1)]).limit(20).to_list()
        for u in recent_users:
            created_at = ensure_tz_aware(u.created_at)
            if created_at:
                activities.append({
                    "type": "user_registration",
                    "icon": "user",
                    "title": f"New user registered: {u.username}",
                    "description": f"{u.email} ({u.role.value if hasattr(u.role, 'value') else u.role})",
                    "timestamp": created_at.isoformat(),
                    "entity_id": str(u.id),
                    "entity_type": "user"
                })

        for u in recent_users:
            last_login = ensure_tz_aware(u.last_login)
            if last_login and last_login > seven_days_ago:
                activities.append({
                    "type": "user_login",
                    "icon": "login",
                    "title": f"User login: {u.username}",
                    "description": f"Last login from {u.organization or 'Unknown organization'}",
                    "timestamp": last_login.isoformat(),
                    "entity_id": str(u.id),
                    "entity_type": "user"
                })

        recent_projects = await Project.find_all().sort([("created_at", -1)]).limit(20).to_list()
        for p in recent_projects:
            created_at = ensure_tz_aware(p.created_at)
            if created_at:
                owner = await User.find_one(User.id == p.owner_id) if p.owner_id else None
                activities.append({
                    "type": "project_created",
                    "icon": "folder",
                    "title": f"Project created: {p.name}",
                    "description": f"By {owner.username if owner else 'Unknown'}",
                    "timestamp": created_at.isoformat(),
                    "entity_id": str(p.id),
                    "entity_type": "project"
                })

        recent_scans = await ScanReport.find_all().sort([("created_at", -1)]).limit(30).to_list()
        for s in recent_scans:
            scan_created_at = ensure_tz_aware(s.created_at)
            if scan_created_at:
                scan_status = s.status.value if hasattr(s.status, 'value') else str(s.status)
                icon = "check" if scan_status == "completed" else "x" if scan_status == "failed" else "clock"

                activities.append({
                    "type": f"scan_{scan_status}",
                    "icon": icon,
                    "title": f"Scan {scan_status}: {s.project_name}",
                    "description": f"{s.total_findings or 0} findings" if scan_status == "completed" else "",
                    "timestamp": scan_created_at.isoformat(),
                    "entity_id": str(s.id),
                    "entity_type": "scan"
                })

        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "activities": activities[:limit],
            "total": len(activities)
        }

    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to fetch activity")
        )


@router.get("/users/{user_id}/activity")
async def get_user_activity_admin(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        activities = []

        user_projects = await Project.find(Project.owner_id == user_id).to_list()
        for p in user_projects:
            if p.created_at:
                activities.append({
                    "type": "project_created",
                    "icon": "folder",
                    "title": f"Created project: {p.name}",
                    "description": p.description[:100] if p.description else "",
                    "timestamp": p.created_at.isoformat(),
                    "entity_id": str(p.id),
                    "entity_type": "project"
                })

        user_scans = await ScanReport.find(ScanReport.user_id == user_id).to_list()
        for s in user_scans:
            if s.created_at:
                scan_status = s.status.value if hasattr(s.status, 'value') else str(s.status)
                activities.append({
                    "type": f"scan_{scan_status}",
                    "icon": "shield",
                    "title": f"Ran scan: {s.project_name}",
                    "description": f"{s.total_findings or 0} findings found",
                    "timestamp": s.created_at.isoformat(),
                    "entity_id": str(s.id),
                    "entity_type": "scan"
                })

        if user.last_login:
            activities.append({
                "type": "login",
                "icon": "login",
                "title": "Last login",
                "description": f"From {user.organization or 'Unknown organization'}",
                "timestamp": user.last_login.isoformat(),
                "entity_id": str(user.id),
                "entity_type": "user"
            })

        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "activities": activities[:limit],
            "total": len(activities)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e, "Failed to fetch user activity")
        )
