"""
OWASP ZAP DAST Scanner
======================

Dynamic Application Security Testing using OWASP Zed Attack Proxy.
Communicates with ZAP daemon via its REST API.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from ..base.config import ScanConfig
from ..base.exceptions import TargetNotAllowedError
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class ZAPScanner(BaseScanner):
    """
    OWASP ZAP Dynamic Application Security Testing scanner.

    Starts ZAP in daemon mode and uses its REST API to spider,
    actively scan, and extract alerts from web application targets.
    """

    SCANNER_NAME = "zap"
    SCANNER_TYPE = ScanType.DAST

    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.zap_path = self.config.zap_path
        self.proxy_port = 8080
        self.zap_process = None
        self.api_key = None

    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []

        if not self._is_target_allowed(target):
            raise TargetNotAllowedError(target, self.SCANNER_NAME)

        try:
            await self._start_zap_daemon()
            api_base = f"http://127.0.0.1:{self.proxy_port}/JSON"

            spider_id = await self._spider_target(api_base, target)
            if spider_id:
                await self._wait_for_spider(api_base, spider_id)

            scan_id_zap = await self._active_scan(api_base, target)
            if scan_id_zap:
                await self._wait_for_scan(api_base, scan_id_zap)

            findings = await self._get_zap_findings(api_base, target, scan_id)

        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        finally:
            await self._stop_zap_daemon()

        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        return findings

    async def is_available(self) -> bool:
        try:
            stdout, stderr, code = await self.run_command(
                [self.zap_path, "-version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False

    async def get_version(self) -> str:
        try:
            stdout, stderr, code = await self.run_command(
                [self.zap_path, "-version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"

    def _is_target_allowed(self, target_url: str) -> bool:
        if not self.config.dast_target_allowlist:
            return False
        parsed_url = urlparse(target_url)
        target_host = parsed_url.netloc.lower()
        for allowed in self.config.dast_target_allowlist:
            allowed_lower = allowed.lower()
            if target_host == allowed_lower or target_host.endswith(f".{allowed_lower}"):
                return True
        return False

    async def _start_zap_daemon(self):
        cmd = [
            self.zap_path, "-daemon",
            "-port", str(self.proxy_port),
            "-config", "api.disablekey=true",
            "-config", "api.addrs.addr.name=.*",
            "-config", "api.addrs.addr.regex=true"
        ]
        self.zap_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(10)
        logger.info("ZAP daemon started on port %d", self.proxy_port)

    async def _stop_zap_daemon(self):
        if self.zap_process:
            self.zap_process.terminate()
            await self.zap_process.wait()
            logger.info("ZAP daemon stopped")

    async def _api_call(self, api_base: str, path: str) -> Optional[Dict[str, Any]]:
        url = f"{api_base}{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.warning("ZAP API call failed: %s - %s", path, e)
            return None

    async def _spider_target(self, api_base: str, target: str) -> Optional[str]:
        result = await self._api_call(
            api_base,
            f"/spider/action/scan/?url={target}&recurse=true&maxChildren=10"
        )
        if result:
            spider_id = result.get("scan")
            logger.info("ZAP spider started: %s", spider_id)
            return spider_id
        return None

    async def _wait_for_spider(self, api_base: str, spider_id: str, max_wait: int = 120):
        for _ in range(max_wait):
            result = await self._api_call(
                api_base,
                f"/spider/view/status/?scanId={spider_id}"
            )
            if result:
                status = result.get("status", "0")
                logger.debug("ZAP spider status: %s%%", status)
                if status == "100":
                    logger.info("ZAP spider completed")
                    return
            await asyncio.sleep(2)
        logger.warning("ZAP spider timed out")

    async def _active_scan(self, api_base: str, target: str) -> Optional[str]:
        result = await self._api_call(
            api_base,
            f"/ascan/action/scan/?url={target}&recurse=true"
        )
        if result:
            scan_id = result.get("scan")
            logger.info("ZAP active scan started: %s", scan_id)
            return scan_id
        return None

    async def _wait_for_scan(self, api_base: str, scan_id: str, max_wait: int = 600):
        for _ in range(max_wait):
            result = await self._api_call(
                api_base,
                f"/ascan/view/status/?scanId={scan_id}"
            )
            if result:
                status = result.get("status", "0")
                logger.debug("ZAP active scan status: %s%%", status)
                if status == "100":
                    logger.info("ZAP active scan completed")
                    return
            await asyncio.sleep(2)
        logger.warning("ZAP active scan timed out")

    async def _get_zap_findings(self, api_base: str, target: str, scan_id: str) -> List[Finding]:
        findings = []
        result = await self._api_call(
            api_base,
            f"/core/view/alerts/?baseurl={target}"
        )
        if not result:
            logger.info("No ZAP alerts returned (ZAP may not be installed)")
            return findings

        alerts = result.get("alerts", [])
        for idx, alert in enumerate(alerts):
            finding = self._alert_to_finding(alert, scan_id, idx)
            if finding:
                findings.append(finding)

        logger.info("ZAP returned %d findings from %d alerts", len(findings), len(alerts))
        return findings

    def _alert_to_finding(self, alert: Dict[str, Any], scan_id: str, index: int) -> Optional[Finding]:
        try:
            return Finding(
                id=f"zap-{scan_id}-{index}",
                source="zap",
                rule_id=alert.get("pluginId", "unknown"),
                title=alert.get("name", "Unknown Alert"),
                description=alert.get("description", ""),
                severity=self._normalize_zap_severity(alert.get("risk", "Low")),
                confidence=self._confidence_from_alert(alert),
                location={
                    "url": alert.get("url", ""),
                    "param": alert.get("param", ""),
                    "evidence": alert.get("evidence", ""),
                    "attack": alert.get("attack", "")
                },
                recommendation=alert.get("solution", ""),
                scan_type=ScanType.DAST,
                raw_output=alert
            )
        except Exception as e:
            logger.error("Failed to create finding from ZAP alert: %s", e)
            return None

    def _normalize_zap_severity(self, risk: str) -> Severity:
        severity_map = {
            "3": Severity.HIGH,
            "2": Severity.MEDIUM,
            "1": Severity.LOW,
            "0": Severity.INFO,
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW,
            "Informational": Severity.INFO
        }
        return severity_map.get(risk, Severity.LOW)

    def _confidence_from_alert(self, alert: Dict[str, Any]) -> str:
        confidence_map = {
            "3": "High",
            "2": "Medium",
            "1": "Low",
            "0": "Low",
            "High": "High",
            "Medium": "Medium",
            "Low": "Low"
        }
        return confidence_map.get(alert.get("confidence", "2"), "Medium")
