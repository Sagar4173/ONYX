"""
Base Models and Enums for ONYX Platform
========================================

This is the SINGLE SOURCE OF TRUTH for all shared enums and base models.
All other files should import from here to avoid duplication.

Usage:
    from models.base import (
        ScannerType, SeverityLevel, ScanStatus, ComplianceFramework,
        ThreatCategory, RiskLevel, ScanType
    )
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# Import from central utility - re-export for backward compatibility
from utils.datetime_utils import utc_now


# =============================================================================
# Scanner Enums
# =============================================================================

class ScannerType(str, Enum):
    """
    Supported security scanner types.
    
    Categories:
    - SAST: Static Application Security Testing
    - DAST: Dynamic Application Security Testing  
    - SCA: Software Composition Analysis
    - IaC: Infrastructure as Code
    - Secrets: Secret Detection
    """
    # SAST Scanners
    SEMGREP = "semgrep"
    BANDIT = "bandit"
    CODEQL = "codeql"
    
    # DAST Scanners
    OWASP_ZAP = "owasp_zap"
    NUCLEI = "nuclei"
    
    # Container/Artifact Scanning
    TRIVY = "trivy"
    
    # SCA (Dependency) Scanners
    SAFETY = "safety"
    
    # IaC Scanners
    CHECKOV = "checkov"
    
    # Secret Detection
    GITLEAKS = "gitleaks"
    DETECT_SECRETS = "detect_secrets"
    
    # Infrastructure Scanners
    LYNIS = "lynis"


class SeverityLevel(str, Enum):
    """
    Vulnerability severity levels.
    Follows industry standard CVSS-based naming.
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Alias for backward compatibility
Severity = SeverityLevel
ScanSeverity = SeverityLevel


class ScanStatus(str, Enum):
    """Status of a scan operation."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ScanType(str, Enum):
    """Types of security scans."""
    SAST = "sast"               # Static Application Security Testing
    DAST = "dast"               # Dynamic Application Security Testing
    IAC = "iac"                 # Infrastructure as Code
    SECRETS = "secrets"         # Secret Detection
    SCA = "sca"                 # Software Composition Analysis
    DEPENDENCIES = "dependencies"  # Alias for SCA
    PENTEST = "pentest"         # Penetration Testing
    CONTAINER = "container"     # Container Scanning
    COMPREHENSIVE = "comprehensive"  # All scan types


# =============================================================================
# Compliance Enums
# =============================================================================

class ComplianceFramework(str, Enum):
    """
    Supported compliance frameworks.
    Used across compliance_analyzer, governance_engine, and advanced_compliance.
    """
    # Financial & Audit
    SOX = "sox"                 # Sarbanes-Oxley Act
    SOC2 = "soc2"               # Service Organization Control 2
    PCI_DSS = "pci_dss"         # Payment Card Industry Data Security Standard
    
    # Healthcare
    HIPAA = "hipaa"             # Health Insurance Portability and Accountability Act
    
    # Privacy
    GDPR = "gdpr"               # General Data Protection Regulation
    
    # Security Frameworks
    ISO_27001 = "iso_27001"     # Information Security Management
    NIST = "nist"               # National Institute of Standards and Technology
    NIST_CSF = "nist_csf"       # NIST Cybersecurity Framework
    CIS = "cis"                 # Center for Internet Security
    CIS_CONTROLS = "cis_controls"  # CIS Critical Security Controls
    
    # Application Security
    OWASP = "owasp"             # Open Web Application Security Project
    OWASP_TOP_10 = "owasp_top_10"  # OWASP Top 10
    
    # Custom
    CUSTOM = "custom"           # Custom compliance framework


class ComplianceStatus(str, Enum):
    """Compliance assessment status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    UNDER_REVIEW = "under_review"


# =============================================================================
# Trend Analytics Enums
# =============================================================================

class TrendPeriod(str, Enum):
    """Time periods for trend analysis."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    UNKNOWN = "unknown"


# =============================================================================
# Vulnerability Management Enums
# =============================================================================

class VulnerabilityStatus(str, Enum):
    """Vulnerability lifecycle status."""
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"


class VulnerabilityPriority(str, Enum):
    """Vulnerability priority levels."""
    IMMEDIATE = "immediate"    # Fix within 24 hours
    HIGH = "high"             # Fix within 7 days
    MEDIUM = "medium"         # Fix within 30 days
    LOW = "low"              # Fix within 90 days
    INFORMATIONAL = "info"    # No immediate action required


class ExposureLevel(str, Enum):
    """Service exposure levels."""
    INTERNET_FACING = "internet_facing"
    INTERNAL_NETWORK = "internal_network"
    ISOLATED = "isolated"
    UNKNOWN = "unknown"


class AssetType(str, Enum):
    """Asset type classification."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DATABASE = "database"
    CONTAINER = "container"
    INFRASTRUCTURE = "infrastructure"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    IOT_DEVICE = "iot_device"


