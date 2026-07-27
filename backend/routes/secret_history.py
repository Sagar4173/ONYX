import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.user import User, UserRole
from routes.dependencies import get_current_user, require_role
from services.scanning.secrets.secret_history_service import SecretHistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/secret-history", tags=["Secret History"])

secret_history_service = SecretHistoryService()


@router.get("")
async def list_secret_history(
    project_name: str = Query(..., description="Project/repository name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, regex="^(active|resolved|dismissed)$"),
    user: User = Depends(get_current_user),
):
    try:
        result = await secret_history_service.get_secret_history(
            project_name=project_name,
            limit=limit,
            offset=offset,
            status=status,
        )
        return result
    except Exception as e:
        logger.error("Failed to list secret history: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list secret history")


@router.get("/trends")
async def get_secret_trends(
    project_name: str = Query(..., description="Project/repository name"),
    limit: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
):
    try:
        trends = await secret_history_service.get_trends(
            project_name=project_name,
            limit=limit,
        )
        return {"trends": trends}
    except Exception as e:
        logger.error("Failed to get secret trends: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get secret trends")


@router.get("/summary")
async def get_secret_summary(
    project_name: str = Query(..., description="Project/repository name"),
    user: User = Depends(get_current_user),
):
    try:
        summary = await secret_history_service.get_summary(project_name=project_name)
        return summary
    except Exception as e:
        logger.error("Failed to get secret summary: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get secret summary")


@router.patch("/{record_id}")
async def update_secret_status(
    record_id: str,
    status: str = Query(..., regex="^(active|resolved|dismissed)$"),
    user: User = Depends(require_role(UserRole.SECURITY_MANAGER)),
):
    try:
        success = await secret_history_service.update_status(record_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Secret record not found")
        return {"success": True, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update secret status: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update secret status")
