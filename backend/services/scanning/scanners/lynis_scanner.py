"""
Lynis Infrastructure Auditor
============================

Infrastructure auditing and security scanning using Lynis.
Scans system configuration and security settings.
"""

import asyncio
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.config import ScanConfig
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class LynisScanner(BaseScanner):
    """
    Lynis infrastructure security auditor.

    Runs Lynis to audit system security and parses its output
    for warnings, suggestions, and security findings.
    """

    SCANNER_NAME = "lynis"
    SCANNER_TYPE = ScanType.IAC

    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.lynis_path = getattr(config, 'lynis_path', 'lynis')

    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []

        try:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as log_file:
                log_path = log_file.name
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.dat', delete=False) as dat_file:
                dat_path = dat_file.name

            cmd = [
                self.lynis_path, "audit", "system",
                "--quick",
                "--no-colors",
                "--logfile", log_path,
                "--reportfile", dat_path
            ]

            stdout, stderr, return_code = await self.run_command(cmd, timeout=600)

            findings = self._parse_lynis_output(log_path, scan_id)
            if not findings:
                findings = self._parse_lynis_stdout(stdout, scan_id)

            Path(log_path).unlink(missing_ok=True)
            Path(dat_path).unlink(missing_ok=True)

        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise

        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        return findings

    async def is_available(self) -> bool:
        try:
            stdout, stderr, code = await self.run_command(
                [self.lynis_path, "--version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False

    async def get_version(self) -> str:
        try:
            stdout, stderr, code = await self.run_command(
                [self.lynis_path, "--version"],
                timeout=30
            )
            if code == 0:
                for line in stdout.split('\n'):
                    if 'version' in line.lower():
                        return line.strip()
            return "unknown"
        except Exception:
            return "unknown"

    def _parse_lynis_output(self, log_path: str, scan_id: str) -> List[Finding]:
        findings = []
        try:
            with open(log_path, 'r', errors='ignore') as f:
                content = f.read()
            findings = self._extract_findings_from_log(content, scan_id)
        except FileNotFoundError:
            logger.debug("Lynis log file not found at %s", log_path)
        except Exception as e:
            logger.error("Error parsing Lynis output: %s", e)
        return findings

    def _parse_lynis_stdout(self, stdout: str, scan_id: str) -> List[Finding]:
        return self._extract_findings_from_log(stdout, scan_id)

    def _extract_findings_from_log(self, content: str, scan_id: str) -> List[Finding]:
        findings = []
        lines = content.split('\n')
        warning_index = 0
        suggestion_index = 0
        test_index = 0

        for line in lines:
            line_stripped = line.strip()

            warning_match = re.match(
                r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s+Warning:\s+(.+)$',
                line_stripped
            )
            if warning_match:
                finding = Finding(
                    id=f"lynis-{scan_id}-warn-{warning_index}",
                    source="lynis",
                    rule_id=f"LYN-WARN-{warning_index}",
                    title=f"Lynis Warning: {warning_match.group(1)[:80]}",
                    description=warning_match.group(1),
                    severity=Severity.MEDIUM,
                    confidence="Medium",
                    location={"log_type": "warning"},
                    recommendation="Review Lynis warning and apply recommended hardening",
                    scan_type=ScanType.IAC,
                    raw_output={"type": "warning", "message": warning_match.group(1)}
                )
                findings.append(finding)
                warning_index += 1
                continue

            suggestion_match = re.match(
                r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s+Suggestion:\s+(.+)$',
                line_stripped
            )
            if suggestion_match:
                finding = Finding(
                    id=f"lynis-{scan_id}-sug-{suggestion_index}",
                    source="lynis",
                    rule_id=f"LYN-SUG-{suggestion_index}",
                    title=f"Lynis Suggestion: {suggestion_match.group(1)[:80]}",
                    description=suggestion_match.group(1),
                    severity=Severity.LOW,
                    confidence="Medium",
                    location={"log_type": "suggestion"},
                    recommendation=suggestion_match.group(1),
                    scan_type=ScanType.IAC,
                    raw_output={"type": "suggestion", "message": suggestion_match.group(1)}
                )
                findings.append(finding)
                suggestion_index += 1
                continue

            test_match = re.match(
                r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s+Test:\s+(.+)$',
                line_stripped
            )
            if test_match and ('FAIL' in line_stripped or 'ERROR' in line_stripped):
                finding = Finding(
                    id=f"lynis-{scan_id}-test-{test_index}",
                    source="lynis",
                    rule_id=f"LYN-TEST-{test_index}",
                    title=f"Lynis Failed Test: {test_match.group(1)[:80]}",
                    description=test_match.group(1),
                    severity=Severity.HIGH,
                    confidence="High",
                    location={"log_type": "failed_test"},
                    recommendation="Investigate and remediate the failed security test",
                    scan_type=ScanType.IAC,
                    raw_output={"type": "failed_test", "message": test_match.group(1)}
                )
                findings.append(finding)
                test_index += 1

        return findings
