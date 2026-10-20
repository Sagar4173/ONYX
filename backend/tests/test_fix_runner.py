"""Fix runner: propose/approve with approval gate + dry-run (spec 4.3.4)."""
import asyncio
import logging
import shutil
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from bson import ObjectId

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
from services.ai.fix_runner import (
    FixConflictError,
    FixRunResult,
    _MAX_CAS_ATTEMPTS,
    _cas_pending_map,
    _record_fix_outcome,
    _refresh_report,
    _store_pending,
    approve_fix,
    discard_pending,
    get_fix_state,
    propose_fix,
)
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


@pytest.fixture(autouse=True)
def _default_cas(monkeypatch):
    monkeypatch.setattr(
        "services.ai.fix_runner._cas_pending_map", AsyncMock(return_value=True)
    )


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


def _fake_collection(matched_count=1, modified_count=None):
    collection = MagicMock()
    result = SimpleNamespace(matched_count=matched_count)
    if modified_count is not None:
        result.modified_count = modified_count
    collection.update_one = AsyncMock(return_value=result)
    return collection


@pytest.fixture
def outcome_collection():
    return _fake_collection()


def _assert_outcome_update(collection, scan_report, *, status, pr_url):
    collection.update_one.assert_awaited_once()
    filter_doc, update_doc = collection.update_one.await_args.args
    assert filter_doc == {"_id": getattr(scan_report, "id", None)}
    assert update_doc == {"$set": {
        "metadata.findings.$[e].fix_status": status,
        "metadata.findings.$[e].fix_pr_url": pr_url,
    }}
    assert "array_filters" in collection.update_one.await_args.kwargs
    scan_report.save.assert_not_awaited()


async def test_cas_pending_map_expected_dict_matches_and_sets(scan_report):
    collection = _fake_collection()
    scan_report.id = "scan-oid"
    expected = {"finding.001": {"diff": "old"}}
    updated = {"finding.001": {"diff": "new"}}
    with patch.object(ScanReport, "get_motor_collection", return_value=collection):
        assert await _cas_pending_map(scan_report, expected, updated) is True
    filter_doc, update_doc = collection.update_one.await_args.args
    assert filter_doc["_id"] == "scan-oid"
    assert filter_doc["metadata.pending_fixes"] == expected
    assert update_doc == {"$set": {"metadata.pending_fixes": updated}}


async def test_cas_pending_map_expected_none_requires_absent_map(scan_report):
    collection = _fake_collection()
    updated = {"finding-001": {"diff": "d"}}
    with patch.object(ScanReport, "get_motor_collection", return_value=collection):
        assert await _cas_pending_map(scan_report, None, updated) is True
    filter_doc, update_doc = collection.update_one.await_args.args
    assert filter_doc["metadata.pending_fixes"] == {"$exists": False}
    assert update_doc == {"$set": {"metadata.pending_fixes": updated}}


async def test_cas_pending_map_empty_update_unsets(scan_report):
    collection = _fake_collection()
    expected = {"finding-001": {"diff": "d"}}
    with patch.object(ScanReport, "get_motor_collection", return_value=collection):
        assert await _cas_pending_map(scan_report, expected, {}) is True
    _, update_doc = collection.update_one.await_args.args
    assert update_doc == {"$unset": {"metadata.pending_fixes": ""}}


async def test_cas_pending_map_miss_returns_false(scan_report):
    collection = _fake_collection(matched_count=0)
    with patch.object(ScanReport, "get_motor_collection", return_value=collection):
        assert await _cas_pending_map(scan_report, None, {"x": {}}) is False


async def test_store_pending_retry_reads_refreshed_map(scan_report, monkeypatch):
    scan_report.id = ObjectId()
    fresh = MagicMock(spec=ScanReport)
    fresh.metadata = {"pending_fixes": {"other.finding": {"diff": "existing"}}}
    cas = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    get_mock = AsyncMock(return_value=fresh)
    with patch.object(ScanReport, "get", get_mock):
        await _store_pending(scan_report, "finding-001", {"diff": "new"})
    get_mock.assert_awaited_once_with(scan_report.id)
    assert cas.await_count == 2
    expected, updated = cas.await_args.args[1], cas.await_args.args[2]
    assert expected == {"other.finding": {"diff": "existing"}}
    assert updated["other.finding"] == {"diff": "existing"}
    assert updated["finding-001"] == {"diff": "new"}
    assert scan_report.metadata["pending_fixes"]["finding-001"] == {"diff": "new"}


