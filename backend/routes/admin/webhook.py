"""
Admin webhook configuration endpoints.

Allows administrators to view the webhook integration status and rotate
the shared webhook secret. The secret is persisted to backend/.env so it
survives restarts and deploys.
"""
import logging
import secrets
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from config import settings
from models.user import User
from routes.dependencies import require_admin
from utils.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
SECRET_LINE_PREFIX = "WEBHOOK_SECRET="


def _load_env_lines() -> List[str]:
    if not ENV_PATH.exists():
        return []
    return ENV_PATH.read_text(encoding="utf-8").splitlines()


def _save_env_lines(lines: List[str]) -> None:
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _webhook_url(request: Request) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/webhook/"


@router.get("/webhook/status")
@limiter.limit("30/minute")
async def get_webhook_status(
    request: Request,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Show webhook integration status. Never returns the full secret."""
    secret = settings.webhook_secret or ""
    return {
        "configured": bool(secret),
        "secret_prefix": secret[:8] if secret else None,
        "url": _webhook_url(request),
        "events": ["push", "pull_request"],
        "auth": ["x-onyx-webhook-secret", "x-hub-signature-256"],
    }


@router.post("/webhook/rotate")
@limiter.limit("5/hour")
async def rotate_webhook_secret(
    request: Request,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Generate a new webhook secret and persist it to .env.

    The new secret takes effect after the backend service restarts, so all
    gunicorn workers pick it up consistently.
    """
    new_secret = secrets.token_hex(32)

    lines = _load_env_lines()
    kept = [line for line in lines if not line.startswith(SECRET_LINE_PREFIX)]
    kept.append(f"{SECRET_LINE_PREFIX}{new_secret}")

    try:
        _save_env_lines(kept)
    except OSError as e:
        logger.error(f"Failed to persist webhook secret to {ENV_PATH}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not write the new secret to backend/.env (permission problem). "
                   "Rotate it manually or fix .env write access.",
        )

    logger.warning(f"Webhook secret rotated by {current_user.email}")

    return {
        "secret": new_secret,
        "url": _webhook_url(request),
        "restart_required": True,
        "message": "Webhook secret rotated. Restart the backend service to apply it, "
                   "then update your GitHub webhook with the new secret.",
    }
