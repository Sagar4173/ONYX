"""Credential-bearing repository URLs must be rejected at input boundaries or redacted."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import app
from models.base import ProjectCategory, ProjectPriority, ProjectStatus
from models.project import (
    Project,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    RepositoryConfigResponse,
)
from models.user import User
from routes.advanced_scanning.schemas import (
    ComprehensiveScanRequest,
    IaCScanRequest,
    SASTScanRequest,
    SuppressionRuleRequest,
)
from routes.dependencies import get_current_user
from routes.webhook.schemas import ScanRequest

CREDENTIAL_URL = "https://ghp_secret@github.com/owner/repo.git"
QUERY_CREDENTIAL_URL = "https://github.com/owner/repo.git?access_token=secret"
PASSWORD_QUERY_URL = "https://github.com/owner/repo.git?password=secret"
REDACTED_URL = "https://github.com/owner/repo.git"


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def _client():
    user = MagicMock(spec=User)
    user.id = "user-test-123"
    user.username = "tester"

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    return TestClient(app)


class TestScanRequestCredentials:
    def test_rejects_userinfo_credentials(self):
        with pytest.raises(ValidationError):
            ScanRequest(repository_url=CREDENTIAL_URL)

    @pytest.mark.parametrize(
        "url",
        [
            QUERY_CREDENTIAL_URL,
            PASSWORD_QUERY_URL,
            "https://github.com/owner/repo.git?oauth_token=secret",
            "https://github.com/owner/repo.git?access-token=secret",
            "https://github.com/owner/repo.git?client_secret=secret",
        ],
    )
    def test_rejects_query_credentials(self, url):
        with pytest.raises(ValidationError):
            ScanRequest(repository_url=url)

    def test_accepts_plain_repository_url(self):
        request = ScanRequest(repository_url=REDACTED_URL)
        assert str(request.repository_url).startswith(REDACTED_URL)


class TestAdvancedScanRequestCredentials:
    @pytest.mark.parametrize(
        "request_factory",
        [
            lambda url: ComprehensiveScanRequest(repository_url=url),
            lambda url: SASTScanRequest(repository_url=url),
            lambda url: IaCScanRequest(repository_url=url),
            lambda url: SuppressionRuleRequest(
                name="rule",
                description="rule",
                repository_url=url,
            ),
        ],
    )
    def test_rejects_userinfo_credentials(self, request_factory):
        with pytest.raises(ValidationError):
            request_factory(CREDENTIAL_URL)

    @pytest.mark.parametrize(
        "request_factory",
        [
            lambda url: ComprehensiveScanRequest(repository_url=url),
            lambda url: SASTScanRequest(repository_url=url),
            lambda url: IaCScanRequest(repository_url=url),
            lambda url: SuppressionRuleRequest(
                name="rule",
                description="rule",
                repository_url=url,
            ),
        ],
    )
    def test_accepts_plain_repository_url(self, request_factory):
        assert request_factory(REDACTED_URL)


class TestProjectRequestCredentials:
    def test_create_rejects_userinfo_credentials(self):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                name="test",
                repository={"url": CREDENTIAL_URL, "branch": "main"},
            )

    def test_update_rejects_userinfo_credentials(self):
        with pytest.raises(ValidationError):
            ProjectUpdateRequest(repository={"url": CREDENTIAL_URL})

    @pytest.mark.parametrize(
        "url",
        [
            "user:pass@git@github.com:owner/repo.git",
            "user:pass@github.com/owner/repo.git",
            PASSWORD_QUERY_URL,
        ],
    )
    def test_rejects_ambiguous_or_query_credentials(self, url):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                name="test",
                repository={"url": url, "branch": "main"},
            )

    def test_create_accepts_plain_repository_url(self):
        request = ProjectCreateRequest(
            name="test",
            repository={"url": REDACTED_URL, "branch": "main"},
        )
        assert request.repository.url == REDACTED_URL

    def test_create_accepts_ssh_username(self):
        request = ProjectCreateRequest(
            name="test",
            repository={"url": "ssh://deploy@example.com/owner/repo.git"},
        )
        assert request.repository.url == "ssh://deploy@example.com/owner/repo.git"


class TestProjectResponseRedaction:
    def test_repository_response_redacts_url(self):
        repository = RepositoryConfigResponse(
            url=CREDENTIAL_URL,
            branch="main",
            scan_paths=["/"],
            exclude_paths=[],
        )
        assert repository.url == REDACTED_URL

    def test_project_response_redacts_nested_url(self):
        response = ProjectResponse(
            id="project-1",
            name="test",
            description=None,
            category=ProjectCategory.OTHER,
            priority=ProjectPriority.MEDIUM,
            status=ProjectStatus.ACTIVE,
            repository={
                "url": CREDENTIAL_URL,
                "branch": "main",
                "scan_paths": ["/"],
                "exclude_paths": [],
            },
            scan_config={},
            owner_id="user-1",
            team_members=[],
            tags=[],
            stats={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert response.repository.url == REDACTED_URL

    def test_repository_response_redacts_ambiguous_credentials(self):
        repository = RepositoryConfigResponse(
            url="user:pass@git@github.com:owner/repo.git",
            branch="main",
            scan_paths=["/"],
            exclude_paths=[],
        )
        assert repository.url == "git@github.com:owner/repo.git"

    def test_project_summary_redacts_url(self):
        now = datetime.now(timezone.utc)
        project = SimpleNamespace(
            id="project-1",
            name="test",
            description=None,
            category=ProjectCategory.OTHER,
            priority=ProjectPriority.MEDIUM,
            status=ProjectStatus.ACTIVE,
            repository=SimpleNamespace(url=CREDENTIAL_URL),
            stats=SimpleNamespace(
                total_scans=0,
                last_scan_date=None,
                security_score=0,
                critical_vulnerabilities=0,
                high_vulnerabilities=0,
                medium_vulnerabilities=0,
                low_vulnerabilities=0,
            ),
            created_at=now,
            updated_at=now,
        )
        assert Project.to_dict_summary(project)["repository_url"] == REDACTED_URL


def test_validation_response_does_not_echo_credentials():
    client = _client()
    response = client.post(
        "/api/projects/",
        json={
            "name": "test",
            "repository": {
                "url": CREDENTIAL_URL,
                "branch": "main",
                "access_token": "ghp_nested_secret",
            },
        },
    )

    assert response.status_code == 422
    assert "ghp_secret" not in response.text
    assert "ghp_nested_secret" not in response.text
