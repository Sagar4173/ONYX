import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from config import settings
from models.user import User, UserCreate, UserResponse, UserRole
from services.auth.auth_service import auth_service
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user)
):
    if not settings.allow_registration and not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Please contact an administrator."
        )

    if current_user:
        if current_user.role != UserRole.ADMIN and user_data.role != UserRole.VIEWER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create users with elevated roles"
            )
        created_by = current_user.id
    else:
        user_data.role = UserRole.VIEWER
        created_by = None

    try:
        user = await auth_service.create_user(user_data, created_by)

        if user.email_verification_token:
            await auth_service.send_verification_email(user.email, user.email_verification_token)

        if not current_user:
            await auth_service.send_welcome_email(user.email, user.username or user.email.split('@')[0])

        return UserResponse(**user.dict())

    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = error['loc'][-1] if error['loc'] else 'field'
            message = error['msg']
            errors.append({"field": field, "message": message})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors}
        )
    except Exception as e:
        error_msg = str(e)
        if "must be at least" in error_msg or "must be less than" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_detail(e)
        )
