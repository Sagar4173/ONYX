"""IsolationForest hardening (Phase 4, spec 5.1 P4): activation gate, real data, honest metrics."""
import pickle
import sqlite3
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from config import settings
from models.base import CVSSScore, ScanStatus, ScannerType, SeverityLevel
from models.report import ScanReport, ScanResult, VulnerabilityFinding
from services.ai.ml_anomaly_detection_engine import (
    FEATURE_NAMES,
    MLAnomalyDetectionEngine,
    MLModelMetrics,
)

FEATURE_KEYS = {
    "total_findings",
    "critical_ratio",
    "high_ratio",
    "avg_cvss_score",
    "unique_cwe_count",
    "findings_per_hour",
}


@pytest.fixture
def engine(tmp_path):
    return MLAnomalyDetectionEngine(
        db_path=str(tmp_path / "ml.db"), models_path=str(tmp_path / "models")
    )


def _rows(n):
    rows = []
    for i in range(n):
        rows.append({
            "scan_id": f"scan-{i}",
            "total_findings": 20 if i != n - 1 else 120,  # last row = outlier
            "critical_ratio": 0.1,
            "high_ratio": 0.2,
            "avg_cvss_score": 5.5,
            "unique_cwe_count": 4,
            "findings_per_hour": 1.5 if i != n - 1 else 12.0,
        })
    return rows


def _train_settings(monkeypatch, enabled=True, min_scans=10):
    monkeypatch.setattr(settings, "ml_isolation_forest_enabled", enabled)
    monkeypatch.setattr(settings, "ml_min_training_scans", min_scans)


def _make_engine(tmp_path, *, db_name="ml.db", models_name="models"):
    return MLAnomalyDetectionEngine(
        db_path=str(tmp_path / db_name), models_path=str(tmp_path / models_name)
    )


def _write_artifact(path, *, features=None, n_cols=6):
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    x = np.random.RandomState(0).rand(12, n_cols)
    scaler = StandardScaler().fit(x)
    model = IsolationForest(contamination=0.1, random_state=42).fit(scaler.transform(x))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(
            {
                "model": model,
                "scaler": scaler,
                "features": features if features is not None else list(FEATURE_NAMES),
            },
            f,
        )


def _insert_model_row(
    db_path,
    model_file_path,
    *,
    model_id="anomaly_model_test_000000",
    last_trained="2026-10-19T00:00:00+00:00",
    anomaly_rate=0.1,
    score_mean=-0.04,
    score_std=0.01,
    feature_importance_json="{}",
):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO ml_models "
        "(model_id, model_type, training_data_size, last_trained, feature_importance_json, "
        " model_file_path, status, anomaly_rate, score_mean, score_std) "
        "VALUES (?, 'IsolationForest', 40, ?, ?, ?, 'active', ?, ?, ?)",
        (
            model_id,
            last_trained,
            feature_importance_json,
            str(model_file_path),
            anomaly_rate,
            score_mean,
            score_std,
        ),
    )
    conn.commit()
    conn.close()


async def test_train_refuses_when_disabled(engine, monkeypatch):
    monkeypatch.setattr(settings, "ml_isolation_forest_enabled", False)
    collect = AsyncMock(return_value=_rows(40))
    monkeypatch.setattr(engine, "_collect_training_data", collect)

    assert await engine.train_anomaly_model() is None
    collect.assert_not_awaited()
    assert engine.models == {}


async def test_train_refuses_below_min_scans(engine, monkeypatch):
    _train_settings(monkeypatch, min_scans=30)
    monkeypatch.setattr(engine, "_collect_training_data", AsyncMock(return_value=_rows(5)))

    assert await engine.train_anomaly_model() is None
    assert engine.models == {}


