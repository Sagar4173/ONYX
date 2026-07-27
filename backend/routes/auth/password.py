import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from models.user import PasswordResetConfirm, PasswordResetRequest, User, UserPasswordChange
from services.auth.auth_service import auth_service
from services.notifications.service import email_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(auth_service.get_current_user)
):
    success = await auth_service.change_password(current_user.id, password_data)
    if success:
        asyncio.create_task(email_service.send_password_changed_email(
            email=current_user.email,
            user_name=current_user.full_name or current_user.username,
            changed_at=utc_now().strftime("%B %d, %Y at %I:%M %p UTC")
        ))
        return {"message": "Password changed successfully. Please log in again."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/request-password-reset")
async def request_password_reset(reset_request: PasswordResetRequest) -> Dict[str, Any]:
    await auth_service.request_password_reset(reset_request.email)
    return {
        "message": "If the email address is registered, you will receive password reset instructions."
    }


@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm) -> Dict[str, Any]:
    success = await auth_service.reset_password(reset_data)
    if success:
        return {"message": "Password reset successfully. Please log in with your new password."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
