"""
Security Scanners
=================

Individual scanner implementations for various security tools.

Available Scanners:
- BaseScanner: Abstract base class for all scanners
- RealSecurityScanner: Comprehensive multi-tool scanner
- ZAPScanner: OWASP ZAP DAST scanner
- NucleiScanner: Nuclei pentest scanner
- CodeQLScanner: GitHub CodeQL SAST scanner
- CheckovScanner: Checkov IaC scanner
- BanditScanner: Bandit Python SAST scanner
- SemgrepScanner: Semgrep multi-language SAST scanner
- TrivyScanner: Trivy container and artifact vulnerability scanner
- GitLeaksScanner: GitLeaks secret detection scanner
- SafetyScanner: Safety Python dependency vulnerability scanner
- SopsScanner: SOPS configuration and encrypted file scanner
- DependencyGovernanceScanner: Dependency governance policy scanner
"""

from .bandit_scanner import BanditScanner
from .base_scanner import BaseScanner
from .checkov_scanner import CheckovScanner
from .codeql_scanner import CodeQLScanner
from .dependency_governance_scanner import DependencyGovernanceScanner
from .detect_secrets_scanner import DetectSecretsScanner
from .gitleaks_scanner import GitLeaksScanner
from .lynis_scanner import LynisScanner
from .nuclei_scanner import NucleiScanner
from .real_scanner import RealSecurityScanner
from .safety_scanner import SafetyScanner
from .semgrep_scanner import SemgrepScanner
from .sops_scanner import SopsScanner
from .trivy_scanner import TrivyScanner
from .zap_scanner import ZAPScanner

__all__ = [
    # Base class
    "BaseScanner",
    
    # Comprehensive scanner
    "RealSecurityScanner",
    
    # DAST (Dynamic Application Security Testing)
    "ZAPScanner",
    "NucleiScanner",
    
    # SAST (Static Application Security Testing)
    "CodeQLScanner",
    "BanditScanner",
    "SemgrepScanner",
    
    # IaC (Infrastructure as Code)
    "CheckovScanner",
    "LynisScanner",
    
    # Container/Artifact Scanning
    "TrivyScanner",
    
    # Secret Detection
    "DetectSecretsScanner",
    "GitLeaksScanner",
    "SopsScanner",
    
    # SCA (Software Composition Analysis)
    "SafetyScanner",
    "DependencyGovernanceScanner",
]
