from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
