"""
Advanced Compliance & Governance System
NIST, ISO 27001 mapping, policy enforcement, audit trails, incident response

DEPRECATED: This module uses SQLite for storage.
Use governance_engine_mongodb.py instead for production.
"""
import json
import logging
import sqlite3
import uuid
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import canonical enums from models.base (SINGLE SOURCE OF TRUTH)
from models.base import ComplianceFramework, IncidentStatus, PolicySeverity

logger = logging.getLogger(__name__)

# Emit deprecation warning
warnings.warn(
    "compliance_governance.py is deprecated. Use governance_engine_mongodb.py instead.",
    DeprecationWarning,
    stacklevel=2
)

@dataclass
class ComplianceControl:
    """Individual compliance control"""
    control_id: str
    framework: ComplianceFramework
    title: str
    description: str
    category: str
    subcategory: str
    implementation_guidance: str
    testing_procedures: List[str] = field(default_factory=list)
    automation_checks: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    maturity_level: int = 1  # 1-5 scale
    is_mandatory: bool = True
    related_controls: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class PolicyViolation:
    """Security policy violation record"""
    violation_id: str
    policy_id: str
    severity: PolicySeverity
    title: str
    description: str
    violated_rule: str
    repository: str
    file_path: str
    line_number: Optional[int]
    commit_hash: str
    author: str
    detected_at: datetime
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation_guidance: str = ""
    status: str = "open"
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""

@dataclass
class AuditEvent:
    """Audit trail event"""
    event_id: str
    event_type: str  # scan, policy_check, incident_response, etc.
    user_id: str
    user_email: str
    action: str
    resource: str
    timestamp: datetime
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_frameworks: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    session_id: Optional[str] = None

@dataclass
class IncidentResponse:
    """Incident response workflow"""
    incident_id: str
    title: str
    description: str
    severity: PolicySeverity
    status: IncidentStatus
    assigned_team: str
    reporter: str
    detected_at: datetime
    source_findings: List[str] = field(default_factory=list)  # Violation IDs
    affected_systems: List[str] = field(default_factory=list)
    containment_actions: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    external_tickets: Dict[str, str] = field(default_factory=dict)  # Jira, SOAR, etc.
    evidence_collected: List[str] = field(default_factory=list)
    lessons_learned: str = ""
    closed_at: Optional[datetime] = None

