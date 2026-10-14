"""Shared read-only tool registry (Phase 4 extraction)."""
import pytest
from pydantic_ai import Agent, ModelRetry, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from services.ai.agent_tools import register_readonly_tools, resolve_in_workspace


def test_resolve_in_workspace_blocks_escape(tmp_path):
    with pytest.raises(ModelRetry):
        resolve_in_workspace(tmp_path, "../outside.txt")


def test_resolve_in_workspace_missing_file(tmp_path):
    with pytest.raises(ModelRetry):
        resolve_in_workspace(tmp_path, "nope.py")


def _registered_names(workspace):
    """Names actually offered to the model on the first turn (public AgentInfo API)."""
    seen = {}

    def fn(messages, info):
        seen["names"] = {tool.name for tool in info.function_tools}
        return ModelResponse(parts=[TextPart("ok")])

    agent = Agent(FunctionModel(fn), output_type=str)
    register_readonly_tools(agent, workspace=workspace)
    agent.run_sync("go")
    return set(seen["names"])


def test_registry_registers_all_four(tmp_path):
    names = _registered_names(tmp_path)
    assert {"read_file", "search_repo", "get_cwe", "get_vuln_intel"} <= names


def test_registry_workspace_none_registers_intel_only(tmp_path):
    names = _registered_names(None)
    assert {"get_cwe", "get_vuln_intel"} <= names
    assert "read_file" not in names and "search_repo" not in names
