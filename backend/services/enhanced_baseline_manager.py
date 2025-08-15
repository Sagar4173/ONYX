"""
Enhanced Security Baseline Management System
Advanced baseline establishment, deviation detection, and compliance drift monitoring
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from .baseline_scanner import ScanBaseline, SecurityDrift, DriftSeverity
from .advanced_scanners import ScanResult, ScanFinding, ScannerType, ScanSeverity
from .custom_security_rules import ComplianceStandard, ComplianceRule

logger = logging.getLogger(__name__)


class BaselineType(str, Enum):
    """Types of security baselines"""
    GOLDEN_BRANCH = "golden_branch"
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class DriftType(str, Enum):
    """Types of security drift"""
    NEW_VULNERABILITY = "new_vulnerability"
    REGRESSION = "regression"
    COMPLIANCE_DEVIATION = "compliance_deviation"
    SEVERITY_INCREASE = "severity_increase"
    NEW_ATTACK_SURFACE = "new_attack_surface"
    CONFIGURATION_DRIFT = "configuration_drift"


class ComplianceDriftAlert(BaseModel):
    """Alert for compliance drift"""
    alert_id: str = Field(default_factory=lambda: f"drift_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    compliance_standard: ComplianceStandard
    control_id: str
    drift_type: DriftType
    severity: DriftSeverity
    description: str
    current_state: Dict[str, Any]
    baseline_state: Dict[str, Any]
    affected_files: List[str] = Field(default_factory=list)
    remediation_steps: List[str] = Field(default_factory=list)
    business_impact: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assignee: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical


class SecurityBaseline(BaseModel):
    """Enhanced security baseline with compliance mapping"""
    baseline_id: str
    baseline_type: BaselineType
    name: str
    description: str
    repository: str
    branch: str
    commit_hash: str
    scan_timestamp: datetime
    
    # Core security metrics
    vulnerability_fingerprints: Dict[str, str] = Field(default_factory=dict)
    security_score: float = 0.0
    risk_score: float = 0.0
    
    # Compliance metrics
    compliance_scores: Dict[str, float] = Field(default_factory=dict)  # standard -> score
    compliance_controls: Dict[str, List[str]] = Field(default_factory=dict)  # standard -> control_ids
    
    # Scanner results
    scanner_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # scanner -> results summary
    
    # Coverage metrics
    code_coverage: float = 0.0
    test_coverage: float = 0.0
    dependency_coverage: float = 0.0
    
    # Infrastructure metrics
    infrastructure_score: float = 0.0
    configuration_hash: str = ""
    
    # Metadata
    created_by: str = ""
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_overall_score(self) -> float:
        """Calculate overall security score"""
        scores = [self.security_score, self.risk_score]
        scores.extend(self.compliance_scores.values())
        return sum(scores) / len(scores) if scores else 0.0


class BaselineComparison(BaseModel):
    """Comparison between two security baselines"""
    comparison_id: str = Field(default_factory=lambda: f"comp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    baseline_id: str
    current_scan_id: str
    comparison_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Drift metrics
    new_vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    severity_changes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Compliance drift
    compliance_drift: Dict[str, List[ComplianceDriftAlert]] = Field(default_factory=dict)
    
    # Score changes
    security_score_delta: float = 0.0
    risk_score_delta: float = 0.0
    compliance_score_deltas: Dict[str, float] = Field(default_factory=dict)
    
    # Summary
    drift_severity: DriftSeverity = DriftSeverity.LOW
    total_drift_count: int = 0
    critical_drift_count: int = 0
    
    def calculate_drift_severity(self) -> DriftSeverity:
        """Calculate overall drift severity"""
        if self.critical_drift_count > 0:
            return DriftSeverity.CRITICAL
        elif self.total_drift_count > 10:
            return DriftSeverity.HIGH
        elif self.total_drift_count > 5:
            return DriftSeverity.MEDIUM
        elif self.total_drift_count > 0:
            return DriftSeverity.LOW
        else:
            return DriftSeverity.NONE


class EnhancedBaselineManager:
    """Enhanced security baseline management with compliance drift monitoring"""
    
    def __init__(self, baselines_directory: str = "baselines"):
        self.baselines_dir = Path(baselines_directory)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        
        self.golden_baselines: Dict[str, SecurityBaseline] = {}
        self.compliance_baselines: Dict[str, Dict[str, SecurityBaseline]] = {}  # standard -> baselines
        self.drift_history: List[BaselineComparison] = []
        
        # Load existing baselines
        self._load_baselines()
    
    async def establish_golden_baseline(
        self, 
        repository: str, 
        branch: str = "main",
        scan_results: Dict[str, ScanResult] = None,
        compliance_standards: List[ComplianceStandard] = None
    ) -> SecurityBaseline:
        """Establish a golden branch baseline with full security scan"""
        
        baseline_id = f"golden_{repository.replace('/', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Establishing golden baseline for {repository}:{branch}")
        
        # Calculate security metrics from scan results
        security_metrics = self._calculate_security_metrics(scan_results or {})
        
        # Calculate compliance scores
        compliance_scores = {}
        compliance_controls = {}
        
        if compliance_standards and scan_results:
            for standard in compliance_standards:
                score, controls = self._calculate_compliance_score(standard, scan_results)
                compliance_scores[standard.value] = score
                compliance_controls[standard.value] = controls
        
        # Create baseline
        baseline = SecurityBaseline(
            baseline_id=baseline_id,
            baseline_type=BaselineType.GOLDEN_BRANCH,
            name=f"Golden Baseline - {repository}",
            description=f"Security baseline for golden branch {branch}",
            repository=repository,
            branch=branch,
            commit_hash=await self._get_latest_commit_hash(repository, branch),
            scan_timestamp=datetime.utcnow(),
            vulnerability_fingerprints=self._generate_vulnerability_fingerprints(scan_results or {}),
            security_score=security_metrics['security_score'],
            risk_score=security_metrics['risk_score'],
            compliance_scores=compliance_scores,
            compliance_controls=compliance_controls,
            scanner_results=self._summarize_scanner_results(scan_results or {}),
            infrastructure_score=security_metrics.get('infrastructure_score', 0.0),
            configuration_hash=await self._calculate_config_hash(repository),
            created_by="system",
            tags=["golden", "baseline", branch]
        )
        
        # Save baseline
        self.golden_baselines[repository] = baseline
        self._save_baseline(baseline)
        
        logger.info(f"Golden baseline established: {baseline_id}")
        return baseline
    
    async def compare_with_baseline(
        self, 
        repository: str,
        current_scan_results: Dict[str, ScanResult],
        baseline_id: Optional[str] = None
    ) -> BaselineComparison:
        """Compare current scan results with baseline and detect drift"""
        
        # Get baseline to compare against
        if baseline_id:
            baseline = self._load_baseline_by_id(baseline_id)
        else:
            baseline = self.golden_baselines.get(repository)
        
        if not baseline:
            raise ValueError(f"No baseline found for repository {repository}")
        
        logger.info(f"Comparing current scan with baseline {baseline.baseline_id}")
        
        comparison = BaselineComparison(
            baseline_id=baseline.baseline_id,
            current_scan_id=f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Compare vulnerability fingerprints
        current_fingerprints = self._generate_vulnerability_fingerprints(current_scan_results)
        baseline_fingerprints = baseline.vulnerability_fingerprints
        
        # Detect new vulnerabilities
        new_vulns = set(current_fingerprints.keys()) - set(baseline_fingerprints.keys())
        comparison.new_vulnerabilities = [
            {"fingerprint": fp, "details": current_fingerprints[fp]} 
            for fp in new_vulns
        ]
        
        # Detect resolved vulnerabilities
        resolved_vulns = set(baseline_fingerprints.keys()) - set(current_fingerprints.keys())
        comparison.resolved_vulnerabilities = [
            {"fingerprint": fp, "details": baseline_fingerprints[fp]}
            for fp in resolved_vulns
        ]
        
        # Calculate score deltas
        current_metrics = self._calculate_security_metrics(current_scan_results)
        comparison.security_score_delta = current_metrics['security_score'] - baseline.security_score
        comparison.risk_score_delta = current_metrics['risk_score'] - baseline.risk_score
        
        # Detect compliance drift
        await self._detect_compliance_drift(comparison, baseline, current_scan_results)
        
        # Calculate overall drift severity
        comparison.total_drift_count = len(comparison.new_vulnerabilities)
        comparison.critical_drift_count = len([v for v in comparison.new_vulnerabilities 
                                              if v.get('severity') == 'critical'])
        comparison.drift_severity = comparison.calculate_drift_severity()
        
        # Save comparison
        self.drift_history.append(comparison)
        self._save_comparison(comparison)
        
        logger.info(f"Baseline comparison completed: {comparison.total_drift_count} drift items detected")
        return comparison
    
    async def monitor_compliance_drift(
        self, 
        repository: str,
        compliance_standards: List[ComplianceStandard],
        scan_results: Dict[str, ScanResult]
    ) -> Dict[str, List[ComplianceDriftAlert]]:
        """Monitor compliance drift for specific standards"""
        
        compliance_alerts = {}
        
        for standard in compliance_standards:
            alerts = []
            
            # Get compliance baseline for this standard
            if standard.value in self.compliance_baselines:
                baseline = self.compliance_baselines[standard.value].get(repository)
                if baseline:
                    alerts = await self._detect_standard_drift(
                        standard, baseline, scan_results, repository
                    )
            
            if alerts:
                compliance_alerts[standard.value] = alerts
                logger.warning(f"Compliance drift detected for {standard.value}: {len(alerts)} alerts")
        
        return compliance_alerts
    
    def get_baseline_trends(
        self, 
        repository: str, 
        days: int = 30
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Get baseline trends over time"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        trends = {
            'security_score': [],
            'risk_score': [],
            'vulnerability_count': [],
            'compliance_scores': {}
        }
        
        # Get comparisons for this repository in the time range
        repo_comparisons = [
            comp for comp in self.drift_history
            if comp.comparison_timestamp >= cutoff_date
            and self._get_repository_from_baseline(comp.baseline_id) == repository
        ]
        
        # Sort by timestamp
        repo_comparisons.sort(key=lambda x: x.comparison_timestamp)
        
        # Extract trends
        for comparison in repo_comparisons:
            timestamp = comparison.comparison_timestamp
            
            # Security metrics trends (would need to store these in comparison)
            # For now, return empty trends
            trends['security_score'].append((timestamp, 0.0))
            trends['risk_score'].append((timestamp, 0.0))
            trends['vulnerability_count'].append((timestamp, len(comparison.new_vulnerabilities)))
        
        return trends
    
    def _calculate_security_metrics(self, scan_results: Dict[str, ScanResult]) -> Dict[str, float]:
        """Calculate overall security metrics from scan results"""
        if not scan_results:
            return {'security_score': 0.0, 'risk_score': 0.0, 'infrastructure_score': 0.0}
        
        total_findings = 0
        critical_findings = 0
        high_findings = 0
        
        for scanner_type, result in scan_results.items():
            total_findings += len(result.findings)
            critical_findings += result.critical_count
            high_findings += result.high_count
        
        # Calculate security score (0-100, higher is better)
        if total_findings == 0:
            security_score = 100.0
        else:
            # Weighted scoring: critical = -10, high = -5, others = -1
            penalty = (critical_findings * 10) + (high_findings * 5) + ((total_findings - critical_findings - high_findings) * 1)
            security_score = max(0.0, 100.0 - penalty)
        
        # Calculate risk score (0-100, lower is better)
        risk_score = min(100.0, (critical_findings * 20) + (high_findings * 10))
        
        # Infrastructure score (placeholder)
        infrastructure_score = 75.0  # Would be calculated from IaC scan results
        
        return {
            'security_score': security_score,
            'risk_score': risk_score,
            'infrastructure_score': infrastructure_score
        }
    
    def _calculate_compliance_score(
        self, 
        standard: ComplianceStandard, 
        scan_results: Dict[str, ScanResult]
    ) -> Tuple[float, List[str]]:
        """Calculate compliance score for a specific standard"""
        
        # This would map scan findings to compliance controls
        # For now, return a placeholder implementation
        
        total_findings = sum(len(result.findings) for result in scan_results.values())
        controls_affected = []
        
        # Simple scoring based on findings count
        if total_findings == 0:
            score = 100.0
        else:
            score = max(0.0, 100.0 - (total_findings * 2))
        
        # Map findings to controls (placeholder)
        if total_findings > 0:
            controls_affected = [f"{standard.value}-3.4", f"{standard.value}-6.2"]
        
        return score, controls_affected
    
    def _generate_vulnerability_fingerprints(self, scan_results: Dict[str, ScanResult]) -> Dict[str, str]:
        """Generate fingerprints for vulnerabilities to track them across scans"""
        fingerprints = {}
        
        for scanner_type, result in scan_results.items():
            for finding in result.findings:
                # Create unique fingerprint based on finding characteristics
                fingerprint_data = f"{finding.title}:{finding.file_path}:{finding.line_number}:{finding.scanner}"
                fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]
                
                fingerprints[fingerprint] = {
                    'title': finding.title,
                    'severity': finding.severity.value,
                    'file_path': finding.file_path,
                    'scanner': finding.scanner.value
                }
        
        return fingerprints
    
    def _summarize_scanner_results(self, scan_results: Dict[str, ScanResult]) -> Dict[str, Dict[str, Any]]:
        """Summarize scanner results for baseline storage"""
        summary = {}
        
        for scanner_type, result in scan_results.items():
            summary[scanner_type] = {
                'total_findings': len(result.findings),
                'critical_count': result.critical_count,
                'high_count': result.high_count,
                'summary': result.summary,
                'duration': result.duration_seconds,
                'status': result.status
            }
        
        return summary
    
    async def _detect_compliance_drift(
        self, 
        comparison: BaselineComparison,
        baseline: SecurityBaseline,
        current_scan_results: Dict[str, ScanResult]
    ):
        """Detect compliance-specific drift"""
        
        for standard, baseline_score in baseline.compliance_scores.items():
            current_score, current_controls = self._calculate_compliance_score(
                ComplianceStandard(standard), current_scan_results
            )
            
            score_delta = current_score - baseline_score
            comparison.compliance_score_deltas[standard] = score_delta
            
            # Generate alerts for significant drift
            if abs(score_delta) > 10.0:  # More than 10 point change
                alert = ComplianceDriftAlert(
                    compliance_standard=ComplianceStandard(standard),
                    control_id="OVERALL",
                    drift_type=DriftType.COMPLIANCE_DEVIATION,
                    severity=DriftSeverity.HIGH if abs(score_delta) > 20.0 else DriftSeverity.MEDIUM,
                    description=f"Compliance score changed by {score_delta:.1f} points",
                    current_state={"score": current_score, "controls": current_controls},
                    baseline_state={"score": baseline_score, "controls": baseline.compliance_controls.get(standard, [])}
                )
                
                if standard not in comparison.compliance_drift:
                    comparison.compliance_drift[standard] = []
                comparison.compliance_drift[standard].append(alert)
    
    async def _detect_standard_drift(
        self,
        standard: ComplianceStandard,
        baseline: SecurityBaseline,
        scan_results: Dict[str, ScanResult],
        repository: str
    ) -> List[ComplianceDriftAlert]:
        """Detect drift for a specific compliance standard"""
        
        alerts = []
        
        # This would implement detailed compliance control mapping
        # For now, return placeholder alerts
        
        current_score, current_controls = self._calculate_compliance_score(standard, scan_results)
        baseline_score = baseline.compliance_scores.get(standard.value, 0.0)
        
        if current_score < baseline_score - 5.0:  # 5 point decrease
            alert = ComplianceDriftAlert(
                compliance_standard=standard,
                control_id="GENERAL",
                drift_type=DriftType.COMPLIANCE_DEVIATION,
                severity=DriftSeverity.MEDIUM,
                description=f"Compliance score decreased from {baseline_score:.1f} to {current_score:.1f}",
                current_state={"score": current_score},
                baseline_state={"score": baseline_score}
            )
            alerts.append(alert)
        
        return alerts
    
    async def _get_latest_commit_hash(self, repository: str, branch: str) -> str:
        """Get latest commit hash for repository/branch"""
        # This would integrate with Git to get actual commit hash
        return f"commit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    async def _calculate_config_hash(self, repository: str) -> str:
        """Calculate hash of infrastructure configuration"""
        # This would hash infrastructure config files
        return f"config_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    def _load_baselines(self):
        """Load existing baselines from storage"""
        # Implementation would load from database or files
        pass
    
    def _save_baseline(self, baseline: SecurityBaseline):
        """Save baseline to storage"""
        baseline_file = self.baselines_dir / f"{baseline.baseline_id}.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline.dict(), f, default=str, indent=2)
    
    def _save_comparison(self, comparison: BaselineComparison):
        """Save comparison to storage"""
        comparison_file = self.baselines_dir / f"comparison_{comparison.comparison_id}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison.dict(), f, default=str, indent=2)
    
    def _load_baseline_by_id(self, baseline_id: str) -> Optional[SecurityBaseline]:
        """Load baseline by ID"""
        baseline_file = self.baselines_dir / f"{baseline_id}.json"
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                data = json.load(f)
                return SecurityBaseline(**data)
        return None
    
    def _get_repository_from_baseline(self, baseline_id: str) -> str:
        """Extract repository name from baseline ID"""
        # Parse repository from baseline ID
        parts = baseline_id.split('_')
        if len(parts) >= 2:
            return parts[1]
        return ""


# Export main classes
__all__ = [
    'BaselineType', 'DriftType', 'ComplianceDriftAlert', 
    'SecurityBaseline', 'BaselineComparison', 'EnhancedBaselineManager'
]
