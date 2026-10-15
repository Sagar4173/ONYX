"""ML triage endpoints (Phase 4, spec 5.1 P4). Operator-driven; no scan-path coupling."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from models.user import User, UserRole
from routes.dependencies import get_current_user
from services.ai.ml_anomaly_detection_engine import get_ml_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ML"])


def _sklearn_available() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


@router.get("/status")
async def ml_status(user: User = Depends(get_current_user)):
    engine = get_ml_engine()
    active = engine.models.get("anomaly_detector")
    return {
        "isolation_forest_enabled": settings.ml_isolation_forest_enabled,
        "min_training_scans": settings.ml_min_training_scans,
        "training_window_days": settings.ml_training_window_days,
        "model_trained": active is not None,
        "sklearn_available": _sklearn_available(),
        "active_model": (
            {
                "model_id": active["metrics"].model_id,
                "training_data_size": active["metrics"].training_data_size,
                "anomaly_rate": active["metrics"].anomaly_rate,
                "last_trained": active["metrics"].last_trained,
            }
            if active
            else None
        ),
    }


@router.post("/train")
async def ml_train(user: User = Depends(get_current_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not settings.ml_isolation_forest_enabled:
        raise HTTPException(status_code=409, detail="IsolationForest is disabled (ML_ISOLATION_FOREST_ENABLED=false)")
    metrics = await get_ml_engine().train_anomaly_model()
    if metrics is None:
        raise HTTPException(status_code=409, detail="Training skipped: insufficient scan history or sklearn unavailable")
    return {
        "model_id": metrics.model_id,
        "training_data_size": metrics.training_data_size,
        "anomaly_rate": metrics.anomaly_rate,
        "score_mean": metrics.score_mean,
        "score_std": metrics.score_std,
        "last_trained": metrics.last_trained,
    }


@router.get("/anomalies")
async def ml_anomalies(user: User = Depends(get_current_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return await get_ml_engine().get_anomaly_dashboard()
