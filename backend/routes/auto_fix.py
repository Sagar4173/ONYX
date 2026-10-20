import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_accessible_scan_report
from services.ai.fix_runner import (
    FixConflictError,
    approve_fix,
    discard_pending,
    get_fix_state,
    propose_fix,
)
from services.scm.auto_fix_service import AutoFixError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Auto-Fix PRs"])


class FixRunResponse(BaseModel):
    status: str  # dry_run | awaiting_approval | pr_created | verified
    finding_id: str
    file_path: str
    diff: str = ""
    gate_failures: List[str] = Field(default_factory=list)
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    model_used: str = ""


async def _report_or_404(scan_id: str, user):
    report = await get_accessible_scan_report(scan_id, str(user.id))
    if not report:
        raise HTTPException(status_code=404, detail="Scan report not found or access denied")
    return report


@router.post("/{scan_id}/auto-fix", response_model=FixRunResponse)
async def trigger_auto_fix(scan_id: str, finding_id: str, user=Depends(get_current_user)):
    report = await _report_or_404(scan_id, user)
    try:
        return FixRunResponse(**vars(await propose_fix(report, finding_id)))
    except FixConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AutoFixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Auto-fix propose failed for scan {scan_id}, finding {finding_id}: {e}")
        raise HTTPException(status_code=502, detail="Auto-fix failed. Please try again later.")


@router.post("/{scan_id}/auto-fix/{finding_id}/approve", response_model=FixRunResponse)
async def approve_auto_fix(scan_id: str, finding_id: str, user=Depends(get_current_user)):
    report = await _report_or_404(scan_id, user)
    try:
        return FixRunResponse(**vars(await approve_fix(report, finding_id)))
    except AutoFixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Auto-fix approve failed for scan {scan_id}, finding {finding_id}: {e}")
        raise HTTPException(status_code=502, detail="Auto-fix approval failed. Please try again later.")


class FixStateResponse(BaseModel):
    status: str  # none | awaiting_approval | pr_created | verified
    finding_id: str
    file_path: Optional[str] = None
    diff: str = ""
    pr_url: Optional[str] = None
    model_used: str = ""
    created_at: Optional[str] = None


@router.get("/{scan_id}/auto-fix/{finding_id}", response_model=FixStateResponse)
async def get_auto_fix_state(
    scan_id: str,
    finding_id: str,
    file_path: Optional[str] = None,
    user=Depends(get_current_user),
):
    report = await _report_or_404(scan_id, user)
    return FixStateResponse(**get_fix_state(report, finding_id, file_path=file_path))


class DiscardResponse(BaseModel):
    status: str = "discarded"


@router.delete("/{scan_id}/auto-fix/{finding_id}", response_model=DiscardResponse)
async def discard_auto_fix(scan_id: str, finding_id: str, user=Depends(get_current_user)):
    report = await _report_or_404(scan_id, user)
    try:
        await discard_pending(report, finding_id)
    except FixConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return DiscardResponse()
