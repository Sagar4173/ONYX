"""
Configuration Classes for Security Scanning
============================================

Contains configuration dataclasses and Pydantic models for scanner settings.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import ScannerType, ScanSeverity

# =============================================================================
# Dataclass Configuration (for internal use)
# =============================================================================

@dataclass
class ScanConfig:
    """
    Configuration for advanced scanning operations.
    
    This is the primary configuration class for the AdvancedScannerEngine.
    """
    # General settings
    max_concurrent_scans: int = 3
    scan_timeout: int = 1800  # 30 minutes
    
    # DAST settings
    dast_target_allowlist: List[str] = None
    dast_rate_limit: float = 2.0  # requests per second
    dast_max_depth: int = 3
    
    # SAST settings
    sast_languages: List[str] = None
    sast_exclude_patterns: List[str] = None
    
    # IaC settings
    iac_frameworks: List[str] = None
    iac_custom_policies: List[str] = None
    
    # Suppression settings
    suppression_file: str = ".security-suppressions.yaml"
    allow_inline_suppressions: bool = True
    
    # Scanner-specific paths
    zap_path: str = "zap.sh"
    nuclei_path: str = "nuclei"
    codeql_path: str = "codeql"
    checkov_path: str = "checkov"
    bandit_path: str = "bandit"
    semgrep_path: str = "semgrep"
    trivy_path: str = "trivy"
    gitleaks_path: str = "gitleaks"
    
    def __post_init__(self):
        if self.dast_target_allowlist is None:
            self.dast_target_allowlist = []
        if self.sast_languages is None:
            self.sast_languages = ["python", "javascript", "java", "go", "csharp"]
        if self.sast_exclude_patterns is None:
            self.sast_exclude_patterns = ["**/node_modules/**", "**/vendor/**", "**/.git/**"]
        if self.iac_frameworks is None:
            self.iac_frameworks = ["terraform", "cloudformation", "kubernetes", "docker"]
        if self.iac_custom_policies is None:
            self.iac_custom_policies = []


# =============================================================================
# Pydantic Configuration (for API serialization)
# =============================================================================

class AdvancedScannerConfig(BaseModel):
    """
    Configuration for advanced security scanners (Pydantic model for API).
    
    Used when configuring scans via API endpoints.
    """
    scanner_type: ScannerType
    enabled: bool = True
    timeout_seconds: int = 300
    max_findings: int = 1000
    severity_threshold: ScanSeverity = ScanSeverity.MEDIUM
    custom_config: Dict[str, Any] = Field(default_factory=dict)
    fail_build_on_critical: bool = True
    fail_build_on_high: bool = False
    
    class Config:
        use_enum_values = True


class DASTConfig(BaseModel):
    """Configuration specifically for DAST scanners."""
    target_url: str
    authenticated: bool = False
    auth_config: Optional[Dict[str, Any]] = None
    rate_limit: float = 2.0
    max_depth: int = 3
    excluded_paths: List[str] = Field(default_factory=list)
    timeout_seconds: int = 1800


class SASTConfig(BaseModel):
    """Configuration specifically for SAST scanners."""
    repo_path: str
    languages: List[str] = Field(default_factory=lambda: ["python", "javascript"])
    exclude_patterns: List[str] = Field(default_factory=lambda: ["**/node_modules/**", "**/vendor/**"])
    include_patterns: List[str] = Field(default_factory=list)
    timeout_seconds: int = 600


class IaCConfig(BaseModel):
    """Configuration specifically for IaC scanners."""
    target_path: str
    frameworks: List[str] = Field(default_factory=lambda: ["terraform", "kubernetes", "docker"])
    custom_policies: List[str] = Field(default_factory=list)
    skip_checks: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
