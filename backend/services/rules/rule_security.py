"""
Security boundaries and validation for custom rules
This module provides comprehensive security controls for user-defined rules
"""
import json
import re
import subprocess
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


class AllowedLanguage(str, Enum):
    """Supported languages for custom rules"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    PHP = "php"

class AllowedRuleType(str, Enum):
    """Allowed rule types with security boundaries"""
    SEMGREP = "semgrep"
    REGEX = "regex"

class SeverityLevel(str, Enum):
    """Required severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RuleSecurityError(Exception):
    """Exception raised when rule violates security boundaries"""
    pass

class RuleExecutionLimits:
    """Execution limits for rule validation and testing"""
    MAX_EXECUTION_TIME = 5.0  # seconds
    MAX_MEMORY_MB = 100  # MB
    MAX_MATCHES_PER_RULE = 1000
    MAX_REGEX_LENGTH = 500
    MAX_FILE_SIZE_MB = 10  # MB per file
    MAX_FILES_PER_SCAN = 1000

class RegexSecurityValidator:
    """Validates regex patterns for security vulnerabilities"""
    
    # Dangerous regex patterns that can cause ReDoS
    DANGEROUS_PATTERNS = [
        r'\(\.\+\)\+',          # (.+)+
        r'\(\.\*\)\+',          # (.*)+
        r'\(\.\+\)\*',          # (.+)*
        r'\([^)]*\)\+',         # (x+)+ - simplified without back reference
        r'\([^)]*\)\*',         # (x*)* - simplified without back reference  
        r'\([^)]*\)\{\d+,\}',   # (x){2,}
        r'\.\*\.\*',            # .*.*
        r'\.\+\.\+',            # .+.+
        r'\(\w\+\)\+',          # (word+)+
        r'\(\d\+\)\+',          # (digit+)+
    ]
    
    # Forbidden constructs - simplified to avoid false positives
    FORBIDDEN_CONSTRUCTS = [
        r'\\x[0-9a-fA-F]{2}',     # Hex escapes like \x41
        r'\\[0-7]{3}',            # Octal escapes like \041  
        r'\\[0-9]+',              # Backreferences like \1, \2 etc (can cause issues)
        r'\(\?\<\!',              # Negative lookbehind start
        r'\(\?\<\=',              # Positive lookbehind start
    ]
    
    @staticmethod
    def validate_regex(pattern: str) -> Tuple[bool, List[str]]:
        """
        Validate regex pattern for security issues
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check length
        if len(pattern) > RuleExecutionLimits.MAX_REGEX_LENGTH:
            errors.append(f"Regex pattern too long: {len(pattern)} > {RuleExecutionLimits.MAX_REGEX_LENGTH}")
        
        # Check for dangerous patterns
        for dangerous in RegexSecurityValidator.DANGEROUS_PATTERNS:
            if re.search(dangerous, pattern):
                errors.append(f"Dangerous regex pattern detected: {dangerous}")
        
        # Check for forbidden constructs
        for forbidden in RegexSecurityValidator.FORBIDDEN_CONSTRUCTS:
            if re.search(forbidden, pattern):
                errors.append(f"Forbidden regex construct: {forbidden}")
        
        # Try to compile regex
        try:
            compiled = re.compile(pattern)
            
            # Simple performance test without threading (to avoid hanging)
            test_string = "a" * 100  # Smaller test string
            start_time = time.time()
            try:
                # Quick performance test
                for _ in range(10):  # Reduced iterations
                    compiled.search(test_string)
                elapsed_time = time.time() - start_time
                
                # If it takes too long for simple test, flag as potential ReDoS
                if elapsed_time > 0.1:  # 100ms threshold
                    errors.append("Regex shows signs of poor performance")
                    
            except Exception as e:
                errors.append(f"Regex performance test failed: {str(e)}")
                
        except re.error as e:
            errors.append(f"Invalid regex pattern: {str(e)}")
        
        return len(errors) == 0, errors

class PathSecurityValidator:
    """Validates file paths and globs for security issues"""
    
    FORBIDDEN_PATTERNS = [
        r'\.\./',               # Directory traversal
        r'\.\.\.',              # Directory traversal
        r'^/',                  # Absolute paths
        r'^[A-Za-z]:',          # Windows absolute paths
        r'/etc/',               # System directories
        r'/var/',               # System directories
        r'/usr/',               # System directories
        r'/bin/',               # System directories
        r'/sbin/',              # System directories
        r'/proc/',              # System directories
        r'/sys/',               # System directories
        r'/dev/',               # Device files
        r'/tmp/',               # Temp directories (outside of sandbox)
        r'~/',                  # Home directory
        r'\$\{',                # Environment variable expansion
        r'\$\(',                # Command substitution
    ]
    
    @staticmethod
    def validate_file_pattern(pattern: str) -> Tuple[bool, List[str]]:
        """
        Validate file pattern for security issues
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for forbidden patterns
        for forbidden in PathSecurityValidator.FORBIDDEN_PATTERNS:
            if re.search(forbidden, pattern):
                errors.append(f"Forbidden path pattern: {forbidden}")
        
        # Additional checks
        if len(pattern) > 200:
            errors.append("File pattern too long")
        
        # Must be relative path within repository
        if not pattern.startswith('./') and not pattern.startswith('**'):
            if '/' in pattern and not pattern.startswith('*'):
                errors.append("File patterns must be relative to repository root")
        
        return len(errors) == 0, errors

