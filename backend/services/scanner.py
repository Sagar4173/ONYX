"""
Security scanner service for running multiple vulnerability scanners
"""
import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import shutil

from models.report import ScanResult, ScannerType, ScanStatus, VulnerabilityFinding
from utils.result_parser import result_parser
from config import settings

logger = logging.getLogger(__name__)


class ScannerError(Exception):
    """Custom exception for scanner errors"""
    pass


class SecurityScanner:
    """Main security scanner orchestrator"""
    
    def __init__(self):
        self.scanners = {
            ScannerType.SEMGREP: SemgrepScanner(),
            ScannerType.TRIVY: TrivyScanner(),
            ScannerType.GITLEAKS: GitLeaksScanner(),
            ScannerType.LYNIS: LynisScanner()
        }
    
    async def run_all_scans(
        self,
        repo_path: str,
        selected_scanners: Optional[List[ScannerType]] = None
    ) -> List[ScanResult]:
        """
        Run all enabled security scanners on the repository
        
        Args:
            repo_path: Path to the repository to scan
            selected_scanners: List of scanners to run (if None, run all)
            
        Returns:
            List of scan results
        """
        if selected_scanners is None:
            selected_scanners = list(self.scanners.keys())
        
        logger.info(f"Starting security scans on {repo_path} with scanners: {selected_scanners}")
        
        # Run scanners concurrently
        tasks = []
        for scanner_type in selected_scanners:
            if scanner_type in self.scanners:
                task = self._run_single_scanner(scanner_type, repo_path)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        scan_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scanner_type = selected_scanners[i]
                logger.error(f"Scanner {scanner_type.value} failed: {result}")
                # Create failed scan result
                scan_result = ScanResult(
                    scanner=scanner_type,
                    status=ScanStatus.FAILED,
                    error_message=str(result),
                    completed_at=datetime.now(timezone.utc)
                )
                scan_results.append(scan_result)
            else:
                scan_results.append(result)
        
        logger.info(f"Completed {len(scan_results)} scans")
        return scan_results
    
    async def _run_single_scanner(
        self,
        scanner_type: ScannerType,
        repo_path: str
    ) -> ScanResult:
        """Run a single scanner and return results"""
        scanner = self.scanners[scanner_type]
        
        scan_result = ScanResult(
            scanner=scanner_type,
            status=ScanStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )
        
        try:
            logger.info(f"Starting {scanner_type.value} scan")
            
            # Check if scanner is available
            if not await scanner.is_available():
                raise ScannerError(f"{scanner_type.value} is not available")
            
            # Run the scan
            output = await scanner.scan(repo_path)
            
            # Parse results
            findings = result_parser.parse_results(scanner_type, output)
            
            # Update scan result
            scan_result.status = ScanStatus.COMPLETED
            scan_result.completed_at = datetime.now(timezone.utc)
            scan_result.duration_seconds = (
                scan_result.completed_at - scan_result.started_at
            ).total_seconds()
            scan_result.findings = findings
            scan_result.raw_output = output
            scan_result.summary = result_parser.get_summary_stats(findings)
            
            logger.info(f"{scanner_type.value} scan completed with {len(findings)} findings")
            
        except Exception as e:
            scan_result.status = ScanStatus.FAILED
            scan_result.completed_at = datetime.now(timezone.utc)
            scan_result.error_message = str(e)
            logger.error(f"{scanner_type.value} scan failed: {e}")
        
        return scan_result
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health status of all scanners"""
        health_status = {}
        
        for scanner_type, scanner in self.scanners.items():
            try:
                is_healthy = await scanner.is_available()
                health_status[scanner_type.value] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {scanner_type.value}: {e}")
                health_status[scanner_type.value] = False
        
        return health_status


class BaseScannerRunner:
    """Base class for individual scanner runners"""
    
    def __init__(self, scanner_type: ScannerType, executable_path: str):
        self.scanner_type = scanner_type
        self.executable_path = executable_path
    
    async def is_available(self) -> bool:
        """Check if scanner is available and working"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.executable_path,
                '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"{self.scanner_type.value} availability check failed: {e}")
            return False
    
    async def run_command(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        timeout: int = 600
    ) -> str:
        """Run scanner command and return output"""
        try:
            cmd = [self.executable_path] + args
            logger.debug(f"Running command: {' '.join(cmd)}")
            
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
            
            output = stdout.decode('utf-8', errors='ignore')
            error_output = stderr.decode('utf-8', errors='ignore')
            
            if process.returncode != 0 and not output:
                raise ScannerError(f"Command failed with return code {process.returncode}: {error_output}")
            
            return output
            
        except asyncio.TimeoutError:
            raise ScannerError(f"Scanner timeout after {timeout} seconds")
        except Exception as e:
            raise ScannerError(f"Scanner execution failed: {e}")
    
    async def scan(self, repo_path: str) -> str:
        """Run scanner on repository - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement scan method")


class SemgrepScanner(BaseScannerRunner):
    """Semgrep static analysis scanner"""
    
    def __init__(self):
        super().__init__(ScannerType.SEMGREP, settings.semgrep_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run Semgrep scan"""
        args = [
            '--config=auto',  # Use community rules
            '--json',
            '--quiet',
            '--no-git-ignore',
            '--max-target-bytes=1000000',  # 1MB max file size
            repo_path
        ]
        
        return await self.run_command(args, timeout=settings.git_scan_timeout)


