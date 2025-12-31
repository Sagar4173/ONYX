"""
Checkov IaC Scanner
===================

Infrastructure as Code security scanning using Checkov.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import logging

from .base_scanner import BaseScanner
from ..base.models import Finding, ScanType, Severity
from ..base.config import ScanConfig
from ..base.exceptions import ScannerError

logger = logging.getLogger(__name__)


class CheckovScanner(BaseScanner):
    """
    Checkov Infrastructure as Code security scanner.
    
    Scans Terraform, CloudFormation, Kubernetes, Docker, and other IaC files
    for security misconfigurations.
    """
    
    SCANNER_NAME = "checkov"
    SCANNER_TYPE = ScanType.IAC
    SUPPORTED_FRAMEWORKS = ["terraform", "cloudformation", "kubernetes", "docker", "arm", "bicep"]
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.checkov_path = self.config.checkov_path
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform IaC scan with Checkov.
        
        Args:
            target: Path to IaC files to scan
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - frameworks: List of frameworks to check
                - skip_checks: List of check IDs to skip
                
        Returns:
            List of security findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(
                mode='w+', suffix='.json', delete=False
            ) as tmp_file:
                output_file = tmp_file.name
            
            # Build Checkov command
            cmd = self._build_command(target, output_file, **kwargs)
            
            # Run Checkov (may return non-zero on findings)
            stdout, stderr, return_code = await self.run_command(cmd)
            
            # Parse results
            findings = self._parse_checkov_output(output_file, scan_id)
            
            # Cleanup
            Path(output_file).unlink(missing_ok=True)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def is_available(self) -> bool:
        """Check if Checkov is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.checkov_path, "--version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get Checkov version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.checkov_path, "--version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _build_command(
        self, 
        target: str, 
        output_file: str, 
        **kwargs
    ) -> List[str]:
        """Build Checkov command with options."""
        cmd = [
            self.checkov_path,
            "-d", target,
            "--output", "json",
            "--output-file-path", str(Path(output_file).parent),
            "--quiet",
            "--compact"
        ]
        
        # Add framework filters
        frameworks = kwargs.get('frameworks') or self.config.iac_frameworks
        if frameworks:
            cmd.extend(["--framework"] + frameworks)
        
        # Add custom policies
        for policy_path in self.config.iac_custom_policies:
            cmd.extend(["--external-checks-dir", policy_path])
        
        # Add skip checks
        if kwargs.get('skip_checks'):
            cmd.extend(["--skip-check", ",".join(kwargs['skip_checks'])])
        
        return cmd
    
    def _parse_checkov_output(self, output_file: str, scan_id: str) -> List[Finding]:
        """Parse Checkov JSON output."""
        findings = []
        
        try:
            # Checkov outputs to a directory, find the results file
            output_path = Path(output_file).parent
            results_file = output_path / "results_json.json"
            
            if not results_file.exists():
                results_file = Path(output_file)
            
            if not results_file.exists():
                logger.warning(f"Checkov output file not found")
                return findings
            
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            # Parse failed checks
            failed_checks = data.get("results", {}).get("failed_checks", [])
            
            for idx, check in enumerate(failed_checks):
                finding = self._create_finding(check, scan_id, idx)
                if finding:
                    findings.append(finding)
                    
        except Exception as e:
            logger.error(f"Error parsing Checkov output: {e}")
        
        return findings
    
    def _create_finding(
        self, 
        check: Dict[str, Any], 
        scan_id: str, 
        index: int
    ) -> Optional[Finding]:
        """Create a Finding from Checkov check result."""
        try:
            # Get file location
            file_line_range = check.get("file_line_range", [0, 0])
            
            finding = Finding(
                id=f"checkov-{scan_id}-{index}",
                source="checkov",
                rule_id=check.get("check_id", "unknown"),
                title=check.get("check_name", "Unknown Check"),
                description=check.get("description", ""),
                severity=self._normalize_checkov_severity(
                    check.get("severity", "MEDIUM")
                ),
                confidence="High",
                location={
                    "file": check.get("file_path", ""),
                    "line": file_line_range[0] if file_line_range else 0,
                    "end_line": file_line_range[1] if len(file_line_range) > 1 else None,
                    "resource": check.get("resource", ""),
                    "framework": check.get("check_type", "")
                },
                recommendation=check.get("guideline", ""),
                scan_type=ScanType.IAC,
                raw_output=check
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Checkov result: {e}")
            return None
    
    def _normalize_checkov_severity(self, checkov_severity: str) -> Severity:
        """Normalize Checkov severity to standard levels."""
        severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "INFO": Severity.INFO
        }
        return severity_map.get(checkov_severity.upper(), Severity.MEDIUM)
    
    def has_iac_files(self, repo_path: str) -> bool:
        """Check if repository has IaC files."""
        iac_patterns = [
            "*.tf",           # Terraform
            "*.yaml",         # Kubernetes, CloudFormation
            "*.yml",          # Kubernetes, CloudFormation
            "Dockerfile",     # Docker
            "docker-compose*.yml",
            "*.bicep",        # Azure Bicep
            "*.json"          # ARM templates
        ]
        
        for pattern in iac_patterns:
            if list(Path(repo_path).rglob(pattern)):
                return True
        
        return False