async def test_train_happy_path_honest_metrics(engine, monkeypatch):
    _train_settings(monkeypatch, min_scans=10)
    monkeypatch.setattr(engine, "_collect_training_data", AsyncMock(return_value=_rows(40)))

    metrics = await engine.train_anomaly_model()

    assert isinstance(metrics, MLModelMetrics)
    # Fake demo metrics are gone entirely.
    for fake in ("accuracy", "precision", "recall", "f1_score"):
        assert not hasattr(metrics, fake)
    assert metrics.model_type == "IsolationForest"
    assert metrics.training_data_size == 40
    assert 0.0 < metrics.anomaly_rate <= 0.5
    assert isinstance(metrics.score_mean, float)
    assert isinstance(metrics.score_std, float)
    assert set(metrics.feature_importance) == FEATURE_KEYS
    assert metrics.last_trained

    assert "anomaly_detector" in engine.models
    entry = engine.models["anomaly_detector"]
    assert entry["features"] == [
        "total_findings", "critical_ratio", "high_ratio",
        "avg_cvss_score", "unique_cwe_count", "findings_per_hour",
    ]
    assert entry["model"] is not None
    assert entry["scaler"] is not None
    assert (engine.models_path / f"{metrics.model_id}.pkl").exists()

    # Balanced insert: legacy metric columns stay NULL, honest columns populated.
    conn = sqlite3.connect(engine.db_path)
    row = conn.execute(
        "SELECT accuracy, precision_score, recall_score, f1_score, "
        "training_data_size, anomaly_rate, score_mean, score_std, status "
        "FROM ml_models WHERE model_id = ?",
        (metrics.model_id,),
    ).fetchone()
    conn.close()
    assert row[:4] == (None, None, None, None)
    assert row[4] == 40
    assert row[5] == pytest.approx(metrics.anomaly_rate)
    assert row[6] == pytest.approx(metrics.score_mean)
    assert row[7] == pytest.approx(metrics.score_std)
    assert row[8] == "active"


async def test_train_then_restart_hydrates_model(tmp_path, monkeypatch):
    _train_settings(monkeypatch, min_scans=10)
    first = _make_engine(tmp_path)
    monkeypatch.setattr(first, "_collect_training_data", AsyncMock(return_value=_rows(40)))
    metrics = await first.train_anomaly_model()
    assert metrics is not None

    revived = _make_engine(tmp_path)

    assert "anomaly_detector" in revived.models
    entry = revived.models["anomaly_detector"]
    assert entry["metrics"].model_id == metrics.model_id
    assert entry["metrics"].training_data_size == 40
    assert entry["features"] == list(FEATURE_NAMES)
    sample = np.array([[row[k] for k in FEATURE_NAMES] for row in _rows(2)])
    assert entry["model"].predict(entry["scaler"].transform(sample)).shape == (2,)


async def test_no_hydration_when_disabled(tmp_path, monkeypatch):
    _train_settings(monkeypatch, min_scans=10)
    first = _make_engine(tmp_path)
    monkeypatch.setattr(first, "_collect_training_data", AsyncMock(return_value=_rows(40)))
    await first.train_anomaly_model()

    monkeypatch.setattr(settings, "ml_isolation_forest_enabled", False)
    revived = _make_engine(tmp_path)

    assert revived.models == {}


def test_no_hydration_without_row(tmp_path, monkeypatch):
    _train_settings(monkeypatch)

    engine = _make_engine(tmp_path)

    assert engine.models == {}


class _FieldExpr:
    """Offline stand-in for Beanie query expressions (class attr access).

    Records operands so tests can pin the actual query filters.
    """

    def __init__(self):
        self.ge_operands = []
        self.eq_operands = []

    def __ge__(self, other) -> bool:
        self.ge_operands.append(other)
        return True

    def __eq__(self, other) -> bool:
        self.eq_operands.append(other)
        return True


def _finding(finding_id, severity, cwe_id, base_score):
    return VulnerabilityFinding(
        id=finding_id,
        scanner=ScannerType.SEMGREP,
        rule_id="rule-1",
        title="Issue",
        description="Issue description",
        severity=severity,
        file_path="app.py",
        cwe_id=cwe_id,
        cvss_score=CVSSScore(base_score=base_score),
    )


