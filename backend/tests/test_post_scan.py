"""Background post-scan AI analysis."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import services.ai.post_scan as post_scan_mod
from services.ai.post_scan import (
    reset_post_scan_state,
    run_post_scan_ai,
    schedule_post_scan_ai,
)


class FakeQuery:
    """Mimics beanie: await query gives the record; query.update({...}) chains."""

    def __init__(self, record=None):
        self.record = record
        self.updates = []

    def __await__(self):
        async def _get():
            return self.record
        return _get().__await__()

    def update(self, doc):
        async def _do():
            self.updates.append(doc)
            return 1
        return _do()


def _report():
    return SimpleNamespace(
        scan_id="scan-001",
        project_name="demo",
        scan_results=[MagicMock()],
        git_metadata=None,
    )


def _fake_analysis():
    from datetime import datetime, timezone

    from models.report import AIAnalysis

    return AIAnalysis(
        model_used="gemini/gemini-2.5-flash",
        generated_at=datetime.now(timezone.utc),
        executive_summary="s", risk_assessment="r",
        risk_score=40, risk_level="CRITICAL", security_score=80,
        priority_findings=[], recommendations=[],
        secure_code_examples={}, compliance_impact={},
        estimated_fix_time="8 hours", attack_vectors=[],
        threat_categories={}, remediation_roadmap=[],
    )


async def test_success_writes_analysis_and_status_complete():
    reset_post_scan_state()
    query = FakeQuery(record=_report())
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(return_value=_fake_analysis())

    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")

    fake_processor.analyze_scan_results.assert_awaited_once()
    # ai_analysis write + two status writes (running, complete)
    assert len(query.updates) == 3
    assert "ai_analysis" in query.updates[1]["$set"]
    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", None, "complete"]


async def test_processor_failure_sets_status_failed():
    reset_post_scan_state()
    query = FakeQuery(record=_report())
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(side_effect=RuntimeError("provider down"))

    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")

    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", "failed"]
    assert "provider down" in query.updates[-1]["$set"]["metadata.ai_error"]


async def test_missing_report_sets_status_failed():
    reset_post_scan_state()
    query = FakeQuery(record=None)
    with patch.object(post_scan_mod.ScanReport, "find_one", return_value=query):
        await run_post_scan_ai("scan-001")
    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", "failed"]


async def test_schedule_creates_task_and_cleans_up():
    reset_post_scan_state()
    mock_run = AsyncMock()
    with patch.object(post_scan_mod, "run_post_scan_ai", mock_run):
        schedule_post_scan_ai("scan-001")
        await asyncio.sleep(0.05)
    mock_run.assert_awaited_once_with("scan-001")
    assert len(post_scan_mod._tasks) == 0


async def test_reset_clears_semaphore():
    reset_post_scan_state()
    first = post_scan_mod._get_semaphore()
    reset_post_scan_state()
    assert post_scan_mod._semaphore is None
    assert post_scan_mod._get_semaphore() is not first  # fresh instance


async def test_empty_scan_results_runs_clean_analysis():
    reset_post_scan_state()
    record = SimpleNamespace(
        scan_id="scan-001", project_name="demo", scan_results=[], git_metadata=None
    )
    query = FakeQuery(record=record)
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(return_value=_fake_analysis())

    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")

    fake_processor.analyze_scan_results.assert_awaited_once()
    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", None, "complete"]


async def test_ai_error_scrubbed_on_failure():
    reset_post_scan_state()
    query = FakeQuery(record=_report())
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(
        side_effect=RuntimeError("boom sk-abc123XYZ456")
    )
    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")
    err = query.updates[-1]["$set"]["metadata.ai_error"]
    assert "boom" in err
    assert "sk-abc123XYZ456" not in err


async def test_ai_error_cleared_on_success():
    reset_post_scan_state()
    query = FakeQuery(record=_report())
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(side_effect=RuntimeError("boom"))
    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")
    assert "boom" in query.updates[-1]["$set"]["metadata.ai_error"]

    # retry succeeds -> the stale error must be explicitly cleared
    fake_processor.analyze_scan_results = AsyncMock(return_value=_fake_analysis())
    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")
    last = query.updates[-1]["$set"]
    assert last["metadata.ai_status"] == "complete"
    assert "metadata.ai_error" in last
    assert last["metadata.ai_error"] is None
