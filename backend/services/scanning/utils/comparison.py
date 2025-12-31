"""
Scan Comparison Service
Compare security scans to track fixed vulnerabilities, new issues, and regressions
Provides delta analysis between scans for tracking remediation progress
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


from models.base import SeverityLevel


class ChangeType(Enum):
    """Type of change between scans"""
    FIXED = "fixed"
    NEW = "new"
    UNCHANGED = "unchanged"
    REINTRODUCED = "reintroduced"  # Was fixed, now back
    MODIFIED = "modified"  # Same issue, different severity


# Use SeverityLevel from models.base for consistency
FindingSeverity = SeverityLevel


@dataclass
class Finding:
    """Represents a single security finding"""
    id: str
    rule_id: str
    title: str
    description: str
    severity: FindingSeverity
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    scanner: str = ""
    category: str = ""
    cwe_ids: List[str] = field(default_factory=list)
    owasp_ids: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Generate unique fingerprint for this finding"""
        # Use rule, file, and approximate location for matching
        data = f"{self.rule_id}:{self.file_path}:{self.line_start}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class FindingChange:
    """Represents a change in a finding between scans"""
    change_type: ChangeType
    finding: Finding
    previous_finding: Optional[Finding] = None
    severity_change: Optional[Tuple[str, str]] = None  # (old, new)
    notes: Optional[str] = None


@dataclass
class ScanSummary:
    """Summary of a single scan"""
    scan_id: str
    timestamp: datetime
    project_id: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    total_findings: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    scanners_used: List[str] = field(default_factory=list)
    duration_seconds: Optional[float] = None


