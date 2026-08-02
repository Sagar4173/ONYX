from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field, field_validator

from models.base import ScanType


def _validate_cron_expression(expression: str) -> str:
    """Validate a 5/6-field cron expression using APScheduler's parser."""
    from apscheduler.triggers.cron import CronTrigger

    try:
        CronTrigger.from_crontab(expression)
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {e}")
    return expression


class ScanSchedule(Document):
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    target: str
    scan_types: List[ScanType]
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    created_by: Indexed(str)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    next_run: Optional[datetime] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    misfire_grace_time: int = 60
    coalesce: bool = True
    max_instances: int = 1

    class Settings:
        name = "scan_schedules"


class ScheduleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    target: str
    scan_types: List[ScanType]
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    misfire_grace_time: int = 60
    coalesce: bool = True
    max_instances: int = 1

    @field_validator("cron_expression")
    @classmethod
    def _validate_cron(cls, v: str) -> str:
        return _validate_cron_expression(v)


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target: Optional[str] = None
    scan_types: Optional[List[ScanType]] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    misfire_grace_time: Optional[int] = None
    coalesce: Optional[bool] = None
    max_instances: Optional[int] = None

    @field_validator("cron_expression")
    @classmethod
    def _validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_cron_expression(v)
        return v


class ScheduleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    target: str
    scan_types: List[str]
    cron_expression: str
    timezone: str
    enabled: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    next_run: Optional[datetime] = None
    config: Dict[str, Any]
    misfire_grace_time: int
    coalesce: bool
    max_instances: int
