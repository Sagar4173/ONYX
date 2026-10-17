"""Tests for per-finding triage labels (spec 5.1 P4)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import app
from models.base import ScannerType, ScanStatus, SeverityLevel, CVSSScore
from models.report import GitMetadata, ScanReport, ScanResult, VulnerabilityFinding
from models.user import User, UserRole
from routes.dependencies import get_current_user

# Valid ObjectId -> detail route resolves via ScanReport.get (patched in tests).
SCAN_ID = "64b7f1a2c3d4e5f6a7b8c9d0"


def _make_mock_user(role=UserRole.DEVELOPER):
    user = MagicMock(spec=User)
    user.id = "user-test-123"
    user.user_id = "user-test-123"
    user.email = "test@example.com"
    user.role = role
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


def _make_finding(**overrides):
    data = dict(
        id="f-1",
        scanner=ScannerType.SEMGREP,
        rule_id="rule-1",
        title="SQL Injection",
        description="User input flows into query",
        severity=SeverityLevel.HIGH,
        file_path="app.py",
    )
    data.update(overrides)
    return VulnerabilityFinding(**data)


def _make_report(finding=None):
    if finding is None:
        finding = _make_finding()
    report = ScanReport.model_construct(
        project_name="test-project",
        user_id="user-test-123",
        scan_id=SCAN_ID,
        git_metadata=GitMetadata(
            repository_url="https://github.com/test/repo.git",
            branch="main",
            commit_hash="abc123",
            event_type="push",
        ),
        status=ScanStatus.COMPLETED,
        scan_results=[
            ScanResult(
                scanner=ScannerType.SEMGREP,
                status=ScanStatus.COMPLETED,
                findings=[finding],
            )
        ],
        metadata={"triage": {"cached": True}},
        total_findings=1,
    )
    object.__setattr__(report, "save", AsyncMock())
    return report


class TestFindingLabelEndpoint:
    async def test_set_label_persists_and_clears(self, monkeypatch):
        client = _setup_client()
        report = _make_report()
        monkeypatch.setattr(
            "routes.finding_labels.get_accessible_scan_report",
            AsyncMock(return_value=report),
        )

        resp = client.post(
            f"/api/reports/{SCAN_ID}/findings/f-1/label",
            json={"label": "false_positive"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["scan_id"] == SCAN_ID
        assert data["finding_id"] == "f-1"
        assert data["triage_label"] == "false_positive"

        finding = report.scan_results[0].findings[0]
        assert finding.triage_label == "false_positive"
        assert "triage" not in report.metadata
        report.save.assert_awaited()

        resp2 = client.post(
            f"/api/reports/{SCAN_ID}/findings/f-1/label",
            json={"label": "untriaged"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["triage_label"] is None
        assert finding.triage_label is None

    async def test_label_unknown_finding_404(self, monkeypatch):
        client = _setup_client()
        report = _make_report()
        monkeypatch.setattr(
            "routes.finding_labels.get_accessible_scan_report",
            AsyncMock(return_value=report),
        )

        resp = client.post(
            f"/api/reports/{SCAN_ID}/findings/nope/label",
            json={"label": "accepted"},
        )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Finding not found"

    async def test_label_inaccessible_scan_404(self, monkeypatch):
        client = _setup_client()
        monkeypatch.setattr(
            "routes.finding_labels.get_accessible_scan_report",
            AsyncMock(return_value=None),
        )

        resp = client.post(
            f"/api/reports/{SCAN_ID}/findings/f-1/label",
            json={"label": "accepted"},
        )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Scan not found"

    async def test_label_unauthenticated_401(self):
        app.dependency_overrides.clear()
        client = TestClient(app)

        resp = client.post(
            f"/api/reports/{SCAN_ID}/findings/f-1/label",
            json={"label": "accepted"},
        )

        assert resp.status_code == 401


class TestReportDetailExposesLabel:
    async def test_report_detail_includes_label(self):
        client = _setup_client()
        report = _make_report(
            finding=_make_finding(
                triage_label="accepted",
                cvss_score=CVSSScore(
                    base_score=9.8,
                    vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                ),
            )
        )

        with patch.object(
            ScanReport, "get", AsyncMock(return_value=report)
        ), patch(
            "routes.reports.detail.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{SCAN_ID}")

        assert resp.status_code == 200
        findings = resp.json()["scan_results"][0]["findings"]
        assert findings[0]["id"] == "f-1"
        assert "triage_label" in findings[0]
        assert findings[0]["triage_label"] == "accepted"
        assert findings[0]["cvss_score"]["base_score"] == 9.8
        assert findings[0]["cvss_score"]["vector_string"].startswith("CVSS:3.1")

    async def test_report_detail_cvss_null_when_absent(self):
        client = _setup_client()
        report = _make_report(finding=_make_finding())

        with patch.object(
            ScanReport, "get", AsyncMock(return_value=report)
        ), patch(
            "routes.reports.detail.get_user_project_ids", AsyncMock(return_value=[])
        ):
            resp = client.get(f"/api/reports/{SCAN_ID}")

        assert resp.status_code == 200
        findings = resp.json()["scan_results"][0]["findings"]
        assert findings[0]["cvss_score"] is None


class TestVulnerabilityFindingTriageLabelSchema:
    def test_vulnerability_finding_accepts_label(self):
        f = _make_finding(triage_label="accepted")
        assert f.triage_label == "accepted"

        with pytest.raises(ValidationError):
            _make_finding(triage_label="banana")
