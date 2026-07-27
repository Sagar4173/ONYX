"""
Base Scanner Abstract Class
============================

Defines the interface that all scanners must implement.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..base.config import ScanConfig
from ..base.exceptions import ScanTimeoutError
from ..base.models import Finding, ScanType, Severity

logger = logging.getLogger(__name__)


class BaseScanner(ABC):
    """
    Abstract base class for all security scanners.
    
    All scanner implementations should inherit from this class and implement
    the abstract methods to ensure consistent behavior across scanners.
    """
    
    # Scanner metadata - override in subclasses
    SCANNER_NAME: str = "base"
    SCANNER_TYPE: ScanType = ScanType.SAST
    SUPPORTED_LANGUAGES: List[str] = []
    
    def __init__(self, config: ScanConfig = None):
        """
        Initialize the scanner with configuration.
        
        Args:
            config: Scanner configuration. If None, uses defaults.
        """
        self.config = config or ScanConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.SCANNER_NAME}")
    
    @abstractmethod
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform a security scan on the target.
        
        Args:
            target: Path to repository or URL to scan
            scan_id: Unique identifier for this scan
            **kwargs: Additional scanner-specific arguments
            
        Returns:
            List of Finding objects discovered during the scan
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the scanner is available and properly configured.
        
        Returns:
            True if scanner is ready to use, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_version(self) -> str:
        """
        Get the version of the scanner tool.
        
        Returns:
            Version string or "unknown" if not available
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the scanner.
        
        Returns:
            Dictionary with health status information
        """
        try:
            is_available = await self.is_available()
            version = await self.get_version() if is_available else "N/A"
            
            return {
                "scanner": self.SCANNER_NAME,
                "type": self.SCANNER_TYPE.value,
                "available": is_available,
                "version": version,
                "status": "healthy" if is_available else "unavailable"
            }
        except Exception as e:
            return {
                "scanner": self.SCANNER_NAME,
                "type": self.SCANNER_TYPE.value,
                "available": False,
                "version": "N/A",
                "status": "error",
                "error": str(e)
            }
    
    async def run_with_timeout(
        self,
        coro,
        timeout: int = None,
        error_message: str = "Scan timed out"
    ):
        """
        Run a coroutine with a timeout.
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds (uses config default if None)
            error_message: Message for timeout exception
            
        Returns:
            Result of the coroutine
            
        Raises:
            ScanTimeoutError: If the operation times out
        """
        timeout = timeout or self.config.scan_timeout
        
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise ScanTimeoutError(
                scanner_name=self.SCANNER_NAME,
                timeout_seconds=timeout,
                message=error_message
            )
    
    async def run_command(
        self,
        cmd: List[str],
        cwd: str = None,
        timeout: int = None
    ) -> tuple:
        """
        Run a command asynchronously.
        
        Args:
            cmd: Command and arguments as a list
            cwd: Working directory for the command
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        timeout = timeout or self.config.scan_timeout
        
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return stdout.decode(), stderr.decode(), process.returncode
            
        except asyncio.TimeoutError:
            if 'process' in locals():
                process.kill()
                await process.wait()
            raise ScanTimeoutError(
                scanner_name=self.SCANNER_NAME,
                timeout_seconds=timeout
            )
    
    def normalize_severity(self, raw_severity: str) -> Severity:
        """
        Normalize severity string to Severity enum.
        
        Override in subclasses for scanner-specific mappings.
        
        Args:
            raw_severity: Raw severity string from scanner output
            
        Returns:
            Normalized Severity enum value
        """
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "moderate": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
            "informational": Severity.INFO,
            "warning": Severity.MEDIUM,
        }
        
        normalized = raw_severity.lower().strip()
        return severity_map.get(normalized, Severity.MEDIUM)
    
    def log_scan_start(self, target: str, scan_id: str):
        """Log the start of a scan."""
        self.logger.info(f"🔍 Starting {self.SCANNER_NAME} scan [{scan_id}] on {target}")
    
    def log_scan_complete(self, scan_id: str, findings_count: int, duration: float):
        """Log the completion of a scan."""
        self.logger.info(
            f"✅ {self.SCANNER_NAME} scan [{scan_id}] completed: "
            f"{findings_count} findings in {duration:.2f}s"
        )
    
    def log_scan_error(self, scan_id: str, error: Exception):
        """Log a scan error."""
        self.logger.error(f"❌ {self.SCANNER_NAME} scan [{scan_id}] failed: {error}")
