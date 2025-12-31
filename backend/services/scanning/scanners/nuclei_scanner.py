"""
Nuclei Pentest Scanner
======================

Penetration testing using Nuclei vulnerability scanner with templates.
"""

import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from pathlib import Path
import tempfile
import logging

from .base_scanner import BaseScanner
from ..base.models import Finding, ScanType, Severity
from ..base.config import ScanConfig
from ..base.exceptions import TargetNotAllowedError, ScannerError

logger = logging.getLogger(__name__)


class NucleiScanner(BaseScanner):
    """
    Nuclei vulnerability scanner for penetration testing.
    
    Uses Nuclei templates to detect vulnerabilities, misconfigurations,
    and security issues in web applications.
    """
    
    SCANNER_NAME = "nuclei"
    SCANNER_TYPE = ScanType.PENTEST
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.nuclei_path = self.config.nuclei_path
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform pentest scan with Nuclei.
        
        Args:
            target: Target URL to scan
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - templates: List of template IDs to use
                - severity: Filter by severity (critical, high, medium, low)
                
        Returns:
            List of security findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        # Validate target is in allowlist
        if not self._is_target_allowed(target):
            raise TargetNotAllowedError(target, self.SCANNER_NAME)
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(
                mode='w+', suffix='.json', delete=False
            ) as tmp_file:
                output_file = tmp_file.name
            
            # Build Nuclei command
            cmd = self._build_command(target, output_file, **kwargs)
            
            # Run Nuclei
            stdout, stderr, return_code = await self.run_command(cmd)
            
            # Parse results
            findings = self._parse_nuclei_output(output_file, scan_id)
            
            # Cleanup
            Path(output_file).unlink(missing_ok=True)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def is_available(self) -> bool:
        """Check if Nuclei is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.nuclei_path, "-version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get Nuclei version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.nuclei_path, "-version"],
                timeout=30
            )
            if code == 0:
                # Parse version from output
                for line in stdout.split('\n'):
                    if 'nuclei' in line.lower():
                        return line.strip()
            return "unknown"
        except Exception:
            return "unknown"
    
    def _is_target_allowed(self, target_url: str) -> bool:
        """Check if target is in allowlist."""
        if not self.config.dast_target_allowlist:
            return False
        
        parsed_url = urlparse(target_url)
        target_host = parsed_url.netloc.lower()
        
        for allowed in self.config.dast_target_allowlist:
            allowed_lower = allowed.lower()
            if target_host == allowed_lower or target_host.endswith(f".{allowed_lower}"):
                return True
        
        return False
    
    def _build_command(
        self, 
        target: str, 
        output_file: str, 
        **kwargs
    ) -> List[str]:
        """Build Nuclei command with options."""
        cmd = [
            self.nuclei_path,
            "-target", target,
            "-json",
            "-output", output_file,
            "-rate-limit", str(int(self.config.dast_rate_limit)),
            "-timeout", "30",
            "-retries", "1",
            "-no-color",
            "-silent"
        ]
        
        # Add template filters if specified
        if kwargs.get('templates'):
            cmd.extend(["-t", ",".join(kwargs['templates'])])
        
        # Add severity filter if specified
        if kwargs.get('severity'):
            cmd.extend(["-s", kwargs['severity']])
        
        return cmd
    
    def _parse_nuclei_output(self, output_file: str, scan_id: str) -> List[Finding]:
        """Parse Nuclei JSON output."""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            finding = self._create_finding(result, scan_id, line_num)
                            if finding:
                                findings.append(finding)
                        except json.JSONDecodeError:
                            continue
        
        except FileNotFoundError:
            logger.warning(f"Nuclei output file not found: {output_file}")
        except Exception as e:
            logger.error(f"Error parsing Nuclei output: {e}")
        
        return findings
    
    def _create_finding(
        self, 
        result: Dict[str, Any], 
        scan_id: str, 
        index: int
    ) -> Optional[Finding]:
        """Create a Finding from Nuclei result."""
        try:
            info = result.get("info", {})
            classification = info.get("classification", {})
            
            finding = Finding(
                id=f"nuclei-{scan_id}-{index}",
                source="nuclei",
                rule_id=result.get("template-id", "unknown"),
                title=info.get("name", "Unknown Template"),
                description=info.get("description", ""),
                severity=self._normalize_nuclei_severity(
                    info.get("severity", "low")
                ),
                confidence="High",
                location={
                    "url": result.get("matched-at", ""),
                    "template": result.get("template", ""),
                    "matcher": result.get("matcher-name", "")
                },
                recommendation=info.get("remediation", ""),
                scan_type=ScanType.PENTEST,
                raw_output=result
            )
            
            # Add CWE if available
            if "cwe-id" in classification:
                finding.cwe = f"CWE-{classification['cwe-id']}"
            
            # Add CVE if available
            if "cve-id" in classification:
                finding.cve = classification['cve-id']
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Nuclei result: {e}")
            return None
    
    def _normalize_nuclei_severity(self, nuclei_severity: str) -> Severity:
        """Normalize Nuclei severity to standard levels."""
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO
        }
        return severity_map.get(nuclei_severity.lower(), Severity.LOW)
