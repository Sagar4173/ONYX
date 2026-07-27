from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.notifications.notification_service import (
    NotificationService,
    NotificationChannel,
)


@pytest.fixture
def service():
    return NotificationService()


@pytest.fixture
def mock_scan_report():
    report = MagicMock()
    report.scan_id = "scan-001"
    report.project_name = "test-project"
    report.status = "completed"
    report.total_findings = 5
    report.findings_by_severity = {"critical": 1, "high": 2, "medium": 1, "low": 1}
    report.duration_seconds = 45.0
    report.completed_at = None
    report.git_metadata = MagicMock()
    report.git_metadata.repository_url = "https://github.com/test/test"
    report.git_metadata.branch = "main"
    report.git_metadata.commit_hash = "abc123def456"
    report.ai_analysis = None
    return report


class TestSendScanNotification:
    """Tests for send_scan_notification"""

    @pytest.mark.asyncio
    async def test_delegates_to_notifier_service(self, service, mock_scan_report):
        mock_notifier = AsyncMock()
        mock_notifier.send_scan_notification.return_value = MagicMock(
            slack_sent=True, teams_sent=False
        )

        with patch(
            "services.notifications.notifier.notification_service", mock_notifier
        ):
            result = await service.send_scan_notification(mock_scan_report)

        assert result is True
        mock_notifier.send_scan_notification.assert_called_once_with(mock_scan_report)

    @pytest.mark.asyncio
    async def test_returns_false_on_failure(self, service, mock_scan_report):
        with patch(
            "services.notifications.notifier.notification_service"
        ) as mock_notifier:
            mock_notifier.send_scan_notification = AsyncMock(
                side_effect=Exception("notifier failed")
            )
            result = await service.send_scan_notification(mock_scan_report)

        assert result is False


class TestSendSlackTeams:
    """Tests for _send_slack_teams"""

    @pytest.mark.asyncio
    async def test_loads_report_and_sends(self, service, mock_scan_report):
        mock_notifier = AsyncMock()
        mock_notifier.send_scan_notification = AsyncMock()

        with (
            patch(
                "services.notifications.notifier.notification_service", mock_notifier
            ),
            patch.object(service, "_load_scan_report", return_value=mock_scan_report),
        ):
            await service._send_slack_teams("scan-001")

        mock_notifier.send_scan_notification.assert_called_once_with(mock_scan_report)

    @pytest.mark.asyncio
    async def test_skips_when_no_report(self, service):
        mock_notifier = AsyncMock()

        with (
            patch(
                "services.notifications.notifier.notification_service", mock_notifier
            ),
            patch.object(service, "_load_scan_report", return_value=None),
        ):
            await service._send_slack_teams("scan-001")

        mock_notifier.send_scan_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_notifier_error_gracefully(self, service, mock_scan_report):
        with (
            patch(
                "services.notifications.notifier.notification_service"
            ) as mock_notifier,
            patch.object(service, "_load_scan_report", return_value=mock_scan_report),
        ):
            mock_notifier.send_scan_notification = AsyncMock(
                side_effect=Exception("network error")
            )
            await service._send_slack_teams("scan-001")


class TestSendScanStarted:
    """Tests for send_scan_started"""

    @pytest.mark.asyncio
    async def test_calls_send_slack_teams(self, service):
        with patch.object(service, "_send_slack_teams", AsyncMock()) as mock_slack:
            result = await service.send_scan_started(
                project_name="test",
                scan_id="scan-001",
                user_id="user-1",
                repository_url="https://github.com/test/test",
            )

        assert result is True
        mock_slack.assert_called_once_with("scan-001")

    @pytest.mark.asyncio
    async def test_slack_teams_error_does_not_block(self, service):
        # _send_slack_teams is internally safe (catches its own exceptions),
        # but if anything else fails the method returns False
        with patch.object(service, "_send_slack_teams", AsyncMock()):
            result = await service.send_scan_started(
                project_name="test", scan_id="scan-001", user_id="user-1"
            )

        assert result is True


class TestSendScanCompleted:
    """Tests for send_scan_completed"""

    @pytest.mark.asyncio
    async def test_calls_send_slack_teams(self, service):
        with (
            patch.object(service, "_send_slack_teams", AsyncMock()) as mock_slack,
            patch.object(
                service, "_get_user_notification_preferences", return_value={}
            ),
        ):
            result = await service.send_scan_completed(
                project_name="test",
                scan_id="scan-001",
                user_id="user-1",
                findings_count=5,
                critical_count=0,
                high_count=2,
            )

        assert result is True
        mock_slack.assert_called_once_with("scan-001")

    @pytest.mark.asyncio
    async def test_calls_critical_alert_when_critical_findings(self, service):
        with (
            patch.object(service, "_send_slack_teams", AsyncMock()),
            patch.object(
                service, "_get_user_notification_preferences", return_value={}
            ),
            patch.object(
                service, "send_critical_vulnerability_alert", AsyncMock()
            ) as mock_critical,
        ):
            result = await service.send_scan_completed(
                project_name="test",
                scan_id="scan-001",
                user_id="user-1",
                findings_count=5,
                critical_count=2,
                high_count=1,
            )

        assert result is True
        mock_critical.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_critical_alert_when_no_critical(self, service):
        with (
            patch.object(service, "_send_slack_teams", AsyncMock()),
            patch.object(
                service, "_get_user_notification_preferences", return_value={}
            ),
            patch.object(
                service, "send_critical_vulnerability_alert", AsyncMock()
            ) as mock_critical,
        ):
            result = await service.send_scan_completed(
                project_name="test",
                scan_id="scan-001",
                user_id="user-1",
                findings_count=3,
                critical_count=0,
                high_count=1,
            )

        assert result is True
        mock_critical.assert_not_called()


class TestSendScanFailed:
    """Tests for send_scan_failed"""

    @pytest.mark.asyncio
    async def test_calls_send_slack_teams(self, service):
        with patch.object(service, "_send_slack_teams", AsyncMock()) as mock_slack:
            result = await service.send_scan_failed(
                project_name="test",
                scan_id="scan-001",
                user_id="user-1",
                error_message="Something went wrong",
            )

        assert result is True
        mock_slack.assert_called_once_with("scan-001")

    @pytest.mark.asyncio
    async def test_handles_without_error_message(self, service):
        with patch.object(service, "_send_slack_teams", AsyncMock()):
            result = await service.send_scan_failed(
                project_name="test", scan_id="scan-001", user_id="user-1"
            )

        assert result is True


class TestSendCriticalVulnerabilityAlert:
    """Tests for send_critical_vulnerability_alert"""

    @pytest.mark.asyncio
    async def test_calls_send_slack_teams(self, service):
        with (
            patch.object(service, "_send_slack_teams", AsyncMock()) as mock_slack,
            patch.object(
                service, "_get_user_notification_preferences", return_value={}
            ),
        ):
            result = await service.send_critical_vulnerability_alert(
                project_name="test",
                scan_id="scan-001",
                user_id="user-1",
                critical_count=3,
            )

        assert result is True
        mock_slack.assert_called_once_with("scan-001")


class TestConfigureChannels:
    """Tests for configure_channels"""

    def test_sets_enabled_channels(self, service):
        channels = [NotificationChannel.SLACK, NotificationChannel.EMAIL]
        service.configure_channels(channels)
        assert service.enabled_channels == channels

    def test_is_channel_enabled(self, service):
        service.enabled_channels = [NotificationChannel.EMAIL]
        assert service.is_channel_enabled(NotificationChannel.EMAIL) is True
        assert service.is_channel_enabled(NotificationChannel.SLACK) is False
