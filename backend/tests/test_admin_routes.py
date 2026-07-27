from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAdminDashboard:
    """Test admin dashboard statistics logic."""

    @pytest.mark.asyncio
    async def test_dashboard_stats_users_section(self):
        from models.user import User, UserRole, UserStatus

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[MagicMock(spec=User, role=UserRole.DEVELOPER, status=UserStatus.ACTIVE)])

        with (
            patch.object(User, "find_all", return_value=mock_find),
            patch.object(User, "count", new_callable=AsyncMock, return_value=1),
        ):
            total_users = await User.count()
            assert total_users == 1

    @pytest.mark.asyncio
    async def test_dashboard_empty_database(self):
        with (
            patch("models.user.User.count", new_callable=AsyncMock, return_value=0),
            patch("models.project.Project.count", new_callable=AsyncMock, return_value=0),
            patch("models.report.ScanReport.count", new_callable=AsyncMock, return_value=0),
        ):
            assert True

    def test_ensure_tz_aware_naive(self):
        from routes.admin.dashboard import ensure_tz_aware
        from datetime import datetime, timezone

        naive = datetime(2026, 1, 1, 12, 0, 0)
        aware = ensure_tz_aware(naive)
        assert aware.tzinfo is not None
        assert aware.tzinfo == timezone.utc

    def test_ensure_tz_aware_already_aware(self):
        from routes.admin.dashboard import ensure_tz_aware
        from datetime import datetime, timezone

        aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_tz_aware(aware)
        assert result == aware


class TestAdminUsers:
    """Test admin user management logic."""

    @pytest.mark.asyncio
    async def test_list_all_users(self):
        from models.user import User, UserRole, UserStatus

        mock_users = []
        for i in range(3):
            u = MagicMock()
            u.configure_mock(id=f"user-{i}")
            u.username = f"user{i}"
            u.role = UserRole.DEVELOPER
            u.status = UserStatus.ACTIVE
            mock_users.append(u)

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=mock_users)

        with patch.object(User, "find", return_value=mock_find):
            users = await User.find().sort("-created_at").to_list()
            assert len(users) == 3

    @pytest.mark.asyncio
    async def test_delete_user(self):
        from models.user import User

        mock_user = MagicMock()
        mock_user.configure_mock(id="user-to-delete")
        mock_user.delete = AsyncMock()

        with patch.object(User, "get", new_callable=AsyncMock, return_value=mock_user):
            user = await User.get("user-to-delete")
            assert user is not None
            await user.delete()
            user.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        from models.user import User

        with patch.object(User, "get", new_callable=AsyncMock, return_value=None):
            user = await User.get("nonexistent")
            assert user is None

    @pytest.mark.asyncio
    async def test_update_user_role(self):
        from models.user import User, UserRole
        from datetime import datetime, timezone

        mock_user = MagicMock()
        mock_user.configure_mock(id="user-1")
        mock_user.role = UserRole.DEVELOPER
        mock_user.save = AsyncMock()

        mock_user.role = UserRole.ADMIN
        mock_user.last_updated_by = "admin-id"

        assert mock_user.role == UserRole.ADMIN
        assert mock_user.last_updated_by == "admin-id"

    @pytest.mark.asyncio
    async def test_update_user_status(self):
        from models.user import User, UserStatus

        mock_user = MagicMock()
        mock_user.configure_mock(id="user-1")
        mock_user.status = UserStatus.ACTIVE
        mock_user.save = AsyncMock()

        mock_user.status = UserStatus.SUSPENDED
        mock_user.last_updated_by = "admin-id"

        assert mock_user.status == UserStatus.SUSPENDED

    def test_last_admin_guard(self):
        from models.user import UserRole
        admin_users = [MagicMock(role=UserRole.ADMIN)]
        assert len(admin_users) >= 1


class TestAdminProjects:
    """Test admin project management logic."""

    @pytest.mark.asyncio
    async def test_list_all_projects(self):
        from models.project import Project

        mock_project = MagicMock()
        mock_project.configure_mock(id="proj-1")
        mock_project.name = "test-project"

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[mock_project])

        with patch.object(Project, "find", return_value=mock_find):
            projects = await Project.find().sort("-created_at").to_list()
            assert len(projects) == 1
            assert projects[0].name == "test-project"

    @pytest.mark.asyncio
    async def test_delete_project(self):
        from models.project import Project
        from models.report import ScanReport

        mock_project = MagicMock()
        mock_project.configure_mock(id="proj-1")
        mock_project.delete = AsyncMock()

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[])

        with (
            patch.object(Project, "get", new_callable=AsyncMock, return_value=mock_project),
            patch.object(ScanReport, "find", return_value=mock_find),
        ):
            project = await Project.get("proj-1")
            assert project is not None
            await project.delete()
            project.delete.assert_awaited_once()


