"""Investigate-finding endpoint (spec 4.4, 5.1 P4)."""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config import settings
from models.user import User
from routes.ai_chat import screen_or_block
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_accessible_scan_report
from services.ai.investigate_agent import (
    InvestigateAgentError,
    InvestigateReport,
    run_investigate_agent,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["Investigate"])


class InvestigateRequest(BaseModel):
    scan_id: str
    finding_id: str
    question: Optional[str] = Field(None, max_length=2000)


class InvestigateResponse(BaseModel):
    report: InvestigateReport
    provider: str
    model: str
    usage: Dict[str, Any]


def _find_finding(report, finding_id: str):
    for scan_result in report.scan_results:
        for finding in scan_result.findings:
            if finding.id == finding_id:
                return finding
    return None


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate_finding(
    payload: InvestigateRequest,
    user: User = Depends(get_current_user),
):
    if not settings.investigate_agent_enabled:
        raise HTTPException(status_code=503, detail="Investigate agent is disabled")
    report = await get_accessible_scan_report(payload.scan_id, str(user.id))
    if not report:
        raise HTTPException(status_code=404, detail="Scan not found")
    finding = _find_finding(report, payload.finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    if payload.question:
        await screen_or_block(payload.question)

    try:
        result = await run_investigate_agent(
            finding=finding, report=report, question=payload.question or ""
        )
    except InvestigateAgentError as e:
        logger.error("Investigate failed for scan %s finding %s: %s",
                     payload.scan_id, payload.finding_id, e)
        raise HTTPException(status_code=503, detail="Investigation is temporarily unavailable")
    except Exception as e:
        logger.error("Investigate crashed for scan %s finding %s: %s",
                     payload.scan_id, payload.finding_id, e, exc_info=True)
        raise HTTPException(status_code=502, detail=get_safe_error_detail(e))

    return InvestigateResponse(
        report=result.report, provider=result.provider, model=result.model, usage=result.usage
    )
