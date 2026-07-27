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

from .config import (
    AdvancedScannerConfig,
    ScanConfig,
)
from .exceptions import (
    ScanConfigurationError,
    ScannerError,
    ScanTimeoutError,
    TargetNotAllowedError,
)
from .models import (
    Finding,
    # Pydantic models
    ScanFinding,
    ScanMetrics,
    # Enums
    ScannerType,
    ScanResult,
    ScanSeverity,
    ScanType,
    Severity,
    # Helper function
    utc_now,
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
