"""
Enhanced security scanner service for running multiple vulnerability scanners
with advanced features like custom rules, caching, and comprehensive reporting
"""
import asyncio
import json
import logging
import os
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import hashlib
import toml

from models.report import ScanResult, ScannerType, ScanStatus, VulnerabilityFinding
from utils.result_parser import result_parser
from config import settings

logger = logging.getLogger(__name__)


class ScannerError(Exception):
    """Custom exception for scanner errors"""
    pass


class SecurityScanner:
    """Enhanced security scanner orchestrator with advanced features"""
    
    def __init__(self):
        self.scanners = {
            ScannerType.SEMGREP: EnhancedSemgrepScanner(),
            ScannerType.TRIVY: EnhancedTrivyScanner(),
            ScannerType.GITLEAKS: EnhancedGitLeaksScanner(),
            ScannerType.LYNIS: EnhancedLynisScanner(),
            ScannerType.BANDIT: BanditScanner(),
            ScannerType.SAFETY: SafetyScanner()
        }
        self._setup_cache_directories()
    
    def _setup_cache_directories(self):
        """Setup cache directories for scanners"""
        try:
            # Trivy cache directory
            os.makedirs(settings.trivy_cache_dir, exist_ok=True)
            
            # Temp directory for scanner outputs
            os.makedirs(settings.temp_dir, exist_ok=True)
            
        except Exception as e:
            logger.warning(f"Failed to setup cache directories: {e}")
    
    async def run_all_scans(
        self,
        repo_path: str,
        selected_scanners: Optional[List[ScannerType]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> List[ScanResult]:
        """
        Run all enabled security scanners on the repository
        
        Args:
            repo_path: Path to the repository to scan
            selected_scanners: List of scanners to run (if None, run all enabled)
            custom_config: Custom configuration for scanners
            
        Returns:
            List of scan results
        """
        if selected_scanners is None:
            # Only run enabled scanners
            selected_scanners = [
                scanner_type for scanner_type in self.scanners.keys()
                if self._is_scanner_enabled(scanner_type)
            ]
        
        logger.info(f"Starting security scans on {repo_path} with scanners: {selected_scanners}")
        
        # Apply custom configuration if provided
        if custom_config:
            await self._apply_custom_config(custom_config)
        
        # Run scanners concurrently with rate limiting
        semaphore = asyncio.Semaphore(settings.max_concurrent_scans)
        tasks = []
        
        for scanner_type in selected_scanners:
            if scanner_type in self.scanners:
                task = self._run_single_scanner_with_semaphore(
                    semaphore, scanner_type, repo_path
                )
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
    
    def _is_scanner_enabled(self, scanner_type: ScannerType) -> bool:
        """Check if a scanner is enabled in configuration"""
        scanner_config_map = {
            ScannerType.SEMGREP: settings.enable_semgrep,
            ScannerType.TRIVY: settings.enable_trivy,
            ScannerType.GITLEAKS: settings.enable_gitleaks,
            ScannerType.LYNIS: settings.enable_lynis,
            ScannerType.BANDIT: settings.enable_bandit,
            ScannerType.SAFETY: settings.enable_safety
        }
        return scanner_config_map.get(scanner_type, False)
    
    async def _apply_custom_config(self, custom_config: Dict[str, Any]):
        """Apply custom configuration to scanners"""
        for scanner_type_str, config in custom_config.items():
            try:
                scanner_type = ScannerType(scanner_type_str)
                if scanner_type in self.scanners:
                    scanner = self.scanners[scanner_type]
                    if hasattr(scanner, 'apply_custom_config'):
                        await scanner.apply_custom_config(config)
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to apply custom config for {scanner_type_str}: {e}")
    
    async def _run_single_scanner_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        scanner_type: ScannerType,
        repo_path: str
    ) -> ScanResult:
        """Run a single scanner with concurrency control"""
    
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
            
            # Prepare context for enhanced analysis
            repository_context = {
                'path': repo_path,
                'scanner_type': scanner_type.value,
                'scan_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            business_context = {
                'environment': 'production',  # This could be parameterized
                'data_classification': 'medium',  # This could be detected
                'compliance_requirements': ['SOC2', 'GDPR']  # This could be configured
            }
            
            # Parse results with enhanced context
            findings = result_parser.parse_results(
                scanner_type, 
                output, 
                repository_context=repository_context,
                business_context=business_context
            )
            
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
    
    async def update_scanner_databases(self) -> Dict[str, bool]:
        """Update scanner databases (like Trivy)"""
        update_status = {}
        
        # Update Trivy database
        if ScannerType.TRIVY in self.scanners:
            try:
                trivy_scanner = self.scanners[ScannerType.TRIVY]
                await trivy_scanner.update_database()
                update_status["trivy"] = True
            except Exception as e:
                logger.error(f"Failed to update Trivy database: {e}")
                update_status["trivy"] = False
        
        return update_status


class BaseScannerRunner:
    """Enhanced base class for individual scanner runners"""
    
    def __init__(self, scanner_type: ScannerType, executable_path: str):
        self.scanner_type = scanner_type
        self.executable_path = executable_path
        self.custom_config = {}
    
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
        timeout: int = 600,
        env: Optional[Dict[str, str]] = None
    ) -> str:
        """Run scanner command and return output"""
        try:
            cmd = [self.executable_path] + args
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            # Merge environment variables
            command_env = os.environ.copy()
            if env:
                command_env.update(env)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=command_env
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
    
    async def apply_custom_config(self, config: Dict[str, Any]):
        """Apply custom configuration to the scanner"""
        self.custom_config.update(config)


