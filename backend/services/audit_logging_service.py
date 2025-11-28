"""
Audit Logging Service
Comprehensive audit trail for user actions, system events, and compliance reporting
"""
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from pymongo import ASCENDING, DESCENDING
import hashlib
import json

logger = structlog.get_logger()


class AuditEventType(str, Enum):
    # User Management Events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_STATUS_CHANGED = "user_status_changed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    
    # Project Management Events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    PROJECT_ACCESSED = "project_accessed"
    PROJECT_MEMBER_ADDED = "project_member_added"
    PROJECT_MEMBER_REMOVED = "project_member_removed"
    PROJECT_PERMISSIONS_CHANGED = "project_permissions_changed"
    
    # Scan Events
    SCAN_INITIATED = "scan_initiated"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    SCAN_CANCELLED = "scan_cancelled"
    SCAN_RESULTS_VIEWED = "scan_results_viewed"
    SCAN_RESULTS_EXPORTED = "scan_results_exported"
    
    # Security Events
    VULNERABILITY_FOUND = "vulnerability_found"
    VULNERABILITY_FIXED = "vulnerability_fixed"
    VULNERABILITY_IGNORED = "vulnerability_ignored"
    SECURITY_POLICY_CREATED = "security_policy_created"
    SECURITY_POLICY_UPDATED = "security_policy_updated"
    SECURITY_POLICY_DELETED = "security_policy_deleted"
    SECURITY_RULE_CREATED = "security_rule_created"
    SECURITY_RULE_UPDATED = "security_rule_updated"
    SECURITY_RULE_DELETED = "security_rule_deleted"
    
    # Configuration Events
    CONFIG_UPDATED = "config_updated"
    INTEGRATION_CONFIGURED = "integration_configured"
    WEBHOOK_CONFIGURED = "webhook_configured"
    API_KEY_GENERATED = "api_key_generated"
    API_KEY_REVOKED = "api_key_revoked"
    
    # Access Events
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Data Events
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    DATA_DELETED = "data_deleted"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Compliance Events
    COMPLIANCE_REPORT_GENERATED = "compliance_report_generated"
    AUDIT_LOG_ACCESSED = "audit_log_accessed"
    POLICY_VIOLATION = "policy_violation"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLoggingService:
    """Service for comprehensive audit logging"""

    def __init__(self, db):
        self.db = db
        self.logger = logger.bind(service="audit_logging")

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        details: Dict[str, Any] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log an audit event"""
        try:
            timestamp = datetime.utcnow()
            event_id = f"audit_{timestamp.timestamp()}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"

            audit_entry = {
                "event_id": event_id,
                "event_type": event_type.value,
                "timestamp": timestamp,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "details": details or {},
                "severity": severity.value,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id,
                "indexed_at": timestamp,
            }

            # Calculate event hash for integrity verification
            event_hash = self._calculate_event_hash(audit_entry)
            audit_entry["event_hash"] = event_hash

            # Store in database
            await self.db.audit_logs.insert_one(audit_entry)

            self.logger.info(
                "audit_event_logged",
                event_id=event_id,
                event_type=event_type.value,
                user_id=user_id,
                resource_type=resource_type,
            )

            # Check for suspicious patterns
            if severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                await self._check_suspicious_activity(user_id, event_type)

            return {"success": True, "event_id": event_id}

        except Exception as e:
            self.logger.error("audit_logging_failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _calculate_event_hash(self, event: Dict[str, Any]) -> str:
        """Calculate hash of event for integrity verification"""
        # Create deterministic string representation
        hash_data = {
            "event_type": event["event_type"],
            "timestamp": event["timestamp"].isoformat(),
            "user_id": event["user_id"],
            "resource_type": event["resource_type"],
            "resource_id": event["resource_id"],
            "action": event["action"],
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    async def query_audit_logs(
        self,
        filters: Dict[str, Any] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Query audit logs with various filters"""
        try:
            query = {}

            # Date range filter
            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date

            # Event type filter
            if event_types:
                query["event_type"] = {"$in": [et.value for et in event_types]}

            # User filter
            if user_id:
                query["user_id"] = user_id

            # Resource type filter
            if resource_type:
                query["resource_type"] = resource_type

            # Severity filter
            if severity:
                query["severity"] = severity.value

            # Additional custom filters
            if filters:
                query.update(filters)

            # Execute query
            logs = await self.db.audit_logs.find(query).sort(
                "timestamp", DESCENDING
            ).skip(skip).limit(limit).to_list(length=limit)

            total = await self.db.audit_logs.count_documents(query)

            return {
                "success": True,
                "logs": logs,
                "total": total,
                "limit": limit,
                "skip": skip,
            }

        except Exception as e:
            self.logger.error("query_audit_logs_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_user_activity(
        self, user_id: str, days: int = 30, limit: int = 100
    ) -> Dict[str, Any]:
        """Get user activity history"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            logs = await self.db.audit_logs.find(
                {"user_id": user_id, "timestamp": {"$gte": start_date}}
            ).sort("timestamp", DESCENDING).limit(limit).to_list(length=limit)

            # Analyze activity patterns
            activity_summary = {
                "total_events": len(logs),
                "event_types": {},
                "severity_counts": {},
                "recent_events": logs[:10],
            }

            for log in logs:
                event_type = log["event_type"]
                severity = log["severity"]

                activity_summary["event_types"][event_type] = (
                    activity_summary["event_types"].get(event_type, 0) + 1
                )
                activity_summary["severity_counts"][severity] = (
                    activity_summary["severity_counts"].get(severity, 0) + 1
                )

            return {"success": True, "user_id": user_id, "activity": activity_summary}

        except Exception as e:
            self.logger.error("get_user_activity_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_resource_history(
        self, resource_type: str, resource_id: str, limit: int = 100
    ) -> Dict[str, Any]:
        """Get complete history of changes to a resource"""
        try:
            logs = await self.db.audit_logs.find(
                {"resource_type": resource_type, "resource_id": resource_id}
            ).sort("timestamp", DESCENDING).limit(limit).to_list(length=limit)

            return {
                "success": True,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "history": logs,
                "total_events": len(logs),
            }

        except Exception as e:
            self.logger.error("get_resource_history_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "full",
    ) -> Dict[str, Any]:
        """Generate compliance audit report"""
        try:
            # Query all relevant audit logs
            logs = await self.db.audit_logs.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            ).to_list(length=None)

            report = {
                "report_type": report_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_events": len(logs),
                    "unique_users": len(set(log["user_id"] for log in logs if log["user_id"])),
                    "event_types": {},
                    "severity_distribution": {},
                },
                "security_events": [],
                "access_events": [],
                "data_events": [],
                "policy_violations": [],
            }

            # Analyze logs
            for log in logs:
                event_type = log["event_type"]
                severity = log["severity"]

                # Count event types
                report["summary"]["event_types"][event_type] = (
                    report["summary"]["event_types"].get(event_type, 0) + 1
                )

                # Count severity
                report["summary"]["severity_distribution"][severity] = (
                    report["summary"]["severity_distribution"].get(severity, 0) + 1
                )

                # Categorize events
                if "security" in event_type or "vulnerability" in event_type:
                    report["security_events"].append(log)
                elif "access" in event_type or "login" in event_type:
                    report["access_events"].append(log)
                elif "data" in event_type or "export" in event_type:
                    report["data_events"].append(log)
                elif "violation" in event_type:
                    report["policy_violations"].append(log)

            # Store report
            await self.db.compliance_reports.insert_one(report)

            self.logger.info(
                "compliance_report_generated",
                start_date=start_date,
                end_date=end_date,
                total_events=len(logs),
            )

            return {"success": True, "report": report}

        except Exception as e:
            self.logger.error("generate_compliance_report_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def _check_suspicious_activity(
        self, user_id: Optional[str], event_type: AuditEventType
    ):
        """Check for patterns indicating suspicious activity"""
        try:
            if not user_id:
                return

            # Check for repeated failed login attempts
            if event_type == AuditEventType.USER_LOGIN_FAILED:
                recent_failures = await self.db.audit_logs.count_documents(
                    {
                        "user_id": user_id,
                        "event_type": AuditEventType.USER_LOGIN_FAILED.value,
                        "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=15)},
                    }
                )

                if recent_failures >= 5:
                    await self.log_event(
                        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                        user_id=user_id,
                        resource_type="authentication",
                        resource_id=None,
                        action="multiple_failed_logins",
                        details={"failed_attempts": recent_failures},
                        severity=AuditSeverity.CRITICAL,
                    )

            # Check for unusual access patterns
            elif event_type == AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT:
                recent_attempts = await self.db.audit_logs.count_documents(
                    {
                        "user_id": user_id,
                        "event_type": AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT.value,
                        "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)},
                    }
                )

                if recent_attempts >= 3:
                    await self.log_event(
                        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                        user_id=user_id,
                        resource_type="access_control",
                        resource_id=None,
                        action="repeated_unauthorized_access",
                        details={"attempts": recent_attempts},
                        severity=AuditSeverity.CRITICAL,
                    )

        except Exception as e:
            self.logger.error("suspicious_activity_check_failed", error=str(e))

    async def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json",
    ) -> Dict[str, Any]:
        """Export audit logs for archival or external analysis"""
        try:
            logs = await self.db.audit_logs.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            ).sort("timestamp", ASCENDING).to_list(length=None)

            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "total_records": len(logs),
                "logs": logs,
            }

            # Log the export action
            await self.log_event(
                event_type=AuditEventType.AUDIT_LOG_ACCESSED,
                user_id=None,  # System action
                resource_type="audit_logs",
                resource_id=None,
                action="export",
                details={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "record_count": len(logs),
                },
                severity=AuditSeverity.INFO,
            )

            return {"success": True, "export_data": export_data, "format": format}

        except Exception as e:
            self.logger.error("export_audit_logs_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def verify_log_integrity(
        self, event_id: str
    ) -> Dict[str, Any]:
        """Verify the integrity of an audit log entry"""
        try:
            log = await self.db.audit_logs.find_one({"event_id": event_id})
            
            if not log:
                return {"success": False, "error": "Log entry not found"}

            stored_hash = log.get("event_hash")
            calculated_hash = self._calculate_event_hash(log)

            is_valid = stored_hash == calculated_hash

            return {
                "success": True,
                "event_id": event_id,
                "integrity_valid": is_valid,
                "stored_hash": stored_hash,
                "calculated_hash": calculated_hash,
            }

        except Exception as e:
            self.logger.error("verify_log_integrity_failed", error=str(e))
            return {"success": False, "error": str(e)}


# Singleton instance
_audit_service_instance = None


def get_audit_service(db) -> AuditLoggingService:
    """Get or create audit logging service instance"""
    global _audit_service_instance
    if _audit_service_instance is None:
        _audit_service_instance = AuditLoggingService(db)
    return _audit_service_instance
