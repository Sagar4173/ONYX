"""
API routes for Custom Rule Engine, Baseline Scanning, and Policy as Code
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import logging
import tempfile
import os

# Import timezone-aware UTC datetime helper
from utils.datetime_utils import utc_now

# Environment check for safe error messages
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

def safe_error_detail(error: Exception, operation: str) -> str:
    """Return safe error message - hide details in production"""
    if IS_PRODUCTION:
        return f"{operation} failed. Please try again later."
    return f"{operation} failed: {str(error)}"

from services.rules.rule_engine import (
    rule_engine, CustomRule, RuleTemplate, RuleValidationResult, 
    AllowedRuleType, SeverityLevel, RuleStatus
)
from services.scanning.baseline_scanner import (
    baseline_service, ScanBaseline, SecurityDrift, RegressionAlert,
    DriftSeverity
)
from services.rules.policy_engine import (
    policy_service, SecurityPolicy, PolicyViolation, PolicyEvaluationResult,
    PolicyScope, PolicyAction
)
from models.report import ScanReport
from models.user import User
from services.auth.auth_service import AuthService
from database import scan_reports_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["security"])
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)


# ========== Custom Rule Engine Endpoints ==========

class RuleCreateRequest(BaseModel):
    rule_data: Dict[str, Any]
    validate_rule: bool = True  # Renamed from 'validate' to avoid shadowing BaseModel.validate
    test_repo_path: Optional[str] = None

class RuleFromTemplateRequest(BaseModel):
    template_id: str
    rule_id: str
    variables: Dict[str, Any]


@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_rules(status: Optional[RuleStatus] = None):
    """Get all custom rules"""
    try:
        rules = await rule_engine.get_all_rules(status)
        return [rule.dict() for rule in rules]
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Rule retrieval"))


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    """Get a specific rule by ID"""
    try:
        rule = await rule_engine.load_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Rule retrieval"))


@router.post("/rules")
async def create_rule(request: RuleCreateRequest):
    """Create a new custom rule"""
    try:
        # Create rule from data
        rule = CustomRule(**request.rule_data)
        
        # Validate if requested
        if request.validate_rule:
            validation_result = await rule_engine.validate_rule(rule, request.test_repo_path)
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
        
        # Save rule
        success = await rule_engine.save_rule(rule)
        if success:
            return {"success": True, "rule_id": rule.id, "message": "Rule created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save rule")
            
    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/validate")
async def validate_rule(rule_data: Dict[str, Any], test_repo_path: Optional[str] = None):
    """Validate a custom rule"""
    try:
        rule = CustomRule(**rule_data)
        validation_result = await rule_engine.validate_rule(rule, test_repo_path)
        return validation_result.dict()
    except Exception as e:
        logger.error(f"Error validating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule-templates", response_model=List[Dict[str, Any]])
async def get_rule_templates():
    """Get all rule templates"""
    try:
        templates = await rule_engine.get_all_templates()
        return [template.dict() for template in templates]
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/from-template")
async def create_rule_from_template(request: RuleFromTemplateRequest):
    """Create a rule from a template"""
    try:
        rule = await rule_engine.create_rule_from_template(
            request.template_id, 
            request.variables, 
            request.rule_id
        )
        
        if not rule:
            raise HTTPException(status_code=404, detail="Template not found")
        
        success = await rule_engine.save_rule(rule)
        if success:
            return {"success": True, "rule": rule.dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to save rule")
            
    except Exception as e:
        logger.error(f"Error creating rule from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/upload")
async def upload_rules(file: UploadFile = File(...)):
    """Upload rules from YAML/JSON file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Load and validate rules
            import yaml
            import json
            
            with open(tmp_file_path, 'r') as f:
                if file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
                    rules_data = yaml.safe_load(f)
                else:
                    rules_data = json.load(f)
            
            # Handle single rule or list of rules
            if isinstance(rules_data, dict):
                rules_data = [rules_data]
            
            created_rules = []
            errors = []
            
            for rule_data in rules_data:
                try:
                    rule = CustomRule(**rule_data)
                    success = await rule_engine.save_rule(rule)
                    if success:
                        created_rules.append(rule.id)
                    else:
                        errors.append(f"Failed to save rule {rule.id}")
                except Exception as e:
                    errors.append(f"Invalid rule data: {e}")
            
            return {
                "success": len(errors) == 0,
                "created_rules": created_rules,
                "errors": errors
            }
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Error uploading rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Baseline Scanning Endpoints ==========

