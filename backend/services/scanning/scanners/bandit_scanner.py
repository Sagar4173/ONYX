"""
Bandit Python SAST Scanner
==========================

Static Application Security Testing for Python using Bandit.
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


class BanditScanner(BaseScanner):
    """
    Bandit Python Static Application Security Testing scanner.
    
    Designed to find common security issues in Python code including:
    - SQL injection
    - Command injection
    - Hardcoded passwords
    - Use of weak cryptographic functions
    - And many more
    """
    
    SCANNER_NAME = "bandit"
    SCANNER_TYPE = ScanType.SAST
    SUPPORTED_LANGUAGES = ["python"]
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.bandit_path = self.config.bandit_path
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform SAST scan with Bandit.
        
        Args:
            target: Path to Python code to scan
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - severity: Minimum severity to report (low, medium, high)
                - confidence: Minimum confidence (low, medium, high)
                
        Returns:
            List of security findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        # Check if there are Python files
        python_files = list(Path(target).rglob("*.py"))
        if not python_files:
            logger.info("No Python files found for Bandit scan")
            return findings
        
        logger.info(f"Found {len(python_files)} Python files to scan")
        
        try:
            # Build Bandit command
            cmd = self._build_command(target, **kwargs)
            
            # Run Bandit
            stdout, stderr, return_code = await self.run_command(cmd)
            
            # Parse JSON output from stdout
            if stdout:
                findings = self._parse_bandit_output(stdout, scan_id, target)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def is_available(self) -> bool:
        """Check if Bandit is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.bandit_path, "--version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get Bandit version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.bandit_path, "--version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build Bandit command with options."""
        cmd = [
            self.bandit_path,
            "-r", target,
            "-f", "json",
            "-q"  # Quiet mode
        ]
        
        # Add severity filter
        severity = kwargs.get('severity', 'low')
        if severity:
            severity_map = {'low': 'l', 'medium': 'm', 'high': 'h'}
            cmd.extend(["-l", severity_map.get(severity.lower(), 'l')])
        
        # Add confidence filter
        confidence = kwargs.get('confidence', 'low')
        if confidence:
            confidence_map = {'low': 'l', 'medium': 'm', 'high': 'h'}
            cmd.extend(["-i", confidence_map.get(confidence.lower(), 'l')])
        
        # Exclude patterns
        for pattern in self.config.sast_exclude_patterns:
            cmd.extend(["--exclude", pattern])
        
        return cmd
    
    def _parse_bandit_output(
        self, 
        output: str, 
        scan_id: str, 
        repo_path: str
    ) -> List[Finding]:
        """Parse Bandit JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            for idx, result in enumerate(data.get("results", [])):
                finding = self._create_finding(result, scan_id, idx, repo_path)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON output: {e}")
        except Exception as e:
            logger.error(f"Error parsing Bandit output: {e}")
        
        return findings
    
    def _create_finding(
        self, 
        result: Dict[str, Any], 
        scan_id: str, 
        index: int,
        repo_path: str
    ) -> Optional[Finding]:
        """Create a Finding from Bandit result."""
        try:
            # Get relative file path
            file_path = result.get("filename", "")
            try:
                file_path = str(Path(file_path).relative_to(repo_path))
            except ValueError:
                pass
            
            finding = Finding(
                id=f"bandit-{scan_id}-{index}",
                source="bandit",
                rule_id=result.get("test_id", "UNKNOWN"),
                title=result.get("test_name", "Unknown Security Issue"),
                description=result.get("issue_text", "Security issue detected"),
                severity=self._normalize_bandit_severity(
                    result.get("issue_severity", "LOW")
                ),
                confidence=result.get("issue_confidence", "MEDIUM"),
                location={
                    "file": file_path,
                    "line": result.get("line_number", 0),
                    "col_offset": result.get("col_offset", 0),
                    "end_col_offset": result.get("end_col_offset", 0)
                },
                recommendation=self._get_remediation(result.get("test_id", "")),
                scan_type=ScanType.SAST,
                raw_output=result
            )
            
            # Add CWE if available
            cwe = result.get("issue_cwe", {})
            if cwe:
                finding.cwe = f"CWE-{cwe.get('id', '')}"
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from Bandit result: {e}")
            return None
    
    def _normalize_bandit_severity(self, bandit_severity: str) -> Severity:
        """Normalize Bandit severity to standard levels."""
        severity_map = {
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW
        }
        return severity_map.get(bandit_severity.upper(), Severity.MEDIUM)
    
    def _get_remediation(self, test_id: str) -> str:
        """Get remediation advice for Bandit test."""
        remediations = {
            "B101": "Avoid using assert statements in production code. Use proper error handling.",
            "B102": "Use subprocess with shell=False and pass arguments as a list.",
            "B103": "Set secure file permissions using os.chmod().",
            "B104": "Avoid binding to all interfaces (0.0.0.0). Use specific IP addresses.",
            "B105": "Do not hardcode passwords. Use environment variables or secure vaults.",
            "B106": "Do not hardcode passwords in function arguments.",
            "B107": "Do not hardcode passwords in function defaults.",
            "B108": "Avoid using temporary files with predictable names.",
            "B110": "Always specify exception types. Avoid bare 'except:' clauses.",
            "B112": "Avoid using 'try-except-continue' patterns.",
            "B201": "Avoid using Flask in debug mode in production.",
            "B301": "Use pickle with caution. Consider using json for untrusted data.",
            "B302": "marshal.loads() can execute arbitrary code. Use with caution.",
            "B303": "MD5 and SHA1 are insecure for cryptographic purposes. Use SHA-256+.",
            "B304": "Use secure random number generators from secrets module.",
            "B305": "Use secure ciphers. Avoid DES, 3DES, RC4.",
            "B306": "Use secure cryptographic modes. Avoid ECB mode.",
            "B307": "Do not use eval(). Use ast.literal_eval() for safe evaluation.",
            "B308": "mark_safe() can lead to XSS. Ensure content is properly escaped.",
            "B310": "Validate URLs before making requests to prevent SSRF.",
            "B311": "Use secrets.choice() instead of random.choice() for security.",
            "B312": "telnetlib is insecure. Use SSH instead.",
            "B313": "xml.etree is vulnerable to XXE. Use defusedxml.",
            "B320": "lxml is vulnerable to XXE. Use defusedxml.",
            "B324": "Use hashlib with secure algorithms (SHA-256+).",
            "B501": "Enable SSL certificate validation. Never use verify=False.",
            "B502": "Use ssl.create_default_context() for secure SSL configuration.",
            "B503": "Use secure SSL protocols (TLS 1.2+).",
            "B504": "Enable hostname checking in SSL connections.",
            "B505": "Use cryptographically secure key sizes (RSA 2048+, EC 256+).",
            "B506": "Use safe YAML loading: yaml.safe_load() instead of yaml.load().",
            "B507": "Enable host key verification in SSH connections.",
            "B601": "Avoid shell=True in paramiko.exec_command().",
            "B602": "Avoid subprocess with shell=True. Pass arguments as a list.",
            "B603": "Validate and sanitize subprocess inputs.",
            "B604": "Validate and sanitize function call arguments.",
            "B605": "Avoid os.system(). Use subprocess with shell=False.",
            "B606": "Avoid os.popen(). Use subprocess with shell=False.",
            "B607": "Use absolute paths in subprocess calls.",
            "B608": "Use parameterized queries to prevent SQL injection.",
            "B609": "Avoid wildcard injection in shell commands.",
            "B610": "Use Django ORM's extra() with caution. Prefer ORM methods.",
            "B611": "Use Django ORM's raw() with parameterized queries.",
            "B701": "Avoid using Jinja2 with autoescape disabled.",
            "B702": "Use Mako with proper escaping enabled.",
            "B703": "Disable Django template debug mode in production.",
        }
        
        return remediations.get(test_id, "Review the finding and apply appropriate security measures.")
