"""
Result parsing utilities for normalizing scanner outputs
"""
import json
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from models.report import VulnerabilityFinding, ScannerType, SeverityLevel

logger = logging.getLogger(__name__)


class ResultParseError(Exception):
    """Custom exception for result parsing errors"""
    pass


class BaseResultParser:
    """Base class for scanner result parsers"""
    
    def __init__(self, scanner_type: ScannerType):
        self.scanner_type = scanner_type
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """
        Parse scanner output into normalized findings
        
        Args:
            output: Raw scanner output
            file_path: Optional path to output file
            
        Returns:
            List of normalized vulnerability findings
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    def _normalize_severity(self, severity: str) -> SeverityLevel:
        """Normalize severity level to standard enum"""
        severity_lower = severity.lower().strip()
        
        if severity_lower in ['critical', 'crit']:
            return SeverityLevel.CRITICAL
        elif severity_lower in ['high', 'error']:
            return SeverityLevel.HIGH
        elif severity_lower in ['medium', 'moderate', 'warning', 'warn']:
            return SeverityLevel.MEDIUM
        elif severity_lower in ['low', 'minor']:
            return SeverityLevel.LOW
        elif severity_lower in ['info', 'information', 'note']:
            return SeverityLevel.INFO
        else:
            logger.warning(f"Unknown severity level: {severity}, defaulting to MEDIUM")
            return SeverityLevel.MEDIUM
    
    def _extract_cwe_from_text(self, text: str) -> Optional[str]:
        """Extract CWE ID from text"""
        cwe_pattern = r'CWE-(\d+)'
        match = re.search(cwe_pattern, text, re.IGNORECASE)
        return f"CWE-{match.group(1)}" if match else None
    
    def _extract_cve_from_text(self, text: str) -> Optional[str]:
        """Extract CVE ID from text"""
        cve_pattern = r'CVE-\d{4}-\d{4,}'
        match = re.search(cve_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None


class SemgrepResultParser(BaseResultParser):
    """Parser for Semgrep SARIF/JSON output"""
    
    def __init__(self):
        super().__init__(ScannerType.SEMGREP)
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """Parse Semgrep SARIF or JSON output"""
        try:
            data = json.loads(output)
            findings = []
            
            # Handle SARIF format
            if 'runs' in data:
                findings.extend(self._parse_sarif(data))
            # Handle Semgrep JSON format
            elif 'results' in data:
                findings.extend(self._parse_semgrep_json(data))
            else:
                logger.warning("Unknown Semgrep output format")
            
            return findings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep JSON output: {e}")
            return []
    
    def _parse_sarif(self, data: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """Parse SARIF format output"""
        findings = []
        
        for run in data.get('runs', []):
            tool = run.get('tool', {})
            driver = tool.get('driver', {})
            rules = {rule['id']: rule for rule in driver.get('rules', [])}
            
            for result in run.get('results', []):
                rule_id = result.get('ruleId', '')
                rule = rules.get(rule_id, {})
                
                for location in result.get('locations', []):
                    finding = self._create_finding_from_sarif_location(
                        result, rule, location
                    )
                    if finding:
                        findings.append(finding)
        
        return findings
    
    def _parse_semgrep_json(self, data: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """Parse Semgrep JSON format output"""
        findings = []
        
        for result in data.get('results', []):
            finding = VulnerabilityFinding(
                id=f"semgrep-{result.get('check_id', '')}-{hash(str(result))}",
                scanner=self.scanner_type,
                rule_id=result.get('check_id', ''),
                title=result.get('extra', {}).get('message', 'Semgrep Finding'),
                description=result.get('extra', {}).get('message', ''),
                severity=self._normalize_severity(
                    result.get('extra', {}).get('severity', 'medium')
                ),
                confidence=result.get('extra', {}).get('metadata', {}).get('confidence'),
                file_path=result.get('path', ''),
                line_start=result.get('start', {}).get('line'),
                line_end=result.get('end', {}).get('line'),
                column_start=result.get('start', {}).get('col'),
                column_end=result.get('end', {}).get('col'),
                code_snippet=result.get('extra', {}).get('lines'),
                cwe_id=self._extract_cwe_from_text(str(result.get('extra', {}))),
                owasp_category=result.get('extra', {}).get('metadata', {}).get('owasp'),
                references=result.get('extra', {}).get('metadata', {}).get('references', []),
                metadata=result.get('extra', {}).get('metadata', {})
            )
            findings.append(finding)
        
        return findings
    
    def _create_finding_from_sarif_location(
        self, result: Dict, rule: Dict, location: Dict
    ) -> Optional[VulnerabilityFinding]:
        """Create finding from SARIF location data"""
        try:
            physical_location = location.get('physicalLocation', {})
            artifact_location = physical_location.get('artifactLocation', {})
            region = physical_location.get('region', {})
            
            return VulnerabilityFinding(
                id=f"semgrep-sarif-{result.get('ruleId', '')}-{hash(str(location))}",
                scanner=self.scanner_type,
                rule_id=result.get('ruleId', ''),
                title=rule.get('shortDescription', {}).get('text', 'SARIF Finding'),
                description=rule.get('fullDescription', {}).get('text', ''),
                severity=self._normalize_severity(
                    result.get('level', 'warning')
                ),
                file_path=artifact_location.get('uri', ''),
                line_start=region.get('startLine'),
                line_end=region.get('endLine'),
                column_start=region.get('startColumn'),
                column_end=region.get('endColumn'),
                code_snippet=region.get('snippet', {}).get('text'),
                metadata={
                    'help_uri': rule.get('helpUri', ''),
                    'properties': rule.get('properties', {})
                }
            )
        except Exception as e:
            logger.error(f"Error creating finding from SARIF location: {e}")
            return None


class TrivyResultParser(BaseResultParser):
    """Parser for Trivy JSON output"""
    
    def __init__(self):
        super().__init__(ScannerType.TRIVY)
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """Parse Trivy JSON output"""
        try:
            data = json.loads(output)
            findings = []
            
            for result in data.get('Results', []):
                target = result.get('Target', '')
                vulnerabilities = result.get('Vulnerabilities', [])
                
                for vuln in vulnerabilities:
                    finding = VulnerabilityFinding(
                        id=f"trivy-{vuln.get('VulnerabilityID', '')}-{hash(str(vuln))}",
                        scanner=self.scanner_type,
                        rule_id=vuln.get('VulnerabilityID', ''),
                        title=vuln.get('Title', vuln.get('VulnerabilityID', '')),
                        description=vuln.get('Description', ''),
                        severity=self._normalize_severity(vuln.get('Severity', 'unknown')),
                        file_path=target,
                        cve_id=vuln.get('VulnerabilityID') if vuln.get('VulnerabilityID', '').startswith('CVE') else None,
                        cwe_id=self._extract_cwe_from_text(vuln.get('Description', '')),
                        references=vuln.get('References', []),
                        metadata={
                            'package_name': vuln.get('PkgName', ''),
                            'installed_version': vuln.get('InstalledVersion', ''),
                            'fixed_version': vuln.get('FixedVersion', ''),
                            'primary_url': vuln.get('PrimaryURL', ''),
                            'published_date': vuln.get('PublishedDate', ''),
                            'last_modified_date': vuln.get('LastModifiedDate', '')
                        }
                    )
                    findings.append(finding)
            
            return findings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Trivy JSON output: {e}")
            return []


class GitLeaksResultParser(BaseResultParser):
    """Parser for GitLeaks JSON output"""
    
    def __init__(self):
        super().__init__(ScannerType.GITLEAKS)
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """Parse GitLeaks JSON output"""
        try:
            data = json.loads(output) if output.strip().startswith('[') else [json.loads(line) for line in output.strip().split('\n') if line.strip()]
            findings = []
            
            for item in data:
                finding = VulnerabilityFinding(
                    id=f"gitleaks-{item.get('RuleID', '')}-{hash(str(item))}",
                    scanner=self.scanner_type,
                    rule_id=item.get('RuleID', ''),
                    title=f"Secret detected: {item.get('Description', item.get('RuleID', ''))}",
                    description=item.get('Description', ''),
                    severity=SeverityLevel.HIGH,  # Secrets are generally high severity
                    file_path=item.get('File', ''),
                    line_start=item.get('StartLine'),
                    line_end=item.get('EndLine'),
                    column_start=item.get('StartColumn'),
                    column_end=item.get('EndColumn'),
                    code_snippet=item.get('Secret', ''),
                    metadata={
                        'commit': item.get('Commit', ''),
                        'entropy': item.get('Entropy'),
                        'author': item.get('Author', ''),
                        'email': item.get('Email', ''),
                        'date': item.get('Date', ''),
                        'message': item.get('Message', ''),
                        'tags': item.get('Tags', [])
                    }
                )
                findings.append(finding)
            
            return findings
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse GitLeaks JSON output: {e}")
            return []


class LynisResultParser(BaseResultParser):
    """Parser for Lynis output"""
    
    def __init__(self):
        super().__init__(ScannerType.LYNIS)
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """Parse Lynis output (typically from lynis.log or report data)"""
        findings = []
        
        # Parse different Lynis output formats
        if file_path and file_path.endswith('.json'):
            findings.extend(self._parse_json_output(output))
        else:
            findings.extend(self._parse_text_output(output))
        
        return findings
    
    def _parse_json_output(self, output: str) -> List[VulnerabilityFinding]:
        """Parse Lynis JSON output if available"""
        try:
            data = json.loads(output)
            findings = []
            
            for warning in data.get('warnings', []):
                finding = VulnerabilityFinding(
                    id=f"lynis-warning-{hash(str(warning))}",
                    scanner=self.scanner_type,
                    rule_id=warning.get('test', ''),
                    title=f"Lynis Warning: {warning.get('message', '')}",
                    description=warning.get('details', warning.get('message', '')),
                    severity=SeverityLevel.MEDIUM,
                    file_path='',
                    metadata={'test': warning.get('test', '')}
                )
                findings.append(finding)
            
            for suggestion in data.get('suggestions', []):
                finding = VulnerabilityFinding(
                    id=f"lynis-suggestion-{hash(str(suggestion))}",
                    scanner=self.scanner_type,
                    rule_id=suggestion.get('test', ''),
                    title=f"Lynis Suggestion: {suggestion.get('message', '')}",
                    description=suggestion.get('details', suggestion.get('message', '')),
                    severity=SeverityLevel.LOW,
                    file_path='',
                    metadata={'test': suggestion.get('test', '')}
                )
                findings.append(finding)
            
            return findings
            
        except json.JSONDecodeError:
            return []
    
    def _parse_text_output(self, output: str) -> List[VulnerabilityFinding]:
        """Parse Lynis text output"""
        findings = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse warning lines
            if '[WARNING]' in line:
                finding = VulnerabilityFinding(
                    id=f"lynis-warning-{hash(line)}",
                    scanner=self.scanner_type,
                    rule_id='',
                    title='Lynis Security Warning',
                    description=line.replace('[WARNING]', '').strip(),
                    severity=SeverityLevel.MEDIUM,
                    file_path='',
                    metadata={'raw_line': line}
                )
                findings.append(finding)
            
            # Parse suggestion lines
            elif '[SUGGESTION]' in line:
                finding = VulnerabilityFinding(
                    id=f"lynis-suggestion-{hash(line)}",
                    scanner=self.scanner_type,
                    rule_id='',
                    title='Lynis Security Suggestion',
                    description=line.replace('[SUGGESTION]', '').strip(),
                    severity=SeverityLevel.LOW,
                    file_path='',
                    metadata={'raw_line': line}
                )
                findings.append(finding)
        
        return findings


class UnifiedResultParser:
    """Unified parser that handles all scanner types"""
    
    def __init__(self):
        self.parsers = {
            ScannerType.SEMGREP: SemgrepResultParser(),
            ScannerType.TRIVY: TrivyResultParser(),
            ScannerType.GITLEAKS: GitLeaksResultParser(),
            ScannerType.LYNIS: LynisResultParser()
        }
    
    def parse_results(
        self,
        scanner_type: ScannerType,
        output: str,
        file_path: Optional[str] = None
    ) -> List[VulnerabilityFinding]:
        """
        Parse scanner results using appropriate parser
        
        Args:
            scanner_type: Type of scanner that generated the output
            output: Raw scanner output
            file_path: Optional path to output file
            
        Returns:
            List of normalized vulnerability findings
        """
        parser = self.parsers.get(scanner_type)
        if not parser:
            logger.error(f"No parser available for scanner type: {scanner_type}")
            return []
        
        try:
            findings = parser.parse(output, file_path)
            logger.info(f"Parsed {len(findings)} findings from {scanner_type.value}")
            return findings
            
        except Exception as e:
            logger.error(f"Error parsing {scanner_type.value} results: {e}")
            return []
    
    def get_summary_stats(self, findings: List[VulnerabilityFinding]) -> Dict[str, int]:
        """Generate summary statistics from findings"""
        stats = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "total": len(findings)
        }
        
        for finding in findings:
            stats[finding.severity.value] += 1
        
        return stats


# Global parser instance
result_parser = UnifiedResultParser()
