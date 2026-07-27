"""
Enhanced result parsing utilities for normalizing scanner outputs
with compliance mapping and threat analysis
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.compliance_analyzer import compliance_service

from models.report import ScannerType, SeverityLevel, VulnerabilityFinding

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
    
    def enhance_finding_with_analysis(
        self, 
        finding: VulnerabilityFinding,
        repository_context: Optional[Dict[str, Any]] = None,
        business_context: Optional[Dict[str, Any]] = None
    ) -> VulnerabilityFinding:
        """
        Enhance finding with compliance mapping and threat analysis
        
        Args:
            finding: The vulnerability finding to enhance
            repository_context: Repository context information
            business_context: Business context information
            
        Returns:
            Enhanced vulnerability finding
        """
        try:
            # Perform compliance mapping
            compliance_mappings = compliance_service.analyze_finding_compliance(finding)
            finding.compliance_mappings = compliance_mappings
            
            # Perform threat analysis
            threat_analysis = compliance_service.perform_threat_analysis(finding, repository_context)
            finding.threat_analysis = threat_analysis
            
            # Calculate CVSS score
            cvss_score = compliance_service.calculate_cvss_score(finding, repository_context)
            finding.cvss_score = cvss_score
            
            # Calculate business impact
            if business_context:
                business_impact = compliance_service.calculate_business_impact(finding, business_context)
                finding.business_impact = business_impact
            
            # Calculate overall risk level
            risk_level = compliance_service.calculate_risk_level(finding, business_context)
            finding.risk_level = risk_level
            
            # Add categorization tags
            finding.tags = self._generate_tags(finding)
            
            # Calculate exploitability score
            finding.exploitability_score = self._calculate_exploitability_score(finding)
            
            # Calculate false positive score
            finding.false_positive_score = self._calculate_false_positive_score(finding)
            
            # Set remediation priority
            finding.remediation_priority = threat_analysis.mitigation_priority
            
        except Exception as e:
            logger.error(f"Failed to enhance finding with analysis: {e}")
        
        return finding
    
    def _generate_tags(self, finding: VulnerabilityFinding) -> List[str]:
        """Generate categorization tags for the finding"""
        tags = []
        
        # Add scanner tag
        tags.append(f"scanner:{finding.scanner.value}")
        
        # Add severity tag
        tags.append(f"severity:{finding.severity.value}")
        
        # Add threat category tags
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            for category in finding.threat_analysis.threat_categories:
                tags.append(f"category:{category.value}")
        
        # Add compliance framework tags
        if finding.compliance_mappings:
            for mapping in finding.compliance_mappings:
                tags.append(f"compliance:{mapping.framework.value}")
        
        # Add CWE tag
        if finding.cwe_id:
            tags.append(f"cwe:{finding.cwe_id}")
        
        # Add OWASP tag
        if finding.owasp_category:
            tags.append(f"owasp:{finding.owasp_category}")
        
        # Add language/file type tags
        if finding.file_path:
            file_extension = Path(finding.file_path).suffix.lower()
            if file_extension:
                tags.append(f"filetype:{file_extension[1:]}")  # Remove the dot
        
        return tags
    
    def _calculate_exploitability_score(self, finding: VulnerabilityFinding) -> float:
        """Calculate numerical exploitability score (0-10)"""
        
        # Base score from severity
        severity_scores = {
            SeverityLevel.CRITICAL: 9.0,
            SeverityLevel.HIGH: 7.0,
            SeverityLevel.MEDIUM: 5.0,
            SeverityLevel.LOW: 3.0,
            SeverityLevel.INFO: 1.0
        }
        
        base_score = severity_scores.get(finding.severity, 5.0)
        
        # Adjust based on threat categories
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            from models.report import ThreatCategory
            
            high_exploitability_categories = [
                ThreatCategory.INJECTION,
                ThreatCategory.SECRETS,
                ThreatCategory.AUTHENTICATION
            ]
            
            category_boost = sum(1.5 for cat in finding.threat_analysis.threat_categories 
                               if cat in high_exploitability_categories)
            base_score = min(base_score + category_boost, 10.0)
        
        # Adjust based on CVSS score if available
        if finding.cvss_score and finding.cvss_score.base_score:
            # Average the severity-based score with CVSS
            base_score = (base_score + finding.cvss_score.base_score) / 2
        
        return round(base_score, 1)
    
    def _calculate_false_positive_score(self, finding: VulnerabilityFinding) -> float:
        """Calculate false positive likelihood score (0-1)"""
        
        # Base score from scanner reliability
        scanner_fp_rates = {
            "semgrep": 0.1,    # Low false positive rate
            "safety": 0.05,    # Very low false positive rate
            "trivy": 0.1,      # Low false positive rate
            "gitleaks": 0.15,  # Low-medium false positive rate
            "bandit": 0.25,    # Medium false positive rate
            "lynis": 0.3       # Medium-high false positive rate
        }
        
        base_fp = scanner_fp_rates.get(finding.scanner.value, 0.2)
        
        # Adjust based on confidence
        if finding.confidence:
            confidence_lower = finding.confidence.lower()
            if confidence_lower in ["high", "certain"]:
                base_fp *= 0.5  # Reduce FP likelihood
            elif confidence_lower in ["low", "uncertain"]:
                base_fp *= 1.5  # Increase FP likelihood
        
        # Adjust based on threat analysis
        if finding.threat_analysis:
            fp_assessment = finding.threat_analysis.false_positive_likelihood
            if fp_assessment:
                fp_multipliers = {
                    "very_low": 0.5,
                    "low": 0.7,
                    "medium": 1.0,
                    "high": 1.3,
                    "very_high": 1.5
                }
                base_fp *= fp_multipliers.get(fp_assessment, 1.0)
        
        return round(min(base_fp, 1.0), 2)


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
            extra = result.get('extra', {})
            metadata = extra.get('metadata', {})
            
            # Extract remediation from Semgrep metadata (fix, fix_regex, or message)
            remediation = None
            remediation_code = None
            fix_effort = None
            
            # Semgrep provides fix suggestions in metadata
            if metadata.get('fix'):
                remediation = metadata.get('fix')
            elif metadata.get('fix_regex'):
                remediation = f"Apply regex fix: {metadata.get('fix_regex')}"
            elif metadata.get('remediation'):
                remediation = metadata.get('remediation')
            
            # Extract fix effort based on metadata
            if metadata.get('impact'):
                impact = metadata.get('impact', '').lower()
                if 'high' in impact:
                    fix_effort = 'high'
                elif 'low' in impact:
                    fix_effort = 'low'
                else:
                    fix_effort = 'medium'
            
            finding = VulnerabilityFinding(
                id=f"semgrep-{result.get('check_id', '')}-{hash(str(result))}",
                scanner=self.scanner_type,
                rule_id=result.get('check_id', ''),
                title=extra.get('message', 'Semgrep Finding'),
                description=extra.get('message', ''),
                severity=self._normalize_severity(
                    extra.get('severity', 'medium')
                ),
                confidence=metadata.get('confidence'),
                file_path=result.get('path', ''),
                line_start=result.get('start', {}).get('line'),
                line_end=result.get('end', {}).get('line'),
                column_start=result.get('start', {}).get('col'),
                column_end=result.get('end', {}).get('col'),
                code_snippet=extra.get('lines'),
                cwe_id=self._extract_cwe_from_text(str(extra)),
                owasp_category=metadata.get('owasp'),
                references=metadata.get('references', []),
                metadata=metadata,
                remediation=remediation,
                remediation_code=remediation_code,
                fix_effort=fix_effort
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
                    # Generate remediation from Trivy data
                    pkg_name = vuln.get('PkgName', '')
                    installed_version = vuln.get('InstalledVersion', '')
                    fixed_version = vuln.get('FixedVersion', '')
                    
                    remediation = None
                    if fixed_version:
                        remediation = f"Update {pkg_name} from version {installed_version} to {fixed_version} or later to resolve this vulnerability."
                    elif pkg_name:
                        remediation = f"Review and update {pkg_name} (currently {installed_version}) to the latest secure version. Check vendor advisories for patches."
                    
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
                        remediation=remediation,
                        fix_effort='low' if fixed_version else 'medium',
                        metadata={
                            'package_name': pkg_name,
                            'installed_version': installed_version,
                            'fixed_version': fixed_version,
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


class SecretAnalyzer:
    """
    Analyzes detected secrets to determine if they are:
    - Real credentials (high risk)
    - Example/placeholder credentials (low risk but still flagged)
    - Test/dummy credentials (informational)
    
    This helps reduce false positive anxiety while still alerting about potential issues.
    """
    
    # Patterns that indicate a placeholder/example credential
    PLACEHOLDER_PATTERNS = [
        # Generic placeholders
        r'^your[-_]?.*[-_]?here$',
        r'^<.*>$',                          # <your_api_key>
        r'^\[.*\]$',                        # [your_api_key]
        r'^\{.*\}$',                        # {your_api_key}
        r'^xxx+$',                          # xxx, xxxx
        r'^X{3,}$',                         # XXX, XXXX
        r'^\*{3,}$',                        # ***, ****
        r'^\.{3,}$',                        # ..., ....
        r'^_+$',                            # ___, ____
        r'^placeholder',
        r'^example',
        r'^sample',
        r'^dummy',
        r'^fake',
        r'^test[-_]?',
        r'^demo[-_]?',
        r'^my[-_]?',
        r'^changeme',
        r'^replace[-_]?me',
        r'^insert[-_]?',
        r'^enter[-_]?',
        r'^todo',
        r'^fixme',
        r'^your[-_]?',
        r'^put[-_]?',
        r'^add[-_]?',
        r'^fill[-_]?in',
        r'^update[-_]?this',
        r'^set[-_]?this',
        
        # Common example passwords
        r'^password$',
        r'^password\d+$',
        r'^pass\d*$',
        r'^secret$',
        r'^secret\d+$',
        r'^admin$',
        r'^admin\d+$',
        r'^root$',
        r'^user$',
        r'^guest$',
        r'^default$',
        r'^qwerty',
        r'^123456',
        r'^abcdef',
        r'^abc123',
        r'^letmein',
        r'^welcome',
        r'^monkey',
        r'^dragon',
        r'^master',
        r'^login',
        r'^passw0rd',
        r'^iloveyou',
        r'^princess',
        r'^sunshine',
        r'^12345',
        
        # API key placeholders
        r'^sk[-_]?test',
        r'^pk[-_]?test',
        r'^api[-_]?key[-_]?here',
        r'^your[-_]?api[-_]?key',
        r'^insert[-_]?api[-_]?key',
        r'^api[-_]?key[-_]?goes[-_]?here',
        r'^put[-_]?your[-_]?key',
        r'^replace[-_]?with[-_]?',
        r'^sk_test_',
        r'^pk_test_',
        r'^test_api_key',
        r'^development_key',
        r'^dev_key',
        r'^staging_key',
        r'^sandbox',
    ]
    
    # File patterns that commonly contain example credentials
    EXAMPLE_FILE_PATTERNS = [
        r'\.example$',
        r'\.sample$',
        r'\.template$',
        r'\.dist$',
        r'\.default$',
        r'-example\.',
        r'-sample\.',
        r'-template\.',
        r'\.env\.example',
        r'\.env\.sample',
        r'\.env\.template',
        r'\.env\.local\.example',
        r'config\.example\.',
        r'settings\.example\.',
        r'README\.md$',
        r'README\.txt$',
        r'readme\.',
        r'CONTRIBUTING\.md$',
        r'INSTALL\.md$',
        r'SETUP\.md$',
        r'CONFIGURATION\.md$',
        r'docs[/\\]',
        r'documentation[/\\]',
        r'examples[/\\]',
        r'samples[/\\]',
        r'templates[/\\]',
        r'fixtures[/\\]',
        r'__tests__[/\\]',
        r'tests?[/\\]',
        r'spec[/\\]',
        r'\.md$',
        r'\.rst$',
        r'\.txt$',
        r'docker-compose\.yml\.example',
        r'docker-compose\.sample\.yml',
    ]
    
    # Entropy thresholds for different secret types
    ENTROPY_THRESHOLDS = {
        'api_key': 3.5,
        'password': 2.5,
        'token': 4.0,
        'secret': 3.0,
        'default': 3.0
    }
    
    @classmethod
    def calculate_entropy(cls, secret: str) -> float:
        """Calculate Shannon entropy of a string"""
        import math
        if not secret:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in secret:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        length = len(secret)
        entropy = 0.0
        for count in freq.values():
            if count > 0:
                prob = count / length
                entropy -= prob * math.log2(prob)
        
        return entropy
    
    @classmethod
    def is_example_file(cls, file_path: str) -> bool:
        """Check if file is likely an example/documentation file"""
        if not file_path:
            return False
        
        file_path_lower = file_path.lower().replace('\\', '/')
        
        for pattern in cls.EXAMPLE_FILE_PATTERNS:
            if re.search(pattern, file_path_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def is_placeholder_secret(cls, secret: str) -> bool:
        """Check if secret matches common placeholder patterns"""
        if not secret:
            return False
        
        secret_lower = secret.lower().strip()
        
        # Check against placeholder patterns
        for pattern in cls.PLACEHOLDER_PATTERNS:
            if re.match(pattern, secret_lower, re.IGNORECASE):
                return True
        
        # Check for repeated characters (like aaaa, 1111)
        if len(set(secret)) <= 2 and len(secret) > 3:
            return True
        
        # Check for sequential patterns
        if secret_lower in ['abcdefghijklmnopqrstuvwxyz', '0123456789', 'qwertyuiop']:
            return True
        
        return False
    
    @classmethod
    def analyze_secret(cls, secret: str, file_path: str, secret_type: str = 'default') -> Dict[str, Any]:
        """
        Comprehensive secret analysis
        
        Returns:
            Dict with analysis results:
            - is_likely_real: bool - True if secret appears to be real
            - is_placeholder: bool - True if secret matches placeholder patterns
            - is_example_file: bool - True if file is an example/doc file
            - confidence: str - 'high', 'medium', 'low'
            - entropy: float - Shannon entropy of secret
            - adjusted_severity: str - Recommended severity level
            - reason: str - Human-readable explanation
            - recommendation: str - What user should do
        """
        analysis = {
            'is_likely_real': True,
            'is_placeholder': False,
            'is_example_file': False,
            'confidence': 'medium',
            'entropy': 0.0,
            'adjusted_severity': 'high',
            'reason': '',
            'recommendation': ''
        }
        
        # Check if file is example/documentation
        analysis['is_example_file'] = cls.is_example_file(file_path)
        
        # Check if secret is a placeholder
        analysis['is_placeholder'] = cls.is_placeholder_secret(secret)
        
        # Calculate entropy
        analysis['entropy'] = cls.calculate_entropy(secret)
        
        # Get entropy threshold for this secret type
        threshold = cls.ENTROPY_THRESHOLDS.get(
            secret_type.lower() if secret_type else 'default',
            cls.ENTROPY_THRESHOLDS['default']
        )
        
        low_entropy = analysis['entropy'] < threshold
        
        # Determine if secret is likely real
        reasons = []
        
        if analysis['is_placeholder']:
            analysis['is_likely_real'] = False
            reasons.append('matches placeholder pattern')
        
        if analysis['is_example_file']:
            if not analysis['is_placeholder'] and not low_entropy:
                # High entropy secret in example file - could be accidentally committed!
                analysis['is_likely_real'] = True
                reasons.append('HIGH ENTROPY secret in example file - may be accidentally committed!')
                analysis['confidence'] = 'medium'
            else:
                analysis['is_likely_real'] = False
                reasons.append('found in example/documentation file')
        
        if low_entropy and not analysis['is_example_file']:
            # Low entropy in regular file - suspicious
            if analysis['is_placeholder']:
                analysis['is_likely_real'] = False
                reasons.append('low entropy placeholder')
            else:
                # Low entropy but not a known placeholder - might still be a weak password
                analysis['is_likely_real'] = True
                reasons.append('low entropy (weak credential) but in production file')
                analysis['confidence'] = 'low'
        
        # Set adjusted severity and recommendation
        if not analysis['is_likely_real']:
            if analysis['is_example_file'] and analysis['is_placeholder']:
                analysis['adjusted_severity'] = 'info'
                analysis['recommendation'] = (
                    'This appears to be a placeholder/example credential in a documentation or example file. '
                    'No immediate action required, but ensure real credentials are never committed to this file.'
                )
            elif analysis['is_placeholder']:
                analysis['adjusted_severity'] = 'low'
                analysis['recommendation'] = (
                    'This appears to be a placeholder credential. Verify it is not used in production. '
                    'Consider using more obviously fake values like "REPLACE_ME_WITH_REAL_KEY".'
                )
            elif analysis['is_example_file']:
                analysis['adjusted_severity'] = 'low'
                analysis['recommendation'] = (
                    'Secret found in example/documentation file. While likely intentional, '
                    'verify this is not a real credential accidentally committed. Check entropy and pattern.'
                )
            analysis['confidence'] = 'high'
        else:
            if analysis['is_example_file']:
                # Real-looking secret in example file - DANGER
                analysis['adjusted_severity'] = 'critical'
                analysis['recommendation'] = (
                    '⚠️ CAUTION: This secret has high entropy and may be a REAL credential accidentally '
                    'committed to an example file! Immediately verify if this is a real secret. '
                    'If real: 1) Rotate immediately, 2) Remove from git history, 3) Add to .gitignore'
                )
                analysis['confidence'] = 'high'
            else:
                analysis['adjusted_severity'] = 'high'
                analysis['recommendation'] = (
                    'This appears to be a real credential. '
                    '1) Rotate/revoke immediately, 2) Remove from code and git history, '
                    '3) Use environment variables or secrets manager'
                )
        
        analysis['reason'] = '; '.join(reasons) if reasons else 'Standard secret detection'
        
        return analysis


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
                rule_id = item.get('RuleID', '')
                secret_type = item.get('Description', rule_id)
                detected_file_path = item.get('File', '')
                secret_value = item.get('Secret', '')
                
                # Analyze the secret to determine if it's real or placeholder
                secret_analysis = SecretAnalyzer.analyze_secret(
                    secret=secret_value,
                    file_path=detected_file_path,
                    secret_type=secret_type
                )
                
                # Adjust severity based on analysis
                severity_map = {
                    'critical': SeverityLevel.CRITICAL,
                    'high': SeverityLevel.HIGH,
                    'medium': SeverityLevel.MEDIUM,
                    'low': SeverityLevel.LOW,
                    'info': SeverityLevel.INFO
                }
                adjusted_severity = severity_map.get(
                    secret_analysis['adjusted_severity'], 
                    SeverityLevel.HIGH
                )
                
                # Create title with context
                if not secret_analysis['is_likely_real']:
                    if secret_analysis['is_placeholder']:
                        title = f"[Placeholder] Example credential detected: {secret_type}"
                    else:
                        title = f"[Example File] Credential in documentation: {secret_type}"
                else:
                    if secret_analysis['is_example_file']:
                        title = f"⚠️ [VERIFY] Possible real secret in example file: {secret_type}"
                    else:
                        title = f"🚨 Secret detected: {secret_type}"
                
                # Generate context-aware remediation
                remediation = secret_analysis['recommendation']
                if secret_analysis['is_likely_real']:
                    remediation += (
                        f"\n\nSteps to remediate:\n"
                        f"1. Immediately rotate or revoke the exposed {secret_type}.\n"
                        f"2. Remove the secret from {detected_file_path} and git history using BFG Repo-Cleaner or git filter-branch.\n"
                        f"3. Store secrets securely using environment variables or secrets managers (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault).\n"
                        f"4. Add patterns to .gitignore to prevent future commits of sensitive files."
                    )
                
                finding = VulnerabilityFinding(
                    id=f"gitleaks-{rule_id}-{hash(str(item))}",
                    scanner=self.scanner_type,
                    rule_id=rule_id,
                    title=title,
                    description=item.get('Description', '') + f"\n\nAnalysis: {secret_analysis['reason']}",
                    severity=adjusted_severity,
                    file_path=detected_file_path,
                    line_start=item.get('StartLine'),
                    line_end=item.get('EndLine'),
                    column_start=item.get('StartColumn'),
                    column_end=item.get('EndColumn'),
                    code_snippet=secret_value,
                    remediation=remediation,
                    fix_effort='low' if not secret_analysis['is_likely_real'] else 'medium',
                    metadata={
                        'commit': item.get('Commit', ''),
                        'entropy': item.get('Entropy') or secret_analysis['entropy'],
                        'author': item.get('Author', ''),
                        'email': item.get('Email', ''),
                        'date': item.get('Date', ''),
                        'message': item.get('Message', ''),
                        'tags': item.get('Tags', []),
                        # Secret analysis metadata
                        'is_likely_real': secret_analysis['is_likely_real'],
                        'is_placeholder': secret_analysis['is_placeholder'],
                        'is_example_file': secret_analysis['is_example_file'],
                        'analysis_confidence': secret_analysis['confidence'],
                        'calculated_entropy': secret_analysis['entropy']
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


class BanditResultParser(BaseResultParser):
    """Parser for Bandit JSON output"""
    
    def __init__(self):
        super().__init__(ScannerType.BANDIT)
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """Parse Bandit JSON output"""
        try:
            data = json.loads(output)
            findings = []
            
            for result in data.get('results', []):
                finding = VulnerabilityFinding(
                    id=f"bandit-{result.get('test_id', '')}-{hash(str(result))}",
                    scanner=self.scanner_type,
                    rule_id=result.get('test_id', ''),
                    title=result.get('test_name', 'Bandit Security Issue'),
                    description=result.get('issue_text', ''),
                    severity=self._normalize_bandit_severity(
                        result.get('issue_severity', 'MEDIUM')
                    ),
                    confidence=result.get('issue_confidence', ''),
                    file_path=result.get('filename', ''),
                    line_start=result.get('line_number'),
                    line_end=result.get('line_number'),
                    code_snippet=result.get('code', ''),
                    cwe_id=self._extract_cwe_from_text(
                        result.get('more_info', '') + ' ' + result.get('issue_text', '')
                    ),
                    references=[result.get('more_info', '')] if result.get('more_info') else [],
                    metadata={
                        'test_id': result.get('test_id', ''),
                        'line_range': result.get('line_range', []),
                        'col_offset': result.get('col_offset'),
                        'test_name': result.get('test_name', '')
                    }
                )
                findings.append(finding)
            
            return findings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON output: {e}")
            return []
    
    def _normalize_bandit_severity(self, severity: str) -> SeverityLevel:
        """Normalize Bandit severity levels"""
        severity_lower = severity.lower().strip()
        
        if severity_lower == 'high':
            return SeverityLevel.HIGH
        elif severity_lower == 'medium':
            return SeverityLevel.MEDIUM
        elif severity_lower == 'low':
            return SeverityLevel.LOW
        else:
            return SeverityLevel.MEDIUM


class SafetyResultParser(BaseResultParser):
    """Parser for Safety JSON output"""
    
    def __init__(self):
        super().__init__(ScannerType.SAFETY)
    
    def parse(self, output: str, file_path: Optional[str] = None) -> List[VulnerabilityFinding]:
        """Parse Safety JSON output"""
        try:
            data = json.loads(output)
            findings = []
            
            # Handle both direct vulnerabilities list and nested structure
            vulnerabilities = data.get('vulnerabilities', data) if isinstance(data, dict) else data
            
            if isinstance(vulnerabilities, list):
                for vuln in vulnerabilities:
                    finding = self._create_safety_finding(vuln)
                    if finding:
                        findings.append(finding)
            
            return findings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Safety JSON output: {e}")
            return []
    
    def _create_safety_finding(self, vuln: Dict[str, Any]) -> Optional[VulnerabilityFinding]:
        """Create a vulnerability finding from Safety vulnerability data"""
        try:
            # Safety vulnerability structure
            package = vuln.get('package', '')
            installed_version = vuln.get('installed_version', '')
            vulnerability_id = vuln.get('vulnerability_id', '')
            advisory = vuln.get('advisory', '')
            
            # Determine severity based on CVE or advisory content
            severity = self._determine_safety_severity(advisory, vulnerability_id)
            
            finding = VulnerabilityFinding(
                id=f"safety-{vulnerability_id}-{package}",
                scanner=self.scanner_type,
                rule_id=vulnerability_id,
                title=f"Vulnerable dependency: {package}",
                description=f"Package {package} version {installed_version} has a known vulnerability: {advisory}",
                severity=severity,
                file_path=vuln.get('dependency_file', 'requirements.txt'),
                cve_id=self._extract_cve_from_text(advisory + ' ' + vulnerability_id),
                references=self._extract_references_from_advisory(advisory),
                metadata={
                    'package': package,
                    'installed_version': installed_version,
                    'vulnerability_id': vulnerability_id,
                    'advisory': advisory,
                    'patched_versions': vuln.get('patched_versions', []),
                    'closest_patched_version': vuln.get('closest_patched_version', '')
                }
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating Safety finding: {e}")
            return None
    
    def _determine_safety_severity(self, advisory: str, vuln_id: str) -> SeverityLevel:
        """Determine severity based on advisory content and vulnerability ID"""
        advisory_lower = advisory.lower()
        
        # High severity indicators
        if any(keyword in advisory_lower for keyword in [
            'remote code execution', 'rce', 'critical', 'arbitrary code',
            'code injection', 'command injection', 'privilege escalation'
        ]):
            return SeverityLevel.CRITICAL
        
        # Medium-high severity indicators
        if any(keyword in advisory_lower for keyword in [
            'sql injection', 'xss', 'csrf', 'authentication bypass',
            'authorization bypass', 'directory traversal', 'path traversal'
        ]):
            return SeverityLevel.HIGH
        
        # Medium severity indicators
        if any(keyword in advisory_lower for keyword in [
            'denial of service', 'dos', 'information disclosure',
            'memory exhaustion', 'resource consumption'
        ]):
            return SeverityLevel.MEDIUM
        
        # Default to medium for unknown patterns
        return SeverityLevel.MEDIUM
    
    def _extract_references_from_advisory(self, advisory: str) -> List[str]:
        """Extract reference URLs from advisory text"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, advisory)
        return urls[:5]  # Limit to first 5 URLs


