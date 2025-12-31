"""
Models package for ONYX Platform
================================

All shared enums and base models are defined in models.base.
Other modules should import from there for consistency.
"""

# Base enums and models (SINGLE SOURCE OF TRUTH)
from .base import (
    # Helper
    utc_now,
    # Scanner Enums
    ScannerType,
    SeverityLevel,
    Severity,
    ScanSeverity,
    ScanStatus,
    ScanType,
    # Compliance Enums
    ComplianceFramework,
    ComplianceStatus,
    # Trend Analytics Enums
    TrendPeriod,
    TrendDirection,
    # Vulnerability Management Enums
    VulnerabilityStatus,
    VulnerabilityPriority,
    ExposureLevel,
    AssetType,
    # Policy Engine Enums
    PolicyType,
    EnforcementMode,
    PolicyStatus,
    ViolationAction,
    # Anomaly Detection Enums
    AnomalyType,
    ThreatIndicator,
    # Pentest Enums
    PentestType,
    AttackVector,
    TestStatus,
    # Rule Engine Enums
    RuleFormat,
    ValidationSeverity,
    RuleStatus,
    # Metric Enums
    MetricType,
    # Threat Intelligence Enums
    ThreatSeverity,
    ThreatType,
    ThreatSource,
    # Incident Response Enums
    IncidentStatus,
    PolicySeverity,
    # Threat Enums
    ThreatCategory,
    RiskLevel,
    # User Enums
    UserRole,
    UserStatus,
    # Project Enums
    ProjectStatus,
    ProjectCategory,
    ProjectPriority,
    # Base Models
    BusinessImpact,
    CVSSScore,
    ComplianceMapping,
    ThreatAnalysis,
)

# Report models
from .report import (
    VulnerabilityFinding,
    ScanResult,
    AIAnalysis,
    GitMetadata,
    NotificationStatus,
    ScanReport,
    WebhookEvent,
    ScannerHealth,
)

# User models
from .user import User, UserSession, APIToken

# Project models
from .project import Project

__all__ = [
    # Helper
    "utc_now",
    
    # Base Enums
    "ScannerType",
    "SeverityLevel",
    "Severity",
    "ScanSeverity",
    "ScanStatus",
    "ScanType",
    "ComplianceFramework",
    "ComplianceStatus",
    # Trend Analytics
    "TrendPeriod",
    "TrendDirection",
    # Vulnerability Management
    "VulnerabilityStatus",
    "VulnerabilityPriority",
    "ExposureLevel",
    "AssetType",
    # Policy Engine
    "PolicyType",
    "EnforcementMode",
    "PolicyStatus",
    "ViolationAction",
    # Anomaly Detection
    "AnomalyType",
    "ThreatIndicator",
    # Pentest
    "PentestType",
    "AttackVector",
    "TestStatus",
    # Rule Engine
    "RuleFormat",
    "ValidationSeverity",
    "RuleStatus",
    # Metrics
    "MetricType",
    # Threat Intelligence
    "ThreatSeverity",
    "ThreatType",
    "ThreatSource",
    # Incident Response
    "IncidentStatus",
    "PolicySeverity",
    # Threat
    "ThreatCategory",
    "RiskLevel",
    "UserRole",
    "UserStatus",
    "ProjectStatus",
    "ProjectCategory",
    "ProjectPriority",
    
    # Base Models
    "BusinessImpact",
    "CVSSScore",
    "ComplianceMapping",
    "ThreatAnalysis",
    
    # Report models
    "VulnerabilityFinding",
    "ScanResult",
    "AIAnalysis",
    "GitMetadata",
    "NotificationStatus",
    "ScanReport",
    "WebhookEvent",
    "ScannerHealth",
    
    # User models
    "User",
    "UserSession",
    "APIToken",
    
    # Project models
    "Project",
]