async def test_propose_default_approval_stores_pending(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", True)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    result = await propose_fix(scan_report, "finding-001")
    assert result.status == "awaiting_approval"
    pending = scan_report.metadata["pending_fixes"]["finding-001"]
    assert pending["patched_content"] == GOOD
    assert pending["base_sha"]
    scan_report.save.assert_not_awaited()
    cas.assert_awaited_once()
    assert cas.await_args.args[0] is scan_report
    assert cas.await_args.args[1] is None
    assert cas.await_args.args[2]["finding-001"]["patched_content"] == GOOD


async def test_propose_retries_cas_then_stores(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", True)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    cas = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    result = await propose_fix(scan_report, "finding-001")
    assert result.status == "awaiting_approval"
    assert cas.await_count == 2
    assert scan_report.metadata["pending_fixes"]["finding-001"]["patched_content"] == GOOD
    scan_report.save.assert_not_awaited()


async def test_propose_cas_exhaustion_raises(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", True)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    cas = AsyncMock(return_value=False)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    with pytest.raises(AutoFixError, match="Could not persist"):
        await propose_fix(scan_report, "finding-001")
    assert cas.await_count == _MAX_CAS_ATTEMPTS
    assert "pending_fixes" not in scan_report.metadata
    scan_report.save.assert_not_awaited()


async def test_propose_refuses_fresh_approval_claim(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", True)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    entry = {
        "file_path": "app/run.py",
        "diff": "old",
        "_approving": True,
        "_approving_at": time.time(),
    }
    scan_report.metadata = {"pending_fixes": {"finding-001": entry}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    with pytest.raises(FixConflictError, match="already in progress"):
        await propose_fix(scan_report, "finding-001")
    cas.assert_not_awaited()
    assert scan_report.metadata["pending_fixes"]["finding-001"] == entry
    scan_report.save.assert_not_awaited()


async def test_propose_replaces_stale_approval_claim(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", True)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    entry = {
        "file_path": "app/run.py",
        "diff": "old",
        "_approving": True,
        "_approving_at": time.time() - 901,
    }
    scan_report.metadata = {"pending_fixes": {"finding-001": entry}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    result = await propose_fix(scan_report, "finding-001")
    assert result.status == "awaiting_approval"
    pending = scan_report.metadata["pending_fixes"]["finding-001"]
    assert pending["patched_content"] == GOOD
    assert "_approving" not in pending
    assert "_approving_at" not in pending
    cas.assert_awaited_once()
    assert cas.await_args.args[1] == {"finding-001": entry}
    assert cas.await_args.args[2]["finding-001"] == pending
    scan_report.save.assert_not_awaited()


async def test_propose_dry_run_returns_diff_without_persisting(scan_report, runner_env, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", True)
    result = await propose_fix(scan_report, "finding-001")
    assert result.status == "dry_run"
    assert result.diff
    assert "pending_fixes" not in (scan_report.metadata or {})
    scan_report.save.assert_not_awaited()


async def test_propose_approval_off_opens_pr_immediately(
    scan_report, runner_env, monkeypatch, outcome_collection
):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", False)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection),
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


async def test_approve_success_pushes_and_clears_pending(
    scan_report, runner_env, monkeypatch, outcome_collection
):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")  # approval default ON -> pending stored
    original = dict(scan_report.metadata["pending_fixes"])
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection),
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
    scan_report.save.assert_not_awaited()
    assert cas.await_count == 2
    claim = cas.await_args_list[0].args
    assert claim[0] is scan_report
    assert claim[1] == original
    marked = claim[2]
    assert marked["finding-001"]["_approving"] is True
    assert "_approving_at" in marked["finding-001"]
    final = cas.await_args_list[1].args
    assert final[1] == marked
    assert final[2] == {}


async def test_approve_removal_failure_after_pr_does_not_restore_pending(
    scan_report, runner_env, monkeypatch
):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")
    cas = AsyncMock(side_effect=[True, RuntimeError("db down")])
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    opened = FixRunResult(
        status="pr_created",
        finding_id="finding-001",
        file_path="app/run.py",
        pr_url="https://x/pull/13",
        pr_number=13,
    )
    with patch("services.ai.fix_runner._open_pr", AsyncMock(return_value=opened)):
        result = await approve_fix(scan_report, "finding-001")
    assert result is opened
    assert cas.await_count == 2
    pending = scan_report.metadata["pending_fixes"]["finding-001"]
    assert pending["_approving"] is True
    assert "_approving_at" in pending
    scan_report.save.assert_not_awaited()


async def test_approve_without_pending_raises(scan_report, runner_env):
    with pytest.raises(AutoFixError, match="No pending fix"):
        await approve_fix(scan_report, "finding-001")


async def test_approve_fresh_claim_raises_in_progress(scan_report, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    scan_report.metadata = {"pending_fixes": {"finding-001": {
        "file_path": "app/run.py", "patched_content": GOOD, "base_sha": "sha",
        "_approving": True, "_approving_at": time.time(),
    }}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    with pytest.raises(AutoFixError, match="Approval already in progress"):
        await approve_fix(scan_report, "finding-001")
    cas.assert_not_awaited()


async def test_approve_stale_claim_is_reclaimed(
    scan_report, runner_env, monkeypatch, outcome_collection
):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")
    entry = scan_report.metadata["pending_fixes"]["finding-001"]
    entry["_approving"] = True
    entry["_approving_at"] = time.time() - 901
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection),
        patch("services.scanning.scanners.real_scanner.RealSecurityScanner", return_value=scanner),
        patch("services.ai.fix_runner.auto_fix_service._create_branch_and_commit",
              return_value="onyx-auto-fix/stale"),
        patch("services.ai.fix_runner.auto_fix_service._push_branch"),
        patch("services.ai.fix_runner.auto_fix_service._create_pr",
              AsyncMock(return_value=("https://x/pull/12", 12))),
    ):
        result = await approve_fix(scan_report, "finding-001")
    assert result.pr_url == "https://x/pull/12"
    assert "finding-001" not in scan_report.metadata.get("pending_fixes", {})


async def test_approve_claim_cas_exhaustion_raises_race(scan_report, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    scan_report.metadata = {"pending_fixes": {"finding-001": {
        "file_path": "app/run.py", "patched_content": GOOD, "base_sha": "sha",
    }}}
    cas = AsyncMock(return_value=False)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    open_pr = AsyncMock()
    with patch("services.ai.fix_runner._open_pr", new=open_pr):
        with pytest.raises(AutoFixError, match="No pending fix"):
            await approve_fix(scan_report, "finding-001")
    assert cas.await_count == _MAX_CAS_ATTEMPTS
    open_pr.assert_not_awaited()


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
    scan_report, runner_env, monkeypatch, outcome_collection
):
    """Gated content was screened for the propose-time path only: if the
    finding's path changed between propose and approve, approval must refuse
    and put the pending entry back (spec 4.3.4)."""
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")
    original = dict(scan_report.metadata["pending_fixes"])
    stored = dict(original["finding-001"])
    assert stored["file_path"] == "app/run.py"
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)

    # rescan/metadata rewrite points the finding at another file mid-flight
    scan_report.scan_results[0].findings[0].file_path = "app/other.py"

    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={"total_findings": 0, "detailed_findings": []})
    with (
        patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection),
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
        assert "_approving" not in pending_now["finding-001"]
        assert "_approving_at" not in pending_now["finding-001"]
        assert cas.await_count == 2
        claim = cas.await_args_list[0].args
        marked = claim[2]
        assert claim[1] == original
        assert marked["finding-001"]["_approving"] is True
        release = cas.await_args_list[1].args
        assert release[1] == marked
        assert release[2] == original

        # path restored -> the very same pending entry approves normally
        scan_report.scan_results[0].findings[0].file_path = "app/run.py"
        result = await approve_fix(scan_report, "finding-001")

    assert result.pr_url == "https://x/pull/3"
    assert "finding-001" not in scan_report.metadata.get("pending_fixes", {})


async def test_approve_release_never_clobbers_newer_map(
    scan_report, runner_env, monkeypatch
):
    """If the release CAS misses, a newer map won: leave it untouched."""
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    await propose_fix(scan_report, "finding-001")
    original = dict(scan_report.metadata["pending_fixes"])
    cas = AsyncMock(side_effect=[True, False])
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    scan_report.scan_results[0].findings[0].file_path = "app/other.py"

    with pytest.raises(AutoFixError, match="Finding path changed since propose"):
        await approve_fix(scan_report, "finding-001")

    assert cas.await_count == 2
    claim = cas.await_args_list[0].args
    marked = claim[2]
    assert claim[1] == original
    release = cas.await_args_list[1].args
    assert release[1] == marked
    assert release[2] == original
    # release missed, so the in-memory mirror stays at the claimed state
    assert scan_report.metadata["pending_fixes"]["finding-001"] == marked["finding-001"]
    assert scan_report.metadata["pending_fixes"]["finding-001"]["_approving"] is True


async def test_concurrent_approve_claims_pending_before_open_pr(scan_report, runner_env, monkeypatch):
    """Concurrent approves: the pending entry is claimed before any await into
    _open_pr, so exactly one call wins and the other sees the fresh marker."""
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
    assert len(losses) == 1 and "Approval already in progress" in str(losses[0]), results
    assert pending_at_open_pr == [True], pending_at_open_pr
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


def test_get_fix_state_outcome_pr_created_raw_shape(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "file_path": "app/run.py",
                "title": "Shell injection",
                "fix_pr_url": "https://x/pull/3",
                "fix_status": "pr_created",
            }
        ]
    }
    assert get_fix_state(scan_report, "finding-001") == {
        "status": "pr_created",
        "finding_id": "finding-001",
        "file_path": "app/run.py",
        "pr_url": "https://x/pull/3",
    }


def test_get_fix_state_raw_entry_without_status_returns_none(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "file_path": "app/run.py",
                "title": "Shell injection",
            }
        ]
    }
    assert get_fix_state(scan_report, "finding-001") == {
        "status": "none",
        "finding_id": "finding-001",
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


def test_get_fix_state_path_disambiguates_duplicate_outcomes(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "file_path": "a.py",
                "fix_pr_url": "https://x/pull/1",
                "fix_status": "pr_created",
            },
            {
                "rule_id": "finding-001",
                "file_path": "b.py",
                "fix_pr_url": "https://x/pull/2",
                "fix_status": "pr_created",
            },
        ]
    }
    assert get_fix_state(scan_report, "finding-001", file_path="b.py") == {
        "status": "pr_created",
        "finding_id": "finding-001",
        "file_path": "b.py",
        "pr_url": "https://x/pull/2",
    }
    legacy = get_fix_state(scan_report, "finding-001")
    assert legacy["file_path"] == "a.py"
    assert legacy["pr_url"] == "https://x/pull/1"


