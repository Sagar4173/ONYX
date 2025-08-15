"""
CodeQL and Checkov Advanced Security Scanners
Part 2 of Advanced Security Scanning implementation
"""
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .advanced_scanners import (
    ScannerType, ScanSeverity, ScanFinding, ScanResult, AdvancedScannerConfig
)

logger = logging.getLogger(__name__)


class CodeQLScanner:
    """CodeQL static analysis scanner for code security"""
    
    def __init__(self, codeql_path: str = "codeql"):
        self.codeql_path = codeql_path
        self.database_dir = None
        self.queries_dir = None
    
    async def scan_repository(self, repo_path: str, language: str, config: AdvancedScannerConfig) -> ScanResult:
        """Run CodeQL analysis on repository"""
        scan_id = f"codeql_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        try:
            # Create temporary database directory
            self.database_dir = tempfile.mkdtemp(prefix="codeql_db_")
            database_path = Path(self.database_dir) / "database"
            
            # Create CodeQL database
            await self._create_database(repo_path, language, database_path, config)
            
            # Run queries
            results_file = await self._run_queries(database_path, language, config)
            
            # Parse SARIF output
            findings = await self._parse_sarif_output(results_file, repo_path)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScanResult(
                scanner=ScannerType.CODEQL,
                target=repo_path,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=duration,
                findings=findings,
                metadata={
                    "codeql_version": await self._get_codeql_version(),
                    "language": language,
                    "database_size": self._get_directory_size(database_path)
                }
            )
            
        except Exception as e:
            logger.error(f"CodeQL scan error: {e}")
            return ScanResult(
                scanner=ScannerType.CODEQL,
                target=repo_path,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                status="failed",
                error_message=str(e)
            )
        finally:
            if self.database_dir and Path(self.database_dir).exists():
                shutil.rmtree(self.database_dir)
    
    async def _create_database(self, repo_path: str, language: str, database_path: Path, config: AdvancedScannerConfig):
        """Create CodeQL database from repository"""
        cmd = [
            self.codeql_path,
            "database", "create",
            str(database_path),
            "--language", language,
            "--source-root", repo_path
        ]
        
        # Add build command if specified
        if "build_command" in config.custom_config:
            cmd.extend(["--command", config.custom_config["build_command"]])
        
        logger.info(f"Creating CodeQL database: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Database creation failed"
            raise Exception(f"CodeQL database creation failed: {error_msg}")
    
    async def _run_queries(self, database_path: Path, language: str, config: AdvancedScannerConfig) -> Path:
        """Run CodeQL queries against database"""
        results_file = database_path.parent / "results.sarif"
        
        # Determine query suite to use
        query_suite = config.custom_config.get("query_suite", f"{language}-security-and-quality")
        
        cmd = [
            self.codeql_path,
            "database", "analyze",
            str(database_path),
            query_suite,
            "--format", "sarif-latest",
            "--output", str(results_file)
        ]
        
        # Add additional options
        if "threads" in config.custom_config:
            cmd.extend(["--threads", str(config.custom_config["threads"])])
        
        if "ram" in config.custom_config:
            cmd.extend(["--ram", str(config.custom_config["ram"])])
        
        logger.info(f"Running CodeQL analysis: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=config.timeout_seconds
            )
        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"CodeQL analysis timed out after {config.timeout_seconds} seconds")
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Analysis failed"
            raise Exception(f"CodeQL analysis failed: {error_msg}")
        
        return results_file
    
    async def _parse_sarif_output(self, sarif_file: Path, repo_path: str) -> List[ScanFinding]:
        """Parse CodeQL SARIF output into ScanFindings"""
        findings = []
        
        try:
            with open(sarif_file, 'r') as f:
                sarif_data = json.load(f)
            
            for run in sarif_data.get('runs', []):
                for result in run.get('results', []):
                    finding = self._convert_sarif_result(result, repo_path, run)
                    if finding:
                        findings.append(finding)
        except Exception as e:
            logger.error(f"Failed to parse SARIF output: {e}")
        
        return findings
    
    def _convert_sarif_result(self, result: Dict, repo_path: str, run: Dict) -> Optional[ScanFinding]:
        """Convert SARIF result to ScanFinding"""
        try:
            rule_id = result.get('ruleId', 'unknown')
            rule_index = result.get('ruleIndex', 0)
            
            # Get rule info from run
            rules = run.get('tool', {}).get('driver', {}).get('rules', [])
            rule_info = rules[rule_index] if rule_index < len(rules) else {}
            
            # Get location info
            locations = result.get('locations', [])
            file_path = None
            line_number = None
            
            if locations:
                physical_location = locations[0].get('physicalLocation', {})
                artifact_location = physical_location.get('artifactLocation', {})
                file_path = artifact_location.get('uri', '')
                
                region = physical_location.get('region', {})
                line_number = region.get('startLine')
            
            return ScanFinding(
                id=f"codeql_{rule_id}",
                title=rule_info.get('shortDescription', {}).get('text', result.get('message', {}).get('text', 'Unknown issue')),
                description=rule_info.get('fullDescription', {}).get('text', ''),
                severity=self._map_codeql_severity(result.get('level', 'note')),
                scanner=ScannerType.CODEQL,
                file_path=file_path,
                line_number=line_number,
                cwe_id=self._extract_cwe_from_tags(rule_info.get('properties', {}).get('tags', [])),
                evidence={
                    'rule_id': rule_id,
                    'message': result.get('message', {}).get('text', ''),
                    'help_uri': rule_info.get('helpUri', ''),
                    'code_flows': result.get('codeFlows', [])
                },
                references=[rule_info.get('helpUri', '')] if rule_info.get('helpUri') else []
            )
        except Exception as e:
            logger.error(f"Failed to convert SARIF result: {e}")
            return None
    
    def _map_codeql_severity(self, level: str) -> ScanSeverity:
        """Map CodeQL levels to our severity enum"""
        level_map = {
            'error': ScanSeverity.HIGH,
            'warning': ScanSeverity.MEDIUM,
            'note': ScanSeverity.LOW,
            'info': ScanSeverity.INFO
        }
        return level_map.get(level.lower(), ScanSeverity.INFO)
    
    def _extract_cwe_from_tags(self, tags: List[str]) -> Optional[str]:
        """Extract CWE ID from CodeQL tags"""
        for tag in tags:
            if tag.startswith('external/cwe/cwe-'):
                return tag.replace('external/cwe/', '').upper()
        return None
    
    def _get_directory_size(self, path: Path) -> int:
        """Get directory size in bytes"""
        try:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        except:
            return 0
    
    async def _get_codeql_version(self) -> str:
        """Get CodeQL version for metadata"""
        try:
            result = await asyncio.create_subprocess_exec(
                self.codeql_path, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return stdout.decode().strip()
        except:
            return "unknown"


class CheckovScanner:
    """Checkov Infrastructure as Code security scanner"""
    
    def __init__(self, checkov_path: str = "checkov"):
        self.checkov_path = checkov_path
    
    async def scan_iac(self, target_path: str, config: AdvancedScannerConfig) -> ScanResult:
        """Run Checkov scan on Infrastructure as Code files"""
        scan_id = f"checkov_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
                output_file_path = output_file.name
            
            # Build Checkov command
            cmd = [
                self.checkov_path,
                "--directory", target_path,
                "--output", "json",
                "--output-file", output_file_path,
                "--quiet"
            ]
            
            # Add framework filters
            frameworks = config.custom_config.get("frameworks", ["terraform", "cloudformation", "kubernetes"])
            if frameworks:
                cmd.extend(["--framework"] + frameworks)
            
            # Add severity threshold
            if config.severity_threshold != ScanSeverity.INFO:
                severity_map = {
                    ScanSeverity.CRITICAL: "CRITICAL",
                    ScanSeverity.HIGH: "HIGH",
                    ScanSeverity.MEDIUM: "MEDIUM"
                }
                cmd.extend(["--check", severity_map.get(config.severity_threshold, "MEDIUM")])
            
            # Add custom checks directory if specified
            if "custom_checks" in config.custom_config:
                cmd.extend(["--external-checks-dir", config.custom_config["custom_checks"]])
            
            logger.info(f"Starting Checkov scan: {' '.join(cmd)}")
            
            # Run Checkov
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                raise Exception(f"Checkov scan timed out after {config.timeout_seconds} seconds")
            
            # Checkov returns non-zero when findings are present, so we check stderr for actual errors
            if process.returncode not in [0, 1] and stderr:
                error_msg = stderr.decode()
                logger.error(f"Checkov scan failed: {error_msg}")
                raise Exception(f"Checkov scan failed: {error_msg}")
            
            # Parse Checkov output
            findings = await self._parse_checkov_output(output_file_path, target_path)
            
            # Check if build should fail
            if config.fail_build_on_critical:
                critical_findings = [f for f in findings if f.severity == ScanSeverity.CRITICAL]
                if critical_findings:
                    logger.warning(f"Found {len(critical_findings)} critical IaC misconfigurations")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScanResult(
                scanner=ScannerType.CHECKOV,
                target=target_path,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=duration,
                findings=findings,
                metadata={
                    "checkov_version": await self._get_checkov_version(),
                    "frameworks_scanned": frameworks,
                    "files_scanned": len(set(f.file_path for f in findings if f.file_path))
                }
            )
            
        except Exception as e:
            logger.error(f"Checkov scan error: {e}")
            return ScanResult(
                scanner=ScannerType.CHECKOV,
                target=target_path,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                status="failed",
                error_message=str(e)
            )
        finally:
            # Cleanup temp file
            try:
                Path(output_file_path).unlink()
            except:
                pass
    
    async def _parse_checkov_output(self, output_file: str, target_path: str) -> List[ScanFinding]:
        """Parse Checkov JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                checkov_data = json.load(f)
            
            # Parse failed checks
            for result in checkov_data.get('results', {}).get('failed_checks', []):
                finding = self._convert_checkov_result(result, target_path)
                if finding:
                    findings.append(finding)
        except Exception as e:
            logger.error(f"Failed to parse Checkov output: {e}")
        
        return findings
    
    def _convert_checkov_result(self, result: Dict, target_path: str) -> Optional[ScanFinding]:
        """Convert Checkov result to ScanFinding"""
        try:
            return ScanFinding(
                id=f"checkov_{result.get('check_id', 'unknown')}",
                title=result.get('check_name', 'IaC Misconfiguration'),
                description=result.get('description', ''),
                severity=self._map_checkov_severity(result.get('severity', 'MEDIUM')),
                scanner=ScannerType.CHECKOV,
                file_path=result.get('file_path', ''),
                line_number=result.get('file_line_range', [None])[0],
                evidence={
                    'check_id': result.get('check_id', ''),
                    'resource': result.get('resource', ''),
                    'guideline': result.get('guideline', ''),
                    'code_block': result.get('code_block', []),
                    'caller_file_path': result.get('caller_file_path', ''),
                    'caller_file_line_range': result.get('caller_file_line_range', [])
                },
                references=[result.get('guideline', '')] if result.get('guideline') else []
            )
        except Exception as e:
            logger.error(f"Failed to convert Checkov result: {e}")
            return None
    
    def _map_checkov_severity(self, checkov_severity: str) -> ScanSeverity:
        """Map Checkov severity to our severity enum"""
        severity_map = {
            'CRITICAL': ScanSeverity.CRITICAL,
            'HIGH': ScanSeverity.HIGH,
            'MEDIUM': ScanSeverity.MEDIUM,
            'LOW': ScanSeverity.LOW,
            'INFO': ScanSeverity.INFO
        }
        return severity_map.get(checkov_severity.upper(), ScanSeverity.MEDIUM)
    
    async def _get_checkov_version(self) -> str:
        """Get Checkov version for metadata"""
        try:
            result = await asyncio.create_subprocess_exec(
                self.checkov_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return stdout.decode().strip()
        except:
            return "unknown"


# Export classes
__all__ = ['CodeQLScanner', 'CheckovScanner']
