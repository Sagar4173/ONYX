from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRootAndHealth:
    """Test public root and health endpoints."""

    def test_root_returns_message(self, test_app):
        response = test_app.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data

    def test_health_check_structure(self, test_app):
        with patch("app.db_manager.db", MagicMock()):
            response = test_app.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "version" in data
        assert "services" in data
        assert "timestamp" in data

    def test_health_check_db_disconnected(self, test_app):
        with (
            patch("app.db_manager.db", None),
            patch("app.db_manager.test_connection", new_callable=AsyncMock, return_value="disconnected"),
        ):
            response = test_app.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["services"]["database"] == "disconnected"


class TestPublicStats:
    """Test /api/stats/public endpoint."""

    def test_stats_with_data(self, test_app):
        mock_find_all = MagicMock()
        mock_find_all.to_list = AsyncMock(return_value=[MagicMock(total_findings=50)])

        with (
            patch("routes.stats.ScanReport.count", new_callable=AsyncMock, return_value=10),
            patch("routes.stats.User.count", new_callable=AsyncMock, return_value=5),
            patch("routes.stats.ScanReport.find_all", return_value=mock_find_all),
            patch("routes.stats.db_manager.db", MagicMock()),
        ):
            response = test_app.get("/api/stats/public")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 10
        assert data["total_users"] == 5
        assert data["total_vulnerabilities"] == 50

    def test_stats_no_database(self, test_app):
        with patch("routes.stats.db_manager.db", None):
            response = test_app.get("/api/stats/public")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 0
        assert data["total_users"] == 0

    def test_stats_zero_counts(self, test_app):
        mock_find_all = MagicMock()
        mock_find_all.to_list = AsyncMock(return_value=[])

        with (
            patch("routes.stats.ScanReport.count", new_callable=AsyncMock, return_value=0),
            patch("routes.stats.User.count", new_callable=AsyncMock, return_value=0),
            patch("routes.stats.ScanReport.find_all", return_value=mock_find_all),
            patch("routes.stats.db_manager.db", MagicMock()),
        ):
            response = test_app.get("/api/stats/public")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 0


