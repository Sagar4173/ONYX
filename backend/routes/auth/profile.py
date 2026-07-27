import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from models.user import User, UserResponse, UserUpdate
from services.auth.auth_service import auth_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


class AvatarUpdate(BaseModel):
    avatar_url: Optional[str] = ""


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(auth_service.get_current_user)
):
    return UserResponse(**current_user.dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    update_data = user_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = utc_now()
    current_user.last_updated_by = current_user.id

    await current_user.save()

    return UserResponse(**current_user.dict())


@router.post("/me/avatar")
async def upload_avatar(
    avatar_data: AvatarUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    avatar_url = (avatar_data.avatar_url or "").strip()

    if not avatar_url:
        current_user.avatar_url = None
        current_user.updated_at = utc_now()
        await current_user.save()
        return {
            "message": "Avatar removed successfully",
            "avatar_url": None
        }

    if not avatar_url.startswith(("http://", "https://", "data:image/")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid avatar format. Provide a URL or base64 data URI."
        )

    if avatar_url.startswith("data:image/") and len(avatar_url) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar image too large. Maximum size is 5MB."
        )

    current_user.avatar_url = avatar_url
    current_user.updated_at = utc_now()
    await current_user.save()

    return {
        "message": "Avatar updated successfully",
        "avatar_url": avatar_url
    }
