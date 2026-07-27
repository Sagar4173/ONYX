"""
Scan Workflow
=============

Enhanced scanning workflows for different use cases.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from utils.datetime_utils import utc_now

from ..base.config import ScanConfig
from ..base.models import Finding, ScanResult, ScanType
from .orchestrator import ScanOrchestrator, ScanRequest

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Types of scan workflows."""
    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    CI_CD = "ci_cd"
    PR_REVIEW = "pr_review"
    COMPLIANCE = "compliance"
    PENTEST = "pentest"


@dataclass
class WorkflowConfig:
    """Configuration for a scan workflow."""
    name: str
    workflow_type: WorkflowType
    scan_types: List[ScanType]
    
    # Thresholds
    fail_on_critical: bool = True
    fail_on_high: bool = False
    max_critical: int = 0
    max_high: int = 5
    max_medium: int = 20
    
    # Timeouts
    timeout_seconds: int = 3600
    per_scanner_timeout: int = 600
    
    # Options
    enable_ai_analysis: bool = False
    generate_sbom: bool = False
    generate_report: bool = True
    
    # Callbacks
    on_finding: Optional[Callable[[Finding], None]] = None
    on_progress: Optional[Callable[[str, int], None]] = None


# Predefined workflow configurations
WORKFLOW_PRESETS: Dict[WorkflowType, WorkflowConfig] = {
    WorkflowType.QUICK: WorkflowConfig(
        name="Quick Scan",
        workflow_type=WorkflowType.QUICK,
        scan_types=[ScanType.SAST, ScanType.SECRETS],
        timeout_seconds=300,
        per_scanner_timeout=120
    ),
    WorkflowType.STANDARD: WorkflowConfig(
        name="Standard Scan",
        workflow_type=WorkflowType.STANDARD,
        scan_types=[ScanType.SAST, ScanType.SCA, ScanType.SECRETS],
        timeout_seconds=1800,
        per_scanner_timeout=600
    ),
    WorkflowType.COMPREHENSIVE: WorkflowConfig(
        name="Comprehensive Scan",
        workflow_type=WorkflowType.COMPREHENSIVE,
        scan_types=list(ScanType),
        timeout_seconds=7200,
        per_scanner_timeout=1200,
        enable_ai_analysis=True,
        generate_sbom=True
    ),
    WorkflowType.CI_CD: WorkflowConfig(
        name="CI/CD Pipeline Scan",
        workflow_type=WorkflowType.CI_CD,
        scan_types=[ScanType.SAST, ScanType.SCA, ScanType.SECRETS, ScanType.IAC],
        fail_on_critical=True,
        fail_on_high=True,
        max_critical=0,
        max_high=0,
        timeout_seconds=900,
        per_scanner_timeout=300
    ),
    WorkflowType.PR_REVIEW: WorkflowConfig(
        name="Pull Request Review",
        workflow_type=WorkflowType.PR_REVIEW,
        scan_types=[ScanType.SAST, ScanType.SECRETS],
        fail_on_critical=True,
        max_critical=0,
        timeout_seconds=600,
        per_scanner_timeout=180
    ),
    WorkflowType.COMPLIANCE: WorkflowConfig(
        name="Compliance Scan",
        workflow_type=WorkflowType.COMPLIANCE,
        scan_types=[ScanType.SAST, ScanType.SCA, ScanType.IAC, ScanType.SECRETS],
        enable_ai_analysis=True,
        generate_report=True,
        timeout_seconds=3600
    ),
    WorkflowType.PENTEST: WorkflowConfig(
        name="Penetration Testing Scan",
        workflow_type=WorkflowType.PENTEST,
        scan_types=[ScanType.DAST, ScanType.SAST],
        timeout_seconds=7200,
        per_scanner_timeout=1800
    )
}


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    scan_result: ScanResult
    workflow_type: WorkflowType
    passed: bool
    failure_reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ScanWorkflow:
    """
    Enhanced scanning workflow manager.
    
    Provides predefined workflows for common scanning scenarios
    with built-in thresholds and failure conditions.
    
    Usage:
        workflow = ScanWorkflow(config)
        result = await workflow.run(target, WorkflowType.CI_CD)
    """
    
    def __init__(self, config: ScanConfig = None):
        self.config = config or ScanConfig()
        self.orchestrator = ScanOrchestrator(self.config)
    
    async def run(
        self, 
        target: str, 
        workflow_type: WorkflowType,
        custom_config: Optional[WorkflowConfig] = None
    ) -> WorkflowResult:
        """
        Run a predefined scan workflow.
        
        Args:
            target: Target to scan
            workflow_type: Type of workflow to run
            custom_config: Optional custom configuration override
            
        Returns:
            WorkflowResult with scan results and pass/fail status
        """
        # Get workflow config
        workflow_config = custom_config or WORKFLOW_PRESETS.get(
            workflow_type, 
            WORKFLOW_PRESETS[WorkflowType.STANDARD]
        )
        
        logger.info(f"Starting {workflow_config.name} for {target}")
        
        # Create scan request
        request = ScanRequest(
            target=target,
            scan_types=workflow_config.scan_types,
            options={
                "timeout": workflow_config.per_scanner_timeout,
                "enable_ai": workflow_config.enable_ai_analysis,
                "generate_sbom": workflow_config.generate_sbom
            }
        )
        
        # Run scan with timeout
        try:
            scan_result = await asyncio.wait_for(
                self.orchestrator.run_scan(request),
                timeout=workflow_config.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Workflow {workflow_config.name} timed out")
            return WorkflowResult(
                scan_result=ScanResult(
                    scan_id=request.scan_id,
                    target=target,
                    status="timeout",
                    findings=[],
                    error="Workflow timed out"
                ),
                workflow_type=workflow_type,
                passed=False,
                failure_reasons=["Scan workflow timed out"]
            )
        
        # Evaluate results against thresholds
        passed, failure_reasons = self._evaluate_thresholds(
            scan_result, workflow_config
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            scan_result, workflow_config
        )
        
        # Build summary
        summary = self._build_summary(scan_result, workflow_config)
        
        return WorkflowResult(
            scan_result=scan_result,
            workflow_type=workflow_type,
            passed=passed,
            failure_reasons=failure_reasons,
            recommendations=recommendations,
            summary=summary
        )
    
    async def run_quick(self, target: str) -> WorkflowResult:
        """Run a quick scan workflow."""
        return await self.run(target, WorkflowType.QUICK)
    
    async def run_ci_cd(self, target: str) -> WorkflowResult:
        """Run a CI/CD pipeline scan workflow."""
        return await self.run(target, WorkflowType.CI_CD)
    
    async def run_pr_review(
        self, 
        target: str,
        changed_files: Optional[List[str]] = None
    ) -> WorkflowResult:
        """Run a pull request review scan workflow."""
        config = WorkflowConfig(
            **vars(WORKFLOW_PRESETS[WorkflowType.PR_REVIEW])
        )
        
        if changed_files:
            config.scan_types = [ScanType.SAST, ScanType.SECRETS]
        
        return await self.run(target, WorkflowType.PR_REVIEW, config)
    
    def _evaluate_thresholds(
        self, 
        result: ScanResult, 
        config: WorkflowConfig
    ) -> tuple[bool, List[str]]:
        """Evaluate scan results against thresholds."""
        failure_reasons = []
        
        if result.status == "failed":
            return False, ["Scan execution failed"]
        
        metrics = result.metrics
        
        # Check critical findings
        if config.fail_on_critical and metrics.critical > config.max_critical:
            failure_reasons.append(
                f"Found {metrics.critical} critical findings "
                f"(max allowed: {config.max_critical})"
            )
        
        # Check high findings
        if config.fail_on_high and metrics.high > config.max_high:
            failure_reasons.append(
                f"Found {metrics.high} high severity findings "
                f"(max allowed: {config.max_high})"
            )
        
        # Check medium findings
        if metrics.medium > config.max_medium:
            failure_reasons.append(
                f"Found {metrics.medium} medium severity findings "
                f"(max allowed: {config.max_medium})"
            )
        
        passed = len(failure_reasons) == 0
        
        return passed, failure_reasons
    
    def _generate_recommendations(
        self, 
        result: ScanResult, 
        config: WorkflowConfig
    ) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        
        # Analyze findings by category
        categories = {}
        for finding in result.findings:
            cat = finding.scan_type.value if hasattr(finding.scan_type, 'value') else str(finding.scan_type)
            categories[cat] = categories.get(cat, 0) + 1
        
        # Generate category-specific recommendations
        if categories.get("secrets", 0) > 0:
            recommendations.append(
                "Secret Detection: Remove exposed secrets from code and rotate credentials immediately. "
                "Consider using environment variables or a secrets management solution."
            )
        
        if categories.get("sca", 0) > 0:
            recommendations.append(
                "Dependency Vulnerabilities: Update vulnerable dependencies to secure versions. "
                "Consider using Dependabot or Renovate for automated updates."
            )
        
        if categories.get("sast", 0) > 5:
            recommendations.append(
                "Code Security: Multiple code security issues detected. "
                "Consider security training for developers and code review processes."
            )
        
        if categories.get("iac", 0) > 0:
            recommendations.append(
                "Infrastructure Security: Review and fix IaC misconfigurations. "
                "Implement IaC security scanning in CI/CD pipeline."
            )
        
        # Priority recommendation
        if result.metrics.critical > 0:
            recommendations.insert(0,
                f"🚨 URGENT: {result.metrics.critical} critical vulnerabilities require immediate attention."
            )
        
        return recommendations
    
    def _build_summary(
        self, 
        result: ScanResult, 
        config: WorkflowConfig
    ) -> Dict[str, Any]:
        """Build a summary of the scan results."""
        return {
            "workflow": config.name,
            "target": result.target,
            "status": result.status,
            "duration_seconds": result.metrics.duration_seconds,
            "findings": {
                "total": result.metrics.total_findings,
                "critical": result.metrics.critical,
                "high": result.metrics.high,
                "medium": result.metrics.medium,
                "low": result.metrics.low
            },
            "thresholds": {
                "max_critical": config.max_critical,
                "max_high": config.max_high,
                "max_medium": config.max_medium
            },
            "scanners_used": result.scanners_used,
            "timestamp": utc_now().isoformat()
        }
    
    @staticmethod
    def list_workflows() -> Dict[str, Dict[str, Any]]:
        """List all available workflows with their configurations."""
        return {
            wf.value: {
                "name": WORKFLOW_PRESETS[wf].name,
                "scan_types": [st.value for st in WORKFLOW_PRESETS[wf].scan_types],
                "timeout": WORKFLOW_PRESETS[wf].timeout_seconds,
                "fail_on_critical": WORKFLOW_PRESETS[wf].fail_on_critical,
                "fail_on_high": WORKFLOW_PRESETS[wf].fail_on_high
            }
            for wf in WorkflowType
        }
