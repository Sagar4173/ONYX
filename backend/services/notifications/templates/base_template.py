"""
Base Email Template and Styles
Provides the foundation for all email templates with ONYX design language
"""

from datetime import datetime

from config import settings

BASE_STYLES = '''
<!--[if mso]>
<style type="text/css">
    body, table, td {font-family: Arial, Helvetica, sans-serif !important;}
    .fallback-font {font-family: Arial, Helvetica, sans-serif !important;}
</style>
<![endif]-->
<style>
  @media only screen and (max-width: 480px) {
    .email-container { width: 100% !important; }
    .email-padding { padding: 16px !important; }
    .stack-cell { display: block !important; width: 100% !important; }
    .stack-item { display: block !important; width: 100% !important; margin-bottom: 8px !important; }
    .hide-mobile { display: none !important; }
    .badge-grid { display: block !important; }
    .badge-cell { display: block !important; width: 100% !important; padding: 4px 0 !important; }
  }
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
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #0a0e1a; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0a0e1a;">
        <tr>
            <td align="center" style="padding: 32px 16px;">
                <!-- Preheader Text -->
                <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
                    {header_subtitle} — {footer_text if footer_text else 'ONYX Security Intelligence Platform'}
                </div>
                <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;</div>

                <!-- Main Card -->
                <table class="email-container" role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%; background-color: #111827; border-radius: 16px; border: 1px solid #1f2937; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">

                    <!-- Brand Bar -->
                    <tr>
                        <td style="background: linear-gradient(90deg, #06b6d4, #7c3aed); padding: 3px 0; font-size: 0; line-height: 0;"></td>
                    </tr>

                    <!-- Header -->
                    <tr>
                        <td style="background: {header_gradient}; padding: 36px 32px 28px; text-align: center;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="width: 56px; height: 56px; background: linear-gradient(135deg, #06b6d4, #7c3aed); border-radius: 50%; text-align: center; vertical-align: middle; box-shadow: 0 8px 24px rgba(6, 182, 212, 0.25);">
                                                    <div style="width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05)); margin: 0 auto; line-height: 56px;">
                                                        <span style="font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: 2px;">O</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-bottom: 4px;">
                                        <h1 style="color: #ffffff; font-size: 22px; margin: 0; font-weight: 800; letter-spacing: 3px;">
                                            ONYX
                                        </h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-bottom: 16px;">
                                        <p style="color: rgba(255,255,255,0.5); margin: 0; font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;">
                                            Security Intelligence Platform
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            <div style="font-size: 40px; line-height: 1; margin: 8px 0 4px;">{header_icon}</div>
                            <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 15px; font-weight: 500; line-height: 1.4;">
                                {header_subtitle}
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td class="email-padding" style="padding: 36px 32px; background-color: #111827;">
                            {content}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0a0e1a; padding: 28px 32px; text-align: center; border-top: 1px solid #1f2937;">
                            {f'<p style="color: #64748b; font-size: 13px; margin: 0 0 16px 0; line-height: 1.5;">{footer_text}</p>' if footer_text else ''}
                            <p style="color: #475569; font-size: 11px; margin: 0 0 12px; line-height: 1.6;">
                                &copy; {current_year} ONYX Security Intelligence Platform.
                                <br class="hide-mobile">
                                All rights reserved.
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                <tr>
                                    <td style="padding: 0 8px;">
                                        <a href="{base_url}/privacy-policy" style="color: #64748b; text-decoration: none; font-size: 11px;">Privacy</a>
                                    </td>
                                    <td style="padding: 0 8px;">
                                        <span style="color: #374151; font-size: 11px;">&bull;</span>
                                    </td>
                                    <td style="padding: 0 8px;">
                                        <a href="{base_url}/terms-of-service" style="color: #64748b; text-decoration: none; font-size: 11px;">Terms</a>
                                    </td>
                                    <td style="padding: 0 8px;">
                                        <span style="color: #374151; font-size: 11px;">&bull;</span>
                                    </td>
                                    <td style="padding: 0 8px;">
                                        <a href="{base_url}/profile?tab=notifications" style="color: #64748b; text-decoration: none; font-size: 11px;">Unsubscribe</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>

                <!-- Postscript Note -->
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%; margin-top: 16px;">
                    <tr>
                        <td style="text-align: center; padding: 8px;">
                            <p style="color: #374151; font-size: 10px; margin: 0; line-height: 1.5;">
                                This is an automated message from ONYX Security Intelligence Platform.
                                Please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#22c55e",
    "info": "#3b82f6"
}


GRADIENTS = {
    "purple": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)",
    "red": "linear-gradient(135deg, #ef4444 0%, #f97316 100%)",
    "green": "linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)",
    "blue": "linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%)",
    "orange": "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
    "cyan": "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
    "amber": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
    "dark_red": "linear-gradient(135deg, #dc2626 0%, #ef4444 50%, #f97316 100%)",
    "purple_blue": "linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%)",
    "onyx": "linear-gradient(135deg, #06b6d4 0%, #7c3aed 100%)"
}
