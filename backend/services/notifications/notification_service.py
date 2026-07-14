"""
Notification Service for Security Scanning Platform
Handles sending notifications for scan events and security alerts
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum

from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications that can be sent"""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    CRITICAL_VULNERABILITY = "critical_vulnerability"
    HIGH_SEVERITY_ALERT = "high_severity_alert"
    COMPLIANCE_VIOLATION = "compliance_violation"
    AI_ANALYSIS_READY = "ai_analysis_ready"
    NEW_LOGIN = "new_login"


class NotificationChannel(str, Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationService:
    """Service for handling notifications and alerts"""
    
    def __init__(self):
        self.enabled_channels = [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user's email from database"""
        try:
            from models.user import User
            # User.id is a UUID string, not ObjectId
            user = await User.find_one({"_id": user_id})
            if user and user.email:
                return user.email
            return None
        except Exception as e:
            logger.warning(f"Could not get user email for {user_id}: {e}")
            return None
    
    async def _get_user_notification_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get user's notification preferences"""
        try:
            from models.user import User
            # User.id is a UUID string, not ObjectId
            user = await User.find_one({"_id": user_id})
            if user and hasattr(user, 'notification_preferences'):
                return user.notification_preferences or {}
            return {"email_scan_results": True, "email_security_alerts": True}
        except Exception as e:
            logger.warning(f"Could not get notification preferences for {user_id}: {e}")
            return {"email_scan_results": True, "email_security_alerts": True}
        
    async def send_scan_started(
        self, 
        project_name: str, 
        scan_id: str, 
        user_id: str,
        repository_url: str = None
    ) -> bool:
        """Send notification when a scan starts"""
        try:
            notification_data = {
                "type": NotificationType.SCAN_STARTED,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "repository_url": repository_url,
                "timestamp": utc_now().isoformat(),
                "message": f"Security scan started for project '{project_name}'"
            }
            
            logger.info(f"📬 Scan started notification: {notification_data}")
            
            # For now, just log the notification
            # In production, you would integrate with actual notification services
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send scan started notification: {e}")
            return False
    
    async def send_scan_completed(
        self, 
        project_name: str, 
        scan_id: str, 
        user_id: str,
        findings_count: int = 0,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        scan_type: str = "Security",
        duration: str = "N/A",
        files_scanned: int = 0,
        detailed_findings: Optional[List[Dict]] = None
    ) -> bool:
        """Send notification when a scan completes"""
        try:
            notification_data = {
                "type": NotificationType.SCAN_COMPLETED,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "findings_count": findings_count,
                "critical_count": critical_count,
                "high_count": high_count,
                "timestamp": utc_now().isoformat(),
                "message": f"Security scan completed for project '{project_name}' - {findings_count} findings ({critical_count} critical, {high_count} high)"
            }
            
            logger.info(f"✅ Scan completed notification: {notification_data}")
            
            # Generate report attachment HTML
            report_html = None
            if detailed_findings:
                try:
                    from services.notifications.templates.security_templates import get_scan_report_attachment_template
                    from jinja2 import Environment, BaseLoader
                    from datetime import datetime
                    
                    tmpl_source = get_scan_report_attachment_template()
                    loader = BaseLoader()
                    env = Environment(loader=loader)
                    # Manually parse and render since we have the source
                    from jinja2 import Template
                    tmpl = Template(tmpl_source)
                    
                    severity_rows = ""
                    severity_order = [("critical", "Critical", "#ef4444"), ("high", "High", "#f97316"), ("medium", "Medium", "#eab308"), ("low", "Low", "#22c55e"), ("info", "Info", "#3b82f6")]
                    sev_counts = {"critical": critical_count, "high": high_count, "medium": medium_count, "low": low_count, "info": 0}
                    
                    severity_rows = '<div style="display: table; width: 100%; margin: 24px 0;">'
                    severity_rows += '<div style="display: table-row;">'
                    for key, label, color in severity_order:
                        count = sev_counts.get(key, 0)
                        severity_rows += f'''
                        <div style="display: table-cell; width: 20%; padding: 8px;">
                            <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
                                <div style="font-size: 28px; font-weight: 700; color: {color};">{count}</div>
                                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">{label}</div>
                            </div>
                        </div>'''
                    severity_rows += '</div></div>'
                    
                    total_scanners = len(set(f.get("scanner", "unknown") for f in detailed_findings)) if detailed_findings else 0
                    
                    findings_rows = ""
                    for idx, f in enumerate(detailed_findings[:50]):
                        sev = f.get("severity", "medium").lower()
                        sev_colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22c55e", "info": "#3b82f6"}
                        sc = sev_colors.get(sev, "#94a3b8")
                        findings_rows += f'''
                        <div style="padding: 16px; margin-bottom: 12px; background: rgba(255,255,255,0.03); border-radius: 12px; border-left: 4px solid {sc};">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #e2e8f0; font-size: 14px; font-weight: 600;">{f.get("title", "Unknown")}</span>
                                <span style="background: {sc}; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600;">{sev.upper()}</span>
                            </div>
                            <p style="color: #94a3b8; font-size: 13px; margin: 0 0 8px 0; line-height: 1.5;">{f.get("description", "")[:200]}</p>
                            <div style="font-size: 12px; color: #64748b;">
                                <span>Scanner: {f.get("scanner", "N/A")}</span>
                                {' | <span>File: ' + f.get("file_path", "") + '</span>' if f.get("file_path") else ''}
                            </div>
                        </div>'''
                    
                    if len(detailed_findings) > 50:
                        findings_rows += f'''<div style="text-align: center; padding: 16px; color: #64748b; font-size: 13px;">
                            ... and {len(detailed_findings) - 50} more findings
                        </div>'''
                    
                    report_html = tmpl.render(
                        project_name=project_name,
                        generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p UTC"),
                        total_findings=findings_count,
                        scanner_count=total_scanners,
                        severity_section=severity_rows,
                        findings_section=findings_rows
                    )
                except Exception as report_err:
                    logger.warning(f"Failed to generate report attachment: {report_err}")
            
            # Send email notification if enabled
            if NotificationChannel.EMAIL in self.enabled_channels:
                prefs = await self._get_user_notification_preferences(user_id)
                if prefs.get("email_scan_results", True):
                    email = await self._get_user_email(user_id)
                    if email:
                        try:
                            from services.notifications.service import email_service
                            attachments = None
                            if report_html:
                                attachments = [{"filename": f"scan_report_{scan_id[:8]}.html", "content": report_html.encode("utf-8"), "content_type": "text/html"}]
                            await email_service.send_scan_completed_email(
                                email=email,
                                project_name=project_name,
                                scan_type=scan_type,
                                critical_count=critical_count,
                                high_count=high_count,
                                medium_count=medium_count,
                                low_count=low_count,
                                duration=duration,
                                files_scanned=files_scanned,
                                report_id=scan_id,
                                attachments=attachments,
                                detailed_findings=detailed_findings
                            )
                            logger.info(f"📧 Scan completion email sent to {email}")
                        except Exception as email_error:
                            logger.warning(f"Failed to send scan email: {email_error}")
            
            # For critical findings, also send alert
            if critical_count > 0:
                await self.send_critical_vulnerability_alert(
                    project_name, scan_id, user_id, critical_count
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send scan completed notification: {e}")
            return False
    
    async def send_scan_failed(
        self, 
        project_name: str, 
        scan_id: str, 
        user_id: str,
        error_message: str = None
    ) -> bool:
        """Send notification when a scan fails"""
        try:
            notification_data = {
                "type": NotificationType.SCAN_FAILED,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "error_message": error_message,
                "timestamp": utc_now().isoformat(),
                "message": f"Security scan failed for project '{project_name}'"
            }
            
            logger.error(f"💥 Scan failed notification: {notification_data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send scan failed notification: {e}")
            return False
    
    async def send_critical_vulnerability_alert(
        self, 
        project_name: str, 
        scan_id: str, 
        user_id: str,
        critical_count: int,
        vulnerability_details: Dict[str, Any] = None
    ) -> bool:
        """Send alert for critical vulnerabilities"""
        try:
            notification_data = {
                "type": NotificationType.CRITICAL_VULNERABILITY,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "critical_count": critical_count,
                "timestamp": utc_now().isoformat(),
                "message": f"🚨 CRITICAL ALERT: {critical_count} critical vulnerabilities found in '{project_name}'"
            }
            
            logger.warning(f"🚨 Critical vulnerability alert: {notification_data}")
            
            # Send email alert for critical vulnerabilities
            if NotificationChannel.EMAIL in self.enabled_channels:
                prefs = await self._get_user_notification_preferences(user_id)
                if prefs.get("email_security_alerts", True):
                    email = await self._get_user_email(user_id)
                    if email:
                        try:
                            from services.notifications.service import email_service
                            details = vulnerability_details or {}
                            await email_service.send_security_alert_email(
                                email=email,
                                alert_title=f"{critical_count} Critical Vulnerabilities Detected",
                                alert_description=f"A security scan of '{project_name}' has identified {critical_count} critical vulnerabilities that require immediate attention.",
                                severity="critical",
                                project_name=project_name,
                                file_path=details.get("file_path", "Multiple files"),
                                vulnerability_type=details.get("type", "Various"),
                                cwe_id=details.get("cwe_id", "See full report"),
                                cvss_score=details.get("cvss_score", "9.0+"),
                                recommendation="Review the full scan report and prioritize fixing critical vulnerabilities immediately.",
                                alert_id=scan_id
                            )
                            logger.info(f"📧 Critical alert email sent to {email}")
                        except Exception as email_error:
                            logger.warning(f"Failed to send critical alert email: {email_error}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send critical vulnerability alert: {e}")
            return False
    
    async def send_ai_analysis_ready(
        self, 
        project_name: str, 
        scan_id: str, 
        user_id: str,
        analysis_summary: str = None
    ) -> bool:
        """Send notification when AI analysis is ready"""
        try:
            notification_data = {
                "type": NotificationType.AI_ANALYSIS_READY,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "analysis_summary": analysis_summary,
                "timestamp": utc_now().isoformat(),
                "message": f"🤖 AI analysis completed for project '{project_name}'"
            }
            
            logger.info(f"🤖 AI analysis ready notification: {notification_data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send AI analysis ready notification: {e}")
            return False
    
    async def send_compliance_violation(
        self, 
        project_name: str, 
        scan_id: str, 
        user_id: str,
        framework: str,
        violations: List[Dict[str, Any]]
    ) -> bool:
        """Send notification for compliance violations"""
        try:
            notification_data = {
                "type": NotificationType.COMPLIANCE_VIOLATION,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "framework": framework,
                "violations_count": len(violations),
                "violations": violations,
                "timestamp": utc_now().isoformat(),
                "message": f"⚖️ Compliance violations detected in '{project_name}' for {framework}"
            }
            
            logger.warning(f"⚖️ Compliance violation notification: {notification_data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send compliance violation notification: {e}")
            return False
    
    async def send_custom_notification(
        self,
        notification_type: str,
        user_id: str,
        message: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """Send a custom notification"""
        try:
            notification_data = {
                "type": notification_type,
                "user_id": user_id,
                "message": message,
                "data": data or {},
                "timestamp": utc_now().isoformat()
            }
            
            logger.info(f"📬 Custom notification: {notification_data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send custom notification: {e}")
            return False
    
    async def send_login_alert(
        self,
        user_id: str,
        login_time: str,
        location: str = "Unknown",
        device: str = "Unknown",
        browser: str = "Unknown",
        ip_address: str = "Unknown"
    ) -> bool:
        """Send new login alert notification"""
        try:
            notification_data = {
                "type": NotificationType.NEW_LOGIN,
                "user_id": user_id,
                "login_time": login_time,
                "location": location,
                "device": device,
                "browser": browser,
                "ip_address": ip_address,
                "timestamp": utc_now().isoformat(),
                "message": f"New login detected from {device} in {location}"
            }
            
            logger.info(f"🔐 Login alert notification: {notification_data}")
            
            # Send email alert for new login
            if NotificationChannel.EMAIL in self.enabled_channels:
                prefs = await self._get_user_notification_preferences(user_id)
                if prefs.get("email_security_alerts", True):
                    email = await self._get_user_email(user_id)
                    if email:
                        try:
                            from services.notifications.service import email_service
                            await email_service.send_login_alert_email(
                                email=email,
                                login_time=login_time,
                                location=location,
                                device=device,
                                browser=browser,
                                ip_address=ip_address
                            )
                            logger.info(f"📧 Login alert email sent to {email}")
                        except Exception as email_error:
                            logger.warning(f"Failed to send login alert email: {email_error}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send login alert: {e}")
            return False
    
    async def send_new_vulnerability_notification(
        self,
        user_id: str,
        vulnerability_title: str,
        severity: str,
        project_name: str,
        file_path: str,
        line_number: int = 0,
        description: str = "",
        fix_suggestion: str = "",
        vulnerability_id: str = None
    ) -> bool:
        """Send notification for new vulnerability found"""
        try:
            notification_data = {
                "type": NotificationType.HIGH_SEVERITY_ALERT if severity.lower() in ["critical", "high"] else "vulnerability_found",
                "user_id": user_id,
                "vulnerability_title": vulnerability_title,
                "severity": severity,
                "project_name": project_name,
                "file_path": file_path,
                "timestamp": utc_now().isoformat(),
                "message": f"New {severity} vulnerability: {vulnerability_title} in {project_name}"
            }
            
            logger.info(f"🔓 New vulnerability notification: {notification_data}")
            
            # Only send email for high/critical vulnerabilities
            if severity.lower() in ["critical", "high"]:
                if NotificationChannel.EMAIL in self.enabled_channels:
                    prefs = await self._get_user_notification_preferences(user_id)
                    if prefs.get("email_security_alerts", True):
                        email = await self._get_user_email(user_id)
                        if email:
                            try:
                                from services.notifications.service import email_service
                                await email_service.send_new_vulnerability_email(
                                    email=email,
                                    vulnerability_title=vulnerability_title,
                                    severity=severity,
                                    project_name=project_name,
                                    file_path=file_path,
                                    line_number=line_number,
                                    description=description,
                                    fix_suggestion=fix_suggestion,
                                    vulnerability_id=vulnerability_id
                                )
                                logger.info(f"📧 Vulnerability alert email sent to {email}")
                            except Exception as email_error:
                                logger.warning(f"Failed to send vulnerability email: {email_error}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send vulnerability notification: {e}")
            return False
    
    def configure_channels(self, channels: List[NotificationChannel]):
        """Configure enabled notification channels"""
        self.enabled_channels = channels
        logger.info(f"📬 Notification channels configured: {channels}")
    
    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a notification channel is enabled"""
        return channel in self.enabled_channels


# Global notification service instance
notification_service = NotificationService()
