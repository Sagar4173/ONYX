#!/usr/bin/env python3
"""
Advanced Scanner Engine
Integrates ZAP, Nuclei, CodeQL, and Checkov with unified pipeline
"""
import asyncio
import json
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import yaml
import re
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ScanType(Enum):
    """Types of security scans"""
    SAST = "sast"  # Static Application Security Testing
    DAST = "dast"  # Dynamic Application Security Testing
    IAC = "iac"    # Infrastructure as Code
    SECRETS = "secrets"
    DEPENDENCIES = "dependencies"
    PENTEST = "pentest"

class Severity(Enum):
    """Normalized severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Finding:
    """Normalized finding schema for all scanners"""
    id: str
    source: str  # Scanner that generated the finding
    rule_id: str
    title: str
    description: str
    severity: Severity
    confidence: str
    location: Dict[str, Any]  # file, line, column, url, etc.
    cwe: Optional[str] = None
    cve: Optional[str] = None
    recommendation: Optional[str] = None
    scan_type: ScanType = ScanType.SAST
    raw_output: Optional[Dict] = None
    timestamp: str = None
    suppressed: bool = False
    suppression_reason: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

@dataclass
class ScanConfig:
    """Configuration for advanced scanning"""
    # General settings
    max_concurrent_scans: int = 3
    scan_timeout: int = 1800  # 30 minutes
    
    # DAST settings
    dast_target_allowlist: List[str] = None
    dast_rate_limit: float = 2.0  # requests per second
    dast_max_depth: int = 3
    
    # SAST settings
    sast_languages: List[str] = None
    sast_exclude_patterns: List[str] = None
    
    # IaC settings
    iac_frameworks: List[str] = None
    iac_custom_policies: List[str] = None
    
    # Suppression settings
    suppression_file: str = ".security-suppressions.yaml"
    allow_inline_suppressions: bool = True
    
    def __post_init__(self):
        if self.dast_target_allowlist is None:
            self.dast_target_allowlist = []
        if self.sast_languages is None:
            self.sast_languages = ["python", "javascript", "java", "go", "csharp"]
        if self.sast_exclude_patterns is None:
            self.sast_exclude_patterns = ["**/node_modules/**", "**/vendor/**", "**/.git/**"]
        if self.iac_frameworks is None:
            self.iac_frameworks = ["terraform", "cloudformation", "kubernetes", "docker"]
        if self.iac_custom_policies is None:
            self.iac_custom_policies = []

class SuppressionEngine:
    """Handles false positive suppression with policy-as-code"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.suppression_rules = {}
        self.inline_suppressions = {}
        
    def load_suppression_rules(self, repo_path: str) -> Dict:
        """Load suppression rules from repository"""
        suppression_file = Path(repo_path) / self.config.suppression_file
        
        if suppression_file.exists():
            try:
                with open(suppression_file, 'r') as f:
                    self.suppression_rules = yaml.safe_load(f) or {}
                logger.info(f"Loaded {len(self.suppression_rules)} suppression rules")
            except Exception as e:
                logger.error(f"Error loading suppression rules: {e}")
                self.suppression_rules = {}
        
        return self.suppression_rules
    
    def scan_inline_suppressions(self, repo_path: str) -> Dict:
        """Scan for inline suppression annotations"""
        if not self.config.allow_inline_suppressions:
            return {}
        
        suppressions = {}
        
        # Common suppression patterns
        patterns = [
            r'#\s*nosec\s*(\S+)?',  # Python, Shell
            r'//\s*nosec\s*(\S+)?',  # JavaScript, Go, Java
            r'/\*\s*nosec\s*(\S+)?\s*\*/',  # C-style
            r'<!--\s*nosec\s*(\S+)?\s*-->',  # HTML, XML
        ]
        
        for file_path in Path(repo_path).rglob("*"):
            if file_path.is_file() and not any(pattern in str(file_path) for pattern in self.config.sast_exclude_patterns):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            for pattern in patterns:
                                match = re.search(pattern, line, re.IGNORECASE)
                                if match:
                                    rule_id = match.group(1) if match.group(1) else "all"
                                    key = f"{file_path.relative_to(repo_path)}:{line_num}"
                                    suppressions[key] = {
                                        "rule_id": rule_id,
                                        "reason": "inline suppression",
                                        "line": line_num
                                    }
                except Exception as e:
                    logger.debug(f"Could not scan {file_path} for suppressions: {e}")
        
        self.inline_suppressions = suppressions
        logger.info(f"Found {len(suppressions)} inline suppressions")
        return suppressions
    
    def should_suppress(self, finding: Finding, repo_path: str) -> tuple[bool, str]:
        """Check if finding should be suppressed"""
        
        # Check global suppression rules
        for rule_pattern, rule_config in self.suppression_rules.items():
            if self._matches_suppression_rule(finding, rule_pattern, rule_config):
                return True, f"Global suppression rule: {rule_pattern}"
        
        # Check inline suppressions
        if "file" in finding.location:
            file_path = finding.location["file"]
            line = finding.location.get("line", 0)
            
            # Check exact line
            suppression_key = f"{file_path}:{line}"
            if suppression_key in self.inline_suppressions:
                suppression = self.inline_suppressions[suppression_key]
                if suppression["rule_id"] == "all" or suppression["rule_id"] == finding.rule_id:
                    return True, f"Inline suppression: {suppression['reason']}"
            
            # Check line above (common pattern)
            suppression_key = f"{file_path}:{line-1}"
            if suppression_key in self.inline_suppressions:
                suppression = self.inline_suppressions[suppression_key]
                if suppression["rule_id"] == "all" or suppression["rule_id"] == finding.rule_id:
                    return True, f"Inline suppression (line above): {suppression['reason']}"
        
        return False, ""
    
    def _matches_suppression_rule(self, finding: Finding, pattern: str, config: Dict) -> bool:
        """Check if finding matches suppression rule"""
        # Rule ID matching
        if "rule_ids" in config:
            if finding.rule_id not in config["rule_ids"]:
                return False
        
        # Severity matching
        if "severities" in config:
            if finding.severity.value not in config["severities"]:
                return False
        
        # File pattern matching
        if "file_patterns" in config and "file" in finding.location:
            file_path = finding.location["file"]
            if not any(re.match(fp, file_path) for fp in config["file_patterns"]):
                return False
        
        # Scanner matching
        if "scanners" in config:
            if finding.source not in config["scanners"]:
                return False
        
        return True

