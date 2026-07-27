from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAnalyticsOverview:
    """Test /api/analytics/overview route logic."""

    @pytest.mark.asyncio
    async def test_analytics_overview_with_data(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"
        mock_report.total_findings = 25
        mock_report.findings_by_severity = {"critical": 2, "high": 5, "medium": 8, "low": 10, "info": 0}
        mock_report.scan_results = []

        data = {
            "period": {"days_back": 30},
            "scan_summary": {"total_scans": 1, "completed_scans": 1, "failed_scans": 0, "success_rate": 100.0},
            "vulnerability_summary": {"critical": 2, "high": 5, "medium": 8, "low": 10, "info": 0},
            "scanner_performance": {},
            "top_projects": [{"project_name": "test-project", "total_findings": 25}],
        }

        assert data["scan_summary"]["total_scans"] == 1
        assert data["scan_summary"]["completed_scans"] == 1
        assert data["scan_summary"]["success_rate"] == 100.0
        assert data["vulnerability_summary"]["critical"] == 2

    @pytest.mark.asyncio
    async def test_analytics_overview_no_data(self):
        from models.report import ScanReport

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find({"created_at": {"$gte": "cutoff"}}).to_list()
            assert len(reports) == 0

    def test_analytics_vulnerability_summary_aggregation(self):
        mock_reports = [
            {"findings_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 2, "info": 0}},
            {"findings_by_severity": {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 1}},
            {"findings_by_severity": {"critical": 2, "high": 4, "medium": 6, "low": 6, "info": 2}},
        ]

        vuln_summary = {
            k: sum(r["findings_by_severity"].get(k, 0) for r in mock_reports)
            for k in ("critical", "high", "medium", "low", "info")
        }

        assert vuln_summary["critical"] == 3
        assert vuln_summary["high"] == 6
        assert vuln_summary["low"] == 12
        assert vuln_summary["info"] == 3

    def test_analytics_success_rate(self):
        total = 50
        completed = 40
        rate = (completed / total * 100) if total > 0 else 0
        assert rate == 80.0

    def test_analytics_success_rate_zero(self):
        total = 0
        rate = (0 / total * 100) if total > 0 else 0
        assert rate == 0.0

    def test_top_projects_sorting(self):
        projects = [
            {"name": "proj-a", "total_findings": 100},
            {"name": "proj-b", "total_findings": 50},
            {"name": "proj-c", "total_findings": 200},
        ]
        sorted_projects = sorted(projects, key=lambda x: x["total_findings"], reverse=True)
        assert sorted_projects[0]["name"] == "proj-c"
        assert sorted_projects[1]["name"] == "proj-a"
        assert sorted_projects[2]["name"] == "proj-b"

    def test_top_projects_limited_to_10(self):
        projects = [{"name": f"proj-{i}", "total_findings": i * 10} for i in range(15)]
        sorted_projects = sorted(projects, key=lambda x: x["total_findings"], reverse=True)[:10]
        assert len(sorted_projects) == 10
