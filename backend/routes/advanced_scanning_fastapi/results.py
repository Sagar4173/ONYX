import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from database import db_manager
from models.user import User
from routes.dependencies import get_current_user
from utils.error_handling import get_safe_error_detail

from .engine import get_scanner_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Scanning - Results"])


@router.get("/scan/{scan_id}/findings")
async def get_scan_findings(
    scan_id: str,
    severity: Optional[str] = None,
    scanner: Optional[str] = None,
    scan_type: Optional[str] = None,
    suppressed: bool = False,
    current_user: User = Depends(get_current_user)
):
    try:
        report = await db_manager.get_scan_report(scan_id)

        if not report:
            raise HTTPException(status_code=404, detail="Scan not found")

        findings = report['results']['findings']

        filtered_findings = []
        for finding in findings:
            if finding.get('suppressed', False) and not suppressed:
                continue

            if severity and finding.get('severity') != severity:
                continue
            if scanner and finding.get('source') != scanner:
                continue
            if scan_type and finding.get('scan_type') != scan_type:
                continue

            filtered_findings.append(finding)

        return {
            'success': True,
            'scan_id': scan_id,
            'findings': filtered_findings,
            'total_count': len(filtered_findings),
            'filters_applied': {
                'severity': severity,
                'scanner': scanner,
                'scan_type': scan_type,
                'include_suppressed': suppressed
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan findings: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get findings"))


@router.get("/scan/{scan_id}/summary")
async def get_scan_summary(
    scan_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        report = await db_manager.get_scan_report(scan_id)

        if not report:
            raise HTTPException(status_code=404, detail="Scan not found")

        results = report['results']

        return {
            'success': True,
            'scan_id': scan_id,
            'summary': results.get('summary', {}),
            'scanners': results.get('scanners', {}),
            'duration': results.get('duration', 0),
            'start_time': results.get('start_time'),
            'end_time': results.get('end_time')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan summary: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get summary"))


@router.get("/config")
async def get_scanner_config(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        engine = get_scanner_engine()
        config = engine.config

        return {
            'success': True,
            'config': {
                'max_concurrent_scans': config.max_concurrent_scans,
                'scan_timeout': config.scan_timeout,
                'dast_target_allowlist': config.dast_target_allowlist,
                'dast_rate_limit': config.dast_rate_limit,
                'dast_max_depth': config.dast_max_depth,
                'sast_languages': config.sast_languages,
                'sast_exclude_patterns': config.sast_exclude_patterns,
                'iac_frameworks': config.iac_frameworks,
                'suppression_file': config.suppression_file,
                'allow_inline_suppressions': config.allow_inline_suppressions
            }
        }

    except Exception as e:
        logger.error(f"Failed to get scanner config: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get config"))
