import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.scanning.utils.comparison import get_scan_comparison_service
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scans", tags=["Enterprise Security - Scan Comparison"])


class ScanCompareRequest(BaseModel):
    base_scan_id: str = Field(..., description="ID of the baseline scan")
    compare_scan_id: str = Field(..., description="ID of the scan to compare")
    include_unchanged: bool = Field(default=False, description="Include unchanged findings")


@router.post("/compare")
async def compare_scans(request: ScanCompareRequest) -> Dict[str, Any]:
    try:
        comparison_service = get_scan_comparison_service()

        result = await comparison_service.compare_scans(
            base_scan_id=request.base_scan_id,
            compare_scan_id=request.compare_scan_id,
            include_unchanged=request.include_unchanged
        )

        report = await comparison_service.generate_comparison_report(result)

        return {
            "success": True,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=get_safe_error_detail(e, "Resource not found"))
    except Exception as e:
        logger.error(f"Error comparing scans: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/{project_id}/compare-with-latest")
async def compare_with_latest(
    project_id: str,
    scan_id: str = Query(..., description="Scan ID to compare with latest")
):
    try:
        comparison_service = get_scan_comparison_service()

        result = await comparison_service.compare_with_latest(
            project_id=project_id,
            scan_id=scan_id
        )

        report = await comparison_service.generate_comparison_report(result)

        return {
            "success": True,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=get_safe_error_detail(e, "Resource not found"))
    except Exception as e:
        logger.error(f"Error comparing with latest: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/{project_id}/branches/compare")
async def compare_branches(
    project_id: str,
    base_branch: str = Query(..., description="Base branch name"),
    compare_branch: str = Query(..., description="Branch to compare")
):
    try:
        comparison_service = get_scan_comparison_service()

        result = await comparison_service.compare_branches(
            project_id=project_id,
            base_branch=base_branch,
            compare_branch=compare_branch
        )

        report = await comparison_service.generate_comparison_report(result)

        return {
            "success": True,
            "base_branch": base_branch,
            "compare_branch": compare_branch,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=get_safe_error_detail(e, "Resource not found"))
    except Exception as e:
        logger.error(f"Error comparing branches: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/{project_id}/remediation-progress")
async def get_remediation_progress(
    project_id: str,
    days: int = Query(30, ge=7, le=365)
):
    try:
        comparison_service = get_scan_comparison_service()

        progress = await comparison_service.get_remediation_progress(
            project_id=project_id,
            days=days
        )

        return {
            "success": True,
            "data": progress
        }
    except Exception as e:
        logger.error(f"Error fetching remediation progress: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/{project_id}/fix-velocity")
async def get_fix_velocity(
    project_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    try:
        comparison_service = get_scan_comparison_service()

        velocity = await comparison_service.get_fix_velocity(
            project_id=project_id,
            severity=severity
        )

        return {
            "success": True,
            "data": velocity
        }
    except Exception as e:
        logger.error(f"Error fetching fix velocity: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
