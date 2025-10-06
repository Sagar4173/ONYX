"""
Notification Service for Security Scanning Platform
Handles sending notifications for scan events and security alerts
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

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


class NotificationChannel(str, Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationService:
    """Service for handling notifications and alerts"""
    
    def __init__(self):
        self.enabled_channels = [NotificationChannel.IN_APP]  # Default to in-app only
        
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
                "timestamp": datetime.utcnow().isoformat(),
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
        high_count: int = 0
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
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Security scan completed for project '{project_name}' - {findings_count} findings ({critical_count} critical, {high_count} high)"
            }
            
            logger.info(f"✅ Scan completed notification: {notification_data}")
            
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
                "timestamp": datetime.utcnow().isoformat(),
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
        critical_count: int
    ) -> bool:
        """Send alert for critical vulnerabilities"""
        try:
            notification_data = {
                "type": NotificationType.CRITICAL_VULNERABILITY,
                "project_name": project_name,
                "scan_id": scan_id,
                "user_id": user_id,
                "critical_count": critical_count,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"🚨 CRITICAL ALERT: {critical_count} critical vulnerabilities found in '{project_name}'"
            }
            
            logger.warning(f"🚨 Critical vulnerability alert: {notification_data}")
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
                "timestamp": datetime.utcnow().isoformat(),
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
                "timestamp": datetime.utcnow().isoformat(),
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
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"📬 Custom notification: {notification_data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send custom notification: {e}")
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
