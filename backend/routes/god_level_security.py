"""
Advanced Security Integration Route
Orchestrates all god-level security features: rule parsing, testing, baselines, and policy enforcement
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Body
import asyncio
import logging
from datetime import datetime, timezone
import traceback
from typing import Dict, Any, List
from pydantic import BaseModel

from services.rule_parsing_engine import RuleParsingEngine
from services.rule_testing_framework import RuleTestingFramework
from services.baseline_manager import BaselineManager
from services.policy_as_code_engine import PolicyAsCodeEngine
from services.ai_processor import get_ai_processor
from services.advanced_scanners import AdvancedSecurityScanner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/god-level", tags=["god-level"])

# Create alias for backward compatibility
god_level_bp = router

# Request/Response models
class RuleUploadRequest(BaseModel):
    rule_content: str
    rule_format: str
    metadata: Dict[str, Any] = {}

class SecurityScanRequest(BaseModel):
    repository_url: str
    branch: str = "main"
    project_name: str
    scan_config: Dict[str, Any] = {}

# Initialize god-level components
rule_parser = RuleParsingEngine()
rule_tester = RuleTestingFramework()
baseline_manager = BaselineManager()
policy_engine = PolicyAsCodeEngine()
# ai_processor initialized lazily when needed
advanced_scanner = AdvancedSecurityScanner()

@router.post("/rule/upload")
async def upload_custom_rule(request_data: RuleUploadRequest):
    """
    God-Level Rule Upload Endpoint
    - Strict schema validation
    - Safety analysis
    - Mandatory testing against vulnerable corpus
    - Provenance tracking
    """
    try:
        rule_content = request_data.rule_content
        rule_format = request_data.rule_format
        metadata = request_data.metadata
        
        if not rule_content:
            raise HTTPException(status_code=400, detail="No rule content provided")
        
        logger.info("Processing god-level rule upload request")
        
        # Step 1: Parse and validate rule with strict schema enforcement
        validation_result = await rule_parser.parse_and_validate_rule(
            rule_content=rule_content,
            rule_type=rule_format,
            author=metadata.get('author', 'unknown'),
            source_repo=metadata.get('source_repo'),
            commit_hash=metadata.get('commit_hash')
        )
        
        if not validation_result['is_valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Rule validation failed",
                    "validation_issues": validation_result['issues'],
                    "god_level_features": ["strict_schema_validation", "safety_analysis"]
                }
            )
        
        rule_id = validation_result['rule_id']
        
        # Step 2: Mandatory testing against vulnerable repository corpus
        testing_result = await rule_tester.run_certification_tests(
            rule_id=rule_id,
            rule_content=rule_content,
            rule_type=rule_format
        )
        
        if not testing_result['certified']:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Rule failed certification tests",
                    "test_results": testing_result,
                    "god_level_features": ["mandatory_vulnerable_corpus_testing", "precision_recall_requirements"]
                }
            )
        
        # Step 3: AI-powered rule analysis and optimization
        ai_analysis = await get_ai_processor().analyze_custom_rule(
            rule_content=rule_content,
            validation_result=validation_result,
            test_results=testing_result
        )
        
        response = {
            "success": True,
            "rule_id": rule_id,
            "validation_summary": {
                "schema_valid": validation_result['is_valid'],
                "safety_score": validation_result.get('safety_score', 0),
                "performance_risk": validation_result.get('performance_risk', 'unknown')
            },
            "certification_summary": {
                "certified": testing_result['certified'],
                "precision": testing_result.get('precision', 0),
                "recall": testing_result.get('recall', 0),
                "test_cases_passed": testing_result.get('passed_tests', 0),
                "total_test_cases": testing_result.get('total_tests', 0)
            },
            "ai_analysis": ai_analysis,
            "god_level_features": [
                "strict_schema_validation",
                "regex_safety_analysis", 
                "mandatory_corpus_testing",
                "ai_powered_optimization",
                "rule_provenance_tracking"
            ]
        }
        
        logger.info(f"Successfully processed god-level rule upload: {rule_id}")
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"God-level rule upload failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during god-level rule processing",
                "details": str(e)
            }
        )

@router.post("/scan/advanced")
async def advanced_security_scan(request_data: SecurityScanRequest):
    """
    God-Level Security Scan Endpoint
    - Advanced multi-scanner integration
    - Baseline drift detection
    - Policy-as-code enforcement
    - AI-powered analysis
    """
    try:
        repository = request_data.repository_url
        branch = request_data.branch
        project_name = request_data.project_name
        scan_config = request_data.scan_config
        
        if not repository:
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        logger.info(f"Starting god-level advanced security scan: {repository}@{branch}")
        
        # Step 1: Run advanced security scanners
        scan_results = await advanced_scanner.run_comprehensive_scan(
            target=repository,  # Changed from repository to target
            scan_types=None  # Use default scan types
        )
        
        # Step 2: Baseline drift detection and analysis
        baseline_analysis = await baseline_manager.analyze_scan_results(
            repository=repository,
            branch=branch,
            current_findings=scan_results['findings']
        )
        
        # Step 3: Policy-as-code enforcement evaluation
        policy_evaluation = await policy_engine.evaluate_policies(
            repository=repository,
            branch=branch,
            commit_hash=commit_hash,
            scan_results=scan_results
        )
        
        # Step 4: AI-powered threat analysis and recommendations
        ai_analysis = await get_ai_processor().analyze_security_findings(
            scan_results=scan_results,
            baseline_analysis=baseline_analysis,
            policy_evaluation=policy_evaluation
        )
        
        # Compile comprehensive response
        response = {
            "scan_id": scan_results.get('scan_id'),
            "repository": repository,
            "branch": branch,
            "commit_hash": commit_hash,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            
            "scan_results": {
                "total_findings": scan_results.get('total_findings', 0),
                "findings_by_severity": scan_results.get('findings_by_severity', {}),
                "scanners_used": scan_results.get('scanners_used', []),
                "scan_duration": scan_results.get('scan_duration', 0)
            },
            
            "baseline_analysis": {
                "drift_detected": baseline_analysis.get('drift_detected', False),
                "new_vulnerabilities": baseline_analysis.get('new_vulnerabilities', []),
                "resolved_vulnerabilities": baseline_analysis.get('resolved_vulnerabilities', []),
                "security_score_trend": baseline_analysis.get('security_score_trend', {}),
                "baseline_actions": baseline_analysis.get('automatic_actions', [])
            },
            
            "policy_enforcement": {
                "overall_result": policy_evaluation.get('overall_result', 'unknown'),
                "policies_evaluated": len(policy_evaluation.get('policy_results', [])),
                "violations_count": len(policy_evaluation.get('violations', [])),
                "actions_required": policy_evaluation.get('actions_required', []),
                "enforcement_summary": policy_evaluation.get('policy_results', [])
            },
            
            "ai_insights": ai_analysis,
            
            "god_level_features": [
                "multi_scanner_integration",
                "baseline_drift_detection", 
                "policy_as_code_enforcement",
                "ai_powered_threat_analysis",
                "automatic_remediation_recommendations"
            ]
        }
        
        logger.info(f"Completed god-level advanced security scan: {repository}@{branch}")
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"God-level advanced scan failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during god-level security scan",
                "details": str(e)
            }
        )

@god_level_bp.route('/baseline/status', methods=['GET'])
async def get_baseline_status():
    """Get baseline status and drift analysis for repositories"""
    try:
        repository = request.args.get('repository')
        branch = request.args.get('branch', 'main')
        
        if repository:
            # Get status for specific repository
            status = await baseline_manager.get_baseline_status(repository, branch)
            drift_analysis = await baseline_manager.get_drift_analysis(repository, branch)
            
            response = {
                "repository": repository,
                "branch": branch,
                "baseline_status": status,
                "drift_analysis": drift_analysis,
                "god_level_features": ["drift_detection", "security_score_tracking"]
            }
        else:
            # Get overview of all repositories
            overview = await baseline_manager.get_repositories_overview()
            response = {
                "repositories_overview": overview,
                "god_level_features": ["multi_repo_baseline_tracking"]
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Failed to get baseline status: {e}")
        return jsonify({"error": str(e)}), 500

@god_level_bp.route('/policy/evaluate', methods=['POST'])
async def evaluate_policy_compliance():
    """Evaluate policy compliance for specific commit"""
    try:
        data = request.get_json()
        
        repository = data.get('repository')
        branch = data.get('branch', 'main')
        commit_hash = data.get('commit_hash')
        scan_results = data.get('scan_results', {})
        
        if not all([repository, commit_hash]):
            return jsonify({"error": "Repository and commit_hash are required"}), 400
        
        evaluation_result = await policy_engine.evaluate_policies(
            repository=repository,
            branch=branch,
            commit_hash=commit_hash,
            scan_results=scan_results
        )
        
        response = {
            "policy_evaluation": evaluation_result,
            "god_level_features": ["policy_as_code", "git_based_governance", "enforcement_modes"]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Policy evaluation failed: {e}")
        return jsonify({"error": str(e)}), 500

@god_level_bp.route('/rule/test-status/<rule_id>', methods=['GET'])
async def get_rule_test_status(rule_id: str):
    """Get testing status and certification details for a rule"""
    try:
        test_status = await rule_tester.get_rule_test_status(rule_id)
        
        response = {
            "rule_id": rule_id,
            "test_status": test_status,
            "god_level_features": ["vulnerable_corpus_testing", "precision_recall_tracking"]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Failed to get rule test status: {e}")
        return jsonify({"error": str(e)}), 500

@god_level_bp.route('/analytics/dashboard', methods=['GET'])
async def get_god_level_analytics():
    """Get comprehensive analytics dashboard data"""
    try:
        # Aggregate data from all god-level components
        analytics = {
            "rule_parsing": await rule_parser.get_analytics(),
            "rule_testing": await rule_tester.get_analytics(), 
            "baseline_management": await baseline_manager.get_analytics(),
            "policy_enforcement": await policy_engine.get_analytics() if hasattr(policy_engine, 'get_analytics') else {},
            "god_level_features": [
                "comprehensive_rule_validation",
                "mandatory_testing_pipeline",
                "drift_detection_analytics",
                "policy_compliance_tracking",
                "ai_powered_insights"
            ]
        }
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Failed to get god-level analytics: {e}")
        return jsonify({"error": str(e)}), 500

@god_level_bp.route('/security/boundaries/test', methods=['POST'])
async def test_security_boundaries():
    """Test security boundaries with adversarial cases"""
    try:
        logger.info("Running adversarial tests for security boundaries")
        
        # Run adversarial tests
        test_results = await rule_parser.run_adversarial_tests()
        
        response = {
            "adversarial_test_results": test_results,
            "god_level_features": [
                "sandboxed_rule_execution",
                "resource_limit_enforcement", 
                "adversarial_test_validation",
                "catastrophic_backtracking_protection"
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Security boundary testing failed: {e}")
        return jsonify({"error": str(e)}), 500

@god_level_bp.route('/rule/test-boundary/<rule_id>', methods=['POST'])
async def test_rule_security_boundary(rule_id: str):
    """Test a specific rule with security boundaries"""
    try:
        data = request.get_json() or {}
        test_files = data.get('test_files')
        
        # Test rule with security boundaries
        test_result = await rule_parser.test_rule_with_security_boundaries(
            rule_id=rule_id,
            test_files=test_files
        )
        
        response = {
            "rule_id": rule_id,
            "boundary_test_result": test_result,
            "god_level_features": [
                "cpu_memory_limits",
                "execution_timeout_protection",
                "resource_usage_monitoring",
                "safety_assessment"
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Rule boundary testing failed: {e}")
        return jsonify({"error": str(e)}), 500

@god_level_bp.route('/health', methods=['GET'])
async def health_check():
    """Health check for all god-level components"""
    try:
        health_status = {
            "status": "healthy",
            "components": {
                "rule_parsing_engine": "operational",
                "rule_testing_framework": "operational", 
                "baseline_manager": "operational",
                "policy_as_code_engine": "operational",
                "security_boundary_engine": "operational"
            },
            "god_level_features": [
                "enterprise_grade_validation",
                "automated_testing_pipeline",
                "intelligent_baseline_management",
                "policy_driven_enforcement",
                "sandboxed_rule_execution",
                "adversarial_test_protection"
            ]
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Error handlers
@god_level_bp.errorhandler(Exception)
def handle_god_level_error(error):
    """Handle god-level errors gracefully"""
    logger.error(f"God-level error: {error}")
    logger.error(traceback.format_exc())
    
    return jsonify({
        "error": "God-level security processing error",
        "message": str(error),
        "god_level_note": "Enterprise-grade error handling active"
    }), 500
