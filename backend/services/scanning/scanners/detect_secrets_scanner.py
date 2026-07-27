"""
Detect-Secrets Scanner
======================

Secret detection using the detect-secrets Python library.
Scans files for high-entropy strings, private keys, credentials, and tokens.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from detect_secrets import SecretsCollection
from detect_secrets.settings import default_settings

from ..base.config import ScanConfig
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class DetectSecretsScanner(BaseScanner):
    """
    Detect-secrets secret detection scanner.

    Uses the detect-secrets library to find:
    - High-entropy strings (passwords, tokens)
    - Private keys
    - AWS/GCP/Azure credentials
    - OAuth tokens
    - Database connection strings
    """

    SCANNER_NAME = "detect-secrets"
    SCANNER_TYPE = ScanType.SECRETS

    def __init__(self, config: ScanConfig = None):
        super().__init__(config)

    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []

        try:
            scan_path = Path(target)
            if not scan_path.exists():
                logger.warning("Target path does not exist: %s", target)
                return findings

            secrets_collection = await asyncio.to_thread(
                self._scan_directory, scan_path
            )

            findings = self._secrets_to_findings(secrets_collection, scan_id)

        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise

        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        return findings

    async def is_available(self) -> bool:
        try:
            import detect_secrets
            return True
        except ImportError:
            return False

    async def get_version(self) -> str:
        try:
            import detect_secrets
            return getattr(detect_secrets, '__version__', '1.4.0+')
        except ImportError:
            return "unknown"

    def _scan_directory(self, scan_path: Path) -> SecretsCollection:
        secrets = SecretsCollection()
        with default_settings():
            for file_path in scan_path.rglob('*'):
                if file_path.is_file() and not self._is_excluded(file_path):
                    try:
                        secrets.scan_file(str(file_path))
                    except Exception as e:
                        logger.debug("Skipping %s: %s", file_path, e)
        return secrets

    def _is_excluded(self, file_path: Path) -> bool:
        excluded_patterns = [
            '.git/', 'node_modules/', 'vendor/', '__pycache__/',
            '.venv/', 'venv/', 'dist/', 'build/', '.tox/',
            '.egg-info/', 'site-packages/', '.pytest_cache/',
            '.mypy_cache/', '.coverage', '.DS_Store'
        ]
        str_path = str(file_path.as_posix())
        return any(p in str_path for p in excluded_patterns)

    def _secrets_to_findings(
        self, secrets: SecretsCollection, scan_id: str
    ) -> List[Finding]:
        findings = []
        index = 0

        for filename in secrets.files:
            for secret in secrets[filename]:
                finding = self._secret_to_finding(
                    secret, filename, scan_id, index
                )
                if finding:
                    findings.append(finding)
                    index += 1

        return findings

    def _secret_to_finding(
        self,
        secret: Dict[str, Any],
        filename: str,
        scan_id: str,
        index: int
    ) -> Optional[Finding]:
        try:
            secret_type = secret.get('type', 'Unknown')
            is_verified = secret.get('is_verified', False)

            severity = Severity.CRITICAL if is_verified else Severity.HIGH

            return Finding(
                id=f"detect-secrets-{scan_id}-{index}",
                source="detect-secrets",
                rule_id=f"DS-{secret_type}",
                title=f"Secret Detected: {secret_type}",
                description=secret.get('description', ''),
                severity=severity,
                confidence="High" if is_verified else "Medium",
                location={
                    "file": filename,
                    "line": secret.get('line_number', 0),
                    "line_number": secret.get('line_number', 0)
                },
                recommendation=(
                    "Immediately rotate this secret. Check if it was "
                    "committed to the repository and clean the git history."
                ),
                scan_type=ScanType.SECRETS,
                raw_output={
                    "type": secret_type,
                    "filename": filename,
                    "line_number": secret.get('line_number'),
                    "is_verified": is_verified,
                    "hashed_secret": secret.get('hashed_secret', ''),
                }
            )
        except Exception as e:
            logger.error("Failed to create finding for secret: %s", e)
            return None