@dataclass
class ComparisonResult:
    """Result of comparing two scans"""
    base_scan: ScanSummary
    compare_scan: ScanSummary
    
    # Counts
    fixed_count: int = 0
    new_count: int = 0
    unchanged_count: int = 0
    reintroduced_count: int = 0
    modified_count: int = 0
    
    # Changes by severity
    fixed_by_severity: Dict[str, int] = field(default_factory=dict)
    new_by_severity: Dict[str, int] = field(default_factory=dict)
    
    # Detailed changes
    fixed: List[FindingChange] = field(default_factory=list)
    new: List[FindingChange] = field(default_factory=list)
    unchanged: List[FindingChange] = field(default_factory=list)
    reintroduced: List[FindingChange] = field(default_factory=list)
    modified: List[FindingChange] = field(default_factory=list)
    
    # Metrics
    improvement_score: float = 0.0  # Positive = improved, negative = degraded
    net_change: int = 0  # new - fixed
    
    # Insights
    summary: str = ""
    highlights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ScanComparisonService:
    """
    Service for comparing security scans and tracking remediation progress.
    Provides delta analysis to show what's fixed, new, and unchanged.
    """

    def __init__(self, db=None):
        self.db = db
        self._cache: Dict[str, Any] = {}

    async def compare_scans(
        self,
        base_scan_id: str,
        compare_scan_id: str,
        include_unchanged: bool = False
    ) -> ComparisonResult:
        """
        Compare two scans and return detailed delta.
        
        Args:
            base_scan_id: The older/baseline scan ID
            compare_scan_id: The newer/current scan ID
            include_unchanged: Whether to include unchanged findings
            
        Returns:
            ComparisonResult with all changes
        """
        # Load scans
        base_scan = await self._load_scan(base_scan_id)
        compare_scan = await self._load_scan(compare_scan_id)
        
        if not base_scan or not compare_scan:
            raise ValueError("One or both scans not found")

        # Load findings
        base_findings = await self._load_findings(base_scan_id)
        compare_findings = await self._load_findings(compare_scan_id)
        
        # Create fingerprint maps
        base_map = {f.fingerprint: f for f in base_findings}
        compare_map = {f.fingerprint: f for f in compare_findings}
        
        # Track historical fixed findings for reintroduction detection
        historical_fixed = await self._get_historical_fixed(
            base_scan.project_id,
            before_date=base_scan.timestamp
        )
        
        # Classify changes
        fixed: List[FindingChange] = []
        new: List[FindingChange] = []
        unchanged: List[FindingChange] = []
        reintroduced: List[FindingChange] = []
        modified: List[FindingChange] = []
        
        # Find fixed (in base but not in compare)
        for fp, finding in base_map.items():
            if fp not in compare_map:
                fixed.append(FindingChange(
                    change_type=ChangeType.FIXED,
                    finding=finding,
                    notes="Finding has been remediated"
                ))
            else:
                compare_finding = compare_map[fp]
                if finding.severity != compare_finding.severity:
                    modified.append(FindingChange(
                        change_type=ChangeType.MODIFIED,
                        finding=compare_finding,
                        previous_finding=finding,
                        severity_change=(finding.severity.value, compare_finding.severity.value)
                    ))
                elif include_unchanged:
                    unchanged.append(FindingChange(
                        change_type=ChangeType.UNCHANGED,
                        finding=compare_finding
                    ))

        # Find new (in compare but not in base)
        for fp, finding in compare_map.items():
            if fp not in base_map:
                # Check if it's a reintroduction
                if fp in historical_fixed:
                    reintroduced.append(FindingChange(
                        change_type=ChangeType.REINTRODUCED,
                        finding=finding,
                        notes="This vulnerability was previously fixed and has been reintroduced"
                    ))
                else:
                    new.append(FindingChange(
                        change_type=ChangeType.NEW,
                        finding=finding
                    ))

        # Calculate severity breakdowns
        fixed_by_severity = self._count_by_severity(fixed)
        new_by_severity = self._count_by_severity(new)

        # Calculate metrics
        improvement_score = self._calculate_improvement_score(fixed, new, reintroduced)
        net_change = len(new) + len(reintroduced) - len(fixed)

        # Generate insights
        summary = self._generate_summary(fixed, new, reintroduced, modified)
        highlights = self._generate_highlights(fixed, new, reintroduced, modified)
        recommendations = self._generate_recommendations(new, reintroduced)

        return ComparisonResult(
            base_scan=base_scan,
            compare_scan=compare_scan,
            fixed_count=len(fixed),
            new_count=len(new),
            unchanged_count=len(unchanged),
            reintroduced_count=len(reintroduced),
            modified_count=len(modified),
            fixed_by_severity=fixed_by_severity,
            new_by_severity=new_by_severity,
            fixed=fixed,
            new=new,
            unchanged=unchanged if include_unchanged else [],
            reintroduced=reintroduced,
            modified=modified,
            improvement_score=improvement_score,
            net_change=net_change,
            summary=summary,
            highlights=highlights,
            recommendations=recommendations
        )

    async def compare_with_latest(
        self,
        project_id: str,
        scan_id: str
    ) -> ComparisonResult:
        """Compare a scan with the latest scan for the project"""
        latest_scan = await self._get_latest_scan(project_id)
        if not latest_scan:
            raise ValueError("No scans found for project")

        return await self.compare_scans(scan_id, latest_scan.scan_id)

    async def compare_branches(
        self,
        project_id: str,
        base_branch: str,
        compare_branch: str
    ) -> ComparisonResult:
        """Compare latest scans from two branches"""
        base_scan = await self._get_latest_scan_for_branch(project_id, base_branch)
        compare_scan = await self._get_latest_scan_for_branch(project_id, compare_branch)
        
        if not base_scan or not compare_scan:
            raise ValueError("Scans not found for one or both branches")

        return await self.compare_scans(base_scan.scan_id, compare_scan.scan_id)

    async def get_remediation_progress(
        self,
        project_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get remediation progress over time.
        Shows how many vulnerabilities were fixed vs introduced per period.
        """
        scans = await self._get_scans_for_period(project_id, days)
        
        if len(scans) < 2:
            return {
                "message": "Need at least 2 scans to calculate progress",
                "scans_available": len(scans)
            }

        # Compare consecutive scans
        progress_data = []
        total_fixed = 0
        total_new = 0
        
        for i in range(1, len(scans)):
            base = scans[i - 1]
            compare = scans[i]
            
            comparison = await self.compare_scans(base.scan_id, compare.scan_id)
            
            progress_data.append({
                "date": compare.timestamp.isoformat(),
                "scan_id": compare.scan_id,
                "fixed": comparison.fixed_count,
                "new": comparison.new_count,
                "reintroduced": comparison.reintroduced_count,
                "net_change": comparison.net_change,
                "total_findings": compare.total_findings
            })
            
            total_fixed += comparison.fixed_count
            total_new += comparison.new_count

        # Calculate overall metrics
        first_scan = scans[0]
        last_scan = scans[-1]
        
        return {
            "period_start": first_scan.timestamp.isoformat(),
            "period_end": last_scan.timestamp.isoformat(),
            "total_scans": len(scans),
            "total_fixed": total_fixed,
            "total_new": total_new,
            "net_reduction": total_fixed - total_new,
            "starting_findings": first_scan.total_findings,
            "current_findings": last_scan.total_findings,
            "reduction_percentage": (
                (first_scan.total_findings - last_scan.total_findings) / 
                first_scan.total_findings * 100
            ) if first_scan.total_findings > 0 else 0,
            "progress": progress_data
        }

    async def get_fix_velocity(
        self,
        project_id: str,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate fix velocity metrics"""
        # Get historical fix data
        fixes = await self._get_fix_history(project_id, severity)
        
        if not fixes:
            return {"message": "No fix data available"}

        # Calculate metrics
        fix_times = [f["time_to_fix_hours"] for f in fixes if f.get("time_to_fix_hours")]
        
        if not fix_times:
            return {"message": "Insufficient data for velocity calculation"}

        import statistics
        
        avg_time = statistics.mean(fix_times)
        median_time = statistics.median(fix_times)
        
        # Group by severity
        by_severity = defaultdict(list)
        for f in fixes:
            if f.get("time_to_fix_hours"):
                by_severity[f["severity"]].append(f["time_to_fix_hours"])

        severity_metrics = {}
        for sev, times in by_severity.items():
            severity_metrics[sev] = {
                "avg_hours": statistics.mean(times),
                "median_hours": statistics.median(times),
                "count": len(times)
            }

        return {
            "overall": {
                "avg_hours": avg_time,
                "median_hours": median_time,
                "total_fixed": len(fix_times)
            },
            "by_severity": severity_metrics,
            "trend": "improving" if avg_time < 48 else "needs_attention"
        }

    async def generate_comparison_report(
        self,
        comparison: ComparisonResult
    ) -> Dict[str, Any]:
        """Generate a detailed comparison report"""
        return {
            "report_type": "scan_comparison",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "base_scan": {
                "id": comparison.base_scan.scan_id,
                "timestamp": comparison.base_scan.timestamp.isoformat(),
                "branch": comparison.base_scan.branch,
                "commit": comparison.base_scan.commit_sha,
                "total_findings": comparison.base_scan.total_findings
            },
            "compare_scan": {
                "id": comparison.compare_scan.scan_id,
                "timestamp": comparison.compare_scan.timestamp.isoformat(),
                "branch": comparison.compare_scan.branch,
                "commit": comparison.compare_scan.commit_sha,
                "total_findings": comparison.compare_scan.total_findings
            },
            "summary": {
                "fixed": comparison.fixed_count,
                "new": comparison.new_count,
                "unchanged": comparison.unchanged_count,
                "reintroduced": comparison.reintroduced_count,
                "modified": comparison.modified_count,
                "net_change": comparison.net_change,
                "improvement_score": comparison.improvement_score
            },
            "severity_breakdown": {
                "fixed": comparison.fixed_by_severity,
                "new": comparison.new_by_severity
            },
            "details": {
                "fixed": [
                    self._format_finding_change(fc) 
                    for fc in comparison.fixed
                ],
                "new": [
                    self._format_finding_change(fc)
                    for fc in comparison.new
                ],
                "reintroduced": [
                    self._format_finding_change(fc)
                    for fc in comparison.reintroduced
                ],
                "modified": [
                    self._format_finding_change(fc)
                    for fc in comparison.modified
                ]
            },
            "analysis": {
                "summary": comparison.summary,
                "highlights": comparison.highlights,
                "recommendations": comparison.recommendations
            }
        }

    # ============ Private Methods ============

    async def _load_scan(self, scan_id: str) -> Optional[ScanSummary]:
        """Load scan summary from database"""
        # Would query database in real implementation
        # For demo, return mock data
        return ScanSummary(
            scan_id=scan_id,
            timestamp=datetime.now(timezone.utc),
            project_id="project-1",
            branch="main",
            commit_sha="abc123",
            total_findings=50,
            critical=2,
            high=8,
            medium=20,
            low=15,
            info=5,
            scanners_used=["semgrep", "trivy", "gitleaks"],
            duration_seconds=45.5
        )

    async def _load_findings(self, scan_id: str) -> List[Finding]:
        """Load findings from a scan"""
        # Would query database in real implementation
        # For demo, return mock findings
        import random
        
        findings = []
        severities = list(FindingSeverity)
        rules = [
            "sql-injection", "xss-stored", "hardcoded-secret",
            "weak-crypto", "path-traversal", "ssrf", "open-redirect"
        ]
        
        for i in range(random.randint(30, 70)):
            severity = random.choice(severities)
            rule = random.choice(rules)
            findings.append(Finding(
                id=f"finding-{scan_id}-{i}",
                rule_id=rule,
                title=f"{rule.replace('-', ' ').title()} Vulnerability",
                description=f"Detected potential {rule} vulnerability",
                severity=severity,
                file_path=f"src/app/module{i % 5}.py",
                line_start=random.randint(1, 500),
                scanner="semgrep",
                category="security"
            ))
        
        return findings

    async def _get_latest_scan(self, project_id: str) -> Optional[ScanSummary]:
        """Get the latest scan for a project"""
        return ScanSummary(
            scan_id="latest-scan",
            timestamp=datetime.now(timezone.utc),
            project_id=project_id,
            total_findings=45
        )

    async def _get_latest_scan_for_branch(
        self, 
        project_id: str,
        branch: str
    ) -> Optional[ScanSummary]:
        """Get latest scan for a specific branch"""
        return ScanSummary(
            scan_id=f"scan-{branch}-latest",
            timestamp=datetime.now(timezone.utc),
            project_id=project_id,
            branch=branch,
            total_findings=40
        )

    async def _get_scans_for_period(
        self,
        project_id: str,
        days: int
    ) -> List[ScanSummary]:
        """Get all scans for a project in the given period"""
        # Mock data for demo
        from datetime import timedelta
        
        scans = []
        now = datetime.now(timezone.utc)
        
        for i in range(min(days // 7, 10)):  # One scan per week
            scan_date = now - timedelta(days=i * 7)
            scans.append(ScanSummary(
                scan_id=f"scan-{i}",
                timestamp=scan_date,
                project_id=project_id,
                total_findings=50 - i * 2  # Simulating improvement
            ))
        
        return list(reversed(scans))

    async def _get_historical_fixed(
        self,
        project_id: str,
        before_date: datetime
    ) -> Set[str]:
        """Get fingerprints of historically fixed findings"""
        # Would query fix history in real implementation
        return set()

    async def _get_fix_history(
        self,
        project_id: str,
        severity: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get fix history for velocity calculation"""
        import random
        
        fixes = []
        for i in range(50):
            fixes.append({
                "severity": random.choice(["critical", "high", "medium", "low"]),
                "time_to_fix_hours": random.uniform(4, 168),
                "fixed_at": datetime.now(timezone.utc).isoformat()
            })
        
        if severity:
            fixes = [f for f in fixes if f["severity"] == severity]
        
        return fixes

    def _count_by_severity(self, changes: List[FindingChange]) -> Dict[str, int]:
        """Count changes by severity"""
        counts = defaultdict(int)
        for change in changes:
            counts[change.finding.severity.value] += 1
        return dict(counts)

    def _calculate_improvement_score(
        self,
        fixed: List[FindingChange],
        new: List[FindingChange],
        reintroduced: List[FindingChange]
    ) -> float:
        """
        Calculate improvement score.
        Positive = improved, Negative = degraded
        """
        # Weight by severity
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1,
            "info": 0.1
        }
        
        fixed_score = sum(
            severity_weights.get(fc.finding.severity.value, 1)
            for fc in fixed
        )
        
        new_score = sum(
            severity_weights.get(fc.finding.severity.value, 1)
            for fc in new
        )
        
        reintro_score = sum(
            severity_weights.get(fc.finding.severity.value, 1) * 1.5  # Penalty for reintroduction
            for fc in reintroduced
        )
        
        return round(fixed_score - new_score - reintro_score, 2)

    def _generate_summary(
        self,
        fixed: List[FindingChange],
        new: List[FindingChange],
        reintroduced: List[FindingChange],
        modified: List[FindingChange]
    ) -> str:
        """Generate human-readable summary"""
        parts = []
        
        if fixed:
            parts.append(f"{len(fixed)} vulnerabilities fixed")
        if new:
            parts.append(f"{len(new)} new vulnerabilities introduced")
        if reintroduced:
            parts.append(f"{len(reintroduced)} vulnerabilities reintroduced")
        if modified:
            parts.append(f"{len(modified)} vulnerabilities changed severity")

        if len(fixed) > len(new) + len(reintroduced):
            parts.append("Overall security posture has improved")
        elif len(new) + len(reintroduced) > len(fixed):
            parts.append("Overall security posture needs attention")
        else:
            parts.append("Security posture is stable")

        return ". ".join(parts) + "."

    def _generate_highlights(
        self,
        fixed: List[FindingChange],
        new: List[FindingChange],
        reintroduced: List[FindingChange],
        modified: List[FindingChange]
    ) -> List[str]:
        """Generate highlight points"""
        highlights = []
        
        # Count critical fixes
        critical_fixed = [fc for fc in fixed if fc.finding.severity == FindingSeverity.CRITICAL]
        if critical_fixed:
            highlights.append(f"🎉 {len(critical_fixed)} critical vulnerabilities fixed!")
        
        # Count critical new
        critical_new = [fc for fc in new if fc.finding.severity == FindingSeverity.CRITICAL]
        if critical_new:
            highlights.append(f"⚠️ {len(critical_new)} new critical vulnerabilities detected")
        
        # Reintroductions
        if reintroduced:
            highlights.append(f"🔄 {len(reintroduced)} previously fixed issues have reappeared")
        
        # Most common fixed rule
        if fixed:
            rule_counts = defaultdict(int)
            for fc in fixed:
                rule_counts[fc.finding.rule_id] += 1
            top_rule = max(rule_counts.items(), key=lambda x: x[1])
            highlights.append(f"📊 Most fixed rule: {top_rule[0]} ({top_rule[1]} instances)")

        return highlights

    def _generate_recommendations(
        self,
        new: List[FindingChange],
        reintroduced: List[FindingChange]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Prioritize critical/high
        critical_high = [
            fc for fc in new + reintroduced
            if fc.finding.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
        ]
        
        if critical_high:
            recommendations.append(
                f"Prioritize fixing {len(critical_high)} critical/high severity issues"
            )
        
        if reintroduced:
            recommendations.append(
                "Review recent changes that may have reintroduced fixed vulnerabilities"
            )
            recommendations.append(
                "Consider adding regression tests for previously fixed issues"
            )
        
        # Group by file for focused remediation
        files_with_issues = set()
        for fc in new:
            files_with_issues.add(fc.finding.file_path)
        
        if len(files_with_issues) > 5:
            recommendations.append(
                f"Issues span {len(files_with_issues)} files - consider targeted code review"
            )
        
        # Scanner recommendations
        scanners = set(fc.finding.scanner for fc in new if fc.finding.scanner)
        if scanners:
            recommendations.append(
                f"Focus on issues from: {', '.join(scanners)}"
            )

        return recommendations

    def _format_finding_change(self, fc: FindingChange) -> Dict[str, Any]:
        """Format finding change for API response"""
        result = {
            "change_type": fc.change_type.value,
            "finding": {
                "id": fc.finding.id,
                "rule_id": fc.finding.rule_id,
                "title": fc.finding.title,
                "severity": fc.finding.severity.value,
                "file_path": fc.finding.file_path,
                "line": fc.finding.line_start,
                "scanner": fc.finding.scanner
            }
        }
        
        if fc.severity_change:
            result["severity_change"] = {
                "from": fc.severity_change[0],
                "to": fc.severity_change[1]
            }
        
        if fc.notes:
            result["notes"] = fc.notes

        return result


# Singleton instance
_comparison_service: Optional[ScanComparisonService] = None


def get_scan_comparison_service(db=None) -> ScanComparisonService:
    """Get scan comparison service instance"""
    global _comparison_service
    if _comparison_service is None:
        _comparison_service = ScanComparisonService(db)
    return _comparison_service
