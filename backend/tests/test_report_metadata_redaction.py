"""Redaction of pre-approval auto-fix payloads from report metadata."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.base import ScannerType, ScanStatus, SeverityLevel
from models.report import GitMetadata, ScanReport, ScanResult, VulnerabilityFinding
from models.user import User, UserRole
from routes.dependencies import get_current_user
from utils.report_metadata import redacted_report_metadata

CUSTOM_SCAN_ID = "qa-live-check-001"


def _pending_metadata():
    return {
        "pending_fixes": {
            "f-1": {"patched_content": "SECRET PATCH", "base_sha": "s"}
        },
        "triage": {"cached": True},
    }


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


def _make_report(metadata):
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
        id="64b7f1a2c3d4e5f6a7b8c9d0",
        project_name="test-project",
        user_id="user-test-123",
        scan_id=CUSTOM_SCAN_ID,
        status=ScanStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None,
        duration_seconds=120,
        git_metadata=GitMetadata(
            repository_url="https://github.com/test/repo.git",
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
        metadata=metadata,
    )
    return report


class TestRedactedReportMetadata:
    def test_strips_pending_fixes_and_preserves_other_keys(self):
        metadata = {
            "pending_fixes": {
                "f-1": {"patched_content": "SECRET PATCH", "base_sha": "s"}
            },
            "findings": [{"rule_id": "B608"}],
            "triage": {"cached": True},
        }

        result = redacted_report_metadata(metadata)

        assert result == {
            "findings": [{"rule_id": "B608"}],
            "triage": {"cached": True},
        }

    @pytest.mark.parametrize("metadata", [None, [], "x"])
    def test_returns_empty_dict_for_non_dict(self, metadata):
        assert redacted_report_metadata(metadata) == {}

    def test_does_not_mutate_input(self):
        metadata = _pending_metadata()

        result = redacted_report_metadata(metadata)

        assert result == {"triage": {"cached": True}}
        assert "pending_fixes" in metadata


class TestReportDetailRedactsPendingFixes:
    def test_detail_omits_pending_fixes(self):
        client = _setup_client()
        report = _make_report(_pending_metadata())

        with patch(
            "routes.reports.detail.ScanReport"
        ) as mock_report_cls, patch(
            "routes.reports.detail.get_user_project_ids", AsyncMock(return_value=[])
        ):
            mock_report_cls.find_one = AsyncMock(return_value=report)
            resp = client.get(f"/api/reports/{CUSTOM_SCAN_ID}")

        assert resp.status_code == 200
        assert resp.json()["metadata"] == {"triage": {"cached": True}}
        assert "SECRET PATCH" not in resp.text
        assert "pending_fixes" not in resp.text
