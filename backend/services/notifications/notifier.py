"""
Notification service for sending alerts via Slack, Teams, and other channels
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx
from slack_sdk.webhook.async_client import AsyncWebhookClient

from models.report import ScanReport, AIAnalysis, NotificationStatus
from config import settings

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification channels"""
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"


class NotificationError(Exception):
    """Custom exception for notification errors"""
    pass


class NotificationService:
    """Service for sending security scan notifications"""
    
    def __init__(self):
        self.slack_client = None
        self.teams_webhook_url = settings.teams_webhook_url
        
        if settings.slack_webhook_url:
            self.slack_client = AsyncWebhookClient(settings.slack_webhook_url)
    
    async def send_scan_notification(
        self,
        scan_report: ScanReport,
        channels: Optional[List[NotificationChannel]] = None
    ) -> NotificationStatus:
        """
        Send scan completion notification to specified channels
        
        Args:
            scan_report: Completed scan report
            channels: List of notification channels (if None, send to all configured)
            
        Returns:
            Notification status with delivery results
        """
        if channels is None:
            channels = self._get_configured_channels()
        
        logger.info(f"Sending scan notifications to {len(channels)} channels")
        
        notification_status = NotificationStatus()
        
        # Send notifications concurrently
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.SLACK and self.slack_client:
                task = self._send_slack_notification(scan_report, notification_status)
                tasks.append(task)
            elif channel == NotificationChannel.TEAMS and self.teams_webhook_url:
                task = self._send_teams_notification(scan_report, notification_status)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return notification_status
    
    def _get_configured_channels(self) -> List[NotificationChannel]:
        """Get list of configured notification channels"""
        channels = []
        
        if settings.slack_webhook_url:
            channels.append(NotificationChannel.SLACK)
        
        if settings.teams_webhook_url:
            channels.append(NotificationChannel.TEAMS)
        
        return channels
    
    async def _send_slack_notification(
        self,
        scan_report: ScanReport,
        notification_status: NotificationStatus
    ):
        """Send notification to Slack"""
        try:
            logger.info("Sending Slack notification")
            
            message = self._create_slack_message(scan_report)
            
            response = await self.slack_client.send(
                text=message['text'],
                blocks=message.get('blocks', []),
                attachments=message.get('attachments', [])
            )
            
            if response.status_code == 200:
                notification_status.slack_sent = True
                notification_status.slack_timestamp = datetime.now(timezone.utc)
                logger.info("Slack notification sent successfully")
            else:
                error_msg = f"Slack API error: {response.status_code}"
                notification_status.errors.append(error_msg)
                logger.error(error_msg)
                
        except Exception as e:
            error_msg = f"Slack notification failed: {e}"
            notification_status.errors.append(error_msg)
            logger.error(error_msg)
    
    async def _send_teams_notification(
        self,
        scan_report: ScanReport,
        notification_status: NotificationStatus
    ):
        """Send notification to Microsoft Teams"""
        try:
            logger.info("Sending Teams notification")
            
            message = self._create_teams_message(scan_report)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.teams_webhook_url,
                    json=message,
                    headers={'Content-Type': 'application/json'},
                    timeout=30.0
                )
            
            if response.status_code == 200:
                notification_status.teams_sent = True
                notification_status.teams_timestamp = datetime.now(timezone.utc)
                logger.info("Teams notification sent successfully")
            else:
                error_msg = f"Teams API error: {response.status_code} - {response.text}"
                notification_status.errors.append(error_msg)
                logger.error(error_msg)
                
        except Exception as e:
            error_msg = f"Teams notification failed: {e}"
            notification_status.errors.append(error_msg)
            logger.error(error_msg)
    
    def _create_slack_message(self, scan_report: ScanReport) -> Dict[str, Any]:
        """Create Slack message format"""
        # Determine alert color based on severity
        color = self._get_alert_color(scan_report.findings_by_severity)
        
        # Create main message
        text = f"🔒 Security Scan Completed for {scan_report.project_name}"
        
        # Create rich blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔒 Security Scan Report - {scan_report.project_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:* {scan_report.git_metadata.repository_url}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:* {scan_report.git_metadata.branch}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Commit:* {scan_report.git_metadata.commit_hash[:8]}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:* {scan_report.status.value.title()}"
                    }
                ]
            }
        ]
        
        # Add findings summary
        if scan_report.total_findings > 0:
            findings_text = self._format_findings_summary(scan_report.findings_by_severity)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Findings Summary:*\n{findings_text}"
                }
            })
            
            # Add AI analysis summary if available
            if scan_report.ai_analysis:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Risk Assessment:*\n{scan_report.ai_analysis.risk_assessment[:200]}..."
                    }
                })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ *No security vulnerabilities detected!*"
                }
            })
        
        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Scan completed at {scan_report.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })
        
        return {
            "text": text,
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Total Findings",
                            "value": str(scan_report.total_findings),
                            "short": True
                        },
                        {
                            "title": "Duration",
                            "value": f"{scan_report.duration_seconds:.1f}s" if scan_report.duration_seconds else "N/A",
                            "short": True
                        }
                    ]
                }
            ]
        }
    
    def _create_teams_message(self, scan_report: ScanReport) -> Dict[str, Any]:
        """Create Microsoft Teams message format"""
        # Determine theme color
        theme_color = self._get_teams_color(scan_report.findings_by_severity)
        
        # Create sections
        sections = [
            {
                "activityTitle": f"Security Scan Completed - {scan_report.project_name}",
                "activitySubtitle": f"Repository: {scan_report.git_metadata.repository_url}",
                "activityImage": "https://raw.githubusercontent.com/github/explore/main/topics/security/security.png",
                "facts": [
                    {
                        "name": "Branch",
                        "value": scan_report.git_metadata.branch
                    },
                    {
                        "name": "Commit",
                        "value": scan_report.git_metadata.commit_hash[:12]
                    },
                    {
                        "name": "Status",
                        "value": scan_report.status.value.title()
                    },
                    {
                        "name": "Total Findings",
                        "value": str(scan_report.total_findings)
                    },
                    {
                        "name": "Scan Duration",
                        "value": f"{scan_report.duration_seconds:.1f}s" if scan_report.duration_seconds else "N/A"
                    }
                ]
            }
        ]
        
        # Add findings breakdown
        if scan_report.total_findings > 0:
            findings_text = self._format_findings_summary(scan_report.findings_by_severity)
            sections.append({
                "activityTitle": "Findings Summary",
                "text": findings_text
            })
            
            # Add AI analysis if available
            if scan_report.ai_analysis and scan_report.ai_analysis.executive_summary:
                sections.append({
                    "activityTitle": "AI Analysis Summary",
                    "text": scan_report.ai_analysis.executive_summary[:500] + "..." if len(scan_report.ai_analysis.executive_summary) > 500 else scan_report.ai_analysis.executive_summary
                })
        else:
            sections.append({
                "activityTitle": "Result",
                "text": "✅ No security vulnerabilities detected!"
            })
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"Security scan completed for {scan_report.project_name}",
            "sections": sections
        }
    
    def _format_findings_summary(self, findings_by_severity: Dict[str, int]) -> str:
        """Format findings summary text"""
        if not any(findings_by_severity.values()):
            return "No vulnerabilities found"
        
        summary_parts = []
        severity_emojis = {
            "critical": "🔴",
            "high": "🟠", 
            "medium": "🟡",
            "low": "🔵",
            "info": "⚪"
        }
        
        for severity, count in findings_by_severity.items():
            if count > 0:
                emoji = severity_emojis.get(severity, "⚫")
                summary_parts.append(f"{emoji} {severity.title()}: {count}")
        
        return "\n".join(summary_parts)
    
    def _get_alert_color(self, findings_by_severity: Dict[str, int]) -> str:
        """Get Slack attachment color based on findings severity"""
        if findings_by_severity.get("critical", 0) > 0:
            return "danger"  # Red
        elif findings_by_severity.get("high", 0) > 0:
            return "warning"  # Orange
        elif findings_by_severity.get("medium", 0) > 0:
            return "#ffdd44"  # Yellow
        elif any(findings_by_severity.values()):
            return "good"  # Green
        else:
            return "good"  # Green for clean scan
    
    def _get_teams_color(self, findings_by_severity: Dict[str, int]) -> str:
        """Get Teams theme color based on findings severity"""
        if findings_by_severity.get("critical", 0) > 0:
            return "FF0000"  # Red
        elif findings_by_severity.get("high", 0) > 0:
            return "FF8C00"  # Orange
        elif findings_by_severity.get("medium", 0) > 0:
            return "FFD700"  # Gold
        elif any(findings_by_severity.values()):
            return "32CD32"  # Green
        else:
            return "32CD32"  # Green for clean scan
    
    async def send_test_notification(
        self,
        channels: Optional[List[NotificationChannel]] = None
    ) -> NotificationStatus:
        """Send test notification to verify configuration"""
        if channels is None:
            channels = self._get_configured_channels()
        
        logger.info("Sending test notifications")
        
        notification_status = NotificationStatus()
        test_message = {
            "text": "🔒 ONYX Platform Test Notification",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "This is a test notification from the ONYX Platform. Your notification configuration is working correctly!"
                    }
                }
            ]
        }
        
        # Send test notifications
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.SLACK and self.slack_client:
                task = self._send_test_slack(test_message, notification_status)
                tasks.append(task)
            elif channel == NotificationChannel.TEAMS and self.teams_webhook_url:
                task = self._send_test_teams(test_message, notification_status)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return notification_status
    
    async def _send_test_slack(self, message: Dict, notification_status: NotificationStatus):
        """Send test Slack notification"""
        try:
            response = await self.slack_client.send(**message)
            if response.status_code == 200:
                notification_status.slack_sent = True
                notification_status.slack_timestamp = datetime.now(timezone.utc)
        except Exception as e:
            notification_status.errors.append(f"Slack test failed: {e}")
    
    async def _send_test_teams(self, message: Dict, notification_status: NotificationStatus):
        """Send test Teams notification"""
        try:
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "32CD32",
                "summary": "ONYX Platform Test",
                "sections": [
                    {
                        "activityTitle": "🔒 ONYX Platform Test Notification",
                        "text": "This is a test notification from the ONYX Platform. Your notification configuration is working correctly!"
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.teams_webhook_url,
                    json=teams_message,
                    headers={'Content-Type': 'application/json'},
                    timeout=30.0
                )
            
            if response.status_code == 200:
                notification_status.teams_sent = True
                notification_status.teams_timestamp = datetime.now(timezone.utc)
        except Exception as e:
            notification_status.errors.append(f"Teams test failed: {e}")

    async def send_email(self, to_email: str, subject: str, html_body: str):
        """
        Send email using the dedicated email service
        """
        try:
            from services.notifications.service import email_service
            return await email_service.send_email(to_email, subject, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise NotificationError(f"Email sending failed: {str(e)}")


# Global notification service instance
notification_service = NotificationService()
