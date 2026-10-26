import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from git.exc import GitCommandError

from models.report import (
    GitMetadata,
    ScannerType,
    ScanReport,
    ScanResult,
    ScanStatus,
    SeverityLevel,
    VulnerabilityFinding,
)
from services.scm.auto_fix_service import AutoFixError, AutoFixService


@pytest.fixture
def finding():
    return VulnerabilityFinding(
        id="finding-001",
        scanner=ScannerType.SEMGREP,
        rule_id="rule-1",
        title="SQL Injection",
        description="SQL injection in login endpoint",
        severity=SeverityLevel.CRITICAL,
        file_path="app/auth.py",
        line_start=10,
        line_end=12,
        code_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        remediation="Use parameterized queries",
        remediation_code="cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
        fix_effort="low",
    )


@pytest.fixture
def scan_result(finding):
    return ScanResult(
        scanner=ScannerType.SEMGREP,
        status=ScanStatus.COMPLETED,
        findings=[finding],
    )


@pytest.fixture
def scan_report(scan_result):
    sr = MagicMock(spec=ScanReport)
    sr.project_name = "test-repo"
    sr.scan_id = "scan-001"
    sr.user_id = "user-1"
    sr.project_id = "proj-1"
    sr.total_findings = 1
    sr.scan_results = [scan_result]
    sr.git_metadata = GitMetadata(
        repository_url="https://github.com/owner/test-repo",
        branch="main",
        commit_hash="abc123",
        event_type="push",
    )
    sr.metadata = {}
    sr.save = AsyncMock()
    return sr


@pytest.fixture
def service():
    return AutoFixService()


class TestFindFinding:
    def test_finds_existing_finding(self, service, scan_report):
        result = service._find_finding(scan_report, "finding-001")
        assert result is not None
        assert result.id == "finding-001"

    def test_returns_none_for_missing(self, service, scan_report):
        result = service._find_finding(scan_report, "nonexistent")
        assert result is None

    def test_returns_none_for_empty_results(self, service, scan_report):
        scan_report.scan_results = []
        result = service._find_finding(scan_report, "finding-001")
        assert result is None


class TestDetectPlatform:
    def test_github(self, service):
        assert service._detect_platform("https://github.com/owner/repo") == "github"

    def test_gitlab(self, service):
        assert service._detect_platform("https://gitlab.com/owner/repo") == "gitlab"

    def test_bitbucket(self, service):
        assert service._detect_platform("https://bitbucket.org/owner/repo") == "bitbucket"

    def test_unsupported(self, service):
        with pytest.raises(AutoFixError):
            service._detect_platform("https://example.com/owner/repo")


