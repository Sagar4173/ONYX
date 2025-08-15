"""
MongoDB models for SecureDevOps Platform
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from beanie import Document
from bson import ObjectId


class ScanStatus(str, Enum):
    """Scan status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    NIST_CSF = "nist_csf"
    ISO_27001 = "iso_27001"
    OWASP_TOP_10 = "owasp_top_10"
    CIS_CONTROLS = "cis_controls"


class ThreatCategory(str, Enum):
    """Threat categorization types"""
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    DATA_EXPOSURE = "data_exposure"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    CODE_QUALITY = "code_quality"
    SECRETS = "secrets"
    MALWARE = "malware"
    NETWORK = "network"
    INFRASTRUCTURE = "infrastructure"


class RiskLevel(str, Enum):
    """Business risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class BusinessImpact(BaseModel):
    """Business impact assessment"""
    confidentiality_impact: str = Field(..., description="Impact on data confidentiality")
    integrity_impact: str = Field(..., description="Impact on data integrity")
    availability_impact: str = Field(..., description="Impact on system availability")
    business_criticality: str = Field(..., description="Business criticality of the asset")
    compliance_risk: str = Field(..., description="Regulatory compliance risk")
    financial_impact: str = Field(..., description="Potential financial impact")


class CVSSScore(BaseModel):
    """CVSS scoring information"""
    version: str = Field(default="3.1", description="CVSS version")
    base_score: float = Field(..., description="CVSS base score (0-10)")
    temporal_score: Optional[float] = Field(None, description="CVSS temporal score")
    environmental_score: Optional[float] = Field(None, description="CVSS environmental score")
    vector_string: Optional[str] = Field(None, description="CVSS vector string")
    attack_vector: Optional[str] = Field(None, description="Attack vector")
    attack_complexity: Optional[str] = Field(None, description="Attack complexity")
    privileges_required: Optional[str] = Field(None, description="Privileges required")
    user_interaction: Optional[str] = Field(None, description="User interaction required")
    scope: Optional[str] = Field(None, description="Scope of impact")
    confidentiality_impact: Optional[str] = Field(None, description="Confidentiality impact")
    integrity_impact: Optional[str] = Field(None, description="Integrity impact")
    availability_impact: Optional[str] = Field(None, description="Availability impact")


class ComplianceMapping(BaseModel):
    """Compliance framework mapping"""
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    control_id: str = Field(..., description="Control ID within the framework")
    control_title: str = Field(..., description="Control title")
    control_description: str = Field(..., description="Control description")
    severity: SeverityLevel = Field(..., description="Compliance violation severity")
    requirement_category: str = Field(..., description="Category of requirement")


class ThreatAnalysis(BaseModel):
    """Comprehensive threat analysis"""
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    cve_id: Optional[str] = Field(None, description="CVE identifier")
    threat_categories: List[ThreatCategory] = Field(default_factory=list, description="Threat categories")
    attack_patterns: List[str] = Field(default_factory=list, description="CAPEC attack patterns")
    exploitability: str = Field(..., description="Exploitability assessment")
    impact_assessment: str = Field(..., description="Impact assessment")
    mitigation_priority: str = Field(..., description="Mitigation priority")
    remediation_effort: str = Field(..., description="Estimated remediation effort")
    false_positive_likelihood: str = Field(default="low", description="False positive likelihood")


class ScannerType(str, Enum):
    """Supported scanner types"""
    SEMGREP = "semgrep"
    TRIVY = "trivy"
    GITLEAKS = "gitleaks"
    LYNIS = "lynis"
    BANDIT = "bandit"
    SAFETY = "safety"


class VulnerabilityFinding(BaseModel):
    """Enhanced individual vulnerability finding with compliance mapping and threat analysis"""
    id: str = Field(..., description="Unique finding identifier")
    scanner: ScannerType = Field(..., description="Scanner that found this vulnerability")
    rule_id: str = Field(..., description="Rule or check ID")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    severity: SeverityLevel = Field(..., description="Severity level")
    confidence: Optional[str] = Field(None, description="Confidence level")
    file_path: str = Field(..., description="Relative path to affected file")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    column_start: Optional[int] = Field(None, description="Starting column")
    column_end: Optional[int] = Field(None, description="Ending column")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    cve_id: Optional[str] = Field(None, description="CVE identifier")
    owasp_category: Optional[str] = Field(None, description="OWASP Top 10 category")
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Enhanced fields for compliance and threat analysis
    compliance_mappings: List[ComplianceMapping] = Field(
        default_factory=list, 
        description="Compliance framework mappings"
    )
    threat_analysis: Optional[ThreatAnalysis] = Field(
        None, 
        description="Comprehensive threat analysis"
    )
    cvss_score: Optional[CVSSScore] = Field(
        None, 
        description="CVSS scoring information"
    )
    business_impact: Optional[BusinessImpact] = Field(
        None, 
        description="Business impact assessment"
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM, 
        description="Calculated business risk level"
    )
    tags: List[str] = Field(
        default_factory=list, 
        description="Categorization tags (injection, crypto, auth, etc.)"
    )
    remediation_priority: Optional[str] = Field(
        None, 
        description="Calculated remediation priority"
    )
    exploitability_score: Optional[float] = Field(
        None, 
        description="Exploitability score (0-10)"
    )
    false_positive_score: Optional[float] = Field(
        None, 
        description="False positive likelihood score (0-1)"
    )


class ScanResult(BaseModel):
    """Results from a specific scanner"""
    scanner: ScannerType = Field(..., description="Scanner type")
    status: ScanStatus = Field(..., description="Scan status")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Scan duration")
    findings: List[VulnerabilityFinding] = Field(default_factory=list)
    error_message: Optional[str] = Field(None, description="Error message if failed")
    raw_output: Optional[str] = Field(None, description="Raw scanner output")
    summary: Dict[str, int] = Field(
        default_factory=lambda: {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "total": 0
        }
    )


class AIAnalysis(BaseModel):
    """AI-generated analysis and recommendations"""
    model_used: str = Field(..., description="AI model used for analysis")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executive_summary: str = Field(..., description="Executive summary of findings")
    risk_assessment: str = Field(..., description="Overall risk assessment")
    priority_findings: List[str] = Field(default_factory=list, description="Priority vulnerabilities")
    recommendations: List[str] = Field(default_factory=list, description="Remediation recommendations")
    secure_code_examples: Dict[str, str] = Field(
        default_factory=dict, 
        description="Secure code examples for fixes"
    )
    compliance_impact: Dict[str, str] = Field(
        default_factory=dict,
        description="Impact on compliance frameworks"
    )
    estimated_fix_time: Optional[str] = Field(None, description="Estimated time to fix issues")
    raw_response: Optional[str] = Field(None, description="Raw AI response")


class GitMetadata(BaseModel):
    """Git repository metadata"""
    repository_url: str = Field(..., description="Repository URL")
    branch: str = Field(..., description="Branch name")
    commit_hash: str = Field(..., description="Commit SHA")
    commit_message: Optional[str] = Field(None, description="Commit message")
    commit_author: Optional[str] = Field(None, description="Commit author")
    commit_timestamp: Optional[datetime] = Field(None, description="Commit timestamp")
    pr_number: Optional[int] = Field(None, description="Pull request number")
    event_type: str = Field(..., description="Event type (push, pull_request, etc.)")


class NotificationStatus(BaseModel):
    """Notification delivery status"""
    slack_sent: bool = Field(default=False)
    slack_timestamp: Optional[datetime] = Field(None)
    teams_sent: bool = Field(default=False)
    teams_timestamp: Optional[datetime] = Field(None)
    email_sent: bool = Field(default=False)
    email_timestamp: Optional[datetime] = Field(None)
    errors: List[str] = Field(default_factory=list)


class ScanReport(Document):
    """Main scan report document"""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Identifiers
    project_name: str = Field(..., description="Project/repository name")
    scan_id: str = Field(..., description="Unique scan identifier")
    
    # Git information
    git_metadata: GitMetadata = Field(..., description="Git repository metadata")
    
    # Scan information
    status: ScanStatus = Field(default=ScanStatus.PENDING)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None)
    duration_seconds: Optional[float] = Field(None)
    
    # Scanner results
    scan_results: List[ScanResult] = Field(default_factory=list)
    
    # AI analysis
    ai_analysis: Optional[AIAnalysis] = Field(None)
    
    # Summary statistics
    total_findings: int = Field(default=0)
    findings_by_severity: Dict[str, int] = Field(
        default_factory=lambda: {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
    )
    
    # Notifications
    notifications: NotificationStatus = Field(default_factory=NotificationStatus)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "scan_reports"
        indexes = [
            "project_name",
            "git_metadata.repository_url",
            "git_metadata.branch",
            "git_metadata.commit_hash",
            "status",
            "created_at",
            [("project_name", 1), ("created_at", -1)],
            [("status", 1), ("created_at", -1)]
        ]

    def update_summary(self):
        """Update summary statistics from scan results"""
        total_findings = 0
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for scan_result in self.scan_results:
            for finding in scan_result.findings:
                total_findings += 1
                severity_counts[finding.severity.value] += 1
        
        self.total_findings = total_findings
        self.findings_by_severity = severity_counts
        self.updated_at = datetime.now(timezone.utc)


class WebhookEvent(Document):
    """Webhook event tracking"""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type")
    repository_url: str = Field(..., description="Repository URL")
    branch: Optional[str] = Field(None)
    commit_hash: Optional[str] = Field(None)
    pr_number: Optional[int] = Field(None)
    
    # Processing status
    status: str = Field(default="received")  # received, processing, completed, failed
    processed_at: Optional[datetime] = Field(None)
    scan_report_id: Optional[str] = Field(None)  # String reference instead of ObjectId
    
    # Raw webhook data
    headers: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Error tracking
    error_message: Optional[str] = Field(None)
    retry_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "webhook_events"
        indexes = [
            "event_id",
            "repository_url",
            "status",
            "created_at",
            [("repository_url", 1), ("created_at", -1)]
        ]


class ScannerHealth(Document):
    """Scanner health monitoring"""
    
    scanner: ScannerType = Field(..., description="Scanner type")
    version: Optional[str] = Field(None, description="Scanner version")
    last_check: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_available: bool = Field(default=False)
    response_time_ms: Optional[float] = Field(None)
    error_message: Optional[str] = Field(None)
    
    class Settings:
        name = "scanner_health"
        indexes = ["scanner", "last_check"]


# Export all models
__all__ = [
    "ScanStatus",
    "SeverityLevel", 
    "ScannerType",
    "VulnerabilityFinding",
    "ScanResult",
    "AIAnalysis",
    "GitMetadata",
    "NotificationStatus",
    "ScanReport",
    "WebhookEvent",
    "ScannerHealth"
]
