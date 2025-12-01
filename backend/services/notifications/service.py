"""
Email Service for ONYX Security Intelligence Platform
Handles email sending with support for multiple providers:
- SMTP (Gmail, Outlook, Yahoo, SendGrid)
- Brevo API (HTTP-based, works on Render/cloud platforms, no domain verification needed)
Refactored for modularity and maintainability
"""
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import ssl
import aiosmtplib
import httpx
from datetime import datetime

from config import settings
from .templates import get_jinja_environment
from .templates.base_template import SEVERITY_COLORS

logger = logging.getLogger(__name__)


class EmailService:
    """Production-ready email service with SMTP and Brevo API support"""
    
    def __init__(self):
        """Initialize email service with configured templates"""
        self.jinja_env = get_jinja_environment()
        self.use_brevo = False
        self.brevo_api_key = None
        self._configure_provider()
    
    def _configure_provider(self):
        """Configure email settings based on provider or custom settings"""
        if not settings.email_enabled:
            logger.info("Email service disabled")
            return
        
        # Check if Brevo is configured (preferred for cloud platforms like Render)
        # Brevo: 300 emails/day free, no domain verification required
        if settings.brevo_api_key or (settings.email_provider and settings.email_provider.lower() == 'brevo'):
            self.use_brevo = True
            self.brevo_api_key = settings.brevo_api_key
            self.email_from = settings.email_from
            self.email_from_name = settings.email_from_name
            if not self.email_from:
                logger.error("EMAIL_FROM is required for Brevo")
            else:
                logger.info("✅ Configured email with Brevo API (HTTP-based, no domain verification)")
            return
            
        # Provider-specific SMTP configurations
        if settings.email_provider:
            provider_configs = {
                'gmail': {
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'smtp_use_tls': True,
                    'smtp_use_ssl': False
                },
                'outlook': {
                    'smtp_server': 'smtp-mail.outlook.com',
                    'smtp_port': 587,
                    'smtp_use_tls': True,
                    'smtp_use_ssl': False
                },
                'yahoo': {
                    'smtp_server': 'smtp.mail.yahoo.com',
                    'smtp_port': 587,
                    'smtp_use_tls': True,
                    'smtp_use_ssl': False
                },
                'sendgrid': {
                    'smtp_server': 'smtp.sendgrid.net',
                    'smtp_port': 587,
                    'smtp_use_tls': True,
                    'smtp_use_ssl': False
                }
            }
            
            provider = settings.email_provider.lower()
            if provider in provider_configs:
                config = provider_configs[provider]
                self.smtp_server = config['smtp_server']
                self.smtp_port = config['smtp_port']
                self.smtp_use_tls = config['smtp_use_tls']
                self.smtp_use_ssl = config['smtp_use_ssl']
                logger.info(f"Configured email for provider: {provider}")
            else:
                logger.warning(f"Unknown email provider: {provider}, using custom settings")
                self._use_custom_settings()
        else:
            self._use_custom_settings()
            
        # Credentials and sender info
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.email_from = settings.email_from or settings.smtp_username
        self.email_from_name = settings.email_from_name
        
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.email_from]):
            logger.error("Incomplete email configuration. Please check SMTP settings.")
    
    def _use_custom_settings(self):
        """Use custom SMTP settings from environment"""
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_use_tls = settings.smtp_use_tls
        self.smtp_use_ssl = settings.smtp_use_ssl
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send email using Resend API or SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML body content
            text_body: Optional plain text body
            attachments: Optional list of attachments
            
        Returns:
            bool: True if email sent successfully
        """
        if not settings.email_enabled:
            logger.info(f"📧 Email service disabled. Would send to: {to_email}")
            logger.info(f"📧 Subject: {subject}")
            return True
        
        try:
            # Use Brevo API if configured (works on Render/cloud platforms)
            if self.use_brevo:
                return await self._send_brevo_email(to_email, subject, html_body, text_body)
            
            # Otherwise use SMTP
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.email_from_name} <{self.email_from}>"
            message['To'] = to_email
            
            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                message.attach(text_part)
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Send email via SMTP
            await self._send_smtp_email(message, to_email)
            
            logger.info(f"✅ Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def _send_brevo_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send email via Brevo API (HTTP-based, works on cloud platforms, no domain verification)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={
                        "api-key": self.brevo_api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "sender": {
                            "name": self.email_from_name,
                            "email": self.email_from
                        },
                        "to": [{"email": to_email}],
                        "subject": subject,
                        "htmlContent": html_body,
                        "textContent": text_body or ""
                    },
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Email sent via Brevo to: {to_email}")
                    return True
                else:
                    logger.error(f"❌ Brevo API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Brevo email error: {str(e)}")
            return False
    
    async def _send_smtp_email(self, message: MIMEMultipart, to_email: str):
        """Send email via SMTP"""
        try:
            # Use SSL context for security
            context = ssl.create_default_context()
            
            # Configure SMTP client based on settings
            if self.smtp_use_ssl:
                # Direct SSL connection (port 465)
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    use_tls=True,
                    tls_context=context
                )
            else:
                # Regular connection with STARTTLS (port 587)
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    use_tls=False,
                    start_tls=self.smtp_use_tls,
                    tls_context=context
                )
            
            await smtp_client.connect()
            
            if self.smtp_username and self.smtp_password:
                await smtp_client.login(self.smtp_username, self.smtp_password)
            
            await smtp_client.send_message(message)
            await smtp_client.quit()
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            filename = attachment.get('filename', 'attachment')
            content = attachment.get('content', b'')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            message.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename')}: {str(e)}")
    
    async def send_verification_email(self, email: str, verification_token: str) -> bool:
        """Send email verification email"""
        try:
            verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
            
            template = self.jinja_env.get_template('verification')
            html_body = template.render(
                verification_url=verification_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔐 Verify Your Email - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False
    
    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email"""
        try:
            reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
            
            template = self.jinja_env.get_template('password_reset')
            html_body = template.render(
                reset_url=reset_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔑 Password Reset - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False
    
    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        try:
            dashboard_url = f"{settings.frontend_url}/"
            
            template = self.jinja_env.get_template('welcome')
            html_body = template.render(
                user_name=user_name,
                dashboard_url=dashboard_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🎉 Welcome to ONYX Platform - Let's Get Started!",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    async def send_scan_completed_email(
        self, 
        email: str, 
        project_name: str,
        scan_type: str,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        duration: str = "N/A",
        files_scanned: int = 0,
        report_id: str = None
    ) -> bool:
        """Send scan completion notification email"""
        try:
            report_url = f"{settings.frontend_url}/reports/{report_id}" if report_id else f"{settings.frontend_url}/dashboard"
            
            template = self.jinja_env.get_template('scan_completed')
            html_body = template.render(
                project_name=project_name,
                scan_type=scan_type,
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count,
                duration=duration,
                files_scanned=files_scanned,
                completed_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                report_url=report_url
            )
            
            # Determine urgency based on findings
            if critical_count > 0:
                subject = f"🚨 CRITICAL: Scan Complete - {critical_count} critical issues in {project_name}"
            elif high_count > 0:
                subject = f"⚠️ Scan Complete - {high_count} high severity issues in {project_name}"
            else:
                subject = f"✅ Scan Complete - {project_name}"
            
            return await self.send_email(
                to_email=email,
                subject=subject,
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send scan completed email: {str(e)}")
            return False
    
    async def send_security_alert_email(
        self,
        email: str,
        alert_title: str,
        alert_description: str,
        severity: str,
        project_name: str,
        file_path: str = "N/A",
        vulnerability_type: str = "Unknown",
        cwe_id: str = "N/A",
        cvss_score: str = "N/A",
        recommendation: str = "Review the finding and apply appropriate fixes.",
        alert_id: str = None
    ) -> bool:
        """Send security alert notification email"""
        try:
            alert_url = f"{settings.frontend_url}/alerts/{alert_id}" if alert_id else f"{settings.frontend_url}/dashboard"
            severity_color = SEVERITY_COLORS.get(severity.lower(), "#6b7280")
            
            template = self.jinja_env.get_template('security_alert')
            html_body = template.render(
                alert_title=alert_title,
                alert_description=alert_description,
                severity=severity.upper(),
                severity_color=severity_color,
                project_name=project_name,
                file_path=file_path,
                detected_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                vulnerability_type=vulnerability_type,
                cwe_id=cwe_id,
                cvss_score=cvss_score,
                recommendation=recommendation,
                alert_url=alert_url
            )
            
            return await self.send_email(
                to_email=email,
                subject=f"🚨 Security Alert: {severity.upper()} - {alert_title}",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send security alert email: {str(e)}")
            return False
    
    async def send_new_vulnerability_email(
        self,
        email: str,
        vulnerability_title: str,
        severity: str,
        project_name: str,
        file_path: str,
        line_number: int = 0,
        description: str = "",
        fix_suggestion: str = "",
        vulnerability_id: str = None
    ) -> bool:
        """Send new vulnerability notification email"""
        try:
            vulnerability_url = f"{settings.frontend_url}/vulnerabilities/{vulnerability_id}" if vulnerability_id else f"{settings.frontend_url}/dashboard"
            severity_color = SEVERITY_COLORS.get(severity.lower(), "#6b7280")
            
            template = self.jinja_env.get_template('new_vulnerability')
            html_body = template.render(
                vulnerability_title=vulnerability_title,
                severity=severity,
                severity_color=severity_color,
                project_name=project_name,
                file_path=file_path,
                line_number=line_number,
                description=description,
                fix_suggestion=fix_suggestion,
                vulnerability_url=vulnerability_url
            )
            
            return await self.send_email(
                to_email=email,
                subject=f"🔓 New {severity.upper()} Vulnerability: {vulnerability_title}",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send new vulnerability email: {str(e)}")
            return False
    
    async def send_login_alert_email(
        self,
        email: str,
        login_time: str,
        location: str = "Unknown",
        device: str = "Unknown",
        browser: str = "Unknown",
        ip_address: str = "Unknown"
    ) -> bool:
        """Send new login alert email"""
        try:
            secure_account_url = f"{settings.frontend_url}/profile?tab=security"
            review_sessions_url = f"{settings.frontend_url}/profile?tab=sessions"
            
            template = self.jinja_env.get_template('login_alert')
            html_body = template.render(
                login_time=login_time,
                location=location,
                device=device,
                browser=browser,
                ip_address=ip_address,
                secure_account_url=secure_account_url,
                review_sessions_url=review_sessions_url
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔐 New Login to Your Account - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send login alert email: {str(e)}")
            return False
    
    async def send_weekly_digest_email(
        self,
        email: str,
        week_start: str,
        week_end: str,
        total_scans: int,
        total_vulnerabilities: int,
        resolved_count: int,
        critical_count: int,
        high_count: int,
        medium_count: int,
        low_count: int,
        top_issues: List[Dict[str, Any]] = None
    ) -> bool:
        """Send weekly security digest email"""
        try:
            dashboard_url = f"{settings.frontend_url}/dashboard"
            
            # Calculate percentages
            total = critical_count + high_count + medium_count + low_count
            if total > 0:
                critical_percent = (critical_count / total) * 100
                high_percent = (high_count / total) * 100
                medium_percent = (medium_count / total) * 100
                low_percent = (low_count / total) * 100
            else:
                critical_percent = high_percent = medium_percent = low_percent = 0
            
            # Generate top issues HTML
            top_issues_html = ""
            if top_issues:
                for issue in top_issues[:5]:
                    color = SEVERITY_COLORS.get(issue.get('severity', '').lower(), '#94a3b8')
                    top_issues_html += f'''
                    <div style="padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #e2e8f0; font-size: 14px;">{issue.get('title', 'Unknown Issue')}</span>
                        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{issue.get('severity', 'Unknown').upper()}</span>
                    </div>
                    '''
            else:
                top_issues_html = '<p style="color: #4ade80; font-size: 14px;">🎉 No critical issues this week!</p>'
            
            template = self.jinja_env.get_template('weekly_digest')
            html_body = template.render(
                week_start=week_start,
                week_end=week_end,
                total_scans=total_scans,
                total_vulnerabilities=total_vulnerabilities,
                resolved_count=resolved_count,
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count,
                critical_percent=critical_percent,
                high_percent=high_percent,
                medium_percent=medium_percent,
                low_percent=low_percent,
                top_issues_html=top_issues_html,
                dashboard_url=dashboard_url
            )
            
            return await self.send_email(
                to_email=email,
                subject=f"📊 Weekly Security Digest - {week_start} to {week_end}",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send weekly digest email: {str(e)}")
            return False

    async def send_2fa_enabled_email(self, email: str, user_name: str, enabled_at: str, device_info: str = None) -> bool:
        """Send email when 2FA is enabled"""
        try:
            security_url = f"{settings.frontend_url}/profile"
            
            template = self.jinja_env.get_template('2fa_enabled')
            html_body = template.render(
                user_name=user_name,
                enabled_at=enabled_at,
                device_info=device_info or "Unknown Device",
                security_settings_url=security_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="✅ Two-Factor Authentication Enabled - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send 2FA enabled email: {str(e)}")
            return False

    async def send_2fa_disabled_email(self, email: str, user_name: str, disabled_at: str, ip_address: str = None) -> bool:
        """Send warning email when 2FA is disabled"""
        try:
            security_url = f"{settings.frontend_url}/profile"
            enable_2fa_url = f"{settings.frontend_url}/profile?tab=security"
            
            template = self.jinja_env.get_template('2fa_disabled')
            html_body = template.render(
                user_name=user_name,
                disabled_at=disabled_at,
                ip_address=ip_address or "Unknown",
                enable_2fa_url=enable_2fa_url,
                secure_account_url=security_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="⚠️ Two-Factor Authentication Disabled - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send 2FA disabled email: {str(e)}")
            return False

    async def send_2fa_recovery_used_email(self, email: str, user_name: str, used_at: str, ip_address: str = None, remaining_codes: int = 0) -> bool:
        """Send alert when a 2FA recovery code is used"""
        try:
            security_url = f"{settings.frontend_url}/profile?tab=security"
            
            template = self.jinja_env.get_template('2fa_recovery_used')
            html_body = template.render(
                user_name=user_name,
                used_at=used_at,
                ip_address=ip_address or "Unknown",
                remaining_codes=remaining_codes,
                security_url=security_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔑 Recovery Code Used - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send 2FA recovery used email: {str(e)}")
            return False

    async def send_password_changed_email(self, email: str, user_name: str, changed_at: str, ip_address: str = None, device: str = None) -> bool:
        """Send notification when password is changed"""
        try:
            security_url = f"{settings.frontend_url}/profile?tab=security"
            
            template = self.jinja_env.get_template('password_changed')
            html_body = template.render(
                user_name=user_name,
                changed_at=changed_at,
                ip_address=ip_address or "Unknown",
                device=device or "Unknown",
                secure_account_url=security_url,
                platform_name="ONYX Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔐 Password Changed - ONYX Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send password changed email: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test SMTP connection"""
        if not settings.email_enabled:
            logger.info("Email service disabled, skipping connection test")
            return False
            
        try:
            context = ssl.create_default_context()
            
            # Configure SMTP client based on settings
            if self.smtp_use_ssl:
                # Direct SSL connection (port 465)
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    use_tls=True,
                    tls_context=context
                )
            else:
                # Regular connection with STARTTLS (port 587)
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    use_tls=False,
                    start_tls=self.smtp_use_tls,
                    tls_context=context
                )
            
            await smtp_client.connect()
            
            if self.smtp_username and self.smtp_password:
                await smtp_client.login(self.smtp_username, self.smtp_password)
            
            await smtp_client.quit()
            logger.info("✅ SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
