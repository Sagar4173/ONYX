import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from models.user import TwoFactorSetupResponse, TwoFactorVerifyRequest, User
from services.auth.auth_service import auth_service
from services.notifications.service import email_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/me/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    current_user: User = Depends(auth_service.get_current_user)
):
    import secrets

    import pyotp

    secret = pyotp.random_base32()

    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]

    current_user.two_factor_secret = secret
    current_user.two_factor_backup_codes = backup_codes
    await current_user.save()

    totp = pyotp.TOTP(secret)
    qr_code_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="ONYX"
    )

    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_url=qr_code_url,
        backup_codes=backup_codes
    )


@router.post("/me/2fa/enable")
async def enable_two_factor(
    verify_data: TwoFactorVerifyRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    import pyotp

    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call /me/2fa/setup first."
        )

    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(verify_data.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    current_user.two_factor_enabled = True
    current_user.updated_at = utc_now()
    await current_user.save()

    asyncio.create_task(email_service.send_2fa_enabled_email(
        email=current_user.email,
        user_name=current_user.full_name or current_user.username,
        enabled_at=utc_now().strftime("%B %d, %Y at %I:%M %p UTC")
    ))

    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/me/2fa/disable")
async def disable_two_factor(
    verify_data: TwoFactorVerifyRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    import pyotp

    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )

    totp = pyotp.TOTP(current_user.two_factor_secret)
    is_valid = totp.verify(verify_data.code, valid_window=1)

    if not is_valid and verify_data.code.upper() in current_user.two_factor_backup_codes:
        is_valid = True
        current_user.two_factor_backup_codes.remove(verify_data.code.upper())

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_backup_codes = []
    current_user.updated_at = utc_now()
    await current_user.save()

    asyncio.create_task(email_service.send_2fa_disabled_email(
        email=current_user.email,
        user_name=current_user.full_name or current_user.username,
        disabled_at=utc_now().strftime("%B %d, %Y at %I:%M %p UTC")
    ))

    return {"message": "Two-factor authentication disabled successfully"}


@router.get("/me/2fa/status")
async def get_two_factor_status(
    current_user: User = Depends(auth_service.get_current_user)
):
    return {
        "enabled": current_user.two_factor_enabled,
        "backup_codes_remaining": len(current_user.two_factor_backup_codes) if current_user.two_factor_enabled else 0
    }
