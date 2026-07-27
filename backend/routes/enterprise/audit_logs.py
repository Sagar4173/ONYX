import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from models.user import User, UserRole
from routes.dependencies import auth_service
from routes.enterprise.dependencies import get_database
from services.analytics.audit_logging_service import (
    AuditEventType,
    AuditSeverity,
    get_audit_service,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/audit-logs/query")
async def query_audit_logs(
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
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
    try:
        audit_service = get_audit_service(db)

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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/audit-logs/user/{user_id}")
async def get_user_activity(
    user_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
):
    try:
        audit_service = get_audit_service(db)
        result = await audit_service.get_user_activity(user_id, days, limit)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/audit-logs/resource/{resource_type}/{resource_id}")
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
):
    try:
        audit_service = get_audit_service(db)
        result = await audit_service.get_resource_history(
            resource_type, resource_id, limit
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/audit-logs/compliance-report")
async def generate_compliance_audit_report(
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    start_date: str = Body(...),
    end_date: str = Body(...),
    report_type: str = Body(default="full"),
    db=Depends(get_database),
):
    try:
        audit_service = get_audit_service(db)

        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        result = await audit_service.generate_compliance_report(start, end, report_type)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/audit-logs/export")
async def export_audit_logs(
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query(default="json"),
    db=Depends(get_database),
):
    try:
        audit_service = get_audit_service(db)

        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        result = await audit_service.export_audit_logs(start, end, format)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/audit-logs/verify/{event_id}")
async def verify_audit_log_integrity(
    event_id: str,
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    db=Depends(get_database),
):
    try:
        audit_service = get_audit_service(db)
        result = await audit_service.verify_log_integrity(event_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/audit-logs")
async def get_audit_logs(
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_types: Optional[str] = Query(None),
    users: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db=Depends(get_database),
):
    try:
        try:
            audit_logs_collection = db["audit_logs"]

            query = {}
            if search:
                query["$or"] = [
                    {"event_type": {"$regex": search, "$options": "i"}},
                    {"user_id": {"$regex": search, "$options": "i"}},
                    {"details": {"$regex": search, "$options": "i"}}
                ]
            if severity:
                query["severity"] = severity
            if event_types:
                query["event_type"] = {"$in": event_types.split(",")}

            total = await audit_logs_collection.count_documents(query)

            cursor = audit_logs_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            logs = await cursor.to_list(length=limit)

            for log in logs:
                if "_id" in log:
                    log["id"] = str(log["_id"])
                    del log["_id"]
                if "timestamp" in log and hasattr(log["timestamp"], "isoformat"):
                    log["timestamp"] = log["timestamp"].isoformat()

            return {
                "success": True,
                "logs": logs,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error("Failed to query audit logs: %s", e, exc_info=True)
            return {
                "success": False,
                "logs": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }

    except Exception as e:
        logger.error("Failed to query audit logs (outer): %s", e, exc_info=True)
        return {
            "success": False,
            "logs": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }


@router.get("/audit-logs/users")
async def get_audit_users(
    current_user: User = Depends(auth_service.require_role(UserRole.SECURITY_MANAGER)),
    db=Depends(get_database),
):
    try:
        try:
            audit_logs_collection = db["audit_logs"]
            users = await audit_logs_collection.distinct("user_id")
            return {
                "success": True,
                "users": [u for u in users if u]
            }
        except Exception as e:
            logger.error("Failed to query audit users: %s", e, exc_info=True)
            return {
                "success": False,
                "users": []
            }
    except Exception as e:
        logger.error("Failed to query audit users (outer): %s", e, exc_info=True)
        return {
            "success": False,
            "users": []
        }


@router.get("/retention-policies")
async def get_retention_policies(
    current_user: User = Depends(auth_service.get_current_user),
    db=Depends(get_database),
):
    try:
        try:
            policies_collection = db["retention_policies"]
            policies = await policies_collection.find().to_list(100)

            for policy in policies:
                if "_id" in policy:
                    policy["id"] = str(policy["_id"])
                    del policy["_id"]

            return {
                "success": True,
                "policies": policies
            }
        except Exception as e:
            logger.error("Failed to query retention policies: %s", e, exc_info=True)
            return {
                "success": False,
                "policies": []
            }
    except Exception as e:
        logger.error("Failed to query retention policies (outer): %s", e, exc_info=True)
        return {
            "success": False,
            "policies": []
        }
