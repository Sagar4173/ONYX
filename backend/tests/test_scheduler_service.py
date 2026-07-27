import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.base import ScanType


def _make_mock_schedule(id="test_id", name="Daily Scan", enabled=True):
    mock = MagicMock()
    mock.id = id
    mock.name = name
    mock.description = "Daily security scan"
    mock.project_id = None
    mock.target = "https://github.com/test/repo.git"
    mock.scan_types = [ScanType.SAST, ScanType.SECRETS]
    mock.cron_expression = "0 2 * * *"
    mock.timezone = "UTC"
    mock.enabled = enabled
    mock.created_by = "user123"
    mock.created_at = datetime.now(timezone.utc)
    mock.updated_at = datetime.now(timezone.utc)
    mock.last_run = None
    mock.last_status = None
    mock.next_run = None
    mock.config = {}
    mock.misfire_grace_time = 60
    mock.coalesce = True
    mock.max_instances = 1
    mock.insert = AsyncMock()
    mock.save = AsyncMock()
    mock.delete = AsyncMock()
    return mock


SERVICE_MODULE = "services.scheduling.scheduler_service"


@pytest.mark.asyncio
async def test_create_schedule():
    mock_schedule = _make_mock_schedule()
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        service.initialize()
        service._running = True
        service._add_job_for_schedule = MagicMock()

        result = await service.create_schedule(mock_schedule)

        assert result == mock_schedule
        mock_schedule.insert.assert_called_once()
        service._add_job_for_schedule.assert_called_once_with(mock_schedule)


@pytest.mark.asyncio
async def test_create_schedule_disabled():
    mock_schedule = _make_mock_schedule(enabled=False)
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        service.initialize()
        service._running = True
        service._add_job_for_schedule = MagicMock()

        result = await service.create_schedule(mock_schedule)

        assert result == mock_schedule
        mock_schedule.insert.assert_called_once()
        service._add_job_for_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_update_schedule():
    mock_schedule = _make_mock_schedule()
    schedule_id = "test_id"
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=mock_schedule)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        service.initialize()
        service._running = True
        service._remove_job = MagicMock()
        service._add_job_for_schedule = MagicMock()

        result = await service.update_schedule(schedule_id, {"name": "Updated Scan"})

        assert result is not None
        assert result.name == "Updated Scan"
        mock_schedule.save.assert_called_once()
        service._remove_job.assert_called_once_with(schedule_id)
        service._add_job_for_schedule.assert_called_once()


@pytest.mark.asyncio
async def test_update_schedule_not_found():
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=None)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.update_schedule("nonexistent", {"name": "Test"})

        assert result is None


@pytest.mark.asyncio
async def test_delete_schedule():
    mock_schedule = _make_mock_schedule()
    schedule_id = "test_id"
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=mock_schedule)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        service.initialize()
        service._remove_job = MagicMock()

        result = await service.delete_schedule(schedule_id)

        assert result is True
        mock_schedule.delete.assert_called_once()
        service._remove_job.assert_called_once_with(schedule_id)


@pytest.mark.asyncio
async def test_delete_schedule_not_found():
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=None)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.delete_schedule("nonexistent")

        assert result is False


@pytest.mark.asyncio
async def test_toggle_schedule():
    mock_schedule = _make_mock_schedule(enabled=True)
    schedule_id = "test_id"
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=mock_schedule)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        service.initialize()
        service._running = True
        service._remove_job = MagicMock()
        service._add_job_for_schedule = MagicMock()

        result = await service.toggle_schedule(schedule_id)

        assert result is not None
        assert result.enabled is False
        mock_schedule.save.assert_called_once()
        service._remove_job.assert_called_once_with(schedule_id)


@pytest.mark.asyncio
async def test_toggle_schedule_not_found():
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=None)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.toggle_schedule("nonexistent")

        assert result is None


