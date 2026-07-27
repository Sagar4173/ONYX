"""
Models package for ONYX Platform
================================

All shared enums and base models are defined in models.base.
Other modules should import from there for consistency.
"""

# Base enums and models (SINGLE SOURCE OF TRUTH)
from .base import (
    # Anomaly Detection Enums
    AnomalyType,
    AssetType,
    AttackVector,
    # Base Models
    BusinessImpact,
    # Compliance Enums
    ComplianceFramework,
    ComplianceMapping,
    ComplianceStatus,
    CVSSScore,
    EnforcementMode,
    ExposureLevel,
    # Incident Response Enums
    IncidentStatus,
    # Metric Enums
    MetricType,
    # Pentest Enums
    PentestType,
    PolicySeverity,
    PolicyStatus,
    # Policy Engine Enums
    PolicyType,
    ProjectCategory,
    ProjectPriority,
    # Project Enums
    ProjectStatus,
    RiskLevel,
    # Rule Engine Enums
    RuleFormat,
    RuleStatus,
    # Scanner Enums
    ScannerType,
    ScanSeverity,
    ScanStatus,
    ScanType,
    Severity,
    SeverityLevel,
    TestStatus,
    ThreatAnalysis,
    # Threat Enums
    ThreatCategory,
    ThreatIndicator,
    # Threat Intelligence Enums
    ThreatSeverity,
    ThreatSource,
    ThreatType,
    TrendDirection,
    # Trend Analytics Enums
    TrendPeriod,
    # User Enums
    UserRole,
    UserStatus,
    ValidationSeverity,
    ViolationAction,
    VulnerabilityPriority,
    # Vulnerability Management Enums
    VulnerabilityStatus,
    # Helper
    utc_now,
)

# Project models
from .project import Project

# Report models
from .report import (
    AIAnalysis,
    GitMetadata,
    NotificationStatus,
    ScannerHealth,
    ScanReport,
    ScanResult,
    VulnerabilityFinding,
    WebhookEvent,
)

# User models
from .user import APIToken, User, UserSession

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
