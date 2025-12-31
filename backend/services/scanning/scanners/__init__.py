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
"""

from .base_scanner import BaseScanner
from .real_scanner import RealSecurityScanner
from .zap_scanner import ZAPScanner
from .nuclei_scanner import NucleiScanner
from .codeql_scanner import CodeQLScanner
from .checkov_scanner import CheckovScanner
from .bandit_scanner import BanditScanner
from .semgrep_scanner import SemgrepScanner
from .trivy_scanner import TrivyScanner
from .gitleaks_scanner import GitLeaksScanner
from .safety_scanner import SafetyScanner

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
    
    # Container/Artifact Scanning
    "TrivyScanner",
    
    # Secret Detection
    "GitLeaksScanner",
    
    # SCA (Software Composition Analysis)
    "SafetyScanner",
]
