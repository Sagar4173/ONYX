"""
Baseline Scanning System for tracking security drift and regression detection
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# Helper function for timezone-aware UTC datetime
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field

from database import db_manager
from models.report import ScanReport, VulnerabilityFinding

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    NEW = "new"
    FIXED = "fixed"
    MODIFIED = "modified"
    REOPENED = "reopened"
    UNCHANGED = "unchanged"


class DriftSeverity(str, Enum):
    CRITICAL = "critical"  # Critical new vulnerabilities
    HIGH = "high"         # High severity regressions
    MEDIUM = "medium"     # Medium security drift
    LOW = "low"          # Minor changes
    INFO = "info"        # Information only


class BaselineFingerprint(BaseModel):
    """Fingerprint for a vulnerability finding"""
    finding_hash: str = Field(..., description="Unique hash for the finding")
    file_path: str = Field(..., description="File path")
    line_number: Optional[int] = Field(None, description="Line number")
    rule_id: str = Field(..., description="Rule ID")
    message: str = Field(..., description="Finding message")
    severity: str = Field(..., description="Severity level")
    
    @classmethod
    def from_finding(cls, finding: VulnerabilityFinding) -> 'BaselineFingerprint':
        """Create fingerprint from vulnerability finding"""
        # Create a stable hash based on key identifying attributes
        content = {
            'file_path': finding.file_path,
            'line_number': finding.line_number,
            'rule_id': finding.rule_id,
            'message': finding.description or finding.title,
            'pattern': getattr(finding, 'pattern', '')
        }
        
        # Create hash
        content_str = json.dumps(content, sort_keys=True)
        finding_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        return cls(
            finding_hash=finding_hash,
            file_path=finding.file_path,
            line_number=finding.line_number,
            rule_id=finding.rule_id,
            message=finding.description or finding.title,
            severity=finding.severity.value
        )


class ScanBaseline(BaseModel):
    """Baseline snapshot of a security scan"""
    baseline_id: str = Field(..., description="Unique baseline identifier")
    repository_url: str = Field(..., description="Repository URL")
    branch: str = Field(..., description="Git branch")
    commit_hash: str = Field(..., description="Git commit hash")
    scan_timestamp: datetime = Field(..., description="Scan timestamp")
    
    # Fingerprints
    fingerprints: List[BaselineFingerprint] = Field(default_factory=list, description="Finding fingerprints")
    total_findings: int = Field(..., description="Total number of findings")
    
    # Statistics
    severity_counts: Dict[str, int] = Field(default_factory=dict, description="Findings by severity")
    scanner_counts: Dict[str, int] = Field(default_factory=dict, description="Findings by scanner")
    cwe_counts: Dict[str, int] = Field(default_factory=dict, description="Findings by CWE")
    
    # Metadata
    scan_duration_seconds: float = Field(..., description="Scan duration")
    scanned_files: int = Field(..., description="Number of files scanned")
    created_by: str = Field(..., description="User who created baseline")
    tags: List[str] = Field(default_factory=list, description="Baseline tags")


class SecurityDrift(BaseModel):
    """Security drift analysis result"""
    baseline_id: str = Field(..., description="Reference baseline ID")
    current_scan_id: str = Field(..., description="Current scan ID")
    comparison_timestamp: datetime = Field(default_factory=_utc_now, description="Comparison timestamp")
    
    # Change summary
    new_findings: List[Dict[str, Any]] = Field(default_factory=list, description="New findings")
    fixed_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Fixed findings")
    modified_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Modified findings")
    reopened_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Reopened findings")
    
    # Statistics
    total_changes: int = Field(0, description="Total number of changes")
    drift_severity: DriftSeverity = Field(..., description="Overall drift severity")
    security_score_change: float = Field(0.0, description="Security score change")
    
    # Trend data
    severity_trend: Dict[str, int] = Field(default_factory=dict, description="Severity trend")
    file_impact: Dict[str, int] = Field(default_factory=dict, description="Files with changes")


class RegressionAlert(BaseModel):
    """Security regression alert"""
    alert_id: str = Field(..., description="Alert identifier")
    repository_url: str = Field(..., description="Repository URL")
    branch: str = Field(..., description="Git branch")
    detected_at: datetime = Field(default_factory=_utc_now, description="Detection timestamp")
    
    # Regression details
    regression_type: str = Field(..., description="Type of regression")
    affected_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Affected findings")
    severity: DriftSeverity = Field(..., description="Regression severity")
    
    # Context
    commit_range: str = Field(..., description="Commit range where regression occurred")
    potential_cause: str = Field(..., description="Potential cause analysis")
    remediation_suggestions: List[str] = Field(default_factory=list, description="Remediation suggestions")


class BaselineScanningService:
    """Service for baseline scanning and drift detection"""
    
    def __init__(self):
        self.baselines_collection: Optional[AsyncIOMotorCollection] = None
        self.drift_collection: Optional[AsyncIOMotorCollection] = None
        self.alerts_collection: Optional[AsyncIOMotorCollection] = None
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize MongoDB collections"""
        if db_manager.client:
            db = db_manager.client[db_manager.database_name]
            self.baselines_collection = db['scan_baselines']
            self.drift_collection = db['security_drift']
            self.alerts_collection = db['regression_alerts']
    
    async def create_baseline(
        self,
        scan_report: ScanReport,
        repository_url: str,
        branch: str,
        commit_hash: str,
        created_by: str,
        tags: Optional[List[str]] = None
    ) -> ScanBaseline:
        """Create a new baseline from a scan report"""
        
        # Generate baseline ID
        baseline_id = f"{repository_url.split('/')[-1]}_{branch}_{commit_hash[:8]}_{int(_utc_now().timestamp())}"
        
        # Create fingerprints for all findings
        fingerprints = []
        severity_counts = {}
        scanner_counts = {}
        cwe_counts = {}
        
        for finding in scan_report.findings:
            fingerprint = BaselineFingerprint.from_finding(finding)
            fingerprints.append(fingerprint)
            
            # Update statistics
            severity_counts[finding.severity.value] = severity_counts.get(finding.severity.value, 0) + 1
            scanner_counts[finding.scanner.value] = scanner_counts.get(finding.scanner.value, 0) + 1
            
            if finding.cwe_id:
                cwe_counts[finding.cwe_id] = cwe_counts.get(finding.cwe_id, 0) + 1
        
        # Create baseline
        baseline = ScanBaseline(
            baseline_id=baseline_id,
            repository_url=repository_url,
            branch=branch,
            commit_hash=commit_hash,
            scan_timestamp=scan_report.created_at or _utc_now(),
            fingerprints=fingerprints,
            total_findings=len(scan_report.findings),
            severity_counts=severity_counts,
            scanner_counts=scanner_counts,
            cwe_counts=cwe_counts,
            scan_duration_seconds=getattr(scan_report, 'duration_seconds', 0),
            scanned_files=getattr(scan_report, 'scanned_files', 0),
            created_by=created_by,
            tags=tags or []
        )
        
        # Save to database
        if self.baselines_collection:
            await self.baselines_collection.insert_one(baseline.dict())
        
        logger.info(f"Created baseline {baseline_id} with {len(fingerprints)} findings")
        return baseline
    
    async def compare_with_baseline(
        self,
        current_scan: ScanReport,
        baseline_id: Optional[str] = None,
        repository_url: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Optional[SecurityDrift]:
        """Compare current scan with baseline"""
        
        # Get baseline
        if baseline_id:
            baseline = await self.get_baseline(baseline_id)
        else:
            baseline = await self.get_latest_baseline(repository_url, branch)
        
        if not baseline:
            logger.warning("No baseline found for comparison")
            return None
        
        # Create fingerprints for current scan
        current_fingerprints = {}
        for finding in current_scan.findings:
            fingerprint = BaselineFingerprint.from_finding(finding)
            current_fingerprints[fingerprint.finding_hash] = {
                'fingerprint': fingerprint,
                'finding': finding
            }
        
        # Create baseline fingerprints map
        baseline_fingerprints = {}
        for fingerprint in baseline.fingerprints:
            baseline_fingerprints[fingerprint.finding_hash] = fingerprint
        
        # Compare fingerprints
        new_findings = []
        fixed_findings = []
        modified_findings = []
        reopened_findings = []
        
        # Find new findings
        for hash_id, current_data in current_fingerprints.items():
            if hash_id not in baseline_fingerprints:
                new_findings.append({
                    'finding_hash': hash_id,
                    'file_path': current_data['fingerprint'].file_path,
                    'rule_id': current_data['fingerprint'].rule_id,
                    'severity': current_data['fingerprint'].severity,
                    'message': current_data['fingerprint'].message,
                    'change_type': ChangeType.NEW
                })
        
        # Find fixed findings
        for hash_id, baseline_fingerprint in baseline_fingerprints.items():
            if hash_id not in current_fingerprints:
                fixed_findings.append({
                    'finding_hash': hash_id,
                    'file_path': baseline_fingerprint.file_path,
                    'rule_id': baseline_fingerprint.rule_id,
                    'severity': baseline_fingerprint.severity,
                    'message': baseline_fingerprint.message,
                    'change_type': ChangeType.FIXED
                })
        
        # Calculate drift severity
        drift_severity = self._calculate_drift_severity(new_findings, fixed_findings, modified_findings)
        
        # Calculate security score change
        baseline_score = self._calculate_security_score(baseline.severity_counts)
        current_severity_counts = {}
        for finding in current_scan.findings:
            current_severity_counts[finding.severity.value] = current_severity_counts.get(finding.severity.value, 0) + 1
        current_score = self._calculate_security_score(current_severity_counts)
        security_score_change = current_score - baseline_score
        
        # Calculate trends
        severity_trend = {}
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            baseline_count = baseline.severity_counts.get(severity, 0)
            current_count = current_severity_counts.get(severity, 0)
            severity_trend[severity] = current_count - baseline_count
        
        # Calculate file impact
        file_impact = {}
        for finding_data in new_findings + fixed_findings + modified_findings:
            file_path = finding_data['file_path']
            file_impact[file_path] = file_impact.get(file_path, 0) + 1
        
        # Create drift analysis
        drift = SecurityDrift(
            baseline_id=baseline.baseline_id,
            current_scan_id=current_scan.report_id,
            new_findings=new_findings,
            fixed_findings=fixed_findings,
            modified_findings=modified_findings,
            reopened_findings=reopened_findings,
            total_changes=len(new_findings) + len(fixed_findings) + len(modified_findings),
            drift_severity=drift_severity,
            security_score_change=security_score_change,
            severity_trend=severity_trend,
            file_impact=file_impact
        )
        
        # Save drift analysis
        if self.drift_collection:
            await self.drift_collection.insert_one(drift.dict())
        
        # Check for regressions
        await self._check_for_regressions(drift, baseline, current_scan)
        
        logger.info(f"Drift analysis completed: {drift.total_changes} changes, severity: {drift_severity}")
        return drift
    
    def _calculate_drift_severity(
        self,
        new_findings: List[Dict[str, Any]],
        fixed_findings: List[Dict[str, Any]],
        modified_findings: List[Dict[str, Any]]
    ) -> DriftSeverity:
        """Calculate overall drift severity"""
        
        # Count critical and high severity new findings
        critical_new = len([f for f in new_findings if f['severity'] == 'critical'])
        high_new = len([f for f in new_findings if f['severity'] == 'high'])
        
        # Count fixed critical and high
        critical_fixed = len([f for f in fixed_findings if f['severity'] == 'critical'])
        high_fixed = len([f for f in fixed_findings if f['severity'] == 'high'])
        
        # Determine severity
        if critical_new > 0:
            return DriftSeverity.CRITICAL
        elif high_new > critical_fixed + high_fixed:
            return DriftSeverity.HIGH
        elif len(new_findings) > len(fixed_findings):
            return DriftSeverity.MEDIUM
        elif len(new_findings) + len(modified_findings) > 0:
            return DriftSeverity.LOW
        else:
            return DriftSeverity.INFO
    
    def _calculate_security_score(self, severity_counts: Dict[str, int]) -> float:
        """Calculate security score based on severity distribution"""
        weights = {
            'critical': -10,
            'high': -5,
            'medium': -2,
            'low': -1,
            'info': 0
        }
        
        score = 100  # Start with perfect score
        for severity, count in severity_counts.items():
            weight = weights.get(severity, 0)
            score += weight * count
        
        return max(0, min(100, score))  # Clamp between 0 and 100
    
    async def _check_for_regressions(
        self,
        drift: SecurityDrift,
        baseline: ScanBaseline,
        current_scan: ScanReport
    ):
        """Check for security regressions and create alerts"""
        
        # Check for critical regressions
        critical_new = [f for f in drift.new_findings if f['severity'] == 'critical']
        high_new = [f for f in drift.new_findings if f['severity'] == 'high']
        
        if critical_new or len(high_new) > 2:
            alert = RegressionAlert(
                alert_id=f"regression_{current_scan.report_id}_{int(_utc_now().timestamp())}",
                repository_url=baseline.repository_url,
                branch=baseline.branch,
                regression_type="critical_vulnerabilities" if critical_new else "high_vulnerability_increase",
                affected_findings=critical_new + high_new[:5],  # Limit to top 5
                severity=DriftSeverity.CRITICAL if critical_new else DriftSeverity.HIGH,
                commit_range=f"{baseline.commit_hash}..{getattr(current_scan, 'commit_hash', 'HEAD')}",
                potential_cause="New vulnerabilities introduced in recent commits",
                remediation_suggestions=[
                    "Review recent code changes for security issues",
                    "Run security scanners before merging code",
                    "Implement pre-commit hooks for security scanning"
                ]
            )
            
            if self.alerts_collection:
                await self.alerts_collection.insert_one(alert.dict())
            
            logger.warning(f"Regression alert created: {alert.alert_id}")
    
    async def get_baseline(self, baseline_id: str) -> Optional[ScanBaseline]:
        """Get baseline by ID"""
        if not self.baselines_collection:
            return None
        
        baseline_doc = await self.baselines_collection.find_one({'baseline_id': baseline_id})
        if baseline_doc:
            return ScanBaseline(**baseline_doc)
        return None
    
    async def get_latest_baseline(self, repository_url: str, branch: str) -> Optional[ScanBaseline]:
        """Get latest baseline for repository and branch"""
        if not self.baselines_collection:
            return None
        
        baseline_doc = await self.baselines_collection.find_one(
            {'repository_url': repository_url, 'branch': branch},
            sort=[('scan_timestamp', -1)]
        )
        
        if baseline_doc:
            return ScanBaseline(**baseline_doc)
        return None
    
    async def get_baselines_for_repository(
        self,
        repository_url: str,
        branch: Optional[str] = None,
        limit: int = 10
    ) -> List[ScanBaseline]:
        """Get baselines for repository"""
        if not self.baselines_collection:
            return []
        
        query = {'repository_url': repository_url}
        if branch:
            query['branch'] = branch
        
        cursor = self.baselines_collection.find(query).sort('scan_timestamp', -1).limit(limit)
        baselines = []
        
        async for baseline_doc in cursor:
            baselines.append(ScanBaseline(**baseline_doc))
        
        return baselines
    
    async def get_drift_analysis(
        self,
        repository_url: str,
        branch: Optional[str] = None,
        days: int = 30
    ) -> List[SecurityDrift]:
        """Get drift analysis for repository"""
        if not self.drift_collection:
            return []
        
        # Find baselines for repository
        baselines = await self.get_baselines_for_repository(repository_url, branch, limit=100)
        baseline_ids = [b.baseline_id for b in baselines]
        
        # Get drift analyses
        since_date = _utc_now() - timedelta(days=days)
        cursor = self.drift_collection.find({
            'baseline_id': {'$in': baseline_ids},
            'comparison_timestamp': {'$gte': since_date}
        }).sort('comparison_timestamp', -1)
        
        drift_analyses = []
        async for drift_doc in cursor:
            drift_analyses.append(SecurityDrift(**drift_doc))
        
        return drift_analyses
    
    async def get_regression_alerts(
        self,
        repository_url: str,
        branch: Optional[str] = None,
        days: int = 7
    ) -> List[RegressionAlert]:
        """Get regression alerts for repository"""
        if not self.alerts_collection:
            return []
        
        query = {'repository_url': repository_url}
        if branch:
            query['branch'] = branch
        
        since_date = _utc_now() - timedelta(days=days)
        query['detected_at'] = {'$gte': since_date}
        
        cursor = self.alerts_collection.find(query).sort('detected_at', -1)
        alerts = []
        
        async for alert_doc in cursor:
            alerts.append(RegressionAlert(**alert_doc))
        
        return alerts
    
    async def generate_trend_analysis(
        self,
        repository_url: str,
        branch: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """Generate trend analysis for repository"""
        
        # Get baselines for trend analysis
        baselines = await self.get_baselines_for_repository(repository_url, branch, limit=100)
        
        # Filter by date range
        since_date = _utc_now() - timedelta(days=days)
        recent_baselines = [b for b in baselines if b.scan_timestamp >= since_date]
        
        if len(recent_baselines) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        # Sort by timestamp
        recent_baselines.sort(key=lambda x: x.scan_timestamp)
        
        # Calculate trends
        trend_data = {
            'repository_url': repository_url,
            'branch': branch,
            'period_days': days,
            'data_points': len(recent_baselines),
            'timeline': [],
            'severity_trends': {},
            'security_score_trend': [],
            'total_findings_trend': []
        }
        
        for baseline in recent_baselines:
            timestamp = baseline.scan_timestamp.isoformat()
            security_score = self._calculate_security_score(baseline.severity_counts)
            
            trend_data['timeline'].append(timestamp)
            trend_data['security_score_trend'].append(security_score)
            trend_data['total_findings_trend'].append(baseline.total_findings)
            
            # Track severity trends
            for severity, count in baseline.severity_counts.items():
                if severity not in trend_data['severity_trends']:
                    trend_data['severity_trends'][severity] = []
                trend_data['severity_trends'][severity].append(count)
        
        # Calculate trend direction
        if len(trend_data['security_score_trend']) >= 2:
            first_score = trend_data['security_score_trend'][0]
            last_score = trend_data['security_score_trend'][-1]
            trend_data['security_improvement'] = last_score - first_score
            
            if trend_data['security_improvement'] > 5:
                trend_data['trend_direction'] = 'improving'
            elif trend_data['security_improvement'] < -5:
                trend_data['trend_direction'] = 'declining'
            else:
                trend_data['trend_direction'] = 'stable'
        
        return trend_data


# Global baseline scanning service instance
baseline_service = BaselineScanningService()