async def test_collect_training_data_uses_mongo(engine, monkeypatch):
    from datetime import datetime, timedelta, timezone

    report_a = ScanReport.model_construct(
        project_name="test-project",
        user_id="user-test-123",
        scan_id="scan-a",
        status=ScanStatus.COMPLETED,
        started_at=datetime.now(timezone.utc) - timedelta(days=1),
        duration_seconds=3600.0,
        scan_results=[
            ScanResult(
                scanner=ScannerType.SEMGREP,
                status=ScanStatus.COMPLETED,
                findings=[
                    _finding("f-1", SeverityLevel.HIGH, "89", 7.5),
                    _finding("f-2", SeverityLevel.CRITICAL, "79", 9.8),
                ],
            )
        ],
        total_findings=2,
    )
    report_empty = ScanReport.model_construct(
        project_name="test-project",
        user_id="user-test-123",
        scan_id="scan-empty",
        status=ScanStatus.COMPLETED,
        started_at=datetime.now(timezone.utc) - timedelta(days=2),
        duration_seconds=600.0,
        scan_results=[
            ScanResult(scanner=ScannerType.SEMGREP, status=ScanStatus.COMPLETED, findings=[])
        ],
        total_findings=0,
    )

    stub = MagicMock()
    stub.to_list = AsyncMock(return_value=[report_a, report_empty])
    find_mock = MagicMock(return_value=stub)

    # Beanie is not initialized offline: class-level query operands and find()
    # are replaced with offline stand-ins that record their operands.
    started_expr, status_expr = _FieldExpr(), _FieldExpr()
    monkeypatch.setattr(ScanReport, "started_at", started_expr, raising=False)
    monkeypatch.setattr(ScanReport, "status", status_expr, raising=False)
    monkeypatch.setattr(ScanReport, "find", find_mock, raising=False)

    rows = await engine._collect_training_data(90)

    find_mock.assert_called_once()
    stub.to_list.assert_awaited_once()

    # Pin the actual query filters (cutoff math + completed-only).
    args, kwargs = find_mock.call_args
    assert len(args) == 2 and not kwargs
    assert len(started_expr.ge_operands) == 1
    cutoff = started_expr.ge_operands[0]
    assert datetime.now(timezone.utc) - timedelta(days=90, minutes=2) < cutoff
    assert status_expr.eq_operands == [ScanStatus.COMPLETED]

    assert len(rows) == 1  # empty scan skipped
    row = rows[0]
    assert set(row) == FEATURE_KEYS | {"scan_id"}
    assert row["scan_id"] == "scan-a"
    assert row["total_findings"] == 2
    assert row["critical_ratio"] == pytest.approx(0.5)
    assert row["high_ratio"] == pytest.approx(0.5)
    assert row["avg_cvss_score"] == pytest.approx(8.65)
    assert row["unique_cwe_count"] == 2
    assert row["findings_per_hour"] == pytest.approx(2.0)


async def test_collect_training_data_returns_empty_on_query_error(engine, monkeypatch):
    monkeypatch.setattr(ScanReport, "started_at", _FieldExpr(), raising=False)
    monkeypatch.setattr(ScanReport, "status", _FieldExpr(), raising=False)
    monkeypatch.setattr(ScanReport, "find", MagicMock(side_effect=RuntimeError("no db")), raising=False)

    assert await engine._collect_training_data(90) == []


async def test_detect_ml_alerts_on_outlier(engine, monkeypatch):
    _train_settings(monkeypatch, min_scans=10)
    monkeypatch.setattr(engine, "_collect_training_data", AsyncMock(return_value=_rows(40)))
    metrics = await engine.train_anomaly_model()
    assert metrics is not None

    outlier = {
        "total_findings": 400,
        "critical_ratio": 0.1,
        "high_ratio": 0.2,
        "avg_cvss_score": 5.5,
        "unique_cwe_count": 4,
        "findings_per_hour": 80.0,
    }
    alerts = await engine._detect_ml_based_anomalies(outlier)

    assert isinstance(alerts, list)
    assert len(alerts) >= 1
    assert alerts[0].anomaly_type == "ml_detected"
    assert alerts[0].confidence_score > 0


def test_init_database_adds_and_survives_new_columns(tmp_path):
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE ml_models (
            model_id TEXT PRIMARY KEY,
            model_type TEXT NOT NULL,
            training_data_size INTEGER,
            accuracy REAL,
            precision_score REAL,
            recall_score REAL,
            f1_score REAL,
            last_trained TEXT,
            feature_importance_json TEXT,
            model_file_path TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )
    conn.commit()
    conn.close()

    # First init ALTERs a legacy table; second init must swallow "duplicate column".
    for _ in range(2):
        MLAnomalyDetectionEngine(db_path=str(db), models_path=str(tmp_path / "models"))

    conn = sqlite3.connect(db)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(ml_models)")}
    conn.close()
    assert {"anomaly_rate", "score_mean", "score_std"} <= cols


async def test_dashboard_degrades_on_missing_new_columns(engine):
    conn = sqlite3.connect(engine.db_path)
    conn.execute("DROP TABLE ml_models")
    conn.execute(
        "CREATE TABLE ml_models (model_id TEXT, model_type TEXT, "
        "training_data_size INTEGER, last_trained TEXT, status TEXT)"
    )
    conn.commit()
    conn.close()

    dashboard = await engine.get_anomaly_dashboard()

    assert dashboard["recent_alerts"] == []
    assert dashboard["alert_statistics"] == {}
    assert dashboard["active_model"] is None
    assert dashboard["total_recent_alerts"] == 0
    assert dashboard["anomaly_detection_status"] == "degraded"
    assert "error" in dashboard
