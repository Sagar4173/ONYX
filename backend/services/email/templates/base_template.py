"""
Base Email Template and Styles
Provides the foundation for all email templates
"""

from datetime import datetime
from config import settings

# Base email styles - using web-safe fonts for email compatibility
BASE_STYLES = '''
<!--[if mso]>
<style type="text/css">
    body, table, td {font-family: Arial, Helvetica, sans-serif !important;}
</style>
<![endif]-->
'''


def get_base_template(
    title: str,
    header_gradient: str,
    header_icon: str,
    header_subtitle: str,
    content: str,
    footer_text: str = ""
) -> str:
    """
    Generate base email template with consistent styling
    
    Args:
        title: Email title for <title> tag
        header_gradient: CSS gradient for header background
        header_icon: Emoji or icon for header
        header_subtitle: Subtitle text in header
        content: Main HTML content body
        footer_text: Optional footer message
        
    Returns:
        Complete HTML email template
    """
    current_year = datetime.now().year
    base_url = settings.frontend_url
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    {BASE_STYLES}
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #0f172a;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0f172a;">
        <tr>
            <td align="center" style="padding: 20px;">
                <!-- Main Card -->
                <table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" style="max-width: 640px; width: 100%; background-color: #1e293b; border-radius: 24px; border: 1px solid #334155;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: {header_gradient}; background-color: #10b981; padding: 32px 24px; text-align: center; border-radius: 24px 24px 0 0;">
                            <div style="font-size: 40px; margin-bottom: 12px;">{header_icon}</div>
                            <h1 style="color: #ffffff; font-size: 24px; margin: 0; font-weight: 700; letter-spacing: -0.5px;">
                                SecureDevOps Platform
                            </h1>
                            <p style="color: #d1fae5; margin: 8px 0 0 0; font-size: 14px; font-weight: 500;">
                                {header_subtitle}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 32px; background-color: #1e293b;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 32px; text-align: center; border-top: 1px solid #334155; border-radius: 0 0 24px 24px;">
                            {f'<p style="color: #94a3b8; font-size: 13px; margin: 0 0 16px 0;">{footer_text}</p>' if footer_text else ''}
                            <p style="color: #64748b; font-size: 12px; margin: 0;">
                                © {current_year} SecureDevOps Platform. All rights reserved.
                            </p>
                            <p style="margin-top: 16px; margin-bottom: 0;">
                                <a href="{base_url}/privacy-policy" style="color: #64748b; text-decoration: none; font-size: 12px;">Privacy Policy</a>
                                <span style="color: #475569;"> • </span>
                                <a href="{base_url}/terms-of-service" style="color: #64748b; text-decoration: none; font-size: 12px;">Terms of Service</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


# Color constants for severity levels
SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#22c55e",
    "info": "#3b82f6"
}


# Common gradient patterns
GRADIENTS = {
    "purple": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)",
    "red": "linear-gradient(135deg, #ef4444 0%, #f97316 100%)",
    "green": "linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)",
    "blue": "linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%)",
    "orange": "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
    "cyan": "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
    "amber": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
    "dark_red": "linear-gradient(135deg, #dc2626 0%, #ef4444 50%, #f97316 100%)",
    "purple_blue": "linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%)"
}
