"""
Safety Dependency Scanner
=========================

Python dependency vulnerability scanner using Safety.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.config import ScanConfig
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class SafetyScanner(BaseScanner):
    """
    Safety dependency vulnerability scanner.
    
    Scans Python dependencies for known security vulnerabilities
    using the Safety database.
    """
    
    SCANNER_NAME = "safety"
    SCANNER_TYPE = ScanType.SCA
    SUPPORTED_FILES = ["requirements.txt", "Pipfile.lock", "poetry.lock", "setup.py"]
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.safety_path = getattr(config, 'safety_path', 'safety')
        self.api_key = getattr(config, 'safety_api_key', None)
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform dependency vulnerability scan with Safety.
        
        Args:
            target: Path to requirements file or directory
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - requirements_file: Specific requirements file to scan
                - stdin: Read from stdin (piped pip freeze output)
                
        Returns:
            List of vulnerability findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        try:
            # Find requirements files
            req_files = self._find_requirements_files(target, kwargs.get('requirements_file'))
            
            if not req_files:
                logger.warning(f"No requirements files found in {target}")
                return findings
            
            # Scan each requirements file
            for req_file in req_files:
                file_findings = await self._scan_requirements_file(
                    req_file, scan_id, len(findings)
                )
                findings.extend(file_findings)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def scan_requirements(self, requirements_file: str, scan_id: str) -> List[Finding]:
        """Scan a specific requirements file."""
        return await self.scan(requirements_file, scan_id, requirements_file=requirements_file)
    
    async def is_available(self) -> bool:
        """Check if Safety is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.safety_path, "--version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get Safety version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.safety_path, "--version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _find_requirements_files(
        self, 
        target: str, 
        specific_file: Optional[str] = None
    ) -> List[Path]:
        """Find all requirements files in target."""
        target_path = Path(target)
        
        if specific_file:
            specific_path = Path(specific_file)
            if specific_path.exists():
                return [specific_path]
        
        if target_path.is_file():
            return [target_path]
        
        req_files = []
        
        # Look for common Python dependency files
        patterns = [
            "requirements*.txt",
            "requirements/*.txt",
            "Pipfile.lock",
            "poetry.lock"
        ]
        
        for pattern in patterns:
            req_files.extend(target_path.glob(pattern))
        
        return req_files
    
    async def _scan_requirements_file(
        self, 
        req_file: Path, 
        scan_id: str,
        start_index: int
    ) -> List[Finding]:
        """Scan a single requirements file."""
        findings = []
        
        cmd = self._build_command(str(req_file))
        
        # Run Safety
        stdout, stderr, return_code = await self.run_command(cmd)
        
        # Parse JSON output
        if stdout:
            findings = self._parse_safety_output(
                stdout, scan_id, str(req_file), start_index
            )
        
        return findings
    
    def _build_command(self, requirements_file: str) -> List[str]:
        """Build Safety command with options."""
        cmd = [
            self.safety_path,
            "check",
            "--file", requirements_file,
            "--json"
        ]
        
        # Add API key if available (for full vulnerability database)
        if self.api_key:
            cmd.extend(["--key", self.api_key])
        
        return cmd
    
    def _parse_safety_output(
        self, 
        output: str, 
        scan_id: str, 
        req_file: str,
        start_index: int
    ) -> List[Finding]:
        """Parse Safety JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            # Safety 2.x format
            vulnerabilities = data.get("vulnerabilities", [])
            
            # Safety 1.x format fallback
            if not vulnerabilities and isinstance(data, list):
                vulnerabilities = data
            
            for idx, vuln in enumerate(vulnerabilities):
                finding = self._create_finding(
                    vuln, scan_id, start_index + idx, req_file
                )
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Safety JSON output: {e}")
        except Exception as e:
            logger.error(f"Error parsing Safety output: {e}")
        
        return findings
    
    def _create_finding(
        self, 
        vuln: Dict[str, Any], 
        scan_id: str, 
        index: int,
        req_file: str
    ) -> Optional[Finding]:
        """Create a Finding from Safety vulnerability."""
        try:
            # Handle different Safety output formats
            if isinstance(vuln, list):
                # Safety 1.x format: [package, spec, installed, description, id]
                package = vuln[0] if len(vuln) > 0 else "unknown"
                installed = vuln[2] if len(vuln) > 2 else "unknown"
                description = vuln[3] if len(vuln) > 3 else "Vulnerability detected"
                vuln_id = str(vuln[4]) if len(vuln) > 4 else "UNKNOWN"
            else:
                # Safety 2.x format
                package = vuln.get("package_name", vuln.get("name", "unknown"))
                installed = vuln.get("installed_version", vuln.get("version", "unknown"))
                description = vuln.get("advisory", vuln.get("description", "Vulnerability detected"))
                vuln_id = vuln.get("vulnerability_id", vuln.get("id", "UNKNOWN"))
            
            finding = Finding(
                id=f"safety-{scan_id}-{index}",
                source="safety",
                rule_id=str(vuln_id),
                title=f"Vulnerable Dependency: {package}",
                description=description,
                severity=self._determine_severity(vuln),
                confidence="HIGH",
                location={
                    "file": req_file,
                    "package": package,
                    "installed_version": installed,
                    "affected_versions": vuln.get("affected_versions", []) if isinstance(vuln, dict) else []
                },
                recommendation=self._get_remediation(vuln, package),
                scan_type=ScanType.SCA,
                raw_output=vuln
            )
            
            # Add CVE if available
            if isinstance(vuln, dict):
                cve = vuln.get("CVE") or vuln.get("cve")
                if cve:
                    finding.cve = cve
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Safety vulnerability: {e}")
            return None
    
    def _determine_severity(self, vuln: Dict[str, Any]) -> Severity:
        """Determine severity from Safety vulnerability data."""
        if isinstance(vuln, list):
            # Safety 1.x format - default to HIGH for known vulnerabilities
            return Severity.HIGH
        
        # Try to get explicit severity
        severity = vuln.get("severity", "").upper()
        
        if severity:
            severity_map = {
                "CRITICAL": Severity.CRITICAL,
                "HIGH": Severity.HIGH,
                "MEDIUM": Severity.MEDIUM,
                "LOW": Severity.LOW
            }
            return severity_map.get(severity, Severity.MEDIUM)
        
        # Try CVSS score
        cvss = vuln.get("cvss_score") or vuln.get("cvss", {}).get("score")
        if cvss:
            score = float(cvss)
            if score >= 9.0:
                return Severity.CRITICAL
            elif score >= 7.0:
                return Severity.HIGH
            elif score >= 4.0:
                return Severity.MEDIUM
            else:
                return Severity.LOW
        
        # Default to HIGH for known vulnerabilities
        return Severity.HIGH
    
    def _get_remediation(self, vuln: Dict[str, Any], package: str) -> str:
        """Get remediation advice for vulnerability."""
        if isinstance(vuln, dict):
            safe_versions = vuln.get("safe_versions", [])
            if safe_versions:
                versions = ", ".join(safe_versions) if isinstance(safe_versions, list) else safe_versions
                return f"Upgrade {package} to a safe version: {versions}"
        
        return f"Review and upgrade {package} to the latest secure version. Check the advisory for specific guidance."
