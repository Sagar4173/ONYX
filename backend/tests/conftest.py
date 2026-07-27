"""
Pytest Configuration and Fixtures
"""
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database connection for testing"""
    with patch("database.db_manager") as mock_db:
        mock_db.connected = True
        mock_db.connect = AsyncMock(return_value=True)
        mock_db.disconnect = AsyncMock()
        yield mock_db


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    from models.user import UserRole, UserStatus
    
    return MagicMock(
        id="test-user-id-123",
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE,
        email_verified=True,
        hashed_password="$2b$12$hashedpassword",
    )


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user for testing"""
    from models.user import UserRole, UserStatus
    
    return MagicMock(
        id="admin-user-id-456",
        email="admin@example.com",
        username="adminuser",
        full_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
        hashed_password="$2b$12$hashedpassword",
    )


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQtMTIzIn0.mock"


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Authorization headers with Bearer token"""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def sample_scan_result():
    """Sample scan result for testing"""
    return {
        "scan_id": "scan-123",
        "repository_url": "https://github.com/test/repo",
        "status": "completed",
        "findings": [
            {
                "id": "finding-1",
                "severity": "high",
                "title": "SQL Injection Vulnerability",
                "description": "Potential SQL injection found",
                "file": "app.py",
                "line": 42,
                "scanner": "semgrep"
            }
        ],
        "summary": {
            "total": 1,
            "critical": 0,
            "high": 1,
            "medium": 0,
            "low": 0
        }
    }


@pytest.fixture
def sample_project():
    """Sample project for testing"""
    return {
        "id": "project-123",
        "name": "Test Project",
        "description": "A test project",
        "repository_url": "https://github.com/test/repo",
        "default_branch": "main",
        "scan_enabled": True
    }


@pytest.fixture
def test_app():
    """Create a TestClient with mocked lifespan and no database."""
    from app import app

    # Override lifespan to a no-op to skip DB init
    @asynccontextmanager
    async def noop_lifespan(_app):
        yield
    app.router.lifespan_context = noop_lifespan

    # Clear any previous overrides
    app.dependency_overrides = {}

    with TestClient(app) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
def mock_scan_report():
    """Mock ScanReport class methods for integration tests."""
    from models.report import ScanReport, ScanStatus
    from datetime import datetime, timezone

    mock_report = MagicMock()
    mock_report.configure_mock(scan_id="scan-001")
    mock_report.status = ScanStatus.COMPLETED
    mock_report.project_name = "test-project"
    mock_report.total_findings = 50
    mock_report.findings_by_severity = {"critical": 2, "high": 5, "medium": 10, "low": 33, "info": 0}
    mock_report.scan_results = []
    mock_report.created_at = datetime.now(timezone.utc)
    mock_report.repository_url = "https://github.com/test/repo"
    mock_report.branch = "main"
    mock_report.commit_hash = "abc123"

    return mock_report


@pytest.fixture
def patch_auth(test_app):
    """Patch auth_service.get_current_user for testing auth-guarded endpoints.
    Yields a dict with user, admin flags for easy setup in tests."""

    from models.user import UserRole, UserStatus
    from unittest.mock import patch as _patch
    from routes.dependencies import auth_service

    mock_admin = MagicMock(
        id="admin-user-id-456",
        email="admin@example.com",
        username="adminuser",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    mock_user = MagicMock(
        id="test-user-id-123",
        email="test@example.com",
        username="testuser",
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )

    yield {
        "admin": mock_admin,
        "user": mock_user,
        "user_patch": _patch.object(auth_service, "get_current_user", new_callable=AsyncMock),
        "admin_patch": _patch.object(auth_service, "get_current_user", new_callable=AsyncMock),
    }


@pytest.fixture
def admin_auth(test_app):
    """Patch auth_service to return an admin user for all guarded endpoints."""
    from routes.dependencies import auth_service
    from models.user import UserRole, UserStatus

    mock_admin = MagicMock(
        id="admin-user-id-456",
        email="admin@example.com",
        username="adminuser",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    with patch.object(auth_service, "get_current_user", new_callable=AsyncMock, return_value=mock_admin):
        yield


@pytest.fixture
def user_auth(test_app):
    """Patch auth_service to return a non-admin user for all guarded endpoints."""
    from routes.dependencies import auth_service
    from models.user import UserRole, UserStatus

    mock_user = MagicMock(
        id="test-user-id-123",
        email="test@example.com",
        username="testuser",
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    with patch.object(auth_service, "get_current_user", new_callable=AsyncMock, return_value=mock_user):
        yield
