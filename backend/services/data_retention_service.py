"""
Data Retention Policy Service
Automated data cleanup, configurable retention periods, and compliance-driven archiving
"""
import structlog
from datetime import datetime, timedelta

# Helper function to get timezone-aware UTC datetime (replaces deprecated utc_now())
def utc_now() -> datetime:
    return datetime.now(timezone.utc)
from typing import Dict, Any, List, Optional
from enum import Enum
from pymongo import ASCENDING, DESCENDING
import json
import gzip
import base64

logger = structlog.get_logger()


class RetentionPolicyType(str, Enum):
    SCAN_RESULTS = "scan_results"
    AUDIT_LOGS = "audit_logs"
    USER_SESSIONS = "user_sessions"
    NOTIFICATIONS = "notifications"
    TEMPORARY_FILES = "temporary_files"
    ARCHIVED_REPORTS = "archived_reports"
    COMPLIANCE_REPORTS = "compliance_reports"


class RetentionAction(str, Enum):
    DELETE = "delete"
    ARCHIVE = "archive"
    COMPRESS = "compress"
    ANONYMIZE = "anonymize"


class DataRetentionService:
    """Service for managing data retention policies and cleanup"""

    def __init__(self, db):
        self.db = db
        self.logger = logger.bind(service="data_retention")

        # Default retention periods (in days)
        self.default_retention_periods = {
            RetentionPolicyType.SCAN_RESULTS: 365,  # 1 year
            RetentionPolicyType.AUDIT_LOGS: 2555,  # 7 years (compliance requirement)
            RetentionPolicyType.USER_SESSIONS: 90,  # 3 months
            RetentionPolicyType.NOTIFICATIONS: 180,  # 6 months
            RetentionPolicyType.TEMPORARY_FILES: 7,  # 1 week
            RetentionPolicyType.ARCHIVED_REPORTS: 730,  # 2 years
            RetentionPolicyType.COMPLIANCE_REPORTS: 2555,  # 7 years
        }

    async def create_retention_policy(
        self,
        policy_type: RetentionPolicyType,
        retention_days: int,
        action: RetentionAction,
        enabled: bool = True,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a new data retention policy"""
        try:
            policy_id = f"retention_{policy_type.value}_{utc_now().timestamp()}"

            policy_data = {
                "policy_id": policy_id,
                "policy_type": policy_type.value,
                "retention_days": retention_days,
                "action": action.value,
                "enabled": enabled,
                "metadata": metadata or {},
                "created_at": utc_now(),
                "last_executed": None,
                "execution_count": 0,
                "items_processed": 0,
            }

            await self.db.retention_policies.insert_one(policy_data)

            self.logger.info(
                "retention_policy_created",
                policy_id=policy_id,
                policy_type=policy_type.value,
                retention_days=retention_days,
            )

            return {"success": True, "policy_id": policy_id, "policy": policy_data}

        except Exception as e:
            self.logger.error("create_retention_policy_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def execute_retention_policy(
        self, policy_id: str
    ) -> Dict[str, Any]:
        """Execute a specific retention policy"""
        try:
            policy = await self.db.retention_policies.find_one({"policy_id": policy_id})

            if not policy:
                return {"success": False, "error": "Policy not found"}

            if not policy.get("enabled", True):
                return {"success": False, "error": "Policy is disabled"}

            policy_type = RetentionPolicyType(policy["policy_type"])
            retention_days = policy["retention_days"]
            action = RetentionAction(policy["action"])

            cutoff_date = utc_now() - timedelta(days=retention_days)

            # Execute based on policy type
            if policy_type == RetentionPolicyType.SCAN_RESULTS:
                result = await self._cleanup_scan_results(cutoff_date, action)
            elif policy_type == RetentionPolicyType.AUDIT_LOGS:
                result = await self._cleanup_audit_logs(cutoff_date, action)
            elif policy_type == RetentionPolicyType.USER_SESSIONS:
                result = await self._cleanup_user_sessions(cutoff_date, action)
            elif policy_type == RetentionPolicyType.NOTIFICATIONS:
                result = await self._cleanup_notifications(cutoff_date, action)
            elif policy_type == RetentionPolicyType.TEMPORARY_FILES:
                result = await self._cleanup_temporary_files(cutoff_date, action)
            elif policy_type == RetentionPolicyType.ARCHIVED_REPORTS:
                result = await self._cleanup_archived_reports(cutoff_date, action)
            elif policy_type == RetentionPolicyType.COMPLIANCE_REPORTS:
                result = await self._cleanup_compliance_reports(cutoff_date, action)
            else:
                result = {"success": False, "error": "Unknown policy type"}

            # Update policy execution stats
            await self.db.retention_policies.update_one(
                {"policy_id": policy_id},
                {
                    "$set": {"last_executed": utc_now()},
                    "$inc": {
                        "execution_count": 1,
                        "items_processed": result.get("processed_count", 0),
                    },
                },
            )

            self.logger.info(
                "retention_policy_executed",
                policy_id=policy_id,
                processed=result.get("processed_count", 0),
            )

            return {
                "success": True,
                "policy_id": policy_id,
                "execution_result": result,
            }

        except Exception as e:
            self.logger.error("execute_retention_policy_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def execute_all_policies(self) -> Dict[str, Any]:
        """Execute all enabled retention policies"""
        try:
            policies = await self.db.retention_policies.find(
                {"enabled": True}
            ).to_list(length=None)

            results = []
            total_processed = 0

            for policy in policies:
                result = await self.execute_retention_policy(policy["policy_id"])
                results.append({
                    "policy_id": policy["policy_id"],
                    "policy_type": policy["policy_type"],
                    "result": result,
                })
                if result.get("success"):
                    total_processed += result.get("execution_result", {}).get("processed_count", 0)

            self.logger.info(
                "all_retention_policies_executed",
                policies_count=len(policies),
                total_processed=total_processed,
            )

            return {
                "success": True,
                "policies_executed": len(policies),
                "total_items_processed": total_processed,
                "results": results,
            }

        except Exception as e:
            self.logger.error("execute_all_policies_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def _cleanup_scan_results(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup old scan results"""
        try:
            query = {"created_at": {"$lt": cutoff_date}}

            if action == RetentionAction.DELETE:
                result = await self.db.scan_reports.delete_many(query)
                processed_count = result.deleted_count

            elif action == RetentionAction.ARCHIVE:
                # Move to archive collection
                scans = await self.db.scan_reports.find(query).to_list(length=None)
                if scans:
                    for scan in scans:
                        scan["archived_at"] = utc_now()
                    await self.db.archived_scan_reports.insert_many(scans)
                    result = await self.db.scan_reports.delete_many(query)
                    processed_count = result.deleted_count
                else:
                    processed_count = 0

            elif action == RetentionAction.COMPRESS:
                # Compress large scan data
                scans = await self.db.scan_reports.find(query).to_list(length=None)
                processed_count = 0
                for scan in scans:
                    if "findings" in scan and len(scan["findings"]) > 100:
                        compressed_data = self._compress_data(scan["findings"])
                        await self.db.scan_reports.update_one(
                            {"_id": scan["_id"]},
                            {
                                "$set": {
                                    "findings_compressed": compressed_data,
                                    "compressed": True,
                                },
                                "$unset": {"findings": ""},
                            },
                        )
                        processed_count += 1

            else:
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_scan_results_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    async def _cleanup_audit_logs(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup old audit logs (with compliance considerations)"""
        try:
            query = {"timestamp": {"$lt": cutoff_date}}

            if action == RetentionAction.ARCHIVE:
                # Archive old logs for compliance
                logs = await self.db.audit_logs.find(query).to_list(length=None)
                if logs:
                    # Compress and archive
                    compressed_logs = self._compress_data(logs)
                    archive_entry = {
                        "archive_id": f"audit_archive_{utc_now().timestamp()}",
                        "period_start": min(log["timestamp"] for log in logs),
                        "period_end": max(log["timestamp"] for log in logs),
                        "log_count": len(logs),
                        "compressed_data": compressed_logs,
                        "archived_at": utc_now(),
                    }
                    await self.db.archived_audit_logs.insert_one(archive_entry)
                    result = await self.db.audit_logs.delete_many(query)
                    processed_count = result.deleted_count
                else:
                    processed_count = 0

            elif action == RetentionAction.ANONYMIZE:
                # Anonymize sensitive data but keep logs
                result = await self.db.audit_logs.update_many(
                    query,
                    {
                        "$set": {
                            "user_id": "ANONYMIZED",
                            "ip_address": "ANONYMIZED",
                            "user_agent": "ANONYMIZED",
                            "anonymized_at": utc_now(),
                        }
                    },
                )
                processed_count = result.modified_count

            else:
                # Don't delete audit logs by default for compliance
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_audit_logs_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    async def _cleanup_user_sessions(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup old user sessions"""
        try:
            query = {"created_at": {"$lt": cutoff_date}, "active": False}

            if action == RetentionAction.DELETE:
                result = await self.db.user_sessions.delete_many(query)
                processed_count = result.deleted_count
            else:
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_user_sessions_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    async def _cleanup_notifications(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup old notifications"""
        try:
            query = {"created_at": {"$lt": cutoff_date}, "read": True}

            if action == RetentionAction.DELETE:
                result = await self.db.notifications.delete_many(query)
                processed_count = result.deleted_count
            else:
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_notifications_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    async def _cleanup_temporary_files(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup temporary files and data"""
        try:
            query = {"created_at": {"$lt": cutoff_date}, "temporary": True}

            if action == RetentionAction.DELETE:
                # Clean from various temporary collections
                collections = ["temp_scans", "temp_uploads", "temp_exports"]
                total_deleted = 0

                for collection_name in collections:
                    if collection_name in await self.db.list_collection_names():
                        collection = self.db[collection_name]
                        result = await collection.delete_many(query)
                        total_deleted += result.deleted_count

                processed_count = total_deleted
            else:
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_temporary_files_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    async def _cleanup_archived_reports(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup old archived reports"""
        try:
            query = {"archived_at": {"$lt": cutoff_date}}

            if action == RetentionAction.DELETE:
                result = await self.db.archived_scan_reports.delete_many(query)
                processed_count = result.deleted_count
            else:
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_archived_reports_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    async def _cleanup_compliance_reports(
        self, cutoff_date: datetime, action: RetentionAction
    ) -> Dict[str, Any]:
        """Cleanup old compliance reports (with regulatory considerations)"""
        try:
            query = {"generated_at": {"$lt": cutoff_date.isoformat()}}

            if action == RetentionAction.ARCHIVE:
                # Archive for regulatory compliance
                reports = await self.db.compliance_reports.find(query).to_list(length=None)
                if reports:
                    compressed_reports = self._compress_data(reports)
                    archive_entry = {
                        "archive_id": f"compliance_archive_{utc_now().timestamp()}",
                        "report_count": len(reports),
                        "compressed_data": compressed_reports,
                        "archived_at": utc_now(),
                    }
                    await self.db.archived_compliance_reports.insert_one(archive_entry)
                    result = await self.db.compliance_reports.delete_many(query)
                    processed_count = result.deleted_count
                else:
                    processed_count = 0
            else:
                # Don't delete compliance reports by default
                processed_count = 0

            return {"success": True, "processed_count": processed_count}

        except Exception as e:
            self.logger.error("cleanup_compliance_reports_failed", error=str(e))
            return {"success": False, "error": str(e), "processed_count": 0}

    def _compress_data(self, data: Any) -> str:
        """Compress data using gzip and encode as base64"""
        try:
            json_data = json.dumps(data, default=str)
            compressed = gzip.compress(json_data.encode())
            return base64.b64encode(compressed).decode()
        except Exception as e:
            self.logger.error("data_compression_failed", error=str(e))
            return ""

    def _decompress_data(self, compressed_data: str) -> Any:
        """Decompress base64 encoded gzipped data"""
        try:
            compressed = base64.b64decode(compressed_data.encode())
            decompressed = gzip.decompress(compressed)
            return json.loads(decompressed.decode())
        except Exception as e:
            self.logger.error("data_decompression_failed", error=str(e))
            return None

    async def get_retention_statistics(self) -> Dict[str, Any]:
        """Get statistics about data retention and storage usage"""
        try:
            stats = {
                "timestamp": utc_now().isoformat(),
                "collections": {},
                "total_documents": 0,
                "policies": {
                    "total": 0,
                    "enabled": 0,
                    "disabled": 0,
                },
            }

            # Collection statistics
            collections = [
                "scan_reports",
                "audit_logs",
                "notifications",
                "user_sessions",
                "archived_scan_reports",
                "archived_audit_logs",
                "compliance_reports",
            ]

            for collection_name in collections:
                if collection_name in await self.db.list_collection_names():
                    collection = self.db[collection_name]
                    count = await collection.count_documents({})
                    stats["collections"][collection_name] = count
                    stats["total_documents"] += count

            # Policy statistics
            policies = await self.db.retention_policies.find().to_list(length=None)
            stats["policies"]["total"] = len(policies)
            stats["policies"]["enabled"] = len([p for p in policies if p.get("enabled")])
            stats["policies"]["disabled"] = len([p for p in policies if not p.get("enabled")])

            return {"success": True, "statistics": stats}

        except Exception as e:
            self.logger.error("get_retention_statistics_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def initialize_default_policies(self) -> Dict[str, Any]:
        """Initialize default retention policies"""
        try:
            created_policies = []

            for policy_type, retention_days in self.default_retention_periods.items():
                # Check if policy already exists
                existing = await self.db.retention_policies.find_one(
                    {"policy_type": policy_type.value}
                )

                if not existing:
                    # Determine default action
                    if policy_type in [
                        RetentionPolicyType.AUDIT_LOGS,
                        RetentionPolicyType.COMPLIANCE_REPORTS,
                    ]:
                        action = RetentionAction.ARCHIVE
                    elif policy_type == RetentionPolicyType.TEMPORARY_FILES:
                        action = RetentionAction.DELETE
                    else:
                        action = RetentionAction.ARCHIVE

                    result = await self.create_retention_policy(
                        policy_type=policy_type,
                        retention_days=retention_days,
                        action=action,
                        enabled=True,
                        metadata={"default_policy": True},
                    )

                    if result.get("success"):
                        created_policies.append(result["policy_id"])

            self.logger.info(
                "default_policies_initialized", count=len(created_policies)
            )

            return {
                "success": True,
                "created_policies": created_policies,
                "count": len(created_policies),
            }

        except Exception as e:
            self.logger.error("initialize_default_policies_failed", error=str(e))
            return {"success": False, "error": str(e)}


# Singleton instance
_retention_service_instance = None


def get_retention_service(db) -> DataRetentionService:
    """Get or create data retention service instance"""
    global _retention_service_instance
    if _retention_service_instance is None:
        _retention_service_instance = DataRetentionService(db)
    return _retention_service_instance

