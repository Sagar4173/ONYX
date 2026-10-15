"""AI feature-flag/config discovery for the frontend (UX Track, spec Phase 0)."""
from fastapi import APIRouter, Depends

from config import settings
from models.user import User
from routes.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Features"])


@router.get("/features")
async def ai_features(user: User = Depends(get_current_user)) -> dict:
    return {
        "investigate_agent_enabled": settings.investigate_agent_enabled,
        "ml_isolation_forest_enabled": settings.ml_isolation_forest_enabled,
        "ml_min_training_scans": settings.ml_min_training_scans,
        "ml_training_window_days": settings.ml_training_window_days,
        "auto_fix_requires_approval": settings.auto_fix_requires_approval,
        "ai_rate_limit_rpd": settings.ai_rate_limit_rpd,
    }
