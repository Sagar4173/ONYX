r"""Golden evals for the investigate agent - offline, deterministic.

Run: .venv\Scripts\python.exe -m pytest evals/ -v -m eval
No network: FunctionModel returns a canned structured report; quota ledger
and retrieval are monkeypatched to stubs.
"""
from unittest.mock import AsyncMock

import pytest
from pydantic_ai import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from models.report import (
    GitMetadata,
    ScanReport,
    ScanResult,
    ScannerType,
    ScanStatus,
    SeverityLevel,
    VulnerabilityFinding,
)
from services.ai.investigate_agent import InvestigateReport, run_investigate_agent

pytestmark = pytest.mark.eval


def _finding(**over):
    base: dict = dict(
        id="finding-001", scanner=ScannerType.SEMGREP, rule_id="B608",
        title="Shell injection", description="os.popen with user input",
        severity=SeverityLevel.HIGH, file_path="app/run.py",
        line_start=4, line_end=4, cwe_id="CWE-78",
    )
    base.update(over)
    return VulnerabilityFinding(**base)


def _report(finding):
    # model_construct: beanie Document.__init__ requires an initialized
    # collection (same fixture approach as tests/test_investigate_agent.py).
    return ScanReport.model_construct(
        project_name="golden",
        scan_id="scan-golden",
        git_metadata=GitMetadata(
            repository_url="https://github.com/demo/demo",
            branch="main",
            commit_hash="abc123",
            event_type="push",
        ),
        status=ScanStatus.COMPLETED,
        scan_results=[
            ScanResult(
                scanner=ScannerType.SEMGREP,
                status=ScanStatus.COMPLETED,
                findings=[finding],
            )
        ],
    )


CANNED: dict = dict(
    finding_id="finding-001", summary="Shell injection confirmed.",
    exploitability="Direct user input reaches os.popen.",
    evidence=["CWE-78", "line 4 uses os.popen"],
    likely_false_positive=False, false_positive_reasons=[],
    fix_guidance="Use subprocess with a fixed argv list.", confidence="high",
)


@pytest.mark.parametrize("question", ["", "Is this exploitable in CI?"])
async def test_investigate_golden(question, monkeypatch):
    quota = AsyncMock()
    quota.try_consume = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.investigate_agent.QuotaLedger", lambda: quota)
    monkeypatch.setattr("services.ai.agent_tools.retrieve", AsyncMock(return_value=[]))
    finding = _finding()
    model = FunctionModel(
        lambda messages, info: ModelResponse(
            parts=[TextPart(InvestigateReport(**CANNED).model_dump_json())]
        )
    )
    result = await run_investigate_agent(
        finding=finding, report=_report(finding), question=question, model=model
    )
    assert result.report.confidence == "high"
    assert result.report.finding_id == "finding-001"
    assert len(result.report.evidence) <= 8