class TrivyScanner(BaseScannerRunner):
    """Trivy vulnerability scanner"""
    
    def __init__(self):
        super().__init__(ScannerType.TRIVY, settings.trivy_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run Trivy scan"""
        args = [
            'fs',
            '--format', 'json',
            '--quiet',
            '--skip-update',
            repo_path
        ]
        
        return await self.run_command(args, timeout=settings.git_scan_timeout)


class GitLeaksScanner(BaseScannerRunner):
    """GitLeaks secret scanner"""
    
    def __init__(self):
        super().__init__(ScannerType.GITLEAKS, settings.gitleaks_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run GitLeaks scan"""
        # Create temporary config for JSON output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            args = [
                'detect',
                '--source', repo_path,
                '--report-format', 'json',
                '--report-path', output_file,
                '--no-git',
                '--verbose'
            ]
            
            # Run the command (it may exit with code 1 if leaks found)
            try:
                await self.run_command(args, timeout=settings.git_scan_timeout)
            except ScannerError as e:
                # GitLeaks exits with 1 when leaks are found, check if output file exists
                if not Path(output_file).exists():
                    raise e
            
            # Read the output file
            with open(output_file, 'r') as f:
                output = f.read()
            
            return output or '[]'  # Return empty array if no output
            
        finally:
            # Clean up temp file
            try:
                os.unlink(output_file)
            except Exception:
                pass


class LynisScanner(BaseScannerRunner):
    """Lynis system security scanner"""
    
    def __init__(self):
        super().__init__(ScannerType.LYNIS, settings.lynis_path)
    
    async def is_available(self) -> bool:
        """Lynis availability check"""
        try:
            # Lynis might not support --version flag
            process = await asyncio.create_subprocess_exec(
                self.executable_path,
                '--help',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            return process.returncode == 0 or 'Lynis' in stdout.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Lynis availability check failed: {e}")
            return False
    
    async def scan(self, repo_path: str) -> str:
        """Run Lynis scan (limited scope for repository analysis)"""
        # Create temporary directory for Lynis output
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'lynis.log'
            
            args = [
                'audit', 'system',
                '--quick',
                '--quiet',
                '--no-colors',
                '--logfile', str(log_file)
            ]
            
            try:
                # Run Lynis (may exit with various codes)
                await self.run_command(args, timeout=settings.git_scan_timeout)
            except ScannerError:
                # Lynis often exits with non-zero codes, check if log exists
                pass
            
            # Read the log file if it exists
            if log_file.exists():
                with open(log_file, 'r') as f:
                    return f.read()
            else:
                return ''


# Global scanner instance
security_scanner = SecurityScanner()
