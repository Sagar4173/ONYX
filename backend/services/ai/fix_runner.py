"""Fix-run orchestration: propose -> gates -> approval -> PR (spec 4.2/4.3).

Statuses: dry_run (never persists) | awaiting_approval (pending stored) |
pr_created | verified (approval OFF or approved; verified when the re-scan
confirms the finding is gone). AUTO_FIX_REQUIRES_APPROVAL defaults ON
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


def _norm_path(p: Any) -> str:
    return str(p or "").replace("\\", "/")


def _path_matches(record_path: Any, finding_file_path: str) -> bool:
    rp = _norm_path(record_path)
    target = _norm_path(finding_file_path)
    return rp == target or rp.endswith("/" + target)


def _entry_matches_finding(entry: Dict[str, Any], finding: VulnerabilityFinding) -> bool:
    """Match a metadata.findings entry (raw scanner dict) to a finding.

    Real entries carry rule_id, not id; finding.id == rule_id on real scans.
    When both sides have a file path, it must match too so duplicate
    rule_ids on different files are disambiguated.
    """
    ident = entry.get("id") or entry.get("rule_id")
    if ident != finding.id:
        return False
    entry_path = entry.get("file_path")
    if entry_path and finding.file_path:
        return _path_matches(entry_path, finding.file_path)
    return True


async def verify_fix(*, repo_url: str, branch: str, finding: VulnerabilityFinding) -> Dict[str, Any]:
    """Re-scan the fix branch; the agent never grades its own work (spec 4.3.3)."""
    from services.ai.gateway import _scrub
    from services.scanning.scanners.real_scanner import RealSecurityScanner

    scanner = RealSecurityScanner()
    try:
        result = await scanner.scan_repository(repo_url, branch=branch)
    except Exception as e:
        return {"verified": None, "error": _scrub(e, 200)}
    remaining = [
        f'{rec.get("rule_id")} at {rec.get("file_path") or rec.get("filename") or "?"}'
        for rec in (result.get("detailed_findings") or [])
        if isinstance(rec, dict)
        and rec.get("rule_id") == finding.rule_id
        and _path_matches(rec.get("file_path") or rec.get("filename"), finding.file_path)
    ]
    return {
        "verified": not remaining,
        "remaining": remaining,
        "total_findings": result.get("total_findings", 0),
    }


def verification_markdown(v: Dict[str, Any]) -> str:
    if v.get("verified") is True:
        head = "✅ Verified — the original finding was not detected on this branch"
    elif v.get("verified") is False:
        head = "⚠️ Not verified — the original finding is still detected after re-scan"
    else:
        head = "❌ Unknown — the re-scan could not run"
    lines = ["## Verification (re-scan of this branch)", "", f"- {head}"]
    if "total_findings" in v:
        lines.append(f"- Total findings after fix: {v['total_findings']}")
    if v.get("remaining"):
        lines.append(f"- Remaining matching findings: {', '.join(str(x) for x in v['remaining'])}")
    if v.get("error"):
        lines.append(f"- Scanner error: `{v['error']}`")
    return "\n".join(lines)


async def _record_fix_outcome(
    scan_report: ScanReport, finding: VulnerabilityFinding, *, pr_url: str, verification: Dict[str, Any]
) -> None:
    metadata = scan_report.metadata if isinstance(scan_report.metadata, dict) else {}
    entries = metadata.get("findings")
    if not isinstance(entries, list):
        return
    updated, changed = [], False
    for entry in entries:
        if isinstance(entry, dict) and _entry_matches_finding(entry, finding):
            entry = {
                **entry,
                "fix_pr_url": pr_url,
                "fix_status": "verified" if verification.get("verified") else "pr_created",
            }
            changed = True
        updated.append(entry)
    if changed:
        scan_report.metadata = {**metadata, "findings": updated}
        await scan_report.save()


def get_fix_state(scan_report: ScanReport, finding_id: str) -> Dict[str, Any]:
    """Persisted fix state as a safe subset (never patched_content/base_sha).

    Outcome (findings entry fix_status) wins over a still-present pending key.
    """
    metadata = scan_report.metadata if isinstance(scan_report.metadata, dict) else {}
    entries = metadata.get("findings")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and (entry.get("id") or entry.get("rule_id")) == finding_id:
                status = entry.get("fix_status")
                if status in ("pr_created", "verified"):
                    return {
                        "status": status,
                        "finding_id": finding_id,
                        "file_path": entry.get("file_path"),
                        "pr_url": entry.get("fix_pr_url"),
                    }
    pending = metadata.get(PENDING_FIXES)
    if isinstance(pending, dict) and finding_id in pending:
        entry = pending[finding_id] if isinstance(pending[finding_id], dict) else {}
        return {
            "status": "awaiting_approval",
            "finding_id": finding_id,
            "file_path": entry.get("file_path"),
            "diff": entry.get("diff") or "",
            "model_used": entry.get("model_used") or "",
            "created_at": entry.get("created_at"),
        }
    return {"status": "none", "finding_id": finding_id}


async def discard_pending(scan_report: ScanReport, finding_id: str) -> bool:
    """Remove a pending proposal (idempotent). Returns True when one existed."""
    metadata = scan_report.metadata if isinstance(scan_report.metadata, dict) else {}
    pending = metadata.get(PENDING_FIXES)
    if not isinstance(pending, dict) or finding_id not in pending:
        return False
    remaining = {k: v for k, v in pending.items() if k != finding_id}
    updated = {**metadata}
    if remaining:
        updated[PENDING_FIXES] = remaining
    else:
        updated.pop(PENDING_FIXES, None)
    scan_report.metadata = updated
    await scan_report.save()
    return True


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
    verification = await verify_fix(repo_url=repo_url, branch=branch_name, finding=finding)
    pr_url, pr_number = await auto_fix_service._create_pr(
        repo_url=repo_url, branch=branch, branch_name=branch_name,
        finding=finding, token=token, scan_report=scan_report,
        body_extra=verification_markdown(verification),
    )
    await _record_fix_outcome(scan_report, finding, pr_url=pr_url, verification=verification)
    return FixRunResult(
        status="verified" if verification.get("verified") is True else "pr_created",
        finding_id=finding.id, file_path=finding.file_path,
        pr_url=pr_url, pr_number=pr_number, branch=branch_name,
        verification=verification, model_used=model_used,
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
    pending_map = dict(metadata.get(PENDING_FIXES) or {})
    pending = pending_map.get(finding_id)
    if not pending:
        raise AutoFixError(f"No pending fix for finding {finding_id}")
    # Claim the pending entry atomically before any await: a concurrent approve
    # then loses with "No pending fix" instead of double-opening a PR. The
    # read+pop above/below runs under the GIL with no suspension point, so it
    # is a single synchronous operation.
    pending_map.pop(finding_id)
    scan_report.metadata = {**metadata, PENDING_FIXES: pending_map}

    def _restore_pending() -> None:
        # Put the entry back on any failure after the claim so the user can
        # retry — but never clobber a newer pending fix added meanwhile.
        current = scan_report.metadata if isinstance(scan_report.metadata, dict) else {}
        remaining = dict(current.get(PENDING_FIXES) or {})
        if finding_id not in remaining:
            remaining[finding_id] = pending
            scan_report.metadata = {**current, PENDING_FIXES: remaining}

    finding = auto_fix_service._find_finding(scan_report, finding_id)
    if not finding:
        _restore_pending()
        raise AutoFixError(f"Finding {finding_id} not found in scan report")

    repo_url = scan_report.git_metadata.repository_url
    branch = scan_report.git_metadata.branch

    local_path = None
    try:
        # The pending content was gated against the propose-time path only
        # (single-file allowlist). If a rescan/metadata rewrite moved the
        # finding, committing it to the current path would bypass that gate.
        if pending.get("file_path") != finding.file_path:
            raise AutoFixError("Finding path changed since propose — re-run auto-fix")
        token = await auto_fix_service._resolve_token(scan_report)
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
        await scan_report.save()
        return result
    except BaseException:
        _restore_pending()
        raise
    finally:
        if local_path and os.path.exists(local_path):
            shutil.rmtree(local_path, ignore_errors=True)
