import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.report import (
    GitMetadata,
    ScanReport,
    ScanResult,
    ScannerType,
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


class TestApplyFix:
    def _create_file(self, tmpdir, lines=15):
        file_path = os.path.join(tmpdir, "app/auth.py")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            for i in range(1, lines + 1):
                f.write(f"line{i}\n")
        return file_path

    def test_successful_patch(self, service, finding):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_file(tmpdir)
            finding.file_path = "app/auth.py"
            result = service._apply_fix(tmpdir, finding)

            assert result == "app/auth.py"
            file_path = os.path.join(tmpdir, "app/auth.py")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))" in content
            assert "line1" in content
            assert "line9" in content
            assert "line13" in content

    def test_file_not_found(self, service, finding):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(AutoFixError, match="File not found"):
                service._apply_fix(tmpdir, finding)

    def test_line_range_out_of_bounds(self, service, finding):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "app/auth.py")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("line1\n")
            finding.file_path = "app/auth.py"
            finding.line_start = 10
            with pytest.raises(AutoFixError, match="Line range out of bounds"):
                service._apply_fix(tmpdir, finding)


class TestCreateAutoFixPr:
    @pytest.mark.asyncio
    async def test_full_success(self, service, scan_report, finding):
        with (
            patch.object(service, "_find_finding", return_value=finding),
            patch.object(service, "_resolve_token", AsyncMock(return_value="ghp_token")),
            patch.object(service, "_clone_repo", return_value="/tmp/fake-clone"),
            patch.object(service, "_apply_fix", return_value="app/auth.py"),
            patch.object(service, "_create_branch_and_commit", return_value="onyx-auto-fix/branch-1"),
            patch.object(service, "_push_branch"),
            patch.object(service, "_create_pr", AsyncMock(return_value=("https://github.com/owner/repo/pull/1", 1))),
        ):
            result = await service.create_auto_fix_pr(scan_report, "finding-001")

        assert result["pr_url"] == "https://github.com/owner/repo/pull/1"
        assert result["pr_number"] == 1
        assert result["branch"] == "onyx-auto-fix/branch-1"
        assert result["finding_id"] == "finding-001"
        assert result["file_path"] == "app/auth.py"

    @pytest.mark.asyncio
    async def test_finding_not_found(self, service, scan_report):
        with patch.object(service, "_find_finding", return_value=None):
            with pytest.raises(AutoFixError, match="not found"):
                await service.create_auto_fix_pr(scan_report, "nonexistent")

    @pytest.mark.asyncio
    async def test_no_remediation_code(self, service, scan_report, finding):
        finding.remediation_code = None
        with patch.object(service, "_find_finding", return_value=finding):
            with pytest.raises(AutoFixError, match="no remediation code"):
                await service.create_auto_fix_pr(scan_report, "finding-001")

    @pytest.mark.asyncio
    async def test_cleanup_on_clone_failure(self, service, scan_report, finding):
        with (
            patch.object(service, "_find_finding", return_value=finding),
            patch.object(service, "_resolve_token", AsyncMock(return_value="token")),
            patch.object(service, "_clone_repo", side_effect=AutoFixError("clone failed")),
        ):
            with pytest.raises(AutoFixError, match="clone failed"):
                await service.create_auto_fix_pr(scan_report, "finding-001")

    @pytest.mark.asyncio
    async def test_no_token_available(self, service, scan_report, finding):
        with (
            patch.object(service, "_find_finding", return_value=finding),
            patch.object(service, "_resolve_token", AsyncMock(return_value=None)),
            patch.object(service, "_clone_repo", return_value="/tmp/fake"),
            patch.object(service, "_apply_fix", return_value="app/auth.py"),
            patch.object(service, "_create_branch_and_commit", return_value="branch"),
            patch.object(service, "_push_branch"),
        ):
            with pytest.raises(AutoFixError, match="No SCM token"):
                await service.create_auto_fix_pr(scan_report, "finding-001")
