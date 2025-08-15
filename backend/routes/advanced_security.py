"""
Advanced Security API Routes
Exposes OWASP ZAP, Nuclei, CodeQL, Checkov, custom rules, and enhanced baseline management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from pydantic import BaseModel
from datetime import datetime
import logging
import tempfile
import asyncio

from services.advanced_scanners import (
    OWASPZAPScanner, NucleiScanner, ScannerType, ScanSeverity, 
    AdvancedScannerConfig, ScanResult
)
from services.codeql_checkov_scanners import CodeQLScanner, CheckovScanner
from services.custom_security_rules import (
    CustomSecurityRulesEngine, ComplianceStandard, IndustryType,
    ComplianceRule, OrganizationalRule, CustomRuleCategory
)
from services.enhanced_baseline_manager import (
    EnhancedBaselineManager, BaselineType, SecurityBaseline,
    BaselineComparison, ComplianceDriftAlert
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced-security", tags=["advanced-security"])

# Initialize components
zap_scanner = OWASPZAPScanner()
nuclei_scanner = NucleiScanner()
codeql_scanner = CodeQLScanner()
checkov_scanner = CheckovScanner()
custom_rules_engine = CustomSecurityRulesEngine()
baseline_manager = EnhancedBaselineManager()


# ========== Request/Response Models ==========

class ScanRequest(BaseModel):
    targets: List[str]
    scanner_config: Dict[str, Any] = {}
    timeout_seconds: int = 300
    severity_threshold: ScanSeverity = ScanSeverity.MEDIUM


class ZAPScanRequest(BaseModel):
    target_url: str
    scan_type: str = "quick"  # quick, full, api
    timeout_seconds: int = 600
    custom_config: Dict[str, Any] = {}


class NucleiScanRequest(BaseModel):
    targets: List[str]
    templates: Optional[str] = None  # Path to custom templates
    severity_filter: List[ScanSeverity] = [ScanSeverity.MEDIUM, ScanSeverity.HIGH, ScanSeverity.CRITICAL]
    rate_limit: int = 150
    timeout_seconds: int = 300


class CodeQLScanRequest(BaseModel):
    repository_path: str
    language: str  # python, java, javascript, etc.
    query_suite: str = "security-and-quality"
    build_command: Optional[str] = None
    timeout_seconds: int = 1800  # 30 minutes


class CheckovScanRequest(BaseModel):
    target_path: str
    frameworks: List[str] = ["terraform", "cloudformation", "kubernetes"]
    severity_threshold: ScanSeverity = ScanSeverity.MEDIUM
    custom_checks_dir: Optional[str] = None
    fail_on_critical: bool = True


class ComplianceRuleRequest(BaseModel):
    compliance_standard: ComplianceStandard
    industry_type: Optional[IndustryType] = None


class OrganizationalRuleRequest(BaseModel):
    organization: str
    rule_data: Dict[str, Any]


class BaselineRequest(BaseModel):
    repository: str
    branch: str = "main"
    baseline_type: BaselineType = BaselineType.GOLDEN_BRANCH
    compliance_standards: List[ComplianceStandard] = []


class BaselineComparisonRequest(BaseModel):
    repository: str
    baseline_id: Optional[str] = None
    include_compliance_drift: bool = True


# ========== OWASP ZAP Endpoints ==========

@router.post("/scan/zap", response_model=ScanResult)
async def run_zap_scan(request: ZAPScanRequest, background_tasks: BackgroundTasks):
    """Run OWASP ZAP DAST scan against target URL"""
    try:
        config = AdvancedScannerConfig(
            scanner_type=ScannerType.OWASP_ZAP,
            timeout_seconds=request.timeout_seconds,
            custom_config=request.custom_config
        )
        
        logger.info(f"Starting ZAP scan for {request.target_url}")
        result = await zap_scanner.scan_url(request.target_url, config)
        
        # Log results summary
        logger.info(f"ZAP scan completed: {len(result.findings)} findings, "
                   f"{result.critical_count} critical, {result.high_count} high")
        
        return result
        
    except Exception as e:
        logger.error(f"ZAP scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"ZAP scan failed: {str(e)}")


@router.get("/scan/zap/status/{scan_id}")
async def get_zap_scan_status(scan_id: str):
    """Get status of ZAP scan"""
    # Implementation would track scan status
    return {"scan_id": scan_id, "status": "completed", "message": "Scan finished"}


# ========== Nuclei Endpoints ==========

@router.post("/scan/nuclei", response_model=ScanResult)
async def run_nuclei_scan(request: NucleiScanRequest):
    """Run Nuclei vulnerability scan against target URLs"""
    try:
        config = AdvancedScannerConfig(
            scanner_type=ScannerType.NUCLEI,
            timeout_seconds=request.timeout_seconds,
            severity_threshold=min(request.severity_filter) if request.severity_filter else ScanSeverity.MEDIUM,
            custom_config={
                "templates": request.templates,
                "rate_limit": request.rate_limit
            }
        )
        
        logger.info(f"Starting Nuclei scan for {len(request.targets)} targets")
        result = await nuclei_scanner.scan_urls(request.targets, config)
        
        logger.info(f"Nuclei scan completed: {len(result.findings)} findings")
        return result
        
    except Exception as e:
        logger.error(f"Nuclei scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Nuclei scan failed: {str(e)}")


@router.get("/nuclei/templates")
async def list_nuclei_templates():
    """List available Nuclei templates"""
    # This would scan the nuclei templates directory
    return {
        "community_templates": ["cves", "vulnerabilities", "exposures"],
        "custom_templates": ["org-specific", "compliance"],
        "total_count": 3000  # Placeholder
    }


# ========== CodeQL Endpoints ==========

@router.post("/scan/codeql", response_model=ScanResult)
async def run_codeql_scan(request: CodeQLScanRequest):
    """Run CodeQL static analysis scan"""
    try:
        config = AdvancedScannerConfig(
            scanner_type=ScannerType.CODEQL,
            timeout_seconds=request.timeout_seconds,
            custom_config={
                "query_suite": request.query_suite,
                "build_command": request.build_command,
                "threads": 4,
                "ram": 4096
            }
        )
        
        logger.info(f"Starting CodeQL scan for {request.repository_path} ({request.language})")
        result = await codeql_scanner.scan_repository(request.repository_path, request.language, config)
        
        logger.info(f"CodeQL scan completed: {len(result.findings)} findings")
        return result
        
    except Exception as e:
        logger.error(f"CodeQL scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"CodeQL scan failed: {str(e)}")


@router.get("/codeql/languages")
async def list_codeql_languages():
    """List supported CodeQL languages"""
    return {
        "supported_languages": [
            "python", "java", "javascript", "typescript", "csharp", 
            "cpp", "go", "ruby", "swift", "kotlin"
        ]
    }


@router.get("/codeql/query-suites")
async def list_codeql_query_suites():
    """List available CodeQL query suites"""
    return {
        "query_suites": [
            "security-and-quality",
            "security-only", 
            "quality-only",
            "code-scanning",
            "custom"
        ]
    }


# ========== Checkov Endpoints ==========

@router.post("/scan/checkov", response_model=ScanResult)
async def run_checkov_scan(request: CheckovScanRequest):
    """Run Checkov Infrastructure as Code scan"""
    try:
        config = AdvancedScannerConfig(
            scanner_type=ScannerType.CHECKOV,
            timeout_seconds=300,
            severity_threshold=request.severity_threshold,
            fail_build_on_critical=request.fail_on_critical,
            custom_config={
                "frameworks": request.frameworks,
                "custom_checks": request.custom_checks_dir
            }
        )
        
        logger.info(f"Starting Checkov scan for {request.target_path}")
        result = await checkov_scanner.scan_iac(request.target_path, config)
        
        logger.info(f"Checkov scan completed: {len(result.findings)} findings")
        
        # Check if build should fail
        if request.fail_on_critical and result.critical_count > 0:
            raise HTTPException(
                status_code=422, 
                detail=f"Build failed: {result.critical_count} critical IaC misconfigurations found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkov scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Checkov scan failed: {str(e)}")


@router.get("/checkov/frameworks")
async def list_checkov_frameworks():
    """List supported Checkov frameworks"""
    return {
        "frameworks": [
            "terraform", "cloudformation", "kubernetes", "dockerfile",
            "helm", "kustomize", "arm", "bicep", "ansible"
        ]
    }


# ========== Multi-Scanner Orchestration ==========

@router.post("/scan/comprehensive")
async def run_comprehensive_scan(
    repository_path: str = Form(...),
    target_urls: List[str] = Form([]),
    languages: List[str] = Form([]),
    include_zap: bool = Form(False),
    include_nuclei: bool = Form(True),
    include_codeql: bool = Form(True),
    include_checkov: bool = Form(True)
):
    """Run comprehensive security scan with multiple tools"""
    
    scan_results = {}
    
    try:
        # Run scans in parallel where possible
        tasks = []
        
        if include_nuclei and target_urls:
            config = AdvancedScannerConfig(scanner_type=ScannerType.NUCLEI)
            tasks.append(("nuclei", nuclei_scanner.scan_urls(target_urls, config)))
        
        if include_codeql and languages:
            for language in languages:
                config = AdvancedScannerConfig(scanner_type=ScannerType.CODEQL)
                tasks.append((f"codeql_{language}", codeql_scanner.scan_repository(repository_path, language, config)))
        
        if include_checkov:
            config = AdvancedScannerConfig(scanner_type=ScannerType.CHECKOV)
            tasks.append(("checkov", checkov_scanner.scan_iac(repository_path, config)))
        
        if include_zap and target_urls:
            config = AdvancedScannerConfig(scanner_type=ScannerType.OWASP_ZAP)
            for i, url in enumerate(target_urls[:3]):  # Limit to 3 URLs for ZAP
                tasks.append((f"zap_{i}", zap_scanner.scan_url(url, config)))
        
        # Execute all scans
        if tasks:
            results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            for i, (scanner_name, result) in enumerate(zip([task[0] for task in tasks], results)):
                if isinstance(result, Exception):
                    logger.error(f"Scanner {scanner_name} failed: {result}")
                    scan_results[scanner_name] = {"error": str(result)}
                else:
                    scan_results[scanner_name] = result
        
        # Calculate overall summary
        total_findings = sum(len(r.findings) if hasattr(r, 'findings') else 0 for r in scan_results.values() if not isinstance(r, dict))
        critical_findings = sum(r.critical_count if hasattr(r, 'critical_count') else 0 for r in scan_results.values() if not isinstance(r, dict))
        
        return {
            "scan_id": f"comprehensive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "repository": repository_path,
            "scanners_used": list(scan_results.keys()),
            "total_findings": total_findings,
            "critical_findings": critical_findings,
            "results": scan_results,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive scan failed: {str(e)}")


# ========== Custom Rules Endpoints ==========

@router.get("/rules/compliance/{compliance_standard}", response_model=List[ComplianceRule])
async def get_compliance_rules(
    compliance_standard: ComplianceStandard,
    industry_type: Optional[IndustryType] = None
):
    """Get compliance rules for a specific standard"""
    try:
        rules = custom_rules_engine.get_compliance_rules(compliance_standard, industry_type)
        return rules
    except Exception as e:
        logger.error(f"Failed to get compliance rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/industry/{industry_type}", response_model=List[OrganizationalRule])
async def get_industry_rules(industry_type: IndustryType):
    """Get industry-specific security rules"""
    try:
        rules = custom_rules_engine.get_industry_rules(industry_type)
        return rules
    except Exception as e:
        logger.error(f"Failed to get industry rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/organizational")
async def create_organizational_rule(rule: OrganizationalRule):
    """Create a new organizational security rule"""
    try:
        success = await custom_rules_engine.create_organizational_rule(rule)
        if success:
            return {"message": f"Organizational rule {rule.rule_id} created successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create organizational rule")
    except Exception as e:
        logger.error(f"Failed to create organizational rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/organizational/{organization}")
async def get_organizational_rules(organization: str):
    """Get all organizational rules for a specific organization"""
    try:
        rules = custom_rules_engine.get_organizational_rules(organization)
        return rules
    except Exception as e:
        logger.error(f"Failed to get organizational rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Baseline Management Endpoints ==========

@router.post("/baseline/establish", response_model=SecurityBaseline)
async def establish_security_baseline(request: BaselineRequest):
    """Establish a new security baseline"""
    try:
        # This would typically include running a comprehensive scan first
        baseline = await baseline_manager.establish_golden_baseline(
            repository=request.repository,
            branch=request.branch,
            compliance_standards=request.compliance_standards
        )
        return baseline
    except Exception as e:
        logger.error(f"Failed to establish baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/baseline/compare", response_model=BaselineComparison)
async def compare_with_baseline(request: BaselineComparisonRequest):
    """Compare current state with security baseline"""
    try:
        # This would typically include running current scans first
        comparison = await baseline_manager.compare_with_baseline(
            repository=request.repository,
            current_scan_results={},  # Would include actual scan results
            baseline_id=request.baseline_id
        )
        return comparison
    except Exception as e:
        logger.error(f"Failed to compare with baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/baseline/trends/{repository}")
async def get_baseline_trends(repository: str, days: int = Query(30, ge=1, le=365)):
    """Get security baseline trends over time"""
    try:
        trends = baseline_manager.get_baseline_trends(repository, days)
        return trends
    except Exception as e:
        logger.error(f"Failed to get baseline trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/baseline/compliance-drift")
async def monitor_compliance_drift(
    repository: str = Form(...),
    compliance_standards: List[ComplianceStandard] = Form(...)
):
    """Monitor compliance drift for specific standards"""
    try:
        # This would include current scan results
        drift_alerts = await baseline_manager.monitor_compliance_drift(
            repository=repository,
            compliance_standards=compliance_standards,
            scan_results={}  # Would include actual scan results
        )
        return drift_alerts
    except Exception as e:
        logger.error(f"Failed to monitor compliance drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Utility Endpoints ==========

@router.get("/scanners/status")
async def get_scanners_status():
    """Get status of all advanced security scanners"""
    try:
        status = {}
        
        # Check ZAP
        try:
            zap_version = await zap_scanner._get_zap_version()
            status["zap"] = {"available": True, "version": zap_version}
        except:
            status["zap"] = {"available": False, "error": "ZAP not found"}
        
        # Check Nuclei
        try:
            nuclei_version = await nuclei_scanner._get_nuclei_version()
            status["nuclei"] = {"available": True, "version": nuclei_version}
        except:
            status["nuclei"] = {"available": False, "error": "Nuclei not found"}
        
        # Check CodeQL
        try:
            codeql_version = await codeql_scanner._get_codeql_version()
            status["codeql"] = {"available": True, "version": codeql_version}
        except:
            status["codeql"] = {"available": False, "error": "CodeQL not found"}
        
        # Check Checkov
        try:
            checkov_version = await checkov_scanner._get_checkov_version()
            status["checkov"] = {"available": True, "version": checkov_version}
        except:
            status["checkov"] = {"available": False, "error": "Checkov not found"}
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get scanner status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/standards")
async def list_compliance_standards():
    """List all supported compliance standards"""
    return {
        "standards": [standard.value for standard in ComplianceStandard],
        "industries": [industry.value for industry in IndustryType],
        "categories": [category.value for category in CustomRuleCategory]
    }
