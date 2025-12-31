"""
Semgrep SAST Scanner
====================

Static Application Security Testing using Semgrep for multi-language support.
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


class SemgrepScanner(BaseScanner):
    """
    Semgrep Static Application Security Testing scanner.
    
    A fast, open-source static analysis tool for finding bugs and 
    enforcing code standards. Supports many languages including
    Python, JavaScript, TypeScript, Java, Go, Ruby, and more.
    """
    
    SCANNER_NAME = "semgrep"
    SCANNER_TYPE = ScanType.SAST
    SUPPORTED_LANGUAGES = [
        "python", "javascript", "typescript", "java", "go", 
        "ruby", "php", "c", "cpp", "csharp", "rust", "scala", "kotlin"
    ]
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.semgrep_path = getattr(config, 'semgrep_path', 'semgrep')
        self.custom_rules_path = getattr(config, 'custom_rules_path', None)
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform SAST scan with Semgrep.
        
        Args:
            target: Path to code to scan
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - rules: Rule config (auto, p/security-audit, p/owasp-top-ten, etc.)
                - exclude: List of paths to exclude
                
        Returns:
            List of security findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        try:
            # Build Semgrep command
            cmd = self._build_command(target, **kwargs)
            
            # Run Semgrep
            stdout, stderr, return_code = await self.run_command(
                cmd, 
                timeout=self.config.semgrep_timeout
            )
            
            # Parse JSON output
            if stdout:
                findings = self._parse_semgrep_output(stdout, scan_id, target)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def is_available(self) -> bool:
        """Check if Semgrep is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.semgrep_path, "--version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get Semgrep version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.semgrep_path, "--version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build Semgrep command with options."""
        cmd = [
            self.semgrep_path,
            "--json",
            "-q"  # Quiet mode
        ]
        
        # Rule configuration
        rules = kwargs.get('rules', 'auto')
        if rules == 'custom' and self.custom_rules_path:
            cmd.extend(["--config", self.custom_rules_path])
        elif rules:
            cmd.extend(["--config", rules])
        
        # Exclude patterns
        for pattern in kwargs.get('exclude', []):
            cmd.extend(["--exclude", pattern])
        
        for pattern in self.config.sast_exclude_patterns:
            cmd.extend(["--exclude", pattern])
        
        # Add target
        cmd.append(target)
        
        return cmd
    
    def _parse_semgrep_output(
        self, 
        output: str, 
        scan_id: str, 
        repo_path: str
    ) -> List[Finding]:
        """Parse Semgrep JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            for idx, result in enumerate(data.get("results", [])):
                finding = self._create_finding(result, scan_id, idx, repo_path)
                if finding:
                    findings.append(finding)
                    
            # Log errors if any
            for error in data.get("errors", []):
                logger.warning(f"Semgrep error: {error.get('message', 'Unknown error')}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep JSON output: {e}")
        except Exception as e:
            logger.error(f"Error parsing Semgrep output: {e}")
        
        return findings
    
    def _create_finding(
        self, 
        result: Dict[str, Any], 
        scan_id: str, 
        index: int,
        repo_path: str
    ) -> Optional[Finding]:
        """Create a Finding from Semgrep result."""
        try:
            # Get relative file path
            file_path = result.get("path", "")
            try:
                file_path = str(Path(file_path).relative_to(repo_path))
            except ValueError:
                pass
            
            # Get metadata
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})
            
            finding = Finding(
                id=f"semgrep-{scan_id}-{index}",
                source="semgrep",
                rule_id=result.get("check_id", "UNKNOWN"),
                title=self._get_title(result),
                description=extra.get("message", "Security issue detected"),
                severity=self._normalize_semgrep_severity(
                    extra.get("severity", "WARNING")
                ),
                confidence=metadata.get("confidence", "MEDIUM"),
                location={
                    "file": file_path,
                    "line_start": result.get("start", {}).get("line", 0),
                    "line_end": result.get("end", {}).get("line", 0),
                    "col_start": result.get("start", {}).get("col", 0),
                    "col_end": result.get("end", {}).get("col", 0)
                },
                recommendation=self._get_fix(result),
                scan_type=ScanType.SAST,
                raw_output=result
            )
            
            # Add CWE if available
            cwe = metadata.get("cwe", [])
            if cwe:
                finding.cwe = cwe[0] if isinstance(cwe, list) else cwe
            
            # Add OWASP if available
            owasp = metadata.get("owasp", [])
            if owasp:
                finding.owasp = owasp if isinstance(owasp, list) else [owasp]
            
            # Add references
            refs = metadata.get("references", [])
            if refs:
                finding.references = refs
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Semgrep result: {e}")
            return None
    
    def _get_title(self, result: Dict[str, Any]) -> str:
        """Extract title from Semgrep result."""
        check_id = result.get("check_id", "")
        # Extract readable name from rule ID
        parts = check_id.split(".")
        if parts:
            return parts[-1].replace("-", " ").replace("_", " ").title()
        return "Security Issue"
    
    def _get_fix(self, result: Dict[str, Any]) -> str:
        """Get fix information from Semgrep result."""
        extra = result.get("extra", {})
        
        # Check for automated fix
        if extra.get("fix"):
            return f"Suggested fix: {extra['fix']}"
        
        # Check for fix_regex
        if extra.get("fix_regex"):
            return "A regex-based fix is available. Review and apply manually."
        
        # Check metadata for guidance
        metadata = extra.get("metadata", {})
        if metadata.get("fix"):
            return metadata["fix"]
        
        return "Review the finding and apply appropriate security measures."
    
    def _normalize_semgrep_severity(self, semgrep_severity: str) -> Severity:
        """Normalize Semgrep severity to standard levels."""
        severity_map = {
            "ERROR": Severity.HIGH,
            "WARNING": Severity.MEDIUM,
            "INFO": Severity.LOW
        }
        return severity_map.get(semgrep_severity.upper(), Severity.MEDIUM)