# =============================================================================
# Policy Engine Enums
# =============================================================================

class PolicyType(str, Enum):
    """Types of security policies."""
    VULNERABILITY_THRESHOLD = "vulnerability_threshold"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    CODE_QUALITY_GATE = "code_quality_gate"
    SECRET_DETECTION = "secret_detection"
    DEPENDENCY_POLICY = "dependency_policy"
    CUSTOM_RULE = "custom_rule"


class EnforcementMode(str, Enum):
    """Policy enforcement modes."""
    ENFORCE = "enforce"       # Block merges on violation
    WARN = "warn"            # Allow merge with warnings
    CANARY = "canary"        # Test mode, collect data only
    DISABLED = "disabled"    # Policy disabled


class PolicyStatus(str, Enum):
    """Policy lifecycle status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class ViolationAction(str, Enum):
    """Actions to take on policy violation."""
    BLOCK_MERGE = "block_merge"
    REQUIRE_APPROVAL = "require_approval"
    SEND_NOTIFICATION = "send_notification"
    CREATE_ISSUE = "create_issue"
    LOG_ONLY = "log_only"


# =============================================================================
# Anomaly Detection Enums
# =============================================================================

class AnomalyType(str, Enum):
    """Types of security anomalies."""
    COMMIT_SIZE = "commit_size"
    SECRET_DENSITY = "secret_density"
    UNUSUAL_PATTERNS = "unusual_patterns"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    CONTENT = "content"


class ThreatIndicator(str, Enum):
    """Threat indicators for hunting."""
    SUSPICIOUS_PATTERNS = "suspicious_patterns"
    MALICIOUS_DOMAINS = "malicious_domains"
    KNOWN_EXPLOITS = "known_exploits"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    BACKDOOR_SIGNATURES = "backdoor_signatures"


# =============================================================================
# Pentest Enums
# =============================================================================

class PentestType(str, Enum):
    """Types of penetration tests."""
    AUTOMATED = "automated"
    MANUAL = "manual"
    RED_TEAM = "red_team"
    BLUE_TEAM = "blue_team"
    PURPLE_TEAM = "purple_team"
    BUG_BOUNTY = "bug_bounty"


class AttackVector(str, Enum):
    """Attack vectors for testing."""
    NETWORK = "network"
    WEB_APPLICATION = "web_application"
    SOCIAL_ENGINEERING = "social_engineering"
    PHYSICAL = "physical"
    WIRELESS = "wireless"
    CLOUD = "cloud"


class TestStatus(str, Enum):
    """Test/scan execution status."""
    SCHEDULED = "scheduled"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


# =============================================================================
# Rule Engine Enums
# =============================================================================

class RuleFormat(str, Enum):
    """Supported rule formats."""
    SEMGREP = "semgrep"
    REGEX = "regex" 
    CODEQL = "codeql"
    CUSTOM = "custom"


class ValidationSeverity(str, Enum):
    """Validation issue severity."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleStatus(str, Enum):
    """Rule lifecycle status."""
    DRAFT = "draft"
    TESTING = "testing"
    APPROVED = "approved"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


# =============================================================================
# Metric Enums
# =============================================================================

class MetricType(str, Enum):
    """Types of security metrics."""
    VULNERABILITY = "vulnerability"
    COMPLIANCE = "compliance"
    THREAT = "threat"
    POSTURE = "posture"
    PERFORMANCE = "performance"


# =============================================================================
# Threat Intelligence Enums
# =============================================================================

class ThreatSeverity(str, Enum):
    """Threat severity levels (alias for SeverityLevel)."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatType(str, Enum):
    """Types of threats."""
    CVE = "cve"
    ZERO_DAY = "zero_day"
    MALWARE = "malware"
    APT = "apt"
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    SUPPLY_CHAIN = "supply_chain"


class ThreatSource(str, Enum):
    """Threat intelligence sources."""
    NVD = "nvd"
    OSV = "osv"
    CISA_KEV = "cisa_kev"
    MITRE = "mitre"
    GITHUB_ADVISORY = "github_advisory"
    CUSTOM = "custom"
    MANUAL = "manual"
    AUTOMATED = "automated"


# =============================================================================
# Incident Response Enums
# =============================================================================

class IncidentStatus(str, Enum):
    """Incident response status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    LESSONS_LEARNED = "lessons_learned"
    CLOSED = "closed"


