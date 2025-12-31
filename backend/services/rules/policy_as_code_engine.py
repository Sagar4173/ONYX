"""
Policy-as-Code Enforcement Engine
Treats security policies like code with PR, review, approval and enforcement modes
"""
import asyncio
import logging
import json
import yaml
import sqlite3
import git
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import uuid
import hashlib
import jsonschema

# Import canonical enums from models.base (SINGLE SOURCE OF TRUTH)
from models.base import (
    PolicyType, EnforcementMode, PolicyStatus, ViolationAction
)

logger = logging.getLogger(__name__)

@dataclass
class PolicyRule:
    """Individual policy rule"""
    rule_id: str
    name: str
    description: str
    condition: str  # Expression to evaluate
    action: ViolationAction
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class SecurityPolicy:
    """Security policy definition"""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    enforcement_mode: EnforcementMode
    rules: List[PolicyRule] = field(default_factory=list)
    applies_to: Dict[str, List[str]] = field(default_factory=dict)  # repositories, branches, etc.
    exceptions: List[str] = field(default_factory=list)  # Exception patterns
    status: PolicyStatus = PolicyStatus.DRAFT
    version: str = "1.0.0"
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PolicyViolation:
    """Policy violation record"""
    violation_id: str
    policy_id: str
    rule_id: str
    repository: str
    branch: str
    commit_hash: str
    file_path: Optional[str] = None
    violation_details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"
    action_taken: Optional[ViolationAction] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""

@dataclass
class PolicyChangeRequest:
    """Policy change request (like a PR for policies)"""
    change_id: str
    title: str
    description: str
    policy_changes: List[Dict[str, Any]] = field(default_factory=list)  # Add/modify/delete operations
    requested_by: str = "unknown"
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewers: List[str] = field(default_factory=list)
    approvals: List[str] = field(default_factory=list)
    status: str = "open"  # open, approved, rejected, merged
    merge_commit: Optional[str] = None