class BaselineCreateRequest(BaseModel):
    scan_report_id: str
    repository_url: str
    branch: str
    commit_hash: str
    tags: Optional[List[str]] = None


@router.post("/baselines")
async def create_baseline(request: BaselineCreateRequest, created_by: str = "api"):
    """Create a new baseline from a scan report"""
    try:
        # Get scan report
        scan_report_doc = await scan_reports_collection.find_one({"report_id": request.scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")
        
        scan_report = ScanReport(**scan_report_doc)
        
        # Create baseline
        baseline = await baseline_service.create_baseline(
            scan_report=scan_report,
            repository_url=request.repository_url,
            branch=request.branch,
            commit_hash=request.commit_hash,
            created_by=created_by,
            tags=request.tags
        )
        
        return {"success": True, "baseline": baseline.dict()}
        
    except Exception as e:
        logger.error(f"Error creating baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/baselines")
async def get_baselines(
    repository_url: str,
    branch: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """Get baselines for a repository"""
    try:
        baselines = await baseline_service.get_baselines_for_repository(
            repository_url, branch, limit
        )
        return [baseline.dict() for baseline in baselines]
        
    except Exception as e:
        logger.error(f"Error getting baselines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drift-analysis")
async def analyze_drift(
    scan_report_id: str,
    baseline_id: Optional[str] = None,
    repository_url: Optional[str] = None,
    branch: Optional[str] = None
):
    """Analyze security drift between current scan and baseline"""
    try:
        # Get scan report
        scan_report_doc = await scan_reports_collection.find_one({"report_id": scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")
        
        scan_report = ScanReport(**scan_report_doc)
        
        # Compare with baseline
        drift = await baseline_service.compare_with_baseline(
            current_scan=scan_report,
            baseline_id=baseline_id,
            repository_url=repository_url,
            branch=branch
        )
        
        if not drift:
            raise HTTPException(status_code=404, detail="No baseline found for comparison")
        
        return drift.dict()
        
    except Exception as e:
        logger.error(f"Error analyzing drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift-history")
async def get_drift_history(
    repository_url: str,
    branch: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    """Get drift analysis history for a repository"""
    try:
        drift_analyses = await baseline_service.get_drift_analysis(
            repository_url, branch, days
        )
        return [drift.dict() for drift in drift_analyses]
        
    except Exception as e:
        logger.error(f"Error getting drift history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regression-alerts")
async def get_regression_alerts(
    repository_url: str,
    branch: Optional[str] = None,
    days: int = Query(7, ge=1, le=30)
):
    """Get regression alerts for a repository"""
    try:
        alerts = await baseline_service.get_regression_alerts(
            repository_url, branch, days
        )
        return [alert.dict() for alert in alerts]
        
    except Exception as e:
        logger.error(f"Error getting regression alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_security_trends(
    repository_url: str,
    branch: str,
    days: int = Query(90, ge=7, le=365)
):
    """Get security trends for a repository"""
    try:
        trends = await baseline_service.generate_trend_analysis(
            repository_url, branch, days
        )
        return trends
        
    except Exception as e:
        logger.error(f"Error getting security trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Policy as Code Endpoints ==========

@router.get("/policies")
async def get_policies(
    repository_url: Optional[str] = None,
    branch: str = "main",
    environment: str = "development"
):
    """Get policies applicable to repository/branch/environment"""
    try:
        if repository_url:
            policies = await policy_service.get_applicable_policies(
                repository_url, branch, environment
            )
        else:
            policies = list(policy_service.policies_cache.values())
            if not policies:
                await policy_service.load_policies()
                policies = list(policy_service.policies_cache.values())
        
        return [policy.dict() for policy in policies]
        
    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/evaluate")
async def evaluate_policies(
    scan_report_id: str,
    repository_url: str,
    branch: str = "main",
    commit_hash: str = "HEAD",
    environment: str = "development"
):
    """Evaluate policies against scan results"""
    try:
        # Get scan report
        scan_report_doc = await scan_reports_collection.find_one({"report_id": scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")
        
        scan_report = ScanReport(**scan_report_doc)
        
        # Evaluate all applicable policies
        results = await policy_service.evaluate_all_policies(
            scan_report=scan_report,
            repository_url=repository_url,
            branch=branch,
            commit_hash=commit_hash,
            environment=environment
        )
        
        return [result.dict() for result in results]
        
    except Exception as e:
        logger.error(f"Error evaluating policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-violations")
async def get_policy_violations(
    repository_url: str,
    branch: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    status: str = Query("open", regex="^(open|resolved|all)$")
):
    """Get policy violations for a repository"""
    try:
        if not policy_service.violations_collection:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Build query
        query = {"repository_url": repository_url}
        if branch:
            query["branch"] = branch
        
        if status != "all":
            query["status"] = status
        
        # Date filter
        since_date = utc_now() - timedelta(days=days)
        query["detected_at"] = {"$gte": since_date}
        
        # Get violations
        cursor = policy_service.violations_collection.find(query).sort("detected_at", -1)
        violations = []
        
        async for violation_doc in cursor:
            violations.append(violation_doc)
        
        return violations
        
    except Exception as e:
        logger.error(f"Error getting policy violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-compliance-report")
async def get_policy_compliance_report(
    repository_url: str,
    branch: str = "main",
    days: int = Query(30, ge=1, le=365)
):
    """Get policy compliance report for a repository"""
    try:
        report = await policy_service.get_policy_compliance_report(
            repository_url, branch, days
        )
        return report
        
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/update-from-git")
async def update_policies_from_git(background_tasks: BackgroundTasks):
    """Update policies from Git repository"""
    try:
        background_tasks.add_task(policy_service.update_policy_from_git)
        return {"success": True, "message": "Policy update initiated"}
        
    except Exception as e:
        logger.error(f"Error updating policies from Git: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Combined Endpoints ==========

@router.post("/full-security-analysis")
async def full_security_analysis(
    scan_report_id: str,
    repository_url: str,
    branch: str = "main",
    commit_hash: str = "HEAD",
    environment: str = "development",
    create_baseline: bool = False
):
    """Perform comprehensive security analysis including drift and policy evaluation"""
    try:
        # Get scan report
        scan_report_doc = await scan_reports_collection.find_one({"report_id": scan_report_id})
        if not scan_report_doc:
            raise HTTPException(status_code=404, detail="Scan report not found")
        
        scan_report = ScanReport(**scan_report_doc)
        
        analysis_result = {
            "scan_report_id": scan_report_id,
            "repository_url": repository_url,
            "branch": branch,
            "commit_hash": commit_hash,
            "analysis_timestamp": utc_now().isoformat()
        }
        
        # 1. Drift Analysis
        try:
            drift = await baseline_service.compare_with_baseline(
                current_scan=scan_report,
                repository_url=repository_url,
                branch=branch
            )
            analysis_result["drift_analysis"] = drift.dict() if drift else None
        except Exception as e:
            logger.warning(f"Drift analysis failed: {e}")
            analysis_result["drift_analysis"] = {"error": str(e)}
        
        # 2. Policy Evaluation
        try:
            policy_results = await policy_service.evaluate_all_policies(
                scan_report=scan_report,
                repository_url=repository_url,
                branch=branch,
                commit_hash=commit_hash,
                environment=environment
            )
            analysis_result["policy_evaluation"] = [result.dict() for result in policy_results]
        except Exception as e:
            logger.warning(f"Policy evaluation failed: {e}")
            analysis_result["policy_evaluation"] = {"error": str(e)}
        
        # 3. Create baseline if requested
        if create_baseline:
            try:
                baseline = await baseline_service.create_baseline(
                    scan_report=scan_report,
                    repository_url=repository_url,
                    branch=branch,
                    commit_hash=commit_hash,
                    created_by="api",
                    tags=["automated"]
                )
                analysis_result["new_baseline"] = baseline.dict()
            except Exception as e:
                logger.warning(f"Baseline creation failed: {e}")
                analysis_result["new_baseline"] = {"error": str(e)}
        
        # 4. Generate recommendations
        recommendations = []
        
        # From drift analysis
        if "drift_analysis" in analysis_result and isinstance(analysis_result["drift_analysis"], dict):
            drift_data = analysis_result["drift_analysis"]
            if drift_data.get("drift_severity") in ["critical", "high"]:
                recommendations.append("Significant security drift detected - review recent changes")
            if drift_data.get("new_findings"):
                recommendations.append(f"{len(drift_data['new_findings'])} new vulnerabilities found")
        
        # From policy evaluation
        if "policy_evaluation" in analysis_result and isinstance(analysis_result["policy_evaluation"], list):
            for policy_result in analysis_result["policy_evaluation"]:
                if not policy_result.get("compliant", True):
                    recommendations.append(f"Policy violation: {policy_result.get('policy_id')}")
        
        analysis_result["recommendations"] = recommendations
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error in full security analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