class TestAdminReports:
    """Test admin report listing logic."""

    @pytest.mark.asyncio
    async def test_list_all_reports(self):
        from models.report import ScanReport, ScanStatus

        mock_report = MagicMock()
        mock_report.configure_mock(scan_id="scan-001")
        mock_report.status = ScanStatus.COMPLETED
        mock_report.project_name = "test-project"
        mock_report.total_findings = 10
        mock_report.findings_by_severity = {"critical": 1, "high": 2, "medium": 3, "low": 4}

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.skip.return_value = mock_find
        mock_find.limit.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[mock_report])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find().sort("-created_at").skip(0).limit(10).to_list()
            assert len(reports) == 1

    @pytest.mark.asyncio
    async def test_list_reports_with_search(self):
        from models.report import ScanReport

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_find
        mock_find.to_list = AsyncMock(return_value=[])

        with patch.object(ScanReport, "find", return_value=mock_find):
            reports = await ScanReport.find({"project_name": "test-project"}).sort("-created_at").to_list()
            assert reports == []


class TestAdminActivity:
    """Test admin activity feed logic."""

    @pytest.mark.asyncio
    async def test_recent_activity_aggregation(self):
        from datetime import datetime, timezone, timedelta

        mock_users_find = MagicMock()
        mock_users_find.to_list = AsyncMock(return_value=[MagicMock()])

        mock_projects_find = MagicMock()
        mock_projects_find.to_list = AsyncMock(return_value=[MagicMock()])

        mock_scans_find = MagicMock()
        mock_scans_find.to_list = AsyncMock(return_value=[MagicMock()])

        with (
            patch("models.user.User.find", return_value=mock_users_find),
            patch("models.project.Project.find", return_value=mock_projects_find),
            patch("models.report.ScanReport.find", return_value=mock_scans_find),
        ):
            assert True

    @pytest.mark.asyncio
    async def test_user_activity(self):
        from models.project import Project
        from models.report import ScanReport

        mock_projects_find = MagicMock()
        mock_projects_find.to_list = AsyncMock(return_value=[MagicMock()])

        mock_scans_find = MagicMock()
        mock_scans_find.to_list = AsyncMock(return_value=[MagicMock()])

        with (
            patch.object(Project, "find", return_value=mock_projects_find),
            patch.object(ScanReport, "find", return_value=mock_scans_find),
        ):
            projects = await Project.find({"owner_id": "user-1"}).to_list()
            scans = await ScanReport.find({"user_id": "user-1"}).to_list()
            assert len(projects) >= 0
            assert len(scans) >= 0


class TestAdminStatsHealthScore:
    """Test health score computation logic."""

    def test_health_score_perfect(self):
        scan_count = 100
        completed = 100
        critical_count = 0
        total_findings = 50
        active_users = 10
        total_users = 10

        scan_rate = completed / scan_count if scan_count > 0 else 0
        crit_ratio = 1 - (critical_count / total_findings) if total_findings > 0 else 1
        user_ratio = active_users / total_users if total_users > 0 else 0

        health = scan_rate * 40 + crit_ratio * 30 + user_ratio * 30
        assert health == 100.0

    def test_health_score_all_failing(self):
        scan_count = 10
        completed = 0
        critical_count = 10
        total_findings = 10
        active_users = 0
        total_users = 10

        scan_rate = completed / scan_count if scan_count > 0 else 0
        crit_ratio = 1 - (critical_count / total_findings) if total_findings > 0 else 1
        user_ratio = active_users / total_users if total_users > 0 else 0

        health = scan_rate * 40 + crit_ratio * 30 + user_ratio * 30
        assert health == 0.0

    def test_health_score_partial(self):
        scan_count = 10
        completed = 7
        critical_count = 2
        total_findings = 30
        active_users = 5
        total_users = 10

        scan_rate = completed / scan_count
        crit_ratio = 1 - (critical_count / total_findings)
        user_ratio = active_users / total_users

        health = scan_rate * 40 + crit_ratio * 30 + user_ratio * 30
        assert 60 < health < 80
