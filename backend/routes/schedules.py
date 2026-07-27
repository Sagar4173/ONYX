import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from models.schedule import ScanSchedule, ScheduleCreate, ScheduleResponse, ScheduleUpdate
from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


def _get_scheduler():
    scheduler = ServiceRegistry.get_scan_scheduler()
    if not scheduler:
        from services.scheduling.scheduler_service import ScanSchedulerService
        scheduler = ScanSchedulerService()
        scheduler.initialize()
    return scheduler


def _schedule_to_response(schedule: ScanSchedule) -> dict:
    return {
        "id": str(schedule.id),
        "name": schedule.name,
        "description": schedule.description,
        "project_id": schedule.project_id,
        "target": schedule.target,
        "scan_types": [st.value if hasattr(st, "value") else st for st in schedule.scan_types],
        "cron_expression": schedule.cron_expression,
        "timezone": schedule.timezone,
        "enabled": schedule.enabled,
        "created_by": schedule.created_by,
        "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
        "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
        "last_status": schedule.last_status,
        "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
        "config": schedule.config,
        "misfire_grace_time": schedule.misfire_grace_time,
        "coalesce": schedule.coalesce,
        "max_instances": schedule.max_instances,
    }


@router.get("")
async def list_schedules(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")

        schedules = await _get_scheduler().list_schedules(project_id)

        if not is_admin:
            schedules = [s for s in schedules if s.created_by == user_id]

        return JSONResponse(
            status_code=200,
            content={"schedules": [_schedule_to_response(s) for s in schedules]},
        )
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to list schedules"))


@router.post("")
async def create_schedule(
    data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        schedule = ScanSchedule(
            name=data.name,
            description=data.description,
            project_id=data.project_id,
            target=data.target,
            scan_types=data.scan_types,
            cron_expression=data.cron_expression,
            timezone=data.timezone,
            enabled=data.enabled,
            created_by=str(current_user.id),
            config=data.config,
            misfire_grace_time=data.misfire_grace_time,
            coalesce=data.coalesce,
            max_instances=data.max_instances,
        )
        schedule = await _get_scheduler().create_schedule(schedule)
        return JSONResponse(status_code=201, content=_schedule_to_response(schedule))
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to create schedule"))


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        schedule = await _get_scheduler().get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")
        if not is_admin and schedule.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this schedule")

        return JSONResponse(status_code=200, content=_schedule_to_response(schedule))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get schedule"))


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        existing = await _get_scheduler().get_schedule(schedule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule not found")

        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")
        if not is_admin and existing.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this schedule")

        update_data = data.model_dump(exclude_unset=True)
        schedule = await _get_scheduler().update_schedule(schedule_id, update_data)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return JSONResponse(status_code=200, content=_schedule_to_response(schedule))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to update schedule"))


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        existing = await _get_scheduler().get_schedule(schedule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule not found")

        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")
        if not is_admin and existing.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this schedule")

        deleted = await _get_scheduler().delete_schedule(schedule_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return JSONResponse(status_code=200, content={"message": "Schedule deleted successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to delete schedule"))


@router.post("/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        existing = await _get_scheduler().get_schedule(schedule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule not found")

        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")
        if not is_admin and existing.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this schedule")

        triggered = await _get_scheduler().run_now(schedule_id)
        if not triggered:
            raise HTTPException(status_code=400, detail="Failed to trigger schedule")

        return JSONResponse(status_code=200, content={"message": "Scan triggered successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger schedule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to trigger schedule"))


@router.patch("/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        existing = await _get_scheduler().get_schedule(schedule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule not found")

        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")
        if not is_admin and existing.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this schedule")

        schedule = await _get_scheduler().toggle_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return JSONResponse(status_code=200, content=_schedule_to_response(schedule))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle schedule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to toggle schedule"))


@router.get("/{schedule_id}/history")
async def get_schedule_history(
    schedule_id: str,
    limit: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        existing = await _get_scheduler().get_schedule(schedule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule not found")

        user_id = str(current_user.id)
        is_admin = current_user.role in ("admin", "ADMIN")
        if not is_admin and existing.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this schedule")

        history = await _get_scheduler().get_schedule_history(schedule_id, limit)
        return JSONResponse(status_code=200, content={"history": history})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule history: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get schedule history"))
