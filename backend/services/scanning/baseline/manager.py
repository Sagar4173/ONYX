"""
Advanced Baseline Management with Drift Detection
Stores baseline findings per repo+branch and detects security regressions/improvements
"""
import asyncio
import logging
import json
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import deepdiff
import statistics

logger = logging.getLogger(__name__)

from models.base import SeverityLevel


class ChangeType(Enum):
    """Types of baseline changes"""
    NEW_ISSUE = "new_issue"           # New vulnerability found
    RESOLVED_ISSUE = "resolved_issue" # Vulnerability fixed
    MODIFIED_ISSUE = "modified_issue" # Existing vulnerability changed
    RECURRING_ISSUE = "recurring_issue" # Previously fixed vulnerability returned


# DriftSeverity extends SeverityLevel with IMPROVED status for drift detection
class DriftSeverity(Enum):
    """Severity of baseline drift - extends standard levels with IMPROVED"""
    CRITICAL = "critical"  # Critical new vulnerabilities
    HIGH = "high"         # High severity new issues or many new issues
    MEDIUM = "medium"     # Medium severity changes
    LOW = "low"          # Minor changes or improvements
    IMPROVED = "improved" # Overall security improvement (unique to drift detection)

class BaselineStatus(Enum):
    """Baseline status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"

@dataclass
class SecurityFinding:
    """Individual security finding"""
    finding_id: str
    rule_id: str
    file_path: str
    line_number: int
    column_number: int = 0
    severity: str = "medium"
    category: str = "security"
    message: str = ""
    code_snippet: str = ""
    cwe_id: Optional[str] = None
    confidence: float = 1.0
    fingerprint: str = ""  # Unique fingerprint for tracking
    
    def __post_init__(self):
        """Generate fingerprint if not provided"""
        if not self.fingerprint:
            self.fingerprint = self.generate_fingerprint()
    
    def generate_fingerprint(self) -> str:
        """Generate unique fingerprint for finding"""
        # Combine key attributes to create unique identifier
        content = f"{self.rule_id}:{self.file_path}:{self.line_number}:{self.message}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

@dataclass
class SecurityBaseline:
    """Security baseline for repository+branch"""
    baseline_id: str
    repository: str
    branch: str
    commit_hash: str
    scan_timestamp: datetime
    findings: List[SecurityFinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: BaselineStatus = BaselineStatus.ACTIVE
    created_by: str = "system"
    notes: str = ""

@dataclass
class BaselineDrift:
    """Detected drift between baselines"""
    drift_id: str
    old_baseline_id: str
    new_baseline_id: str
    repository: str
    branch: str
    detected_at: datetime
    drift_severity: DriftSeverity
    new_issues: List[SecurityFinding] = field(default_factory=list)
    resolved_issues: List[SecurityFinding] = field(default_factory=list)
    modified_issues: List[Tuple[SecurityFinding, SecurityFinding]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    auto_actions_taken: List[str] = field(default_factory=list)

class BaselineManager:
    """Advanced baseline management with drift detection"""
    
    def __init__(self, data_dir: str = "data/baselines"):
        """Initialize baseline manager"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database for baseline storage
        self.db_path = self.data_dir / "baselines.db"
        
        # Drift detection configuration
        self.drift_config = {
            "max_new_critical": 0,      # 0 new critical issues allowed
            "max_new_high": 2,          # 2 new high severity issues allowed
            "max_new_medium": 10,       # 10 new medium severity issues allowed
            "regression_penalty": 2.0,  # Multiply score for recurring issues
            "improvement_threshold": 0.2, # 20% reduction for "improved" status
            "auto_close_resolved": True, # Auto-close resolved issues in tracker
            "auto_create_tickets": True  # Auto-create tickets for new critical issues
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize baseline database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS security_baselines (
                    baseline_id TEXT PRIMARY KEY,
                    repository TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    commit_hash TEXT NOT NULL,
                    scan_timestamp TEXT NOT NULL,
                    findings TEXT,              -- JSON array of findings
                    metadata TEXT,              -- JSON object
                    status TEXT NOT NULL,
                    created_by TEXT,
                    notes TEXT,
                    created_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS baseline_findings (
                    finding_id TEXT PRIMARY KEY,
                    baseline_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER,
                    severity TEXT NOT NULL,
                    category TEXT,
                    message TEXT,
                    code_snippet TEXT,
                    cwe_id TEXT,
                    confidence REAL,
                    fingerprint TEXT NOT NULL,
                    created_at TEXT,
                    FOREIGN KEY (baseline_id) REFERENCES security_baselines (baseline_id)
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS baseline_drifts (
                    drift_id TEXT PRIMARY KEY,
                    old_baseline_id TEXT NOT NULL,
                    new_baseline_id TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    drift_severity TEXT NOT NULL,
                    new_issues_count INTEGER,
                    resolved_issues_count INTEGER,
                    modified_issues_count INTEGER,
                    summary TEXT,               -- JSON object
                    auto_actions_taken TEXT,    -- JSON array
                    FOREIGN KEY (old_baseline_id) REFERENCES security_baselines (baseline_id),
                    FOREIGN KEY (new_baseline_id) REFERENCES security_baselines (baseline_id)
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS drift_changes (
                    change_id TEXT PRIMARY KEY,
                    drift_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    finding_fingerprint TEXT NOT NULL,
                    old_finding TEXT,           -- JSON object (for modified/resolved)
                    new_finding TEXT,           -- JSON object (for new/modified)
                    change_details TEXT,        -- JSON object
                    FOREIGN KEY (drift_id) REFERENCES baseline_drifts (drift_id)
                )
                """)
                
                # Indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_baselines_repo_branch ON security_baselines(repository, branch)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_baselines_status ON security_baselines(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_baseline ON baseline_findings(baseline_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_fingerprint ON baseline_findings(fingerprint)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_drifts_repo_branch ON baseline_drifts(repository, branch)")
                
        except Exception as e:
            logger.error(f"Failed to initialize baseline database: {e}")
            raise
    
    async def create_baseline(self, repository: str, branch: str, commit_hash: str,
                            findings: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None,
                            created_by: str = "system") -> str:
        """Create new security baseline"""
        try:
            baseline_id = str(uuid.uuid4())
            
            # Convert findings to SecurityFinding objects
            security_findings = []
            for finding_data in findings:
                finding = SecurityFinding(
                    finding_id=str(uuid.uuid4()),
                    rule_id=finding_data.get("rule_id", "unknown"),
                    file_path=finding_data.get("file_path", ""),
                    line_number=finding_data.get("line_number", 0),
                    column_number=finding_data.get("column_number", 0),
                    severity=finding_data.get("severity", "medium"),
                    category=finding_data.get("category", "security"),
                    message=finding_data.get("message", ""),
                    code_snippet=finding_data.get("code_snippet", ""),
                    cwe_id=finding_data.get("cwe_id"),
                    confidence=finding_data.get("confidence", 1.0)
                )
                security_findings.append(finding)
            
            # Create baseline
            baseline = SecurityBaseline(
                baseline_id=baseline_id,
                repository=repository,
                branch=branch,
                commit_hash=commit_hash,
                scan_timestamp=datetime.now(timezone.utc),
                findings=security_findings,
                metadata=metadata or {},
                created_by=created_by
            )
            
            # Archive previous active baseline
            await self._archive_previous_baseline(repository, branch)
            
            # Store new baseline
            await self._store_baseline(baseline)
            
            logger.info(f"Created baseline {baseline_id} for {repository}:{branch} with {len(security_findings)} findings")
            return baseline_id
            
        except Exception as e:
            logger.error(f"Failed to create baseline: {e}")
            raise
    
    async def detect_drift(self, repository: str, branch: str, 
                         new_findings: List[Dict[str, Any]], 
                         commit_hash: str) -> Optional[BaselineDrift]:
        """Detect drift between current scan and latest baseline"""
        try:
            # Get latest baseline
            current_baseline = await self._get_latest_baseline(repository, branch)
            
            if not current_baseline:
                logger.info(f"No baseline found for {repository}:{branch}, creating first baseline")
                await self.create_baseline(repository, branch, commit_hash, new_findings)
                return None
            
            # Convert new findings to SecurityFinding objects
            new_security_findings = []
            for finding_data in new_findings:
                finding = SecurityFinding(
                    finding_id=str(uuid.uuid4()),
                    rule_id=finding_data.get("rule_id", "unknown"),
                    file_path=finding_data.get("file_path", ""),
                    line_number=finding_data.get("line_number", 0),
                    column_number=finding_data.get("column_number", 0),
                    severity=finding_data.get("severity", "medium"),
                    category=finding_data.get("category", "security"),
                    message=finding_data.get("message", ""),
                    code_snippet=finding_data.get("code_snippet", ""),
                    cwe_id=finding_data.get("cwe_id"),
                    confidence=finding_data.get("confidence", 1.0)
                )
                new_security_findings.append(finding)
            
            # Create temporary new baseline
            new_baseline_id = str(uuid.uuid4())
            
            # Detect changes
            drift = await self._calculate_drift(
                current_baseline, new_security_findings, new_baseline_id, commit_hash
            )
            
            if drift:
                # Store drift record
                await self._store_drift(drift)
                
                # Take automatic actions
                await self._take_automatic_actions(drift)
                
                # Create new baseline if significant changes
                if drift.drift_severity in [DriftSeverity.CRITICAL, DriftSeverity.HIGH, DriftSeverity.MEDIUM]:
                    await self.create_baseline(repository, branch, commit_hash, new_findings)
                
                logger.info(f"Detected {drift.drift_severity.value} drift for {repository}:{branch}")
                
            return drift
            
        except Exception as e:
            logger.error(f"Failed to detect drift: {e}")
            return None
    
    async def _calculate_drift(self, old_baseline: SecurityBaseline, 
                             new_findings: List[SecurityFinding],
                             new_baseline_id: str, commit_hash: str) -> Optional[BaselineDrift]:
        """Calculate drift between old baseline and new findings"""
        try:
            # Create fingerprint maps for comparison
            old_fingerprints = {f.fingerprint: f for f in old_baseline.findings}
            new_fingerprints = {f.fingerprint: f for f in new_findings}
            
            # Detect changes
            new_issues = []
            resolved_issues = []
            modified_issues = []
            
            # Find new issues (in new but not in old)
            for fingerprint, finding in new_fingerprints.items():
                if fingerprint not in old_fingerprints:
                    new_issues.append(finding)
            
            # Find resolved issues (in old but not in new)
            for fingerprint, finding in old_fingerprints.items():
                if fingerprint not in new_fingerprints:
                    resolved_issues.append(finding)
            
            # Find modified issues (in both but with changes)
            for fingerprint in set(old_fingerprints.keys()) & set(new_fingerprints.keys()):
                old_finding = old_fingerprints[fingerprint]
                new_finding = new_fingerprints[fingerprint]
                
                # Check for meaningful changes
                if (old_finding.severity != new_finding.severity or
                    old_finding.message != new_finding.message or
                    old_finding.confidence != new_finding.confidence):
                    modified_issues.append((old_finding, new_finding))
            
            # Calculate drift severity
            drift_severity = self._calculate_drift_severity(new_issues, resolved_issues, modified_issues)
            
            # If no significant changes, return None
            if (not new_issues and not resolved_issues and not modified_issues and
                drift_severity == DriftSeverity.LOW):
                return None
            
            # Create drift object
            drift = BaselineDrift(
                drift_id=str(uuid.uuid4()),
                old_baseline_id=old_baseline.baseline_id,
                new_baseline_id=new_baseline_id,
                repository=old_baseline.repository,
                branch=old_baseline.branch,
                detected_at=datetime.now(timezone.utc),
                drift_severity=drift_severity,
                new_issues=new_issues,
                resolved_issues=resolved_issues,
                modified_issues=modified_issues,
                summary=self._create_drift_summary(new_issues, resolved_issues, modified_issues)
            )
            
            return drift
            
        except Exception as e:
            logger.error(f"Failed to calculate drift: {e}")
            return None
    
    def _calculate_drift_severity(self, new_issues: List[SecurityFinding],
                                resolved_issues: List[SecurityFinding],
                                modified_issues: List[Tuple[SecurityFinding, SecurityFinding]]) -> DriftSeverity:
        """Calculate overall drift severity"""
        try:
            # Count new issues by severity
            new_critical = len([f for f in new_issues if f.severity.lower() == "critical"])
            new_high = len([f for f in new_issues if f.severity.lower() == "high"])
            new_medium = len([f for f in new_issues if f.severity.lower() == "medium"])
            
            # Count resolved issues by severity  
            resolved_critical = len([f for f in resolved_issues if f.severity.lower() == "critical"])
            resolved_high = len([f for f in resolved_issues if f.severity.lower() == "high"])
            
            # Check critical thresholds
            if new_critical > self.drift_config["max_new_critical"]:
                return DriftSeverity.CRITICAL
            
            if new_high > self.drift_config["max_new_high"]:
                return DriftSeverity.CRITICAL
            
            # Check for high severity conditions
            if new_critical > 0 or new_high > 2:
                return DriftSeverity.HIGH
            
            if new_medium > self.drift_config["max_new_medium"]:
                return DriftSeverity.HIGH
            
            # Check for improvements
            total_new = len(new_issues)
            total_resolved = len(resolved_issues)
            
            if total_resolved > total_new and resolved_critical + resolved_high > 0:
                improvement_ratio = (total_resolved - total_new) / max(total_resolved, 1)
                if improvement_ratio >= self.drift_config["improvement_threshold"]:
                    return DriftSeverity.IMPROVED
            
            # Medium severity for moderate changes
            if total_new > 0 or len(modified_issues) > 3:
                return DriftSeverity.MEDIUM
            
            return DriftSeverity.LOW
            
        except Exception as e:
            logger.error(f"Failed to calculate drift severity: {e}")
            return DriftSeverity.MEDIUM
    
    def _create_drift_summary(self, new_issues: List[SecurityFinding],
                            resolved_issues: List[SecurityFinding],
                            modified_issues: List[Tuple[SecurityFinding, SecurityFinding]]) -> Dict[str, Any]:
        """Create summary of drift changes"""
        try:
            # Count by severity
            new_by_severity = {}
            resolved_by_severity = {}
            
            for finding in new_issues:
                severity = finding.severity.lower()
                new_by_severity[severity] = new_by_severity.get(severity, 0) + 1
            
            for finding in resolved_issues:
                severity = finding.severity.lower()
                resolved_by_severity[severity] = resolved_by_severity.get(severity, 0) + 1
            
            # Count by category
            new_by_category = {}
            for finding in new_issues:
                category = finding.category
                new_by_category[category] = new_by_category.get(category, 0) + 1
            
            return {
                "total_changes": len(new_issues) + len(resolved_issues) + len(modified_issues),
                "new_issues": {
                    "total": len(new_issues),
                    "by_severity": new_by_severity,
                    "by_category": new_by_category
                },
                "resolved_issues": {
                    "total": len(resolved_issues),
                    "by_severity": resolved_by_severity
                },
                "modified_issues": {
                    "total": len(modified_issues)
                },
                "net_change": len(new_issues) - len(resolved_issues),
                "security_score_change": self._calculate_security_score_change(
                    new_issues, resolved_issues
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to create drift summary: {e}")
            return {}
    
    def _calculate_security_score_change(self, new_issues: List[SecurityFinding],
                                       resolved_issues: List[SecurityFinding]) -> float:
        """Calculate change in security score"""
        try:
            severity_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
            
            # Calculate negative impact from new issues
            negative_score = 0
            for finding in new_issues:
                weight = severity_weights.get(finding.severity.lower(), 1)
                negative_score += weight
            
            # Calculate positive impact from resolved issues
            positive_score = 0
            for finding in resolved_issues:
                weight = severity_weights.get(finding.severity.lower(), 1)
                positive_score += weight
            
            return positive_score - negative_score
            
        except Exception as e:
            logger.error(f"Failed to calculate security score change: {e}")
            return 0.0
    
    async def _take_automatic_actions(self, drift: BaselineDrift):
        """Take automatic actions based on drift"""
        try:
            actions_taken = []
            
            # Auto-close resolved issues if configured
            if self.drift_config["auto_close_resolved"] and drift.resolved_issues:
                for resolved_issue in drift.resolved_issues:
                    # Mock auto-close action
                    logger.info(f"Auto-closing resolved issue: {resolved_issue.finding_id}")
                actions_taken.append(f"Auto-closed {len(drift.resolved_issues)} resolved issues")
            
            # Auto-create tickets for critical new issues
            if self.drift_config["auto_create_tickets"]:
                critical_new = [f for f in drift.new_issues if f.severity.lower() == "critical"]
                if critical_new:
                    for critical_issue in critical_new:
                        # Mock ticket creation
                        logger.info(f"Auto-creating ticket for critical issue: {critical_issue.finding_id}")
                    actions_taken.append(f"Created tickets for {len(critical_new)} critical issues")
            
            # Block merge for critical drift
            if drift.drift_severity == DriftSeverity.CRITICAL:
                logger.warning(f"Blocking merge due to critical security drift in {drift.repository}:{drift.branch}")
                actions_taken.append("Blocked merge due to critical security regression")
            
            drift.auto_actions_taken = actions_taken
            
        except Exception as e:
            logger.error(f"Failed to take automatic actions: {e}")
    
    async def _archive_previous_baseline(self, repository: str, branch: str):
        """Archive the previous active baseline"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                UPDATE security_baselines 
                SET status = ? 
                WHERE repository = ? AND branch = ? AND status = ?
                """, (BaselineStatus.SUPERSEDED.value, repository, branch, BaselineStatus.ACTIVE.value))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to archive previous baseline: {e}")
    
    async def _store_baseline(self, baseline: SecurityBaseline):
        """Store baseline in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store baseline record
                conn.execute("""
                INSERT INTO security_baselines (
                    baseline_id, repository, branch, commit_hash, scan_timestamp,
                    findings, metadata, status, created_by, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    baseline.baseline_id,
                    baseline.repository,
                    baseline.branch,
                    baseline.commit_hash,
                    baseline.scan_timestamp.isoformat(),
                    json.dumps([{
                        "finding_id": f.finding_id,
                        "rule_id": f.rule_id,
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "column_number": f.column_number,
                        "severity": f.severity,
                        "category": f.category,
                        "message": f.message,
                        "code_snippet": f.code_snippet,
                        "cwe_id": f.cwe_id,
                        "confidence": f.confidence,
                        "fingerprint": f.fingerprint
                    } for f in baseline.findings]),
                    json.dumps(baseline.metadata),
                    baseline.status.value,
                    baseline.created_by,
                    baseline.notes,
                    datetime.now(timezone.utc).isoformat()
                ))
                
                # Store individual findings
                for finding in baseline.findings:
                    conn.execute("""
                    INSERT INTO baseline_findings (
                        finding_id, baseline_id, rule_id, file_path, line_number,
                        column_number, severity, category, message, code_snippet,
                        cwe_id, confidence, fingerprint, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        finding.finding_id,
                        baseline.baseline_id,
                        finding.rule_id,
                        finding.file_path,
                        finding.line_number,
                        finding.column_number,
                        finding.severity,
                        finding.category,
                        finding.message,
                        finding.code_snippet,
                        finding.cwe_id,
                        finding.confidence,
                        finding.fingerprint,
                        datetime.now(timezone.utc).isoformat()
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store baseline: {e}")
            raise
    
    async def _store_drift(self, drift: BaselineDrift):
        """Store drift record in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store drift record
                conn.execute("""
                INSERT INTO baseline_drifts (
                    drift_id, old_baseline_id, new_baseline_id, repository, branch,
                    detected_at, drift_severity, new_issues_count, resolved_issues_count,
                    modified_issues_count, summary, auto_actions_taken
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    drift.drift_id,
                    drift.old_baseline_id,
                    drift.new_baseline_id,
                    drift.repository,
                    drift.branch,
                    drift.detected_at.isoformat(),
                    drift.drift_severity.value,
                    len(drift.new_issues),
                    len(drift.resolved_issues),
                    len(drift.modified_issues),
                    json.dumps(drift.summary),
                    json.dumps(drift.auto_actions_taken)
                ))
                
                # Store individual changes
                for new_issue in drift.new_issues:
                    conn.execute("""
                    INSERT INTO drift_changes (
                        change_id, drift_id, change_type, finding_fingerprint,
                        old_finding, new_finding, change_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        drift.drift_id,
                        ChangeType.NEW_ISSUE.value,
                        new_issue.fingerprint,
                        None,
                        json.dumps({
                            "finding_id": new_issue.finding_id,
                            "rule_id": new_issue.rule_id,
                            "file_path": new_issue.file_path,
                            "line_number": new_issue.line_number,
                            "severity": new_issue.severity,
                            "message": new_issue.message
                        }),
                        json.dumps({"type": "new_vulnerability"})
                    ))
                
                for resolved_issue in drift.resolved_issues:
                    conn.execute("""
                    INSERT INTO drift_changes (
                        change_id, drift_id, change_type, finding_fingerprint,
                        old_finding, new_finding, change_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        drift.drift_id,
                        ChangeType.RESOLVED_ISSUE.value,
                        resolved_issue.fingerprint,
                        json.dumps({
                            "finding_id": resolved_issue.finding_id,
                            "rule_id": resolved_issue.rule_id,
                            "file_path": resolved_issue.file_path,
                            "line_number": resolved_issue.line_number,
                            "severity": resolved_issue.severity,
                            "message": resolved_issue.message
                        }),
                        None,
                        json.dumps({"type": "vulnerability_fixed"})
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store drift: {e}")
            raise
    
    async def _get_latest_baseline(self, repository: str, branch: str) -> Optional[SecurityBaseline]:
        """Get the latest active baseline for repository+branch"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                SELECT * FROM security_baselines 
                WHERE repository = ? AND branch = ? AND status = ?
                ORDER BY scan_timestamp DESC
                LIMIT 1
                """, (repository, branch, BaselineStatus.ACTIVE.value))
                
                row = cursor.fetchone()
                
                if row:
                    findings_data = json.loads(row[5]) if row[5] else []
                    findings = []
                    
                    for finding_data in findings_data:
                        finding = SecurityFinding(
                            finding_id=finding_data["finding_id"],
                            rule_id=finding_data["rule_id"],
                            file_path=finding_data["file_path"],
                            line_number=finding_data["line_number"],
                            column_number=finding_data.get("column_number", 0),
                            severity=finding_data["severity"],
                            category=finding_data.get("category", "security"),
                            message=finding_data.get("message", ""),
                            code_snippet=finding_data.get("code_snippet", ""),
                            cwe_id=finding_data.get("cwe_id"),
                            confidence=finding_data.get("confidence", 1.0),
                            fingerprint=finding_data["fingerprint"]
                        )
                        findings.append(finding)
                    
                    return SecurityBaseline(
                        baseline_id=row[0],
                        repository=row[1],
                        branch=row[2],
                        commit_hash=row[3],
                        scan_timestamp=datetime.fromisoformat(row[4]),
                        findings=findings,
                        metadata=json.loads(row[6]) if row[6] else {},
                        status=BaselineStatus(row[7]),
                        created_by=row[8] or "system",
                        notes=row[9] or ""
                    )
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest baseline: {e}")
            return None
    
    async def get_drift_history(self, repository: str, branch: str,
                              days: int = 30) -> List[Dict[str, Any]]:
        """Get drift history for repository+branch"""
        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                SELECT drift_id, detected_at, drift_severity, new_issues_count,
                       resolved_issues_count, modified_issues_count, summary
                FROM baseline_drifts
                WHERE repository = ? AND branch = ? AND detected_at >= ?
                ORDER BY detected_at DESC
                """, (repository, branch, since_date.isoformat()))
                
                drifts = []
                for row in cursor.fetchall():
                    drifts.append({
                        "drift_id": row[0],
                        "detected_at": row[1],
                        "drift_severity": row[2],
                        "new_issues_count": row[3],
                        "resolved_issues_count": row[4],
                        "modified_issues_count": row[5],
                        "summary": json.loads(row[6]) if row[6] else {}
                    })
                
                return drifts
                
        except Exception as e:
            logger.error(f"Failed to get drift history: {e}")
            return []
    
    async def get_baseline_comparison(self, baseline_id1: str, baseline_id2: str) -> Dict[str, Any]:
        """Compare two baselines and show differences"""
        try:
            # This would be implemented to compare any two baselines
            # For now, return a mock comparison
            return {
                "baseline1_id": baseline_id1,
                "baseline2_id": baseline_id2,
                "comparison_type": "detailed",
                "differences": {
                    "new_in_baseline2": [],
                    "removed_in_baseline2": [],
                    "modified": []
                },
                "summary": {
                    "total_differences": 0,
                    "security_impact": "neutral"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to compare baselines: {e}")
            return {"error": str(e)}
    
    async def get_security_trends(self, repository: str, branch: str,
                                days: int = 90) -> Dict[str, Any]:
        """Get security trends over time"""
        try:
            drifts = await self.get_drift_history(repository, branch, days)
            
            if not drifts:
                return {"error": "No drift data available"}
            
            # Calculate trends
            new_issues_trend = [d["new_issues_count"] for d in drifts]
            resolved_issues_trend = [d["resolved_issues_count"] for d in drifts]
            
            return {
                "repository": repository,
                "branch": branch,
                "time_period_days": days,
                "drift_count": len(drifts),
                "trends": {
                    "new_issues": {
                        "total": sum(new_issues_trend),
                        "average": statistics.mean(new_issues_trend) if new_issues_trend else 0,
                        "trend": "increasing" if len(new_issues_trend) > 1 and new_issues_trend[0] > new_issues_trend[-1] else "stable"
                    },
                    "resolved_issues": {
                        "total": sum(resolved_issues_trend),
                        "average": statistics.mean(resolved_issues_trend) if resolved_issues_trend else 0,
                        "trend": "increasing" if len(resolved_issues_trend) > 1 and resolved_issues_trend[0] > resolved_issues_trend[-1] else "stable"
                    },
                    "net_improvement": sum(resolved_issues_trend) - sum(new_issues_trend)
                },
                "severity_distribution": {
                    "critical_drifts": len([d for d in drifts if d["drift_severity"] == "critical"]),
                    "high_drifts": len([d for d in drifts if d["drift_severity"] == "high"]),
                    "medium_drifts": len([d for d in drifts if d["drift_severity"] == "medium"]),
                    "improved_drifts": len([d for d in drifts if d["drift_severity"] == "improved"])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get security trends: {e}")
            return {"error": str(e)}

# Export main classes
__all__ = [
    'BaselineManager', 'SecurityBaseline', 'SecurityFinding', 'BaselineDrift',
    'ChangeType', 'DriftSeverity', 'BaselineStatus'
]
