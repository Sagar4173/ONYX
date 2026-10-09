"""Fix runner: propose/approve with approval gate + dry-run (spec 4.3.4)."""
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

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
from services.ai.fix_agent import FixAgentError, FixAgentResult, PatchProposal
from services.ai.fix_gates import GateReport
from services.ai.fix_runner import approve_fix, propose_fix
from services.scm.auto_fix_service import AutoFixError

GOOD = "import os\nimport shlex\n\ndef run(q):\n    return os.popen(shlex.quote(q))\n"


@pytest.fixture
def finding():
    return VulnerabilityFinding(
        id="finding-001", scanner=ScannerType.SEMGREP, rule_id="B608",
        title="Shell injection", description="popen", severity=SeverityLevel.HIGH,
        file_path="app/run.py", line_start=4, line_end=4,
    )


@pytest.fixture
def scan_report(finding):
    sr = MagicMock(spec=ScanReport)
    sr.scan_id = "scan-001"
    sr.project_id = None
    sr.scan_results = [ScanResult(scanner=ScannerType.SEMGREP, status=ScanStatus.COMPLETED, findings=[finding])]
    sr.git_metadata = GitMetadata(repository_url="https://github.com/owner/repo", branch="main",
                                  commit_hash="abc", event_type="push")
    sr.metadata = {}
    sr.save = AsyncMock()
    return sr


@pytest.fixture
def workspace(tmp_path):
    from git import Repo

    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "run.py").write_text(
        "import os\n\ndef run(query):\n    return os.popen(query)\n", encoding="utf-8"
    )
    repo = Repo.init(tmp_path)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "t")
        cw.set_value("user", "email", "t@example.com")
    repo.index.add(["app/run.py"])
    repo.index.commit("init")
    return tmp_path


def _agent_result():
    return FixAgentResult(
        proposal=PatchProposal(file_path="app/run.py", line_start=1, line_end=4,
                               patched_content=GOOD, rationale="quote"),
        gate_report=GateReport(passed=True, failures=[], diff="--- a\n+++ b\n",
                               added_lines=2, removed_lines=2),
        provider="groq", model="m", usage={"requests": 1},
    )


@pytest.fixture
def runner_env(workspace, monkeypatch):
    def _fake_clone(*args, **kwargs):
        # fresh working copy per call: real clone semantics, so the runner's
        # rmtree cleanup never destroys the shared fixture workspace
        dst = str(workspace.parent / f"clone-{uuid4().hex}")
        shutil.copytree(workspace, dst)
        return dst

    monkeypatch.setattr("services.ai.fix_runner.auto_fix_service._clone_repo", _fake_clone)
    monkeypatch.setattr("services.ai.fix_runner.auto_fix_service._resolve_token",
                        AsyncMock(return_value="tok"))
    monkeypatch.setattr("services.ai.fix_runner.run_fix_agent",
                        AsyncMock(return_value=_agent_result()))
    monkeypatch.setattr("services.ai.fix_runner._guidance_for", AsyncMock(return_value=""))
    return workspace


async def test_propose_default_approval_stores_pending(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", True)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    result = await propose_fix(scan_report, "finding-001")
    assert result.status == "awaiting_approval"
    pending = scan_report.metadata["pending_fixes"]["finding-001"]
    assert pending["patched_content"] == GOOD
    assert pending["base_sha"]
    scan_report.save.assert_awaited()


async def test_propose_dry_run_returns_diff_without_persisting(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", True)
    result = await propose_fix(scan_report, "finding-001")
    assert result.status == "dry_run"
    assert result.diff
    assert "pending_fixes" not in (scan_report.metadata or {})
    scan_report.save.assert_not_awaited()


async def test_propose_approval_off_opens_pr_immediately(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", False)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    with (
        patch("services.ai.fix_runner.auto_fix_service._create_branch_and_commit",
              return_value="onyx-auto-fix/x"),
        patch("services.ai.fix_runner.auto_fix_service._push_branch"),
        patch("services.ai.fix_runner.auto_fix_service._create_pr",
              AsyncMock(return_value=("https://x/pull/1", 1))),
    ):
        result = await propose_fix(scan_report, "finding-001")
    assert result.status in ("pr_created", "verified")
    assert result.pr_url == "https://x/pull/1"


async def test_propose_unknown_finding_raises(scan_report, runner_env):
    with pytest.raises(AutoFixError, match="not found"):
        await propose_fix(scan_report, "nope")


async def test_propose_missing_file_path_raises(scan_report, runner_env):
    scan_report.scan_results[0].findings[0].file_path = ""
    with pytest.raises(AutoFixError, match="no file path"):
        await propose_fix(scan_report, "finding-001")


async def test_propose_agent_error_becomes_autofix_error(scan_report, runner_env, monkeypatch):
    monkeypatch.setattr("services.ai.fix_runner.run_fix_agent",
                        AsyncMock(side_effect=FixAgentError("gates failed")))
    with pytest.raises(AutoFixError, match="gates failed"):
        await propose_fix(scan_report, "finding-001")


async def test_approve_success_pushes_and_clears_pending(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")  # approval default ON -> pending stored
    with (
        patch("services.ai.fix_runner.auto_fix_service._create_branch_and_commit",
              return_value="onyx-auto-fix/y"),
        patch("services.ai.fix_runner.auto_fix_service._push_branch") as push,
        patch("services.ai.fix_runner.auto_fix_service._create_pr",
              AsyncMock(return_value=("https://x/pull/2", 2))),
    ):
        result = await approve_fix(scan_report, "finding-001")
    assert result.pr_url == "https://x/pull/2"
    assert push.called
    assert "finding-001" not in scan_report.metadata.get("pending_fixes", {})


async def test_approve_without_pending_raises(scan_report, runner_env):
    with pytest.raises(AutoFixError, match="No pending fix"):
        await approve_fix(scan_report, "finding-001")


async def test_approve_refuses_when_dry_run_enabled(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", True)
    scan_report.metadata = {"pending_fixes": {"finding-001": {"base_sha": "x", "patched_content": GOOD}}}
    with pytest.raises(AutoFixError, match="DRY_RUN"):
        await approve_fix(scan_report, "finding-001")


async def test_approve_stale_base_sha_rejects(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")
    # advance the workspace by a new commit so the re-clone head differs
    from git import Repo
    repo = Repo(str(runner_env))
    (runner_env / "app" / "run.py").write_text("import os\n# advance\n", encoding="utf-8")
    repo.index.add(["app/run.py"])
    repo.index.commit("advance")
    with pytest.raises(AutoFixError, match="advanced since the fix"):
        await approve_fix(scan_report, "finding-001")
