"""
Core Models and Enums for Security Scanning
============================================

This module re-exports core enums from models.base for backward compatibility,
and adds scanning-specific models like Finding, ScanFinding, ScanResult.

IMPORTANT: The canonical enum definitions are in models.base.
This file re-exports them for convenience within the scanning package.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field
import logging

# Import canonical enums from models.base (single source of truth)
from models.base import (
    ScannerType,
    SeverityLevel as ScanSeverity,
    SeverityLevel as Severity,  # Alias for backward compatibility
    ScanStatus,
    ScanType,
    utc_now,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models (for API serialization)
# =============================================================================

class ScanFinding(BaseModel):
    """Individual security finding from scanners (Pydantic model for API)."""
    id: str
    title: str
    description: str
    severity: ScanSeverity
    scanner: ScannerType
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    url: Optional[str] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    remediation: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    code_snippet: Optional[str] = None
    fingerprint: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
    
    class Config:
        use_enum_values = True


class ScanResult(BaseModel):
    """Complete scan result from a scanner (Pydantic model for API)."""
    scanner: ScannerType
    target: str  # URL or repository path
    scan_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    duration_seconds: float
    findings: List[ScanFinding] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "completed"
    error_message: Optional[str] = None
    
    @property
    def critical_count(self) -> int:
        return len([f for f in self.findings if f.severity == ScanSeverity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        return len([f for f in self.findings if f.severity == ScanSeverity.HIGH])
    
    @property
    def summary(self) -> Dict[str, int]:
        """Get finding count summary by severity."""
        summary = {severity.value: 0 for severity in ScanSeverity}
        for finding in self.findings:
            severity_val = finding.severity.value if hasattr(finding.severity, 'value') else finding.severity
            summary[severity_val] = summary.get(severity_val, 0) + 1
        return summary
    
    class Config:
        use_enum_values = True


# =============================================================================
# Dataclass Models (for internal scanner use)
# =============================================================================

@dataclass
class Finding:
    """
    Normalized finding schema for internal scanner use.
    
    This dataclass is used within scanner implementations for efficient
    data handling. Convert to ScanFinding for API responses.
    """
    id: str
    source: str  # Scanner that generated the finding
    rule_id: str
    title: str
    description: str
    severity: Severity
    confidence: str
    location: Dict[str, Any]  # file, line, column, url, etc.
    cwe: Optional[str] = None
    cve: Optional[str] = None
    recommendation: Optional[str] = None
    scan_type: ScanType = ScanType.SAST
    raw_output: Optional[Dict] = None
    timestamp: str = None
    suppressed: bool = False
    suppression_reason: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = utc_now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_scan_finding(self) -> ScanFinding:
        """Convert to ScanFinding Pydantic model for API responses."""
        # Map internal Severity to ScanSeverity
        severity_map = {
            Severity.CRITICAL: ScanSeverity.CRITICAL,
            Severity.HIGH: ScanSeverity.HIGH,
            Severity.MEDIUM: ScanSeverity.MEDIUM,
            Severity.LOW: ScanSeverity.LOW,
            Severity.INFO: ScanSeverity.INFO,
        }
        
        return ScanFinding(
            id=self.id,
            title=self.title,
            description=self.description,
            severity=severity_map.get(self.severity, ScanSeverity.MEDIUM),
            scanner=ScannerType(self.source) if self.source in [s.value for s in ScannerType] else ScannerType.SEMGREP,
            file_path=self.location.get("file"),
            line_number=self.location.get("line"),
            column=self.location.get("column"),
            url=self.location.get("url"),
            cwe_id=self.cwe,
            cve_id=self.cve,
            remediation=self.recommendation,
            evidence=self.raw_output or {},
        )


@dataclass 
class ScanMetrics:
    """Metrics collected during a scan operation."""
    files_scanned: int = 0
    lines_of_code: int = 0
    scan_duration_seconds: float = 0.0
    memory_used_mb: float = 0.0
    findings_count: int = 0
    errors_count: int = 0
