import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from database import db_manager
from models.user import User
from routes.dependencies import get_current_user
from utils.error_handling import get_safe_error_detail

from .models import SuppressionRuleRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Scanning - Suppressions"])


@router.get("/suppressions")
async def get_suppressions(
    repository_url: str,
    current_user: User = Depends(get_current_user)
):
    try:
        suppressions = await db_manager.get_suppression_rules(repository_url)

        return {
            'success': True,
            'suppressions': suppressions
        }

    except Exception as e:
        logger.error(f"Failed to get suppressions: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get suppressions"))


@router.post("/suppressions")
async def create_suppression(
    request: SuppressionRuleRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        user_id = str(current_user.id)

        suppression_rule = {
            'id': str(datetime.now().timestamp()),
            'name': request.name,
            'description': request.description,
            'repository_url': str(request.repository_url),
            'rule_ids': request.rule_ids,
            'file_patterns': request.file_patterns,
            'severities': request.severities,
            'scanners': request.scanners,
            'created_by': user_id,
            'created_at': datetime.now(timezone.utc)
        }

        rule_id = await db_manager.save_suppression_rule(suppression_rule)

        return {
            'success': True,
            'suppression_id': rule_id,
            'message': 'Suppression rule created successfully'
        }

    except Exception as e:
        logger.error(f"Failed to create suppression: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to create suppression"))
