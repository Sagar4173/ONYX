from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.user import UserRole
from routes.dependencies import require_admin


@pytest.fixture(autouse=True)
def _admin_override():
    admin = MagicMock(id="admin-1", email="admin@example.com", role=UserRole.ADMIN)
    app.dependency_overrides[require_admin] = lambda: admin
    yield
    app.dependency_overrides.clear()


class TestWebhookStatus:
    def test_status_when_configured(self):
        from config import settings

        with patch.object(settings, "webhook_secret", "abcdef1234567890"):
            response = TestClient(app).get("/api/admin/webhook/status")

        assert response.status_code == 200
        body = response.json()
        assert body["configured"] is True
        assert body["secret_prefix"] == "abcdef12"
        assert body["url"].endswith("/api/webhook/")
        # Never leak the full secret
        assert "abcdef1234567890" not in response.text

    def test_status_when_unconfigured(self):
        from config import settings

        with patch.object(settings, "webhook_secret", None):
            response = TestClient(app).get("/api/admin/webhook/status")

        assert response.status_code == 200
        body = response.json()
        assert body["configured"] is False
        assert body["secret_prefix"] is None


class TestWebhookRotate:
    def test_rotate_persists_new_secret_and_removes_old(self):
        from config import settings
        from routes.admin import webhook as webhook_admin

        old_lines = [
            "MONGODB_URI=mongodb://example",
            "WEBHOOK_SECRET=oldsecret1234",
            "GEMINI_API_KEY=xyz",
        ]
        saved: list = []

        with (
            patch.object(settings, "webhook_secret", "oldsecret1234"),
            patch.object(webhook_admin, "_load_env_lines", return_value=old_lines),
            patch.object(webhook_admin, "_save_env_lines", side_effect=saved.extend),
        ):
            response = TestClient(app).post("/api/admin/webhook/rotate")
            # Settings not mutated in-memory (restart applies it)
            assert settings.webhook_secret == "oldsecret1234"

        assert response.status_code == 200
        body = response.json()
        assert body["restart_required"] is True
        assert len(body["secret"]) == 64

        secret_lines = [line for line in saved if line.startswith("WEBHOOK_SECRET=")]
        assert len(secret_lines) == 1
        assert secret_lines[0] == f"WEBHOOK_SECRET={body['secret']}"
        # Existing keys untouched
        assert "MONGODB_URI=mongodb://example" in saved
        assert "GEMINI_API_KEY=xyz" in saved

    def test_rotate_returns_500_when_env_unwritable(self):
        from routes.admin import webhook as webhook_admin

        with (
            patch.object(webhook_admin, "_load_env_lines", return_value=[]),
            patch.object(
                webhook_admin,
                "_save_env_lines",
                side_effect=OSError("permission denied"),
            ),
        ):
            response = TestClient(app).post("/api/admin/webhook/rotate")

        assert response.status_code == 500
        assert "permission" in response.json()["detail"].lower()
