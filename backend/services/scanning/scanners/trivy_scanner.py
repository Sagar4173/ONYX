"""
Trivy Scanner
=============

Container and artifact vulnerability scanner using Trivy.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .base_scanner import BaseScanner
from ..base.models import Finding, ScanType, Severity
from ..base.config import ScanConfig
from ..base.exceptions import ScannerError

logger = logging.getLogger(__name__)


class TrivyScanner(BaseScanner):
    """
    Trivy vulnerability scanner.
    
    A comprehensive scanner for detecting vulnerabilities in:
    - Container images
    - Filesystems
    - Git repositories
    - Kubernetes clusters
    - Cloud infrastructure
    - SBOM files
    """
    
    SCANNER_NAME = "trivy"
    SCANNER_TYPE = ScanType.CONTAINER
    SUPPORTED_TARGETS = ["image", "fs", "repo", "config", "sbom"]
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.trivy_path = getattr(config, 'trivy_path', 'trivy')
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform vulnerability scan with Trivy.
        
        Args:
            target: Target to scan (image name, path, etc.)
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - scan_type: Type of scan (image, fs, repo, config, sbom)
                - severity: Severity filter (CRITICAL,HIGH,MEDIUM,LOW)
                - ignore_unfixed: Skip unfixed vulnerabilities
                
        Returns:
            List of security findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        try:
            # Determine scan type
            scan_type = kwargs.get('scan_type', self._detect_scan_type(target))
            
            # Build Trivy command
            cmd = self._build_command(target, scan_type, **kwargs)
            
            # Run Trivy
            stdout, stderr, return_code = await self.run_command(
                cmd, 
                timeout=kwargs.get('timeout', 600)
            )
            
            # Parse JSON output
            if stdout:
                findings = self._parse_trivy_output(stdout, scan_id, scan_type)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def scan_image(self, image: str, scan_id: str, **kwargs) -> List[Finding]:
        """Scan a container image."""
        kwargs['scan_type'] = 'image'
        return await self.scan(image, scan_id, **kwargs)
    
    async def scan_filesystem(self, path: str, scan_id: str, **kwargs) -> List[Finding]:
        """Scan a filesystem path."""
        kwargs['scan_type'] = 'fs'
        return await self.scan(path, scan_id, **kwargs)
    
    async def scan_config(self, path: str, scan_id: str, **kwargs) -> List[Finding]:
        """Scan configuration files (IaC, Dockerfiles, etc.)."""
        kwargs['scan_type'] = 'config'
        return await self.scan(path, scan_id, **kwargs)
    
    async def is_available(self) -> bool:
        """Check if Trivy is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.trivy_path, "version", "--format", "json"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get Trivy version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.trivy_path, "version", "--format", "json"],
                timeout=30
            )
            if code == 0:
                data = json.loads(stdout)
                return data.get("Version", "unknown")
            return "unknown"
        except Exception:
            return "unknown"
    
    def _detect_scan_type(self, target: str) -> str:
        """Detect the appropriate scan type from target."""
        # Check if it looks like a container image
        if ":" in target and not Path(target).exists():
            return "image"
        
        # Check if it's a path
        if Path(target).exists():
            return "fs"
        
        # Default to filesystem
        return "fs"
    
    def _build_command(self, target: str, scan_type: str, **kwargs) -> List[str]:
        """Build Trivy command with options."""
        cmd = [
            self.trivy_path,
            scan_type,
            "--format", "json",
            "-q"  # Quiet mode
        ]
        
        # Severity filter
        severity = kwargs.get('severity')
        if severity:
            cmd.extend(["--severity", severity])
        
        # Ignore unfixed
        if kwargs.get('ignore_unfixed', False):
            cmd.append("--ignore-unfixed")
        
        # Skip directories
        skip_dirs = kwargs.get('skip_dirs', [])
        for skip_dir in skip_dirs:
            cmd.extend(["--skip-dirs", skip_dir])
        
        # Skip files
        skip_files = kwargs.get('skip_files', [])
        for skip_file in skip_files:
            cmd.extend(["--skip-files", skip_file])
        
        # Vulnerability types
        vuln_types = kwargs.get('vuln_types', 'os,library')
        if scan_type in ['image', 'fs']:
            cmd.extend(["--vuln-type", vuln_types])
        
        # Security checks
        security_checks = kwargs.get('security_checks', 'vuln,secret,config')
        if scan_type == 'fs':
            cmd.extend(["--scanners", security_checks])
        
        # Add target
        cmd.append(target)
        
        return cmd
    
    def _parse_trivy_output(
        self, 
        output: str, 
        scan_id: str,
        scan_type: str
    ) -> List[Finding]:
        """Parse Trivy JSON output."""
        findings = []
        finding_index = 0
        
        try:
            data = json.loads(output)
            
            # Handle different output formats
            results = data.get("Results", [])
            if not results and isinstance(data, list):
                results = data
            
            for result in results:
                target_name = result.get("Target", "unknown")
                result_type = result.get("Type", scan_type)
                
                # Process vulnerabilities
                for vuln in result.get("Vulnerabilities", []):
                    finding = self._create_vuln_finding(
                        vuln, scan_id, finding_index, target_name, result_type
                    )
                    if finding:
                        findings.append(finding)
                        finding_index += 1
                
                # Process misconfigurations
                for misconfig in result.get("Misconfigurations", []):
                    finding = self._create_misconfig_finding(
                        misconfig, scan_id, finding_index, target_name
                    )
                    if finding:
                        findings.append(finding)
                        finding_index += 1
                
                # Process secrets
                for secret in result.get("Secrets", []):
                    finding = self._create_secret_finding(
                        secret, scan_id, finding_index, target_name
                    )
                    if finding:
                        findings.append(finding)
                        finding_index += 1
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Trivy JSON output: {e}")
        except Exception as e:
            logger.error(f"Error parsing Trivy output: {e}")
        
        return findings
    
    def _create_vuln_finding(
        self,
        vuln: Dict[str, Any],
        scan_id: str,
        index: int,
        target: str,
        vuln_type: str
    ) -> Optional[Finding]:
        """Create a Finding from Trivy vulnerability."""
        try:
            finding = Finding(
                id=f"trivy-vuln-{scan_id}-{index}",
                source="trivy",
                rule_id=vuln.get("VulnerabilityID", "UNKNOWN"),
                title=vuln.get("Title", vuln.get("VulnerabilityID", "Unknown Vulnerability")),
                description=vuln.get("Description", "Vulnerability detected"),
                severity=self._normalize_trivy_severity(vuln.get("Severity", "UNKNOWN")),
                confidence="HIGH",
                location={
                    "target": target,
                    "package": vuln.get("PkgName", ""),
                    "installed_version": vuln.get("InstalledVersion", ""),
                    "fixed_version": vuln.get("FixedVersion", ""),
                    "type": vuln_type
                },
                recommendation=self._get_vuln_remediation(vuln),
                scan_type=ScanType.CONTAINER if vuln_type in ['os', 'library'] else ScanType.SCA,
                raw_output=vuln
            )
            
            # Add CVE references
            refs = vuln.get("References", [])
            if refs:
                finding.references = refs
            
            # Add CVSS scores if available
            cvss = vuln.get("CVSS", {})
            if cvss:
                finding.cvss = cvss
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Trivy vulnerability: {e}")
            return None
    
    def _create_misconfig_finding(
        self,
        misconfig: Dict[str, Any],
        scan_id: str,
        index: int,
        target: str
    ) -> Optional[Finding]:
        """Create a Finding from Trivy misconfiguration."""
        try:
            finding = Finding(
                id=f"trivy-config-{scan_id}-{index}",
                source="trivy",
                rule_id=misconfig.get("ID", "UNKNOWN"),
                title=misconfig.get("Title", "Misconfiguration detected"),
                description=misconfig.get("Description", ""),
                severity=self._normalize_trivy_severity(misconfig.get("Severity", "MEDIUM")),
                confidence="HIGH",
                location={
                    "target": target,
                    "type": misconfig.get("Type", ""),
                    "cause": misconfig.get("CauseMetadata", {})
                },
                recommendation=misconfig.get("Resolution", "Review and fix the misconfiguration."),
                scan_type=ScanType.IAC,
                raw_output=misconfig
            )
            
            refs = misconfig.get("References", [])
            if refs:
                finding.references = refs
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Trivy misconfiguration: {e}")
            return None
    
    def _create_secret_finding(
        self,
        secret: Dict[str, Any],
        scan_id: str,
        index: int,
        target: str
    ) -> Optional[Finding]:
        """Create a Finding from Trivy secret detection."""
        try:
            finding = Finding(
                id=f"trivy-secret-{scan_id}-{index}",
                source="trivy",
                rule_id=secret.get("RuleID", "UNKNOWN"),
                title=secret.get("Title", "Secret detected"),
                description=f"Secret of type '{secret.get('Category', 'unknown')}' found in code",
                severity=Severity.HIGH,  # Secrets are always high severity
                confidence="HIGH",
                location={
                    "target": target,
                    "match": secret.get("Match", ""),
                    "start_line": secret.get("StartLine", 0),
                    "end_line": secret.get("EndLine", 0)
                },
                recommendation="Remove the secret from source code and rotate it immediately.",
                scan_type=ScanType.SECRETS,
                raw_output=secret
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Trivy secret: {e}")
            return None
    
    def _get_vuln_remediation(self, vuln: Dict[str, Any]) -> str:
        """Get remediation advice for vulnerability."""
        fixed_version = vuln.get("FixedVersion", "")
        pkg_name = vuln.get("PkgName", "package")
        
        if fixed_version:
            return f"Upgrade {pkg_name} to version {fixed_version} or later."
        else:
            return f"No fix available yet. Consider using an alternative package or mitigating controls."
    
    def _normalize_trivy_severity(self, trivy_severity: str) -> Severity:
        """Normalize Trivy severity to standard levels."""
        severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "UNKNOWN": Severity.UNKNOWN
        }
        return severity_map.get(trivy_severity.upper(), Severity.MEDIUM)
