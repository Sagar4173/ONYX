import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from routes.enterprise.dependencies import get_database
from routes.enterprise.schemas import (
    ComplianceAssessmentRequest,
    ComplianceReportRequest,
    CreateComplianceAssessmentRequest,
)
from services.compliance.advanced_compliance_service import (
    ComplianceFramework,
    get_compliance_service,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/compliance/assess")
async def assess_compliance(
    request: ComplianceAssessmentRequest,
    db=Depends(get_database),
):
    try:
        compliance_service = get_compliance_service(db)

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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/compliance/report")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db=Depends(get_database),
):
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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/compliance/trend/{project_id}/{framework}")
async def get_compliance_trend(
    project_id: str,
    framework: str,
    days: int = Query(90, ge=1, le=365),
    db=Depends(get_database),
):
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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/compliance/frameworks")
async def get_compliance_frameworks() -> Dict[str, Any]:
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


@router.get("/compliance/assessments")
async def get_compliance_assessments(
    framework: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db=Depends(get_database),
):
    try:
        query = {"frameworks": {"$exists": True}}
        if framework:
            query["frameworks"] = framework
        if status:
            query["status"] = status

        try:
            assessments_collection = db["compliance_assessments"]
            total = await assessments_collection.count_documents(query)
            cursor = assessments_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            assessments = await cursor.to_list(length=limit)

            for assessment in assessments:
                if "_id" in assessment:
                    assessment["id"] = str(assessment["_id"])
                    del assessment["_id"]

                for date_field in ["assessed_at", "created_at", "assessment_date"]:
                    if date_field in assessment and hasattr(assessment[date_field], "isoformat"):
                        assessment[date_field] = assessment[date_field].isoformat()

                if not assessment.get("assessment_date"):
                    assessment["assessment_date"] = (
                        assessment.get("assessed_at") or
                        assessment.get("created_at") or
                        datetime.now(timezone.utc).isoformat()
                    )

            return {
                "success": True,
                "assessments": assessments,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error("Failed to query compliance assessments: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
    except Exception as e:
        logger.error("Failed to query compliance assessments (outer): %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/compliance/assessments")
async def create_compliance_assessment(
    request: CreateComplianceAssessmentRequest,
    db=Depends(get_database),
):
    try:
        if not request.frameworks:
            raise HTTPException(status_code=400, detail="At least one framework is required")

        compliance_service = get_compliance_service(db)

        scan_results = await db.scan_reports.find_one(
            {"project_id": request.project_id},
            sort=[("created_at", -1)],
        )

        if not scan_results:
            scan_results = {"findings": [], "status": "no_scans"}

        framework_results = []
        overall_score = 0
        total_passed = 0
        total_failed = 0
        total_controls = 0

        for framework_id in request.frameworks:
            try:
                framework_enum = ComplianceFramework(framework_id)
                result = await compliance_service.assess_compliance(
                    project_id=request.project_id,
                    framework=framework_enum,
                    scan_results=scan_results,
                )

                if result.get("success") and result.get("assessment"):
                    assessment_data = result["assessment"]
                    passed = assessment_data.get("controls_compliant", 0)
                    failed = assessment_data.get("controls_non_compliant", 0)
                    partial = assessment_data.get("controls_partial", 0)
                    assessed = assessment_data.get("controls_assessed", 0)
                    score = assessment_data.get("compliance_score", 0)

                    framework_results.append({
                        "framework": framework_id,
                        "score": round(score, 1),
                        "passed_controls": passed,
                        "failed_controls": failed,
                        "partial_controls": partial,
                        "total_controls": assessed,
                        "status": assessment_data.get("overall_status", "unknown"),
                        "recommendations": assessment_data.get("recommendations", [])[:5],
                    })

                    overall_score += score
                    total_passed += passed
                    total_failed += failed
                    total_controls += assessed
                else:
                    framework_results.append({
                        "framework": framework_id,
                        "score": 0,
                        "passed_controls": 0,
                        "failed_controls": 0,
                        "partial_controls": 0,
                        "total_controls": 0,
                        "status": "error",
                        "recommendations": [result.get("error", "Assessment failed")],
                    })

            except ValueError:
                framework_results.append({
                    "framework": framework_id,
                    "score": 0,
                    "passed_controls": 0,
                    "failed_controls": 0,
                    "total_controls": 0,
                    "status": "unsupported",
                    "recommendations": [f"Framework '{framework_id}' is not supported"],
                })

        num_frameworks = len([r for r in framework_results if r.get("status") != "error"])
        avg_score = (overall_score / num_frameworks) if num_frameworks > 0 else 0

        now = datetime.now(timezone.utc)
        assessment_doc = {
            "project_id": request.project_id,
            "frameworks": request.frameworks,
            "framework_results": framework_results,
            "overall_score": round(avg_score, 1),
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_controls": total_controls,
            "status": "completed",
            "assessment_date": now.isoformat(),
            "assessed_at": now,
            "created_at": now,
        }

        try:
            result = await db["compliance_assessments"].insert_one(assessment_doc)
            assessment_doc["id"] = str(result.inserted_id)
        except Exception as e:
            logger.warning("Failed to persist compliance assessment, using UUID fallback: %s", e)

        assessment_doc.pop("_id", None)
        if "assessed_at" in assessment_doc and hasattr(assessment_doc["assessed_at"], "isoformat"):
            assessment_doc["assessed_at"] = assessment_doc["assessed_at"].isoformat()
        if "created_at" in assessment_doc and hasattr(assessment_doc["created_at"], "isoformat"):
            assessment_doc["created_at"] = assessment_doc["created_at"].isoformat()

        return {
            "success": True,
            "assessment": assessment_doc,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/compliance/framework-summary")
async def get_compliance_framework_summary(
    db=Depends(get_database),
):
    try:
        frameworks = [f.value for f in ComplianceFramework]

        summary = []
        for framework in frameworks:
            try:
                assessments_collection = db["compliance_assessments"]
                latest = await assessments_collection.find_one(
                    {"framework": framework},
                    sort=[("assessed_at", -1)]
                )

                if latest:
                    summary.append({
                        "framework": framework,
                        "name": framework.upper(),
                        "status": latest.get("status", "unknown"),
                        "score": latest.get("score", 0),
                        "last_assessed": latest.get("assessed_at").isoformat() if latest.get("assessed_at") else None,
                        "controls_passed": latest.get("controls_passed", 0),
                        "controls_failed": latest.get("controls_failed", 0),
                        "controls_total": latest.get("controls_total", 0)
                    })
                else:
                    summary.append({
                        "framework": framework,
                        "name": framework.upper(),
                        "status": "not_assessed",
                        "score": 0,
                        "last_assessed": None,
                        "controls_passed": 0,
                        "controls_failed": 0,
                        "controls_total": 0
                    })
            except Exception as e:
                logger.warning("Failed to fetch summary for framework %s: %s", framework, e)
                summary.append({
                    "framework": framework,
                    "name": framework.upper(),
                    "status": "not_assessed",
                    "score": 0,
                    "last_assessed": None,
                    "controls_passed": 0,
                    "controls_failed": 0,
                    "controls_total": 0
                })

        return {
            "success": True,
            "frameworks": summary,
            "total_frameworks": len(frameworks)
        }
    except Exception as e:
        logger.error("Failed to generate compliance framework summary: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/compliance/project/{project_id}/assessments")
async def get_project_assessments(
    project_id: str,
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_database),
):
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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