class UnifiedResultParser:
    """Enhanced unified parser that handles all scanner types"""
    
    def __init__(self):
        self.parsers = {
            ScannerType.SEMGREP: SemgrepResultParser(),
            ScannerType.TRIVY: TrivyResultParser(),
            ScannerType.GITLEAKS: GitLeaksResultParser(),
            ScannerType.LYNIS: LynisResultParser(),
            ScannerType.BANDIT: BanditResultParser(),
            ScannerType.SAFETY: SafetyResultParser()
        }
    
    def parse_results(
        self,
        scanner_type: ScannerType,
        output: str,
        file_path: Optional[str] = None,
        repository_context: Optional[Dict] = None,
        business_context: Optional[Dict] = None
    ) -> List[VulnerabilityFinding]:
        """
        Parse scanner results using appropriate parser and enhance with compliance analysis
        
        Args:
            scanner_type: Type of scanner that generated the output
            output: Raw scanner output
            file_path: Optional path to output file
            repository_context: Optional repository metadata for enhanced analysis
            business_context: Optional business context for risk assessment
            
        Returns:
            List of normalized vulnerability findings with compliance analysis
        """
        parser = self.parsers.get(scanner_type)
        if not parser:
            logger.error(f"No parser available for scanner type: {scanner_type}")
            return []
        
        try:
            findings = parser.parse(output, file_path)
            
            # Enhance findings with compliance and threat analysis
            enhanced_findings = []
            for finding in findings:
                enhanced_finding = parser.enhance_finding_with_analysis(
                    finding, repository_context, business_context
                )
                enhanced_findings.append(enhanced_finding)
            
            logger.info(f"Parsed and enhanced {len(enhanced_findings)} findings from {scanner_type.value}")
            return enhanced_findings
            
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
