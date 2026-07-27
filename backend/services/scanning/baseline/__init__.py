"""
Baseline Management Package
===========================

Services for tracking security baselines and detecting drift/regressions.

Components:
- BaselineScanningService: Core baseline scanning and comparison
- BaselineManager: Advanced baseline management with drift detection
"""

from .manager import (
    BaselineDrift,
    BaselineManager,
    BaselineStatus,
    SecurityBaseline,
    SecurityFinding,
)
from .scanner import (
    BaselineFingerprint,
    BaselineScanningService,
    ChangeType,
    DriftSeverity,
    RegressionAlert,
    ScanBaseline,
    SecurityDrift,
    baseline_service,
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
