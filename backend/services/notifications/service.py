"""
Email Service for ONYX Security Intelligence Platform
Handles email sending via SMTP with deliverability best practices:
- Proper email headers (Message-ID, Date, List-Unsubscribe)
- Multipart alternative (HTML + plain text)
- DKIM/SPF aligned From address
- Secure TLS connections
"""
import asyncio
import logging
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, formataddr, make_msgid
from typing import List, Optional, Dict, Any
import ssl
import re
import aiosmtplib
from datetime import datetime

from config import settings
from .templates import get_jinja_environment
from .templates.base_template import SEVERITY_COLORS

logger = logging.getLogger(__name__)


class EmailService:
    """Production-ready email service using SMTP with anti-spam best practices"""
    
    def __init__(self):
        """Initialize email service with configured templates"""
        self.jinja_env = get_jinja_environment()
        self._configure_provider()
    
    def _configure_provider(self):
        """Configure email settings based on provider or custom settings"""
        if not settings.email_enabled:
            logger.info("Email service disabled")
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
            # Strip HTML for plain text version if not provided
            if not text_body:
                text_body = re.sub(r'<[^>]+>', '', html_body)
                text_body = re.sub(r'\s+', ' ', text_body).strip()
                if not text_body:
                    text_body = subject
            
            # Build message with proper headers for deliverability
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = formataddr((self.email_from_name, self.email_from))
            message['To'] = to_email
            message['Message-ID'] = make_msgid(domain=self.email_from.split('@')[-1] if '@' in self.email_from else 'onyx.local')
            message['Date'] = formatdate(localtime=True)
            message['Precedence'] = 'bulk'
            message['X-Mailer'] = 'ONYX Platform'
            message['Auto-Submitted'] = 'auto-generated'
            
            # List-Unsubscribe helps with Gmail spam classification
            unsubscribe_url = f"{settings.frontend_url}/profile?tab=notifications"
            message['List-Unsubscribe'] = f'<{unsubscribe_url}>'
            message['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # Add text and HTML parts
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
    
    async def _send_smtp_email(self, message: MIMEMultipart, to_email: str):
        """Send email via SMTP with secure TLS connection"""
        try:
            context = ssl.create_default_context()
            
            if self.smtp_use_ssl:
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    use_tls=True,
                    tls_context=context
                )
            else:
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    use_tls=False,
                    start_tls=self.smtp_use_tls,
                    tls_context=context
                )
            
            await smtp_client.connect()
            
            # Say HELO/EHLO explicitly for better deliverability
            await smtp_client.ehlo()
            
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
        report_id: str = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        detailed_findings: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send scan completion notification email with optional report attachment"""
        try:
            report_url = f"{settings.frontend_url}/report/{report_id}" if report_id else f"{settings.frontend_url}/dashboard"
            total_findings = critical_count + high_count + medium_count + low_count
            
            # Calculate risk score (0-100, higher = more secure)
            risk_score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 5 + low_count * 1))
            
            # Determine score styling based on risk level
            if risk_score >= 80:
                score_bg_start = "rgba(34, 197, 94, 0.15)"
                score_bg_end = "rgba(16, 185, 129, 0.15)"
                score_border = "rgba(34, 197, 94, 0.3)"
                score_color = "#4ade80"
                score_label_color = "#86efac"
            elif risk_score >= 60:
                score_bg_start = "rgba(234, 179, 8, 0.15)"
                score_bg_end = "rgba(245, 158, 11, 0.15)"
                score_border = "rgba(234, 179, 8, 0.3)"
                score_color = "#fbbf24"
                score_label_color = "#fcd34d"
            else:
                score_bg_start = "rgba(239, 68, 68, 0.15)"
                score_bg_end = "rgba(220, 38, 38, 0.15)"
                score_border = "rgba(239, 68, 68, 0.3)"
                score_color = "#f87171"
                score_label_color = "#fca5a5"
            
            # Generate top findings HTML from detailed_findings
            top_findings_html = ""
            if detailed_findings:
                sev_colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22c55e", "info": "#3b82f6"}
                # Show top 5 critical/high findings
                priority_findings = sorted(
                    detailed_findings,
                    key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(
                        f.get("severity", "info").lower(), 5
                    )
                )[:5]
                
                for f in priority_findings:
                    sev = f.get("severity", "medium").lower()
                    sc = sev_colors.get(sev, "#94a3b8")
                    title = f.get("title", "Unknown Finding")[:80]
                    desc = f.get("description", "")[:150]
                    file_path = f.get("file_path", "")
                    
                    top_findings_html += f'''
                    <div style="padding: 14px 16px; margin-bottom: 10px; background: rgba(255,255,255,0.03); border-radius: 12px; border-left: 4px solid {sc};">
                        <div style="margin-bottom: 6px;">
                            <span style="color: #e2e8f0; font-size: 14px; font-weight: 600;">{title}</span>
                            <span style="background: {sc}; color: white; padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: 600; margin-left: 8px; display: inline-block;">{sev.upper()}</span>
                        </div>
                        {"<p style='color: #94a3b8; font-size: 12px; margin: 0 0 4px 0; line-height: 1.4;'>" + desc + "</p>" if desc else ""}
                        {"<p style='color: #64748b; font-size: 11px; margin: 0; font-family: monospace;'>" + file_path + "</p>" if file_path else ""}
                    </div>'''
            
            # Use the premium scan report email template
            template = self.jinja_env.get_template('scan_report_email')
            html_body = template.render(
                project_name=project_name,
                scan_type=scan_type,
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count,
                total_findings=total_findings,
                duration=duration,
                risk_score=risk_score,
                score_bg_start=score_bg_start,
                score_bg_end=score_bg_end,
                score_border=score_border,
                score_color=score_color,
                score_label_color=score_label_color,
                completed_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                report_url=report_url,
                top_findings_html=top_findings_html,
                has_critical=critical_count > 0,
                has_attachment=attachments is not None and len(attachments) > 0
            )
            
            # Determine urgency based on findings
            if critical_count > 0:
                subject = f"🚨 CRITICAL: Scan Complete - {critical_count} critical issues in {project_name}"
            elif high_count > 0:
                subject = f"⚠️ Scan Complete - {high_count} high severity issues in {project_name}"
            elif total_findings > 0:
                subject = f"✅ Scan Complete - {total_findings} findings in {project_name}"
            else:
                subject = f"🎉 Scan Complete - No issues found in {project_name}"
            
            return await self.send_email(
                to_email=email,
                subject=subject,
                html_body=html_body,
                attachments=attachments
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
