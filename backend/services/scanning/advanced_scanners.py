"""
Advanced Security Scanners Integration
Supports OWASP ZAP, Nuclei, CodeQL, and Checkov for comprehensive security testing
"""
import asyncio
import json
import xml.etree.ElementTree as ET
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import logging
from enum import Enum
import yaml

# Helper function for timezone-aware UTC datetime
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ScannerType(str, Enum):
    """Supported advanced scanner types"""
    OWASP_ZAP = "owasp_zap"
    NUCLEI = "nuclei"
    CODEQL = "codeql"
    CHECKOV = "checkov"


class ScanSeverity(str, Enum):
    """Severity levels for scan findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanFinding(BaseModel):
    """Individual security finding from advanced scanners"""
    id: str
    title: str
    description: str
    severity: ScanSeverity
    scanner: ScannerType
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    url: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    remediation: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_utc_now)


class ScanResult(BaseModel):
    """Complete scan result from an advanced scanner"""
    scanner: ScannerType
    target: str  # URL or repository path
    scan_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    duration_seconds: float
    findings: List[ScanFinding] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "completed"
    error_message: Optional[str] = None
    
    @property
    def critical_count(self) -> int:
        return len([f for f in self.findings if f.severity == ScanSeverity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        return len([f for f in self.findings if f.severity == ScanSeverity.HIGH])
    
    @property
    def summary(self) -> Dict[str, int]:
        """Get finding count summary by severity"""
        summary = {severity.value: 0 for severity in ScanSeverity}
        for finding in self.findings:
            summary[finding.severity.value] += 1
        return summary


class AdvancedScannerConfig(BaseModel):
    """Configuration for advanced security scanners"""
    scanner_type: ScannerType
    enabled: bool = True
    timeout_seconds: int = 300
    max_findings: int = 1000
    severity_threshold: ScanSeverity = ScanSeverity.MEDIUM
    custom_config: Dict[str, Any] = Field(default_factory=dict)
    fail_build_on_critical: bool = True
    fail_build_on_high: bool = False


class OWASPZAPScanner:
    """OWASP ZAP DAST scanner for web applications"""
    
    def __init__(self, zap_path: str = "zap.sh", proxy_port: int = 8080):
        self.zap_path = zap_path
        self.proxy_port = proxy_port
        self.temp_dir = None
    
    async def scan_url(self, target_url: str, config: AdvancedScannerConfig) -> ScanResult:
        """Run OWASP ZAP scan against target URL"""
        scan_id = f"zap_{utc_now().strftime('%Y%m%d_%H%M%S')}"
        start_time = utc_now()
        
        try:
            # Create temporary directory for ZAP output
            self.temp_dir = tempfile.mkdtemp(prefix="zap_scan_")
            output_file = Path(self.temp_dir) / "zap_report.json"
            
            # Build ZAP command for headless scanning
            cmd = [
                self.zap_path,
                "-cmd",  # Command line mode
                "-quickurl", target_url,  # Quick scan of URL
                "-quickout", str(output_file),  # Output file
                "-quickprogress",  # Show progress
                f"-port", str(self.proxy_port)
            ]
            
            # Add custom config options
            if config.timeout_seconds:
                cmd.extend(["-timeout", str(config.timeout_seconds)])
            
            logger.info(f"Starting OWASP ZAP scan: {' '.join(cmd)}")
            
            # Run ZAP scan
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=config.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                raise Exception(f"ZAP scan timed out after {config.timeout_seconds} seconds")
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "ZAP scan failed"
                logger.error(f"ZAP scan failed: {error_msg}")
                raise Exception(f"ZAP scan failed: {error_msg}")
            
            # Parse ZAP output
            findings = await self._parse_zap_output(output_file, target_url)
            
            duration = (utc_now() - start_time).total_seconds()
            
            return ScanResult(
                scanner=ScannerType.OWASP_ZAP,
                target=target_url,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=duration,
                findings=findings,
                metadata={
                    "zap_version": await self._get_zap_version(),
                    "proxy_port": self.proxy_port,
                    "scan_type": "quick"
                }
            )
            
        except Exception as e:
            logger.error(f"ZAP scan error: {e}")
            return ScanResult(
                scanner=ScannerType.OWASP_ZAP,
                target=target_url,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=(utc_now() - start_time).total_seconds(),
                status="failed",
                error_message=str(e)
            )
        finally:
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
    
    async def _parse_zap_output(self, output_file: Path, target_url: str) -> List[ScanFinding]:
        """Parse ZAP JSON/XML output into ScanFindings"""
        findings = []
        
        try:
            if output_file.suffix.lower() == '.json':
                with open(output_file, 'r') as f:
                    zap_data = json.load(f)
                findings = self._parse_zap_json(zap_data, target_url)
            elif output_file.suffix.lower() == '.xml':
                tree = ET.parse(output_file)
                findings = self._parse_zap_xml(tree.getroot(), target_url)
        except Exception as e:
            logger.error(f"Failed to parse ZAP output: {e}")
        
        return findings
    
    def _parse_zap_json(self, zap_data: Dict, target_url: str) -> List[ScanFinding]:
        """Parse ZAP JSON output"""
        findings = []
        
        # ZAP JSON structure varies, adapt as needed
        sites = zap_data.get('site', [])
        if not isinstance(sites, list):
            sites = [sites]
        
        for site in sites:
            alerts = site.get('alerts', [])
            for alert in alerts:
                finding = ScanFinding(
                    id=f"zap_{alert.get('pluginid', 'unknown')}",
                    title=alert.get('name', 'Unknown vulnerability'),
                    description=alert.get('desc', ''),
                    severity=self._map_zap_severity(alert.get('riskdesc', 'Low')),
                    scanner=ScannerType.OWASP_ZAP,
                    url=target_url,
                    evidence={
                        'uri': alert.get('uri', ''),
                        'method': alert.get('method', ''),
                        'param': alert.get('param', ''),
                        'attack': alert.get('attack', ''),
                        'evidence': alert.get('evidence', '')
                    },
                    remediation=alert.get('solution', ''),
                    references=alert.get('reference', '').split('\n') if alert.get('reference') else []
                )
                findings.append(finding)
        
        return findings
    
    def _parse_zap_xml(self, root: ET.Element, target_url: str) -> List[ScanFinding]:
        """Parse ZAP XML output"""
        findings = []
        
        for site in root.findall('.//site'):
            for alert in site.findall('.//alertitem'):
                finding = ScanFinding(
                    id=f"zap_{alert.findtext('pluginid', 'unknown')}",
                    title=alert.findtext('name', 'Unknown vulnerability'),
                    description=alert.findtext('desc', ''),
                    severity=self._map_zap_severity(alert.findtext('riskdesc', 'Low')),
                    scanner=ScannerType.OWASP_ZAP,
                    url=target_url,
                    evidence={
                        'uri': alert.findtext('uri', ''),
                        'method': alert.findtext('method', ''),
                        'param': alert.findtext('param', ''),
                        'attack': alert.findtext('attack', ''),
                        'evidence': alert.findtext('evidence', '')
                    },
                    remediation=alert.findtext('solution', ''),
                    references=alert.findtext('reference', '').split('\n') if alert.findtext('reference') else []
                )
                findings.append(finding)
        
        return findings
    
    def _map_zap_severity(self, zap_risk: str) -> ScanSeverity:
        """Map ZAP risk levels to our severity enum"""
        risk_lower = zap_risk.lower()
        if 'critical' in risk_lower:
            return ScanSeverity.CRITICAL
        elif 'high' in risk_lower:
            return ScanSeverity.HIGH
        elif 'medium' in risk_lower:
            return ScanSeverity.MEDIUM
        elif 'low' in risk_lower:
            return ScanSeverity.LOW
        else:
            return ScanSeverity.INFO
    
    async def _get_zap_version(self) -> str:
        """Get ZAP version for metadata"""
        try:
            result = await asyncio.create_subprocess_exec(
                self.zap_path, "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return stdout.decode().strip()
        except:
            return "unknown"


class NucleiScanner:
    """Nuclei vulnerability scanner"""
    
    def __init__(self, nuclei_path: str = "nuclei"):
        self.nuclei_path = nuclei_path
        self.templates_dir = None
    
    async def scan_urls(self, targets: List[str], config: AdvancedScannerConfig) -> ScanResult:
        """Run Nuclei scan against target URLs"""
        scan_id = f"nuclei_{utc_now().strftime('%Y%m%d_%H%M%S')}"
        start_time = utc_now()
        target_str = ", ".join(targets[:3]) + ("..." if len(targets) > 3 else "")
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as target_file:
                for target in targets:
                    target_file.write(f"{target}\n")
                target_file_path = target_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
                output_file_path = output_file.name
            
            # Build Nuclei command
            cmd = [
                self.nuclei_path,
                "-l", target_file_path,  # Target list file
                "-json",  # JSON output
                "-o", output_file_path,  # Output file
                "-stats",  # Show statistics
                "-silent"  # Reduce noise
            ]
            
            # Add severity filter
            if config.severity_threshold != ScanSeverity.INFO:
                severity_map = {
                    ScanSeverity.CRITICAL: "critical",
                    ScanSeverity.HIGH: "high,critical", 
                    ScanSeverity.MEDIUM: "medium,high,critical"
                }
                cmd.extend(["-severity", severity_map[config.severity_threshold]])
            
            # Add custom templates if specified
            if "templates" in config.custom_config:
                cmd.extend(["-t", config.custom_config["templates"]])
            
            # Add rate limiting
            if "rate_limit" in config.custom_config:
                cmd.extend(["-rate-limit", str(config.custom_config["rate_limit"])])
            
            logger.info(f"Starting Nuclei scan: {' '.join(cmd)}")
            
            # Run Nuclei
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
                raise Exception(f"Nuclei scan timed out after {config.timeout_seconds} seconds")
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Nuclei scan failed"
                logger.warning(f"Nuclei scan completed with warnings: {error_msg}")
            
            # Parse Nuclei output
            findings = await self._parse_nuclei_output(output_file_path)
            
            duration = (utc_now() - start_time).total_seconds()
            
            return ScanResult(
                scanner=ScannerType.NUCLEI,
                target=target_str,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=duration,
                findings=findings,
                metadata={
                    "nuclei_version": await self._get_nuclei_version(),
                    "targets_count": len(targets),
                    "templates_used": config.custom_config.get("templates", "community")
                }
            )
            
        except Exception as e:
            logger.error(f"Nuclei scan error: {e}")
            return ScanResult(
                scanner=ScannerType.NUCLEI,
                target=target_str,
                scan_id=scan_id,
                timestamp=start_time,
                duration_seconds=(utc_now() - start_time).total_seconds(),
                status="failed",
                error_message=str(e)
            )
        finally:
            # Cleanup temp files
            for temp_path in [target_file_path, output_file_path]:
                try:
                    Path(temp_path).unlink()
                except:
                    pass
    
    async def _parse_nuclei_output(self, output_file: str) -> List[ScanFinding]:
        """Parse Nuclei JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                for line in f:
                    if line.strip():
                        nuclei_finding = json.loads(line)
                        finding = self._convert_nuclei_finding(nuclei_finding)
                        if finding:
                            findings.append(finding)
        except Exception as e:
            logger.error(f"Failed to parse Nuclei output: {e}")
        
        return findings
    
    def _convert_nuclei_finding(self, nuclei_data: Dict) -> Optional[ScanFinding]:
        """Convert Nuclei JSON finding to ScanFinding"""
        try:
            info = nuclei_data.get('info', {})
            
            return ScanFinding(
                id=f"nuclei_{nuclei_data.get('template-id', 'unknown')}",
                title=info.get('name', 'Unknown vulnerability'),
                description=info.get('description', ''),
                severity=self._map_nuclei_severity(info.get('severity', 'info')),
                scanner=ScannerType.NUCLEI,
                url=nuclei_data.get('matched-at', ''),
                evidence={
                    'template_id': nuclei_data.get('template-id', ''),
                    'matcher_name': nuclei_data.get('matcher-name', ''),
                    'extracted_results': nuclei_data.get('extracted-results', []),
                    'curl_command': nuclei_data.get('curl-command', '')
                },
                references=info.get('reference', []) if isinstance(info.get('reference'), list) else [info.get('reference', '')]
            )
        except Exception as e:
            logger.error(f"Failed to convert Nuclei finding: {e}")
            return None
    
    def _map_nuclei_severity(self, nuclei_severity: str) -> ScanSeverity:
        """Map Nuclei severity to our severity enum"""
        severity_map = {
            'critical': ScanSeverity.CRITICAL,
            'high': ScanSeverity.HIGH,
            'medium': ScanSeverity.MEDIUM,
            'low': ScanSeverity.LOW,
            'info': ScanSeverity.INFO
        }
        return severity_map.get(nuclei_severity.lower(), ScanSeverity.INFO)
    
    async def _get_nuclei_version(self) -> str:
        """Get Nuclei version for metadata"""
        try:
            result = await asyncio.create_subprocess_exec(
                self.nuclei_path, "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return stdout.decode().strip()
        except:
            return "unknown"


class AdvancedSecurityScanner:
    """Coordinated advanced security scanner that combines multiple tools"""
    
    def __init__(self, config: Optional[AdvancedScannerConfig] = None):
        if config is None:
            # Create default config with multi-scanner support
            config = AdvancedScannerConfig(scanner_type=ScannerType.NUCLEI)
        self.config = config
        self.owasp_scanner = OWASPZAPScanner()
        self.nuclei_scanner = NucleiScanner()
        
    async def run_comprehensive_scan(
        self, 
        target: str, 
        scan_types: List[ScannerType] = None
    ) -> Dict[str, Any]:
        """Run comprehensive security scan with multiple tools"""
        if scan_types is None:
            scan_types = [ScannerType.NUCLEI, ScannerType.OWASP_ZAP]
            
        results = {}
        
        for scanner_type in scan_types:
            try:
                if scanner_type == ScannerType.NUCLEI:
                    result = await self.nuclei_scanner.scan(target)
                elif scanner_type == ScannerType.OWASP_ZAP:
                    result = await self.owasp_scanner.scan(target)
                else:
                    logger.warning(f"Scanner type {scanner_type} not implemented")
                    continue
                    
                results[scanner_type.value] = result
                
            except Exception as e:
                logger.error(f"Scanner {scanner_type} failed: {e}")
                results[scanner_type.value] = {"error": str(e)}
                
        return results


# Export main classes
__all__ = [
    'ScannerType', 'ScanSeverity', 'ScanFinding', 'ScanResult',
    'AdvancedScannerConfig', 'OWASPZAPScanner', 'NucleiScanner',
    'AdvancedSecurityScanner'
]

