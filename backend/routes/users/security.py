from fastapi import APIRouter, Depends, Query

from models.user import (
    User,
    UserRole,
)
from services.auth.auth_service import auth_service
from services.auth.user_service import user_service
from utils.datetime_utils import utc_now

router = APIRouter(tags=["User Management - Security"])


@router.get("/security/overview")
async def get_security_overview(
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
    stats = await user_service.get_user_statistics()

    now = utc_now()

    users_with_failed_logins = await User.find(
        User.failed_login_attempts > 0
    ).count()

    locked_accounts = await User.find(
        User.locked_until > now
    ).count()

    unverified_emails = await User.find(
        not User.is_email_verified
    ).count()

    return {
        **stats,
        "security_metrics": {
            "users_with_failed_logins": users_with_failed_logins,
            "locked_accounts": locked_accounts,
            "unverified_emails": unverified_emails
        }
    }


@router.get("/security/suspicious-activity")
async def get_suspicious_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(auth_service.require_role([UserRole.ADMIN, UserRole.SECURITY_MANAGER]))
):
    suspicious_users = await User.find(
        User.failed_login_attempts >= 3
    ).sort([("failed_login_attempts", -1)]).limit(limit).to_list()

    activities = []
    for user in suspicious_users:
        activities.append({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "failed_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until,
            "last_login": user.last_login,
            "status": user.status
        })

    return {"suspicious_activities": activities}
