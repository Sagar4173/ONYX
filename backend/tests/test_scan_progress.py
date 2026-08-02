"""
Live scan progress tests: phase progress callback, webhook-path progress wiring,
and the in-memory scan console log.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from routes.webhook import processor
from routes.webhook.processor import add_scan_log, get_scan_log
from services.scanning.workflow.enhanced import EnhancedScanningWorkflow


def _workflow_instance():
    workflow = EnhancedScanningWorkflow.__new__(EnhancedScanningWorkflow)
    workflow.notification_service = MagicMock()
    workflow.notification_service.send_scan_notification = AsyncMock()
    return workflow


class TestScanLogStore:
    def test_add_and_get_round_trip(self):
        add_scan_log("s-1", "INFO", "hello")
        add_scan_log("s-1", "SCAN", "world")
        lines = get_scan_log("s-1")
        assert len(lines) == 2
        assert lines[0]["level"] == "INFO"
        assert lines[0]["message"] == "hello"
        assert lines[1]["level"] == "SCAN"
        assert "timestamp" in lines[0]

    def test_unknown_scan_returns_empty(self):
        assert get_scan_log("does-not-exist") == []

    def test_log_is_bounded(self):
        for i in range(processor.MAX_SCAN_LOG_LINES + 50):
            add_scan_log("s-big", "INFO", f"line-{i}")
        assert len(get_scan_log("s-big")) == processor.MAX_SCAN_LOG_LINES


class TestProgressCallback:
    @pytest.fixture(autouse=True)
    def _patch_workflow_internals(self):
        workflow = _workflow_instance()
        with (
            patch.object(workflow, "_analyze_repository_context", new=AsyncMock(return_value={})),
            patch.object(workflow, "_execute_security_scans", new=AsyncMock(return_value=[])),
            patch.object(workflow, "_generate_comprehensive_ai_analysis", new=AsyncMock(return_value=None)),
            patch.object(workflow, "_process_vulnerabilities", new=AsyncMock()),
            patch.object(workflow, "_analyze_compliance", new=AsyncMock(return_value=None)),
            patch(
                "services.scanning.secrets.secret_history_service.SecretHistoryService",
            ) as secret_cls,
        ):
            secret_cls.return_value.update_from_scan = AsyncMock()
            yield workflow

    @pytest.fixture
    def scan_report(self):
        from models.report import ScanReport

        report = ScanReport.model_construct(
            project_name="blogverse",
            scan_id="scan-progress-1",
            status="pending",
            scan_results=[],
            total_findings=0,
            metadata={},
        )
        object.__setattr__(report, "save", AsyncMock())
        return report

    async def test_callback_reports_each_phase_ascending(self, scan_report):
        calls = []

        async def callback(pct, message):
            calls.append((pct, message))

        workflow = _workflow_instance()
        with (
            patch.object(workflow, "_analyze_repository_context", new=AsyncMock(return_value={})),
            patch.object(workflow, "_execute_security_scans", new=AsyncMock(return_value=[])),
            patch.object(workflow, "_generate_comprehensive_ai_analysis", new=AsyncMock(return_value=None)),
            patch.object(workflow, "_process_vulnerabilities", new=AsyncMock()),
            patch.object(workflow, "_analyze_compliance", new=AsyncMock(return_value=None)),
            patch(
                "services.scanning.secrets.secret_history_service.SecretHistoryService",
            ) as secret_cls,
        ):
            secret_cls.return_value.update_from_scan = AsyncMock()
            await workflow.execute_comprehensive_scan(
                scan_report=scan_report,
                repository_path="/tmp/repo",
                progress_callback=callback,
            )

        percentages = [pct for pct, _ in calls]
        assert percentages == sorted(percentages)
        assert percentages[0] == 10
        assert percentages[-1] == 100
        assert calls[-1][1] == "Scan complete"
        assert scan_report.status == "completed"

    async def test_callback_failure_does_not_abort_scan(self, scan_report):
        async def broken_callback(pct, message):
            raise RuntimeError("console down")

        workflow = _workflow_instance()
        with (
            patch.object(workflow, "_analyze_repository_context", new=AsyncMock(return_value={})),
            patch.object(workflow, "_execute_security_scans", new=AsyncMock(return_value=[])),
            patch.object(workflow, "_generate_comprehensive_ai_analysis", new=AsyncMock(return_value=None)),
            patch.object(workflow, "_process_vulnerabilities", new=AsyncMock()),
            patch.object(workflow, "_analyze_compliance", new=AsyncMock(return_value=None)),
            patch(
                "services.scanning.secrets.secret_history_service.SecretHistoryService",
            ) as secret_cls,
        ):
            secret_cls.return_value.update_from_scan = AsyncMock()
            result = await workflow.execute_comprehensive_scan(
                scan_report=scan_report,
                repository_path="/tmp/repo",
                progress_callback=broken_callback,
            )

        assert result.status == "completed"


class TestWebhookScanProgress:
    async def test_webhook_scan_wires_progress_callback_and_log(self):
        from models.report import GitMetadata

        report = MagicMock()
        report.scan_id = "scan-wb-1"
        report.project_name = "blogverse"
        report.save = AsyncMock()
        report.insert = AsyncMock()
        report.total_findings = 3
        report.findings_by_severity = {"critical": 0, "high": 1, "medium": 1, "low": 1, "info": 0}

        event = MagicMock()
        event.save = AsyncMock()

        git_metadata = GitMetadata.model_construct(
            repository_url="https://github.com/Sagar4173/BlogVerse.git",
            branch="main",
            commit_hash="abc123",
            commit_message="",
            commit_author="",
            event_type="push",
        )

        project = MagicMock()
        project.id = "proj-1"
        project.owner_id = "user-1"

        project_cls = MagicMock()
        project_cls.find_one = AsyncMock(return_value=project)

        scan_cls = MagicMock()
        scan_cls.return_value = report

        ws = MagicMock()
        ws.notify_scan_started = AsyncMock()
        ws.notify_scan_progress = AsyncMock()
        ws.notify_scan_completed = AsyncMock()
        ws.notify_scan_failed = AsyncMock()

        workflow = MagicMock()
        workflow.execute_comprehensive_scan = AsyncMock(return_value=report)

        with (
            patch("routes.webhook.processor.ScanReport", new=scan_cls),
            patch("models.project.Project", new=project_cls),
            patch("routes.webhook.processor.ws_manager", new=ws),
            patch("routes.webhook.processor.enhanced_workflow", new=workflow),
            patch(
                "routes.webhook.processor.repo_cloner.clone_repository",
                new=AsyncMock(return_value={"local_path": "/tmp/repo"}),
            ),
            patch(
                "routes.webhook.processor.repo_cloner.cleanup_repository",
                new=AsyncMock(),
            ),
            patch.object(processor.settings, "cleanup_after_scan", False),
        ):
            await processor.webhook_processor._process_scan_workflow(event, git_metadata)

        kwargs = workflow.execute_comprehensive_scan.call_args.kwargs
        assert callable(kwargs["progress_callback"])

        await kwargs["progress_callback"](42, "Running security scanners...")

        assert report.progress == 42
        assert report.current_scanner == "Running security scanners..."
        ws.notify_scan_progress.assert_awaited_once()
        lines = get_scan_log("scan-wb-1")
        assert any(line["message"] == "Running security scanners..." for line in lines)
        assert any(line["level"] == "INFO" for line in lines)

        ws.notify_scan_completed.assert_awaited_once()
        assert ws.notify_scan_failed.await_count == 0

    async def test_webhook_scan_failure_logs_and_notifies(self):
        from models.report import GitMetadata

        report = MagicMock()
        report.scan_id = "scan-wb-fail"
        report.project_name = "blogverse"
        report.started_at = None
        report.save = AsyncMock()
        report.insert = AsyncMock()

        event = MagicMock()
        event.save = AsyncMock()

        git_metadata = GitMetadata.model_construct(
            repository_url="https://github.com/Sagar4173/BlogVerse.git",
            branch="main",
            commit_hash="abc123",
            commit_message="",
            commit_author="",
            event_type="push",
        )

        project = MagicMock()
        project.id = "proj-1"
        project.owner_id = "user-1"

        project_cls = MagicMock()
        project_cls.find_one = AsyncMock(return_value=project)

        scan_cls = MagicMock()
        scan_cls.return_value = report

        ws = MagicMock()
        ws.notify_scan_started = AsyncMock()
        ws.notify_scan_progress = AsyncMock()
        ws.notify_scan_completed = AsyncMock()
        ws.notify_scan_failed = AsyncMock()

        workflow = MagicMock()
        workflow.execute_comprehensive_scan = AsyncMock(side_effect=RuntimeError("boom"))

        with (
            patch("routes.webhook.processor.ScanReport", new=scan_cls),
            patch("models.project.Project", new=project_cls),
            patch("routes.webhook.processor.ws_manager", new=ws),
            patch("routes.webhook.processor.enhanced_workflow", new=workflow),
            patch(
                "routes.webhook.processor.repo_cloner.clone_repository",
                new=AsyncMock(return_value={"local_path": "/tmp/repo"}),
            ),
            patch.object(processor.settings, "cleanup_after_scan", False),
        ):
            await processor.webhook_processor._process_scan_workflow(event, git_metadata)

        ws.notify_scan_failed.assert_awaited_once()
        assert "boom" in ws.notify_scan_failed.await_args.args[2]
        lines = get_scan_log("scan-wb-fail")
        assert any(line["level"] == "ERROR" and "boom" in line["message"] for line in lines)
