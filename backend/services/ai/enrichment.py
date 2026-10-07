"""Severity-stratified top-N remediation enrichment for scan findings.

Token budgeting: critical/high findings are always selected first, then
medium, low, info - capped at settings.ai_enrich_top_n (default 10).
Failures never propagate: enrichment is best-effort enrichment only.
"""
import logging
from typing import Any, Dict, List, Optional

from config import settings
from services.ai.ai_processor import get_ai_processor

logger = logging.getLogger(__name__)

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def select_findings_for_enrichment(
    findings: List[Dict[str, Any]],
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Pick the highest-value findings to enrich (stable order within severity)."""
    if top_n is None:
        top_n = settings.ai_enrich_top_n
    if top_n <= 0 or not findings:
        return []
    ranked = sorted(
        findings,
        key=lambda f: _SEVERITY_RANK.get(str(f.get("severity", "")).lower(), 5),
    )
    return ranked[:top_n]


async def enrich_detailed_findings(
    findings: List[Dict[str, Any]],
    *,
    top_n: Optional[int] = None,
    batch_size: int = 5,
) -> bool:
    """Enrich the selected subset in place. Returns True if enrichment ran."""
    try:
        selected = select_findings_for_enrichment(findings, top_n)
        if not selected:
            return False
        processor = get_ai_processor()
        await processor.enrich_findings_with_remediation(selected, batch_size=batch_size)
        return True
    except Exception as e:
        logger.warning("AI remediation enrichment skipped: %s", e)
        return False