class SemgrepSecurityValidator:
    """Validates Semgrep rules for security boundaries"""
    
    FORBIDDEN_METAVARS = [
        'metavar-command',      # Command execution
        'metavar-shell',        # Shell execution
        'metavar-eval',         # Code evaluation
    ]
    
    FORBIDDEN_KEYS = [
        'fix',                  # Auto-fix can be dangerous
        'r2c-internal-project-depends-on',  # Internal Semgrep features
        'r2c-internal-project-depends-on-either',
    ]
    
    ALLOWED_PATTERN_KEYS = {
        'pattern',
        'pattern-either',
        'pattern-not',
        'pattern-inside',
        'pattern-not-inside',
        'patterns',
        'pattern-regex',
        'pattern-where-python',  # Limited Python - will validate separately
    }
    
    @staticmethod
    def validate_semgrep_rule(rule_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate Semgrep rule dictionary for security issues
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for forbidden keys
        for key in rule_dict.keys():
            if key in SemgrepSecurityValidator.FORBIDDEN_KEYS:
                errors.append(f"Forbidden Semgrep key: {key}")
        
        # Validate patterns section
        if 'patterns' in rule_dict:
            patterns = rule_dict['patterns']
            if isinstance(patterns, list):
                for pattern in patterns:
                    if isinstance(pattern, dict):
                        for pattern_key in pattern.keys():
                            if pattern_key not in SemgrepSecurityValidator.ALLOWED_PATTERN_KEYS:
                                errors.append(f"Unsupported pattern key: {pattern_key}")
                        
                        # Check for dangerous pattern-where-python
                        if 'pattern-where-python' in pattern:
                            python_code = pattern['pattern-where-python']
                            if not SemgrepSecurityValidator._validate_python_expression(python_code):
                                errors.append("Dangerous Python expression in pattern-where-python")
        
        # Validate individual patterns
        for pattern_key in ['pattern', 'pattern-regex']:
            if pattern_key in rule_dict:
                pattern_value = rule_dict[pattern_key]
                if pattern_key == 'pattern-regex':
                    is_valid, regex_errors = RegexSecurityValidator.validate_regex(pattern_value)
                    if not is_valid:
                        errors.extend(regex_errors)
        
        # Check metavariables
        if 'metavariable-regex' in rule_dict:
            for metavar, regex_pattern in rule_dict['metavariable-regex'].items():
                if metavar in SemgrepSecurityValidator.FORBIDDEN_METAVARS:
                    errors.append(f"Forbidden metavariable: {metavar}")
                
                is_valid, regex_errors = RegexSecurityValidator.validate_regex(regex_pattern)
                if not is_valid:
                    errors.extend([f"Metavar {metavar}: {error}" for error in regex_errors])
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_python_expression(code: str) -> bool:
        """Validate Python expression in pattern-where-python"""
        # Very restrictive - only allow simple comparisons and basic operations
        forbidden_keywords = [
            'import', 'exec', 'eval', 'open', 'file', '__import__',
            'compile', 'globals', 'locals', 'vars', 'dir',
            'getattr', 'setattr', 'delattr', 'hasattr',
            'input', 'raw_input', 'execfile', '__builtins__'
        ]
        
        for keyword in forbidden_keywords:
            if keyword in code:
                return False
        
        # Only allow basic string and numeric operations
        allowed_pattern = r'^[a-zA-Z0-9_\s\+\-\*\/\(\)\[\]\.\"\'<>=!&|]+$'
        return bool(re.match(allowed_pattern, code))

class SecureRuleValidator:
    """Main validator for custom rules with comprehensive security checks"""
    
    def __init__(self):
        self.regex_validator = RegexSecurityValidator()
        self.path_validator = PathSecurityValidator()
        self.semgrep_validator = SemgrepSecurityValidator()
    
    def validate_rule_metadata(self, rule_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate required metadata fields"""
        errors = []
        required_fields = ['id', 'message', 'severity', 'languages']
        
        for field in required_fields:
            if field not in rule_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate ID format
        if 'id' in rule_data:
            rule_id = rule_data['id']
            if not re.match(r'^[a-z0-9-_]+$', rule_id):
                errors.append("Rule ID must contain only lowercase letters, numbers, hyphens, and underscores")
            if len(rule_id) > 50:
                errors.append("Rule ID too long (max 50 characters)")
        
        # Validate severity
        if 'severity' in rule_data:
            if rule_data['severity'] not in [s.value for s in SeverityLevel]:
                errors.append(f"Invalid severity level: {rule_data['severity']}")
        
        # Validate languages
        if 'languages' in rule_data:
            languages = rule_data['languages']
            if languages is None:
                errors.append("Languages cannot be None")
            elif not isinstance(languages, list):
                errors.append("Languages must be a list")
            else:
                allowed_langs = [lang.value for lang in AllowedLanguage]
                for lang in languages:
                    if lang not in allowed_langs:
                        errors.append(f"Unsupported language: {lang}. Allowed: {allowed_langs}")
        
        # Validate message
        if 'message' in rule_data:
            message = rule_data['message']
            if message is None:
                errors.append("Rule message cannot be None")
            elif len(message) < 10:
                errors.append("Rule message too short (minimum 10 characters)")
            elif len(message) > 200:
                errors.append("Rule message too long (maximum 200 characters)")
        
        return len(errors) == 0, errors
    
    def validate_rule_content(self, rule_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate rule content based on type"""
        errors = []
        
        rule_type = rule_data.get('type', '').lower()
        
        if rule_type == AllowedRuleType.REGEX.value:
            pattern = rule_data.get('pattern')
            if pattern is None:
                errors.append("Regex rules require a pattern")
            else:
                is_valid, regex_errors = self.regex_validator.validate_regex(pattern)
                if not is_valid:
                    errors.extend(regex_errors)
        
        elif rule_type == AllowedRuleType.SEMGREP.value:
            # Validate Semgrep rule structure
            semgrep_rule = rule_data.get('semgrep_rule')
            if semgrep_rule is None:
                errors.append("Semgrep rules require semgrep_rule content")
            else:
                is_valid, semgrep_errors = self.semgrep_validator.validate_semgrep_rule(semgrep_rule)
                if not is_valid:
                    errors.extend(semgrep_errors)
        
        else:
            errors.append(f"Unsupported rule type: {rule_type}")
        
        # Validate file patterns
        if 'file_patterns' in rule_data:
            file_patterns = rule_data['file_patterns']
            if file_patterns is None:
                errors.append("File patterns cannot be None")
            elif isinstance(file_patterns, list):
                for pattern in file_patterns:
                    if pattern is None:
                        errors.append("File pattern cannot be None")
                    else:
                        is_valid, path_errors = self.path_validator.validate_file_pattern(pattern)
                        if not is_valid:
                            errors.extend([f"File pattern '{pattern}': {error}" for error in path_errors])
            else:
                errors.append("File patterns must be a list")
        
        return len(errors) == 0, errors
    
    def validate_rule_safety(self, rule_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Additional safety checks for rule content"""
        errors = []
        
        # Convert rule to string for content analysis
        rule_str = json.dumps(rule_data, default=str).lower()
        
        # Check for suspicious content
        suspicious_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'import\s+os',
            r'import\s+subprocess',
            r'import\s+sys',
            r'__import__',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
            r'compile\s*\(',
            r'globals\s*\(',
            r'locals\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, rule_str):
                errors.append(f"Suspicious content detected: {pattern}")
        
        # Check for external references
        external_patterns = [
            r'http[s]?://',
            r'ftp://',
            r'file://',
            r'\\\\[^\\]+',  # UNC paths
        ]
        
        for pattern in external_patterns:
            if re.search(pattern, rule_str):
                errors.append(f"External reference not allowed: {pattern}")
        
        return len(errors) == 0, errors

class RuleTestingFramework:
    """Framework for testing rules before deployment"""
    
    def __init__(self):
        self.test_timeout = RuleExecutionLimits.MAX_EXECUTION_TIME
    
    def test_rule_with_samples(self, rule_data: Dict[str, Any], test_cases: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """
        Test rule against provided test cases
        Returns (success, test_results)
        """
        results = {
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'errors': [],
            'execution_time': 0,
            'memory_usage': 0
        }
        
        start_time = time.time()
        
        try:
            for i, test_case in enumerate(test_cases):
                test_content = test_case.get('content', '')
                expected_matches = test_case.get('expected_matches', 0)
                
                # Create temporary file with test content
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                    temp_file.write(test_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Execute rule against test content
                    matches = self._execute_rule_on_file(rule_data, temp_file_path)
                    
                    if len(matches) == expected_matches:
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(
                            f"Test {i+1}: Expected {expected_matches} matches, got {len(matches)}"
                        )
                
                finally:
                    # Cleanup temporary file
                    Path(temp_file_path).unlink(missing_ok=True)
            
            results['execution_time'] = time.time() - start_time
            
        except Exception as e:
            results['errors'].append(f"Test execution failed: {str(e)}")
            results['failed'] = len(test_cases)
        
        success = results['failed'] == 0 and len(results['errors']) == 0
        return success, results
    
    def _execute_rule_on_file(self, rule_data: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Execute rule on a single file and return matches"""
        matches = []
        
        rule_type = rule_data.get('type', '').lower()
        
        if rule_type == AllowedRuleType.REGEX.value:
            matches = self._execute_regex_rule(rule_data, file_path)
        elif rule_type == AllowedRuleType.SEMGREP.value:
            matches = self._execute_semgrep_rule(rule_data, file_path)
        
        return matches
    
    def _execute_regex_rule(self, rule_data: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Execute regex rule on file"""
        matches = []
        pattern = rule_data.get('pattern', '')
        
        try:
            compiled_regex = re.compile(pattern)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for match in compiled_regex.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    matches.append({
                        'line': line_num,
                        'match': match.group(),
                        'start': match.start(),
                        'end': match.end()
                    })
                    
                    # Limit matches to prevent spam
                    if len(matches) >= RuleExecutionLimits.MAX_MATCHES_PER_RULE:
                        break
        
        except Exception as e:
            logger.warning("Regex rule pattern execution failed: %s", e, exc_info=True)
        
        return matches
    
    def _execute_semgrep_rule(self, rule_data: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Execute Semgrep rule on file"""
        matches = []
        
        try:
            # Create temporary Semgrep rule file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as rule_file:
                rule_yaml = {
                    'rules': [rule_data]
                }
                yaml.dump(rule_yaml, rule_file)
                rule_file_path = rule_file.name
            
            # Execute Semgrep with timeout
            cmd = ['semgrep', '--config', rule_file_path, '--json', file_path]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.test_timeout
                )
                
                if result.returncode == 0:
                    output = json.loads(result.stdout)
                    matches = output.get('results', [])
            
            except subprocess.TimeoutExpired:
                logger.warning("Semgrep rule execution timed out for rule: %s on %s", rule_data.get('id', 'unknown'), file_path)
            except json.JSONDecodeError:
                logger.warning("Semgrep returned invalid JSON for rule: %s on %s", rule_data.get('id', 'unknown'), file_path)
            
        except Exception as e:
            logger.warning("Semgrep rule execution failed: %s", e, exc_info=True)
        
        finally:
            # Cleanup temporary rule file
            Path(rule_file_path).unlink(missing_ok=True)
        
        return matches

# Export main classes
__all__ = [
    'SecureRuleValidator',
    'RuleTestingFramework',
    'RuleSecurityError',
    'AllowedLanguage',
    'AllowedRuleType',
    'SeverityLevel',
    'RuleExecutionLimits'
]