def test_get_fix_state_accepts_pathless_outcome_when_path_given(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "fix_pr_url": "https://x/pull/4",
                "fix_status": "verified",
            }
        ]
    }
    assert get_fix_state(scan_report, "finding-001", file_path="whatever.py") == {
        "status": "verified",
        "finding_id": "finding-001",
        "file_path": None,
        "pr_url": "https://x/pull/4",
    }


def test_get_fix_state_prefers_path_match_over_earlier_pathless(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "fix_pr_url": "https://x/pull/1",
                "fix_status": "verified",
            },
            {
                "rule_id": "finding-001",
                "file_path": "app/run.py",
                "fix_pr_url": "https://x/pull/2",
                "fix_status": "pr_created",
            },
        ]
    }
    assert get_fix_state(scan_report, "finding-001", file_path="app/run.py") == {
        "status": "pr_created",
        "finding_id": "finding-001",
        "file_path": "app/run.py",
        "pr_url": "https://x/pull/2",
    }


def test_get_fix_state_suffix_path_match(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "file_path": "src/a.py",
                "fix_pr_url": "https://x/pull/3",
                "fix_status": "verified",
            }
        ]
    }
    assert get_fix_state(scan_report, "finding-001", file_path="a.py") == {
        "status": "verified",
        "finding_id": "finding-001",
        "file_path": "src/a.py",
        "pr_url": "https://x/pull/3",
    }


