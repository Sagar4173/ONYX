from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId

from models.report import GitMetadata, ScanReport, ScanStatus, WebhookEvent
from routes.webhook.processor import WebhookProcessor

REPORT_ID = ObjectId("6a6f6177f12a0f77b5f73d9a")


def _git_metadata():
    return GitMetadata(
        repository_url="https://github.com/test/repo.git",
        branch="main",
        commit_hash="abc123",
        event_type="push",
    )


def _webhook_event():
    return WebhookEvent.model_construct(
        event_id="evt-test-1",
        event_type="push",
        repository_url="https://github.com/test/repo.git",
        status="received",
    )


def _project_mock():
    project_cls = MagicMock()
    project_cls.find_one = AsyncMock(return_value=None)
    return project_cls


def _scan_report_factory(created: List[ScanReport], naive_started_at: bool = False):
    def factory(**kwargs):
        report = ScanReport.model_construct(
            project_name=kwargs["project_name"],
            scan_id=kwargs["scan_id"],
            git_metadata=kwargs["git_metadata"],
            status=ScanStatus.PENDING,
        )
        report.id = REPORT_ID
        report.started_at = (
            datetime(2026, 8, 2, 10, 0, 0)
            if naive_started_at
            else None
        )
        created.append(report)
        return report

    return factory


class TestProcessScanWorkflow:
    """Webhook-triggered scans must persist a string scan_report_id.

    Regression: an ObjectId was assigned to the str-typed field, which made
    every WebhookEvent.save() re-validate and fail, breaking the workflow.
    """

    async def test_scan_report_id_stored_as_string(self):
        processor = WebhookProcessor()
        webhook_event = _webhook_event()
        created: List[ScanReport] = []

        with (
            patch("models.project.Project", new=_project_mock()),
            patch("routes.webhook.processor.ScanReport", new=_scan_report_factory(created)),
            patch.object(ScanReport, "insert", new_callable=AsyncMock, create=True),
            patch.object(ScanReport, "save", new_callable=AsyncMock, create=True),
            patch.object(WebhookEvent, "save", new_callable=AsyncMock, create=True) as event_save,
            patch(
                "routes.webhook.processor.repo_cloner.clone_repository",
                new_callable=AsyncMock,
            ) as clone,
            patch(
                "routes.webhook.processor.enhanced_workflow.execute_comprehensive_scan",
                new_callable=AsyncMock,
            ),
            patch("routes.webhook.processor.settings.cleanup_after_scan", False),
        ):
            clone.return_value = {"local_path": "/tmp/test-repo"}

            await processor._process_scan_workflow(webhook_event, _git_metadata())

        assert created, "workflow did not create a scan report"
        assert isinstance(webhook_event.scan_report_id, str)
        assert webhook_event.scan_report_id == str(REPORT_ID)
        assert webhook_event.status == "processing"
        event_save.assert_awaited()

    async def test_failed_clone_records_event_and_fails_scan_report(self):
        processor = WebhookProcessor()
        webhook_event = _webhook_event()
        created: List[ScanReport] = []

        with (
            patch("models.project.Project", new=_project_mock()),
            patch(
                "routes.webhook.processor.ScanReport",
                new=_scan_report_factory(created, naive_started_at=True),
            ),
            patch.object(ScanReport, "insert", new_callable=AsyncMock, create=True),
            patch.object(ScanReport, "save", new_callable=AsyncMock, create=True) as report_save,
            patch.object(WebhookEvent, "save", new_callable=AsyncMock, create=True) as event_save,
            patch(
                "routes.webhook.processor.repo_cloner.clone_repository",
                new_callable=AsyncMock,
                side_effect=RuntimeError("clone failed"),
            ),
            patch("routes.webhook.processor.settings.cleanup_after_scan", False),
        ):
            await processor._process_scan_workflow(webhook_event, _git_metadata())

        assert created, "workflow did not create a scan report"
        assert webhook_event.status == "failed"
        assert "clone failed" in webhook_event.error_message
        assert isinstance(webhook_event.scan_report_id, str)
        assert created[0].status == ScanStatus.FAILED
        assert created[0].duration_seconds >= 0
        event_save.assert_awaited()
        report_save.assert_awaited()
