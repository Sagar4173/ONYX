import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from models.triage import BusinessContext, TriageResult
from models.user import User, UserRole
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_accessible_scan_report
from services.triage import triage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triage", tags=["Triage"])


async def _require_accessible_scan(scan_id: str, user) -> None:
    report = await get_accessible_scan_report(scan_id, str(user.id))
    if not report:
        raise HTTPException(status_code=404, detail="Scan not found")


@router.get("/{scan_id}", response_model=TriageResult)
async def get_triage(
    scan_id: str,
    top_n: int = Query(20, ge=1, le=200),
    user: User = Depends(get_current_user),
):
    await _require_accessible_scan(scan_id, user)
    try:
        result = await triage_service.triage_scan(scan_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        result.ranked_findings = result.ranked_findings[:top_n]
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Triage failed for scan %s: %s", scan_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Triage processing failed")


@router.post("/{scan_id}", response_model=TriageResult)
async def rescore_triage(
    scan_id: str,
    context: BusinessContext,
    top_n: int = Query(20, ge=1, le=200),
    user: User = Depends(get_current_user),
):
    await _require_accessible_scan(scan_id, user)
    try:
        result = await triage_service.triage_scan(scan_id, business_context=context)
        if result is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        result.ranked_findings = result.ranked_findings[:top_n]
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Rescore triage failed for scan %s: %s", scan_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Triage rescoring failed")