@pytest.mark.asyncio
async def test_run_now():
    mock_schedule = _make_mock_schedule()
    schedule_id = "test_id"
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=mock_schedule)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        service._execute_scan = AsyncMock()

        result = await service.run_now(schedule_id)

        assert result is True
        service._execute_scan.assert_called_once_with(mock_schedule)


@pytest.mark.asyncio
async def test_run_now_not_found():
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=None)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.run_now("nonexistent")

        assert result is False


@pytest.mark.asyncio
async def test_get_schedule():
    mock_schedule = _make_mock_schedule()
    schedule_id = "test_id"
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        MockScanSchedule.get = AsyncMock(return_value=mock_schedule)
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.get_schedule(schedule_id)

        assert result == mock_schedule


@pytest.mark.asyncio
async def test_list_schedules():
    mock_schedule = _make_mock_schedule()
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        mock_find_all = MagicMock()
        mock_find_all.sort.return_value.to_list = AsyncMock(return_value=[mock_schedule])
        MockScanSchedule.find_all.return_value = mock_find_all
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.list_schedules()

        assert len(result) == 1
        assert result[0] == mock_schedule


@pytest.mark.asyncio
async def test_list_schedules_with_project():
    mock_schedule = _make_mock_schedule()
    with patch(f"{SERVICE_MODULE}.ScanSchedule") as MockScanSchedule:
        mock_find = MagicMock()
        mock_find.sort.return_value.to_list = AsyncMock(return_value=[mock_schedule])
        MockScanSchedule.find.return_value = mock_find
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.list_schedules(project_id="proj123")

        assert len(result) == 1


@pytest.mark.asyncio
async def test_execute_scan_no_orchestrator():
    mock_schedule = _make_mock_schedule()
    with (
        patch.object(mock_schedule, "save", AsyncMock()),
        patch("services.service_registry.ServiceRegistry.get_scan_orchestrator", return_value=None),
    ):
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        await service._execute_scan(mock_schedule)

        assert mock_schedule.last_status == "failed"


@pytest.mark.asyncio
async def test_execute_scan_orchestrator_error():
    mock_schedule = _make_mock_schedule()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run_scan = AsyncMock(side_effect=Exception("Scan failed"))
    mock_ws = MagicMock()
    mock_ws.notify_scan_started = AsyncMock()
    mock_ws.notify_scan_failed = AsyncMock()
    with (
        patch.object(mock_schedule, "save", AsyncMock()),
        patch("services.service_registry.ServiceRegistry.get_scan_orchestrator", return_value=mock_orchestrator),
        patch(f"{SERVICE_MODULE}.ws_manager", mock_ws),
    ):
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()
        await service._execute_scan(mock_schedule)

        assert mock_schedule.last_status == "failed"


@pytest.mark.asyncio
async def test_get_schedule_history():
    mock_report = MagicMock()
    mock_report.scan_id = "scan123"
    mock_report.status = "completed"
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.completed_at = datetime.now(timezone.utc)
    mock_report.total_findings = 5
    mock_report.findings_by_severity = {"critical": 1, "high": 2}
    mock_report.error_message = None

    with patch("models.report.ScanReport") as MockScanReport:
        MockScanReport.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(return_value=[mock_report])
        from services.scheduling.scheduler_service import ScanSchedulerService

        service = ScanSchedulerService()

        result = await service.get_schedule_history("test_id")

        assert len(result) == 1
        assert result[0]["scan_id"] == "scan123"
        assert result[0]["total_findings"] == 5


@pytest.mark.asyncio
async def test_add_remove_job():
    mock_schedule = _make_mock_schedule()
    from services.scheduling.scheduler_service import ScanSchedulerService

    service = ScanSchedulerService()
    service.initialize()
    service.scheduler.start()
    service._running = True

    service._add_job_for_schedule(mock_schedule)
    job = service.scheduler.get_job(str(mock_schedule.id))
    assert job is not None
    assert job.name == "Daily Scan"

    service._remove_job(str(mock_schedule.id))
    job = service.scheduler.get_job(str(mock_schedule.id))
    assert job is None

    service.scheduler.shutdown(wait=False)
