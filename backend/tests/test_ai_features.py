"""AI feature-flag discovery endpoint (UX Track Phase 0)."""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app import app
from config import settings
from models.user import User, UserRole
from routes.dependencies import get_current_user


def _setup_client(role=UserRole.DEVELOPER):
    app.dependency_overrides.clear()
    user = MagicMock(spec=User)
    user.id = "user-test-123"
    user.user_id = "user-test-123"
    user.email = "test@example.com"
    user.role = role

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    return TestClient(app)


def test_features_returns_contract():
    client = _setup_client()
    try:
        resp = client.get("/api/ai/features")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data) == {
            "investigate_agent_enabled",
            "ml_isolation_forest_enabled",
            "ml_min_training_scans",
            "ml_training_window_days",
            "auto_fix_requires_approval",
            "ai_rate_limit_rpd",
        }
        assert data["investigate_agent_enabled"] == settings.investigate_agent_enabled
        assert data["ml_isolation_forest_enabled"] == settings.ml_isolation_forest_enabled
        assert data["ml_min_training_scans"] == settings.ml_min_training_scans
        assert data["ml_training_window_days"] == settings.ml_training_window_days
        assert data["auto_fix_requires_approval"] == settings.auto_fix_requires_approval
        assert data["ai_rate_limit_rpd"] == settings.ai_rate_limit_rpd
    finally:
        app.dependency_overrides.clear()


def test_features_requires_auth():
    app.dependency_overrides.clear()
    try:
        resp = TestClient(app).get("/api/ai/features")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()