class ZAPScanner:
    """OWASP ZAP Dynamic Application Security Testing"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.zap_api_key = None
        self.zap_proxy_port = 8080
        
    async def scan(self, target_url: str, scan_id: str) -> List[Finding]:
        """Perform DAST scan with ZAP"""
        findings = []
        
        # Validate target is in allowlist
        if not self._is_target_allowed(target_url):
            raise ValueError(f"Target {target_url} not in allowlist")
        
        try:
            # Start ZAP daemon
            await self._start_zap_daemon()
            
            # Configure ZAP
            await self._configure_zap()
            
            # Spider the target
            spider_id = await self._spider_target(target_url)
            await self._wait_for_spider(spider_id)
            
            # Active scan
            scan_id_zap = await self._active_scan(target_url)
            await self._wait_for_scan(scan_id_zap)
            
            # Get results
            findings = await self._get_zap_findings(target_url, scan_id)
            
        except Exception as e:
            logger.error(f"ZAP scan failed: {e}")
            raise
        finally:
            await self._stop_zap_daemon()
        
        return findings
    
    def _is_target_allowed(self, target_url: str) -> bool:
        """Check if target is in allowlist"""
        if not self.config.dast_target_allowlist:
            return False
        
        parsed_url = urlparse(target_url)
        target_host = parsed_url.netloc.lower()
        
        for allowed in self.config.dast_target_allowlist:
            if target_host == allowed.lower() or target_host.endswith(f".{allowed.lower()}"):
                return True
        
        return False
    
    async def _start_zap_daemon(self):
        """Start ZAP in daemon mode"""
        cmd = [
            "zap.sh", "-daemon",
            "-port", str(self.zap_proxy_port),
            "-config", "api.disablekey=true",
            "-config", "api.addrs.addr.name=.*",
            "-config", "api.addrs.addr.regex=true"
        ]
        
        self.zap_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        # Wait for ZAP to start
        await asyncio.sleep(10)
    
    async def _configure_zap(self):
        """Configure ZAP scanning options"""
        base_url = f"http://localhost:{self.zap_proxy_port}"
        
        # Set global exclusions
        excluded_urls = [
            ".*logout.*",
            ".*\\.css",
            ".*\\.js", 
            ".*\\.gif",
            ".*\\.jpeg",
            ".*\\.jpg",
            ".*\\.png",
            ".*\\.ico"
        ]
        
        for pattern in excluded_urls:
            try:
                requests.get(f"{base_url}/JSON/core/action/excludeFromProxy/", 
                           params={"regex": pattern})
            except:
                pass
    
    async def _spider_target(self, target_url: str) -> str:
        """Spider the target application"""
        base_url = f"http://localhost:{self.zap_proxy_port}"
        
        response = requests.get(f"{base_url}/JSON/spider/action/scan/",
                              params={
                                  "url": target_url,
                                  "maxChildren": "10",
                                  "recurse": "true",
                                  "contextName": "",
                                  "subtreeOnly": "false"
                              })
        
        result = response.json()
        return result["scan"]
    
    async def _wait_for_spider(self, spider_id: str):
        """Wait for spider to complete"""
        base_url = f"http://localhost:{self.zap_proxy_port}"
        
        while True:
            response = requests.get(f"{base_url}/JSON/spider/view/status/",
                                  params={"scanId": spider_id})
            status = response.json()["status"]
            
            if int(status) >= 100:
                break
                
            await asyncio.sleep(2)
    
    async def _active_scan(self, target_url: str) -> str:
        """Start active security scan"""
        base_url = f"http://localhost:{self.zap_proxy_port}"
        
        response = requests.get(f"{base_url}/JSON/ascan/action/scan/",
                              params={
                                  "url": target_url,
                                  "recurse": "true",
                                  "inScopeOnly": "false",
                                  "scanPolicyName": "",
                                  "method": "GET",
                                  "postData": ""
                              })
        
        result = response.json()
        return result["scan"]
    
    async def _wait_for_scan(self, scan_id: str):
        """Wait for active scan to complete"""
        base_url = f"http://localhost:{self.zap_proxy_port}"
        
        while True:
            response = requests.get(f"{base_url}/JSON/ascan/view/status/",
                                  params={"scanId": scan_id})
            status = response.json()["status"]
            
            if int(status) >= 100:
                break
                
            await asyncio.sleep(5)
    
    async def _get_zap_findings(self, target_url: str, scan_id: str) -> List[Finding]:
        """Extract findings from ZAP results"""
        base_url = f"http://localhost:{self.zap_proxy_port}"
        findings = []
        
        try:
            response = requests.get(f"{base_url}/JSON/core/view/alerts/",
                                  params={"baseurl": target_url})
            alerts = response.json()["alerts"]
            
            for alert in alerts:
                finding = Finding(
                    id=f"zap-{scan_id}-{len(findings)}",
                    source="zap",
                    rule_id=alert.get("pluginId", "unknown"),
                    title=alert.get("alert", "Unknown Alert"),
                    description=alert.get("description", ""),
                    severity=self._normalize_zap_severity(alert.get("risk", "Low")),
                    confidence=alert.get("confidence", "Medium"),
                    location={
                        "url": alert.get("url", ""),
                        "method": alert.get("method", ""),
                        "parameter": alert.get("param", "")
                    },
                    cwe=alert.get("cweid"),
                    recommendation=alert.get("solution", ""),
                    scan_type=ScanType.DAST,
                    raw_output=alert
                )
                findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error extracting ZAP findings: {e}")
        
        return findings
    
    def _normalize_zap_severity(self, zap_severity: str) -> Severity:
        """Normalize ZAP severity to standard levels"""
        severity_map = {
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW,
            "Informational": Severity.INFO
        }
        return severity_map.get(zap_severity, Severity.LOW)
    
    async def _stop_zap_daemon(self):
        """Stop ZAP daemon"""
        if hasattr(self, 'zap_process'):
            self.zap_process.terminate()
            await self.zap_process.wait()

class NucleiScanner:
    """Nuclei pentest template scanner"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        
    async def scan(self, target_url: str, scan_id: str) -> List[Finding]:
        """Perform pentest scan with Nuclei"""
        findings = []
        
        # Validate target is in allowlist
        if not self._is_target_allowed(target_url):
            raise ValueError(f"Target {target_url} not in allowlist")
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
                output_file = tmp_file.name
            
            # Build Nuclei command
            cmd = [
                "nuclei",
                "-target", target_url,
                "-json",
                "-output", output_file,
                "-rate-limit", str(int(self.config.dast_rate_limit)),
                "-timeout", "30",
                "-retries", "1",
                "-no-color",
                "-silent"
            ]
            
            # Run Nuclei
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.scan_timeout
            )
            
            # Parse results
            findings = self._parse_nuclei_output(output_file, scan_id)
            
            # Cleanup
            Path(output_file).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Nuclei scan failed: {e}")
            raise
        
        return findings
    
    def _is_target_allowed(self, target_url: str) -> bool:
        """Check if target is in allowlist"""
        if not self.config.dast_target_allowlist:
            return False
        
        parsed_url = urlparse(target_url)
        target_host = parsed_url.netloc.lower()
        
        for allowed in self.config.dast_target_allowlist:
            if target_host == allowed.lower() or target_host.endswith(f".{allowed.lower()}"):
                return True
        
        return False
    
    def _parse_nuclei_output(self, output_file: str, scan_id: str) -> List[Finding]:
        """Parse Nuclei JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            
                            finding = Finding(
                                id=f"nuclei-{scan_id}-{line_num}",
                                source="nuclei",
                                rule_id=result.get("template-id", "unknown"),
                                title=result.get("info", {}).get("name", "Unknown Template"),
                                description=result.get("info", {}).get("description", ""),
                                severity=self._normalize_nuclei_severity(
                                    result.get("info", {}).get("severity", "low")
                                ),
                                confidence="High",
                                location={
                                    "url": result.get("matched-at", ""),
                                    "template": result.get("template", ""),
                                    "matcher": result.get("matcher-name", "")
                                },
                                recommendation=result.get("info", {}).get("remediation", ""),
                                scan_type=ScanType.PENTEST,
                                raw_output=result
                            )
                            
                            # Add CWE if available
                            classification = result.get("info", {}).get("classification", {})
                            if "cwe-id" in classification:
                                finding.cwe = f"CWE-{classification['cwe-id']}"
                            
                            findings.append(finding)
                            
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Error parsing Nuclei output: {e}")
        
        return findings
    
    def _normalize_nuclei_severity(self, nuclei_severity: str) -> Severity:
        """Normalize Nuclei severity to standard levels"""
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO
        }
        return severity_map.get(nuclei_severity.lower(), Severity.LOW)

class CodeQLScanner:
    """GitHub CodeQL deep code analysis"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        
    async def scan(self, repo_path: str, scan_id: str) -> List[Finding]:
        """Perform SAST scan with CodeQL"""
        findings = []
        
        try:
            # Detect languages
            languages = self._detect_languages(repo_path)
            
            if not languages:
                logger.info("No supported languages detected for CodeQL")
                return findings
            
            # Create CodeQL database
            db_path = await self._create_database(repo_path, languages, scan_id)
            
            # Run analysis
            for language in languages:
                lang_findings = await self._analyze_database(db_path, language, scan_id)
                findings.extend(lang_findings)
            
            # Cleanup
            await self._cleanup_database(db_path)
            
        except Exception as e:
            logger.error(f"CodeQL scan failed: {e}")
            raise
        
        return findings
    
    def _detect_languages(self, repo_path: str) -> List[str]:
        """Detect supported languages in repository"""
        detected = []
        
        language_patterns = {
            "python": ["*.py"],
            "javascript": ["*.js", "*.ts", "*.jsx", "*.tsx"],
            "java": ["*.java"],
            "csharp": ["*.cs"],
            "cpp": ["*.cpp", "*.c", "*.cc", "*.cxx"],
            "go": ["*.go"]
        }
        
        for language, patterns in language_patterns.items():
            if language not in self.config.sast_languages:
                continue
                
            for pattern in patterns:
                if list(Path(repo_path).rglob(pattern)):
                    detected.append(language)
                    break
        
        return detected
    
    async def _create_database(self, repo_path: str, languages: List[str], scan_id: str) -> str:
        """Create CodeQL database"""
        db_path = f"/tmp/codeql-db-{scan_id}"
        
        cmd = [
            "codeql", "database", "create",
            db_path,
            f"--source-root={repo_path}",
            f"--language={','.join(languages)}",
            "--overwrite"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=self.config.scan_timeout
        )
        
        if process.returncode != 0:
            raise Exception(f"CodeQL database creation failed: {stderr.decode()}")
        
        return db_path
    
    async def _analyze_database(self, db_path: str, language: str, scan_id: str) -> List[Finding]:
        """Analyze CodeQL database"""
        findings = []
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sarif', delete=False) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Get query suite for language
            query_suite = f"codeql/{language}-queries:codeql-suites/{language}-security-extended.qls"
            
            cmd = [
                "codeql", "database", "analyze",
                db_path,
                query_suite,
                "--format=sarif-latest",
                f"--output={output_file}",
                "--sarif-category=security"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.scan_timeout
            )
            
            if process.returncode == 0:
                findings = self._parse_sarif_output(output_file, scan_id, language)
        
        except Exception as e:
            logger.error(f"CodeQL analysis failed for {language}: {e}")
        
        finally:
            Path(output_file).unlink(missing_ok=True)
        
        return findings
    
    def _parse_sarif_output(self, output_file: str, scan_id: str, language: str) -> List[Finding]:
        """Parse CodeQL SARIF output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                sarif_data = json.load(f)
            
            for run in sarif_data.get("runs", []):
                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "unknown")
                    rule_info = self._get_rule_info(run, rule_id)
                    
                    for location in result.get("locations", []):
                        physical_location = location.get("physicalLocation", {})
                        artifact_location = physical_location.get("artifactLocation", {})
                        region = physical_location.get("region", {})
                        
                        finding = Finding(
                            id=f"codeql-{scan_id}-{len(findings)}",
                            source="codeql",
                            rule_id=rule_id,
                            title=rule_info.get("name", rule_id),
                            description=rule_info.get("description", ""),
                            severity=self._normalize_codeql_severity(
                                rule_info.get("security-severity", "5.0")
                            ),
                            confidence="High",
                            location={
                                "file": artifact_location.get("uri", ""),
                                "line": region.get("startLine", 0),
                                "column": region.get("startColumn", 0),
                                "end_line": region.get("endLine", 0),
                                "end_column": region.get("endColumn", 0)
                            },
                            recommendation=rule_info.get("help", {}).get("text", ""),
                            scan_type=ScanType.SAST,
                            raw_output=result
                        )
                        
                        # Add CWE if available
                        for tag in rule_info.get("properties", {}).get("tags", []):
                            if tag.startswith("cwe-"):
                                finding.cwe = tag.upper().replace("CWE-", "CWE-")
                                break
                        
                        findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error parsing CodeQL SARIF output: {e}")
        
        return findings
    
    def _get_rule_info(self, run: Dict, rule_id: str) -> Dict:
        """Get rule information from SARIF run data"""
        for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
            if rule.get("id") == rule_id:
                return rule
        return {}
    
    def _normalize_codeql_severity(self, security_severity: str) -> Severity:
        """Normalize CodeQL security severity to standard levels"""
        try:
            score = float(security_severity)
            if score >= 9.0:
                return Severity.CRITICAL
            elif score >= 7.0:
                return Severity.HIGH
            elif score >= 4.0:
                return Severity.MEDIUM
            else:
                return Severity.LOW
        except (ValueError, TypeError):
            return Severity.LOW
    
    async def _cleanup_database(self, db_path: str):
        """Clean up CodeQL database"""
        try:
            import shutil
            shutil.rmtree(db_path, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error cleaning up CodeQL database: {e}")

class CheckovScanner:
    """Checkov Infrastructure as Code security scanner"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        
    async def scan(self, repo_path: str, scan_id: str) -> List[Finding]:
        """Perform IaC scan with Checkov"""
        findings = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
                output_file = tmp_file.name
            
            # Build Checkov command
            cmd = [
                "checkov",
                "-d", repo_path,
                "--output", "json",
                "--output-file-path", output_file,
                "--quiet",
                "--compact"
            ]
            
            # Add framework filters
            if self.config.iac_frameworks:
                cmd.extend(["--framework"] + self.config.iac_frameworks)
            
            # Add custom policies
            for policy_path in self.config.iac_custom_policies:
                cmd.extend(["--external-checks-dir", policy_path])
            
            # Run Checkov
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.scan_timeout
            )
            
            # Parse results (Checkov may return non-zero on findings)
            findings = self._parse_checkov_output(output_file, scan_id)
            
            # Cleanup
            Path(output_file).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Checkov scan failed: {e}")
            raise
        
        return findings
    
    def _parse_checkov_output(self, output_file: str, scan_id: str) -> List[Finding]:
        """Parse Checkov JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            # Parse failed checks
            for failed_check in data.get("results", {}).get("failed_checks", []):
                finding = Finding(
                    id=f"checkov-{scan_id}-{len(findings)}",
                    source="checkov",
                    rule_id=failed_check.get("check_id", "unknown"),
                    title=failed_check.get("check_name", "Unknown Check"),
                    description=failed_check.get("description", ""),
                    severity=self._normalize_checkov_severity(
                        failed_check.get("severity", "MEDIUM")
                    ),
                    confidence="High",
                    location={
                        "file": failed_check.get("file_path", ""),
                        "line": failed_check.get("file_line_range", [0])[0],
                        "resource": failed_check.get("resource", ""),
                        "framework": failed_check.get("check_type", "")
                    },
                    recommendation=failed_check.get("guideline", ""),
                    scan_type=ScanType.IAC,
                    raw_output=failed_check
                )
                
                findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error parsing Checkov output: {e}")
        
        return findings
    
    def _normalize_checkov_severity(self, checkov_severity: str) -> Severity:
        """Normalize Checkov severity to standard levels"""
        severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "INFO": Severity.INFO
        }
        return severity_map.get(checkov_severity.upper(), Severity.MEDIUM)

class AdvancedScannerEngine:
    """Main engine coordinating all advanced scanners"""
    
    def __init__(self, config: ScanConfig = None):
        self.config = config or ScanConfig()
        self.suppression_engine = SuppressionEngine(self.config)
        
        # Initialize scanners
        self.zap_scanner = ZAPScanner(self.config)
        self.nuclei_scanner = NucleiScanner(self.config)
        self.codeql_scanner = CodeQLScanner(self.config)
        self.checkov_scanner = CheckovScanner(self.config)
        
        self.active_scans = {}
        self.scan_semaphore = asyncio.Semaphore(self.config.max_concurrent_scans)
    
    async def scan_repository(self, repo_path: str, target_url: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive security scan of repository"""
        scan_id = str(uuid.uuid4())
        scan_start = time.time()
        
        logger.info(f"Starting advanced scan {scan_id} for {repo_path}")
        
        # Load suppression rules
        self.suppression_engine.load_suppression_rules(repo_path)
        self.suppression_engine.scan_inline_suppressions(repo_path)
        
        # Collect all findings
        all_findings = []
        scan_results = {
            "scan_id": scan_id,
            "repository": repo_path,
            "target_url": target_url,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "scanners": {},
            "findings": [],
            "summary": {}
        }
        
        async with self.scan_semaphore:
            # Run SAST scans
            sast_tasks = []
            
            # CodeQL
            if self._has_supported_languages(repo_path):
                sast_tasks.append(self._run_scanner("codeql", self.codeql_scanner.scan, repo_path, scan_id))
            
            # Run IaC scan
            if self._has_iac_files(repo_path):
                sast_tasks.append(self._run_scanner("checkov", self.checkov_scanner.scan, repo_path, scan_id))
            
            # Run DAST scans if target URL provided
            dast_tasks = []
            if target_url and self.config.dast_target_allowlist:
                dast_tasks.extend([
                    self._run_scanner("zap", self.zap_scanner.scan, target_url, scan_id),
                    self._run_scanner("nuclei", self.nuclei_scanner.scan, target_url, scan_id)
                ])
            
            # Execute scans
            all_tasks = sast_tasks + dast_tasks
            if all_tasks:
                results = await asyncio.gather(*all_tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    scanner_name = ["codeql", "checkov", "zap", "nuclei"][i % 4]
                    if isinstance(result, Exception):
                        logger.error(f"Scanner {scanner_name} failed: {result}")
                        scan_results["scanners"][scanner_name] = {"error": str(result)}
                    else:
                        scanner_findings, duration = result
                        all_findings.extend(scanner_findings)
                        scan_results["scanners"][scanner_name] = {
                            "findings_count": len(scanner_findings),
                            "duration": duration,
                            "status": "completed"
                        }
        
        # Apply suppression rules
        for finding in all_findings:
            should_suppress, reason = self.suppression_engine.should_suppress(finding, repo_path)
            if should_suppress:
                finding.suppressed = True
                finding.suppression_reason = reason
        
        # Generate summary
        scan_results["findings"] = [asdict(f) for f in all_findings]
        scan_results["summary"] = self._generate_summary(all_findings)
        scan_results["end_time"] = datetime.now(timezone.utc).isoformat()
        scan_results["duration"] = time.time() - scan_start
        
        logger.info(f"Advanced scan {scan_id} completed in {scan_results['duration']:.2f}s")
        
        return scan_results
    
    async def _run_scanner(self, name: str, scanner_func, *args) -> tuple[List[Finding], float]:
        """Run individual scanner with timing"""
        start_time = time.time()
        try:
            findings = await scanner_func(*args)
            duration = time.time() - start_time
            logger.info(f"Scanner {name} completed with {len(findings)} findings in {duration:.2f}s")
            return findings, duration
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Scanner {name} failed after {duration:.2f}s: {e}")
            raise
    
    def _has_supported_languages(self, repo_path: str) -> bool:
        """Check if repository has languages supported by CodeQL"""
        language_patterns = {
            "python": ["*.py"],
            "javascript": ["*.js", "*.ts"],
            "java": ["*.java"],
            "csharp": ["*.cs"],
            "cpp": ["*.cpp", "*.c"],
            "go": ["*.go"]
        }
        
        for language, patterns in language_patterns.items():
            if language in self.config.sast_languages:
                for pattern in patterns:
                    if list(Path(repo_path).rglob(pattern)):
                        return True
        
        return False
    
    def _has_iac_files(self, repo_path: str) -> bool:
        """Check if repository has Infrastructure as Code files"""
        iac_patterns = [
            "*.tf",      # Terraform
            "*.yaml",    # Kubernetes, CloudFormation
            "*.yml",     # Kubernetes, CloudFormation  
            "Dockerfile", # Docker
            "docker-compose*.yml"
        ]
        
        for pattern in iac_patterns:
            if list(Path(repo_path).rglob(pattern)):
                return True
        
        return False
    
    def _generate_summary(self, findings: List[Finding]) -> Dict[str, Any]:
        """Generate scan summary statistics"""
        total_findings = len(findings)
        active_findings = [f for f in findings if not f.suppressed]
        
        summary = {
            "total_findings": total_findings,
            "active_findings": len(active_findings),
            "suppressed_findings": total_findings - len(active_findings),
            "by_severity": {},
            "by_scanner": {},
            "by_scan_type": {},
            "by_confidence": {}
        }
        
        # Count by severity
        for severity in Severity:
            count = len([f for f in active_findings if f.severity == severity])
            summary["by_severity"][severity.value] = count
        
        # Count by scanner
        scanners = set(f.source for f in active_findings)
        for scanner in scanners:
            count = len([f for f in active_findings if f.source == scanner])
            summary["by_scanner"][scanner] = count
        
        # Count by scan type
        for scan_type in ScanType:
            count = len([f for f in active_findings if f.scan_type == scan_type])
            summary["by_scan_type"][scan_type.value] = count
        
        # Count by confidence
        confidences = set(f.confidence for f in active_findings)
        for confidence in confidences:
            count = len([f for f in active_findings if f.confidence == confidence])
            summary["by_confidence"][confidence] = count
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    async def test_advanced_scanner():
        config = ScanConfig(
            max_concurrent_scans=2,
            dast_target_allowlist=["localhost", "example.com"],
            sast_languages=["python", "javascript"],
            iac_frameworks=["terraform", "kubernetes"]
        )
        
        engine = AdvancedScannerEngine(config)
        
        # Test repository scan
        results = await engine.scan_repository(
            repo_path="/path/to/repo",
            target_url="http://localhost:8080"
        )
        
        print(json.dumps(results, indent=2))
    
    # asyncio.run(test_advanced_scanner())
