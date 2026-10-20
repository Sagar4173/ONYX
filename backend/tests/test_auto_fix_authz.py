from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.report import GitMetadata, ScanReport
from models.user import User, UserRole
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import (
    AUTO_FIX_WRITE_PERMISSION,
    user_can_write_auto_fix,
)


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

    return FixRunResult(
        status=status,
        finding_id="finding-001",
        file_path="app/run.py",
        diff="--- a\n+++ b\n",
        pr_url=None,
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


class TestUserCanWriteAutoFix:
    user_id = "user-test-123"
    object_id = "507f1f77bcf86cd799439011"

    def _report(self, project_id=None, user_id=None):
        report = MagicMock(spec=ScanReport)
        report.project_id = project_id
        report.user_id = user_id if user_id is not None else self.user_id
        report.scan_id = "scan-001"
        return report

    def _member(self, permissions):
        member = MagicMock()
        member.user_id = self.user_id
        member.permissions = permissions
        return member

    def _project(self, owner_id="project-owner", members=()):
        project = MagicMock()
        project.owner_id = owner_id
        project.team_members = list(members)
        return project

    async def test_write_permission_is_scan(self):
        assert AUTO_FIX_WRITE_PERMISSION == "scan"

    async def test_personal_report_owner_allowed(self):
        report = self._report(project_id=None)
        get = AsyncMock()
        find_one = AsyncMock()
        with patch("routes.reports.report_dependencies.Project.get", get):
            with patch("routes.reports.report_dependencies.Project.find_one", find_one):
                assert await user_can_write_auto_fix(report, self.user_id) is True
        get.assert_not_awaited()
        find_one.assert_not_awaited()

    async def test_personal_report_other_user_denied(self):
        report = self._report(project_id=None, user_id="someone-else")
        get = AsyncMock()
        with patch("routes.reports.report_dependencies.Project.get", get):
            assert await user_can_write_auto_fix(report, self.user_id) is False
        get.assert_not_awaited()

    async def test_project_viewer_denied(self):
        report = self._report(project_id=self.object_id)
        project = self._project(members=[self._member(["view_reports"])])
        with patch(
            "routes.reports.report_dependencies.Project.get",
            AsyncMock(return_value=project),
        ):
            assert await user_can_write_auto_fix(report, self.user_id) is False

    async def test_project_scanner_allowed(self):
        report = self._report(project_id=self.object_id)
        project = self._project(members=[self._member(["scan", "view_reports"])])
        with patch(
            "routes.reports.report_dependencies.Project.get",
            AsyncMock(return_value=project),
        ):
            assert await user_can_write_auto_fix(report, self.user_id) is True

    async def test_project_owner_allowed(self):
        report = self._report(project_id=self.object_id)
        project = self._project(owner_id=self.user_id)
        with patch(
            "routes.reports.report_dependencies.Project.get",
            AsyncMock(return_value=project),
        ):
            assert await user_can_write_auto_fix(report, self.user_id) is True

    async def test_project_member_with_all_permission_allowed(self):
        report = self._report(project_id=self.object_id)
        project = self._project(members=[self._member(["all"])])
        with patch(
            "routes.reports.report_dependencies.Project.get",
            AsyncMock(return_value=project),
        ):
            assert await user_can_write_auto_fix(report, self.user_id) is True

    async def test_missing_project_allows_only_report_owner(self):
        report = self._report(project_id=self.object_id)
        get = AsyncMock(return_value=None)
        with patch("routes.reports.report_dependencies.Project.get", get):
            assert await user_can_write_auto_fix(report, self.user_id) is True
            assert await user_can_write_auto_fix(report, "someone-else") is False
        assert get.await_count == 2

    async def test_lookup_error_denies_even_owner(self):
        report = self._report(project_id=self.object_id)
        get = AsyncMock(side_effect=RuntimeError("db down"))
        with patch("routes.reports.report_dependencies.Project.get", get):
            assert await user_can_write_auto_fix(report, self.user_id) is False
        get.assert_awaited_once()

    async def test_legacy_project_id_uses_find_one(self):
        report = self._report(project_id="project-legacy-1")
        project = self._project(members=[self._member(["scan"])])
        find_one = AsyncMock(return_value=project)
        with patch("routes.reports.report_dependencies.Project.find_one", find_one):
            assert await user_can_write_auto_fix(report, self.user_id) is True
        find_one.assert_awaited_once_with({"project_id": "project-legacy-1"})


class TestAutoFixWriteAuthz:
    scan_id = "scan-001"
    finding_id = "finding-001"
    propose_url = f"/api/reports/{scan_id}/auto-fix?finding_id={finding_id}"
    approve_url = f"/api/reports/{scan_id}/auto-fix/{finding_id}/approve"
    state_url = f"/api/reports/{scan_id}/auto-fix/{finding_id}"
    forbidden_detail = "Auto-fix requires scan permission on this project"

    def _make_report(self):
        report = MagicMock(spec=ScanReport)
        report.project_name = "test-repo"
        report.scan_id = self.scan_id
        report.user_id = "user-test-123"
        report.project_id = None
        report.total_findings = 0
        report.scan_results = []
        report.metadata = {}
        report.git_metadata = GitMetadata(
            repository_url="https://github.com/owner/repo",
            branch="main",
            commit_hash="abc123",
            event_type="push",
        )
        return report

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

    def _make_project(self, permissions):
        project = MagicMock()
        project.owner_id = "project-owner"
        member = MagicMock()
        member.user_id = "user-test-123"
        member.permissions = permissions
        project.team_members = [member]
        return project

    def test_propose_with_real_helper_denies_viewer(self):
        report = self._make_report()
        report.project_id = "507f1f77bcf86cd799439011"
        client = _setup_client()
        patchers = self._patch_access(report)
        propose = AsyncMock()
        try:
            with patch(
                "routes.reports.report_dependencies.Project.get",
                AsyncMock(return_value=self._make_project(["view_reports"])),
            ):
                with patch("routes.auto_fix.propose_fix", propose):
                    resp = client.post(self.propose_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 403
        assert resp.json()["detail"] == self.forbidden_detail
        propose.assert_not_awaited()

    def test_propose_with_real_helper_allows_scanner(self):
        report = self._make_report()
        report.project_id = "507f1f77bcf86cd799439011"
        client = _setup_client()
        patchers = self._patch_access(report)
        try:
            with patch(
                "routes.reports.report_dependencies.Project.get",
                AsyncMock(return_value=self._make_project(["scan", "view_reports"])),
            ):
                with patch(
                    "routes.auto_fix.propose_fix",
                    AsyncMock(return_value=_result("awaiting_approval")),
                ):
                    resp = client.post(self.propose_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "awaiting_approval"

    def test_propose_forbidden_returns_403(self):
        client = _setup_client()
        patchers = self._patch_access(self._make_report())
        propose = AsyncMock()
        try:
            with patch(
                "routes.auto_fix.user_can_write_auto_fix", AsyncMock(return_value=False)
            ):
                with patch("routes.auto_fix.propose_fix", propose):
                    resp = client.post(self.propose_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 403
        assert resp.json()["detail"] == self.forbidden_detail
        propose.assert_not_awaited()

    def test_approve_forbidden_returns_403(self):
        client = _setup_client()
        patchers = self._patch_access(self._make_report())
        approve = AsyncMock()
        try:
            with patch(
                "routes.auto_fix.user_can_write_auto_fix", AsyncMock(return_value=False)
            ):
                with patch("routes.auto_fix.approve_fix", approve):
                    resp = client.post(self.approve_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 403
        assert resp.json()["detail"] == self.forbidden_detail
        approve.assert_not_awaited()

    def test_discard_forbidden_returns_403(self):
        client = _setup_client()
        patchers = self._patch_access(self._make_report())
        discard = AsyncMock()
        try:
            with patch(
                "routes.auto_fix.user_can_write_auto_fix", AsyncMock(return_value=False)
            ):
                with patch("routes.auto_fix.discard_pending", discard):
                    resp = client.delete(self.state_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 403
        assert resp.json()["detail"] == self.forbidden_detail
        discard.assert_not_awaited()

    def test_get_state_remains_read_accessible(self):
        client = _setup_client()
        patchers = self._patch_access(self._make_report())
        check = AsyncMock(return_value=False)
        try:
            with patch("routes.auto_fix.user_can_write_auto_fix", check):
                resp = client.get(self.state_url)
        finally:
            self._stop(patchers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "none"
        check.assert_not_awaited()
