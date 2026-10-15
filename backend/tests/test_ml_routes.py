"""ML triage endpoints (/api/ml, Phase 4 spec 5.1 P4)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app import app
from config import settings
from models.user import User, UserRole
from routes.dependencies import get_current_user
from services.ai.ml_anomaly_detection_engine import MLModelMetrics

FEATURE_KEYS = [
    "total_findings", "critical_ratio", "high_ratio",
    "avg_cvss_score", "unique_cwe_count", "findings_per_hour",
]


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


def _metrics():
    return MLModelMetrics(
        model_id="anomaly_model_20260101_000000",
        model_type="IsolationForest",
        training_data_size=40,
        anomaly_rate=0.1,
        score_mean=0.0123,
        score_std=0.0456,
        last_trained="2026-01-01T00:00:00+00:00",
        feature_importance={name: 0.0 for name in FEATURE_KEYS},
    )


def _stub_engine(monkeypatch, metrics=None, dashboard=None):
    stub = MagicMock()
    stub.models = {}
    stub.train_anomaly_model = AsyncMock(return_value=metrics)
    stub.get_anomaly_dashboard = AsyncMock(
        return_value=dashboard
        if dashboard is not None
        else {"recent_alerts": [], "alert_statistics": {}, "active_model": None}
    )
    monkeypatch.setattr("routes.ml.get_ml_engine", lambda: stub)
    return stub


class TestMLRoutes:
    def test_status_ok(self, monkeypatch):
        monkeypatch.setattr(settings, "ml_isolation_forest_enabled", False)
        _stub_engine(monkeypatch)
        client = _setup_client(_make_mock_user(UserRole.DEVELOPER))

        resp = client.get("/api/ml/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["isolation_forest_enabled"] is False
        assert data["sklearn_available"] is True
        assert data["model_trained"] is False
        assert data["active_model"] is None
        assert data["min_training_scans"] == settings.ml_min_training_scans
        assert data["training_window_days"] == settings.ml_training_window_days

    def test_train_requires_admin(self, monkeypatch):
        stub = _stub_engine(monkeypatch, metrics=_metrics())
        client = _setup_client(_make_mock_user(UserRole.DEVELOPER))

        resp = client.post("/api/ml/train")

        assert resp.status_code == 403
        assert resp.json()["detail"] == "Admin access required"
        stub.train_anomaly_model.assert_not_awaited()

    def test_train_409_when_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "ml_isolation_forest_enabled", False)
        stub = _stub_engine(monkeypatch, metrics=_metrics())
        client = _setup_client(_make_mock_user(UserRole.ADMIN))

        resp = client.post("/api/ml/train")

        assert resp.status_code == 409
        assert "disabled" in resp.json()["detail"]
        stub.train_anomaly_model.assert_not_awaited()

    def test_train_409_when_gate_unmet(self, monkeypatch):
        monkeypatch.setattr(settings, "ml_isolation_forest_enabled", True)
        stub = _stub_engine(monkeypatch, metrics=None)
        client = _setup_client(_make_mock_user(UserRole.ADMIN))

        resp = client.post("/api/ml/train")

        assert resp.status_code == 409
        assert "insufficient scan history" in resp.json()["detail"]
        stub.train_anomaly_model.assert_awaited_once()

    def test_train_ok_when_gate_passes(self, monkeypatch):
        monkeypatch.setattr(settings, "ml_isolation_forest_enabled", True)
        stub = _stub_engine(monkeypatch, metrics=_metrics())
        client = _setup_client(_make_mock_user(UserRole.ADMIN))

        resp = client.post("/api/ml/train")

        assert resp.status_code == 200
        data = resp.json()
        assert data["model_id"] == "anomaly_model_20260101_000000"
        assert data["training_data_size"] == 40
        assert data["anomaly_rate"] == 0.1
        assert data["score_mean"] == 0.0123
        assert data["score_std"] == 0.0456
        assert data["last_trained"] == "2026-01-01T00:00:00+00:00"
        stub.train_anomaly_model.assert_awaited_once()

    def test_anomalies_requires_admin(self, monkeypatch):
        stub = _stub_engine(monkeypatch)
        client = _setup_client(_make_mock_user(UserRole.DEVELOPER))

        resp = client.get("/api/ml/anomalies")

        assert resp.status_code == 403
        assert resp.json()["detail"] == "Admin access required"
        stub.get_anomaly_dashboard.assert_not_awaited()

    def test_anomalies_ok_for_admin(self, monkeypatch):
        dashboard = {
            "recent_alerts": [],
            "alert_statistics": {"HIGH": 2},
            "active_model": None,
            "total_recent_alerts": 0,
            "anomaly_detection_status": "training_required",
        }
        stub = _stub_engine(monkeypatch, dashboard=dashboard)
        client = _setup_client(_make_mock_user(UserRole.ADMIN))

        resp = client.get("/api/ml/anomalies")

        assert resp.status_code == 200
        assert resp.json() == dashboard
        stub.get_anomaly_dashboard.assert_awaited_once()
