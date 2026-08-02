from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWebhookProcessor:
    """Test WebhookProcessor service methods."""

    @pytest.mark.asyncio
    async def test_process_webhook_event_success(self):
        from routes.webhook.processor import WebhookProcessor
        import uuid

        processor = WebhookProcessor()
        event_data = {"ref": "refs/heads/main", "repository": {"clone_url": "https://github.com/test/repo", "full_name": "test/repo"}}
        headers = {"x-github-event": "push"}

        mock_git_meta = MagicMock()
        mock_git_meta.repository_url = "https://github.com/test/repo"
        mock_git_meta.branch = "main"
        mock_git_meta.commit_hash = "abc123"
        mock_git_meta.commit_message = "Test commit"
        mock_git_meta.event_type = "push"

        with (
            patch.object(processor, "_parse_webhook_data", return_value=mock_git_meta),
            patch.object(processor, "_process_scan_workflow", new_callable=AsyncMock),
            patch("routes.webhook.processor.WebhookEvent") as mock_event_cls,
        ):
            mock_event = MagicMock()
            mock_event_cls.return_value = mock_event
            mock_event.insert = AsyncMock()
            mock_event.id = uuid.uuid4()

            event_id = await processor.process_webhook_event(event_data, headers)

            assert uuid.UUID(event_id) is not None
            mock_event.insert.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_webhook_event_no_git_metadata(self):
        from routes.webhook.processor import WebhookProcessor

        processor = WebhookProcessor()
        with (
            patch.object(processor, "_parse_webhook_data", return_value=None),
            patch.object(processor, "_process_scan_workflow", new_callable=AsyncMock),
        ):
            with pytest.raises(Exception):
                await processor.process_webhook_event({}, {})

    def test_parse_webhook_data_github(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        headers = {"x-github-event": "push"}
        with patch.object(processor, "_parse_github_webhook", return_value="github_result") as mock_github:
            result = processor._parse_webhook_data({}, headers)
            mock_github.assert_called_once_with({}, headers)
            assert result == "github_result"

    def test_parse_webhook_data_gitlab(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        headers = {"x-gitlab-event": "Push Hook"}
        with patch.object(processor, "_parse_gitlab_webhook", return_value="gitlab_result") as mock_gl:
            result = processor._parse_webhook_data({}, headers)
            mock_gl.assert_called_once_with({}, headers)
            assert result == "gitlab_result"

    def test_parse_webhook_data_bitbucket(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        headers = {"x-event-key": "repo:push"}
        with patch.object(processor, "_parse_bitbucket_webhook", return_value="bb_result") as mock_bb:
            result = processor._parse_webhook_data({}, headers)
            mock_bb.assert_called_once_with({}, headers)
            assert result == "bb_result"

    def test_parse_webhook_data_generic(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        headers = {}
        with patch.object(processor, "_parse_generic_webhook", return_value="generic_result") as mock_gen:
            result = processor._parse_webhook_data({}, headers)
            mock_gen.assert_called_once_with({}, headers)
            assert result == "generic_result"

    def test_parse_github_webhook_push(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123", "message": "fix bug", "timestamp": "2026-01-15T10:00:00Z"},
            "repository": {"clone_url": "https://github.com/test/repo", "full_name": "test/repo"},
        }
        result = processor._parse_github_webhook(payload, {"x-github-event": "push"})
        assert result is not None
        assert result.repository_url == "https://github.com/test/repo"
        assert result.branch == "main"
        assert result.commit_hash == "abc123"

    def test_parse_github_webhook_pull_request(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "action": "opened",
            "pull_request": {"head": {"sha": "pr123", "ref": "feature"}, "title": "PR title"},
            "repository": {"clone_url": "https://github.com/test/repo", "full_name": "test/repo"},
        }
        result = processor._parse_github_webhook(payload, {"x-github-event": "pull_request"})
        assert result is not None
        assert result.commit_hash == "pr123"
        assert result.branch == "feature"

    def test_parse_github_webhook_unsupported_event(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        result = processor._parse_github_webhook({}, {"x-github-event": "issues"})
        assert result is None

    def test_parse_gitlab_webhook_push(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "project": {"git_http_url": "https://gitlab.com/test/repo", "name": "repo"},
            "commits": [{"id": "gl_commit_1", "message": "fix", "timestamp": "2026-01-15T10:00:00Z"}],
            "ref": "refs/heads/main",
            "after": "gl123",
        }
        result = processor._parse_gitlab_webhook(payload, {"x-gitlab-event": "Push Hook"})
        assert result is not None
        assert result.repository_url == "https://gitlab.com/test/repo"
        assert result.commit_hash == "gl123"

    def test_parse_gitlab_webhook_merge_request(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "project": {"git_http_url": "https://gitlab.com/test/repo"},
            "object_attributes": {"last_commit": {"id": "mr456"}, "source_branch": "feature", "title": "MR title"},
        }
        result = processor._parse_gitlab_webhook(payload, {"x-gitlab-event": "Merge Request Hook"})
        assert result is not None
        assert result.commit_hash == "mr456"

    def test_parse_gitlab_webhook_unsupported(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        result = processor._parse_gitlab_webhook({}, {"x-gitlab-event": "Note Hook"})
        assert result is None

    def test_parse_bitbucket_webhook_push(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "repository": {"links": {"clone": [{"name": "http", "href": "https://bitbucket.org/test/repo"}]}},
            "push": {"changes": [{"new": {"name": "main", "target": {"hash": "bb123", "message": "fix"}}}]},
        }
        result = processor._parse_bitbucket_webhook(payload, {"x-event-key": "repo:push"})
        assert result is not None
        assert result.repository_url == "https://bitbucket.org/test/repo"
        assert result.commit_hash == "bb123"

    def test_parse_bitbucket_webhook_pull_request(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "repository": {"links": {"clone": [{"name": "http", "href": "https://bitbucket.org/test/repo"}]}},
            "pullrequest": {
                "source": {"commit": {"hash": "bb_pr1"}, "branch": {"name": "feature"}},
                "title": "PR title",
            },
        }
        result = processor._parse_bitbucket_webhook(payload, {"x-event-key": "pullrequest:created"})
        assert result is not None
        assert result.commit_hash == "bb_pr1"

    def test_parse_bitbucket_webhook_unsupported(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        result = processor._parse_bitbucket_webhook({}, {"x-event-key": "repo:fork"})
        assert result is None

    def test_parse_generic_webhook_full(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        payload = {
            "repository_url": "https://github.com/test/repo",
            "branch": "develop",
            "commit_hash": "abc",
            "commit_message": "generic commit",
        }
        result = processor._parse_generic_webhook(payload, {})
        assert result is not None
        assert result.repository_url == "https://github.com/test/repo"
        assert result.branch == "develop"
        assert result.commit_hash == "abc"

    def test_parse_generic_webhook_missing_fields(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        result = processor._parse_generic_webhook({"repo_url": "https://github.com/test/repo"}, {})
        assert result is None

    def test_extract_project_name(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        assert processor._extract_project_name("https://github.com/org/my-project.git") == "my-project"
        assert processor._extract_project_name("https://github.com/org/my-project/") == "my-project"
        assert processor._extract_project_name("https://github.com/org/my-project") == "my-project"

    def test_parse_timestamp_isoformat(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        ts = processor._parse_timestamp("2026-01-15T10:00:00Z")
        assert ts is not None
        assert ts.year == 2026
        assert ts.month == 1

    def test_parse_timestamp_invalid(self):
        from routes.webhook.processor import WebhookProcessor
        processor = WebhookProcessor()
        ts = processor._parse_timestamp("not-a-date")
        assert ts is not None
        assert ts.tzinfo is not None


class TestWebhookEventRoutes:
    """Test webhook event route handler methods directly."""

    @pytest.mark.asyncio
    async def test_receive_webhook_processing(self):
        from routes.webhook.events import webhook_processor

        mock_headers = {"host": "example.com", "x-github-event": "push", "content-type": "application/json"}

        with patch.object(webhook_processor, "process_webhook_event", new_callable=AsyncMock, return_value="evt-001"):
            event_id = await webhook_processor.process_webhook_event({}, mock_headers)
            assert event_id == "evt-001"

    @pytest.mark.asyncio
    async def test_get_webhook_event_found(self):
        from models.report import WebhookEvent

        mock_event = MagicMock()
        mock_event.configure_mock(id="evt-001")
        mock_event.event_type = "push"

        with patch.object(WebhookEvent, "get", new_callable=AsyncMock, return_value=mock_event):
            event = await WebhookEvent.get("evt-001")
            assert event is not None
            assert event.id == "evt-001"

    @pytest.mark.asyncio
    async def test_get_webhook_event_not_found(self):
        from models.report import WebhookEvent

        with patch.object(WebhookEvent, "get", new_callable=AsyncMock, return_value=None):
            event = await WebhookEvent.get("nonexistent")
            assert event is None

    @pytest.mark.asyncio
    async def test_list_webhook_events(self):
        from models.report import WebhookEvent

        mock_event = MagicMock()
        mock_event.configure_mock(id="evt-001")

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[mock_event])

        with patch.object(WebhookEvent, "find", return_value=mock_find):
            events = await WebhookEvent.find().sort("-created_at").to_list()
            assert len(events) == 1
            assert events[0].id == "evt-001"


class TestScanOperations:
    """Test scan operations service methods directly."""

    @pytest.mark.asyncio
    async def test_submit_scan_creates_report(self):
        from models.report import ScanReport, ScanStatus
        from datetime import datetime, timezone

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.status = ScanStatus.PENDING

        with (
            patch.object(ScanReport, "insert", new_callable=AsyncMock, return_value=mock_report),
            patch("routes.webhook.scan_operations.process_real_scan", new_callable=AsyncMock),
        ):
            inserted = await ScanReport.insert(mock_report)
            assert inserted.scan_id == "scan-001"
            assert inserted.status == ScanStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_scan_status(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.status = ScanStatus.RUNNING
        mock_report.user_id = "user-1"
        mock_report.progress = 45

        mock_find_one = AsyncMock(return_value=mock_report)

        with patch.object(ScanReport, "find_one", mock_find_one):
            report = await ScanReport.find_one({"scan_id": "scan-001"})
            assert report is not None
            assert report.status == ScanStatus.RUNNING
            assert report.progress == 45

    @pytest.mark.asyncio
    async def test_scan_report_not_found(self):
        from models.report import ScanReport

        with patch.object(ScanReport, "find_one", new_callable=AsyncMock, return_value=None):
            report = await ScanReport.find_one({"scan_id": "nonexistent"})
            assert report is None
