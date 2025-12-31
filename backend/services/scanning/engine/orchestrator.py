"""
Scan Orchestrator
=================

Main orchestration engine for coordinating multiple security scanners.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
import logging
from dataclasses import dataclass, field

from utils.datetime_utils import utc_now

from ..scanners import (
    BaseScanner,
    ZAPScanner,
    NucleiScanner,
    CodeQLScanner,
    CheckovScanner,
    BanditScanner,
    SemgrepScanner,
    TrivyScanner,
    GitLeaksScanner,
    SafetyScanner
)
from ..base.models import Finding, ScanResult, ScanMetrics, ScanType, Severity
from ..base.config import ScanConfig
from ..base.exceptions import ScannerError, ScanTimeoutError
from .suppression import SuppressionEngine

logger = logging.getLogger(__name__)


@dataclass
class ScanRequest:
    """Request for a security scan."""
    target: str
    scan_types: List[ScanType]
    scan_id: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.scan_id:
            self.scan_id = str(uuid.uuid4())


class ScanOrchestrator:
    """
    Main orchestration engine for security scanning.
    
    Coordinates multiple scanners, manages scan lifecycle,
    and aggregates results.
    
    Usage:
        orchestrator = ScanOrchestrator(config)
        result = await orchestrator.run_scan(request)
    """
    
    def __init__(self, config: ScanConfig = None):
        self.config = config or ScanConfig()
        self.suppression_engine = SuppressionEngine()
        
        # Initialize scanners
        self._scanners: Dict[ScanType, List[BaseScanner]] = {}
        self._initialize_scanners()
        
        # Track active scans
        self._active_scans: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_scanners(self):
        """Initialize all available scanners."""
        # Create shared scanner instances to avoid duplicates
        trivy_scanner = TrivyScanner(self.config)  # Shared for Container and SCA
        
        # DAST scanners
        self._scanners[ScanType.DAST] = [
            ZAPScanner(self.config),
            NucleiScanner(self.config)
        ]
        
        # SAST scanners
        self._scanners[ScanType.SAST] = [
            CodeQLScanner(self.config),
            BanditScanner(self.config),
            SemgrepScanner(self.config)
        ]
        
        # IaC scanners
        self._scanners[ScanType.IAC] = [
            CheckovScanner(self.config)
        ]
        
        # Container scanners
        self._scanners[ScanType.CONTAINER] = [
            trivy_scanner  # Reuse shared instance
        ]
        
        # Secrets scanners
        self._scanners[ScanType.SECRETS] = [
            GitLeaksScanner(self.config)
        ]
        
        # SCA scanners (Trivy handles both container and dependency scanning)
        self._scanners[ScanType.SCA] = [
            SafetyScanner(self.config),
            trivy_scanner  # Reuse shared instance for SCA
        ]
    
    async def run_scan(self, request: ScanRequest) -> ScanResult:
        """
        Execute a comprehensive security scan.
        
        Args:
            request: Scan request with target and options
            
        Returns:
            ScanResult with all findings and metrics
        """
        scan_id = request.scan_id
        start_time = utc_now()
        
        logger.info(f"Starting scan {scan_id} for target: {request.target}")
        
        # Track active scan
        self._active_scans[scan_id] = {
            "status": "running",
            "start_time": start_time,
            "target": request.target
        }
        
        try:
            # Collect scanners to run
            scanners_to_run = self._get_scanners_for_types(request.scan_types)
            
            # Check scanner availability
            available_scanners = await self._check_scanner_availability(scanners_to_run)
            
            if not available_scanners:
                raise ScannerError("No scanners available for requested scan types")
            
            # Run scans in parallel
            all_findings = await self._run_parallel_scans(
                available_scanners, 
                request.target, 
                scan_id,
                request.options
            )
            
            # Apply suppressions
            if self.suppression_engine:
                all_findings = self.suppression_engine.apply(all_findings)
            
            # Deduplicate findings
            unique_findings = self._deduplicate_findings(all_findings)
            
            # Calculate metrics
            end_time = utc_now()
            metrics = self._calculate_metrics(unique_findings, start_time, end_time)
            
            # Build result
            result = ScanResult(
                scan_id=scan_id,
                target=request.target,
                status="completed",
                findings=unique_findings,
                metrics=metrics,
                start_time=start_time,
                end_time=end_time,
                scanners_used=[s.SCANNER_NAME for s in available_scanners]
            )
            
            self._active_scans[scan_id]["status"] = "completed"
            
            logger.info(
                f"Scan {scan_id} completed: {len(unique_findings)} findings "
                f"in {metrics.duration_seconds:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self._active_scans[scan_id]["status"] = "failed"
            self._active_scans[scan_id]["error"] = str(e)
            logger.error(f"Scan {scan_id} failed: {e}")
            
            return ScanResult(
                scan_id=scan_id,
                target=request.target,
                status="failed",
                findings=[],
                metrics=ScanMetrics(),
                start_time=start_time,
                end_time=utc_now(),
                error=str(e)
            )
        
        finally:
            # Cleanup
            if scan_id in self._active_scans:
                del self._active_scans[scan_id]
    
    async def run_quick_scan(self, target: str, scan_id: str = None) -> ScanResult:
        """Run a quick scan with essential scanners only."""
        request = ScanRequest(
            target=target,
            scan_types=[ScanType.SAST, ScanType.SECRETS],
            scan_id=scan_id,
            options={"quick": True}
        )
        return await self.run_scan(request)
    
    async def run_full_scan(self, target: str, scan_id: str = None) -> ScanResult:
        """Run a comprehensive scan with all scanner types."""
        request = ScanRequest(
            target=target,
            scan_types=list(ScanType),
            scan_id=scan_id,
            options={"full": True}
        )
        return await self.run_scan(request)
    
    def _get_scanners_for_types(self, scan_types: List[ScanType]) -> List[BaseScanner]:
        """Get all scanners for the requested scan types."""
        scanners = []
        seen = set()
        
        for scan_type in scan_types:
            for scanner in self._scanners.get(scan_type, []):
                # Avoid duplicates (e.g., Trivy appears in multiple categories)
                scanner_key = f"{scanner.SCANNER_NAME}"
                if scanner_key not in seen:
                    scanners.append(scanner)
                    seen.add(scanner_key)
        
        return scanners
    
    async def _check_scanner_availability(
        self, 
        scanners: List[BaseScanner]
    ) -> List[BaseScanner]:
        """Check which scanners are available."""
        available = []
        
        availability_checks = [
            (scanner, scanner.is_available()) 
            for scanner in scanners
        ]
        
        for scanner, check in availability_checks:
            try:
                is_available = await check
                if is_available:
                    available.append(scanner)
                    logger.debug(f"Scanner {scanner.SCANNER_NAME} is available")
                else:
                    logger.warning(f"Scanner {scanner.SCANNER_NAME} is not available")
            except Exception as e:
                logger.warning(f"Scanner {scanner.SCANNER_NAME} availability check failed: {e}")
        
        return available
    
    async def _run_parallel_scans(
        self,
        scanners: List[BaseScanner],
        target: str,
        scan_id: str,
        options: Dict[str, Any]
    ) -> List[Finding]:
        """Run multiple scanners in parallel."""
        all_findings = []
        
        # Create scan tasks
        tasks = []
        for scanner in scanners:
            task = self._run_scanner_with_timeout(
                scanner, target, scan_id, options
            )
            tasks.append((scanner.SCANNER_NAME, task))
        
        # Run all tasks
        for scanner_name, task in tasks:
            try:
                findings = await task
                all_findings.extend(findings)
                logger.info(f"{scanner_name}: Found {len(findings)} findings")
            except ScanTimeoutError:
                logger.warning(f"{scanner_name}: Scan timed out")
            except Exception as e:
                logger.error(f"{scanner_name}: Scan failed - {e}")
        
        return all_findings
    
    async def _run_scanner_with_timeout(
        self,
        scanner: BaseScanner,
        target: str,
        scan_id: str,
        options: Dict[str, Any]
    ) -> List[Finding]:
        """Run a scanner with timeout."""
        timeout = options.get('timeout', self.config.scan_timeout)
        
        try:
            return await asyncio.wait_for(
                scanner.scan(target, scan_id, **options),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise ScanTimeoutError(
                f"{scanner.SCANNER_NAME} scan timed out after {timeout}s"
            )
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings."""
        seen = set()
        unique = []
        
        for finding in findings:
            # Create fingerprint for deduplication
            fingerprint = (
                finding.rule_id,
                finding.location.get("file", ""),
                finding.location.get("line", finding.location.get("line_start", 0)),
                finding.title
            )
            
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique.append(finding)
        
        return unique
    
    def _calculate_metrics(
        self, 
        findings: List[Finding], 
        start_time: datetime,
        end_time: datetime
    ) -> ScanMetrics:
        """Calculate scan metrics."""
        duration = (end_time - start_time).total_seconds()
        
        # Count by severity
        severity_counts = {sev: 0 for sev in Severity}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        # Count by source
        source_counts = {}
        for finding in findings:
            source_counts[finding.source] = source_counts.get(finding.source, 0) + 1
        
        return ScanMetrics(
            total_findings=len(findings),
            critical=severity_counts.get(Severity.CRITICAL, 0),
            high=severity_counts.get(Severity.HIGH, 0),
            medium=severity_counts.get(Severity.MEDIUM, 0),
            low=severity_counts.get(Severity.LOW, 0),
            informational=severity_counts.get(Severity.INFORMATIONAL, 0),
            duration_seconds=duration,
            findings_by_source=source_counts
        )
    
    async def get_scanner_status(self) -> Dict[str, Any]:
        """Get status of all configured scanners."""
        status = {}
        
        all_scanners = set()
        for scanners in self._scanners.values():
            for scanner in scanners:
                all_scanners.add(scanner)
        
        for scanner in all_scanners:
            try:
                is_available = await scanner.is_available()
                version = await scanner.get_version() if is_available else "N/A"
                status[scanner.SCANNER_NAME] = {
                    "available": is_available,
                    "version": version,
                    "scan_types": [
                        st.value for st, scanners in self._scanners.items() 
                        if scanner in scanners
                    ]
                }
            except Exception as e:
                status[scanner.SCANNER_NAME] = {
                    "available": False,
                    "error": str(e)
                }
        
        return status
    
    def get_active_scans(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active scans."""
        return dict(self._active_scans)
