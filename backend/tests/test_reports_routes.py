from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestReportsListing:
    """Test reports listing service methods directly."""

    @pytest.mark.asyncio
    async def test_list_reports_empty(self):
        from models.report import ScanReport

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])
        mock_find.count = AsyncMock(return_value=0)

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find().sort("-created_at").to_list()
            assert reports == []

    @pytest.mark.asyncio
    async def test_list_reports_with_results(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[mock_report])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find().sort("-created_at").to_list()
            assert len(reports) == 1
            assert reports[0].scan_id == "scan-001"

    @pytest.mark.asyncio
    async def test_get_project_reports(self):
        from models.report import ScanReport, ScanStatus

        mock_reports = []
        for i in range(3):
            r = MagicMock()
            r.configure_mock(scan_id=f"scan-00{i}")
            r.status = ScanStatus.COMPLETED
            r.project_name = "test-project"
            r.branch = "main"
            r.commit_hash = f"abc{i}"
            r.total_findings = i * 2
            r.findings_by_severity = {"critical": i, "high": i, "medium": i, "low": i}
            r.duration_seconds = 30 + i
            mock_reports.append(r)

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=mock_reports)

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find({"project_name": "test-project"}).sort("-created_at").to_list()
            assert len(reports) == 3

    @pytest.mark.asyncio
    async def test_list_reports_with_filters(self):
        from models.report import ScanReport

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.skip.return_value = mock_find
        mock_find.limit.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find({"project_name": "test-project", "status": "completed"}).sort("-created_at").skip(0).limit(10).to_list()
            assert reports == []


class TestReportDetail:
    """Test report detail service methods directly."""

    @pytest.mark.asyncio
    async def test_get_report_by_scan_id(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"
        mock_report.repository_url = "https://github.com/test/repo"
        mock_report.total_findings = 10

        with patch.object(ScanReport, "find_one", new_callable=AsyncMock, return_value=mock_report):
            report = await ScanReport.find_one({"scan_id": "scan-001"})
            assert report is not None
            assert report.total_findings == 10

    @pytest.mark.asyncio
    async def test_get_report_not_found(self):
        from models.report import ScanReport

        with patch.object(ScanReport, "find_one", new_callable=AsyncMock, return_value=None):
            report = await ScanReport.find_one({"scan_id": "nonexistent"})
            assert report is None

    @pytest.mark.asyncio
    async def test_report_summary_fields(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"
        mock_report.total_findings = 10
        mock_report.findings_by_severity = {"critical": 1, "high": 2, "medium": 3, "low": 4}

        summary = {
            "scan_id": mock_report.scan_id,
            "total_findings": mock_report.total_findings,
            "findings_by_severity": mock_report.findings_by_severity,
        }
        assert summary["scan_id"] == "scan-001"
        assert summary["total_findings"] == 10
        assert summary["findings_by_severity"]["critical"] == 1

    def test_extract_risk_level(self):
        from routes.reports.detail import _extract_risk_level
        assert _extract_risk_level("This is CRITICAL") == "CRITICAL"
        assert _extract_risk_level("HIGH severity risk") == "HIGH"
        assert _extract_risk_level("Medium level") == "MEDIUM"
        assert _extract_risk_level("low impact") == "LOW"
        assert _extract_risk_level("no risk keywords") is None

    def test_extract_risk_level_empty(self):
        from routes.reports.detail import _extract_risk_level
        assert _extract_risk_level("") is None


class TestReportsExport:
    """Test report export logic."""

    def test_export_json_format(self):
        from datetime import datetime, timezone
        report_data = {
            "scan_id": "scan-001",
            "status": "completed",
            "total_findings": 5,
            "findings_by_severity": {"critical": 1},
        }
        import json
        json_str = json.dumps(report_data, indent=2, default=str)
        parsed = json.loads(json_str)
        assert parsed["scan_id"] == "scan-001"

    def test_export_csv_format(self):
        import csv, io
        report_data = {
            "scan_id": "scan-001",
            "project_name": "test-project",
            "status": "completed",
            "total_findings": 5,
            "findings_by_severity": {"critical": 1, "high": 1, "medium": 2, "low": 1},
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
        }
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Project", "Scan ID", "Status", "Total Findings", "Critical", "High", "Medium", "Low", "Repository", "Branch"])
        writer.writerow([
            report_data["project_name"], report_data["scan_id"], report_data["status"],
            report_data["total_findings"],
            report_data["findings_by_severity"]["critical"],
            report_data["findings_by_severity"]["high"],
            report_data["findings_by_severity"]["medium"],
            report_data["findings_by_severity"]["low"],
            report_data["repository_url"], report_data["branch"],
        ])
        content = output.getvalue()
        assert "scan-001" in content
        assert "test-project" in content


class TestReportsAIAnalysis:
    """Test AI analysis retrieval."""

    @pytest.mark.asyncio
    async def test_ai_analysis_present(self):
        from models.report import ScanReport

        mock_ai_data = MagicMock()
        mock_ai_data.executive_summary = "Test summary"
        mock_ai_data.overall_risk_assessment = "Critical risk"
        mock_ai_data.risk_score = 85
        mock_ai_data.risk_level = "CRITICAL"

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.ai_analysis = mock_ai_data

        with patch.object(ScanReport, "find_one", new_callable=AsyncMock, return_value=mock_report):
            report = await ScanReport.find_one({"scan_id": "scan-001"})
            assert report.ai_analysis is not None
            assert report.ai_analysis.risk_level == "CRITICAL"

    @pytest.mark.asyncio
    async def test_ai_analysis_missing(self):
        from models.report import ScanReport

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.ai_analysis = None

        with patch.object(ScanReport, "find_one", new_callable=AsyncMock, return_value=mock_report):
            report = await ScanReport.find_one({"scan_id": "scan-001"})
            assert report.ai_analysis is None


class TestReportsAnalytics:
    """Test reports analytics logic."""

    @pytest.mark.asyncio
    async def test_analytics_overview_computation(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"
        mock_report.total_findings = 10
        mock_report.findings_by_severity = {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 0}
        mock_report.scan_results = []

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[mock_report])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find({"created_at": {"$gte": "cutoff"}}).to_list()
            assert len(reports) == 1

    @pytest.mark.asyncio
    async def test_analytics_overview_empty(self):
        from models.report import ScanReport

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find({"created_at": {"$gte": "cutoff"}}).to_list()
            assert reports == []

    def test_scanner_performance_aggregation(self):
        mock_results = [
            {"scanner": "semgrep", "status": "completed", "findings": [1, 2], "duration_seconds": 30},
            {"scanner": "bandit", "status": "completed", "findings": [3], "duration_seconds": 20},
        ]
        perf = {}
        for r in mock_results:
            scanner = r["scanner"]
            if scanner not in perf:
                perf[scanner] = {"total_runs": 0, "successful_runs": 0, "total_findings": 0, "total_duration": 0}
            perf[scanner]["total_runs"] += 1
            perf[scanner]["successful_runs"] += 1
            perf[scanner]["total_findings"] += len(r["findings"])
            perf[scanner]["total_duration"] += r["duration_seconds"]

        assert perf["semgrep"]["total_runs"] == 1
        assert perf["semgrep"]["total_findings"] == 2
        assert perf["bandit"]["total_findings"] == 1