class TestAnalytics:
    """Test /api/analytics/overview endpoint."""

    def test_analytics_overview_with_data(self, test_app):
        from datetime import datetime, timezone

        from models.report import ScanStatus

        mock_report = MagicMock()
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"
        mock_report.total_findings = 25
        mock_report.findings_by_severity = {"critical": 2, "high": 5, "medium": 8, "low": 10, "info": 0}
        mock_report.scan_results = []

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[mock_report])

        with patch("routes.analytics.ScanReport") as mock_sr:
            mock_sr.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
            mock_sr.find.return_value = mock_find
            response = test_app.get("/api/analytics/overview?days_back=30")
        assert response.status_code == 200
        data = response.json()
        assert data["scan_summary"]["total_scans"] == 1
        assert data["vulnerability_summary"]["critical"] == 2
        assert len(data["top_projects"]) == 1

    def test_analytics_overview_empty(self, test_app):
        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[])

        with patch("routes.analytics.ScanReport.find", return_value=mock_find):
            response = test_app.get("/api/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["scan_summary"]["total_scans"] == 0
        assert data["scan_summary"]["success_rate"] == 0
        assert data["top_projects"] == []


class TestScanners:
    """Test /api/scanners/health endpoint."""

    def test_scanners_health_structure(self, test_app):
        mock_result = {"status": "available", "version": "1.0.0"}

        with patch("routes.scanners._check_scanner_availability", new_callable=AsyncMock, return_value=mock_result):
            response = test_app.get("/api/scanners/health")
        assert response.status_code == 200
        data = response.json()
        assert "scanners" in data
        assert "overall_status" in data
        assert "timestamp" in data

    def test_scanners_health_all_available(self, test_app):
        mock_available = {"status": "available", "version": "1.0.0"}

        with patch("routes.scanners._check_scanner_availability", new_callable=AsyncMock, return_value=mock_available):
            response = test_app.get("/api/scanners/health")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "healthy"
        assert data["available_count"] == 5
        assert data["total_count"] == 5


class TestWebhook:
    """Test /api/webhook endpoints."""

    def test_receive_webhook_accepted(self, test_app):
        from config import settings
        from routes.webhook.processor import webhook_processor

        mock_git_meta = MagicMock()
        mock_git_meta.repository_url = "https://github.com/test/repo"
        mock_git_meta.branch = "main"
        mock_git_meta.commit_hash = "abc123"
        mock_git_meta.event_type = "push"

        with (
            patch.object(settings, "webhook_secret", "test-webhook-secret"),
            patch.object(webhook_processor, "_parse_webhook_data", return_value=mock_git_meta),
            patch.object(webhook_processor, "_process_scan_workflow", new_callable=AsyncMock),
            patch("routes.webhook.processor.WebhookEvent") as mock_event_cls,
        ):
            mock_event = MagicMock()
            mock_event_cls.return_value = mock_event
            mock_event.insert = AsyncMock()

            response = test_app.post(
                "/api/webhook/",
                json={"ref": "refs/heads/main", "repository": {"clone_url": "https://github.com/test/repo"}},
                headers={
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json",
                    "X-Onyx-Webhook-Secret": "test-webhook-secret",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

    def test_webhook_invalid_payload(self, test_app):
        from config import settings

        with patch.object(settings, "webhook_secret", "test-webhook-secret"):
            response = test_app.post(
                "/api/webhook/",
                json={},
                headers={
                    "Content-Type": "application/json",
                    "X-Onyx-Webhook-Secret": "test-webhook-secret",
                },
            )
        assert response.status_code in (400, 500)


AUTH_HEADER = {"Authorization": "Bearer fake-token-for-testing"}


class TestAdminDashboard:
    """Test /api/admin/dashboard/stats endpoint."""

    def test_requires_auth(self, test_app):
        response = test_app.get("/api/admin/dashboard/stats")
        assert response.status_code == 401

    def test_rejects_non_admin(self, test_app, user_auth):
        response = test_app.get("/api/admin/dashboard/stats", headers=AUTH_HEADER)
        assert response.status_code == 403

    def test_allows_admin(self, test_app, admin_auth):
        mock_find_all = MagicMock()
        mock_find_all.to_list = AsyncMock(return_value=[])

        with (
            patch("routes.admin.dashboard.User.count", new_callable=AsyncMock, return_value=5),
            patch("routes.admin.dashboard.Project.count", new_callable=AsyncMock, return_value=3),
            patch("routes.admin.dashboard.ScanReport.count", new_callable=AsyncMock, return_value=10),
            patch("routes.admin.dashboard.User.find_all", return_value=mock_find_all),
            patch("routes.admin.dashboard.Project.find_all", return_value=mock_find_all),
            patch("routes.admin.dashboard.ScanReport.find_all", return_value=mock_find_all),
        ):
            response = test_app.get("/api/admin/dashboard/stats", headers=AUTH_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "projects" in data
        assert "scans" in data
        assert "system" in data


class TestAdminUsers:
    """Test /api/admin/users endpoints."""

    def test_list_requires_auth(self, test_app):
        response = test_app.get("/api/admin/users/all")
        assert response.status_code == 401

    def test_list_allows_admin(self, test_app, admin_auth):
        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.skip.return_value = mock_find
        mock_find.limit.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])
        mock_find.count = AsyncMock(return_value=0)

        with (
            patch("routes.admin.users.User.find", return_value=mock_find),
            patch("routes.admin.users.User.find_all", return_value=mock_find),
            patch("routes.admin.users.Project.find", return_value=mock_find),
            patch("routes.admin.users.ScanReport.find", return_value=mock_find),
        ):
            response = test_app.get("/api/admin/users/all", headers=AUTH_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "pagination" in data


class TestAdminProjects:
    """Test /api/admin/projects endpoints."""

    def test_list_requires_auth(self, test_app):
        response = test_app.get("/api/admin/projects/all")
        assert response.status_code == 401

    def test_list_rejects_non_admin(self, test_app, user_auth):
        response = test_app.get("/api/admin/projects/all", headers=AUTH_HEADER)
        assert response.status_code == 403

    def test_list_allows_admin(self, test_app, admin_auth):
        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.skip.return_value = mock_find
        mock_find.limit.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])
        mock_find.count = AsyncMock(return_value=0)

        with (
            patch("routes.admin.projects.Project.find", return_value=mock_find),
            patch("routes.admin.projects.Project.find_all", return_value=mock_find),
            patch("routes.admin.projects.ScanReport.find", return_value=mock_find),
            patch("routes.admin.projects.User.find_one", new_callable=AsyncMock, return_value=None),
        ):
            response = test_app.get("/api/admin/projects/all", headers=AUTH_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "pagination" in data


class TestAdminReports:
    """Test /api/admin/reports endpoints."""

    def test_list_requires_auth(self, test_app):
        response = test_app.get("/api/admin/reports/all")
        assert response.status_code == 401

    def test_list_allows_admin(self, test_app, admin_auth):
        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.skip.return_value = mock_find
        mock_find.limit.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])
        mock_find.count = AsyncMock(return_value=0)

        with (
            patch("routes.admin.reports.ScanReport.find_all", return_value=mock_find),
            patch("routes.admin.reports.ScanReport.find", return_value=mock_find),
            patch("routes.admin.reports.User.find_one", new_callable=AsyncMock, return_value=None),
        ):
            response = test_app.get("/api/admin/reports/all", headers=AUTH_HEADER)
        assert response.status_code == 200


class TestAdminActivity:
    """Test /api/admin/activity endpoints."""

    def test_recent_requires_auth(self, test_app):
        response = test_app.get("/api/admin/activity/recent")
        assert response.status_code == 401

    def test_recent_rejects_non_admin(self, test_app, user_auth):
        response = test_app.get("/api/admin/activity/recent", headers=AUTH_HEADER)
        assert response.status_code == 403

    def test_recent_allows_admin(self, test_app, admin_auth):
        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.limit.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])

        with (
            patch("routes.admin.activity.User.find", return_value=mock_find),
            patch("routes.admin.activity.Project.find", return_value=mock_find),
            patch("routes.admin.activity.ScanReport.find", return_value=mock_find),
            patch("routes.admin.activity.User.find_all", return_value=mock_find),
            patch("routes.admin.activity.Project.find_all", return_value=mock_find),
            patch("routes.admin.activity.ScanReport.find_all", return_value=mock_find),
        ):
            response = test_app.get("/api/admin/activity/recent", headers=AUTH_HEADER)
        assert response.status_code == 200
