from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    severity: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    skip: int = Field(default=0, ge=0)


class RetentionPolicyCreate(BaseModel):
    policy_type: str
    retention_days: int = Field(gt=0)
    action: str
    enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ComplianceAssessmentRequest(BaseModel):
    project_id: str
    framework: str
    scan_id: Optional[str] = None


class ComplianceReportRequest(BaseModel):
    project_id: str
    frameworks: List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CreateComplianceAssessmentRequest(BaseModel):
    project_id: str
    frameworks: List[str]
