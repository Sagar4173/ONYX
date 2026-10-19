from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.report import GitMetadata, ScanReport
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


def _result(status):
    from services.ai.fix_runner import FixRunResult
    return FixRunResult(status=status, finding_id="finding-001", file_path="app/run.py",
                        diff="--- a\n+++ b\n", pr_url="https://x/pull/1" if status in ("pr_created", "verified") else None)


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
        sr.user_id = "user-test-123"
        sr.project_id = None
        sr.total_findings = 0
        sr.scan_results = []
        sr.git_metadata = GitMetadata(
            repository_url="https://github.com/owner/repo",
            branch="main",
            commit_hash="abc123",
            event_type="push",
        )
        return sr

    def _patch_access(self, report=None):
        from models.report import ScanReport as SR
        patchers = [
            patch.object(SR, "find_one", AsyncMock(return_value=report)),
            patch(
                "routes.reports.report_dependencies.get_user_project_ids",
                AsyncMock(return_value=[]),
            ),
        ]
        for patcher in patchers:
            patcher.start()
        return patchers

    def _stop(self, patchers):
        for patcher in patchers:
            patcher.stop()

    def test_propose_returns_awaiting_approval(self):
        mock_report = self._make_report()
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            with patch("routes.auto_fix.propose_fix", AsyncMock(return_value=_result("awaiting_approval"))):
                resp = client.post(self.endpoint)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "awaiting_approval"

    def test_propose_autofix_error_returns_400(self):
        mock_report = self._make_report()
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            with patch("routes.auto_fix.propose_fix", AsyncMock(side_effect=AutoFixError("boom"))):
                resp = client.post(self.endpoint)
        finally:
            self._stop(patchers)
        assert resp.status_code == 400
        assert "boom" in resp.json()["detail"]

    def test_approve_happy_path(self):
        mock_report = self._make_report()
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            with patch("routes.auto_fix.approve_fix", AsyncMock(return_value=_result("pr_created"))):
                resp = client.post(f"/api/reports/{self.scan_id}/auto-fix/{self.finding_id}/approve")
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pr_created"
        assert resp.json()["pr_url"] == "https://x/pull/1"

    def test_approve_autofix_error_returns_400(self):
        mock_report = self._make_report()
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            with patch("routes.auto_fix.approve_fix",
                       AsyncMock(side_effect=AutoFixError("No pending fix for finding finding-001"))):
                resp = client.post(f"/api/reports/{self.scan_id}/auto-fix/{self.finding_id}/approve")
        finally:
            self._stop(patchers)
        assert resp.status_code == 400

    def test_auto_fix_scan_not_found(self):
        from models.report import ScanReport as SR
        client = _setup_client()

        with patch.object(SR, "find_one", AsyncMock(return_value=None)):
            response = client.post(self.endpoint)

        assert response.status_code == 404

    def test_auto_fix_access_denied_for_foreign_scan(self):
        """Foreign scan must not be auto-fixable (IDOR regression)."""
        foreign_report = self._make_report()
        foreign_report.user_id = "someone-else"

        client = _setup_client()

        patchers = self._patch_access(foreign_report)
        try:
            response = client.post(self.endpoint)
        finally:
            self._stop(patchers)

        assert response.status_code == 404

    def test_auto_fix_unauthenticated(self):
        app.dependency_overrides.clear()
        client = TestClient(app)

        response = client.post(self.endpoint)

        assert response.status_code == 401

    state_url = "/api/reports/scan-001/auto-fix/finding-001"

    def test_get_state_none(self):
        mock_report = self._make_report()
        mock_report.metadata = {}
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            resp = client.get(self.state_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "none"
        assert body["finding_id"] == "finding-001"
        assert body["pr_url"] is None and body["diff"] == ""

    def test_get_state_pending_omits_sensitive_fields(self):
        mock_report = self._make_report()
        mock_report.metadata = {
            "pending_fixes": {
                "finding-001": {
                    "file_path": "app/run.py",
                    "patched_content": "SECRET PATCH",
                    "base_sha": "s",
                    "diff": "--- a\n+++ b\n",
                    "model_used": "groq/m",
                    "created_at": "2026-10-19T00:00:00+00:00",
                }
            }
        }
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            resp = client.get(self.state_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "awaiting_approval"
        assert body["diff"] == "--- a\n+++ b\n"
        assert body["model_used"] == "groq/m"
        assert "SECRET PATCH" not in resp.text
        assert "patched_content" not in body and "base_sha" not in body

    def test_get_state_outcome(self):
        mock_report = self._make_report()
        mock_report.metadata = {
            "findings": [
                {
                    "id": "finding-001",
                    "file_path": "app/run.py",
                    "fix_pr_url": "https://x/pull/1",
                    "fix_status": "pr_created",
                }
            ]
        }
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            resp = client.get(self.state_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        assert resp.json()["pr_url"] == "https://x/pull/1"
        assert resp.json()["status"] == "pr_created"

    def test_get_state_scan_not_found(self):
        from models.report import ScanReport as SR

        client = _setup_client()
        with patch.object(SR, "find_one", AsyncMock(return_value=None)):
            response = client.get(self.state_url)
        assert response.status_code == 404

    def test_get_state_access_denied_for_foreign_scan(self):
        foreign_report = self._make_report()
        foreign_report.user_id = "someone-else"
        client = _setup_client()
        patchers = self._patch_access(foreign_report)
        try:
            response = client.get(self.state_url)
        finally:
            self._stop(patchers)
        assert response.status_code == 404

    def test_get_state_unauthenticated(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get(self.state_url)
        assert response.status_code == 401

    def test_discard_removes_pending(self):
        mock_report = self._make_report()
        mock_report.metadata = {"pending_fixes": {"finding-001": {"diff": "d"}}}
        mock_report.save = AsyncMock()
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            resp = client.delete(self.state_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        assert resp.json() == {"status": "discarded"}
        assert "pending_fixes" not in mock_report.metadata
        mock_report.save.assert_awaited()

    def test_discard_is_idempotent(self):
        mock_report = self._make_report()
        mock_report.metadata = {}
        mock_report.save = AsyncMock()
        client = _setup_client()
        patchers = self._patch_access(mock_report)
        try:
            first = client.delete(self.state_url)
            second = client.delete(self.state_url)
        finally:
            self._stop(patchers)
        assert first.status_code == 200 and second.status_code == 200
        mock_report.save.assert_not_awaited()

    def test_discard_scan_not_found(self):
        from models.report import ScanReport as SR

        client = _setup_client()
        with patch.object(SR, "find_one", AsyncMock(return_value=None)):
            response = client.delete(self.state_url)
        assert response.status_code == 404

    def test_discard_unauthenticated(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.delete(self.state_url)
        assert response.status_code == 401
