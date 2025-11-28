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
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

# Base email styles for consistency
BASE_STYLES = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
</style>
'''

def get_base_template(title: str, header_gradient: str, header_icon: str, header_subtitle: str, content: str, footer_text: str = "") -> str:
    """Generate base email template with consistent styling"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    {BASE_STYLES}
</head>
<body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; min-height: 100vh;">
    <div style="max-width: 640px; margin: 0 auto; padding: 20px;">
        <!-- Main Card -->
        <div style="background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%); border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); border: 1px solid rgba(255,255,255,0.1);">
            
            <!-- Header -->
            <div style="background: {header_gradient}; padding: 48px 32px; text-align: center; position: relative; overflow: hidden;">
                <div style="position: relative; z-index: 1;">
                    <div style="font-size: 48px; margin-bottom: 16px;">{header_icon}</div>
                    <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px;">
                        SecureDevOps Platform
                    </h1>
                    <p style="color: rgba(255,255,255,0.85); margin: 12px 0 0 0; font-size: 16px; font-weight: 500;">
                        {header_subtitle}
                    </p>
                </div>
                <!-- Decorative circles -->
                <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                <div style="position: absolute; bottom: -30px; left: -30px; width: 100px; height: 100px; background: rgba(255,255,255,0.05); border-radius: 50%;"></div>
            </div>
            
            <!-- Content -->
            <div style="padding: 40px 32px;">
                {content}
            </div>
            
            <!-- Footer -->
            <div style="background: rgba(0,0,0,0.3); padding: 32px; text-align: center; border-top: 1px solid rgba(255,255,255,0.1);">
                {f'<p style="color: #94a3b8; font-size: 14px; margin: 0 0 12px 0;">{footer_text}</p>' if footer_text else ''}
                <p style="color: #64748b; font-size: 12px; margin: 0;">
                    © 2025 SecureDevOps Platform. All rights reserved.
                </p>
                <div style="margin-top: 16px;">
                    <a href="#" style="color: #64748b; text-decoration: none; margin: 0 8px; font-size: 12px;">Privacy Policy</a>
                    <span style="color: #475569;">•</span>
                    <a href="#" style="color: #64748b; text-decoration: none; margin: 0 8px; font-size: 12px;">Terms of Service</a>
                    <span style="color: #475569;">•</span>
                    <a href="#" style="color: #64748b; text-decoration: none; margin: 0 8px; font-size: 12px;">Unsubscribe</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''


class EmailTemplateLoader(BaseLoader):
    """Custom Jinja2 template loader for email templates"""
    
    def __init__(self):
        self.templates = {
            'verification': get_base_template(
                title="Email Verification",
                header_gradient="linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)",
                header_icon="✉️",
                header_subtitle="Verify Your Email Address",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Welcome to SecureDevOps! 👋
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Thank you for joining our platform. To complete your registration and unlock all security features, please verify your email address.
                </p>
                
                <!-- CTA Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ verification_url }}" 
                       style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(99, 102, 241, 0.5);
                              transition: all 0.3s ease;">
                        Verify Email Address →
                    </a>
                </div>
                
                <!-- Features Preview -->
                <div style="margin: 32px 0; padding: 24px; background: rgba(99, 102, 241, 0.1); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
                    <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">🚀 What awaits you:</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 12px;">
                        <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 8px 16px; border-radius: 20px; font-size: 13px;">🔍 Advanced SAST Scanning</span>
                        <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 8px 16px; border-radius: 20px; font-size: 13px;">🤖 AI-Powered Analysis</span>
                        <span style="background: rgba(249, 115, 22, 0.2); color: #fb923c; padding: 8px 16px; border-radius: 20px; font-size: 13px;">🔐 Secret Detection</span>
                        <span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; padding: 8px 16px; border-radius: 20px; font-size: 13px;">📊 Compliance Reports</span>
                    </div>
                </div>
                
                <!-- Alternative Link -->
                <div style="margin-top: 24px; padding: 16px; background: rgba(255,255,255,0.05); border-radius: 12px;">
                    <p style="color: #64748b; font-size: 13px; margin: 0;">
                        Button not working? Copy and paste this link in your browser:<br>
                        <a href="{{ verification_url }}" style="color: #818cf8; word-break: break-all; font-size: 12px;">{{ verification_url }}</a>
                    </p>
                </div>
                ''',
                footer_text="This verification link expires in 24 hours."
            ),
            
            'password_reset': get_base_template(
                title="Password Reset",
                header_gradient="linear-gradient(135deg, #ef4444 0%, #f97316 100%)",
                header_icon="🔑",
                header_subtitle="Reset Your Password",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Password Reset Request
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    We received a request to reset your password. If you made this request, click the button below to create a new password.
                </p>
                
                <!-- CTA Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ reset_url }}" 
                       style="background: linear-gradient(135deg, #ef4444 0%, #f97316 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(239, 68, 68, 0.5);">
                        Reset Password →
                    </a>
                </div>
                
                <!-- Security Warning -->
                <div style="margin: 32px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">⚠️</span>
                        <div>
                            <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Security Notice</h4>
                            <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                                If you didn't request this password reset, please ignore this email. Your account remains secure and your password will not be changed.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Alternative Link -->
                <div style="margin-top: 24px; padding: 16px; background: rgba(255,255,255,0.05); border-radius: 12px;">
                    <p style="color: #64748b; font-size: 13px; margin: 0;">
                        Button not working? Copy and paste this link:<br>
                        <a href="{{ reset_url }}" style="color: #fb923c; word-break: break-all; font-size: 12px;">{{ reset_url }}</a>
                    </p>
                </div>
                ''',
                footer_text="This reset link expires in 1 hour for security reasons."
            ),
            
            'welcome': get_base_template(
                title="Welcome to SecureDevOps",
                header_gradient="linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)",
                header_icon="🎉",
                header_subtitle="Your Security Journey Begins",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Welcome aboard, {{ user_name }}! 🚀
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Your account is now active and ready to secure your codebase. Let's explore what you can accomplish with SecureDevOps Platform.
                </p>
                
                <!-- Get Started Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ dashboard_url }}" 
                       style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(16, 185, 129, 0.5);">
                        Go to Dashboard →
                    </a>
                </div>
                
                <!-- Feature Cards -->
                <div style="margin: 32px 0;">
                    <h3 style="color: #e2e8f0; margin: 0 0 20px 0; font-size: 18px; font-weight: 600; text-align: center;">
                        🛡️ Your Security Toolkit
                    </h3>
                    
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 20px; border-radius: 16px; margin-bottom: 12px; border: 1px solid rgba(16, 185, 129, 0.2);">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="background: rgba(16, 185, 129, 0.2); padding: 12px; border-radius: 12px;">
                                <span style="font-size: 24px;">🔍</span>
                            </div>
                            <div>
                                <h4 style="color: #34d399; margin: 0 0 4px 0; font-size: 16px; font-weight: 600;">Security Scanning</h4>
                                <p style="color: #6ee7b7; margin: 0; font-size: 14px;">SAST, secrets detection, dependency analysis, and container scanning</p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(59, 130, 246, 0.1); padding: 20px; border-radius: 16px; margin-bottom: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="background: rgba(59, 130, 246, 0.2); padding: 12px; border-radius: 12px;">
                                <span style="font-size: 24px;">🤖</span>
                            </div>
                            <div>
                                <h4 style="color: #60a5fa; margin: 0 0 4px 0; font-size: 16px; font-weight: 600;">AI-Powered Analysis</h4>
                                <p style="color: #93c5fd; margin: 0; font-size: 14px;">Intelligent vulnerability assessment with actionable remediation</p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(168, 85, 247, 0.1); padding: 20px; border-radius: 16px; border: 1px solid rgba(168, 85, 247, 0.2);">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="background: rgba(168, 85, 247, 0.2); padding: 12px; border-radius: 12px;">
                                <span style="font-size: 24px;">📊</span>
                            </div>
                            <div>
                                <h4 style="color: #c084fc; margin: 0 0 4px 0; font-size: 16px; font-weight: 600;">Compliance & Reports</h4>
                                <p style="color: #d8b4fe; margin: 0; font-size: 14px;">OWASP, PCI DSS, SOC 2, and custom compliance frameworks</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Start -->
                <div style="margin: 32px 0; padding: 24px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">🎯 Quick Start Guide</h3>
                    <ol style="color: #94a3b8; margin: 0; padding-left: 20px; line-height: 2;">
                        <li><strong style="color: #e2e8f0;">Add a project</strong> - Connect your repository or upload code</li>
                        <li><strong style="color: #e2e8f0;">Run your first scan</strong> - Choose scanners and analyze</li>
                        <li><strong style="color: #e2e8f0;">Review findings</strong> - Get AI-powered insights</li>
                        <li><strong style="color: #e2e8f0;">Set up alerts</strong> - Stay informed in real-time</li>
                    </ol>
                </div>
                ''',
                footer_text="Questions? Reply to this email and we'll help you get started."
            ),
            
            'scan_completed': get_base_template(
                title="Scan Completed",
                header_gradient="linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%)",
                header_icon="✅",
                header_subtitle="Security Scan Completed",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Scan Complete: {{ project_name }}
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Your {{ scan_type }} security scan has finished. Here's a summary of the findings:
                </p>
                
                <!-- Stats Grid -->
                <div style="display: table; width: 100%; margin: 24px 0;">
                    <div style="display: table-row;">
                        <div style="display: table-cell; width: 25%; padding: 8px;">
                            <div style="background: rgba(239, 68, 68, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(239, 68, 68, 0.3);">
                                <div style="font-size: 32px; font-weight: 700; color: #f87171;">{{ critical_count }}</div>
                                <div style="font-size: 12px; color: #fca5a5; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Critical</div>
                            </div>
                        </div>
                        <div style="display: table-cell; width: 25%; padding: 8px;">
                            <div style="background: rgba(249, 115, 22, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(249, 115, 22, 0.3);">
                                <div style="font-size: 32px; font-weight: 700; color: #fb923c;">{{ high_count }}</div>
                                <div style="font-size: 12px; color: #fdba74; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">High</div>
                            </div>
                        </div>
                        <div style="display: table-cell; width: 25%; padding: 8px;">
                            <div style="background: rgba(234, 179, 8, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(234, 179, 8, 0.3);">
                                <div style="font-size: 32px; font-weight: 700; color: #fbbf24;">{{ medium_count }}</div>
                                <div style="font-size: 12px; color: #fcd34d; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Medium</div>
                            </div>
                        </div>
                        <div style="display: table-cell; width: 25%; padding: 8px;">
                            <div style="background: rgba(34, 197, 94, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(34, 197, 94, 0.3);">
                                <div style="font-size: 32px; font-weight: 700; color: #4ade80;">{{ low_count }}</div>
                                <div style="font-size: 12px; color: #86efac; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Low</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Scan Details -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(59, 130, 246, 0.1); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.2);">
                    <h3 style="color: #93c5fd; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">📋 Scan Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Scan Type</td>
                            <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ scan_type }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Duration</td>
                            <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ duration }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Files Scanned</td>
                            <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ files_scanned }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Completed At</td>
                            <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ completed_at }}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- View Report Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ report_url }}" 
                       style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(59, 130, 246, 0.5);">
                        View Full Report →
                    </a>
                </div>
                ''',
                footer_text="You received this because scan notifications are enabled."
            ),
            
            'security_alert': get_base_template(
                title="Security Alert",
                header_gradient="linear-gradient(135deg, #dc2626 0%, #ef4444 50%, #f97316 100%)",
                header_icon="🚨",
                header_subtitle="Critical Security Alert",
                content='''
                <div style="background: rgba(239, 68, 68, 0.2); padding: 16px 20px; border-radius: 12px; margin-bottom: 24px; border: 1px solid rgba(239, 68, 68, 0.4);">
                    <p style="color: #fca5a5; margin: 0; font-size: 14px; font-weight: 500;">
                        ⚠️ Immediate attention required
                    </p>
                </div>
                
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    {{ alert_title }}
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    {{ alert_description }}
                </p>
                
                <!-- Alert Details -->
                <div style="margin: 24px 0; padding: 24px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border-left: 4px solid #ef4444;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">Severity</td>
                            <td style="padding: 10px 0; text-align: right;">
                                <span style="background: {{ severity_color }}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{{ severity }}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">Project</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ project_name }}</td>
                        </tr>
                        <tr>
                            <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">File</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ file_path }}</td>
                        </tr>
                        <tr>
                            <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">Detected At</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ detected_at }}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Vulnerability Type -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px;">
                    <h3 style="color: #e2e8f0; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">🔍 Vulnerability Details</h3>
                    <p style="color: #94a3b8; margin: 0; font-size: 14px; line-height: 1.7;">
                        <strong style="color: #e2e8f0;">Type:</strong> {{ vulnerability_type }}<br>
                        <strong style="color: #e2e8f0;">CWE:</strong> {{ cwe_id }}<br>
                        <strong style="color: #e2e8f0;">CVSS Score:</strong> {{ cvss_score }}
                    </p>
                </div>
                
                <!-- Recommendation -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <h3 style="color: #34d399; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">💡 Recommended Action</h3>
                    <p style="color: #6ee7b7; margin: 0; font-size: 14px; line-height: 1.7;">
                        {{ recommendation }}
                    </p>
                </div>
                
                <!-- View Details Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ alert_url }}" 
                       style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(220, 38, 38, 0.5);">
                        View & Remediate →
                    </a>
                </div>
                ''',
                footer_text="This is an automated security alert. Please review immediately."
            ),
            
            'weekly_digest': get_base_template(
                title="Weekly Security Digest",
                header_gradient="linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%)",
                header_icon="📊",
                header_subtitle="Your Weekly Security Summary",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 8px 0; font-weight: 600;">
                    Week of {{ week_start }} - {{ week_end }}
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Here's your security summary for the past week across all projects.
                </p>
                
                <!-- Overall Stats -->
                <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%); padding: 24px; border-radius: 16px; margin-bottom: 24px; border: 1px solid rgba(139, 92, 246, 0.3);">
                    <h3 style="color: #c4b5fd; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📈 Overview</h3>
                    <div style="display: table; width: 100%;">
                        <div style="display: table-cell; width: 33%; text-align: center; padding: 8px;">
                            <div style="font-size: 36px; font-weight: 700; color: #a78bfa;">{{ total_scans }}</div>
                            <div style="font-size: 12px; color: #c4b5fd; margin-top: 4px;">Scans Run</div>
                        </div>
                        <div style="display: table-cell; width: 33%; text-align: center; padding: 8px; border-left: 1px solid rgba(139, 92, 246, 0.3); border-right: 1px solid rgba(139, 92, 246, 0.3);">
                            <div style="font-size: 36px; font-weight: 700; color: #f87171;">{{ total_vulnerabilities }}</div>
                            <div style="font-size: 12px; color: #fca5a5; margin-top: 4px;">Vulnerabilities</div>
                        </div>
                        <div style="display: table-cell; width: 33%; text-align: center; padding: 8px;">
                            <div style="font-size: 36px; font-weight: 700; color: #4ade80;">{{ resolved_count }}</div>
                            <div style="font-size: 12px; color: #86efac; margin-top: 4px;">Resolved</div>
                        </div>
                    </div>
                </div>
                
                <!-- Severity Breakdown -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px;">
                    <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">🎯 Severity Breakdown</h3>
                    
                    <!-- Critical Bar -->
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="color: #f87171; font-size: 13px; font-weight: 500;">Critical</span>
                            <span style="color: #f87171; font-size: 13px;">{{ critical_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #ef4444, #f87171); height: 100%; width: {{ critical_percent }}%; border-radius: 8px;"></div>
                        </div>
                    </div>
                    
                    <!-- High Bar -->
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="color: #fb923c; font-size: 13px; font-weight: 500;">High</span>
                            <span style="color: #fb923c; font-size: 13px;">{{ high_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #f97316, #fb923c); height: 100%; width: {{ high_percent }}%; border-radius: 8px;"></div>
                        </div>
                    </div>
                    
                    <!-- Medium Bar -->
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="color: #fbbf24; font-size: 13px; font-weight: 500;">Medium</span>
                            <span style="color: #fbbf24; font-size: 13px;">{{ medium_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #eab308, #fbbf24); height: 100%; width: {{ medium_percent }}%; border-radius: 8px;"></div>
                        </div>
                    </div>
                    
                    <!-- Low Bar -->
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="color: #4ade80; font-size: 13px; font-weight: 500;">Low</span>
                            <span style="color: #4ade80; font-size: 13px;">{{ low_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #22c55e, #4ade80); height: 100%; width: {{ low_percent }}%; border-radius: 8px;"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Top Issues -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <h3 style="color: #fca5a5; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">⚠️ Top Issues Requiring Attention</h3>
                    {{ top_issues_html }}
                </div>
                
                <!-- View Dashboard Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ dashboard_url }}" 
                       style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(139, 92, 246, 0.5);">
                        View Full Dashboard →
                    </a>
                </div>
                ''',
                footer_text="You're receiving this weekly digest based on your notification preferences."
            ),
            
            'new_vulnerability': get_base_template(
                title="New Vulnerability Found",
                header_gradient="linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
                header_icon="🔓",
                header_subtitle="New Vulnerability Detected",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    {{ vulnerability_title }}
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    A new {{ severity }} severity vulnerability has been detected in your project <strong style="color: #e2e8f0;">{{ project_name }}</strong>.
                </p>
                
                <!-- Severity Badge -->
                <div style="text-align: center; margin: 24px 0;">
                    <span style="background: {{ severity_color }}; color: white; padding: 8px 24px; border-radius: 24px; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
                        {{ severity }} SEVERITY
                    </span>
                </div>
                
                <!-- Vulnerability Info -->
                <div style="margin: 24px 0; padding: 24px; background: rgba(249, 115, 22, 0.1); border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.2);">
                    <h3 style="color: #fdba74; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">📍 Location</h3>
                    <div style="background: rgba(0,0,0,0.3); padding: 16px; border-radius: 12px; font-family: 'Monaco', 'Menlo', monospace;">
                        <p style="color: #e2e8f0; margin: 0 0 8px 0; font-size: 14px;">
                            <span style="color: #64748b;">File:</span> {{ file_path }}
                        </p>
                        <p style="color: #e2e8f0; margin: 0; font-size: 14px;">
                            <span style="color: #64748b;">Line:</span> {{ line_number }}
                        </p>
                    </div>
                </div>
                
                <!-- Description -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px;">
                    <h3 style="color: #e2e8f0; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">📝 Description</h3>
                    <p style="color: #94a3b8; margin: 0; font-size: 14px; line-height: 1.7;">
                        {{ description }}
                    </p>
                </div>
                
                <!-- Fix Suggestion -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <h3 style="color: #34d399; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">🛠️ How to Fix</h3>
                    <p style="color: #6ee7b7; margin: 0; font-size: 14px; line-height: 1.7;">
                        {{ fix_suggestion }}
                    </p>
                </div>
                
                <!-- Action Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ vulnerability_url }}" 
                       style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); 
                              color: #ffffff; 
                              padding: 16px 40px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 16px;
                              box-shadow: 0 10px 30px -5px rgba(249, 115, 22, 0.5);">
                        View Details & Fix →
                    </a>
                </div>
                ''',
                footer_text="Act quickly on high and critical vulnerabilities to maintain security."
            ),
            
            'login_alert': get_base_template(
                title="New Login Detected",
                header_gradient="linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
                header_icon="🔐",
                header_subtitle="New Login to Your Account",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    New Login Detected
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    We noticed a new login to your SecureDevOps account. If this was you, no action is needed.
                </p>
                
                <!-- Login Details -->
                <div style="margin: 24px 0; padding: 24px; background: rgba(6, 182, 212, 0.1); border-radius: 16px; border: 1px solid rgba(6, 182, 212, 0.2);">
                    <h3 style="color: #67e8f9; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">📋 Login Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Time</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ login_time }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Location</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ location }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Device</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ device }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Browser</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ browser }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">IP Address</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ ip_address }}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Security Warning -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">⚠️</span>
                        <div>
                            <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Not you?</h4>
                            <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                                If you didn't log in, your account may be compromised. Please change your password immediately and enable two-factor authentication.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ secure_account_url }}" 
                       style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                              color: #ffffff; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              margin-right: 12px;
                              box-shadow: 0 8px 20px -5px rgba(239, 68, 68, 0.4);">
                        Secure Account
                    </a>
                    <a href="{{ review_sessions_url }}" 
                       style="background: rgba(255,255,255,0.1); 
                              color: #e2e8f0; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              border: 1px solid rgba(255,255,255,0.2);">
                        Review Sessions
                    </a>
                </div>
                ''',
                footer_text="This is an automated security notification."
            ),
            
            '2fa_enabled': get_base_template(
                title="Two-Factor Authentication Enabled",
                header_gradient="linear-gradient(135deg, #10b981 0%, #059669 100%)",
                header_icon="🛡️",
                header_subtitle="2FA Successfully Activated",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Two-Factor Authentication Enabled ✅
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Great news! Two-factor authentication has been successfully enabled on your SecureDevOps account. Your account is now more secure.
                </p>
                
                <!-- Success Badge -->
                <div style="text-align: center; margin: 32px 0;">
                    <div style="display: inline-block; background: rgba(16, 185, 129, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.3);">
                        <span style="font-size: 48px;">🔐</span>
                        <p style="color: #34d399; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">Your account is now protected</p>
                    </div>
                </div>
                
                <!-- What's Changed -->
                <div style="margin: 32px 0; padding: 24px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <h3 style="color: #34d399; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 What's Changed</h3>
                    <ul style="color: #6ee7b7; margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li>You'll need to enter a 6-digit code when logging in</li>
                        <li>Codes are generated by your authenticator app</li>
                        <li>Each code expires after 30 seconds</li>
                        <li>Invalid codes are rejected for security</li>
                    </ul>
                </div>
                
                <!-- Backup Codes Reminder -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(234, 179, 8, 0.1); border-radius: 16px; border: 1px solid rgba(234, 179, 8, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">⚠️</span>
                        <div>
                            <h4 style="color: #fbbf24; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Save Your Backup Codes</h4>
                            <p style="color: #fcd34d; margin: 0; font-size: 14px; line-height: 1.6;">
                                Make sure you've saved your backup codes in a secure location. You'll need them if you lose access to your authenticator app.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Security Notice -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">🚨</span>
                        <div>
                            <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Wasn't You?</h4>
                            <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                                If you didn't enable 2FA, your account may be compromised. Please secure your account immediately and contact support.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Action Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ security_settings_url }}" 
                       style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                              color: #ffffff; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              box-shadow: 0 8px 20px -5px rgba(16, 185, 129, 0.4);">
                        View Security Settings
                    </a>
                </div>
                ''',
                footer_text="This is an automated security notification."
            ),
            
            '2fa_disabled': get_base_template(
                title="Two-Factor Authentication Disabled",
                header_gradient="linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
                header_icon="⚠️",
                header_subtitle="2FA Has Been Disabled",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Two-Factor Authentication Disabled
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Two-factor authentication has been disabled on your SecureDevOps account. Your account is now less secure.
                </p>
                
                <!-- Warning Badge -->
                <div style="text-align: center; margin: 32px 0;">
                    <div style="display: inline-block; background: rgba(249, 115, 22, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.3);">
                        <span style="font-size: 48px;">🔓</span>
                        <p style="color: #fb923c; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">2FA Protection Removed</p>
                    </div>
                </div>
                
                <!-- What This Means -->
                <div style="margin: 32px 0; padding: 24px; background: rgba(249, 115, 22, 0.1); border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.2);">
                    <h3 style="color: #fb923c; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 What This Means</h3>
                    <ul style="color: #fdba74; margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li>Your account is now protected only by your password</li>
                        <li>No verification code will be required to log in</li>
                        <li>Your account is more vulnerable to unauthorized access</li>
                    </ul>
                </div>
                
                <!-- Re-enable Recommendation -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">💡</span>
                        <div>
                            <h4 style="color: #34d399; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Recommendation</h4>
                            <p style="color: #6ee7b7; margin: 0; font-size: 14px; line-height: 1.6;">
                                We strongly recommend re-enabling 2FA to protect your account. Two-factor authentication adds an essential layer of security.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Security Alert -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.15); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">🚨</span>
                        <div>
                            <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Wasn't You?</h4>
                            <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                                If you didn't disable 2FA, your account has been compromised. Change your password immediately and contact support.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ enable_2fa_url }}" 
                       style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                              color: #ffffff; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              margin-right: 12px;
                              box-shadow: 0 8px 20px -5px rgba(16, 185, 129, 0.4);">
                        Re-enable 2FA
                    </a>
                    <a href="{{ secure_account_url }}" 
                       style="background: rgba(255,255,255,0.1); 
                              color: #e2e8f0; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              border: 1px solid rgba(255,255,255,0.2);">
                        Secure Account
                    </a>
                </div>
                ''',
                footer_text="This is an automated security notification."
            ),
            
            '2fa_recovery_used': get_base_template(
                title="Recovery Code Used",
                header_gradient="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                header_icon="🔑",
                header_subtitle="A Recovery Code Was Used",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Recovery Code Used for Login
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    A recovery code was used to log into your SecureDevOps account. This may have been you, or someone with access to your backup codes.
                </p>
                
                <!-- Warning Badge -->
                <div style="text-align: center; margin: 32px 0;">
                    <div style="display: inline-block; background: rgba(245, 158, 11, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(245, 158, 11, 0.3);">
                        <span style="font-size: 48px;">🔐</span>
                        <p style="color: #fbbf24; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">Recovery Code Consumed</p>
                    </div>
                </div>
                
                <!-- Usage Details -->
                <div style="margin: 32px 0; padding: 24px; background: rgba(245, 158, 11, 0.1); border-radius: 16px; border: 1px solid rgba(245, 158, 11, 0.2);">
                    <h3 style="color: #fbbf24; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 Usage Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Used At</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ used_at }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">IP Address</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ ip_address }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Remaining Codes</td>
                            <td style="color: {{ '#fbbf24' if remaining_codes > 3 else '#ef4444' }}; padding: 10px 0; font-size: 14px; text-align: right; font-weight: 600;">{{ remaining_codes }} codes left</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Important Notice -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(234, 179, 8, 0.1); border-radius: 16px; border: 1px solid rgba(234, 179, 8, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">⚠️</span>
                        <div>
                            <h4 style="color: #fbbf24; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Generate New Codes</h4>
                            <p style="color: #fcd34d; margin: 0; font-size: 14px; line-height: 1.6;">
                                Each recovery code can only be used once. Consider generating new backup codes to ensure you always have access to your account.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Security Alert -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.15); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">🚨</span>
                        <div>
                            <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Wasn't You?</h4>
                            <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                                If you didn't use a recovery code, someone may have access to your backup codes. Secure your account immediately and regenerate your codes.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Action Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ security_url }}" 
                       style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                              color: #ffffff; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              box-shadow: 0 8px 20px -5px rgba(245, 158, 11, 0.4);">
                        Manage Recovery Codes
                    </a>
                </div>
                ''',
                footer_text="This is an automated security notification."
            ),
            
            'password_changed': get_base_template(
                title="Password Changed",
                header_gradient="linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                header_icon="🔑",
                header_subtitle="Your Password Has Been Changed",
                content='''
                <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
                    Password Successfully Changed
                </h2>
                
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
                    Your SecureDevOps account password was changed on {{ changed_at }}. If you made this change, no further action is needed.
                </p>
                
                <!-- Success Badge -->
                <div style="text-align: center; margin: 32px 0;">
                    <div style="display: inline-block; background: rgba(99, 102, 241, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.3);">
                        <span style="font-size: 48px;">✅</span>
                        <p style="color: #a5b4fc; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">Password Updated</p>
                    </div>
                </div>
                
                <!-- Change Details -->
                <div style="margin: 32px 0; padding: 24px; background: rgba(99, 102, 241, 0.1); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
                    <h3 style="color: #a5b4fc; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 Change Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Changed At</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ changed_at }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">IP Address</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ ip_address }}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Device</td>
                            <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ device }}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Security Alert -->
                <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.15); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <span style="font-size: 24px;">🚨</span>
                        <div>
                            <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Didn't Change Your Password?</h4>
                            <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                                If you didn't make this change, your account may be compromised. Click the button below to secure your account immediately.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Action Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{{ secure_account_url }}" 
                       style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                              color: #ffffff; 
                              padding: 14px 28px; 
                              text-decoration: none; 
                              border-radius: 12px; 
                              display: inline-block;
                              font-weight: 600;
                              font-size: 14px;
                              box-shadow: 0 8px 20px -5px rgba(239, 68, 68, 0.4);">
                        Secure My Account
                    </a>
                </div>
                ''',
                footer_text="This is an automated security notification."
            )
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
            
            # Color mapping for severity
            severity_colors = {
                "critical": "#dc2626",
                "high": "#f97316",
                "medium": "#eab308",
                "low": "#22c55e",
                "info": "#3b82f6"
            }
            severity_color = severity_colors.get(severity.lower(), "#6b7280")
            
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
            
            severity_colors = {
                "critical": "#dc2626",
                "high": "#f97316",
                "medium": "#eab308",
                "low": "#22c55e"
            }
            severity_color = severity_colors.get(severity.lower(), "#6b7280")
            
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
                subject="🔐 New Login to Your Account - SecureDevOps Platform",
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
                    severity_colors = {
                        "critical": "#f87171",
                        "high": "#fb923c",
                        "medium": "#fbbf24",
                        "low": "#4ade80"
                    }
                    color = severity_colors.get(issue.get('severity', '').lower(), '#94a3b8')
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
                security_url=security_url,
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="✅ Two-Factor Authentication Enabled - SecureDevOps Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send 2FA enabled email: {str(e)}")
            return False

    async def send_2fa_disabled_email(self, email: str, user_name: str, disabled_at: str, ip_address: str = None) -> bool:
        """Send warning email when 2FA is disabled"""
        try:
            security_url = f"{settings.frontend_url}/profile"
            
            template = self.jinja_env.get_template('2fa_disabled')
            html_body = template.render(
                user_name=user_name,
                disabled_at=disabled_at,
                ip_address=ip_address or "Unknown",
                security_url=security_url,
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="⚠️ Two-Factor Authentication Disabled - SecureDevOps Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send 2FA disabled email: {str(e)}")
            return False

    async def send_2fa_recovery_used_email(self, email: str, user_name: str, used_at: str, ip_address: str = None, remaining_codes: int = 0) -> bool:
        """Send alert when a 2FA recovery code is used"""
        try:
            security_url = f"{settings.frontend_url}/profile"
            
            template = self.jinja_env.get_template('2fa_recovery_used')
            html_body = template.render(
                user_name=user_name,
                used_at=used_at,
                ip_address=ip_address or "Unknown",
                remaining_codes=remaining_codes,
                security_url=security_url,
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔑 Recovery Code Used - SecureDevOps Platform",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send 2FA recovery used email: {str(e)}")
            return False

    async def send_password_changed_email(self, email: str, user_name: str, changed_at: str, ip_address: str = None) -> bool:
        """Send notification when password is changed"""
        try:
            security_url = f"{settings.frontend_url}/profile"
            
            template = self.jinja_env.get_template('password_changed')
            html_body = template.render(
                user_name=user_name,
                changed_at=changed_at,
                ip_address=ip_address or "Unknown",
                security_url=security_url,
                platform_name="SecureDevOps Platform"
            )
            
            return await self.send_email(
                to_email=email,
                subject="🔐 Password Changed - SecureDevOps Platform",
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