def test_get_fix_state_returns_pathless_entry_when_path_given(scan_report):
    scan_report.metadata = {
        "findings": [
            {
                "rule_id": "finding-001",
                "fix_pr_url": "https://x/pull/4",
                "fix_status": "pr_created",
            },
            {
                "rule_id": "finding-001",
                "fix_pr_url": "https://x/pull/5",
                "fix_status": "verified",
            },
        ]
    }
    assert get_fix_state(scan_report, "finding-001", file_path="app/run.py") == {
        "status": "pr_created",
        "finding_id": "finding-001",
        "file_path": None,
        "pr_url": "https://x/pull/4",
    }


def test_get_fix_state_pending_path_mismatch_reads_none(scan_report):
    scan_report.metadata = {
        "pending_fixes": {
            "finding-001": {
                "file_path": "app/run.py",
                "diff": "--- a\n+++ b\n",
                "model_used": "groq/m",
            }
        }
    }
    assert get_fix_state(scan_report, "finding-001", file_path="app/other.py") == {
        "status": "none",
        "finding_id": "finding-001",
    }
    assert (
        get_fix_state(scan_report, "finding-001", file_path="app/run.py")["status"]
        == "awaiting_approval"
    )
    assert get_fix_state(scan_report, "finding-001")["status"] == "awaiting_approval"


