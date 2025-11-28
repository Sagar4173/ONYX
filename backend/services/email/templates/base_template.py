"""
Base Email Template and Styles
Provides the foundation for all email templates
"""

# Base email styles for consistency
BASE_STYLES = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
</style>
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
