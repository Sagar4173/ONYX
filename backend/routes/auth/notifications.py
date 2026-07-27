import logging

from fastapi import APIRouter, Depends

from models.user import NotificationPreferencesUpdate, User
from services.auth.auth_service import auth_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me/notifications")
async def get_notification_preferences(
    current_user: User = Depends(auth_service.get_current_user)
):
    return current_user.notification_preferences


@router.put("/me/notifications")
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    update_data = preferences.dict(exclude_unset=True)

    for key, value in update_data.items():
        current_user.notification_preferences[key] = value

    current_user.updated_at = utc_now()
    await current_user.save()

    return {
        "message": "Notification preferences updated",
        "preferences": current_user.notification_preferences
    }