class TestParseRepoInfo:
    def test_standard_url(self, service):
        owner, repo = service._parse_repo_info("https://github.com/owner/my-repo")
        assert owner == "owner"
        assert repo == "my-repo"

    def test_with_git_suffix(self, service):
        owner, repo = service._parse_repo_info("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"

    def test_too_few_parts(self, service):
        with pytest.raises(AutoFixError):
            service._parse_repo_info("https://github.com/single")


def _mock_httpx_client(status_code, text):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


class TestCredentialHygiene:
    def test_clone_failure_message_is_generic(self, service, tmp_path, caplog):
        secret_url = "https://ghp_leakedtoken123456@github.com/owner/repo.git"
        error = GitCommandError(
            "git clone", 128, stderr=f"fatal: unable to access '{secret_url}': 403"
        )
        with (
            patch("git.Repo.clone_from", side_effect=error),
            patch(
                "services.scm.auto_fix_service.tempfile.mkdtemp",
                return_value=str(tmp_path / "clone"),
            ),
            caplog.at_level(logging.WARNING),
        ):
            with pytest.raises(AutoFixError) as excinfo:
                service._clone_repo("https://github.com/owner/repo.git", "main", None)

        message = str(excinfo.value)
        assert message == "Git clone failed - check repository access and try again"
        assert "ghp_leakedtoken123456" not in message
        assert secret_url not in message
        assert "ghp_leakedtoken123456" not in caplog.text
        assert "[REDACTED]" in caplog.text

    def test_push_failure_message_is_generic(self, service, caplog):
        secret_url = "https://ghp_leakedtoken123456@github.com/owner/repo.git"
        error = GitCommandError(
            "git push", 128, stderr=f"fatal: authentication failed for '{secret_url}'"
        )
        repo = MagicMock()
        repo.remote.return_value.push.side_effect = error
        with patch("git.Repo", return_value=repo), caplog.at_level(logging.WARNING):
            with pytest.raises(AutoFixError) as excinfo:
                service._push_branch(
                    "tmp", "branch", None, "https://github.com/owner/repo.git"
                )

        message = str(excinfo.value)
        assert message == "Git push failed - check repository access and try again"
        assert "ghp_leakedtoken123456" not in message
        assert "ghp_leakedtoken123456" not in caplog.text
        assert "[REDACTED]" in caplog.text

    @pytest.mark.asyncio
    async def test_github_pr_failure_hides_response_body(self, service, caplog):
        context = _mock_httpx_client(
            401, "token ghp_leakedtoken123456 is invalid"
        )
        with patch(
            "services.scm.auto_fix_service.httpx.AsyncClient", return_value=context
        ):
            with caplog.at_level(logging.WARNING):
                with pytest.raises(AutoFixError) as excinfo:
                    await service._create_github_pr(
                        "owner", "repo", "main", "branch", "title", "body", "ghp_token"
                    )

        message = str(excinfo.value)
        assert message == "GitHub PR creation failed (HTTP 401)"
        assert "ghp_leakedtoken123456" not in message
        assert "ghp_leakedtoken123456" not in caplog.text
        assert "[REDACTED]" in caplog.text

    @pytest.mark.asyncio
    async def test_gitlab_mr_failure_hides_response_body(self, service, caplog):
        context = _mock_httpx_client(
            500, "glpat-leakedtoken1234567890 rejected"
        )
        with patch(
            "services.scm.auto_fix_service.httpx.AsyncClient", return_value=context
        ):
            with caplog.at_level(logging.WARNING):
                with pytest.raises(AutoFixError) as excinfo:
                    await service._create_gitlab_pr(
                        "https://gitlab.com/owner/repo.git",
                        "main",
                        "branch",
                        "title",
                        "body",
                        "glpat-token",
                    )

        message = str(excinfo.value)
        assert message == "GitLab MR creation failed (HTTP 500)"
        assert "glpat-leakedtoken1234567890" not in message
        assert "glpat-leakedtoken1234567890" not in caplog.text
        assert "[REDACTED]" in caplog.text

    def test_detect_platform_error_omits_url(self, service):
        url = "https://ghp_leakedtoken123456@example.com/owner/repo.git"
        with pytest.raises(AutoFixError) as excinfo:
            service._detect_platform(url)

        assert str(excinfo.value) == "Unsupported SCM platform"
        assert "ghp_leakedtoken123456" not in str(excinfo.value)

    def test_parse_repo_info_error_omits_url(self, service):
        url = "https://ghp_leakedtoken123456@github.com/single"
        with pytest.raises(AutoFixError) as excinfo:
            service._parse_repo_info(url)

        assert str(excinfo.value) == "Could not parse repository owner/name from URL"
        assert "ghp_leakedtoken123456" not in str(excinfo.value)

    def test_clone_injects_token_for_https(self, service, tmp_path):
        clone = MagicMock()
        local_path = str(tmp_path / "clone")
        with (
            patch("git.Repo.clone_from", clone),
            patch(
                "services.scm.auto_fix_service.tempfile.mkdtemp",
                return_value=local_path,
            ),
        ):
            result = service._clone_repo(
                "https://github.com/owner/repo.git", "main", "ghp_token"
            )

        assert result == local_path
        clone.assert_called_once_with(
            "https://ghp_token@github.com/owner/repo.git",
            local_path,
            branch="main",
            depth=1,
        )

    @pytest.mark.parametrize(
        "url",
        [
            "ssh://git@github.com/owner/repo.git",
            "git@github.com:owner/repo.git",
        ],
    )
    def test_clone_does_not_rewrite_non_http_urls(self, service, tmp_path, url):
        clone = MagicMock()
        local_path = str(tmp_path / "clone")
        with (
            patch("git.Repo.clone_from", clone),
            patch(
                "services.scm.auto_fix_service.tempfile.mkdtemp",
                return_value=local_path,
            ),
        ):
            service._clone_repo(url, "main", "ghp_token")

        clone.assert_called_once_with(
            url, local_path, branch="main", depth=1
        )

    def test_push_injects_token_only_for_https(self, service):
        repo = MagicMock()
        repo.remote.return_value.push = MagicMock()
        with patch("git.Repo", return_value=repo):
            service._push_branch(
                "tmp", "branch", "ghp_token", "https://github.com/owner/repo.git"
            )
        repo.remote.return_value.push.assert_called_once_with(
            refspec="branch:branch",
            push_url="https://ghp_token@github.com/owner/repo.git",
        )

        repo = MagicMock()
        repo.remote.return_value.push = MagicMock()
        with patch("git.Repo", return_value=repo):
            service._push_branch(
                "tmp", "branch", "ghp_token", "ssh://git@github.com/owner/repo.git"
            )
        repo.remote.return_value.push.assert_called_once_with(
            refspec="branch:branch",
            push_url="ssh://git@github.com/owner/repo.git",
        )


class TestOpenPrForPatchPath:
    @pytest.mark.asyncio
    async def test_branch_push_pr_sequence(self, service, scan_report, finding, tmp_path):
        (tmp_path / "app").mkdir()
        target = tmp_path / "app" / "auth.py"
        target.write_text("x = 1\n", encoding="utf-8")
        with (
            patch.object(service, "_resolve_token", AsyncMock(return_value="ghp_token")),
            patch.object(service, "_create_branch_and_commit", return_value="onyx-auto-fix/b1"),
            patch.object(service, "_push_branch"),
            patch.object(service, "_create_pr", AsyncMock(return_value=("https://x/pull/1", 1))) as pr,
        ):
            # simulate the runner writing the file, then the service sequence
            target.write_text("x = 2\n", encoding="utf-8")
            branch_name = service._create_branch_and_commit(
                local_path=str(tmp_path), file_path="app/auth.py",
                finding=finding, branch="main",
            )
            service._push_branch(str(tmp_path), branch_name, "ghp_token", "https://github.com/o/r")
            url, num = await service._create_pr(
                repo_url="https://github.com/o/r", branch="main", branch_name=branch_name,
                finding=finding, token="t", scan_report=scan_report, body_extra="## Verification\n- ok",
            )
        assert url == "https://x/pull/1"
        assert pr.await_args.kwargs["body_extra"] == "## Verification\n- ok"
