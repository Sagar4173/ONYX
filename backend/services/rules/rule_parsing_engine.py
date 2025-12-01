"""
Advanced Rule Parsing Engine with Schema Validation and Safety Checks
Validates custom security rules with strict schema enforcement and regex safety analysis
"""
import json
import yaml
import re
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import jsonschema
import ast
import subprocess
import time

from services.security.security_boundary_engine import SecurityBoundaryEngine, ResourceLimits

logger = logging.getLogger(__name__)

class RuleFormat(Enum):
    """Supported rule formats"""
    SEMGREP = "semgrep"
    REGEX = "regex" 
    CODEQL = "codeql"
    CUSTOM = "custom"

class ValidationSeverity(Enum):
    """Validation issue severity"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class RuleStatus(Enum):
    """Rule lifecycle status"""
    DRAFT = "draft"
    TESTING = "testing"
    APPROVED = "approved"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"

@dataclass
class ValidationIssue:
    """Rule validation issue"""
    severity: ValidationSeverity
    category: str
    message: str
    field_path: str
    suggested_fix: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class RuleProvenance:
    """Rule provenance and metadata tracking"""
    rule_id: str
    author: str
    created_at: datetime
    modified_at: datetime
    commit_hash: Optional[str] = None
    source_repo: Optional[str] = None
    version: str = "1.0.0"
    reviewers: List[str] = field(default_factory=list)
    approval_date: Optional[datetime] = None
    change_log: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class SecurityRule:
    """Enhanced security rule with full metadata"""
    rule_id: str
    name: str
    description: str
    format: RuleFormat
    content: str
    severity: str
    category: str
    tags: List[str] = field(default_factory=list)
    status: RuleStatus = RuleStatus.DRAFT
    provenance: Optional[RuleProvenance] = None
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    
class RuleParsingEngine:
    """Advanced rule parsing and validation engine"""
    
    def __init__(self, data_dir: str = "data/rules"):
        """Initialize rule parsing engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database for rule storage
        self.db_path = self.data_dir / "rules.db"
        
        # Security boundary engine for safe rule execution
        self.security_engine = SecurityBoundaryEngine(str(self.data_dir / "security_boundaries"))
        
        # Schema definitions
        self.schemas = self._load_schemas()
        
        # Dangerous regex patterns
        self.dangerous_patterns = self._load_dangerous_patterns()
        
        # Performance thresholds
        self.performance_limits = {
            "max_execution_time": 5.0,  # seconds
            "max_memory_usage": 100,    # MB
            "max_backtrack_steps": 10000
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize rule storage database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS security_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    format TEXT NOT NULL,
                    content TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT,                    -- JSON array
                    status TEXT NOT NULL,
                    created_at TEXT,
                    modified_at TEXT,
                    author TEXT,
                    commit_hash TEXT,
                    version TEXT,
                    reviewers TEXT,               -- JSON array
                    approval_date TEXT,
                    change_log TEXT,              -- JSON array
                    test_cases TEXT,              -- JSON array
                    performance_metrics TEXT,     -- JSON object
                    validation_issues TEXT        -- JSON array
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS rule_test_results (
                    test_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    test_repo TEXT NOT NULL,
                    test_commit TEXT,
                    execution_time REAL,
                    memory_usage REAL,
                    findings_count INTEGER,
                    false_positives INTEGER,
                    false_negatives INTEGER,
                    precision_score REAL,
                    recall_score REAL,
                    test_date TEXT,
                    passed BOOLEAN,
                    error_message TEXT,
                    FOREIGN KEY (rule_id) REFERENCES security_rules (rule_id)
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_rules_status ON security_rules(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_rules_category ON security_rules(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_test_results_rule ON rule_test_results(rule_id)")
                
        except Exception as e:
            logger.error(f"Failed to initialize rule database: {e}")
            raise
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load JSON schemas for rule validation"""
        return {
            "semgrep": {
                "type": "object",
                "required": ["rules"],
                "properties": {
                    "rules": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "pattern", "message", "languages", "severity"],
                            "properties": {
                                "id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
                                "pattern": {"type": "string", "minLength": 1, "maxLength": 10000},
                                "message": {"type": "string", "minLength": 10, "maxLength": 1000},
                                "languages": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1
                                },
                                "severity": {
                                    "type": "string",
                                    "enum": ["ERROR", "WARNING", "INFO"]
                                },
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "cwe": {"type": "string"},
                                        "owasp": {"type": "string"},
                                        "category": {"type": "string"}
                                    }
                                }
                            },
                            "additionalProperties": True
                        }
                    }
                }
            },
            "regex": {
                "type": "object",
                "required": ["pattern", "description", "severity"],
                "properties": {
                    "pattern": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 5000
                    },
                    "description": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 1000
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"]
                    },
                    "flags": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["i", "m", "s", "x"]}
                    },
                    "file_patterns": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "custom": {
                "type": "object",
                "required": ["name", "type", "logic", "severity"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 100},
                    "type": {"type": "string", "enum": ["ast", "semantic", "dataflow"]},
                    "logic": {"type": "string", "minLength": 1},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    
    def _load_dangerous_patterns(self) -> List[Dict[str, str]]:
        """Load known dangerous regex patterns"""
        return [
            {
                "pattern": r"\.\*\+",
                "reason": "Catastrophic backtracking with .* followed by +",
                "severity": "error"
            },
            {
                "pattern": r"\(\.\*\)\+",
                "reason": "Nested quantifiers causing exponential backtracking",
                "severity": "error"
            },
            {
                "pattern": r"\.\*\.\*",
                "reason": "Multiple .* patterns can cause performance issues",
                "severity": "warning"
            },
            {
                "pattern": r"\(\?\!\.\*\)\.\*",
                "reason": "Negative lookahead with .* is inefficient",
                "severity": "warning"
            },
            {
                "pattern": r"\w\*\w\*",
                "reason": "Overlapping quantifiers can cause backtracking",
                "severity": "warning"
            }
        ]
    
    async def parse_and_validate_rule(self, rule_content: str, rule_format: RuleFormat,
                                    author: str, metadata: Optional[Dict[str, Any]] = None) -> SecurityRule:
        """Parse and validate a security rule with comprehensive checks"""
        try:
            # Generate rule ID
            rule_id = str(uuid.uuid4())
            
            # Parse content based on format
            parsed_content, validation_issues = await self._parse_rule_content(
                rule_content, rule_format
            )
            
            # Create provenance record
            provenance = RuleProvenance(
                rule_id=rule_id,
                author=author,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
                commit_hash=metadata.get("commit_hash") if metadata else None,
                source_repo=metadata.get("source_repo") if metadata else None
            )
            
            # Create rule object
            rule = SecurityRule(
                rule_id=rule_id,
                name=parsed_content.get("name", f"Rule-{rule_id[:8]}"),
                description=parsed_content.get("description", ""),
                format=rule_format,
                content=rule_content,
                severity=parsed_content.get("severity", "medium"),
                category=parsed_content.get("category", "security"),
                tags=parsed_content.get("tags", []),
                provenance=provenance,
                validation_issues=validation_issues
            )
            
            # Perform additional validation checks
            await self._validate_rule_safety(rule)
            await self._validate_rule_performance(rule)
            await self._validate_rule_logic(rule)
            
            # Set status based on validation results
            has_errors = any(issue.severity == ValidationSeverity.ERROR 
                           for issue in rule.validation_issues)
            rule.status = RuleStatus.REJECTED if has_errors else RuleStatus.DRAFT
            
            return rule
            
        except Exception as e:
            logger.error(f"Failed to parse and validate rule: {e}")
            raise
    
    async def _parse_rule_content(self, content: str, format: RuleFormat) -> Tuple[Dict[str, Any], List[ValidationIssue]]:
        """Parse rule content and validate against schema"""
        issues = []
        parsed = {}
        
        try:
            if format == RuleFormat.SEMGREP:
                parsed = yaml.safe_load(content)
            elif format in [RuleFormat.REGEX, RuleFormat.CUSTOM]:
                parsed = json.loads(content)
            else:
                parsed = {"content": content}
            
            # Validate against schema
            if format.value in self.schemas:
                try:
                    jsonschema.validate(parsed, self.schemas[format.value])
                except jsonschema.ValidationError as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="schema_validation",
                        message=f"Schema validation failed: {e.message}",
                        field_path=".".join(str(p) for p in e.absolute_path),
                        suggested_fix=f"Check field {e.absolute_path} against schema requirements"
                    ))
            
            return parsed, issues
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="parsing",
                message=f"Failed to parse {format.value} content: {e}",
                field_path="root",
                suggested_fix="Ensure valid JSON/YAML format"
            ))
            return {}, issues
    
    async def _validate_rule_safety(self, rule: SecurityRule):
        """Validate rule for security and safety issues"""
        try:
            if rule.format == RuleFormat.REGEX:
                await self._validate_regex_safety(rule)
            elif rule.format == RuleFormat.SEMGREP:
                await self._validate_semgrep_safety(rule)
            elif rule.format == RuleFormat.CUSTOM:
                await self._validate_custom_rule_safety(rule)
                
        except Exception as e:
            rule.validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="safety_validation",
                message=f"Safety validation failed: {e}",
                field_path="content"
            ))
    
    async def _validate_regex_safety(self, rule: SecurityRule):
        """Validate regex for catastrophic backtracking and other issues"""
        try:
            parsed_content = json.loads(rule.content)
            pattern = parsed_content.get("pattern", "")
            
            # Check against dangerous patterns
            for dangerous in self.dangerous_patterns:
                if re.search(dangerous["pattern"], pattern):
                    severity = ValidationSeverity.ERROR if dangerous["severity"] == "error" else ValidationSeverity.WARNING
                    rule.validation_issues.append(ValidationIssue(
                        severity=severity,
                        category="regex_safety",
                        message=f"Dangerous regex pattern detected: {dangerous['reason']}",
                        field_path="pattern",
                        suggested_fix="Rewrite regex to avoid backtracking issues"
                    ))
            
            # Test regex compilation and basic performance
            try:
                compiled_regex = re.compile(pattern)
                
                # Test with catastrophic input
                test_input = "a" * 1000 + "b"
                start_time = time.time()
                try:
                    compiled_regex.search(test_input)
                    execution_time = time.time() - start_time
                    
                    if execution_time > 1.0:  # More than 1 second
                        rule.validation_issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="performance",
                            message=f"Regex execution time too slow: {execution_time:.2f}s",
                            field_path="pattern",
                            suggested_fix="Optimize regex for better performance"
                        ))
                        
                except Exception:
                    rule.validation_issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="regex_safety",
                        message="Regex causes catastrophic backtracking",
                        field_path="pattern",
                        suggested_fix="Rewrite regex to be more specific"
                    ))
                    
            except re.error as e:
                rule.validation_issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="regex_compilation",
                    message=f"Regex compilation failed: {e}",
                    field_path="pattern",
                    suggested_fix="Fix regex syntax errors"
                ))
                
        except Exception as e:
            rule.validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="regex_validation",
                message=f"Regex validation failed: {e}",
                field_path="content"
            ))
    
    async def _validate_semgrep_safety(self, rule: SecurityRule):
        """Validate Semgrep rule for safety issues"""
        try:
            parsed_content = yaml.safe_load(rule.content)
            
            if "rules" not in parsed_content:
                rule.validation_issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="semgrep_structure",
                    message="Missing 'rules' key in Semgrep rule",
                    field_path="rules"
                ))
                return
            
            for i, semgrep_rule in enumerate(parsed_content["rules"]):
                # Check for overly broad patterns
                pattern = semgrep_rule.get("pattern", "")
                if pattern in ["$X", "...", "$_"]:
                    rule.validation_issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="pattern_broadness",
                        message=f"Overly broad pattern in rule {i}: {pattern}",
                        field_path=f"rules[{i}].pattern",
                        suggested_fix="Make pattern more specific to reduce false positives"
                    ))
                
                # Check for missing metadata
                if "metadata" not in semgrep_rule:
                    rule.validation_issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="missing_metadata",
                        message=f"Missing metadata in rule {i}",
                        field_path=f"rules[{i}].metadata",
                        suggested_fix="Add CWE, OWASP, or other relevant metadata"
                    ))
                    
        except Exception as e:
            rule.validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="semgrep_validation",
                message=f"Semgrep validation failed: {e}",
                field_path="content"
            ))
    
    async def _validate_custom_rule_safety(self, rule: SecurityRule):
        """Validate custom rule for safety issues"""
        try:
            parsed_content = json.loads(rule.content)
            logic = parsed_content.get("logic", "")
            
            # Check for dangerous operations in custom logic
            dangerous_operations = [
                "eval(", "exec(", "__import__", "subprocess", "os.system",
                "open(", "file(", "input(", "raw_input("
            ]
            
            for dangerous_op in dangerous_operations:
                if dangerous_op in logic:
                    rule.validation_issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="dangerous_operation",
                        message=f"Dangerous operation detected: {dangerous_op}",
                        field_path="logic",
                        suggested_fix="Remove dangerous operations from custom logic"
                    ))
            
            # Try to parse as AST to check syntax
            try:
                ast.parse(logic)
            except SyntaxError as e:
                rule.validation_issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="syntax_error",
                    message=f"Syntax error in custom logic: {e}",
                    field_path="logic",
                    line_number=e.lineno,
                    suggested_fix="Fix Python syntax errors"
                ))
                
        except Exception as e:
            rule.validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="custom_validation",
                message=f"Custom rule validation failed: {e}",
                field_path="content"
            ))
    
    async def _validate_rule_performance(self, rule: SecurityRule):
        """Validate rule performance characteristics"""
        try:
            # Simulate performance testing
            performance_metrics = {
                "estimated_execution_time": 0.1,  # seconds
                "estimated_memory_usage": 10,     # MB
                "complexity_score": 3.5           # 1-10 scale
            }
            
            # Check against thresholds
            if performance_metrics["estimated_execution_time"] > self.performance_limits["max_execution_time"]:
                rule.validation_issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="performance",
                    message=f"Estimated execution time too high: {performance_metrics['estimated_execution_time']}s",
                    field_path="content",
                    suggested_fix="Optimize rule logic for better performance"
                ))
            
            rule.performance_metrics = performance_metrics
            
        except Exception as e:
            rule.validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="performance_validation",
                message=f"Performance validation failed: {e}",
                field_path="content"
            ))
    
    async def _validate_rule_logic(self, rule: SecurityRule):
        """Validate rule logic and effectiveness"""
        try:
            # Check for common logical issues
            if rule.format == RuleFormat.SEMGREP:
                parsed_content = yaml.safe_load(rule.content)
                for i, semgrep_rule in enumerate(parsed_content.get("rules", [])):
                    # Check for contradictory patterns
                    pattern = semgrep_rule.get("pattern", "")
                    pattern_not = semgrep_rule.get("pattern-not", [])
                    
                    if pattern_not and pattern in pattern_not:
                        rule.validation_issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="logical_contradiction",
                            message=f"Pattern contradicts pattern-not in rule {i}",
                            field_path=f"rules[{i}]",
                            suggested_fix="Remove contradictory patterns"
                        ))
            
        except Exception as e:
            rule.validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="logic_validation",
                message=f"Logic validation failed: {e}",
                field_path="content"
            ))
    
    async def store_rule(self, rule: SecurityRule) -> bool:
        """Store validated rule in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO security_rules (
                    rule_id, name, description, format, content, severity,
                    category, tags, status, created_at, modified_at, author,
                    commit_hash, version, reviewers, approval_date, change_log,
                    test_cases, performance_metrics, validation_issues
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id,
                    rule.name,
                    rule.description,
                    rule.format.value,
                    rule.content,
                    rule.severity,
                    rule.category,
                    json.dumps(rule.tags),
                    rule.status.value,
                    rule.provenance.created_at.isoformat() if rule.provenance else None,
                    rule.provenance.modified_at.isoformat() if rule.provenance else None,
                    rule.provenance.author if rule.provenance else None,
                    rule.provenance.commit_hash if rule.provenance else None,
                    rule.provenance.version if rule.provenance else "1.0.0",
                    json.dumps(rule.provenance.reviewers) if rule.provenance else "[]",
                    rule.provenance.approval_date.isoformat() if rule.provenance and rule.provenance.approval_date else None,
                    json.dumps(rule.provenance.change_log) if rule.provenance else "[]",
                    json.dumps(rule.test_cases),
                    json.dumps(rule.performance_metrics),
                    json.dumps([{
                        "severity": issue.severity.value,
                        "category": issue.category,
                        "message": issue.message,
                        "field_path": issue.field_path,
                        "suggested_fix": issue.suggested_fix,
                        "line_number": issue.line_number
                    } for issue in rule.validation_issues])
                ))
                conn.commit()
            
            logger.info(f"Stored rule {rule.rule_id} with status {rule.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store rule: {e}")
            return False
    
    async def get_rule_validation_report(self, rule_id: str) -> Dict[str, Any]:
        """Get comprehensive validation report for a rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM security_rules WHERE rule_id = ?",
                    (rule_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return {"error": "Rule not found"}
                
                validation_issues = json.loads(row[19]) if row[19] else []
                performance_metrics = json.loads(row[18]) if row[18] else {}
                
                return {
                    "rule_id": rule_id,
                    "name": row[1],
                    "status": row[8],
                    "validation_summary": {
                        "total_issues": len(validation_issues),
                        "errors": len([i for i in validation_issues if i["severity"] == "error"]),
                        "warnings": len([i for i in validation_issues if i["severity"] == "warning"]),
                        "infos": len([i for i in validation_issues if i["severity"] == "info"])
                    },
                    "validation_issues": validation_issues,
                    "performance_metrics": performance_metrics,
                    "safety_score": self._calculate_safety_score(validation_issues),
                    "ready_for_testing": len([i for i in validation_issues if i["severity"] == "error"]) == 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get validation report: {e}")
            return {"error": str(e)}
    
    def _calculate_safety_score(self, validation_issues: List[Dict[str, Any]]) -> float:
        """Calculate safety score (0-10) based on validation issues"""
        base_score = 10.0
        
        for issue in validation_issues:
            if issue["severity"] == "error":
                base_score -= 3.0
            elif issue["severity"] == "warning":
                base_score -= 1.0
            elif issue["severity"] == "info":
                base_score -= 0.1
        
        return max(0.0, base_score)
    
    async def update_rule_status(self, rule_id: str, new_status: RuleStatus,
                               reviewer: str, notes: Optional[str] = None) -> bool:
        """Update rule status with reviewer tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current rule
                cursor = conn.execute(
                    "SELECT reviewers, change_log FROM security_rules WHERE rule_id = ?",
                    (rule_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                # Update reviewers and change log
                reviewers = json.loads(row[0]) if row[0] else []
                if reviewer not in reviewers:
                    reviewers.append(reviewer)
                
                change_log = json.loads(row[1]) if row[1] else []
                change_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": f"Status changed to {new_status.value}",
                    "reviewer": reviewer,
                    "notes": notes or ""
                })
                
                # Update database
                approval_date = datetime.now(timezone.utc).isoformat() if new_status == RuleStatus.APPROVED else None
                
                conn.execute("""
                UPDATE security_rules SET
                    status = ?, modified_at = ?, reviewers = ?, change_log = ?, approval_date = ?
                WHERE rule_id = ?
                """, (
                    new_status.value,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(reviewers),
                    json.dumps(change_log),
                    approval_date,
                    rule_id
                ))
                conn.commit()
            
            logger.info(f"Updated rule {rule_id} status to {new_status.value} by {reviewer}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update rule status: {e}")
            return False
    
    async def test_rule_with_security_boundaries(self, rule_id: str, 
                                               test_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Test rule execution with security boundaries"""
        try:
            # Get rule content
            rule = await self.get_rule_by_id(rule_id)
            if not rule:
                return {"error": "Rule not found"}
            
            # Use test files or create default ones
            if test_files is None:
                test_files = self._create_default_test_files()
            
            # Set conservative limits for testing
            test_limits = ResourceLimits(
                cpu_limit=0.5,
                memory_limit_mb=128,
                timeout_per_file=3,
                timeout_total=15,
                max_matches=1000,
                max_file_size_mb=5
            )
            
            # Execute with security boundaries
            execution_result, resource_usage = await self.security_engine.execute_rule_safely(
                rule_content=rule["content"],
                rule_type=rule["format"],
                target_files=test_files,
                limits=test_limits
            )
            
            # Analyze results
            safety_assessment = self._analyze_execution_safety(execution_result, resource_usage)
            
            # Store test results
            test_record = {
                "rule_id": rule_id,
                "test_timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_result": execution_result,
                "resource_usage": {
                    "cpu_time": resource_usage.cpu_time,
                    "memory_peak_mb": resource_usage.memory_peak_mb,
                    "wall_time": resource_usage.wall_time,
                    "matches_count": resource_usage.matches_count,
                    "files_processed": resource_usage.files_processed,
                    "killed_by_limit": resource_usage.killed_by_limit,
                    "kill_reason": resource_usage.kill_reason
                },
                "safety_assessment": safety_assessment
            }
            
            # Update rule with test results
            await self._store_rule_test_results(rule_id, test_record)
            
            return test_record
            
        except Exception as e:
            logger.error(f"Failed to test rule with security boundaries: {e}")
            return {"error": str(e)}
    
    async def run_adversarial_tests(self) -> Dict[str, Any]:
        """Run adversarial tests to validate security boundaries"""
        try:
            return await self.security_engine.test_adversarial_cases()
        except Exception as e:
            logger.error(f"Failed to run adversarial tests: {e}")
            return {"error": str(e)}
    
    def _create_default_test_files(self) -> List[str]:
        """Create default test files for rule testing"""
        test_dir = self.data_dir / "test_files"
        test_dir.mkdir(exist_ok=True)
        
        test_files = []
        
        # Python test file
        python_file = test_dir / "test.py"
        python_content = """
import os
import subprocess

def vulnerable_function(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command injection vulnerability  
    os.system(f"echo {user_input}")
    
    # Hardcoded secret
    api_key = "sk-1234567890abcdef"
    
    # XSS vulnerability
    return f"<div>Hello {user_input}</div>"

class TestClass:
    def __init__(self):
        self.password = "hardcoded_password123"
        
    def process_data(self, data):
        eval(data)  # Code injection
        """
        python_file.write_text(python_content)
        test_files.append(str(python_file))
        
        # JavaScript test file
        js_file = test_dir / "test.js"
        js_content = """
function vulnerableFunction(userInput) {
    // XSS vulnerability
    document.getElementById('output').innerHTML = userInput;
    
    // Command injection
    eval(userInput);
    
    // Hardcoded credentials
    const apiKey = 'sk-abcdef1234567890';
    
    // SQL injection
    const query = `SELECT * FROM users WHERE id = ${userInput}`;
    
    return query;
}

// CSRF vulnerability
function transferMoney(amount, toAccount) {
    fetch('/transfer', {
        method: 'POST',
        body: JSON.stringify({amount, toAccount})
    });
}
        """
        js_file.write_text(js_content)
        test_files.append(str(js_file))
        
        return test_files
    
    def _analyze_execution_safety(self, execution_result: Dict[str, Any], 
                                 resource_usage: Any) -> Dict[str, Any]:
        """Analyze execution safety based on results and resource usage"""
        safety_assessment = {
            "overall_safety": "safe",
            "concerns": [],
            "recommendations": []
        }
        
        # Check if killed by limits
        if resource_usage.killed_by_limit:
            safety_assessment["overall_safety"] = "dangerous"
            safety_assessment["concerns"].append(f"Rule killed by security boundary: {resource_usage.kill_reason}")
            safety_assessment["recommendations"].append("Review rule complexity and resource requirements")
        
        # Check resource usage
        if resource_usage.memory_peak_mb > 100:
            safety_assessment["concerns"].append("High memory usage detected")
            if safety_assessment["overall_safety"] == "safe":
                safety_assessment["overall_safety"] = "concerning"
        
        if resource_usage.wall_time > 10:
            safety_assessment["concerns"].append("Slow execution time")
            if safety_assessment["overall_safety"] == "safe":
                safety_assessment["overall_safety"] = "concerning"
        
        if resource_usage.matches_count > 5000:
            safety_assessment["concerns"].append("Excessive number of matches")
            safety_assessment["recommendations"].append("Consider making rule more specific")
        
        # Check execution success
        if execution_result.get("success") is False:
            safety_assessment["concerns"].append(f"Execution failed: {execution_result.get('error', 'Unknown error')}")
        
        return safety_assessment
    
    async def _store_rule_test_results(self, rule_id: str, test_record: Dict[str, Any]):
        """Store rule test results in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO rule_test_results (
                    test_id, rule_id, test_repo, test_commit, test_timestamp,
                    execution_time, findings_count, precision, recall,
                    performance_metrics, test_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    rule_id,
                    "security_boundary_test",
                    "local",
                    test_record["test_timestamp"],
                    test_record["resource_usage"]["wall_time"],
                    test_record["resource_usage"]["matches_count"],
                    None,  # Precision - would be calculated from test results
                    None,  # Recall - would be calculated from test results
                    json.dumps(test_record["resource_usage"]),
                    json.dumps(test_record)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store rule test results: {e}")
    
    async def get_rules_by_status(self, status: RuleStatus) -> List[Dict[str, Any]]:
        """Get all rules with specific status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                SELECT rule_id, name, description, format, severity, category,
                       created_at, author, validation_issues
                FROM security_rules 
                WHERE status = ?
                ORDER BY created_at DESC
                """, (status.value,))
                
                rules = []
                for row in cursor.fetchall():
                    validation_issues = json.loads(row[8]) if row[8] else []
                    rules.append({
                        "rule_id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "format": row[3],
                        "severity": row[4],
                        "category": row[5],
                        "created_at": row[6],
                        "author": row[7],
                        "validation_summary": {
                            "total_issues": len(validation_issues),
                            "errors": len([i for i in validation_issues if i["severity"] == "error"]),
                            "warnings": len([i for i in validation_issues if i["severity"] == "warning"])
                        }
                    })
                
                return rules
                
        except Exception as e:
            logger.error(f"Failed to get rules by status: {e}")
            return []

# Export main classes
__all__ = [
    'RuleParsingEngine', 'SecurityRule', 'RuleProvenance', 'ValidationIssue',
    'RuleFormat', 'RuleStatus', 'ValidationSeverity'
]
