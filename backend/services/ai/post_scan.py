"""Background post-scan AI analysis.

Enqueued after the scan hits 100% so AI latency never blocks scan
completion (spec: "AI blocks scan at progress 90" -> "AI enqueued after
scan 100%, concurrency 1-2 per provider").
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from config import settings
from models.report import ScanReport
from services.ai.ai_processor import get_ai_processor
from services.ai.gateway import _scrub

logger = logging.getLogger(__name__)

_semaphore: Optional[asyncio.Semaphore] = None
_tasks: Set[asyncio.Task] = set()


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(max(1, settings.ai_post_scan_concurrency))
    return _semaphore


async def _set_ai_status(scan_id: str, status: str, error: Optional[str] = None) -> None:
    update: Dict[str, object] = {
        "metadata.ai_status": status,
        # always written so a stale error is cleared on running/complete
        "metadata.ai_error": _scrub(error, limit=200) if error else None,
        "updated_at": datetime.now(timezone.utc),
    }
    try:
        await ScanReport.find_one({"scan_id": scan_id}).update({"$set": update})
    except Exception as e:
        logger.warning("Failed to set ai_status=%s for %s: %s", status, scan_id, e)


async def run_post_scan_ai(scan_id: str) -> None:
    """Analyze scan results in the background; status: running -> complete/failed."""
    async with _get_semaphore():
        await _set_ai_status(scan_id, "running")
        try:
            report = await ScanReport.find_one({"scan_id": scan_id})
            if report is None or report.scan_results is None:
                logger.warning("Post-scan AI skipped: no report/results for %s", scan_id)
                await _set_ai_status(scan_id, "failed", "report unavailable")
                return

            processor = get_ai_processor()
            project_context = {
                "project_name": report.project_name,
                "repository_url": str(report.git_metadata.repository_url)
                if report.git_metadata else "",
                "branch": report.git_metadata.branch if report.git_metadata else "main",
            }
            ai_analysis = await processor.analyze_scan_results(
                report.scan_results, project_context
            )
            await ScanReport.find_one({"scan_id": scan_id}).update(
                {
                    "$set": {
                        "ai_analysis": ai_analysis.model_dump(),
                        "updated_at": datetime.now(timezone.utc),
                    }
                }
            )
            await _set_ai_status(scan_id, "complete")
            logger.info(
                "Post-scan AI analysis completed for scan %s (%s)",
                scan_id,
                ai_analysis.model_used,
            )
        except Exception as e:
            logger.error("Post-scan AI analysis failed for scan %s: %s", scan_id, e)
            await _set_ai_status(scan_id, "failed", str(e))


def schedule_post_scan_ai(scan_id: str) -> None:
    """Fire-and-forget enqueue; safe to call from request handlers."""
    task = asyncio.create_task(run_post_scan_ai(scan_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


def reset_post_scan_state() -> None:
    """Test hook: forget the semaphore and pending task refs."""
    global _semaphore
    _semaphore = None
    _tasks.clear()
