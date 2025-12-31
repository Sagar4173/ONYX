"""
Baseline Management Package
===========================

Services for tracking security baselines and detecting drift/regressions.

Components:
- BaselineScanningService: Core baseline scanning and comparison
- BaselineManager: Advanced baseline management with drift detection
"""

from .scanner import (
    BaselineScanningService,
    BaselineFingerprint,
    ScanBaseline,
    SecurityDrift,
    RegressionAlert,
    ChangeType,
    DriftSeverity,
    baseline_service,
)

from .manager import (
    BaselineManager,
    SecurityBaseline,
    SecurityFinding,
    BaselineDrift,
    BaselineStatus,
)

__all__ = [
    # Scanner
    "BaselineScanningService",
    "baseline_service",
    "BaselineFingerprint",
    "ScanBaseline",
    "SecurityDrift",
    "RegressionAlert",
    "ChangeType",
    "DriftSeverity",
    
    # Manager
    "BaselineManager",
    "SecurityBaseline",
    "SecurityFinding",
    "BaselineDrift",
    "BaselineStatus",
]
