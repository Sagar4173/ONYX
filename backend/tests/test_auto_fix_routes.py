from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.report import (
    GitMetadata,
    ScanReport,
    ScanResult,
    ScannerType,
    ScanStatus,
    SeverityLevel,
    VulnerabilityFinding,
)
from models.user import User, UserRole
from routes.dependencies import get_current_user
from services.scm.auto_fix_service import AutoFixError


def _make_mock_user(role=UserRole.DEVELOPER):
    user = MagicMock(spec=User)
    user.id = "user-test-123"
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


class TestAutoFixRoute:
    scan_id = "scan-001"
    finding_id = "finding-001"
    endpoint = f"/api/reports/{scan_id}/auto-fix?finding_id={finding_id}"

    def _make_report(self):
        from unittest.mock import MagicMock
        sr = MagicMock(spec=ScanReport)
        sr.project_name = "test-repo"
        sr.scan_id = self.scan_id
        sr.owner_id = "user-test-123"
        sr.total_findings = 0
        sr.scan_results = []
        sr.git_metadata = GitMetadata(
            repository_url="https://github.com/owner/repo",
            branch="main",
            commit_hash="abc123",
            event_type="push",
        )
        return sr

    def test_auto_fix_success(self):
        from models.report import ScanReport as SR
        mock_report = self._make_report()

        client = _setup_client()

        with patch.object(SR, "find_one", AsyncMock(return_value=mock_report)):
            with patch(
                "routes.auto_fix.auto_fix_service.create_auto_fix_pr",
                AsyncMock(return_value={
                    "pr_url": "https://github.com/owner/repo/pull/1",
                    "pr_number": 1,
                    "branch": "onyx-auto-fix/branch-1",
                    "finding_id": self.finding_id,
                    "file_path": "app/auth.py",
                }),
            ):
                response = client.post(self.endpoint)

        assert response.status_code == 200
        data = response.json()
        assert data["pr_url"] == "https://github.com/owner/repo/pull/1"
        assert data["pr_number"] == 1

    def test_auto_fix_scan_not_found(self):
        from models.report import ScanReport as SR
        client = _setup_client()

        with patch.object(SR, "find_one", AsyncMock(return_value=None)):
            response = client.post(self.endpoint)

        assert response.status_code == 404

    def test_auto_fix_unauthenticated(self):
        app.dependency_overrides.clear()
        client = TestClient(app)

        response = client.post(self.endpoint)

        assert response.status_code == 401

    def test_auto_fix_service_error(self):
        from models.report import ScanReport as SR
        mock_report = self._make_report()

        client = _setup_client()

        with patch.object(SR, "find_one", AsyncMock(return_value=mock_report)):
            with patch(
                "routes.auto_fix.auto_fix_service.create_auto_fix_pr",
                AsyncMock(side_effect=Exception("Internal error")),
            ):
                response = client.post(self.endpoint)

        assert response.status_code == 502

    def test_auto_fix_bad_request(self):
        from models.report import ScanReport as SR
        mock_report = self._make_report()

        client = _setup_client()

        with patch.object(SR, "find_one", AsyncMock(return_value=mock_report)):
            with patch(
                "routes.auto_fix.auto_fix_service.create_auto_fix_pr",
                AsyncMock(side_effect=AutoFixError("No remediation code")),
            ):
                response = client.post(self.endpoint)

        assert response.status_code == 400
        assert "No remediation code" in response.json()["detail"]
