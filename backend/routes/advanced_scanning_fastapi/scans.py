import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from utils.error_handling import get_safe_error_detail

from .background_tasks import (
    start_comprehensive_scan_task,
    start_dast_scan_task,
    start_iac_scan_task,
    start_sast_scan_task,
)
from .engine import is_target_allowed
from .models import (
    ComprehensiveScanRequest,
    DASTScanRequest,
    IaCScanRequest,
    SASTScanRequest,
    ScanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Scanning - Scans"])


@router.post("/scan/comprehensive", response_model=ScanResponse)
async def comprehensive_scan(
    request: ComprehensiveScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        user_id = str(current_user.id)
        repository_url = str(request.repository_url)
        target_url = str(request.target_url) if request.target_url else None

        if target_url and not is_target_allowed(target_url):
            raise HTTPException(
                status_code=403,
                detail=f"Target URL {target_url} is not in allowlist"
            )

        scan_task = start_comprehensive_scan_task(
            repository_url, target_url, request.config, user_id
        )
        background_tasks.add_task(scan_task)

        scan_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "estimated_duration": "15-30 minutes"},
            duration=0.0
        )

    except Exception as e:
        logger.error(f"Comprehensive scan failed: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Scan failed"))


@router.post("/scan/sast", response_model=ScanResponse)
async def sast_scan(
    request: SASTScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        user_id = str(current_user.id)
        repository_url = str(request.repository_url)

        scan_task = start_sast_scan_task(repository_url, request.languages, user_id)
        background_tasks.add_task(scan_task)

        scan_id = f"sast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "languages": request.languages},
            duration=0.0
        )

    except Exception as e:
        logger.error(f"SAST scan failed: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "SAST scan failed"))


@router.post("/scan/dast", response_model=ScanResponse)
async def dast_scan(
    request: DASTScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        user_id = str(current_user.id)
        target_url = str(request.target_url)

        if not is_target_allowed(target_url):
            raise HTTPException(
                status_code=403,
                detail=f"Target URL {target_url} is not in allowlist"
            )

        scan_task = start_dast_scan_task(target_url, user_id)
        background_tasks.add_task(scan_task)

        scan_id = f"dast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "target": target_url},
            duration=0.0
        )

    except Exception as e:
        logger.error(f"DAST scan failed: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "DAST scan failed"))


@router.post("/scan/iac", response_model=ScanResponse)
async def iac_scan(
    request: IaCScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        user_id = str(current_user.id)
        repository_url = str(request.repository_url)

        scan_task = start_iac_scan_task(repository_url, request.frameworks, user_id)
        background_tasks.add_task(scan_task)

        scan_id = f"iac_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "frameworks": request.frameworks},
            duration=0.0
        )

    except Exception as e:
        logger.error(f"IaC scan failed: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "IaC scan failed"))
