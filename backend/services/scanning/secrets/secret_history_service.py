import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.secret_history import SecretRecord, SecretTrendPoint
from models.report import ScanReport, ScannerType

logger = logging.getLogger(__name__)


class SecretHistoryService:
    async def update_from_scan(self, scan_report: ScanReport):
        try:
            secrets_found: List[Dict[str, Any]] = []
            for scan_result in scan_report.scan_results:
                if scan_result.scanner not in (
                    ScannerType.DETECT_SECRETS,
                    ScannerType.GITLEAKS,
                    ScannerType.SOPS,
                ):
                    continue
                for finding in scan_result.findings:
                    raw = finding.metadata or {}
                    secret_hash = raw.get("hashed_secret", "") or finding.id
                    secrets_found.append({
                        "secret_hash": secret_hash,
                        "file_path": finding.file_path,
                        "secret_type": raw.get("type", finding.rule_id),
                        "line_number": finding.line_start or 0,
                        "severity": finding.severity.value,
                        "scan_id": scan_report.scan_id,
                    })

            if not secrets_found:
                await self._resolve_unseen_secrets(scan_report.project_name, scan_report.scan_id)
                return

            seen_keys = set()
            for secret in secrets_found:
                key = (secret["secret_hash"], secret["file_path"])
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                await self._upsert_secret(secret, scan_report.project_name)

            await self._resolve_unseen_secrets(
                scan_report.project_name, scan_report.scan_id, seen_keys
            )

            await self._record_trend_point(scan_report.project_name)

        except Exception as e:
            logger.error("Failed to update secret history: %s", e)

    async def _upsert_secret(self, secret: Dict[str, Any], project_name: str):
        existing = await SecretRecord.find_one(
            SecretRecord.secret_hash == secret["secret_hash"],
            SecretRecord.file_path == secret["file_path"],
            SecretRecord.project_name == project_name,
        ).run()

        now = datetime.now(timezone.utc)

        if existing:
            existing.last_seen_at = now
            existing.appearance_count += 1
            existing.status = "active"
            existing.resolved_at = None
            if secret["scan_id"] not in existing.scan_ids:
                existing.scan_ids.append(secret["scan_id"])
            await existing.save()
        else:
            await SecretRecord(
                secret_hash=secret["secret_hash"],
                file_path=secret["file_path"],
                secret_type=secret["secret_type"],
                line_number=secret["line_number"],
                severity=secret["severity"],
                project_name=project_name,
                first_seen_at=now,
                last_seen_at=now,
                scan_ids=[secret["scan_id"]],
                appearance_count=1,
                status="active",
            ).save()

    async def _resolve_unseen_secrets(
        self,
        project_name: str,
        scan_id: str,
        seen_keys: Optional[set] = None,
    ):
        if seen_keys is None:
            seen_keys = set()

        cursor = SecretRecord.find(
            SecretRecord.project_name == project_name,
            SecretRecord.status == "active",
        )
        async for record in cursor:
            key = (record.secret_hash, record.file_path)
            if key not in seen_keys and scan_id not in record.scan_ids:
                record.status = "resolved"
                record.resolved_at = datetime.now(timezone.utc)
                await record.save()

    async def _record_trend_point(self, project_name: str):
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        existing = await SecretTrendPoint.find_one(
            SecretTrendPoint.project_name == project_name,
            SecretTrendPoint.date == today,
        ).run()

        total_active = await SecretRecord.find(
            SecretRecord.project_name == project_name,
            SecretRecord.status == "active",
        ).count()

        if existing:
            existing.total_active = total_active
            await existing.save()
        else:
            await SecretTrendPoint(
                project_name=project_name,
                date=today,
                total_active=total_active,
            ).save()

    async def get_secret_history(
        self,
        project_name: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = SecretRecord.find(SecretRecord.project_name == project_name)

        if status:
            query = query.find(SecretRecord.status == status)

        total = await query.count()
        records = (
            await query.sort(-SecretRecord.last_seen_at)
            .skip(offset)
            .limit(limit)
            .to_list()
        )

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "records": [
                {
                    "id": str(r.id),
                    "secret_hash": r.secret_hash[:16] + "...",
                    "file_path": r.file_path,
                    "secret_type": r.secret_type,
                    "line_number": r.line_number,
                    "severity": r.severity,
                    "project_name": r.project_name,
                    "first_seen_at": r.first_seen_at.isoformat(),
                    "last_seen_at": r.last_seen_at.isoformat(),
                    "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                    "appearance_count": r.appearance_count,
                    "status": r.status,
                }
                for r in records
            ],
        }

    async def get_trends(
        self,
        project_name: str,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        points = (
            await SecretTrendPoint.find(
                SecretTrendPoint.project_name == project_name,
            )
            .sort(-SecretTrendPoint.date)
            .limit(limit)
            .to_list()
        )

        result = []
        for i, point in enumerate(reversed(points)):
            new_count = 0
            resolved_count = 0
            if i > 0:
                prev = points[len(points) - i - 1]
                new_count = max(0, point.total_active - prev.total_active)
                resolved_count = max(0, prev.total_active - point.total_active)

            result.append({
                "date": point.date.isoformat(),
                "total_active": point.total_active,
                "new_secrets": new_count,
                "resolved_secrets": resolved_count,
            })

        return result

    async def update_status(self, record_id: str, status: str) -> bool:
        record = await SecretRecord.get(record_id)
        if not record:
            return False

        record.status = status
        if status in ("resolved", "dismissed"):
            record.resolved_at = datetime.now(timezone.utc)
        await record.save()
        return True

    async def get_summary(self, project_name: str) -> Dict[str, Any]:
        total = await SecretRecord.find(
            SecretRecord.project_name == project_name,
        ).count()
        active = await SecretRecord.find(
            SecretRecord.project_name == project_name,
            SecretRecord.status == "active",
        ).count()
        resolved = await SecretRecord.find(
            SecretRecord.project_name == project_name,
            SecretRecord.status == "resolved",
        ).count()
        dismissed = await SecretRecord.find(
            SecretRecord.project_name == project_name,
            SecretRecord.status == "dismissed",
        ).count()

        return {
            "total": total,
            "active": active,
            "resolved": resolved,
            "dismissed": dismissed,
        }
