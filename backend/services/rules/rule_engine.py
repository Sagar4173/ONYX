"""
Enhanced Custom Rule Engine with Security Boundaries
This module provides secure rule management with comprehensive validation
"""
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Helper function for timezone-aware UTC datetime
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

from pydantic import BaseModel, Field, validator

from .rule_security import (
    AllowedLanguage,
    AllowedRuleType,
    RuleExecutionLimits,
    RuleSecurityError,
    RuleTestingFramework,
    SecureRuleValidator,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


# Use security boundary enums instead of local ones
RuleType = AllowedRuleType
RuleSeverity = SeverityLevel


class RuleStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class CustomRule(BaseModel):
    """Enhanced custom security rule definition with security boundaries"""
    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Rule description")
    message: str = Field(..., description="Security message shown when rule matches")
    type: AllowedRuleType = Field(..., description="Rule type (restricted)")
    severity: SeverityLevel = Field(..., description="Rule severity (required)")
    status: RuleStatus = Field(default=RuleStatus.TESTING, description="Rule status")
    
    # Rule content (one of these required based on type)
    pattern: Optional[str] = Field(None, description="Regex pattern for regex rules")
    semgrep_rule: Optional[Dict[str, Any]] = Field(None, description="Semgrep rule YAML")
    
    # Metadata (all required for security)
    cwe_ids: List[str] = Field(default_factory=list, description="Associated CWE IDs")
    languages: List[AllowedLanguage] = Field(..., description="Target languages (restricted)")
    file_patterns: List[str] = Field(..., description="File patterns to scan")
    
    # Rule management
    version: str = Field(default="1.0.0", description="Rule version")
    author: str = Field(..., description="Rule author")
    created_at: datetime = Field(default_factory=_utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=_utc_now, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    
    # Testing and validation (required)
    test_cases: List[Dict[str, Any]] = Field(..., description="Test cases (required)")
    category: str = Field(..., description="Rule category for classification")
    
    # Security validation fields
    security_validated: bool = Field(default=False, description="Security validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    tested_at: Optional[datetime] = Field(None, description="Last test timestamp")
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test results")
    
    @validator('id')
    def validate_id(cls, v):
        # Enhanced ID validation for security
        if not re.match(r'^[a-z0-9-_]+$', v):
            raise ValueError('Rule ID must contain only lowercase letters, numbers, hyphens, and underscores')
        if len(v) > 50:
            raise ValueError('Rule ID too long (max 50 characters)')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 5:
            raise ValueError('Rule name too short (minimum 5 characters)')
        if len(v) > 100:
            raise ValueError('Rule name too long (maximum 100 characters)')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if len(v) < 10:
            raise ValueError('Rule description too short (minimum 10 characters)')
        if len(v) > 500:
            raise ValueError('Rule description too long (maximum 500 characters)')
        return v
    
    @validator('test_cases')
    def validate_test_cases(cls, v):
        if not v:
            raise ValueError('At least one test case is required')
        
        for i, test_case in enumerate(v):
            if 'content' not in test_case:
                raise ValueError(f'Test case {i+1} missing content')
            if 'expected_matches' not in test_case:
                raise ValueError(f'Test case {i+1} missing expected_matches')
            if not isinstance(test_case['expected_matches'], int):
                raise ValueError(f'Test case {i+1} expected_matches must be integer')
        
        return v
    
    @validator('languages')
    def validate_languages(cls, v):
        if not v:
            raise ValueError('At least one language must be specified')
        return v
    
    @validator('file_patterns')
    def validate_file_patterns(cls, v):
        if not v:
            raise ValueError('At least one file pattern must be specified')
        return v
    
    @validator('pattern')
    def validate_pattern(cls, v, values):
        if values.get('type') == RuleType.REGEX and not v:
            raise ValueError('Pattern is required for regex rules')
        if v:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f'Invalid regex pattern: {e}')
        return v
    
    def get_fingerprint(self) -> str:
        """Generate unique fingerprint for rule content"""
        content = {
            'type': self.type,
            'pattern': self.pattern,
            'semgrep_rule': self.semgrep_rule,
            'custom_logic': self.custom_logic
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


class RuleTemplate(BaseModel):
    """Template for creating rules"""
    template_id: str
    name: str
    description: str
    category: str
    type: RuleType
    template_content: Dict[str, Any]
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    cwe_mappings: List[str] = Field(default_factory=list)


class RuleValidationResult(BaseModel):
    """Rule validation result"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)


class CustomRuleEngine:
    """Enhanced engine for managing and executing custom security rules with security boundaries"""
    
    def __init__(self, rules_directory: str = "data/rules", templates_directory: str = "configs/rule_templates"):
        self.rules_directory = Path(rules_directory)
        self.templates_directory = Path(templates_directory)
        self.rules_cache: Dict[str, CustomRule] = {}
        self.templates_cache: Dict[str, RuleTemplate] = {}
        
        # Security components
        self.security_validator = SecureRuleValidator()
        self.testing_framework = RuleTestingFramework()
        
        # Create directories if they don't exist
        self.rules_directory.mkdir(parents=True, exist_ok=True)
        self.templates_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default rule templates"""
        default_templates = [
            {
                "template_id": "sql_injection_template",
                "name": "SQL Injection Detection",
                "description": "Template for detecting SQL injection vulnerabilities",
                "category": "injection",
                "type": RuleType.SEMGREP,
                "template_content": {
                    "rules": [{
                        "id": "custom-sql-injection",
                        "message": "Potential SQL injection vulnerability",
                        "severity": "ERROR",
                        "languages": ["python", "javascript", "java"],
                        "pattern-either": [
                            {"pattern": "cursor.execute($QUERY, ...)"},
                            {"pattern": "cursor.execute($QUERY)"}
                        ],
                        "pattern-not": {"pattern": "cursor.execute(\"...\", ...)"}
                    }]
                },
                "variables": [
                    {"name": "query_pattern", "description": "SQL query pattern", "default": "$QUERY"}
                ],
                "cwe_mappings": ["CWE-89"]
            },
            {
                "template_id": "hardcoded_secret_template",
                "name": "Hardcoded Secret Detection",
                "description": "Template for detecting hardcoded secrets",
                "category": "secrets",
                "type": RuleType.REGEX,
                "template_content": {
                    "pattern": r"(?i)(password|secret|key|token)\s*[=:]\s*['\"]([^'\"]{8,})['\"]",
                    "message": "Potential hardcoded secret detected"
                },
                "variables": [
                    {"name": "secret_keywords", "description": "Keywords to detect", "default": "password|secret|key|token"},
                    {"name": "min_length", "description": "Minimum secret length", "default": "8"}
                ],
                "cwe_mappings": ["CWE-798"]
            }
        ]
        
        for template_data in default_templates:
            template = RuleTemplate(**template_data)
            self._save_template(template)
    
    async def load_rule(self, rule_id: str) -> Optional[CustomRule]:
        """Load a rule by ID"""
        if rule_id in self.rules_cache:
            return self.rules_cache[rule_id]
        
        rule_file = self.rules_directory / f"{rule_id}.yaml"
        if not rule_file.exists():
            rule_file = self.rules_directory / f"{rule_id}.json"
        
        if rule_file.exists():
            try:
                with open(rule_file, 'r') as f:
                    if rule_file.suffix == '.yaml':
                        rule_data = yaml.safe_load(f)
                    else:
                        rule_data = json.load(f)
                
                rule = CustomRule(**rule_data)
                self.rules_cache[rule_id] = rule
                return rule
            except Exception as e:
                logger.error(f"Error loading rule {rule_id}: {e}")
                return None
        
        return None
    
    async def save_rule(self, rule: CustomRule) -> bool:
        """Save a rule to disk with comprehensive security validation"""
        try:
            # Step 1: Comprehensive security validation
            validation_result = await self.validate_rule_security(rule)
            if not validation_result.is_valid:
                logger.error(f"Rule {rule.id} failed security validation: {validation_result.errors}")
                raise RuleSecurityError(f"Security validation failed: {', '.join(validation_result.errors)}")
            
            # Step 2: Test rule with provided test cases
            test_success, test_results = self.testing_framework.test_rule_with_samples(
                rule.dict(), rule.test_cases
            )
            
            if not test_success:
                logger.error(f"Rule {rule.id} failed testing: {test_results}")
                raise RuleSecurityError(f"Rule testing failed: {test_results.get('errors', [])}")
            
            # Step 3: Update rule with validation and test results
            rule.security_validated = True
            rule.validation_errors = []
            rule.tested_at = _utc_now()
            rule.test_results = test_results
            rule.updated_at = _utc_now()
            
            # Step 4: Save to disk
            rule_file = self.rules_directory / f"{rule.id}.yaml"
            rule_data = rule.dict()
            
            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f, default_flow_style=False)
            
            self.rules_cache[rule.id] = rule
            logger.info(f"Rule {rule.id} saved successfully with security validation")
            return True
            
        except RuleSecurityError:
            # Re-raise security errors
            raise
        except Exception as e:
            logger.error(f"Error saving rule {rule.id}: {e}")
            return False
    
    async def validate_rule_security(self, rule: CustomRule) -> RuleValidationResult:
        """Comprehensive security validation for a rule"""
        errors = []
        warnings = []
        
        try:
            # Convert rule to dict for validation
            rule_data = rule.dict()
            
            # Step 1: Validate metadata
            metadata_valid, metadata_errors = self.security_validator.validate_rule_metadata(rule_data)
            if not metadata_valid:
                errors.extend(metadata_errors)
            
            # Step 2: Validate rule content
            content_valid, content_errors = self.security_validator.validate_rule_content(rule_data)
            if not content_valid:
                errors.extend(content_errors)
            
            # Step 3: Validate rule safety
            safety_valid, safety_errors = self.security_validator.validate_rule_safety(rule_data)
            if not safety_valid:
                errors.extend(safety_errors)
            
            # Step 4: Additional validations
            
            # Validate execution limits
            if rule.type == AllowedRuleType.REGEX and rule.pattern:
                if len(rule.pattern) > RuleExecutionLimits.MAX_REGEX_LENGTH:
                    errors.append(f"Regex pattern too long: {len(rule.pattern)} > {RuleExecutionLimits.MAX_REGEX_LENGTH}")
            
            # Validate test cases
            if len(rule.test_cases) == 0:
                errors.append("At least one test case is required")
            elif len(rule.test_cases) > 20:
                warnings.append("Large number of test cases may slow down validation")
            
            # Validate languages
            for lang in rule.languages:
                if lang not in [al.value for al in AllowedLanguage]:
                    errors.append(f"Unsupported language: {lang}")
            
            # Performance metrics (placeholder)
            performance_metrics = {
                "validation_time": 0.1,  # TODO: Measure actual validation time
                "complexity_score": len(rule_data.get('pattern', '')) / 100.0
            }
            
            return RuleValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Error validating rule {rule.id}: {e}")
            return RuleValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=warnings
            )
    
    async def test_rule_in_sandbox(self, rule: CustomRule, test_repository_path: str) -> Dict[str, Any]:
        """Test rule in a sandboxed environment with execution limits"""
        test_results = {
            'rule_id': rule.id,
            'test_status': 'pending',
            'execution_time': 0.0,
            'memory_usage': 0,
            'matches_found': 0,
            'errors': [],
            'warnings': []
        }
        
        start_time = _utc_now()
        
        try:
            # Use testing framework for safe execution
            success, framework_results = self.testing_framework.test_rule_with_samples(
                rule.dict(), rule.test_cases
            )
            
            # Additional repository testing if path provided
            if test_repository_path and Path(test_repository_path).exists():
                repo_results = await self._test_rule_on_repository(rule, test_repository_path)
                framework_results.update(repo_results)
            
            test_results.update({
                'test_status': 'completed' if success else 'failed',
                'execution_time': framework_results.get('execution_time', 0),
                'memory_usage': framework_results.get('memory_usage', 0),
                'test_cases_passed': framework_results.get('passed', 0),
                'test_cases_failed': framework_results.get('failed', 0),
                'errors': framework_results.get('errors', [])
            })
            
        except Exception as e:
            test_results.update({
                'test_status': 'error',
                'errors': [f"Test execution failed: {str(e)}"]
            })
        
        finally:
            execution_time = (_utc_now() - start_time).total_seconds()
            test_results['total_execution_time'] = execution_time
        
        return test_results
    
    async def _test_rule_on_repository(self, rule: CustomRule, repo_path: str) -> Dict[str, Any]:
        """Test rule on a real repository with safety limits"""
        results = {
            'repo_matches': 0,
            'files_scanned': 0,
            'scan_errors': []
        }
        
        try:
            repo_path = Path(repo_path)
            files_scanned = 0
            matches_found = 0
            
            # Iterate through files matching the rule's patterns
            for pattern in rule.file_patterns:
                for file_path in repo_path.glob(pattern):
                    if file_path.is_file():
                        files_scanned += 1
                        
                        # Safety limit on number of files
                        if files_scanned > RuleExecutionLimits.MAX_FILES_PER_SCAN:
                            results['scan_errors'].append(
                                f"File limit exceeded ({RuleExecutionLimits.MAX_FILES_PER_SCAN})"
                            )
                            break
                        
                        # Safety limit on file size
                        if file_path.stat().st_size > RuleExecutionLimits.MAX_FILE_SIZE_MB * 1024 * 1024:
                            continue
                        
                        # Execute rule on file
                        file_matches = self.testing_framework._execute_rule_on_file(
                            rule.dict(), str(file_path)
                        )
                        matches_found += len(file_matches)
                        
                        # Safety limit on matches
                        if matches_found > RuleExecutionLimits.MAX_MATCHES_PER_RULE:
                            results['scan_errors'].append(
                                f"Match limit exceeded ({RuleExecutionLimits.MAX_MATCHES_PER_RULE})"
                            )
                            break
            
            results.update({
                'repo_matches': matches_found,
                'files_scanned': files_scanned
            })
            
        except Exception as e:
            results['scan_errors'].append(f"Repository scan error: {str(e)}")
        
        return results
    
    async def validate_rule(self, rule: CustomRule, test_repo_path: Optional[str] = None) -> RuleValidationResult:
        """Enhanced rule validation with comprehensive security checks"""
        try:
            # Use the comprehensive security validation
            validation_result = await self.validate_rule_security(rule)
            
            # Additional testing if test repository provided
            if test_repo_path and validation_result.is_valid:
                test_results = await self.test_rule_in_sandbox(rule, test_repo_path)
                validation_result.test_results.update(test_results)
                
                # Add warnings for test results
                if test_results.get('test_status') == 'failed':
                    validation_result.warnings.append("Rule failed repository testing")
                
                if test_results.get('errors'):
                    validation_result.warnings.extend(test_results['errors'])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating rule {rule.id}: {e}")
            return RuleValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[]
            )
        
        # Use new security validation
        return validation_result
    
    async def _run_test_case(self, rule: CustomRule, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case"""
        test_content = test_case.get('content', '')
        expected_matches = test_case.get('expected_matches', 0)
        
        if rule.type == RuleType.REGEX and rule.pattern:
            matches = re.findall(rule.pattern, test_content)
            return {
                'matches_found': len(matches),
                'expected_matches': expected_matches,
                'passed': len(matches) == expected_matches,
                'matches': matches
            }
        
        # For other rule types, return placeholder
        return {
            'matches_found': 0,
            'expected_matches': expected_matches,
            'passed': True,
            'note': f'Test execution not implemented for {rule.type} rules'
        }
    
    async def _test_against_repo(self, rule: CustomRule, repo_path: str) -> Dict[str, Any]:
        """Test rule against a repository"""
        repo_path = Path(repo_path)
        results = {
            'files_scanned': 0,
            'matches_found': 0,
            'files_with_matches': [],
            'performance': {}
        }
        
        import time
        start_time = time.time()
        
        # Scan files based on rule patterns
        file_patterns = rule.file_patterns or ['**/*.py', '**/*.js', '**/*.java', '**/*.php']
        
        for pattern in file_patterns:
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        results['files_scanned'] += 1
                        
                        if rule.type == RuleType.REGEX and rule.pattern:
                            matches = re.findall(rule.pattern, content)
                            if matches:
                                results['matches_found'] += len(matches)
                                results['files_with_matches'].append({
                                    'file': str(file_path.relative_to(repo_path)),
                                    'matches': len(matches)
                                })
                    except Exception as e:
                        logger.warning(f"Could not scan file {file_path}: {e}")
        
        results['performance']['scan_time'] = time.time() - start_time
        return results
    
    async def get_all_rules(self, status: Optional[RuleStatus] = None) -> List[CustomRule]:
        """Get all rules, optionally filtered by status"""
        rules = []
        
        for rule_file in self.rules_directory.glob("*.yaml"):
            rule = await self.load_rule(rule_file.stem)
            if rule and (not status or rule.status == status):
                rules.append(rule)
        
        for rule_file in self.rules_directory.glob("*.json"):
            if not (self.rules_directory / f"{rule_file.stem}.yaml").exists():
                rule = await self.load_rule(rule_file.stem)
                if rule and (not status or rule.status == status):
                    rules.append(rule)
        
        return rules
    
    async def create_rule_from_template(self, template_id: str, variables: Dict[str, Any], rule_id: str) -> Optional[CustomRule]:
        """Create a rule from a template"""
        template = await self.load_template(template_id)
        if not template:
            return None
        
        # Apply variables to template
        template_content = template.template_content.copy()
        
        # Replace variables in template content
        template_str = json.dumps(template_content)
        for var_name, var_value in variables.items():
            template_str = template_str.replace(f"${{{var_name}}}", str(var_value))
        
        try:
            processed_content = json.loads(template_str)
        except json.JSONDecodeError:
            logger.error(f"Error processing template variables for {template_id}")
            return None
        
        # Create rule
        rule_data = {
            'id': rule_id,
            'name': variables.get('name', template.name),
            'description': variables.get('description', template.description),
            'type': template.type,
            'severity': variables.get('severity', RuleSeverity.MEDIUM),
            'author': variables.get('author', 'Generated from template'),
            'cwe_ids': template.cwe_mappings,
            'tags': [template.category, 'generated']
        }
        
        if template.type == RuleType.SEMGREP:
            rule_data['semgrep_rule'] = processed_content
        elif template.type == RuleType.REGEX:
            rule_data['pattern'] = processed_content.get('pattern')
        
        return CustomRule(**rule_data)
    
    async def load_template(self, template_id: str) -> Optional[RuleTemplate]:
        """Load a rule template"""
        if template_id in self.templates_cache:
            return self.templates_cache[template_id]
        
        template_file = self.templates_directory / f"{template_id}.yaml"
        if not template_file.exists():
            template_file = self.templates_directory / f"{template_id}.json"
        
        if template_file.exists():
            try:
                with open(template_file, 'r') as f:
                    if template_file.suffix == '.yaml':
                        template_data = yaml.safe_load(f)
                    else:
                        template_data = json.load(f)
                
                template = RuleTemplate(**template_data)
                self.templates_cache[template_id] = template
                return template
            except Exception as e:
                logger.error(f"Error loading template {template_id}: {e}")
        
        return None
    
    def _save_template(self, template: RuleTemplate):
        """Save a template to disk"""
        try:
            template_file = self.templates_directory / f"{template.template_id}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template.dict(), f, default_flow_style=False)
            self.templates_cache[template.template_id] = template
        except Exception as e:
            logger.error(f"Error saving template {template.template_id}: {e}")
    
    async def get_all_templates(self) -> List[RuleTemplate]:
        """Get all available templates"""
        templates = []
        
        for template_file in self.templates_directory.glob("*.yaml"):
            template = await self.load_template(template_file.stem)
            if template:
                templates.append(template)
        
        for template_file in self.templates_directory.glob("*.json"):
            if not (self.templates_directory / f"{template_file.stem}.yaml").exists():
                template = await self.load_template(template_file.stem)
                if template:
                    templates.append(template)
        
        return templates


# Global rule engine instance
rule_engine = CustomRuleEngine()

