import logging

from fastapi import APIRouter, Depends, HTTPException

from models.report import ScanReport
from routes.dependencies import get_current_user
from services.scm.auto_fix_service import AutoFixError, auto_fix_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Auto-Fix PRs"])


@router.post("/{scan_id}/auto-fix")
async def trigger_auto_fix(
    scan_id: str,
    finding_id: str,
    user=Depends(get_current_user),
):
    report = await ScanReport.find_one({"scan_id": scan_id, "owner_id": user.user_id})
    if not report:
        report = await ScanReport.find_one({"scan_id": scan_id})
        if not report:
            raise HTTPException(
                status_code=404, detail="Scan report not found or access denied"
            )

    try:
        result = await auto_fix_service.create_auto_fix_pr(report, finding_id)
        return result
    except AutoFixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Auto-fix failed for scan {scan_id}, finding {finding_id}: {e}")
        raise HTTPException(
            status_code=502, detail=f"Auto-fix failed: {str(e)}"
        )
