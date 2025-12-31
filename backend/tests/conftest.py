"""
Pytest Configuration and Fixtures
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the FastAPI app
import sys
from pathlib import Path
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
