"""Shared least-privilege read-only tools for ONYX agents (spec 4.1/4.4).

fix-agent and investigate-agent both register these. No shell, no network
beyond the existing OSV/NVD service. Workspace-bound tools are only
registered when a workspace clone exists (fix-agent); the investigate
agent has no clone and gets intel-only tools (A7/A8).
"""
import re
from pathlib import Path

from pydantic_ai import ModelRetry

from services.ai.chat_grounding import format_context
from services.ai.gateway import _scrub, spec_for
from services.ai.retrieval import retrieve

AGENT_LANES = ("groq", "openrouter", "openai", "ollama")
_SKIPPED_DIRS = {".git", "node_modules", "vendor", "__pycache__", ".venv", "venv", "dist", "build"}
_MAX_SEARCH_HITS = 50
_MAX_SEARCH_FILES = 2000


def openai_compatible_spec():
    """First configured OpenAI-compatible lane, or None."""
    from config import settings
    for name in settings.configured_provider_chain():
        if name in AGENT_LANES:
            return spec_for(name)
    return None


def resolve_in_workspace(workspace: Path, rel_path: str) -> Path:
    candidate = (workspace / rel_path).resolve()
    if not candidate.is_relative_to(workspace.resolve()):
        raise ModelRetry(f"Path {rel_path!r} escapes the repository workspace")
    if not candidate.is_file():
        raise ModelRetry(f"File not found: {rel_path}")
    return candidate


def register_readonly_tools(agent, workspace: Path | None) -> None:
    """Register get_cwe + get_vuln_intel always; read_file + search_repo only with a workspace."""

    @agent.tool_plain
    async def get_cwe(cwe_id: str) -> str:
        cwe = cwe_id if cwe_id.upper().startswith("CWE-") else f"CWE-{cwe_id}"
        try:
            chunks = await retrieve(f"{cwe} remediation guidance")
            text, _ = format_context(chunks, 3000)
            return text or f"no knowledge base entries for {cwe}"
        except Exception as e:
            return f"knowledge lookup failed: {_scrub(e, 120)}"

    @agent.tool_plain
    async def get_vuln_intel(cve_id: str) -> str:
        try:
            from services.infrastructure.osv_nvd_integration import get_osv_nvd_service

            svc = await get_osv_nvd_service()
            match = await svc.query_by_cve(cve_id)
            if not match:
                return f"no record for {cve_id}"
            return (
                f"id={match.id} summary={getattr(match, 'summary', '')} "
                f"cvss={getattr(match, 'cvss_score', None)} "
                f"epss={getattr(match, 'epss_score', None)} "
                f"kev={getattr(match, 'kev_listed', False)}"
            )[:2000]
        except Exception as e:  # intel is best-effort
            return f"intel lookup failed: {_scrub(e, 120)}"

    if workspace is None:
        return

    @agent.tool_plain
    async def read_file(path: str, start_line: int = 1, end_line: int = 200) -> str:
        target = resolve_in_workspace(workspace, path)
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(1, start_line)
        end = min(len(lines), end_line)
        if start > end:
            raise ModelRetry(f"start_line {start} > end_line {end} (file has {len(lines)} lines)")
        body = "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))
        return body[:12000]

    @agent.tool_plain
    async def search_repo(pattern: str) -> str:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ModelRetry(f"Invalid regex: {e}")
        hits = []
        scanned = 0
        for path in sorted(workspace.rglob("*")):
            if not path.is_file() or set(path.parts) & _SKIPPED_DIRS:
                continue
            scanned += 1
            if scanned > _MAX_SEARCH_FILES or len(hits) >= _MAX_SEARCH_HITS:
                break
            try:
                if path.stat().st_size > 1_000_000:
                    continue
                for n, line in enumerate(
                    path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                ):
                    if regex.search(line):
                        rel = path.relative_to(workspace).as_posix()
                        hits.append(f"{rel}:{n}: {line.strip()[:200]}")
                        if len(hits) >= _MAX_SEARCH_HITS:
                            break
            except OSError:
                continue
        return "\n".join(hits) or "no matches"
