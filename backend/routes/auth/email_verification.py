import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from models.user import EmailVerificationRequest, User, UserRole, UserStatus
from services.auth.auth_service import auth_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


class ResendVerificationRequest(BaseModel):
    email: str


@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest) -> Dict[str, Any]:
    from datetime import timezone

    user = await User.find_one({
        "email_verification_token": request.token
    })

    if user:
        if user.email_verification_expires:
            expires = user.email_verification_expires
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if utc_now() > expires:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification link has expired. Please request a new verification email."
                )

        if user.status == UserStatus.PENDING_VERIFICATION and not user.is_email_verified:
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            user.status = UserStatus.ACTIVE
            user.updated_at = utc_now()
            await user.save()
            return {"message": "Email verified successfully. Your account is now active."}

        elif user.is_email_verified:
            user.email_verification_token = None
            user.email_verification_expires = None
            await user.save()
            return {"message": "Email is already verified. Your account is active."}

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account verification failed. Please contact support."
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification link. Please request a new verification email."
    )


@router.post("/resend-verification")
async def resend_verification_email(
    request_data: Optional[ResendVerificationRequest] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(auth_service.optional_security)
):

    user = None

    if credentials and credentials.credentials:
        try:
            user = await auth_service.get_current_user_for_verification(credentials)
        except HTTPException:
            pass

    if not user and request_data and request_data.email:
        user = await User.find_one({"email": request_data.email.lower()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address. Please check the email or create a new account."
            )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for unauthenticated requests"
        )

    if user.is_email_verified:
        return {"message": "Email is already verified"}

    user.email_verification_token = secrets.token_urlsafe(32)
    user.email_verification_expires = utc_now() + timedelta(hours=2)
    await user.save()

    await auth_service.send_verification_email(
        user.email,
        user.email_verification_token
    )

    return {"message": "Verification email sent successfully"}


@router.post("/test-email")
async def test_email_configuration(
    current_user: User = Depends(auth_service.get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test email configuration"
        )

    try:
        from services.notifications.service import email_service

        connection_ok = await email_service.test_connection()
        if not connection_ok:
            return {
                "message": "Email connection test failed",
                "success": False,
                "error": "Could not connect to SMTP server"
            }

        timestamp = utc_now().isoformat()
        success = await email_service.send_email(
            to_email=current_user.email,
            subject="Test Email - ONYX Platform",
            html_body=f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4F46E5;">Email Configuration Test</h2>
                <p>Congratulations! Your email configuration is working correctly.</p>
                <p>This test email was sent from the ONYX Platform.</p>
                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    Test performed at: {timestamp}
                </p>
            </body>
            </html>
            """
        )

        if success:
            return {
                "message": f"Test email sent successfully to {current_user.email}",
                "success": True
            }
        else:
            return {
                "message": "Failed to send test email",
                "success": False
            }

    except Exception as e:
        return {
            "message": f"Email test failed: {str(e)}",
            "success": False,
            "error": str(e)
        }
