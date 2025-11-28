"""
Enterprise Features API Routes
Notification, Audit Logging, Data Retention, and Advanced Compliance endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from services.audit_logging_service import (
    get_audit_service,
    AuditEventType,
    AuditSeverity,
)
from services.data_retention_service import (
    get_retention_service,
    RetentionPolicyType,
    RetentionAction,
)
from services.advanced_compliance_service import (
    get_compliance_service,
    ComplianceFramework,
    ComplianceStatus,
)
from database import db_manager

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise Features"])


# Dependency to get database
async def get_database():
    """Get database instance"""
    if not db_manager.db:
        raise HTTPException(status_code=503, detail="Database not available")
    return db_manager.db


# ============================================================================
# Pydantic Models
# ============================================================================


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


# ============================================================================
# Audit Logging Endpoints
# ============================================================================


@router.get("/audit-logs/query")
async def query_audit_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_types: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db=Depends(get_database),
):
    """Query audit logs with filters"""
    try:
        audit_service = get_audit_service(db)

        # Parse parameters
        filters = {}
        if start_date:
            filters["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            filters["end_date"] = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        if event_types:
            filters["event_types"] = [
                AuditEventType(et) for et in event_types.split(",")
            ]
        if user_id:
            filters["user_id"] = user_id
        if resource_type:
            filters["resource_type"] = resource_type
        if severity:
            filters["severity"] = AuditSeverity(severity)

        result = await audit_service.query_audit_logs(
            **filters, limit=limit, skip=skip
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/user/{user_id}")
async def get_user_activity(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
):
    """Get user activity history"""
    try:
        audit_service = get_audit_service(db)
        result = await audit_service.get_user_activity(user_id, days, limit)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/resource/{resource_type}/{resource_id}")
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
):
    """Get complete history of changes to a resource"""
    try:
        audit_service = get_audit_service(db)
        result = await audit_service.get_resource_history(
            resource_type, resource_id, limit
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit-logs/compliance-report")
async def generate_compliance_audit_report(
    start_date: str = Body(...),
    end_date: str = Body(...),
    report_type: str = Body(default="full"),
    db=Depends(get_database),
):
    """Generate compliance audit report"""
    try:
        audit_service = get_audit_service(db)

        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        result = await audit_service.generate_compliance_report(start, end, report_type)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/export")
async def export_audit_logs(
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query(default="json"),
    db=Depends(get_database),
):
    """Export audit logs for archival"""
    try:
        audit_service = get_audit_service(db)

        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        result = await audit_service.export_audit_logs(start, end, format)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/verify/{event_id}")
async def verify_audit_log_integrity(
    event_id: str,
    db=Depends(get_database),
):
    """Verify integrity of an audit log entry"""
    try:
        audit_service = get_audit_service(db)
        result = await audit_service.verify_log_integrity(event_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Data Retention Endpoints
# ============================================================================


@router.post("/retention/policies")
async def create_retention_policy(
    policy: RetentionPolicyCreate,
    db=Depends(get_database),
):
    """Create a new data retention policy"""
    try:
        retention_service = get_retention_service(db)

        result = await retention_service.create_retention_policy(
            policy_type=RetentionPolicyType(policy.policy_type),
            retention_days=policy.retention_days,
            action=RetentionAction(policy.action),
            enabled=policy.enabled,
            metadata=policy.metadata,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/policies/{policy_id}/execute")
async def execute_retention_policy(
    policy_id: str,
    db=Depends(get_database),
):
    """Execute a specific retention policy"""
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.execute_retention_policy(policy_id)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/policies/execute-all")
async def execute_all_retention_policies(
    db=Depends(get_database),
):
    """Execute all enabled retention policies"""
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.execute_all_policies()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/statistics")
async def get_retention_statistics(
    db=Depends(get_database),
):
    """Get statistics about data retention and storage usage"""
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.get_retention_statistics()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/initialize-defaults")
async def initialize_default_retention_policies(
    db=Depends(get_database),
):
    """Initialize default retention policies"""
    try:
        retention_service = get_retention_service(db)
        result = await retention_service.initialize_default_policies()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Advanced Compliance Endpoints
# ============================================================================


@router.post("/compliance/assess")
async def assess_compliance(
    request: ComplianceAssessmentRequest,
    db=Depends(get_database),
):
    """Assess compliance against a specific framework"""
    try:
        compliance_service = get_compliance_service(db)

        # Get latest scan results
        scan_results = await db.scan_reports.find_one(
            {"project_id": request.project_id},
            sort=[("created_at", -1)],
        )

        if not scan_results:
            raise HTTPException(
                status_code=404, detail="No scan results found for project"
            )

        result = await compliance_service.assess_compliance(
            project_id=request.project_id,
            framework=ComplianceFramework(request.framework),
            scan_results=scan_results,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/report")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db=Depends(get_database),
):
    """Generate comprehensive compliance report"""
    try:
        compliance_service = get_compliance_service(db)

        frameworks = [ComplianceFramework(f) for f in request.frameworks]

        result = await compliance_service.generate_compliance_report(
            project_id=request.project_id,
            frameworks=frameworks,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/trend/{project_id}/{framework}")
async def get_compliance_trend(
    project_id: str,
    framework: str,
    days: int = Query(90, ge=1, le=365),
    db=Depends(get_database),
):
    """Get compliance trend over time"""
    try:
        compliance_service = get_compliance_service(db)

        result = await compliance_service.get_compliance_trend(
            project_id=project_id,
            framework=ComplianceFramework(framework),
            days=days,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/frameworks")
async def get_compliance_frameworks():
    """Get list of supported compliance frameworks"""
    return {
        "success": True,
        "frameworks": [
            {
                "id": framework.value,
                "name": framework.value.upper(),
                "description": f"{framework.value.upper()} compliance framework",
            }
            for framework in ComplianceFramework
        ],
    }


@router.get("/compliance/project/{project_id}/assessments")
async def get_project_assessments(
    project_id: str,
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_database),
):
    """Get recent compliance assessments for a project"""
    try:
        assessments = await db.compliance_assessments.find(
            {"project_id": project_id}
        ).sort("assessed_at", -1).limit(limit).to_list(length=limit)

        return {
            "success": True,
            "project_id": project_id,
            "assessments": assessments,
            "count": len(assessments),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def enterprise_features_health():
    """Health check for enterprise features"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "audit_logging": "enabled",
            "data_retention": "enabled",
            "advanced_compliance": "enabled",
        },
    }
