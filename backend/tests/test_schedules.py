from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import app
from routes.dependencies import get_current_user


@pytest.fixture(autouse=True)
def _user_override():
    user = MagicMock(id="user-1", role="admin")
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


class TestCronValidation:
    def test_valid_cron_accepted(self):
        from models.schedule import ScheduleCreate

        schedule = ScheduleCreate(
            name="nightly",
            target="https://github.com/test/repo",
            scan_types=["sast"],
            cron_expression="0 2 * * *",
        )
        assert schedule.cron_expression == "0 2 * * *"

    def test_invalid_cron_rejected_at_model_level(self):
        from models.schedule import ScheduleCreate

        with pytest.raises(ValidationError, match="Invalid cron expression"):
            ScheduleCreate(
                name="bad",
                target="https://github.com/test/repo",
                scan_types=["sast"],
                cron_expression="not a cron",
            )

    def test_interval_cron_accepted(self):
        from models.schedule import ScheduleCreate

        schedule = ScheduleCreate(
            name="quarter-hour",
            target="https://github.com/test/repo",
            scan_types=["secrets"],
            cron_expression="*/15 * * * *",
        )
        assert schedule.cron_expression == "*/15 * * * *"

    def test_six_field_cron_rejected(self):
        from models.schedule import ScheduleCreate

        with pytest.raises(ValidationError, match="Invalid cron expression"):
            ScheduleCreate(
                name="seconds",
                target="https://github.com/test/repo",
                scan_types=["secrets"],
                cron_expression="0 0 2 * * *",
            )

    def test_create_endpoint_rejects_invalid_cron(self):
        response = TestClient(app).post(
            "/api/schedules",
            json={
                "name": "bad",
                "target": "https://github.com/test/repo",
                "scan_types": ["sast"],
                "cron_expression": "not a cron",
            },
        )
        assert response.status_code == 422
        assert "cron_expression" in response.text

    async def test_service_rejects_invalid_cron_before_persisting(self):
        from models.schedule import ScanSchedule
        from services.scheduling.scheduler_service import ScanSchedulerService

        # Bypass ScheduleCreate validation to prove the service layer
        # independently rejects invalid cron before insert.
        schedule = ScanSchedule.model_construct(
            name="bad",
            target="https://github.com/test/repo",
            scan_types=["sast"],
            cron_expression="bogus * *",
            created_by="user-1",
        )

        service = ScanSchedulerService()
        with patch.object(ScanSchedule, "insert", new_callable=MagicMock) as insert:
            with pytest.raises(ValueError, match="Invalid cron expression"):
                await service.create_schedule(schedule)
            insert.assert_not_called()
