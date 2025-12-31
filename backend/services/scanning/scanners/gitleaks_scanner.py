"""
GitLeaks Secrets Scanner
========================

Secret detection in Git repositories using GitLeaks.
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


class GitLeaksScanner(BaseScanner):
    """
    GitLeaks secret detection scanner.
    
    Detects hardcoded secrets in Git repositories including:
    - API keys and tokens
    - Passwords and credentials
    - Private keys
    - OAuth tokens
    - AWS/GCP/Azure credentials
    - And many more secret patterns
    """
    
    SCANNER_NAME = "gitleaks"
    SCANNER_TYPE = ScanType.SECRETS
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.gitleaks_path = getattr(config, 'gitleaks_path', 'gitleaks')
        self.custom_config_path = getattr(config, 'gitleaks_config_path', None)
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform secrets scan with GitLeaks.
        
        Args:
            target: Path to Git repository to scan
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - no_git: Scan without Git history (files only)
                - baseline: Path to baseline file
                - config: Path to custom config file
                
        Returns:
            List of secret findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        try:
            # Build GitLeaks command
            cmd = self._build_command(target, **kwargs)
            
            # Run GitLeaks (returns 1 if leaks found, 0 if clean)
            stdout, stderr, return_code = await self.run_command(cmd)
            
            # Parse JSON output (gitleaks outputs to stdout)
            if stdout and stdout.strip():
                findings = self._parse_gitleaks_output(stdout, scan_id, target)
            elif return_code == 0:
                logger.info(f"GitLeaks found no secrets in {target}")
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def scan_no_git(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """Scan files without Git history (for non-git directories)."""
        kwargs['no_git'] = True
        return await self.scan(target, scan_id, **kwargs)
    
    async def is_available(self) -> bool:
        """Check if GitLeaks is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.gitleaks_path, "version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get GitLeaks version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.gitleaks_path, "version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build GitLeaks command with options."""
        cmd = [
            self.gitleaks_path,
            "detect",
            "--report-format", "json",
            "-v"  # Verbose for detailed output
        ]
        
        # Scan mode
        if kwargs.get('no_git', False):
            cmd.extend(["--no-git"])
        
        # Source path
        cmd.extend(["--source", target])
        
        # Custom config
        config_path = kwargs.get('config') or self.custom_config_path
        if config_path and Path(config_path).exists():
            cmd.extend(["--config", config_path])
        
        # Baseline file
        baseline = kwargs.get('baseline')
        if baseline and Path(baseline).exists():
            cmd.extend(["--baseline-path", baseline])
        
        # Output to stdout (we capture it)
        cmd.extend(["--report-path", "/dev/stdout"])
        
        return cmd
    
    def _parse_gitleaks_output(
        self, 
        output: str, 
        scan_id: str, 
        repo_path: str
    ) -> List[Finding]:
        """Parse GitLeaks JSON output."""
        findings = []
        
        try:
            # GitLeaks outputs array of findings directly
            data = json.loads(output)
            
            if not isinstance(data, list):
                data = [data]
            
            for idx, result in enumerate(data):
                finding = self._create_finding(result, scan_id, idx, repo_path)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GitLeaks JSON output: {e}")
        except Exception as e:
            logger.error(f"Error parsing GitLeaks output: {e}")
        
        return findings
    
    def _create_finding(
        self, 
        result: Dict[str, Any], 
        scan_id: str, 
        index: int,
        repo_path: str
    ) -> Optional[Finding]:
        """Create a Finding from GitLeaks result."""
        try:
            # Get relative file path
            file_path = result.get("File", "")
            try:
                file_path = str(Path(file_path).relative_to(repo_path))
            except ValueError:
                pass
            
            # Mask the secret value
            secret_value = result.get("Secret", "")
            masked_secret = self._mask_secret(secret_value)
            
            finding = Finding(
                id=f"gitleaks-{scan_id}-{index}",
                source="gitleaks",
                rule_id=result.get("RuleID", "UNKNOWN"),
                title=f"Secret Detected: {result.get('RuleID', 'Unknown Type')}",
                description=self._get_secret_description(result),
                severity=self._get_secret_severity(result.get("RuleID", "")),
                confidence="HIGH",
                location={
                    "file": file_path,
                    "line_start": result.get("StartLine", 0),
                    "line_end": result.get("EndLine", 0),
                    "commit": result.get("Commit", ""),
                    "author": result.get("Author", ""),
                    "email": result.get("Email", ""),
                    "date": result.get("Date", ""),
                    "message": result.get("Message", "")[:100] if result.get("Message") else ""
                },
                recommendation=self._get_remediation(result),
                scan_type=ScanType.SECRETS,
                raw_output={
                    **result,
                    "Secret": masked_secret  # Never store raw secrets
                }
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from GitLeaks result: {e}")
            return None
    
    def _mask_secret(self, secret: str) -> str:
        """Mask secret value for safe storage."""
        if not secret:
            return ""
        if len(secret) <= 8:
            return "*" * len(secret)
        return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
    
    def _get_secret_description(self, result: Dict[str, Any]) -> str:
        """Generate description for secret finding."""
        rule_id = result.get("RuleID", "unknown")
        file_path = result.get("File", "unknown file")
        
        descriptions = {
            "aws-access-key-id": "AWS Access Key ID found. This key could provide unauthorized access to AWS services.",
            "aws-secret-access-key": "AWS Secret Access Key found. This key paired with an Access Key ID provides full AWS access.",
            "github-token": "GitHub Token found. This token could provide access to repositories and GitHub API.",
            "github-pat": "GitHub Personal Access Token found. This could compromise repository access.",
            "google-api-key": "Google API Key found. This key could provide access to Google Cloud services.",
            "private-key": "Private Key found. This cryptographic key could be used for authentication or decryption.",
            "generic-api-key": "API Key pattern detected. Review to determine the service and potential impact.",
            "password-in-url": "Password embedded in URL. This exposes credentials in logs and browser history.",
            "jwt": "JSON Web Token found. This token could provide authenticated access to services.",
            "slack-token": "Slack Token found. This could provide access to Slack workspace messages and data.",
            "stripe-api-key": "Stripe API Key found. This could allow unauthorized payment operations.",
            "twilio-api-key": "Twilio API Key found. This could allow unauthorized SMS/voice operations.",
        }
        
        base_desc = descriptions.get(
            rule_id.lower(), 
            f"Potential secret ({rule_id}) detected in source code."
        )
        
        return f"{base_desc} Found in {file_path}."
    
    def _get_secret_severity(self, rule_id: str) -> Severity:
        """Determine severity based on secret type."""
        critical_secrets = [
            "aws-secret-access-key", "private-key", "stripe-live-key",
            "gcp-service-account", "azure-storage-key"
        ]
        high_secrets = [
            "aws-access-key-id", "github-token", "github-pat",
            "google-api-key", "slack-token", "jwt", "database-url",
            "password-in-url", "stripe-api-key"
        ]
        
        rule_lower = rule_id.lower()
        
        if any(s in rule_lower for s in critical_secrets):
            return Severity.CRITICAL
        elif any(s in rule_lower for s in high_secrets):
            return Severity.HIGH
        else:
            return Severity.HIGH  # All secrets are at least high severity
    
    def _get_remediation(self, result: Dict[str, Any]) -> str:
        """Get remediation advice for secret finding."""
        rule_id = result.get("RuleID", "").lower()
        
        remediations = {
            "aws": (
                "1. Immediately rotate the AWS credentials in the IAM console.\n"
                "2. Review CloudTrail logs for unauthorized access.\n"
                "3. Remove the secret from Git history using git-filter-repo or BFG.\n"
                "4. Use AWS Secrets Manager or environment variables instead."
            ),
            "github": (
                "1. Revoke the token immediately in GitHub Settings > Developer Settings.\n"
                "2. Review GitHub audit logs for unauthorized access.\n"
                "3. Remove the secret from Git history.\n"
                "4. Use GitHub Actions secrets or environment variables."
            ),
            "private-key": (
                "1. Generate a new key pair immediately.\n"
                "2. Revoke/rotate any certificates using the compromised key.\n"
                "3. Remove the key from Git history.\n"
                "4. Store private keys in secure vaults (HashiCorp Vault, AWS Secrets Manager)."
            ),
            "stripe": (
                "1. Roll the API key in the Stripe Dashboard immediately.\n"
                "2. Review Stripe logs for unauthorized transactions.\n"
                "3. Remove from Git history.\n"
                "4. Use environment variables for Stripe keys."
            ),
            "database": (
                "1. Rotate the database credentials immediately.\n"
                "2. Review database access logs.\n"
                "3. Remove from Git history.\n"
                "4. Use secrets management for database credentials."
            ),
        }
        
        for key, remediation in remediations.items():
            if key in rule_id:
                return remediation
        
        return (
            "1. Rotate or revoke the exposed secret immediately.\n"
            "2. Review logs for unauthorized access.\n"
            "3. Remove the secret from Git history using git-filter-repo or BFG Repo-Cleaner.\n"
            "4. Use a secrets management solution (environment variables, vault, etc.)."
        )
