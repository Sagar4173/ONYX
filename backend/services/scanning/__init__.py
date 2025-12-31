"""
Security Scanning Services
===========================

A modular, well-organized security scanning framework.

⚠️ IMPORTANT: Legacy modules in services/scanning/legacy/ are DEPRECATED
and will be removed in a future version. Do not use them for new code.

PACKAGE STRUCTURE:
==================

    services/scanning/
    ├── base/           # Core models, config, exceptions
    ├── scanners/       # Individual scanner implementations  
    ├── engine/         # Orchestration and workflow
    ├── baseline/       # Baseline tracking and drift detection
    ├── vulnerability/  # Vulnerability lifecycle management
    ├── pentest/        # Penetration testing automation
    ├── workflow/       # Enhanced scanning workflows
    ├── utils/          # SBOM, comparison utilities
    └── legacy/         # ⚠️ DEPRECATED - DO NOT USE (backward compat only)

RECOMMENDED USAGE:
==================

    # Models and configuration
    from services.scanning.base import Finding, ScanResult, Severity, ScanConfig
    
    # Individual scanners
    from services.scanning.scanners import (
        RealSecurityScanner,
        BanditScanner, SemgrepScanner, CodeQLScanner,  # SAST
        ZAPScanner, NucleiScanner,                      # DAST
        TrivyScanner, GitLeaksScanner, SafetyScanner,   # Container/Secrets/SCA
        CheckovScanner,                                  # IaC
    )
    
    # Orchestration
    from services.scanning.engine import ScanOrchestrator, ScanWorkflow
    
    # Baseline management
    from services.scanning.baseline import BaselineManager, BaselineScanningService
    
    # Vulnerability management
    from services.scanning.vulnerability import VulnerabilityManager

MIGRATION GUIDE:
================
If you're using legacy imports, please migrate to the recommended imports above.
Legacy modules will be removed in version 2.0.0.
"""

# ============================================================================
# BASE - Core models, configuration, exceptions
# ============================================================================
from .base import (
    # Models
    Finding,
    ScanFinding,
    ScanResult,
    ScanMetrics,
    ScanType,
    Severity,
    ScanSeverity,
    ScannerType,
    
    # Configuration
    ScanConfig,
    AdvancedScannerConfig,
    
    # Exceptions
    ScannerError,
    ScanTimeoutError,
    ScanConfigurationError,
)

# ============================================================================
# SCANNERS - Individual scanner implementations
# ============================================================================
from .scanners import (
    BaseScanner,
    RealSecurityScanner,
    ZAPScanner,
    NucleiScanner,
    CodeQLScanner,
    CheckovScanner,
    BanditScanner,
    SemgrepScanner,
    TrivyScanner,
    GitLeaksScanner,
    SafetyScanner,
)

# ============================================================================
# ENGINE - Orchestration and workflow
# ============================================================================
from .engine import (
    ScanOrchestrator,
    SuppressionEngine,
    ScanWorkflow,
)

# ============================================================================
# BASELINE - Baseline tracking and drift detection
# ============================================================================
from .baseline import (
    BaselineScanningService,
    BaselineFingerprint,
    ScanBaseline,
    SecurityDrift,
    RegressionAlert,
    BaselineManager,
    SecurityBaseline,
    SecurityFinding,
    BaselineDrift,
)

# ============================================================================
# VULNERABILITY - Vulnerability lifecycle management
# ============================================================================
from .vulnerability import (
    VulnerabilityManager,
    RiskMetrics,
    VulnerabilityStatus,
    VulnerabilityPriority,
)

# ============================================================================
# WORKFLOW - Enhanced scanning workflows
# ============================================================================
from .workflow import enhanced_workflow

# Note: Legacy imports removed - use new scanner architecture:
#   - ScanOrchestrator replaces AdvancedScannerEngine
#   - ZAPScanner replaces OWASPZAPScanner  
#   - RealSecurityScanner replaces AdvancedSecurityScanner


__all__ = [
    # ==================
    # BASE
    # ==================
    "Finding",
    "ScanFinding",
    "ScanResult",
    "ScanMetrics",
    "ScanType",
    "Severity",
    "ScanSeverity",
    "ScannerType",
    "ScanConfig",
    "AdvancedScannerConfig",
    "ScannerError",
    "ScanTimeoutError",
    "ScanConfigurationError",
    
    # ==================
    # SCANNERS
    # ==================
    "BaseScanner",
    "RealSecurityScanner",
    "ZAPScanner",
    "NucleiScanner",
    "CodeQLScanner",
    "CheckovScanner",
    "BanditScanner",
    "SemgrepScanner",
    "TrivyScanner",
    "GitLeaksScanner",
    "SafetyScanner",
    
    # ==================
    # ENGINE
    # ==================
    "ScanOrchestrator",
    "SuppressionEngine",
    "ScanWorkflow",
    
    # ==================
    # BASELINE
    # ==================
    "BaselineScanningService",
    "BaselineFingerprint",
    "ScanBaseline",
    "SecurityDrift",
    "RegressionAlert",
    "BaselineManager",
    "SecurityBaseline",
    "SecurityFinding",
    "BaselineDrift",
    
    # ==================
    # VULNERABILITY
    # ==================
    "VulnerabilityManager",
    "RiskMetrics",
    "VulnerabilityStatus",
    "VulnerabilityPriority",
    
    # ==================
    # WORKFLOW
    # ==================
    "enhanced_workflow",
]
