from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.triage import BusinessContext
from models.user import User, UserRole
from routes.dependencies import get_current_user


def _make_mock_user(role=UserRole.DEVELOPER):
    user = MagicMock(spec=User)
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


class TestGetTriage:
    def test_get_triage_success(self):
        client = _setup_client()
        from models.triage import TriageResult, BusinessContext, ScoreBreakdown, RankedFinding

        mock_result = TriageResult(
            scan_id="scan-001",
            project_name="test-project",
            total_findings=3,
            ranked_findings=[
                RankedFinding(
                    finding_id="f-1",
                    title="SQL Injection",
                    severity="critical",
                    file_path="app.py",
                    composite_score=85.0,
                    priority="IMMEDIATE",
                    score_breakdown=ScoreBreakdown(
                        total=85.0, severity=100, cvss=90, exploitability=80,
                        business_impact=70, compliance_risk=100, epss=75,
                        false_positive_adjustment=0.1,
                    ),
                    sla_deadline="24h",
                )
            ],
            priority_counts={"immediate": 1, "high": 0, "medium": 0, "low": 0, "informational": 2},
            business_context=BusinessContext(),
            executive_summary="Triage summary",
            generated_at="2026-07-27T00:00:00",
        )

        with patch(
            "services.triage.triage_service.TriageService.triage_scan",
            AsyncMock(return_value=mock_result),
        ):
            resp = client.get("/api/triage/scan-001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["scan_id"] == "scan-001"
        assert data["project_name"] == "test-project"
        assert data["total_findings"] == 3
        assert len(data["ranked_findings"]) == 1
        assert data["ranked_findings"][0]["finding_id"] == "f-1"

    def test_get_triage_not_found(self):
        client = _setup_client()
        with patch(
            "services.triage.triage_service.TriageService.triage_scan",
            AsyncMock(return_value=None),
        ):
            resp = client.get("/api/triage/scan-999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Scan not found"

    def test_get_triage_unauthenticated(self):
        client = TestClient(app)
        resp = client.get("/api/triage/scan-001")
        assert resp.status_code == 401


class TestPostTriage:
    def test_post_triage_rescore(self):
        client = _setup_client()
        from models.triage import TriageResult, BusinessContext, ScoreBreakdown, RankedFinding

        mock_result = TriageResult(
            scan_id="scan-001",
            project_name="test-project",
            total_findings=2,
            ranked_findings=[],
            priority_counts={},
            business_context=BusinessContext(
                asset_criticality="critical",
                data_classification="restricted",
                exposure_level="internet_facing",
                compliance_frameworks=["PCI_DSS"],
            ),
            executive_summary=None,
            generated_at="2026-07-27T00:00:00",
        )

        with patch(
            "services.triage.triage_service.TriageService.triage_scan",
            AsyncMock(return_value=mock_result),
        ):
            resp = client.post(
                "/api/triage/scan-001",
                json={
                    "asset_criticality": "critical",
                    "data_classification": "restricted",
                    "exposure_level": "internet_facing",
                    "compliance_frameworks": ["PCI_DSS"],
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["scan_id"] == "scan-001"

    def test_post_triage_not_found(self):
        client = _setup_client()
        with patch(
            "services.triage.triage_service.TriageService.triage_scan",
            AsyncMock(return_value=None),
        ):
            resp = client.post(
                "/api/triage/scan-999",
                json={"asset_criticality": "medium"},
            )
        assert resp.status_code == 404

    def test_post_triage_unauthenticated(self):
        client = TestClient(app)
        resp = client.post(
            "/api/triage/scan-001",
            json={"asset_criticality": "medium"},
        )
        assert resp.status_code == 401
