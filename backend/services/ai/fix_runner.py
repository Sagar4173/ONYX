"""Fix-run orchestration: propose -> gates -> approval -> PR (spec 4.2/4.3).

Statuses: dry_run (never persists) | awaiting_approval (pending stored) |
pr_created (approval OFF or approved). AUTO_FIX_REQUIRES_APPROVAL defaults ON
so the PR only opens via approve_fix; AUTO_FIX_DRY_RUN makes every run
side-effect free.
"""
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import settings
from models.report import ScanReport, VulnerabilityFinding
from services.ai.chat_grounding import format_context
from services.ai.fix_agent import FixAgentError, run_fix_agent
from services.ai.retrieval import retrieve
from services.scm.auto_fix_service import AutoFixError, auto_fix_service

logger = logging.getLogger(__name__)

PENDING_FIXES = "pending_fixes"


@dataclass
class FixRunResult:
    status: str
    finding_id: str
    file_path: str
    diff: str = ""
    gate_failures: List[str] = field(default_factory=list)
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    model_used: str = ""


async def _guidance_for(finding: VulnerabilityFinding) -> str:
    query = " ".join(x for x in (finding.rule_id, finding.cwe_id, finding.title) if x) + " remediation"
    try:
        chunks = await retrieve(query)
        text, _ = format_context(chunks, settings.rag_max_context_chars)
        return text
    except Exception as e:
        logger.info("Guidance retrieval unavailable for fix-agent: %s", e)
        return ""


async def _store_pending(scan_report: ScanReport, finding_id: str, payload: Dict[str, Any]) -> None:
    metadata = scan_report.metadata if isinstance(scan_report.metadata, dict) else {}
    pending = dict(metadata.get(PENDING_FIXES) or {})
    pending[finding_id] = payload
    scan_report.metadata = {**metadata, PENDING_FIXES: pending}
    await scan_report.save()


async def _open_pr(
    scan_report: ScanReport,
    finding: VulnerabilityFinding,
    *,
    local_path: str,
    patched_content: str,
    model_used: str,
) -> FixRunResult:
    target = Path(local_path) / finding.file_path
    target.write_text(patched_content, encoding="utf-8")
    repo_url = scan_report.git_metadata.repository_url
    branch = scan_report.git_metadata.branch
    token = await auto_fix_service._resolve_token(scan_report)
    branch_name = auto_fix_service._create_branch_and_commit(
        local_path=local_path, file_path=finding.file_path, finding=finding, branch=branch
    )
    auto_fix_service._push_branch(local_path, branch_name, token, repo_url)
    pr_url, pr_number = await auto_fix_service._create_pr(
        repo_url=repo_url, branch=branch, branch_name=branch_name,
        finding=finding, token=token, scan_report=scan_report, body_extra="",
    )
    return FixRunResult(
        status="pr_created", finding_id=finding.id, file_path=finding.file_path,
        pr_url=pr_url, pr_number=pr_number, branch=branch_name, model_used=model_used,
    )


async def propose_fix(scan_report: ScanReport, finding_id: str) -> FixRunResult:
    finding = auto_fix_service._find_finding(scan_report, finding_id)
    if not finding:
        raise AutoFixError(f"Finding {finding_id} not found in scan report")
    if not finding.file_path:
        raise AutoFixError(f"Finding {finding_id} has no file path — cannot auto-fix")

    repo_url = scan_report.git_metadata.repository_url
    branch = scan_report.git_metadata.branch
    token = await auto_fix_service._resolve_token(scan_report)

    local_path = None
    try:
        local_path = auto_fix_service._clone_repo(repo_url, branch, token)
        guidance = await _guidance_for(finding)
        agent_result = await run_fix_agent(
            workspace=Path(local_path), finding=finding, guidance=guidance
        )
        model_used = f"{agent_result.provider}/{agent_result.model}"
        common = dict(
            finding_id=finding_id,
            file_path=finding.file_path,
            diff=agent_result.gate_report.diff,
            model_used=model_used,
        )
        if settings.auto_fix_dry_run:
            return FixRunResult(status="dry_run", **common)
        if settings.auto_fix_requires_approval:
            from git import Repo

            base_sha = Repo(local_path).head.commit.hexsha
            await _store_pending(scan_report, finding_id, {
                "file_path": finding.file_path,
                "patched_content": agent_result.proposal.patched_content,
                "base_sha": base_sha,
                "diff": common["diff"],
                "model_used": model_used,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            return FixRunResult(status="awaiting_approval", **common)
        return await _open_pr(
            scan_report, finding, local_path=local_path,
            patched_content=agent_result.proposal.patched_content, model_used=model_used,
        )
    except FixAgentError as e:
        raise AutoFixError(str(e))
    finally:
        if local_path and os.path.exists(local_path):
            shutil.rmtree(local_path, ignore_errors=True)


async def approve_fix(scan_report: ScanReport, finding_id: str) -> FixRunResult:
    if settings.auto_fix_dry_run:
        raise AutoFixError("AUTO_FIX_DRY_RUN is enabled — fixes are never applied")
    metadata = scan_report.metadata if isinstance(scan_report.metadata, dict) else {}
    pending = (metadata.get(PENDING_FIXES) or {}).get(finding_id)
    if not pending:
        raise AutoFixError(f"No pending fix for finding {finding_id}")
    finding = auto_fix_service._find_finding(scan_report, finding_id)
    if not finding:
        raise AutoFixError(f"Finding {finding_id} not found in scan report")

    repo_url = scan_report.git_metadata.repository_url
    branch = scan_report.git_metadata.branch
    token = await auto_fix_service._resolve_token(scan_report)

    local_path = None
    try:
        local_path = auto_fix_service._clone_repo(repo_url, branch, token)
        from git import Repo

        sha = Repo(local_path).head.commit.hexsha
        if sha != pending.get("base_sha"):
            raise AutoFixError("Base branch advanced since the fix was proposed — re-run auto-fix")
        result = await _open_pr(
            scan_report, finding, local_path=local_path,
            patched_content=pending["patched_content"],
            model_used=pending.get("model_used", ""),
        )
        new_metadata = dict(scan_report.metadata or {})
        remaining = dict(new_metadata.get(PENDING_FIXES) or {})
        remaining.pop(finding_id, None)
        scan_report.metadata = {**new_metadata, PENDING_FIXES: remaining}
        await scan_report.save()
        return result
    finally:
        if local_path and os.path.exists(local_path):
            shutil.rmtree(local_path, ignore_errors=True)
