"""Regression tests for the report download/export endpoint.

Covers custom (non-ObjectId) scan_id resolution and that access-control
failures surface as 403 instead of being swallowed by the DB error handler.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.base import ScannerType, ScanStatus, SeverityLevel
from models.report import GitMetadata, ScanReport, ScanResult, VulnerabilityFinding
from models.user import User, UserRole
from routes.dependencies import get_current_user

# Valid ObjectId -> resolved via ScanReport.get
OBJECT_ID = "64b7f1a2c3d4e5f6a7b8c9d0"
# Custom scan_id used by seeded QA scans -> resolved via ScanReport.find_one
CUSTOM_SCAN_ID = "qa-live-check-001"
CREDENTIAL_URL = "https://ghp_secret@github.com/test/repo.git"
REDACTED_URL = "https://github.com/test/repo.git"


def _make_mock_user():
    user = MagicMock(spec=User)
    user.id = "user-test-123"
    user.user_id = "user-test-123"
    user.email = "test@example.com"
    user.role = UserRole.DEVELOPER
    return user


def _setup_client(mock_user=None):
    app.dependency_overrides.clear()
    if mock_user is None:
        mock_user = _make_mock_user()

    async def _override():
        return mock_user

    app.dependency_overrides[get_current_user] = _override
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def _make_report(
    user_id="user-test-123",
    scan_id=CUSTOM_SCAN_ID,
    repository_url="https://github.com/test/repo.git",
):
    finding = VulnerabilityFinding(
        id="f-1",
        scanner=ScannerType.SEMGREP,
        rule_id="rule-1",
        title="SQL Injection",
        description="User input flows into query",
        severity=SeverityLevel.HIGH,
        file_path="app.py",
    )
    report = ScanReport.model_construct(
        id=OBJECT_ID,
        project_name="test-project",
        user_id=user_id,
        scan_id=scan_id,
        status=ScanStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None,
        duration_seconds=120,
        git_metadata=GitMetadata(
            repository_url=repository_url,
            branch="main",
            commit_hash="abc123",
            event_type="push",
        ),
        scan_results=[
            ScanResult(
                scanner=ScannerType.SEMGREP,
                status=ScanStatus.COMPLETED,
                findings=[finding],
            )
        ],
        findings_by_severity={"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0},
        total_findings=1,
        tags=[],
        metadata={},
    )
    return report


class TestReportExportDownload:
    def test_download_json_resolves_by_custom_scan_id(self):
        client = _setup_client()
        report = _make_report()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=json")

        assert resp.status_code == 200
        data = resp.json()
        assert data["scan_id"] == CUSTOM_SCAN_ID
        assert data["project_name"] == "test-project"
        assert CUSTOM_SCAN_ID in resp.headers["content-disposition"]

    def test_download_csv_resolves_by_custom_scan_id(self):
        client = _setup_client()
        report = _make_report()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=csv")

        assert resp.status_code == 200
        assert CUSTOM_SCAN_ID in resp.text

    def test_download_resolves_by_object_id(self):
        client = _setup_client()
        report = _make_report(scan_id=OBJECT_ID)

        with patch.object(ScanReport, "get", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{OBJECT_ID}/download?format=json")

        assert resp.status_code == 200
        assert resp.json()["scan_id"] == OBJECT_ID

    def test_download_foreign_report_returns_403(self):
        client = _setup_client()
        report = _make_report(user_id="someone-else")

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=json")

        assert resp.status_code == 403
        assert resp.json()["detail"] == "Access denied to this report"

    def test_download_json_redacts_pending_fix_payloads(self):
        client = _setup_client()
        report = _make_report()
        report.metadata = {
            "pending_fixes": {
                "f-1": {"patched_content": "SECRET PATCH", "base_sha": "s"}
            },
            "triage": {"cached": True},
        }

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=json")

        assert resp.status_code == 200
        data = resp.json()
        assert data["metadata"] == {"triage": {"cached": True}}
        assert "SECRET PATCH" not in resp.text
        assert "pending_fixes" not in resp.text

    def test_download_unknown_report_returns_404(self):
        client = _setup_client()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=None)):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=json")

        assert resp.status_code == 404
        assert resp.json()["detail"] == f"Report {CUSTOM_SCAN_ID} not found"


class TestReportUrlCredentialRedaction:
    def test_download_json_strips_repository_url_credentials(self):
        client = _setup_client()
        report = _make_report(repository_url=CREDENTIAL_URL)

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=json")

        assert resp.status_code == 200
        assert resp.json()["git_metadata"]["repository_url"] == REDACTED_URL
        assert "ghp_secret" not in resp.text

    def test_download_csv_strips_repository_url_credentials(self):
        client = _setup_client()
        report = _make_report(repository_url=CREDENTIAL_URL)

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)), patch(
            "routes.reports.export.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}/download?format=csv")

        assert resp.status_code == 200
        assert REDACTED_URL in resp.text
        assert "ghp_secret" not in resp.text

    def test_detail_strips_repository_url_credentials(self):
        client = _setup_client()
        report = _make_report(repository_url=CREDENTIAL_URL)

        with patch("routes.reports.detail.ScanReport") as mock_report_cls, patch(
            "routes.reports.detail.get_user_project_ids", AsyncMock(return_value=[])
        ):
            mock_report_cls.find_one = AsyncMock(return_value=report)
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}")

        assert resp.status_code == 200
        assert resp.json()["git_metadata"]["repository_url"] == REDACTED_URL
        assert "ghp_secret" not in resp.text

    @pytest.mark.asyncio
    async def test_pdf_generation_succeeds_with_credential_url(self):
        from utils.pdf_generator import generate_report_pdf

        report = _make_report(repository_url=CREDENTIAL_URL)

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=report)):
            content = await generate_report_pdf(CUSTOM_SCAN_ID)

        assert content is not None
        assert content.startswith(b"%PDF")

    def test_pdf_report_data_redacts_credentials_and_pending_fixes(self):
        from utils.report_data import build_report_data

        report = _make_report(repository_url=CREDENTIAL_URL)
        report.metadata = {
            "pending_fixes": {"f-1": {"diff": "secret"}},
            "triage": {"f-1": {"label": "TP"}},
        }

        data = build_report_data(report)

        assert data["git_metadata"]["repository_url"] == REDACTED_URL
        assert "pending_fixes" not in data["metadata"]
        assert data["metadata"]["triage"] == {"f-1": {"label": "TP"}}
