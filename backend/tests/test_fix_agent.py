"""Fix-agent offline tests — scripted FunctionModel, no network, no provider."""
import json
from unittest.mock import AsyncMock

import pytest
from pydantic_ai import ModelResponse, ModelRetry, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from models.report import ScannerType, SeverityLevel, VulnerabilityFinding
from services.ai.fix_agent import FixAgentError, FixOutcome, PatchProposal, run_fix_agent


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr("services.ai.agent_tools.retrieve", AsyncMock(return_value=[]))
    quota = AsyncMock()
    quota.try_consume = AsyncMock(return_value=True)
    monkeypatch.setattr("services.ai.fix_agent.QuotaLedger", lambda: quota)


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "run.py").write_text(
        "import os\n\ndef run(query):\n    return os.popen(query)\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def finding():
    return VulnerabilityFinding(
        id="finding-001",
        scanner=ScannerType.SEMGREP,
        rule_id="B608",
        title="Shell injection",
        description="os.popen with user input",
        severity=SeverityLevel.HIGH,
        file_path="app/run.py",
        line_start=4,
        line_end=4,
        cwe_id="CWE-78",
    )


GOOD_PATCH = "import os\nimport shlex\n\ndef run(query):\n    return os.popen(shlex.quote(query))\n"


def _final(summary="patched"):
    return ModelResponse(parts=[TextPart(FixOutcome(proposal_accepted=True, summary=summary).model_dump_json())])


def _scripted(responses):
    state = {"n": 0}

    def fn(messages, info):
        out = responses[min(state["n"], len(responses) - 1)]
        state["n"] += 1
        if callable(out):
            return out(messages)
        return out

    return FunctionModel(fn)


def _propose(**over):
    args = {"file_path": "app/run.py", "line_start": 1, "line_end": 4,
            "patched_content": GOOD_PATCH, "rationale": "quote shell arg"}
    args.update(over)
    return ModelResponse(parts=[ToolCallPart("propose_patch", args)])


async def test_happy_path_returns_validated_proposal(workspace, finding):
    model = _scripted([_propose(), _final()])
    result = await run_fix_agent(workspace=workspace, finding=finding, guidance="", model=model)
    assert isinstance(result.proposal, PatchProposal)
    assert result.proposal.patched_content == GOOD_PATCH
    assert result.gate_report.passed
    assert result.usage.get("requests", 0) >= 1


async def test_gate_failure_retries_then_succeeds(workspace, finding):
    bad = _propose(patched_content="def broken(:\n")
    model = _scripted([bad, _propose(), _final()])
    result = await run_fix_agent(workspace=workspace, finding=finding, model=model)
    assert result.gate_report.passed


async def test_retries_exhausted_raises_fix_agent_error(workspace, finding):
    model = _scripted([_propose(patched_content="def broken(:\n")])
    with pytest.raises(FixAgentError):
        await run_fix_agent(workspace=workspace, finding=finding, model=model)


async def test_wrong_file_is_rejected_by_allowlist_in_tool(workspace, finding):
    model = _scripted([_propose(file_path="other/evil.py"), _propose(), _final()])
    result = await run_fix_agent(workspace=workspace, finding=finding, model=model)
    assert result.proposal.file_path == "app/run.py"  # only the allowlisted attempt ever stored


async def test_path_traversal_read_is_rejected(workspace, finding):
    from pydantic_ai import ModelRetry
    from services.ai.agent_tools import resolve_in_workspace

    with pytest.raises(ModelRetry):
        resolve_in_workspace(workspace, "../../etc/passwd")


async def test_agent_finishing_without_proposal_raises(workspace, finding):
    model = _scripted([_final("gave up")])
    with pytest.raises(FixAgentError, match="without a validated patch"):
        await run_fix_agent(workspace=workspace, finding=finding, model=model)


async def test_no_compatible_lane_raises(workspace, finding, monkeypatch):
    from config import settings

    # Settings is a pydantic BaseSettings: methods can only be patched on the class.
    monkeypatch.setattr(type(settings), "configured_provider_chain", lambda self: ["gemini"])
    with pytest.raises(FixAgentError, match="No OpenAI-compatible provider"):
        await run_fix_agent(workspace=workspace, finding=finding)


async def test_quota_exhausted_raises(workspace, finding, monkeypatch):
    quota = AsyncMock()
    quota.try_consume = AsyncMock(return_value=False)
    monkeypatch.setattr("services.ai.fix_agent.QuotaLedger", lambda: quota)
    with pytest.raises(FixAgentError, match="quota"):
        await run_fix_agent(workspace=workspace, finding=finding,
                            model=_scripted([_propose(), _final()]))


async def test_task_prompt_contains_finding_and_guidance(workspace, finding):
    seen = {}

    def capture(messages):
        seen["task"] = messages[-1].parts[0].content if hasattr(messages[-1].parts[0], "content") else str(messages[-1])
        # propose then finish: a run that never proposes a patch must raise
        # (see test_agent_finishing_without_proposal_raises), so the script
        # cannot return the final output directly here.
        return _propose()

    model = _scripted([capture, _final()])
    await run_fix_agent(workspace=workspace, finding=finding,
                         guidance="Use parameterized queries (CWE-89).", model=model)
    task = str(seen.get("task", ""))
    assert "finding-001" in task
    assert "parameterized queries" in task
