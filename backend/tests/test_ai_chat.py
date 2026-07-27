from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
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


class TestAIChatEndpoint:
    """Tests for POST /api/ai/chat"""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        from models.report import ScanReport

        mock_report = MagicMock()
        mock_report.scan_id = "scan-001"
        mock_report.project_name = "test-project"
        mock_report.status = "completed"
        mock_report.total_findings = 5
        mock_report.findings_by_severity = {"critical": 1, "high": 2, "medium": 1, "low": 1}
        mock_report.scan_results = []
        mock_report.ai_analysis = None
        mock_report.owner_id = "user-test-123"
        mock_report.created_at = None

        client = _setup_client()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=mock_report)):
            with patch("routes.ai_chat._call_ai_chat", AsyncMock(return_value="Test AI response")):
                response = client.post(
                    "/api/ai/chat",
                    json={
                        "scan_id": "scan-001",
                        "message": "What are the critical vulnerabilities?",
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Test AI response"
        assert "model_used" in data

    @pytest.mark.asyncio
    async def test_chat_with_history(self):
        from models.report import ScanReport

        mock_report = MagicMock()
        mock_report.scan_id = "scan-001"
        mock_report.project_name = "test-project"
        mock_report.status = "completed"
        mock_report.total_findings = 0
        mock_report.findings_by_severity = {}
        mock_report.scan_results = []
        mock_report.ai_analysis = None
        mock_report.owner_id = "user-test-123"
        mock_report.created_at = None

        client = _setup_client()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=mock_report)):
            with patch("routes.ai_chat._call_ai_chat", AsyncMock(return_value="Follow-up answer")):
                response = client.post(
                    "/api/ai/chat",
                    json={
                        "scan_id": "scan-001",
                        "message": "Tell me more",
                        "conversation_history": [
                            {"role": "user", "content": "What's in this scan?"},
                            {"role": "assistant", "content": "This scan found no vulnerabilities"},
                        ],
                    },
                )

        assert response.status_code == 200
        assert response.json()["reply"] == "Follow-up answer"

    @pytest.mark.asyncio
    async def test_chat_scan_not_found(self):
        from models.report import ScanReport

        client = _setup_client()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=None)):
            response = client.post(
                "/api/ai/chat",
                json={"scan_id": "nonexistent", "message": "Hello"},
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_unauthenticated(self):
        app.dependency_overrides.clear()
        client = TestClient(app)

        response = client.post(
            "/api/ai/chat",
            json={"scan_id": "scan-001", "message": "Hello"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_ai_service_error(self):
        from models.report import ScanReport

        mock_report = MagicMock()
        mock_report.scan_id = "scan-001"
        mock_report.project_name = "test-project"
        mock_report.status = "completed"
        mock_report.total_findings = 0
        mock_report.findings_by_severity = {}
        mock_report.scan_results = []
        mock_report.ai_analysis = None
        mock_report.owner_id = "user-test-123"
        mock_report.created_at = None

        client = _setup_client()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=mock_report)):
            with patch("routes.ai_chat._call_ai_chat", AsyncMock(side_effect=Exception("API down"))):
                response = client.post(
                    "/api/ai/chat",
                    json={"scan_id": "scan-001", "message": "Hello"},
                )

        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_chat_with_findings_context(self):
        from models.report import ScanReport, ScanResult

        mock_finding = MagicMock()
        mock_finding.severity = "critical"
        mock_finding.title = "SQL Injection"
        mock_finding.description = "SQL injection in login endpoint"
        mock_finding.file_path = "app/auth.py"
        mock_finding.remediation = "Use parameterized queries"
        mock_finding.cwe_id = "CWE-89"

        mock_result = MagicMock(spec=ScanResult)
        mock_result.scanner = "semgrep"
        mock_result.findings = [mock_finding]

        mock_report = MagicMock()
        mock_report.scan_id = "scan-001"
        mock_report.project_name = "test-project"
        mock_report.status = "completed"
        mock_report.total_findings = 1
        mock_report.findings_by_severity = {"critical": 1}
        mock_report.scan_results = [mock_result]
        mock_report.ai_analysis = None
        mock_report.owner_id = "user-test-123"
        mock_report.created_at = None

        client = _setup_client()

        with patch.object(ScanReport, "find_one", AsyncMock(return_value=mock_report)):
            with patch("routes.ai_chat._call_ai_chat", AsyncMock(return_value="Fix SQL injection with parameterized queries")) as mock_ai:
                response = client.post(
                    "/api/ai/chat",
                    json={"scan_id": "scan-001", "message": "How to fix the SQL injection?"},
                )

        assert response.status_code == 200
        mock_ai.assert_called_once()
        call_kwargs = mock_ai.call_args[1]
        assert "scan_context" in call_kwargs
        context = call_kwargs["scan_context"]
        assert context["total_findings"] == 1
        assert context["findings"][0]["title"] == "SQL Injection"

    @pytest.mark.asyncio
    async def test_chat_empty_message_rejected(self):
        client = _setup_client()

        response = client.post(
            "/api/ai/chat",
            json={"scan_id": "scan-001", "message": "   "},
        )

        assert response.status_code == 422
