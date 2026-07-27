from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.base import ScanType
from models.user import User, UserRole
from routes.dependencies import get_current_user


def _make_mock_user(role=UserRole.DEVELOPER, user_id="user123"):
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = role
    user.username = "testuser"
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


def _mock_schedule(id="sched_1", name="Daily Scan", enabled=True, created_by="user123"):
    mock = MagicMock()
    mock.id = id
    mock.name = name
    mock.description = "A test schedule"
    mock.project_id = None
    mock.target = "https://github.com/test/repo.git"
    mock.scan_types = [ScanType.SAST, ScanType.SECRETS]
    mock.cron_expression = "0 2 * * *"
    mock.timezone = "UTC"
    mock.enabled = enabled
    mock.created_by = created_by
    mock.created_at = datetime.now(timezone.utc)
    mock.updated_at = datetime.now(timezone.utc)
    mock.last_run = None
    mock.last_status = None
    mock.next_run = None
    mock.config = {}
    mock.misfire_grace_time = 60
    mock.coalesce = True
    mock.max_instances = 1
    return mock


class TestListSchedules:
    def test_list_schedules(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.list_schedules = AsyncMock(return_value=[_mock_schedule()])
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules")

        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert len(data["schedules"]) == 1
        assert data["schedules"][0]["name"] == "Daily Scan"

    def test_list_schedules_empty(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.list_schedules = AsyncMock(return_value=[])
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules")

        assert response.status_code == 200
        data = response.json()
        assert data["schedules"] == []

    def test_list_schedules_admin_sees_all(self):
        admin = _mock_schedule(id="admin_sched", name="Admin Schedule", created_by="admin")
        client = _setup_client(_make_mock_user(role=UserRole.ADMIN, user_id="admin"))
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.list_schedules = AsyncMock(return_value=[admin])
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules")

        assert response.status_code == 200
        data = response.json()
        assert len(data["schedules"]) == 1


class TestCreateSchedule:
    def test_create_schedule(self):
        client = _setup_client()
        created = _mock_schedule()
        with (
            patch("routes.schedules._get_scheduler") as mock_get,
            patch("routes.schedules.ScanSchedule") as MockScanSchedule,
        ):
            MockScanSchedule.return_value = MagicMock()
            mock_svc = MagicMock()
            mock_svc.create_schedule = AsyncMock(return_value=created)
            mock_get.return_value = mock_svc
            response = client.post(
                "/api/schedules",
                json={
                    "name": "Daily Scan",
                    "target": "https://github.com/test/repo.git",
                    "scan_types": ["sast", "secrets"],
                    "cron_expression": "0 2 * * *",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Daily Scan"

    def test_create_schedule_validation_error(self):
        client = _setup_client()
        response = client.post(
            "/api/schedules",
            json={"name": "Bad Schedule"},
        )

        assert response.status_code == 422


class TestGetSchedule:
    def test_get_schedule(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=_mock_schedule())
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules/sched_1")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Daily Scan"

    def test_get_schedule_not_found(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=None)
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules/nonexistent")

        assert response.status_code == 404

    def test_get_schedule_access_denied(self):
        mock_sched = _mock_schedule(created_by="other_user")
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=mock_sched)
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules/sched_1")

        assert response.status_code == 403


class TestUpdateSchedule:
    def test_update_schedule(self):
        client = _setup_client()
        updated = _mock_schedule(name="Updated Scan")
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=_mock_schedule())
            mock_svc.update_schedule = AsyncMock(return_value=updated)
            mock_get.return_value = mock_svc
            response = client.put(
                "/api/schedules/sched_1",
                json={"name": "Updated Scan"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Scan"


class TestDeleteSchedule:
    def test_delete_schedule(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=_mock_schedule())
            mock_svc.delete_schedule = AsyncMock(return_value=True)
            mock_get.return_value = mock_svc
            response = client.delete("/api/schedules/sched_1")

        assert response.status_code == 200


class TestRunSchedule:
    def test_trigger_schedule_now(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=_mock_schedule())
            mock_svc.run_now = AsyncMock(return_value=True)
            mock_get.return_value = mock_svc
            response = client.post("/api/schedules/sched_1/run")

        assert response.status_code == 200


class TestToggleSchedule:
    def test_toggle_schedule(self):
        client = _setup_client()
        toggled = _mock_schedule(enabled=False)
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=_mock_schedule())
            mock_svc.toggle_schedule = AsyncMock(return_value=toggled)
            mock_get.return_value = mock_svc
            response = client.patch("/api/schedules/sched_1/toggle")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False


class TestScheduleHistory:
    def test_get_schedule_history(self):
        client = _setup_client()
        with patch("routes.schedules._get_scheduler") as mock_get:
            mock_svc = MagicMock()
            mock_svc.get_schedule = AsyncMock(return_value=_mock_schedule())
            mock_svc.get_schedule_history = AsyncMock(
                return_value=[
                    {
                        "scan_id": "scan123",
                        "status": "completed",
                        "total_findings": 5,
                        "findings_by_severity": {"critical": 1},
                    }
                ]
            )
            mock_get.return_value = mock_svc
            response = client.get("/api/schedules/sched_1/history")

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 1
        assert data["history"][0]["scan_id"] == "scan123"
