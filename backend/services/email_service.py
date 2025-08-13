"""
Email Service for SecureDevOps AI Platform
Handles SMTP email sending with support for multiple providers
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
from jinja2 import Environment, BaseLoader, TemplateNotFound

from config import settings

logger = logging.getLogger(__name__)


class EmailTemplateLoader(BaseLoader):
    """Custom Jinja2 template loader for email templates"""
    
    def __init__(self):
        self.templates = {
            'verification': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Arial', sans-serif; background-color: #f3f4f6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: bold;">
                🔒 SecureDevOps Platform
            </h1>
            <p style="color: #E0E7FF; margin: 10px 0 0 0; font-size: 16px;">
                Advanced Security Scanning & Analysis
            </p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 20px;">
            <h2 style="color: #374151; font-size: 24px; margin: 0 0 20px 0;">
                Welcome! Please verify your email address
            </h2>
            
            <p style="color: #6B7280; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                Thank you for registering with SecureDevOps Platform. To complete your registration and activate your account, please click the button below:
            </p>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ verification_url }}" 
                   style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); 
                          color: #ffffff; 
                          padding: 16px 32px; 
                          text-decoration: none; 
                          border-radius: 12px; 
                          display: inline-block;
                          font-weight: bold;
                          font-size: 16px;
                          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);">
                    ✉️ Verify Email Address
                </a>
            </div>
            
            <!-- Features -->
            <div style="margin: 30px 0; padding: 20px; background: #F9FAFB; border-radius: 12px; border-left: 4px solid #4F46E5;">
                <h3 style="color: #374151; margin: 0 0 15px 0; font-size: 18px;">🚀 What you can do with SecureDevOps:</h3>
                <ul style="color: #6B7280; margin: 0; padding-left: 20px;">
                    <li style="margin-bottom: 8px;">🔍 Advanced security scanning (SAST, secrets, containers)</li>
                    <li style="margin-bottom: 8px;">🤖 AI-powered vulnerability analysis</li>
                    <li style="margin-bottom: 8px;">📊 Comprehensive compliance reporting</li>
                    <li style="margin-bottom: 8px;">⚡ Real-time security alerts and notifications</li>
                </ul>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background: #F9FAFB; padding: 30px 20px; text-align: center; border-top: 1px solid #E5E7EB;">
            <p style="color: #6B7280; font-size: 14px; margin: 0 0 10px 0;">
                This verification link will expire in 24 hours. If you didn't create an account with us, please ignore this email.
            </p>
            <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
                © 2025 SecureDevOps Platform. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
            ''',
            
            'password_reset': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Arial', sans-serif; background-color: #f3f4f6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: bold;">
                🔒 SecureDevOps Platform
            </h1>
            <p style="color: #FEE2E2; margin: 10px 0 0 0; font-size: 16px;">
                Password Reset Request
            </p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 20px;">
            <h2 style="color: #374151; font-size: 24px; margin: 0 0 20px 0;">
                Reset Your Password
            </h2>
            
            <p style="color: #6B7280; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                We received a request to reset your password. If you made this request, click the button below to reset your password:
            </p>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ reset_url }}" 
                   style="background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); 
                          color: #ffffff; 
                          padding: 16px 32px; 
                          text-decoration: none; 
                          border-radius: 12px; 
                          display: inline-block;
                          font-weight: bold;
                          font-size: 16px;
                          box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);">
                    🔑 Reset Password
                </a>
            </div>
            
            <!-- Security Notice -->
            <div style="margin: 30px 0; padding: 20px; background: #FEF2F2; border-radius: 12px; border-left: 4px solid #EF4444;">
                <h3 style="color: #991B1B; margin: 0 0 15px 0; font-size: 16px;">🛡️ Security Notice</h3>
                <p style="color: #7F1D1D; margin: 0; font-size: 14px;">
                    If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                    For security concerns, contact our support team immediately.
                </p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background: #F9FAFB; padding: 30px 20px; text-align: center; border-top: 1px solid #E5E7EB;">
            <p style="color: #6B7280; font-size: 14px; margin: 0 0 10px 0;">
                This reset link will expire in 1 hour for security reasons.
            </p>
            <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
                © 2025 SecureDevOps Platform. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
            ''',
            
            'welcome': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to SecureDevOps Platform</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Arial', sans-serif; background-color: #f3f4f6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: bold;">
                🎉 Welcome to SecureDevOps Platform!
            </h1>
            <p style="color: #D1FAE5; margin: 10px 0 0 0; font-size: 16px;">
                Your journey to secure development starts here
            </p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 20px;">
            <h2 style="color: #374151; font-size: 24px; margin: 0 0 20px 0;">
                Hi {{ user_name }}, you're all set! 🚀
            </h2>
            
            <p style="color: #6B7280; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                Thank you for joining SecureDevOps Platform! Your account has been successfully created and you now have access to our comprehensive security scanning and analysis tools.
            </p>
            
            <!-- Get Started Button -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ dashboard_url }}" 
                   style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                          color: #ffffff; 
                          padding: 16px 32px; 
                          text-decoration: none; 
                          border-radius: 12px; 
                          display: inline-block;
                          font-weight: bold;
                          font-size: 16px;
                          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                    🚀 Get Started
                </a>
            </div>
            
            <!-- Features Grid -->
            <div style="margin: 30px 0;">
                <h3 style="color: #374151; margin: 0 0 20px 0; font-size: 20px; text-align: center;">🛡️ What you can do now:</h3>
                
                <div style="display: table; width: 100%; margin: 20px 0;">
                    <div style="display: table-cell; width: 50%; padding: 15px; vertical-align: top;">
                        <div style="background: #F0FDF4; padding: 20px; border-radius: 12px; border-left: 4px solid #10B981;">
                            <h4 style="color: #065F46; margin: 0 0 10px 0; font-size: 16px;">🔍 Security Scanning</h4>
                            <p style="color: #047857; margin: 0; font-size: 14px;">Advanced SAST, secrets detection, and container scanning</p>
                        </div>
                    </div>
                    <div style="display: table-cell; width: 50%; padding: 15px; vertical-align: top;">
                        <div style="background: #EFF6FF; padding: 20px; border-radius: 12px; border-left: 4px solid #3B82F6;">
                            <h4 style="color: #1E40AF; margin: 0 0 10px 0; font-size: 16px;">🤖 AI Analysis</h4>
                            <p style="color: #1D4ED8; margin: 0; font-size: 14px;">AI-powered vulnerability assessment and recommendations</p>
                        </div>
                    </div>
                </div>
                
                <div style="display: table; width: 100%; margin: 20px 0;">
                    <div style="display: table-cell; width: 50%; padding: 15px; vertical-align: top;">
                        <div style="background: #FEF3C7; padding: 20px; border-radius: 12px; border-left: 4px solid #F59E0B;">
                            <h4 style="color: #92400E; margin: 0 0 10px 0; font-size: 16px;">📊 Compliance Reports</h4>
                            <p style="color: #B45309; margin: 0; font-size: 14px;">Comprehensive reporting for OWASP, PCI DSS, and more</p>
                        </div>
                    </div>
                    <div style="display: table-cell; width: 50%; padding: 15px; vertical-align: top;">
                        <div style="background: #F3E8FF; padding: 20px; border-radius: 12px; border-left: 4px solid #8B5CF6;">
                            <h4 style="color: #6B21A8; margin: 0 0 10px 0; font-size: 16px;">⚡ Real-time Alerts</h4>
                            <p style="color: #7C2D92; margin: 0; font-size: 14px;">Instant notifications for security findings</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Start Guide -->
            <div style="margin: 30px 0; padding: 25px; background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0;">
                <h3 style="color: #1E293B; margin: 0 0 15px 0; font-size: 18px;">🎯 Quick Start Guide</h3>
                <ol style="color: #475569; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li style="margin-bottom: 8px;"><strong>Add your first project:</strong> Connect your GitHub repository or upload your code</li>
                    <li style="margin-bottom: 8px;"><strong>Run a security scan:</strong> Our AI will analyze your code for vulnerabilities</li>
                    <li style="margin-bottom: 8px;"><strong>Review results:</strong> Get detailed reports with actionable recommendations</li>
                    <li style="margin-bottom: 8px;"><strong>Set up alerts:</strong> Configure notifications for continuous monitoring</li>
                </ol>
            </div>
            
            <!-- Support -->
            <div style="margin: 30px 0; padding: 20px; background: #FEF7FF; border-radius: 12px; border-left: 4px solid #A855F7;">
                <h3 style="color: #7E22CE; margin: 0 0 15px 0; font-size: 16px;">💬 Need Help?</h3>
                <p style="color: #8B5CF6; margin: 0 0 10px 0; font-size: 14px;">
                    Our team is here to help you get the most out of SecureDevOps Platform.
                </p>
                <p style="color: #8B5CF6; margin: 0; font-size: 14px;">
                    📧 Email: support@securedevops.platform<br>
                    📚 Documentation: <a href="{{ docs_url }}" style="color: #7C3AED;">User Guide</a>
                </p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background: #F9FAFB; padding: 30px 20px; text-align: center; border-top: 1px solid #E5E7EB;">
            <p style="color: #6B7280; font-size: 14px; margin: 0 0 10px 0;">
                Welcome aboard! We're excited to help you secure your development workflow.
            </p>
            <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
                © 2025 SecureDevOps Platform. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
            '''
        }
    
    def get_source(self, environment, template):
        if template not in self.templates:
            raise TemplateNotFound(template)
        source = self.templates[template]
        return source, None, lambda: True


class EmailService:
    """Production-ready email service with SMTP support"""
    
    def __init__(self):
        self.jinja_env = Environment(loader=EmailTemplateLoader())
        self._configure_provider()
    
    def _configure_provider(self):
        """Configure SMTP settings based on provider or custom settings"""
        if not settings.email_enabled:
            logger.info("Email service disabled")
            return
            
        # Provider-specific configurations
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
        Send email using SMTP
        
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
            
            # Send email
            await self._send_smtp_email(message, to_email)
            
            logger.info(f"✅ Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
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
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔐 Verify Your Email - SecureDevOps Platform",
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
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔑 Password Reset - SecureDevOps Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False
    
    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        try:
            dashboard_url = f"{settings.frontend_url}/"
            docs_url = f"{settings.frontend_url}/docs"  # You can adjust this URL
            
            template = self.jinja_env.get_template('welcome')
            html_body = template.render(
                user_name=user_name,
                dashboard_url=dashboard_url,
                docs_url=docs_url,
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🎉 Welcome to SecureDevOps Platform - Let's Get Started!",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
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