class PolicyAsCodeEngine:
    """Policy-as-Code enforcement engine"""
    
    def __init__(self, data_dir: str = "data/policies", git_repo_path: Optional[str] = None):
        """Initialize policy engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database for policy enforcement tracking
        self.db_path = self.data_dir / "policies.db"
        
        # Git repository for policy-as-code
        self.git_repo_path = Path(git_repo_path) if git_repo_path else self.data_dir / "policy_repo"
        
        # Policy schemas
        self.policy_schemas = self._load_policy_schemas()
        
        # Default policies
        self.default_policies = self._create_default_policies()
        
        # Initialize systems
        self._init_database()
        self._init_git_repo()
        
        # Load policies from git (lazy initialization)
        self._policies_loaded = False
    
    def _init_database(self):
        """Initialize policy database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS security_policies (
                    policy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    policy_type TEXT NOT NULL,
                    enforcement_mode TEXT NOT NULL,
                    rules TEXT,                 -- JSON array
                    applies_to TEXT,            -- JSON object
                    exceptions TEXT,            -- JSON array
                    status TEXT NOT NULL,
                    version TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    metadata TEXT,              -- JSON object
                    git_commit_hash TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_violations (
                    violation_id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    commit_hash TEXT NOT NULL,
                    file_path TEXT,
                    violation_details TEXT,     -- JSON object
                    severity TEXT,
                    action_taken TEXT,
                    detected_at TEXT,
                    resolved_at TEXT,
                    resolution_notes TEXT,
                    FOREIGN KEY (policy_id) REFERENCES security_policies (policy_id)
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_change_requests (
                    change_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    policy_changes TEXT,        -- JSON array
                    requested_by TEXT,
                    requested_at TEXT,
                    reviewers TEXT,             -- JSON array
                    approvals TEXT,             -- JSON array
                    status TEXT,
                    merge_commit TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_enforcement_log (
                    log_id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    commit_hash TEXT NOT NULL,
                    enforcement_result TEXT,    -- allowed, blocked, warning
                    violations_count INTEGER,
                    action_taken TEXT,
                    logged_at TEXT,
                    FOREIGN KEY (policy_id) REFERENCES security_policies (policy_id)
                )
                """)
                
                # Indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policies_status ON security_policies(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_repo ON policy_violations(repository, branch)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_policy ON policy_violations(policy_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_enforcement_log ON policy_enforcement_log(repository, branch)")
                
        except Exception as e:
            logger.error(f"Failed to initialize policy database: {e}")
            raise
    
    def _init_git_repo(self):
        """Initialize Git repository for policy-as-code"""
        try:
            if not self.git_repo_path.exists():
                # Create new repository
                self.git_repo_path.mkdir(parents=True)
                repo = git.Repo.init(self.git_repo_path)
                
                # Create initial structure
                policies_dir = self.git_repo_path / "policies"
                policies_dir.mkdir()
                
                schemas_dir = self.git_repo_path / "schemas"
                schemas_dir.mkdir()
                
                # Create README
                readme = self.git_repo_path / "README.md"
                readme.write_text("""# Security Policies Repository

This repository contains security policies that are enforced across all projects.

## Structure
- `policies/` - Security policy definitions
- `schemas/` - Policy validation schemas
- `CHANGELOG.md` - Policy change history

## Process
1. Create policy change request
2. Peer review
3. Approval by security team
4. Merge to activate policy
""")
                
                # Initial commit
                if readme.exists():
                    repo.index.add([str(readme)])
                    repo.index.commit("Initial policy repository setup")
                else:
                    logger.error(f"README file not created: {readme}")
                
                logger.info(f"Initialized policy Git repository at {self.git_repo_path}")
            else:
                # Open existing repository
                repo = git.Repo(self.git_repo_path)
                logger.info(f"Using existing policy Git repository at {self.git_repo_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {e}")
            # Create a minimal setup to prevent further errors
            self.git_repo = None
    
    def _load_policy_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load policy validation schemas"""
        return {
            "security_policy": {
                "type": "object",
                "required": ["name", "description", "policy_type", "enforcement_mode", "rules"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 100},
                    "description": {"type": "string", "minLength": 10, "maxLength": 1000},
                    "policy_type": {
                        "type": "string",
                        "enum": [t.value for t in PolicyType]
                    },
                    "enforcement_mode": {
                        "type": "string", 
                        "enum": [m.value for m in EnforcementMode]
                    },
                    "rules": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["name", "condition", "action"],
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "condition": {"type": "string"},
                                "action": {
                                    "type": "string",
                                    "enum": [a.value for a in ViolationAction]
                                },
                                "parameters": {"type": "object"},
                                "enabled": {"type": "boolean"}
                            }
                        }
                    },
                    "applies_to": {
                        "type": "object",
                        "properties": {
                            "repositories": {"type": "array", "items": {"type": "string"}},
                            "branches": {"type": "array", "items": {"type": "string"}},
                            "file_patterns": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "exceptions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    
    def _create_default_policies(self) -> List[SecurityPolicy]:
        """Create default security policies"""
        policies = []
        
        # Critical Vulnerability Threshold Policy
        critical_vuln_policy = SecurityPolicy(
            policy_id="critical-vulnerability-threshold",
            name="Critical Vulnerability Threshold",
            description="Block merges if critical vulnerabilities are detected",
            policy_type=PolicyType.VULNERABILITY_THRESHOLD,
            enforcement_mode=EnforcementMode.ENFORCE,
            rules=[
                PolicyRule(
                    rule_id="critical-vuln-block",
                    name="Block Critical Vulnerabilities",
                    description="Block merge if any critical severity vulnerabilities are found",
                    condition="findings.critical_count > 0",
                    action=ViolationAction.BLOCK_MERGE,
                    parameters={"severity_threshold": "critical", "max_allowed": 0}
                )
            ],
            applies_to={
                "repositories": ["*"],  # All repositories
                "branches": ["main", "master", "production"]
            }
        )
        policies.append(critical_vuln_policy)
        
        # Secret Detection Policy
        secret_policy = SecurityPolicy(
            policy_id="secret-detection-policy",
            name="Secret Detection Policy",
            description="Detect and block exposed secrets",
            policy_type=PolicyType.SECRET_DETECTION,
            enforcement_mode=EnforcementMode.ENFORCE,
            rules=[
                PolicyRule(
                    rule_id="block-hardcoded-secrets",
                    name="Block Hardcoded Secrets",
                    description="Block commits containing hardcoded secrets",
                    condition="findings.secret_exposure_count > 0",
                    action=ViolationAction.BLOCK_MERGE,
                    parameters={"secret_types": ["api_key", "password", "token", "certificate"]}
                )
            ],
            applies_to={
                "repositories": ["*"],
                "branches": ["*"]
            }
        )
        policies.append(secret_policy)
        
        return policies
    
    async def evaluate_policies(self, repository: str, branch: str, commit_hash: str,
                              scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all applicable policies against scan results"""
        try:
            # Ensure policies are loaded
            await self._ensure_policies_loaded()
            
            # Get applicable policies
            applicable_policies = await self._get_applicable_policies(repository, branch)
            
            evaluation_results = {
                "repository": repository,
                "branch": branch,
                "commit_hash": commit_hash,
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_result": "allowed",  # allowed, blocked, warning
                "policy_results": [],
                "violations": [],
                "actions_required": []
            }
            
            blocking_violations = []
            warning_violations = []
            
            for policy in applicable_policies:
                # Skip disabled policies
                if policy.enforcement_mode == EnforcementMode.DISABLED:
                    continue
                
                policy_result = await self._evaluate_single_policy(
                    policy, repository, branch, commit_hash, scan_results
                )
                
                evaluation_results["policy_results"].append(policy_result)
                
                # Collect violations
                for violation in policy_result["violations"]:
                    evaluation_results["violations"].append(violation)
                    
                    # Categorize by enforcement mode
                    if policy.enforcement_mode == EnforcementMode.ENFORCE:
                        if violation["action"] == ViolationAction.BLOCK_MERGE.value:
                            blocking_violations.append(violation)
                    elif policy.enforcement_mode == EnforcementMode.WARN:
                        warning_violations.append(violation)
            
            # Determine overall result
            if blocking_violations:
                evaluation_results["overall_result"] = "blocked"
                evaluation_results["actions_required"].append("merge_blocked")
            elif warning_violations:
                evaluation_results["overall_result"] = "warning"
                evaluation_results["actions_required"].append("review_required")
            
            # Log enforcement result
            await self._log_enforcement_result(evaluation_results)
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Failed to evaluate policies: {e}")
            return {"error": str(e), "overall_result": "error"}
    
    async def _evaluate_single_policy(self, policy: SecurityPolicy, repository: str,
                                    branch: str, commit_hash: str,
                                    scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single policy against scan results"""
        try:
            policy_result = {
                "policy_id": policy.policy_id,
                "policy_name": policy.name,
                "enforcement_mode": policy.enforcement_mode.value,
                "status": "passed",
                "violations": [],
                "evaluation_details": {}
            }
            
            # Prepare evaluation context
            context = {
                "findings": scan_results.get("findings", {}),
                "compliance": scan_results.get("compliance", {}),
                "repository": {
                    "name": repository,
                    "contains_payment_code": "payment" in repository.lower()
                },
                "metadata": scan_results.get("metadata", {})
            }
            
            # Evaluate each rule
            for rule in policy.rules:
                if not rule.enabled:
                    continue
                
                try:
                    # Evaluate rule condition
                    rule_violated = await self._evaluate_rule_condition(rule.condition, context)
                    
                    if rule_violated:
                        violation = PolicyViolation(
                            violation_id=str(uuid.uuid4()),
                            policy_id=policy.policy_id,
                            rule_id=rule.rule_id,
                            repository=repository,
                            branch=branch,
                            commit_hash=commit_hash,
                            violation_details={
                                "rule_name": rule.name,
                                "condition": rule.condition,
                                "context": context,
                                "parameters": rule.parameters
                            },
                            severity=self._determine_violation_severity(rule, context),
                            action_taken=rule.action
                        )
                        
                        # Store violation
                        await self._store_violation(violation)
                        
                        policy_result["violations"].append({
                            "violation_id": violation.violation_id,
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "action": rule.action.value,
                            "severity": violation.severity,
                            "details": violation.violation_details
                        })
                        
                        policy_result["status"] = "violated"
                
                except Exception as e:
                    logger.error(f"Failed to evaluate rule {rule.rule_id}: {e}")
                    policy_result["evaluation_details"][rule.rule_id] = f"Error: {e}"
            
            return policy_result
            
        except Exception as e:
            logger.error(f"Failed to evaluate policy {policy.policy_id}: {e}")
            return {
                "policy_id": policy.policy_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _get_applicable_policies(self, repository: str, branch: str) -> List[SecurityPolicy]:
        """Get policies that apply to the given repository and branch"""
        try:
            # Return default policies for demo
            applicable_policies = []
            for policy in self.default_policies:
                if self._policy_applies_to(repository, branch, policy.applies_to):
                    applicable_policies.append(policy)
            return applicable_policies
            
        except Exception as e:
            logger.error(f"Failed to get applicable policies: {e}")
            return []
    
    def _policy_applies_to(self, repository: str, branch: str, applies_to: Dict[str, List[str]]) -> bool:
        """Check if policy applies to repository/branch"""
        try:
            repo_patterns = applies_to.get("repositories", ["*"])
            branch_patterns = applies_to.get("branches", ["*"])
            
            # Check repository patterns
            repo_match = "*" in repo_patterns or repository in repo_patterns
            
            # Check branch patterns
            branch_match = "*" in branch_patterns or branch in branch_patterns
            
            return repo_match and branch_match
            
        except Exception as e:
            logger.error(f"Failed to check policy applicability: {e}")
            return False
    
    async def _evaluate_rule_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate rule condition"""
        try:
            # Mock evaluation for demo
            if "critical_count > 0" in condition:
                return context.get("findings", {}).get("critical_count", 0) > 0
            elif "secret_exposure_count > 0" in condition:
                return context.get("findings", {}).get("secret_exposure_count", 0) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    def _determine_violation_severity(self, rule: PolicyRule, context: Dict[str, Any]) -> str:
        """Determine violation severity based on rule and context"""
        if rule.action == ViolationAction.BLOCK_MERGE:
            return "high"
        elif rule.action == ViolationAction.REQUIRE_APPROVAL:
            return "medium"
        else:
            return "low"
    
    async def _store_violation(self, violation: PolicyViolation):
        """Store policy violation in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT INTO policy_violations (
                    violation_id, policy_id, rule_id, repository, branch,
                    commit_hash, file_path, violation_details, severity,
                    action_taken, detected_at, resolved_at, resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    violation.violation_id,
                    violation.policy_id,
                    violation.rule_id,
                    violation.repository,
                    violation.branch,
                    violation.commit_hash,
                    violation.file_path,
                    json.dumps(violation.violation_details),
                    violation.severity,
                    violation.action_taken.value if violation.action_taken else None,
                    violation.detected_at.isoformat(),
                    violation.resolved_at.isoformat() if violation.resolved_at else None,
                    violation.resolution_notes
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store violation: {e}")
    
    async def _log_enforcement_result(self, evaluation_results: Dict[str, Any]):
        """Log policy enforcement result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for policy_result in evaluation_results["policy_results"]:
                    conn.execute("""
                    INSERT INTO policy_enforcement_log (
                        log_id, policy_id, repository, branch, commit_hash,
                        enforcement_result, violations_count, action_taken, logged_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        policy_result["policy_id"],
                        evaluation_results["repository"],
                        evaluation_results["branch"],
                        evaluation_results["commit_hash"],
                        evaluation_results["overall_result"],
                        len(policy_result["violations"]),
                        evaluation_results["actions_required"][0] if evaluation_results["actions_required"] else None,
                        datetime.now(timezone.utc).isoformat()
                    ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log enforcement result: {e}")
    
    async def _ensure_policies_loaded(self):
        """Ensure policies are loaded from Git"""
        if not self._policies_loaded:
            await self._load_policies_from_git()
            self._policies_loaded = True
    
    async def _load_policies_from_git(self):
        """Load policies from Git repository"""
        try:
            # Mock implementation for demo
            logger.info("Loading policies from Git repository")
            
        except Exception as e:
            logger.error(f"Failed to load policies from Git: {e}")

# Export main classes
__all__ = [
    'PolicyAsCodeEngine', 'SecurityPolicy', 'PolicyRule', 'PolicyViolation',
    'PolicyChangeRequest', 'PolicyType', 'EnforcementMode', 'ViolationAction'
]
