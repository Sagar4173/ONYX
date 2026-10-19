"""Fix runner: propose/approve with approval gate + dry-run (spec 4.3.4)."""
import asyncio
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
from services.ai.fix_runner import FixRunResult, approve_fix, get_fix_state, propose_fix
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
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner),
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
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner),
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


async def test_approve_rejects_path_changed_since_propose_and_restores_pending(
    scan_report, runner_env, monkeypatch
):
    """Gated content was screened for the propose-time path only: if the
    finding's path changed between propose and approve, approval must refuse
    and put the pending entry back (spec 4.3.4)."""
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")
    stored = dict(scan_report.metadata["pending_fixes"]["finding-001"])
    assert stored["file_path"] == "app/run.py"

    # rescan/metadata rewrite points the finding at another file mid-flight
    scan_report.scan_results[0].findings[0].file_path = "app/other.py"

    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner),
        patch("services.ai.fix_runner.auto_fix_service._create_branch_and_commit",
              return_value="onyx-auto-fix/z"),
        patch("services.ai.fix_runner.auto_fix_service._push_branch") as push,
        patch("services.ai.fix_runner.auto_fix_service._create_pr",
              AsyncMock(return_value=("https://x/pull/3", 3))),
    ):
        with pytest.raises(AutoFixError, match="Finding path changed since propose"):
            await approve_fix(scan_report, "finding-001")
        assert not push.called
        # pending restored (key-absent-only) so the user can retry
        pending_now = scan_report.metadata.get("pending_fixes", {})
        assert pending_now.get("finding-001") == stored

        # path restored -> the very same pending entry approves normally
        scan_report.scan_results[0].findings[0].file_path = "app/run.py"
        result = await approve_fix(scan_report, "finding-001")

    assert result.pr_url == "https://x/pull/3"
    assert "finding-001" not in scan_report.metadata.get("pending_fixes", {})


async def test_concurrent_approve_claims_pending_before_open_pr(scan_report, runner_env, monkeypatch):
    """Concurrent approves: the pending entry is claimed before any await into
    _open_pr, so exactly one call wins and the other gets "No pending fix"."""
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")  # pending stored
    assert "finding-001" in scan_report.metadata["pending_fixes"]

    pending_at_open_pr = []
    second_caller_arrived = asyncio.Event()

    async def _gated_open_pr(*args, **kwargs):
        pending_at_open_pr.append(
            "finding-001" in (scan_report.metadata.get("pending_fixes") or {})
        )
        if len(pending_at_open_pr) == 2:
            second_caller_arrived.set()
        try:
            await asyncio.wait_for(second_caller_arrived.wait(), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        return FixRunResult(
            status="pr_created", finding_id="finding-001", file_path="app/run.py",
            pr_url="https://x/pull/9", pr_number=9,
        )

    with patch("services.ai.fix_runner._open_pr", new=_gated_open_pr):
        results = await asyncio.gather(
            approve_fix(scan_report, "finding-001"),
            approve_fix(scan_report, "finding-001"),
            return_exceptions=True,
        )

    wins = [r for r in results if isinstance(r, FixRunResult)]
    losses = [r for r in results if isinstance(r, AutoFixError)]
    assert len(wins) == 1, results
    assert len(losses) == 1 and "No pending fix" in str(losses[0]), results
    assert pending_at_open_pr == [False], pending_at_open_pr
    assert "finding-001" not in (scan_report.metadata.get("pending_fixes") or {})


def test_get_fix_state_none(scan_report):
    assert get_fix_state(scan_report, "finding-001") == {
        "status": "none",
        "finding_id": "finding-001",
    }


def test_get_fix_state_pending_returns_safe_subset(scan_report):
    scan_report.metadata = {
        "pending_fixes": {
            "finding-001": {
                "file_path": "app/run.py",
                "patched_content": GOOD,
                "base_sha": "sha",
                "diff": "--- a\n+++ b\n",
                "model_used": "groq/m",
                "created_at": "2026-10-19T00:00:00+00:00",
            }
        }
    }
    state = get_fix_state(scan_report, "finding-001")
    assert state == {
        "status": "awaiting_approval",
        "finding_id": "finding-001",
        "file_path": "app/run.py",
        "diff": "--- a\n+++ b\n",
        "model_used": "groq/m",
        "created_at": "2026-10-19T00:00:00+00:00",
    }
    assert "patched_content" not in state and "base_sha" not in state


def test_get_fix_state_outcome_pr_created(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "id": "finding-001",
                "file_path": "app/run.py",
                "fix_pr_url": "https://x/pull/1",
                "fix_status": "pr_created",
            }
        ]
    }
    assert get_fix_state(scan_report, "finding-001") == {
        "status": "pr_created",
        "finding_id": "finding-001",
        "file_path": "app/run.py",
        "pr_url": "https://x/pull/1",
    }


