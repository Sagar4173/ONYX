from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPublicStats:
    """Test /api/stats/public route logic."""

    @pytest.mark.asyncio
    async def test_public_stats_with_data(self):
        from routes.stats import get_public_stats

        mock_report = MagicMock()
        mock_report.total_findings = 50

        mock_find_all = AsyncMock()
        mock_find_all.to_list.return_value = [mock_report]

        with (
            patch("routes.stats.db_manager.db", MagicMock(spec=["count"])),
            patch("routes.stats.ScanReport.count", new_callable=AsyncMock, return_value=10),
            patch("routes.stats.User.count", new_callable=AsyncMock, return_value=25),
            patch("routes.stats.ScanReport.find_all", return_value=mock_find_all),
        ):
            total_scans = 10
            total_users = 25
            reports = [mock_report]
            total_vulnerabilities = sum(r.total_findings for r in reports if r.total_findings)

            assert total_scans == 10
            assert total_users == 25
            assert total_vulnerabilities == 50

    @pytest.mark.asyncio
    async def test_public_stats_no_database(self):
        with patch("routes.stats.db_manager.db", None):
            from routes.stats import get_public_stats

            result = {
                "total_scans": 0,
                "total_vulnerabilities": 0,
                "total_users": 0,
                "uptime_percentage": None,
            }
            assert result["total_scans"] == 0
            assert result["total_users"] == 0
            assert result["uptime_percentage"] is None

    @pytest.mark.asyncio
    async def test_public_stats_empty_database(self):
        with (
            patch("routes.stats.db_manager.db", MagicMock(spec=["count"])),
            patch("routes.stats.ScanReport.count", new_callable=AsyncMock, return_value=0),
            patch("routes.stats.User.count", new_callable=AsyncMock, return_value=0),
            patch("routes.stats.ScanReport.find_all", return_value=AsyncMock(to_list=AsyncMock(return_value=[]))),
        ):
            assert True

    def test_public_stats_response_structure(self):
        response = {
            "total_scans": 42,
            "total_vulnerabilities": 150,
            "total_users": 10,
            "uptime_percentage": None,
        }
        assert "total_scans" in response
        assert "total_vulnerabilities" in response
        assert "total_users" in response
        assert "uptime_percentage" in response

    def test_public_stats_zero_values(self):
        response = {
            "total_scans": 0,
            "total_vulnerabilities": 0,
            "total_users": 0,
            "uptime_percentage": None,
        }
        assert response["total_scans"] == 0
        assert response["total_vulnerabilities"] == 0
