"""
Google SSO (OAuth 2.0 via Google Identity Services ID tokens)

Flow: the frontend obtains an ID token from Google Identity Services and
POSTs it here. The backend verifies signature + audience against
GOOGLE_CLIENT_ID and logs the user in (or auto-provisions an account).

Configuration:
    GOOGLE_CLIENT_ID=<oauth client id>
    GOOGLE_ALLOWED_DOMAINS=example.com,corp.example.org   # optional allowlist
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from config import settings
from utils.rate_limit import limiter
from services.auth.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()


class GoogleSSOLoginRequest(BaseModel):
    id_token: str
    two_factor_code: Optional[str] = None  # Required if user has 2FA enabled
    nonce: Optional[str] = None  # Binds the ID token to the login page session


class GoogleSSOConfigResponse(BaseModel):
    enabled: bool
    client_id: Optional[str] = None


@router.get("/sso/google/config", response_model=GoogleSSOConfigResponse)
async def get_google_sso_config() -> GoogleSSOConfigResponse:
    """Public config so the frontend only renders the SSO button when enabled"""
    return GoogleSSOConfigResponse(
        enabled=settings.google_sso_enabled,
        client_id=settings.google_client_id if settings.google_sso_enabled else None,
    )


@router.post("/sso/google")
@limiter.limit("30/minute")
async def google_sso_login(
    login_data: GoogleSSOLoginRequest,
    request: Request,
) -> Any:
    if not settings.google_sso_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google SSO is not configured"
        )

    try:
        response = await auth_service.google_login(
            login_data.id_token,
            login_data.two_factor_code,
            request,
            nonce=login_data.nonce,
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google SSO login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google SSO login failed due to an internal error"
        )