class ComplianceGovernanceEngine:
    """Advanced compliance and governance system"""
    
    def __init__(self, data_dir: str = "compliance_data"):
        """Initialize compliance governance engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.compliance_db_path = self.data_dir / "compliance.db"
        self.audit_db_path = self.data_dir / "audit_trail.db"
        self.incidents_db_path = self.data_dir / "incidents.db"
        
        # Initialize databases
        self._init_databases()
        
        # Load compliance mappings
        self.control_mappings = self._load_compliance_mappings()
        
        # Policy enforcement rules
        self.enforcement_rules = self._load_enforcement_rules()
        
    def _init_databases(self):
        """Initialize database schemas"""
        try:
            # Compliance controls database
            with sqlite3.connect(self.compliance_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_controls (
                    control_id TEXT PRIMARY KEY,
                    framework TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    subcategory TEXT,
                    implementation_guidance TEXT,
                    testing_procedures TEXT,  -- JSON array
                    automation_checks TEXT,   -- JSON array
                    evidence_requirements TEXT, -- JSON array
                    maturity_level INTEGER DEFAULT 1,
                    is_mandatory INTEGER DEFAULT 1,
                    related_controls TEXT,    -- JSON array
                    created_at TEXT,
                    updated_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_violations (
                    violation_id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    violated_rule TEXT,
                    repository TEXT,
                    file_path TEXT,
                    line_number INTEGER,
                    commit_hash TEXT,
                    author TEXT,
                    detected_at TEXT,
                    evidence TEXT,           -- JSON object
                    remediation_guidance TEXT,
                    status TEXT DEFAULT 'open',
                    assigned_to TEXT,
                    resolved_at TEXT,
                    resolution_notes TEXT
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_severity ON policy_violations(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_status ON policy_violations(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_repo ON policy_violations(repository)")
            
            # Audit trail database
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_email TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    timestamp TEXT NOT NULL,
                    source_ip TEXT,
                    user_agent TEXT,
                    details TEXT,            -- JSON object
                    compliance_frameworks TEXT, -- JSON array
                    risk_score REAL DEFAULT 0.0,
                    session_id TEXT
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type)")
            
            # Incident response database
            with sqlite3.connect(self.incidents_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_team TEXT,
                    reporter TEXT,
                    detected_at TEXT,
                    source_findings TEXT,     -- JSON array
                    affected_systems TEXT,    -- JSON array
                    containment_actions TEXT, -- JSON array
                    timeline TEXT,           -- JSON array
                    external_tickets TEXT,   -- JSON object
                    evidence_collected TEXT, -- JSON array
                    lessons_learned TEXT,
                    closed_at TEXT
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity)")
                
        except Exception as e:
            logger.error(f"Failed to initialize compliance databases: {e}")
            raise
    
    def _load_compliance_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive compliance framework mappings"""
        return {
            "NIST_CSF_CONTROLS": {
                "ID.AM-1": {
                    "title": "Physical devices and systems are inventoried",
                    "category": "Identify",
                    "subcategory": "Asset Management",
                    "automation_checks": ["asset_inventory_scan", "device_discovery"],
                    "evidence": ["asset_register", "network_scans"]
                },
                "ID.AM-2": {
                    "title": "Software platforms and applications are inventoried",
                    "category": "Identify", 
                    "subcategory": "Asset Management",
                    "automation_checks": ["software_inventory", "dependency_scan"],
                    "evidence": ["sbom", "package_manifests"]
                },
                "PR.AC-1": {
                    "title": "Identities and credentials are issued, managed, verified, revoked",
                    "category": "Protect",
                    "subcategory": "Access Control",
                    "automation_checks": ["credential_scan", "access_review"],
                    "evidence": ["iam_logs", "access_matrices"]
                },
                "PR.DS-1": {
                    "title": "Data-at-rest is protected",
                    "category": "Protect",
                    "subcategory": "Data Security",
                    "automation_checks": ["encryption_check", "data_classification"],
                    "evidence": ["encryption_reports", "data_maps"]
                },
                "DE.CM-1": {
                    "title": "The network is monitored to detect potential cybersecurity events",
                    "category": "Detect",
                    "subcategory": "Security Continuous Monitoring",
                    "automation_checks": ["network_monitoring", "anomaly_detection"],
                    "evidence": ["network_logs", "siem_alerts"]
                }
            },
            "ISO_27001_CONTROLS": {
                "A.8.2.1": {
                    "title": "Classification of information",
                    "category": "Asset Management", 
                    "subcategory": "Information Classification",
                    "automation_checks": ["data_classification_scan", "label_verification"],
                    "evidence": ["classification_policy", "data_inventory"]
                },
                "A.9.1.1": {
                    "title": "Access control policy",
                    "category": "Access Control",
                    "subcategory": "Business Requirements",
                    "automation_checks": ["policy_compliance", "access_review"],
                    "evidence": ["access_policy", "review_records"]
                },
                "A.12.6.1": {
                    "title": "Management of technical vulnerabilities",
                    "category": "Systems Acquisition",
                    "subcategory": "Technical Vulnerability Management", 
                    "automation_checks": ["vulnerability_scan", "patch_verification"],
                    "evidence": ["scan_reports", "patch_logs"]
                },
                "A.13.1.1": {
                    "title": "Network controls",
                    "category": "Communications Security",
                    "subcategory": "Network Security Management",
                    "automation_checks": ["network_segmentation", "firewall_rules"],
                    "evidence": ["network_diagrams", "firewall_configs"]
                }
            }
        }
    
    def _load_enforcement_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load runtime policy enforcement rules"""
        return {
            "SECRET_DETECTION": {
                "rule": "No hardcoded secrets in code",
                "severity": PolicySeverity.CRITICAL,
                "frameworks": [ComplianceFramework.PCI_DSS, ComplianceFramework.SOX],
                "enforcement": "block_merge",
                "remediation": "Remove secrets and use secure credential management"
            },
            "VULNERABILITY_THRESHOLD": {
                "rule": "No critical vulnerabilities in production code",
                "severity": PolicySeverity.HIGH,
                "frameworks": [ComplianceFramework.NIST_CSF, ComplianceFramework.ISO_27001],
                "enforcement": "require_approval",
                "remediation": "Fix critical vulnerabilities before deployment"
            },
            "LICENSE_COMPLIANCE": {
                "rule": "All dependencies must have approved licenses",
                "severity": PolicySeverity.MEDIUM,
                "frameworks": [ComplianceFramework.SOX, ComplianceFramework.GDPR],
                "enforcement": "warn",
                "remediation": "Review and approve dependency licenses"
            },
            "DATA_CLASSIFICATION": {
                "rule": "Sensitive data must be properly classified",
                "severity": PolicySeverity.HIGH,
                "frameworks": [ComplianceFramework.GDPR, ComplianceFramework.HIPAA],
                "enforcement": "require_review",
                "remediation": "Add proper data classification labels"
            }
        }
    
    async def log_audit_event(self, event: AuditEvent) -> bool:
        """Log audit trail event"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.execute("""
                INSERT INTO audit_events (
                    event_id, event_type, user_id, user_email, action, resource,
                    timestamp, source_ip, user_agent, details, compliance_frameworks,
                    risk_score, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type,
                    event.user_id,
                    event.user_email,
                    event.action,
                    event.resource,
                    event.timestamp.isoformat(),
                    event.source_ip,
                    event.user_agent,
                    json.dumps(event.details),
                    json.dumps(event.compliance_frameworks),
                    event.risk_score,
                    event.session_id
                ))
                conn.commit()
            
            logger.info(f"Audit event logged: {event.event_type} by {event.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    async def enforce_policy(self, repository: str, commit_hash: str, 
                           author: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runtime policy enforcement in CI/CD"""
        try:
            enforcement_result = {
                "allow_merge": True,
                "violations": [],
                "warnings": [],
                "required_approvals": [],
                "blocked_reasons": []
            }
            
            for finding in findings:
                # Check against enforcement rules
                for rule_id, rule in self.enforcement_rules.items():
                    if self._matches_rule(finding, rule):
                        violation = PolicyViolation(
                            violation_id=str(uuid.uuid4()),
                            policy_id=rule_id,
                            severity=rule["severity"],
                            title=f"Policy Violation: {rule['rule']}",
                            description=finding.get("description", ""),
                            violated_rule=rule["rule"],
                            repository=repository,
                            file_path=finding.get("file_path", ""),
                            line_number=finding.get("line_number"),
                            commit_hash=commit_hash,
                            author=author,
                            detected_at=datetime.now(timezone.utc),
                            evidence=finding,
                            remediation_guidance=rule["remediation"]
                        )
                        
                        # Store violation
                        await self._store_violation(violation)
                        
                        # Apply enforcement action
                        if rule["enforcement"] == "block_merge":
                            enforcement_result["allow_merge"] = False
                            enforcement_result["blocked_reasons"].append(violation.title)
                        elif rule["enforcement"] == "require_approval":
                            enforcement_result["required_approvals"].append({
                                "violation_id": violation.violation_id,
                                "approver_role": "security_team",
                                "reason": violation.title
                            })
                        elif rule["enforcement"] == "warn":
                            enforcement_result["warnings"].append(violation.title)
                        
                        enforcement_result["violations"].append({
                            "id": violation.violation_id,
                            "severity": violation.severity.value,
                            "title": violation.title,
                            "remediation": violation.remediation_guidance
                        })
            
            # Log enforcement action
            await self.log_audit_event(AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type="policy_enforcement",
                user_id=author,
                user_email=f"{author}@company.com",
                action="commit_policy_check",
                resource=f"{repository}:{commit_hash}",
                timestamp=datetime.now(timezone.utc),
                details={
                    "violations_count": len(enforcement_result["violations"]),
                    "allow_merge": enforcement_result["allow_merge"],
                    "findings_processed": len(findings)
                },
                compliance_frameworks=[f.value for f in ComplianceFramework],
                risk_score=self._calculate_risk_score(enforcement_result["violations"])
            ))
            
            return enforcement_result
            
        except Exception as e:
            logger.error(f"Failed to enforce policy: {e}")
            return {"allow_merge": False, "error": str(e)}
    
    def _matches_rule(self, finding: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if finding matches enforcement rule"""
        finding_type = finding.get("type", "").lower()
        rule_type = rule.get("rule", "").lower()
        
        # Pattern matching for different rule types
        if "secret" in rule_type and "secret" in finding_type:
            return True
        elif "vulnerability" in rule_type and finding.get("severity") == "CRITICAL":
            return True
        elif "license" in rule_type and "license" in finding_type:
            return True
        elif "data" in rule_type and "sensitive" in finding.get("description", "").lower():
            return True
        
        return False
    
    async def _store_violation(self, violation: PolicyViolation):
        """Store policy violation in database"""
        try:
            with sqlite3.connect(self.compliance_db_path) as conn:
                conn.execute("""
                INSERT INTO policy_violations (
                    violation_id, policy_id, severity, title, description,
                    violated_rule, repository, file_path, line_number,
                    commit_hash, author, detected_at, evidence,
                    remediation_guidance, status, assigned_to,
                    resolved_at, resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    violation.violation_id,
                    violation.policy_id,
                    violation.severity.value,
                    violation.title,
                    violation.description,
                    violation.violated_rule,
                    violation.repository,
                    violation.file_path,
                    violation.line_number,
                    violation.commit_hash,
                    violation.author,
                    violation.detected_at.isoformat(),
                    json.dumps(violation.evidence),
                    violation.remediation_guidance,
                    violation.status,
                    violation.assigned_to,
                    violation.resolved_at.isoformat() if violation.resolved_at else None,
                    violation.resolution_notes
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store violation: {e}")
            raise
    
    def _calculate_risk_score(self, violations: List[Dict[str, Any]]) -> float:
        """Calculate risk score based on violations"""
        if not violations:
            return 0.0
        
        severity_weights = {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 2.0,
            "info": 1.0
        }
        
        total_score = sum(severity_weights.get(v.get("severity", "low"), 1.0) for v in violations)
        return min(total_score / len(violations), 10.0)
    
    async def create_incident(self, violation_ids: List[str], title: str, 
                            assigned_team: str, reporter: str) -> str:
        """Create incident response workflow"""
        try:
            incident = IncidentResponse(
                incident_id=str(uuid.uuid4()),
                title=title,
                description=f"Security incident created from {len(violation_ids)} violations",
                severity=PolicySeverity.HIGH,  # Default, can be adjusted
                status=IncidentStatus.OPEN,
                assigned_team=assigned_team,
                reporter=reporter,
                detected_at=datetime.now(timezone.utc),
                source_findings=violation_ids,
                timeline=[{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "incident_created",
                    "user": reporter,
                    "notes": "Initial incident creation"
                }]
            )
            
            # Store incident
            with sqlite3.connect(self.incidents_db_path) as conn:
                conn.execute("""
                INSERT INTO incidents (
                    incident_id, title, description, severity, status,
                    assigned_team, reporter, detected_at, source_findings,
                    affected_systems, containment_actions, timeline,
                    external_tickets, evidence_collected, lessons_learned,
                    closed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident.incident_id,
                    incident.title,
                    incident.description,
                    incident.severity.value,
                    incident.status.value,
                    incident.assigned_team,
                    incident.reporter,
                    incident.detected_at.isoformat(),
                    json.dumps(incident.source_findings),
                    json.dumps(incident.affected_systems),
                    json.dumps(incident.containment_actions),
                    json.dumps(incident.timeline),
                    json.dumps(incident.external_tickets),
                    json.dumps(incident.evidence_collected),
                    incident.lessons_learned,
                    None
                ))
                conn.commit()
            
            # Log incident creation
            await self.log_audit_event(AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type="incident_response",
                user_id=reporter,
                user_email=f"{reporter}@company.com",
                action="incident_created",
                resource=f"incident:{incident.incident_id}",
                timestamp=datetime.now(timezone.utc),
                details={
                    "incident_id": incident.incident_id,
                    "violation_count": len(violation_ids),
                    "assigned_team": assigned_team
                },
                risk_score=8.0  # High risk for new incidents
            ))
            
            return incident.incident_id
            
        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            raise
    
    async def link_external_ticket(self, incident_id: str, 
                                 ticket_system: str, ticket_id: str) -> bool:
        """Link incident to external systems (Jira, SOAR, etc.)"""
        try:
            with sqlite3.connect(self.incidents_db_path) as conn:
                # Get current external tickets
                cursor = conn.execute(
                    "SELECT external_tickets FROM incidents WHERE incident_id = ?",
                    (incident_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    external_tickets = json.loads(row[0]) if row[0] else {}
                    external_tickets[ticket_system] = ticket_id
                    
                    # Update incident
                    conn.execute("""
                    UPDATE incidents 
                    SET external_tickets = ? 
                    WHERE incident_id = ?
                    """, (json.dumps(external_tickets), incident_id))
                    conn.commit()
                    
                    logger.info(f"Linked incident {incident_id} to {ticket_system}:{ticket_id}")
                    return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to link external ticket: {e}")
            return False
    
    async def get_compliance_status(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Get compliance status for specific framework"""
        try:
            status = {
                "framework": framework.value,
                "total_controls": 0,
                "implemented_controls": 0,
                "compliance_percentage": 0.0,
                "critical_gaps": [],
                "recommendations": []
            }
            
            # Get controls for framework
            framework_controls = self.control_mappings.get(f"{framework.name}_CONTROLS", {})
            status["total_controls"] = len(framework_controls)
            
            # Calculate implementation status (simplified)
            # In real implementation, this would check actual control implementation
            implemented = 0
            for control_id, control_data in framework_controls.items():
                # Mock implementation check
                if len(control_data.get("automation_checks", [])) > 0:
                    implemented += 1
            
            status["implemented_controls"] = implemented
            status["compliance_percentage"] = (implemented / len(framework_controls)) * 100 if framework_controls else 0
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return {"error": str(e)}
    
    async def generate_audit_report(self, start_date: datetime, 
                                  end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        try:
            report = {
                "report_id": str(uuid.uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {},
                "events": [],
                "violations": [],
                "incidents": []
            }
            
            # Get audit events for period
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.execute("""
                SELECT * FROM audit_events 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                """, (start_date.isoformat(), end_date.isoformat()))
                
                events = cursor.fetchall()
                report["events"] = [dict(zip([d[0] for d in cursor.description], row)) 
                                 for row in events]
            
            # Get violations for period
            with sqlite3.connect(self.compliance_db_path) as conn:
                cursor = conn.execute("""
                SELECT * FROM policy_violations 
                WHERE detected_at BETWEEN ? AND ?
                ORDER BY detected_at DESC
                """, (start_date.isoformat(), end_date.isoformat()))
                
                violations = cursor.fetchall()
                report["violations"] = [dict(zip([d[0] for d in cursor.description], row)) 
                                      for row in violations]
            
            # Generate summary
            report["summary"] = {
                "total_events": len(report["events"]),
                "total_violations": len(report["violations"]),
                "critical_violations": len([v for v in report["violations"] 
                                          if v["severity"] == "critical"]),
                "unique_users": len(set(e["user_id"] for e in report["events"])),
                "high_risk_events": len([e for e in report["events"] 
                                       if json.loads(e.get("details", "{}")).get("risk_score", 0) > 7])
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            return {"error": str(e)}

# Export main classes
__all__ = [
    'ComplianceGovernanceEngine', 'ComplianceControl', 'PolicyViolation', 
    'AuditEvent', 'IncidentResponse', 'ComplianceFramework', 'PolicySeverity',
    'IncidentStatus'
]
