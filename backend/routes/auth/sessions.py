import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from utils.rate_limit import limiter
from models.user import LoginRequest, RefreshTokenRequest, TokenResponse, User, UserSession
from services.auth.auth_service import auth_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
@limiter.limit("30/minute")
async def login(login_data: LoginRequest, request: Request) -> Any:
    try:
        response = await auth_service.login(login_data, request)

        if isinstance(response, dict) and response.get("requires_2fa"):
            return response

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request_data: RefreshTokenRequest) -> TokenResponse:
    try:
        response = await auth_service.refresh_access_token(request_data.refresh_token)
        return response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
):
    success = await auth_service.logout(credentials.credentials)
    if success:
        return {"message": "Successfully logged out"}
    else:
        return {"message": "Session not found or already logged out"}


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(auth_service.get_current_user)
):
    count = await auth_service.logout_all_sessions(current_user.id)
    return {"message": f"Logged out from {count} sessions"}


@router.get("/me/sessions")
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(auth_service.get_current_user)
):
    from user_agents import parse as parse_ua

    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    sessions = await UserSession.find({
        "user_id": current_user.id,
        "is_active": True
    }).to_list()

    result = []
    for session in sessions:
        user_agent_str = session.user_agent or "Unknown"
        try:
            ua = parse_ua(user_agent_str)
            device = f"{ua.device.brand or ''} {ua.device.model or ua.device.family}".strip() or "Unknown Device"
            browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
        except Exception:
            device = "Unknown Device"
            browser = "Unknown Browser"

        location = "Unknown Location"
        if session.location:
            city = session.location.get("city", "")
            country = session.location.get("country", "")
            location = f"{city}, {country}".strip(", ") if city or country else "Unknown Location"

        result.append({
            "session_id": session.session_id,
            "device": device,
            "browser": browser,
            "location": location,
            "ip_address": session.ip_address or "Unknown",
            "is_current": session.access_token == current_token,
            "last_active": session.last_activity,
            "created_at": session.created_at
        })

    return result


@router.delete("/me/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(auth_service.get_current_user)
):
    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    session = await UserSession.find_one({
        "session_id": session_id,
        "user_id": current_user.id,
        "is_active": True
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.access_token == current_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke current session. Use logout instead."
        )

    session.is_active = False
    session.logged_out_at = utc_now()
    await session.save()

    return {"message": "Session revoked successfully"}


@router.delete("/me/sessions")
async def revoke_all_other_sessions(
    request: Request,
    current_user: User = Depends(auth_service.get_current_user)
):
    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    result = await UserSession.find({
        "user_id": current_user.id,
        "is_active": True,
        "access_token": {"$ne": current_token}
    }).update_many({
        "$set": {
            "is_active": False,
            "logged_out_at": utc_now()
        }
    })

    return {"message": f"Revoked {result.modified_count} other sessions"}