def test_get_fix_state_outcome_wins_over_pending(scan_report):
    scan_report.metadata = {
        "findings": [
            {"id": "finding-001", "fix_pr_url": "https://x/pull/2", "fix_status": "verified"}
        ],
        "pending_fixes": {"finding-001": {"diff": "old", "file_path": "app/run.py"}},
    }
    state = get_fix_state(scan_report, "finding-001")
    assert state["status"] == "verified"
    assert state["pr_url"] == "https://x/pull/2"


from services.ai.fix_runner import verification_markdown, verify_fix


async def test_verify_fix_finding_absent_means_verified(finding):
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={
        "total_findings": 3,
        # real scanner shape: rule_id + file_path, no id field
        "detailed_findings": [{"rule_id": "B608", "file_path": "other/x.py"}],
    })
    with patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner):
        v = await verify_fix(repo_url="https://github.com/o/r", branch="onyx-auto-fix/b", finding=finding)
    assert v["verified"] is True and v["total_findings"] == 3
    assert v["remaining"] == []


async def test_verify_fix_finding_still_present_means_unverified(finding):
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={
        "total_findings": 4,
        # real scanner shape: rule_id + file_path, no id field
        "detailed_findings": [
            {"rule_id": "B608", "file_path": "app/run.py"},
            {"rule_id": "B608", "file_path": "/abs/clone/app/run.py"},
        ],
    })
    with patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner):
        v = await verify_fix(repo_url="https://github.com/o/r", branch="b", finding=finding)
    assert v["verified"] is False
    # evidence strings, not ids (scanner dicts have no id)
    assert v["remaining"] == ["B608 at app/run.py", "B608 at /abs/clone/app/run.py"]


async def test_verify_fix_scanner_error_returns_unknown(finding):
    scanner = MagicMock()
    # 12-char token: gateway _scrub only redacts ghp_[A-Za-z0-9]{10,}
    scanner.scan_repository = AsyncMock(side_effect=RuntimeError("clone failed ghp_ABCDEFGHIJK"))
    with patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner):
        v = await verify_fix(repo_url="https://github.com/o/r", branch="b", finding=finding)
    assert v["verified"] is None
    assert "REDACTED" in v["error"]  # token scrubbed


def test_verification_markdown_covers_all_states():
    assert "Verified" in verification_markdown({"verified": True, "total_findings": 0})
    assert "Not verified" in verification_markdown({"verified": False, "total_findings": 2, "remaining": ["f1"]})
    assert "Unknown" in verification_markdown({"verified": None, "error": "x"})


async def test_open_pr_records_verification_and_status(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", False)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    # metadata.findings mirrors the raw dict copy written by process_real_scan
    scan_report.metadata = {"findings": [{"id": "finding-001", "title": "Shell injection"}]}
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={
        "total_findings": 0,
        "detailed_findings": [{"rule_id": "OTHER", "file_path": "elsewhere.py", "id": "fx"}],
    })
    with (
        patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner),
        patch("services.ai.fix_runner.auto_fix_service._create_branch_and_commit",
              return_value="onyx-auto-fix/v"),
        patch("services.ai.fix_runner.auto_fix_service._push_branch"),
        patch("services.ai.fix_runner.auto_fix_service._create_pr",
              AsyncMock(return_value=("https://x/pull/9", 9))) as pr,
    ):
        result = await propose_fix(scan_report, "finding-001")
    assert result.status == "verified"
    assert result.verification["verified"] is True
    assert "Verification" in pr.await_args.kwargs["body_extra"]
    entry = scan_report.metadata["findings"][0]
    assert entry["fix_status"] == "verified"
    assert entry["fix_pr_url"] == "https://x/pull/9"
