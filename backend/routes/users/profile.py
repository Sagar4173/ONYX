
from fastapi import APIRouter, Depends, Query

from models.user import APITokenCreate, APITokenResponse, User, UserPasswordChange, UserResponse, UserUpdate
from services.auth.auth_service import auth_service
from services.auth.user_service import user_service

router = APIRouter(tags=["User Management - Profile"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(auth_service.get_current_user)
):
    return await user_service._user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    return await user_service.update_user_profile(
        current_user.id,
        update_data,
        current_user.id
    )


@router.post("/me/change-password")
async def change_current_user_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(auth_service.get_current_user)
):
    await user_service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}


@router.get("/me/sessions")
async def get_current_user_sessions(
    current_user: User = Depends(auth_service.get_current_user)
):
    sessions = await user_service.get_user_sessions(current_user.id)
    return {"sessions": sessions}


@router.delete("/me/sessions/{session_id}")
async def revoke_current_user_session(
    session_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    await user_service.revoke_user_session(
        current_user.id,
        session_id,
        current_user.id
    )
    return {"message": "Session revoked successfully"}


@router.get("/me/api-tokens")
async def get_current_user_api_tokens(
    current_user: User = Depends(auth_service.get_current_user)
):
    tokens = await user_service.get_user_api_tokens(current_user.id)
    return {"tokens": tokens}


@router.post("/me/api-tokens", response_model=APITokenResponse)
async def create_current_user_api_token(
    token_data: APITokenCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    return await user_service.create_api_token(
        current_user.id,
        token_data,
        current_user.id
    )


@router.delete("/me/api-tokens/{token_id}")
async def revoke_current_user_api_token(
    token_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    await user_service.revoke_api_token(
        current_user.id,
        token_id,
        current_user.id
    )
    return {"message": "API token revoked successfully"}


@router.get("/me/activity")
async def get_current_user_activity(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_user)
):
    activities = await user_service.get_user_activity_log(current_user.id, limit)
    return {"activities": activities}
