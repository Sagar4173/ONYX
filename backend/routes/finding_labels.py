"""Per-finding triage labels (spec 5.1 P4; UX-track triage UI backend)."""
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models.report import ScanReport
from models.user import User
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_accessible_scan_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Finding Labels"])

TRIAGE_CACHE_KEY = "triage"


class LabelRequest(BaseModel):
    label: Optional[Literal["accepted", "false_positive", "dismissed", "untriaged"]] = None


class LabelResponse(BaseModel):
    scan_id: str
    finding_id: str
    triage_label: Optional[str] = None


def _find_finding(report: ScanReport, finding_id: str):
    for scan_result in report.scan_results:
        for finding in scan_result.findings:
            if finding.id == finding_id:
                return finding
    return None


@router.post("/{scan_id}/findings/{finding_id}/label", response_model=LabelResponse)
async def set_finding_label(
    scan_id: str,
    finding_id: str,
    body: LabelRequest,
    user: User = Depends(get_current_user),
):
    report = await get_accessible_scan_report(scan_id, str(user.id))
    if not report:
        raise HTTPException(status_code=404, detail="Scan not found")
    finding = _find_finding(report, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    new_label = None if body.label in (None, "untriaged") else body.label
    finding.triage_label = new_label

    # Cached triage was computed without this label - drop it so the next
    # GET /triage re-ranks with the new signal (A3).
    metadata = report.metadata if isinstance(report.metadata, dict) else {}
    if TRIAGE_CACHE_KEY in metadata:
        report.metadata = {k: v for k, v in metadata.items() if k != TRIAGE_CACHE_KEY}
    await report.save()
    logger.info("Finding %s on scan %s labeled %r", finding_id, scan_id, new_label)
    return LabelResponse(scan_id=scan_id, finding_id=finding_id, triage_label=new_label)
