"""
CodeQL SAST Scanner
===================

Static Application Security Testing using GitHub CodeQL.
"""

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.config import ScanConfig
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class CodeQLScanner(BaseScanner):
    """
    GitHub CodeQL Static Application Security Testing scanner.
    
    Performs deep semantic code analysis to find security vulnerabilities.
    """
    
    SCANNER_NAME = "codeql"
    SCANNER_TYPE = ScanType.SAST
    SUPPORTED_LANGUAGES = ["python", "javascript", "java", "csharp", "cpp", "go"]
    
    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.codeql_path = self.config.codeql_path
    
    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        """
        Perform SAST scan with CodeQL.
        
        Args:
            target: Path to repository to scan
            scan_id: Unique scan identifier
            **kwargs: Additional options
                - languages: List of languages to analyze
                - query_suite: CodeQL query suite to use
                
        Returns:
            List of security findings
        """
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        
        try:
            # Detect languages
            languages = kwargs.get('languages') or self._detect_languages(target)
            
            if not languages:
                logger.info("No supported languages detected for CodeQL")
                return findings
            
            # Create CodeQL database
            db_path = await self._create_database(target, languages, scan_id)
            
            # Run analysis for each language
            for language in languages:
                lang_findings = await self._analyze_database(db_path, language, scan_id)
                findings.extend(lang_findings)
            
            # Cleanup
            await self._cleanup_database(db_path)
            
        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise
        
        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        
        return findings
    
    async def is_available(self) -> bool:
        """Check if CodeQL is available."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.codeql_path, "version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """Get CodeQL version."""
        try:
            stdout, stderr, code = await self.run_command(
                [self.codeql_path, "version"],
                timeout=30
            )
            return stdout.strip() if code == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _detect_languages(self, repo_path: str) -> List[str]:
        """Detect supported languages in repository."""
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
            if language in self.config.sast_languages:
                for pattern in patterns:
                    if list(Path(repo_path).rglob(pattern)):
                        detected.append(language)
                        break
        
        return detected
    
    async def _create_database(
        self, 
        repo_path: str, 
        languages: List[str], 
        scan_id: str
    ) -> str:
        """Create CodeQL database."""
        db_path = tempfile.mkdtemp(prefix=f"codeql-{scan_id}-")
        
        for language in languages:
            lang_db_path = Path(db_path) / language
            
            cmd = [
                self.codeql_path,
                "database", "create",
                str(lang_db_path),
                "--language", language,
                "--source-root", repo_path,
                "--overwrite"
            ]
            
            logger.info(f"Creating CodeQL database for {language}")
            
            try:
                stdout, stderr, code = await self.run_command(cmd, timeout=600)
                if code != 0:
                    logger.warning(f"CodeQL database creation failed for {language}: {stderr}")
            except Exception as e:
                logger.error(f"Error creating CodeQL database: {e}")
        
        return db_path
    
    async def _analyze_database(
        self, 
        db_path: str, 
        language: str, 
        scan_id: str
    ) -> List[Finding]:
        """Analyze CodeQL database."""
        findings = []
        lang_db_path = Path(db_path) / language
        
        if not lang_db_path.exists():
            return findings
        
        # Create output file
        output_file = Path(db_path) / f"{language}-results.sarif"
        
        cmd = [
            self.codeql_path,
            "database", "analyze",
            str(lang_db_path),
            f"{language}-security-and-quality",
            "--format", "sarif-latest",
            "--output", str(output_file)
        ]
        
        try:
            stdout, stderr, code = await self.run_command(cmd, timeout=900)
            
            if output_file.exists():
                findings = self._parse_sarif_output(str(output_file), scan_id, language)
                
        except Exception as e:
            logger.error(f"CodeQL analysis failed: {e}")
        
        return findings
    
    def _parse_sarif_output(
        self, 
        output_file: str, 
        scan_id: str, 
        language: str
    ) -> List[Finding]:
        """Parse CodeQL SARIF output."""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                sarif_data = json.load(f)
            
            for run in sarif_data.get("runs", []):
                for result in run.get("results", []):
                    finding = self._create_finding_from_sarif(
                        result, run, scan_id, language, len(findings)
                    )
                    if finding:
                        findings.append(finding)
                        
        except Exception as e:
            logger.error(f"Error parsing SARIF output: {e}")
        
        return findings
    
    def _create_finding_from_sarif(
        self, 
        result: Dict[str, Any],
        run: Dict[str, Any],
        scan_id: str,
        language: str,
        index: int
    ) -> Optional[Finding]:
        """Create Finding from SARIF result."""
        try:
            rule_id = result.get("ruleId", "unknown")
            rule_info = self._get_rule_info(run, rule_id)
            
            # Get location
            location = {}
            for loc in result.get("locations", []):
                physical = loc.get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})
                
                location = {
                    "file": artifact.get("uri", ""),
                    "line": region.get("startLine", 0),
                    "column": region.get("startColumn", 0),
                    "end_line": region.get("endLine"),
                    "end_column": region.get("endColumn")
                }
                break
            
            finding = Finding(
                id=f"codeql-{scan_id}-{index}",
                source="codeql",
                rule_id=rule_id,
                title=rule_info.get("name", rule_id),
                description=result.get("message", {}).get("text", ""),
                severity=self._normalize_codeql_severity(
                    rule_info.get("defaultConfiguration", {}).get("level", "warning")
                ),
                confidence="High",
                location=location,
                recommendation=rule_info.get("help", {}).get("text", ""),
                scan_type=ScanType.SAST,
                raw_output=result
            )
            
            # Add CWE from tags
            tags = rule_info.get("properties", {}).get("tags", [])
            for tag in tags:
                if tag.startswith("external/cwe/cwe-"):
                    finding.cwe = tag.replace("external/cwe/", "").upper()
                    break
            
            return finding
            
        except Exception as e:
            logger.error(f"Failed to create finding from SARIF: {e}")
            return None
    
    def _get_rule_info(self, run: Dict[str, Any], rule_id: str) -> Dict:
        """Get rule information from SARIF run."""
        tool = run.get("tool", {}).get("driver", {})
        rules = tool.get("rules", [])
        
        for rule in rules:
            if rule.get("id") == rule_id:
                return rule
        
        return {}
    
    def _normalize_codeql_severity(self, level: str) -> Severity:
        """Normalize CodeQL severity level."""
        severity_map = {
            "error": Severity.HIGH,
            "warning": Severity.MEDIUM,
            "note": Severity.LOW,
            "none": Severity.INFO
        }
        return severity_map.get(level.lower(), Severity.MEDIUM)
    
    async def _cleanup_database(self, db_path: str):
        """Clean up CodeQL database."""
        try:
            shutil.rmtree(db_path, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error cleaning up CodeQL database: {e}")