class PolicySeverity(str, Enum):
    """Policy violation severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# =============================================================================
# Threat Enums
# =============================================================================

class ThreatCategory(str, Enum):
    """Threat categorization types based on OWASP and MITRE."""
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
    """Business risk levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


# =============================================================================
# User/Auth Enums
# =============================================================================

class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    SECURITY_MANAGER = "security_manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# =============================================================================
# Project Enums
# =============================================================================

class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectCategory(str, Enum):
    """Project category enumeration."""
    WEB_APPLICATION = "web_application"
    MOBILE_APPLICATION = "mobile_application"
    API_SERVICE = "api_service"
    INFRASTRUCTURE = "infrastructure"
    MICROSERVICE = "microservice"
    LIBRARY = "library"
    OTHER = "other"


class ProjectPriority(str, Enum):
    """Project priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Base Pydantic Models (shared across modules)
# =============================================================================

class BusinessImpact(BaseModel):
    """Business impact assessment."""
    confidentiality_impact: str = Field(..., description="Impact on data confidentiality")
    integrity_impact: str = Field(..., description="Impact on data integrity")
    availability_impact: str = Field(..., description="Impact on system availability")
    business_criticality: str = Field(..., description="Business criticality of the asset")
    compliance_risk: str = Field(..., description="Regulatory compliance risk")
    financial_impact: str = Field(..., description="Potential financial impact")


class CVSSScore(BaseModel):
    """CVSS scoring information."""
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
    """Compliance framework mapping for findings."""
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    control_id: str = Field(..., description="Control ID within the framework")
    control_title: str = Field(..., description="Control title")
    control_description: str = Field(..., description="Control description")
    severity: SeverityLevel = Field(..., description="Compliance violation severity")
    requirement_category: str = Field(..., description="Category of requirement")


class ThreatAnalysis(BaseModel):
    """Comprehensive threat analysis."""
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    cve_id: Optional[str] = Field(None, description="CVE identifier")
    threat_categories: List[ThreatCategory] = Field(default_factory=list)
    attack_patterns: List[str] = Field(default_factory=list, description="CAPEC attack patterns")
    exploitability: str = Field(..., description="Exploitability assessment")
    impact_assessment: str = Field(..., description="Impact assessment")
    mitigation_priority: str = Field(..., description="Mitigation priority")
    remediation_effort: str = Field(..., description="Estimated remediation effort")
    false_positive_likelihood: str = Field(default="low", description="False positive likelihood")


# =============================================================================
# Export All
# =============================================================================

__all__ = [
    # Helper
    "utc_now",
    
    # Scanner Enums
    "ScannerType",
    "SeverityLevel",
    "Severity",
    "ScanSeverity",
    "ScanStatus",
    "ScanType",
    
    # Compliance Enums
    "ComplianceFramework",
    "ComplianceStatus",
    
    # Trend Analytics Enums
    "TrendPeriod",
    "TrendDirection",
    
    # Vulnerability Management Enums
    "VulnerabilityStatus",
    "VulnerabilityPriority",
    "ExposureLevel",
    "AssetType",
    
    # Policy Engine Enums
    "PolicyType",
    "EnforcementMode",
    "PolicyStatus",
    "ViolationAction",
    
    # Anomaly Detection Enums
    "AnomalyType",
    "ThreatIndicator",
    
    # Pentest Enums
    "PentestType",
    "AttackVector",
    "TestStatus",
    
    # Rule Engine Enums
    "RuleFormat",
    "ValidationSeverity",
    "RuleStatus",
    
    # Metric Enums
    "MetricType",
    
    # Threat Intelligence Enums
    "ThreatSeverity",
    "ThreatType",
    "ThreatSource",
    
    # Incident Response Enums
    "IncidentStatus",
    "PolicySeverity",
    
    # Threat Enums
    "ThreatCategory",
    "RiskLevel",
    
    # User Enums
    "UserRole",
    "UserStatus",
    
    # Project Enums
    "ProjectStatus",
    "ProjectCategory",
    "ProjectPriority",
    
    # Base Models
    "BusinessImpact",
    "CVSSScore",
    "ComplianceMapping",
    "ThreatAnalysis",
]
