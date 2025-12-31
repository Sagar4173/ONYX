"""
Base Models and Configuration for Security Scanning
====================================================

This module contains all the foundational Pydantic models, enums, and 
configuration classes used across the scanning subsystem.

Exports:
- Enums: ScannerType, ScanSeverity, ScanType, Severity
- Models: ScanFinding, ScanResult, Finding, ScanMetrics, ScanConfig, AdvancedScannerConfig
- Exceptions: ScannerError, ScanTimeoutError, ScanConfigurationError
"""

from .models import (
    # Enums
    ScannerType,
    ScanSeverity,
    ScanType,
    Severity,
    # Pydantic models
    ScanFinding,
    ScanResult,
    Finding,
    ScanMetrics,
    # Helper function
    utc_now,
)

from .config import (
    ScanConfig,
    AdvancedScannerConfig,
)

from .exceptions import (
    ScannerError,
    ScanTimeoutError,
    ScanConfigurationError,
    TargetNotAllowedError,
)

__all__ = [
    # Enums
    "ScannerType",
    "ScanSeverity",
    "ScanType",
    "Severity",
    # Models
    "ScanFinding",
    "ScanResult",
    "Finding",
    "ScanMetrics",
    # Config
    "ScanConfig",
    "AdvancedScannerConfig",
    # Exceptions
    "ScannerError",
    "ScanTimeoutError",
    "ScanConfigurationError",
    "TargetNotAllowedError",
    # Utils
    "utc_now",
]
