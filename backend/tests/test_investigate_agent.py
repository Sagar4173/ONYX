"""Investigate-agent offline tests - scripted FunctionModel, no network."""
from unittest.mock import AsyncMock

import pytest
from pydantic_ai import ModelResponse, TextPart, ToolCallPart
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
from services.ai.investigate_agent import (
    InvestigateAgentError,
    InvestigateReport,
    run_investigate_agent,
)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr("services.ai.agent_tools.retrieve", AsyncMock(return_value=[]))
    quota = AsyncMock()
    quota.try_consume = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.investigate_agent.QuotaLedger", lambda: quota)


@pytest.fixture
def finding():
    return VulnerabilityFinding(
        id="finding-001",
        scanner=ScannerType.SEMGREP,
        rule_id="sql-injection",
        title="SQL Injection in login query",
        description="User input flows into cursor.execute",
        severity=SeverityLevel.HIGH,
        file_path="app/login.py",
        line_start=10,
        line_end=12,
        code_snippet="cursor.execute(f\"SELECT * FROM u WHERE name='{name}'\")",
        cwe_id="CWE-89",
    )


@pytest.fixture
def report(finding):
    # model_construct: beanie Document.__init__ requires an initialized collection.
    return ScanReport.model_construct(
        project_name="demo",
        scan_id="scan-001",
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


CANNED = dict(
    finding_id="finding-001",
    summary="Confirmed SQLi.",
    exploitability="Reachable endpoint",
    evidence=["cwe-89 matched snippet"],
    likely_false_positive=False,
    false_positive_reasons=[],
    fix_guidance="Parameterize the query.",
    confidence="high",
)


def _final(report_dict=None):
    data = dict(CANNED if report_dict is None else report_dict)
    return ModelResponse(parts=[TextPart(InvestigateReport(**data).model_dump_json())])


def _call(name, args=None):
    return ModelResponse(parts=[ToolCallPart(name, args or {})])


def _scripted(responses):
    state = {"n": 0}

    def fn(messages, info):
        out = responses[min(state["n"], len(responses) - 1)]
        state["n"] += 1
        if callable(out):
            return out(messages)
        return out

    return FunctionModel(fn)


async def test_happy_path_returns_structured_report(report, finding):
    model = _scripted([_final()])
    result = await run_investigate_agent(finding=finding, report=report, model=model)
    assert isinstance(result.report, InvestigateReport)
    assert result.report.confidence == "high"
    assert result.report.finding_id == "finding-001"
    assert result.provider == "test"
    assert result.usage.get("requests", 0) >= 1


async def test_scan_context_tool_is_callable(report, finding):
    seen = {}

    def capture(messages):
        seen["messages"] = str(messages)
        return _final()

    model = _scripted([_call("get_scan_context"), capture])
    result = await run_investigate_agent(finding=finding, report=report, model=model)
    assert "<scan_context>" in seen["messages"]
    assert "scan-001" in seen["messages"]
    assert result.report.finding_id == "finding-001"


async def test_prompt_contains_finding_block(report, finding):
    seen = {}

    def capture(messages):
        seen["task"] = str(messages[0])
        return _final()

    model = _scripted([capture])
    await run_investigate_agent(finding=finding, report=report, model=model)
    assert "<finding>" in seen["task"]
    assert "finding-001" in seen["task"]


async def test_caps_evidence_and_false_positive_reasons(report, finding):
    over = dict(
        CANNED,
        evidence=[f"e{i}" for i in range(10)],
        false_positive_reasons=[f"r{i}" for i in range(6)],
    )
    model = _scripted([_final(over)])
    result = await run_investigate_agent(finding=finding, report=report, model=model)
    assert len(result.report.evidence) == 8
    assert len(result.report.false_positive_reasons) == 5


async def test_quota_exhausted_raises(monkeypatch, report, finding):
    quota = AsyncMock()
    quota.try_consume = AsyncMock(return_value=False)
    monkeypatch.setattr("services.ai.investigate_agent.QuotaLedger", lambda: quota)
    with pytest.raises(InvestigateAgentError, match="quota"):
        await run_investigate_agent(
            finding=finding, report=report, model=_scripted([_final()])
        )


async def test_quota_exhausted_message_precedes_model(report, finding, monkeypatch):
    quota = AsyncMock()
    quota.try_consume = AsyncMock(return_value=False)
    monkeypatch.setattr("services.ai.investigate_agent.QuotaLedger", lambda: quota)
    called = []

    def never(messages, info):
        called.append(1)
        return _final()

    with pytest.raises(InvestigateAgentError) as exc:
        await run_investigate_agent(
            finding=finding, report=report, model=FunctionModel(never)
        )
    assert "Daily AI quota exhausted" in str(exc.value)
    assert called == []  # quota is consumed BEFORE the agent runs