async def test_discard_pending_removes_entry_with_cas(scan_report, monkeypatch):
    scan_report.metadata = {"pending_fixes": {"finding-001": {"diff": "d"}, "other": {"diff": "x"}}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    assert await discard_pending(scan_report, "finding-001") is True
    assert scan_report.metadata["pending_fixes"] == {"other": {"diff": "x"}}
    scan_report.save.assert_not_awaited()
    cas.assert_awaited_once_with(
        scan_report,
        {"finding-001": {"diff": "d"}, "other": {"diff": "x"}},
        {"other": {"diff": "x"}},
    )


async def test_discard_pending_absent_is_noop(scan_report, monkeypatch):
    scan_report.metadata = {"pending_fixes": {"other": {"diff": "x"}}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    assert await discard_pending(scan_report, "finding-001") is False
    assert scan_report.metadata["pending_fixes"] == {"other": {"diff": "x"}}
    scan_report.save.assert_not_awaited()
    cas.assert_not_awaited()


async def test_discard_pending_drops_empty_map(scan_report, monkeypatch):
    scan_report.metadata = {"pending_fixes": {"finding-001": {"diff": "d"}}, "findings": []}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    assert await discard_pending(scan_report, "finding-001") is True
    assert "pending_fixes" not in scan_report.metadata
    assert scan_report.metadata["findings"] == []
    scan_report.save.assert_not_awaited()
    cas.assert_awaited_once_with(
        scan_report, {"finding-001": {"diff": "d"}}, {}
    )


async def test_discard_pending_fresh_claim_conflicts(scan_report, monkeypatch):
    entry = {"diff": "d", "_approving": True, "_approving_at": time.time()}
    scan_report.metadata = {"pending_fixes": {"finding-001": entry}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    with pytest.raises(FixConflictError, match="already in progress"):
        await discard_pending(scan_report, "finding-001")
    cas.assert_not_awaited()
    assert scan_report.metadata["pending_fixes"]["finding-001"] == entry
    scan_report.save.assert_not_awaited()


async def test_discard_pending_stale_claim_discards(scan_report, monkeypatch):
    entry = {"diff": "d", "_approving": True, "_approving_at": time.time() - 901}
    scan_report.metadata = {"pending_fixes": {"finding-001": entry}}
    cas = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    assert await discard_pending(scan_report, "finding-001") is True
    assert "pending_fixes" not in scan_report.metadata
    cas.assert_awaited_once_with(scan_report, {"finding-001": entry}, {})
    scan_report.save.assert_not_awaited()


async def test_discard_pending_cas_exhaustion_returns_false(scan_report, monkeypatch):
    scan_report.metadata = {"pending_fixes": {"finding-001": {"diff": "d"}}}
    cas = AsyncMock(return_value=False)
    monkeypatch.setattr("services.ai.fix_runner._cas_pending_map", cas)
    assert await discard_pending(scan_report, "finding-001") is False
    assert cas.await_count == _MAX_CAS_ATTEMPTS
    assert scan_report.metadata["pending_fixes"] == {"finding-001": {"diff": "d"}}
    scan_report.save.assert_not_awaited()


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


async def test_open_pr_records_verification_and_status(
    scan_report, runner_env, monkeypatch, outcome_collection
):
    from config import settings
    monkeypatch.setattr(settings, "auto_fix_requires_approval", False)
    monkeypatch.setattr(settings, "auto_fix_dry_run", False)
    scan_report.id = "scan-oid"
    # metadata.findings holds the raw scanner dict shape written by
    # process_real_scan: rule_id + file_path, no id
    scan_report.metadata = {"findings": [{
        "rule_id": "finding-001",
        "file_path": "app/run.py",
        "title": "Shell injection",
    }]}
    scanner = MagicMock()
    scanner.scan_repository = AsyncMock(return_value={
        "total_findings": 0,
        "detailed_findings": [{"rule_id": "OTHER", "file_path": "elsewhere.py", "id": "fx"}],
    })
    with (
        patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection),
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
    # pre-existing raw scanner keys survive the outcome write
    assert entry["title"] == "Shell injection"
    assert entry["rule_id"] == "finding-001"
    assert entry["file_path"] == "app/run.py"
    _assert_outcome_update(
        outcome_collection, scan_report, status="verified", pr_url="https://x/pull/9"
    )
    assert outcome_collection.update_one.await_args.kwargs["array_filters"] == [{
        "$and": [
            {"$or": [{"e.id": "finding-001"}, {"e.rule_id": "finding-001"}]},
            {"$or": [
                {"e.file_path": {"$exists": False}},
                {"e.file_path": None},
                {"e.file_path": {"$in": ["app/run.py", "app/run.py"]}},
            ]},
        ]
    }]


async def test_record_outcome_disambiguates_duplicate_rule_id_by_path(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    finding.file_path = "b.py"
    scan_report.metadata = {"findings": [
        {"rule_id": "finding-001", "file_path": "a.py", "title": "A"},
        {"rule_id": "finding-001", "file_path": "b.py", "title": "B"},
    ]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/4", verification={"verified": False}
        )
    a_entry, b_entry = scan_report.metadata["findings"]
    assert a_entry == {"rule_id": "finding-001", "file_path": "a.py", "title": "A"}
    assert b_entry["fix_status"] == "pr_created"
    assert b_entry["fix_pr_url"] == "https://x/pull/4"
    assert b_entry["title"] == "B"
    _assert_outcome_update(
        outcome_collection, scan_report, status="pr_created", pr_url="https://x/pull/4"
    )


async def test_record_outcome_adds_path_filter(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    finding.file_path = "b.py"
    scan_report.metadata = {"findings": [
        {"rule_id": "finding-001", "file_path": "a.py", "title": "A"},
        {"rule_id": "finding-001", "file_path": "b.py", "title": "B"},
    ]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/10", verification={"verified": False}
        )
    array_filter, = outcome_collection.update_one.await_args.kwargs["array_filters"]
    assert array_filter == {"$and": [
        {"$or": [{"e.id": "finding-001"}, {"e.rule_id": "finding-001"}]},
        {"$or": [
            {"e.file_path": {"$exists": False}},
            {"e.file_path": None},
            {"e.file_path": {"$in": ["b.py", "b.py"]}},
        ]},
    ]}


async def test_record_outcome_without_file_path_uses_ident_only(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    finding.file_path = ""
    scan_report.metadata = {"findings": [{"rule_id": "finding-001", "title": "x"}]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/11", verification={"verified": True}
        )
    assert outcome_collection.update_one.await_args.kwargs["array_filters"] == [
        {"$or": [{"e.id": "finding-001"}, {"e.rule_id": "finding-001"}]}
    ]
    assert scan_report.metadata["findings"][0]["fix_status"] == "verified"
    scan_report.save.assert_not_awaited()


async def test_record_outcome_no_findings_list_skips_db(
    scan_report, finding, outcome_collection
):
    scan_report.metadata = {}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/12", verification={"verified": True}
        )
    outcome_collection.update_one.assert_not_awaited()
    scan_report.save.assert_not_awaited()


async def test_record_outcome_updates_all_matching_duplicates(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    scan_report.metadata = {"findings": [
        {"rule_id": "finding-001", "file_path": "app/run.py", "title": "A"},
        {"rule_id": "finding-001", "file_path": "app/run.py", "title": "B"},
    ]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/5", verification={"verified": True}
        )
    entries = scan_report.metadata["findings"]
    assert [e["fix_status"] for e in entries] == ["verified", "verified"]
    assert [e["fix_pr_url"] for e in entries] == ["https://x/pull/5", "https://x/pull/5"]
    assert [e["title"] for e in entries] == ["A", "B"]
    _assert_outcome_update(
        outcome_collection, scan_report, status="verified", pr_url="https://x/pull/5"
    )


async def test_record_outcome_matches_semantic_production_shape(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    # production invariant: VulnerabilityFinding.id is assigned the raw rule_id
    finding.id = "B608"
    scan_report.metadata = {"findings": [
        {"rule_id": "B608", "file_path": "app/run.py", "title": "Shell injection"},
    ]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/6", verification={"verified": True}
        )
    entry = scan_report.metadata["findings"][0]
    assert entry["fix_status"] == "verified"
    assert entry["fix_pr_url"] == "https://x/pull/6"
    _assert_outcome_update(
        outcome_collection, scan_report, status="verified", pr_url="https://x/pull/6"
    )


async def test_record_outcome_legacy_id_entry_still_matches(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    scan_report.metadata = {"findings": [{"id": "finding-001", "file_path": "app/run.py"}]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/7", verification={"verified": False}
        )
    entry = scan_report.metadata["findings"][0]
    assert entry["fix_status"] == "pr_created"
    assert entry["fix_pr_url"] == "https://x/pull/7"
    _assert_outcome_update(
        outcome_collection, scan_report, status="pr_created", pr_url="https://x/pull/7"
    )


async def test_record_outcome_matches_when_entry_lacks_path(
    scan_report, finding, outcome_collection
):
    scan_report.id = "scan-oid"
    scan_report.metadata = {"findings": [{"rule_id": "finding-001", "title": "no path"}]}
    with patch.object(ScanReport, "get_motor_collection", return_value=outcome_collection):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/8", verification={"verified": True}
        )
    assert scan_report.metadata["findings"][0]["fix_status"] == "verified"
    _assert_outcome_update(
        outcome_collection, scan_report, status="verified", pr_url="https://x/pull/8"
    )


async def test_record_outcome_warns_when_no_metadata_entry_matches(
    scan_report, finding, caplog
):
    scan_report.id = "scan-oid"
    scan_report.metadata = {"findings": [{"rule_id": "finding-001", "file_path": "app/run.py"}]}
    collection = _fake_collection(matched_count=1, modified_count=0)
    with (
        caplog.at_level(logging.WARNING, logger="services.ai.fix_runner"),
        patch.object(ScanReport, "get_motor_collection", return_value=collection),
    ):
        await _record_fix_outcome(
            scan_report, finding, pr_url="https://x/pull/13", verification={"verified": True}
        )
    assert scan_report.metadata["findings"][0]["fix_status"] == "verified"
    assert scan_report.metadata["findings"][0]["fix_pr_url"] == "https://x/pull/13"
    scan_report.save.assert_not_awaited()
    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert warnings == [
        "Fix outcome not persisted for finding finding-001 at app/run.py "
        "— no matching metadata entry"
    ]


async def test_refresh_report_warns_without_raw_exception(scan_report, caplog):
    scan_report.id = ObjectId()
    with (
        caplog.at_level(logging.WARNING, logger="services.ai.fix_runner"),
        patch.object(ScanReport, "get", AsyncMock(side_effect=RuntimeError("db secret"))),
    ):
        assert await _refresh_report(scan_report) is scan_report
    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert warnings == [
        f"Could not refresh scan report {scan_report.id} (RuntimeError)"
    ]
    assert all("db secret" not in message for message in warnings)