class EnhancedSemgrepScanner(BaseScannerRunner):
    """Enhanced Semgrep static analysis scanner with custom rules support"""
    
    def __init__(self):
        super().__init__(ScannerType.SEMGREP, settings.semgrep_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run enhanced Semgrep scan with custom rules"""
        args = [
            '--json',
            '--quiet',
            '--no-git-ignore',
            '--max-target-bytes=1000000',  # 1MB max file size
            '--timeout=300',
            '--max-memory=2000',  # 2GB memory limit
        ]
        
        # Use custom rules repo if configured
        if settings.custom_semgrep_rules_repo:
            args.extend(['--config', settings.custom_semgrep_rules_repo])
        else:
            # Use security-focused rulesets
            args.extend([
                '--config=p/security-audit',  # General security rules
                '--config=p/owasp-top-ten',   # OWASP Top 10
                '--config=p/cwe-top-25',      # CWE Top 25
            ])
        
        # Add custom config from apply_custom_config if available
        if 'additional_rules' in self.custom_config:
            for rule in self.custom_config['additional_rules']:
                args.extend(['--config', rule])
        
        args.append(repo_path)
        
        return await self.run_command(args, timeout=settings.git_scan_timeout)


class EnhancedTrivyScanner(BaseScannerRunner):
    """Enhanced Trivy vulnerability scanner with caching"""
    
    def __init__(self):
        super().__init__(ScannerType.TRIVY, settings.trivy_path)
        self.last_db_update = None
    
    async def scan(self, repo_path: str) -> str:
        """Run enhanced Trivy scan with caching"""
        # Check if we need to update the database
        await self._ensure_database_updated()
        
        args = [
            'fs',
            '--format', 'json',
            '--quiet',
            '--cache-dir', settings.trivy_cache_dir,
            '--skip-update',  # We handle updates separately
            '--security-checks', 'vuln,secret,config',
            '--severity', 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL',
            repo_path
        ]
        
        # Add custom scanner options
        if 'skip_files' in self.custom_config:
            args.extend(['--skip-files', self.custom_config['skip_files']])
        
        return await self.run_command(args, timeout=settings.git_scan_timeout)
    
    async def _ensure_database_updated(self):
        """Ensure Trivy database is updated within the configured interval"""
        now = datetime.now(timezone.utc)
        
        if (self.last_db_update is None or 
            (now - self.last_db_update).total_seconds() > settings.trivy_db_update_interval * 3600):
            
            try:
                await self.update_database()
                self.last_db_update = now
            except Exception as e:
                logger.warning(f"Failed to update Trivy database: {e}")
    
    async def update_database(self):
        """Update Trivy vulnerability database"""
        args = [
            'image',
            '--download-db-only',
            '--cache-dir', settings.trivy_cache_dir
        ]
        
        await self.run_command(args, timeout=300)  # 5 minutes timeout
        logger.info("Trivy database updated successfully")


class EnhancedGitLeaksScanner(BaseScannerRunner):
    """Enhanced GitLeaks secret scanner with custom configuration"""
    
    def __init__(self):
        super().__init__(ScannerType.GITLEAKS, settings.gitleaks_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run enhanced GitLeaks scan with custom config"""
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
            
            # Use custom gitleaks config if available
            config_file = None
            if settings.custom_gitleaks_config:
                args.extend(['--config', settings.custom_gitleaks_config])
            elif 'custom_config' in self.custom_config:
                # Create temporary config file
                config_file = await self._create_custom_config()
                args.extend(['--config', config_file])
            
            # Run the command (it may exit with code 1 if leaks found)
            try:
                await self.run_command(args, timeout=settings.git_scan_timeout)
            except ScannerError as e:
                # GitLeaks exits with 1 when leaks are found, check if output file exists
                if not Path(output_file).exists():
                    raise e
            
            # Read and redact the output file for security
            with open(output_file, 'r') as f:
                output = f.read()
            
            # Redact secrets in the output to prevent log leakage
            redacted_output = self._redact_secrets(output)
            
            return redacted_output or '[]'  # Return empty array if no output
            
        finally:
            # Clean up temp files
            for temp_file in [output_file, config_file]:
                if temp_file:
                    try:
                        os.unlink(temp_file)
                    except Exception:
                        pass
    
    async def _create_custom_config(self) -> str:
        """Create custom gitleaks configuration file"""
        config = self.custom_config.get('custom_config', {})
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            toml.dump(config, f)
            return f.name
    
    def _redact_secrets(self, output: str) -> str:
        """Redact detected secrets from the output to prevent log leakage"""
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for finding in data:
                    if 'Secret' in finding:
                        # Replace the actual secret with placeholder
                        finding['Secret'] = '[REDACTED]'
                    if 'Match' in finding:
                        finding['Match'] = '[REDACTED]'
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return output


class EnhancedLynisScanner(BaseScannerRunner):
    """Enhanced Lynis system security scanner for baseline security"""
    
    def __init__(self):
        super().__init__(ScannerType.LYNIS, settings.lynis_path)
    
    async def is_available(self) -> bool:
        """Enhanced Lynis availability check"""
        try:
            # Lynis might not support --version flag, try --help
            process = await asyncio.create_subprocess_exec(
                self.executable_path,
                '--help',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            output = stdout.decode('utf-8', errors='ignore')
            return process.returncode == 0 or 'Lynis' in output
        except Exception as e:
            logger.error(f"Lynis availability check failed: {e}")
            return False
    
    async def scan(self, repo_path: str) -> str:
        """Run enhanced Lynis scan for baseline security assessment"""
        # Create temporary directory for Lynis output
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'lynis.log'
            report_file = Path(temp_dir) / 'lynis-report.dat'
            
            args = [
                'audit', 'system',
                '--quick',
                '--quiet',
                '--no-colors',
                '--logfile', str(log_file),
                '--reportfile', str(report_file)
            ]
            
            # Add custom audit categories if configured
            if 'audit_categories' in self.custom_config:
                for category in self.custom_config['audit_categories']:
                    args.extend(['--tests-category', category])
            
            try:
                # Run Lynis (may exit with various codes)
                await self.run_command(args, timeout=settings.git_scan_timeout)
            except ScannerError:
                # Lynis often exits with non-zero codes, check if files exist
                pass
            
            # Combine log and report data
            result_data = {
                "log": "",
                "report": "",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if log_file.exists():
                with open(log_file, 'r') as f:
                    result_data["log"] = f.read()
            
            if report_file.exists():
                with open(report_file, 'r') as f:
                    result_data["report"] = f.read()
            
            return json.dumps(result_data)


class BanditScanner(BaseScannerRunner):
    """Bandit Python-specific SAST scanner"""
    
    def __init__(self):
        super().__init__(ScannerType.BANDIT, settings.bandit_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run Bandit scan for Python security anti-patterns"""
        args = [
            '-r', repo_path,
            '-f', 'json',
            '--quiet',
            '--confidence-level=low',  # Include low confidence findings
            '--severity-level=low',    # Include low severity findings
        ]
        
        # Add custom config if available
        if 'exclude_paths' in self.custom_config:
            args.extend(['--exclude', ','.join(self.custom_config['exclude_paths'])])
        
        if 'skip_tests' in self.custom_config and self.custom_config['skip_tests']:
            args.extend(['--skip', 'B101'])  # Skip assert_used test
        
        return await self.run_command(args, timeout=settings.git_scan_timeout)


class SafetyScanner(BaseScannerRunner):
    """Safety Python dependency vulnerability scanner"""
    
    def __init__(self):
        super().__init__(ScannerType.SAFETY, settings.safety_path)
    
    async def scan(self, repo_path: str) -> str:
        """Run Safety scan for Python dependency vulnerabilities"""
        # Look for Python dependency files
        dependency_files = self._find_dependency_files(repo_path)
        
        if not dependency_files:
            logger.info("No Python dependency files found, skipping Safety scan")
            return json.dumps({"vulnerabilities": [], "message": "No dependency files found"})
        
        results = {"vulnerabilities": [], "scanned_files": []}
        
        for dep_file in dependency_files:
            try:
                args = [
                    'check',
                    '--json',
                    '--file', dep_file
                ]
                
                # Add custom options
                if 'ignore_ids' in self.custom_config:
                    for ignore_id in self.custom_config['ignore_ids']:
                        args.extend(['--ignore', ignore_id])
                
                output = await self.run_command(args, timeout=300)
                
                # Parse and combine results
                file_results = json.loads(output) if output else []
                if file_results:
                    results["vulnerabilities"].extend(file_results)
                results["scanned_files"].append(dep_file)
                
            except Exception as e:
                logger.warning(f"Safety scan failed for {dep_file}: {e}")
        
        return json.dumps(results)
    
    def _find_dependency_files(self, repo_path: str) -> List[str]:
        """Find Python dependency files in the repository"""
        dependency_files = []
        search_patterns = [
            'requirements*.txt',
            'pyproject.toml',
            'poetry.lock',
            'Pipfile.lock'
        ]
        
        repo_path_obj = Path(repo_path)
        for pattern in search_patterns:
            for file_path in repo_path_obj.rglob(pattern):
                dependency_files.append(str(file_path))
        
        return dependency_files


# Global scanner instance
security_scanner = SecurityScanner()
