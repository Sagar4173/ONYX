import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from models.schedule import ScanSchedule
from services.notifications.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


def _validate_cron(expression: str) -> None:
    """Raise ValueError if the cron expression cannot be parsed by APScheduler."""
    try:
        CronTrigger.from_crontab(expression)
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {e}")


class ScanSchedulerService:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False

    def initialize(self):
        if self.scheduler is not None:
            return
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        logger.info("ScanSchedulerService initialized")

    async def start(self):
        if self._running:
            return
        if self.scheduler is None:
            self.initialize()

        from database import db_manager

        if db_manager.db is not None:
            try:
                jobstore = MongoDBJobStore(
                    database=db_manager.db,
                    collection="apscheduler_jobs",
                    client=db_manager.client,
                )
                self.scheduler.add_jobstore(jobstore, "default")
                logger.info("MongoDBJobStore connected for APScheduler")
            except Exception as e:
                logger.warning(f"Could not connect MongoDBJobStore, using in-memory: {e}")

        self.scheduler.start()
        self._running = True

        enabled_schedules = await ScanSchedule.find(ScanSchedule.enabled == True).to_list()
        loaded = 0
        for schedule in enabled_schedules:
            try:
                self._add_job_for_schedule(schedule)
                loaded += 1
            except Exception as e:
                logger.warning(f"Failed to schedule job for {schedule.name} ({schedule.id}): {e}")
        logger.info(f"ScanSchedulerService started with {loaded} scheduled jobs")

    async def stop(self):
        if self.scheduler and self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("ScanSchedulerService stopped")

    async def create_schedule(self, schedule: ScanSchedule) -> ScanSchedule:
        # Reject invalid cron before persisting anything (job registration
        # would otherwise fail later with a generic 500).
        _validate_cron(schedule.cron_expression)
        await schedule.insert()
        if schedule.enabled and self._running:
            self._add_job_for_schedule(schedule)
        return schedule

    async def update_schedule(self, schedule_id: str, update_data: dict) -> Optional[ScanSchedule]:
        schedule = await ScanSchedule.get(schedule_id)
        if not schedule:
            return None

        if update_data.get("cron_expression"):
            _validate_cron(update_data["cron_expression"])

        for key, value in update_data.items():
            if value is not None and hasattr(schedule, key):
                setattr(schedule, key, value)
        schedule.updated_at = datetime.now(timezone.utc)
        await schedule.save()

        self._remove_job(schedule_id)
        if schedule.enabled and self._running:
            self._add_job_for_schedule(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        schedule = await ScanSchedule.get(schedule_id)
        if not schedule:
            return False
        self._remove_job(schedule_id)
        await schedule.delete()
        return True

    async def toggle_schedule(self, schedule_id: str) -> Optional[ScanSchedule]:
        schedule = await ScanSchedule.get(schedule_id)
        if not schedule:
            return None
        schedule.enabled = not schedule.enabled
        schedule.updated_at = datetime.now(timezone.utc)
        await schedule.save()

        self._remove_job(schedule_id)
        if schedule.enabled and self._running:
            self._add_job_for_schedule(schedule)
        return schedule

    async def run_now(self, schedule_id: str) -> bool:
        schedule = await ScanSchedule.get(schedule_id)
        if not schedule:
            return False
        asyncio.create_task(self._execute_scan(schedule))
        return True

    async def get_schedule(self, schedule_id: str) -> Optional[ScanSchedule]:
        return await ScanSchedule.get(schedule_id)

    async def list_schedules(self, project_id: Optional[str] = None) -> List[ScanSchedule]:
        if project_id:
            return await ScanSchedule.find(
                ScanSchedule.project_id == project_id
            ).sort(-ScanSchedule.created_at).to_list()
        return await ScanSchedule.find_all().sort(-ScanSchedule.created_at).to_list()

    async def get_schedule_history(self, schedule_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        from models.report import ScanReport

        reports = await ScanReport.find(
            ScanReport.metadata.schedule_id == schedule_id
        ).sort(-ScanReport.created_at).limit(limit).to_list()

        return [
            {
                "scan_id": r.scan_id,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "total_findings": r.total_findings,
                "findings_by_severity": r.findings_by_severity,
                "error_message": getattr(r, "error_message", None),
            }
            for r in reports
        ]

    def _add_job_for_schedule(self, schedule: ScanSchedule):
        if self.scheduler is None:
            return
        job_id = str(schedule.id)
        trigger = CronTrigger.from_crontab(schedule.cron_expression, timezone=schedule.timezone)
        self.scheduler.add_job(
            self._execute_scan,
            trigger=trigger,
            args=[schedule],
            id=job_id,
            name=schedule.name,
            misfire_grace_time=schedule.misfire_grace_time,
            coalesce=schedule.coalesce,
            max_instances=schedule.max_instances,
            replace_existing=True,
        )
        next_job = self.scheduler.get_job(job_id)
        if next_job and next_job.next_run_time:
            asyncio.create_task(self._update_next_run(schedule.id, next_job.next_run_time))

    def _remove_job(self, schedule_id: str):
        if self.scheduler and self.scheduler.get_job(str(schedule_id)):
            self.scheduler.remove_job(str(schedule_id))

    async def _execute_scan(self, schedule: ScanSchedule):
        logger.info(f"Executing scheduled scan: {schedule.name} ({schedule.id})")
        schedule.last_status = "running"
        schedule.last_run = datetime.now(timezone.utc)
        await schedule.save()

        from services.service_registry import ServiceRegistry

        orchestrator = ServiceRegistry.get_scan_orchestrator()
        if not orchestrator:
            logger.error("Scan orchestrator not available for scheduled scan")
            schedule.last_status = "failed"
            await schedule.save()
            return

        from services.scanning.engine.orchestrator import ScanRequest as OrchestratorScanRequest

        scan_request = OrchestratorScanRequest(
            target=schedule.target,
            scan_types=schedule.scan_types,
        )

        try:
            await ws_manager.notify_scan_started(str(schedule.id), schedule.name)

            result = await orchestrator.run_scan(scan_request)

            from models.report import ScanReport
            report = await ScanReport.find_one(ScanReport.scan_id == result.scan_id)
            if report:
                from models.report import ScanStatus
                if report.status == ScanStatus.COMPLETED:
                    schedule.last_status = "success"
                elif report.status == ScanStatus.FAILED:
                    schedule.last_status = "failed"
                else:
                    schedule.last_status = "completed"

                if not report.metadata:
                    report.metadata = {}
                report.metadata["schedule_id"] = str(schedule.id)
                report.metadata["schedule_name"] = schedule.name
                await report.save()

                await ws_manager.notify_scan_completed(
                    str(schedule.id), schedule.name,
                    report.total_findings or 0,
                    report.findings_by_severity or {},
                )
            else:
                schedule.last_status = "completed"
                await ws_manager.notify_scan_completed(
                    str(schedule.id), schedule.name, 0, {}
                )

            schedule.last_run = datetime.now(timezone.utc)
            await schedule.save()
            logger.info(f"Scheduled scan completed: {schedule.name}")
        except Exception as e:
            logger.error(f"Scheduled scan failed: {schedule.name} - {e}")
            schedule.last_status = "failed"
            schedule.last_run = datetime.now(timezone.utc)
            await schedule.save()

            await ws_manager.notify_scan_failed(str(schedule.id), schedule.name, str(e))

    async def _update_next_run(self, schedule_id, next_run_time):
        schedule = await ScanSchedule.get(schedule_id)
        if schedule:
            schedule.next_run = next_run_time
            await schedule.save()
