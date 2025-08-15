"""
Policy as Code implementation for version-controlled security configurations
"""
import os
import yaml
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging
from enum import Enum

from pydantic import BaseModel, Field, validator
from git import Repo, InvalidGitRepositoryError
from motor.motor_asyncio import AsyncIOMotorCollection

from models.report import VulnerabilityFinding, SeverityLevel, ScanReport
from database import db_manager

logger = logging.getLogger(__name__)


class PolicyAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    FAIL = "fail"
    BLOCK = "block"


class PolicyScope(str, Enum):
    GLOBAL = "global"
    REPOSITORY = "repository"
    BRANCH = "branch"
    ENVIRONMENT = "environment"


class PolicyCondition(BaseModel):
    """Policy condition definition"""
    field: str = Field(..., description="Field to evaluate")
    operator: str = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    
    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in', 'contains', 'regex']
        if v not in valid_operators:
            raise ValueError(f"Invalid operator. Must be one of: {valid_operators}")
        return v


class PolicyRule(BaseModel):
    """Individual policy rule"""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    
    # Conditions
    conditions: List[PolicyCondition] = Field(..., description="Rule conditions")
    condition_logic: str = Field(default="AND", description="Logic for combining conditions")
    
    # Actions
    action: PolicyAction = Field(..., description="Action to take when rule matches")
    message: str = Field(..., description="Message to display when rule triggers")
    
    # Metadata
    severity: str = Field(default="medium", description="Rule severity")
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    
    @validator('condition_logic')
    def validate_condition_logic(cls, v):
        if v.upper() not in ['AND', 'OR']:
            raise ValueError("condition_logic must be 'AND' or 'OR'")
        return v.upper()


class SecurityPolicy(BaseModel):
    """Security policy definition"""
    policy_id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    version: str = Field(..., description="Policy version")
    
    # Scope
    scope: PolicyScope = Field(..., description="Policy scope")
    target_repositories: List[str] = Field(default_factory=list, description="Target repositories")
    target_branches: List[str] = Field(default_factory=list, description="Target branches")
    target_environments: List[str] = Field(default_factory=list, description="Target environments")
    
    # Rules
    rules: List[PolicyRule] = Field(..., description="Policy rules")
    
    # Thresholds
    max_critical: int = Field(default=0, description="Maximum critical vulnerabilities allowed")
    max_high: int = Field(default=5, description="Maximum high vulnerabilities allowed")
    max_medium: int = Field(default=20, description="Maximum medium vulnerabilities allowed")
    max_total: int = Field(default=100, description="Maximum total vulnerabilities allowed")
    
    # Metadata
    owner: str = Field(..., description="Policy owner")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Policy tags")
    
    # Compliance
    compliance_frameworks: List[str] = Field(default_factory=list, description="Associated compliance frameworks")
    required_controls: List[str] = Field(default_factory=list, description="Required compliance controls")


class PolicyViolation(BaseModel):
    """Policy violation record"""
    violation_id: str = Field(..., description="Unique violation identifier")
    policy_id: str = Field(..., description="Policy that was violated")
    rule_id: str = Field(..., description="Specific rule that was violated")
    
    # Context
    repository_url: str = Field(..., description="Repository URL")
    branch: str = Field(..., description="Git branch")
    commit_hash: str = Field(..., description="Git commit hash")
    scan_id: str = Field(..., description="Scan ID")
    
    # Violation details
    action: PolicyAction = Field(..., description="Action taken")
    message: str = Field(..., description="Violation message")
    severity: str = Field(..., description="Violation severity")
    
    # Evidence
    violating_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Findings that caused violation")
    threshold_exceeded: Optional[Dict[str, Any]] = Field(None, description="Threshold information if applicable")
    
    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    status: str = Field(default="open", description="Violation status")


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation"""
    policy_id: str = Field(..., description="Policy ID")
    compliant: bool = Field(..., description="Whether scan is compliant with policy")
    violations: List[PolicyViolation] = Field(default_factory=list, description="Policy violations")
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    
    # Summary
    total_findings: int = Field(0, description="Total findings")
    findings_by_severity: Dict[str, int] = Field(default_factory=dict, description="Findings by severity")
    threshold_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Threshold status")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Remediation recommendations")


class PolicyAsCodeService:
    """Service for managing Policy as Code"""
    
    def __init__(self, policies_repo_path: str = "security-policies"):
        self.policies_repo_path = Path(policies_repo_path)
        self.policies_cache: Dict[str, SecurityPolicy] = {}
        self.violations_collection: Optional[AsyncIOMotorCollection] = None
        self.evaluations_collection: Optional[AsyncIOMotorCollection] = None
        self._initialize_collections()
        self._initialized = False
        
    async def initialize(self):
        """Initialize the service asynchronously"""
        if not self._initialized:
            await self._initialize_policies_repo()
            self._initialized = True
    
    def _initialize_collections(self):
        """Initialize MongoDB collections"""
        if db_manager.client:
            db = db_manager.client[db_manager.database_name]
            self.violations_collection = db['policy_violations']
            self.evaluations_collection = db['policy_evaluations']
    
    async def _initialize_policies_repo(self):
        """Initialize the policies Git repository"""
        try:
            if not self.policies_repo_path.exists():
                logger.info(f"Creating policies repository at {self.policies_repo_path}")
                self.policies_repo_path.mkdir(parents=True, exist_ok=True)
                
                # Initialize as Git repository
                repo = Repo.init(self.policies_repo_path)
                
                # Create default policy structure
                await self._create_default_policies()
                
                # Initial commit
                repo.index.add(['*'])
                repo.index.commit("Initial commit: Default security policies")
                
                logger.info("Policies repository initialized")
            else:
                # Ensure it's a valid Git repository
                try:
                    Repo(self.policies_repo_path)
                except InvalidGitRepositoryError:
                    logger.warning("Policies directory exists but is not a Git repository. Initializing...")
                    Repo.init(self.policies_repo_path)
                
        except Exception as e:
            logger.error(f"Error initializing policies repository: {e}")
    
    async def _create_default_policies(self):
        """Create default security policies"""
        
        # Global security policy
        global_policy = SecurityPolicy(
            policy_id="global-security-policy",
            name="Global Security Policy",
            description="Default global security policy for all repositories",
            version="1.0.0",
            scope=PolicyScope.GLOBAL,
            owner="security-team",
            max_critical=0,
            max_high=3,
            max_medium=15,
            max_total=50,
            rules=[
                PolicyRule(
                    rule_id="no-critical-vulnerabilities",
                    name="No Critical Vulnerabilities",
                    description="Block any code with critical vulnerabilities",
                    conditions=[
                        PolicyCondition(
                            field="severity",
                            operator="eq",
                            value="critical"
                        )
                    ],
                    action=PolicyAction.FAIL,
                    message="Critical vulnerabilities must be fixed before deployment",
                    severity="critical"
                ),
                PolicyRule(
                    rule_id="limit-high-vulnerabilities",
                    name="Limit High Vulnerabilities",
                    description="Warn when high vulnerabilities exceed threshold",
                    conditions=[
                        PolicyCondition(
                            field="severity",
                            operator="eq",
                            value="high"
                        )
                    ],
                    action=PolicyAction.WARN,
                    message="High severity vulnerabilities should be addressed",
                    severity="high"
                ),
                PolicyRule(
                    rule_id="no-hardcoded-secrets",
                    name="No Hardcoded Secrets",
                    description="Block code with hardcoded secrets",
                    conditions=[
                        PolicyCondition(
                            field="cwe_id",
                            operator="eq",
                            value="CWE-798"
                        )
                    ],
                    action=PolicyAction.FAIL,
                    message="Hardcoded secrets detected. Use environment variables or secret management.",
                    severity="critical"
                )
            ],
            compliance_frameworks=["SOC2", "GDPR", "PCI_DSS"],
            tags=["default", "global"]
        )
        
        # Production environment policy
        production_policy = SecurityPolicy(
            policy_id="production-security-policy",
            name="Production Security Policy",
            description="Strict security policy for production environments",
            version="1.0.0",
            scope=PolicyScope.ENVIRONMENT,
            target_environments=["production", "prod"],
            owner="security-team",
            max_critical=0,
            max_high=0,
            max_medium=5,
            max_total=20,
            rules=[
                PolicyRule(
                    rule_id="zero-critical-high",
                    name="Zero Critical/High Vulnerabilities",
                    description="No critical or high vulnerabilities allowed in production",
                    conditions=[
                        PolicyCondition(
                            field="severity",
                            operator="in",
                            value=["critical", "high"]
                        )
                    ],
                    action=PolicyAction.BLOCK,
                    message="Production deployments blocked due to critical/high vulnerabilities",
                    severity="critical"
                )
            ],
            compliance_frameworks=["SOC2", "GDPR", "PCI_DSS"],
            tags=["production", "strict"]
        )
        
        # Save policies
        await self._save_policy_to_file(global_policy)
        await self._save_policy_to_file(production_policy)
    
    async def _save_policy_to_file(self, policy: SecurityPolicy):
        """Save policy to YAML file"""
        policy_file = self.policies_repo_path / f"{policy.policy_id}.yaml"
        
        with open(policy_file, 'w') as f:
            yaml.dump(policy.dict(), f, default_flow_style=False)
        
        logger.info(f"Saved policy {policy.policy_id} to {policy_file}")
    
    async def load_policies(self) -> List[SecurityPolicy]:
        """Load all policies from the repository"""
        policies = []
        
        if not self.policies_repo_path.exists():
            await self._initialize_policies_repo()
            return policies
        
        # Load YAML and JSON policy files
        for policy_file in self.policies_repo_path.glob("*.yaml"):
            policy = await self._load_policy_from_file(policy_file)
            if policy:
                policies.append(policy)
                self.policies_cache[policy.policy_id] = policy
        
        for policy_file in self.policies_repo_path.glob("*.json"):
            if not (self.policies_repo_path / f"{policy_file.stem}.yaml").exists():
                policy = await self._load_policy_from_file(policy_file)
                if policy:
                    policies.append(policy)
                    self.policies_cache[policy.policy_id] = policy
        
        logger.info(f"Loaded {len(policies)} policies")
        return policies
    
    async def _load_policy_from_file(self, policy_file: Path) -> Optional[SecurityPolicy]:
        """Load policy from file"""
        try:
            with open(policy_file, 'r') as f:
                if policy_file.suffix == '.yaml':
                    policy_data = yaml.safe_load(f)
                else:
                    policy_data = json.load(f)
            
            return SecurityPolicy(**policy_data)
        except Exception as e:
            logger.error(f"Error loading policy from {policy_file}: {e}")
            return None
    
    async def get_applicable_policies(
        self,
        repository_url: str,
        branch: str = "main",
        environment: str = "development"
    ) -> List[SecurityPolicy]:
        """Get policies applicable to repository/branch/environment"""
        
        # Load all policies if cache is empty
        if not self.policies_cache:
            await self.load_policies()
        
        applicable_policies = []
        
        for policy in self.policies_cache.values():
            if await self._is_policy_applicable(policy, repository_url, branch, environment):
                applicable_policies.append(policy)
        
        return applicable_policies
    
    async def _is_policy_applicable(
        self,
        policy: SecurityPolicy,
        repository_url: str,
        branch: str,
        environment: str
    ) -> bool:
        """Check if policy is applicable to given context"""
        
        # Global policies apply to everything
        if policy.scope == PolicyScope.GLOBAL:
            return True
        
        # Repository-specific policies
        if policy.scope == PolicyScope.REPOSITORY:
            if policy.target_repositories:
                return any(repo in repository_url for repo in policy.target_repositories)
            return False
        
        # Branch-specific policies
        if policy.scope == PolicyScope.BRANCH:
            if policy.target_branches:
                return branch in policy.target_branches
            return False
        
        # Environment-specific policies
        if policy.scope == PolicyScope.ENVIRONMENT:
            if policy.target_environments:
                return environment in policy.target_environments
            return False
        
        return False
    
    async def evaluate_policy(
        self,
        policy: SecurityPolicy,
        scan_report: ScanReport,
        repository_url: str,
        branch: str,
        commit_hash: str
    ) -> PolicyEvaluationResult:
        """Evaluate a policy against scan results"""
        
        violations = []
        findings_by_severity = {}
        
        # Count findings by severity
        for finding in scan_report.findings:
            severity = finding.severity.value
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
        
        # Check threshold violations
        threshold_violations = []
        
        if findings_by_severity.get('critical', 0) > policy.max_critical:
            threshold_violations.append({
                'threshold': 'max_critical',
                'limit': policy.max_critical,
                'actual': findings_by_severity.get('critical', 0)
            })
        
        if findings_by_severity.get('high', 0) > policy.max_high:
            threshold_violations.append({
                'threshold': 'max_high',
                'limit': policy.max_high,
                'actual': findings_by_severity.get('high', 0)
            })
        
        if findings_by_severity.get('medium', 0) > policy.max_medium:
            threshold_violations.append({
                'threshold': 'max_medium',
                'limit': policy.max_medium,
                'actual': findings_by_severity.get('medium', 0)
            })
        
        total_findings = sum(findings_by_severity.values())
        if total_findings > policy.max_total:
            threshold_violations.append({
                'threshold': 'max_total',
                'limit': policy.max_total,
                'actual': total_findings
            })
        
        # Create violations for threshold breaches
        for threshold_violation in threshold_violations:
            violation = PolicyViolation(
                violation_id=f"threshold_{threshold_violation['threshold']}_{scan_report.report_id}",
                policy_id=policy.policy_id,
                rule_id=f"threshold_{threshold_violation['threshold']}",
                repository_url=repository_url,
                branch=branch,
                commit_hash=commit_hash,
                scan_id=scan_report.report_id,
                action=PolicyAction.FAIL,
                message=f"Threshold exceeded: {threshold_violation['threshold']} limit {threshold_violation['limit']}, actual {threshold_violation['actual']}",
                severity="high",
                threshold_exceeded=threshold_violation
            )
            violations.append(violation)
        
        # Evaluate rule-based violations
        for rule in policy.rules:
            if not rule.enabled:
                continue
            
            rule_violations = await self._evaluate_rule(
                rule, scan_report, repository_url, branch, commit_hash, policy.policy_id
            )
            violations.extend(rule_violations)
        
        # Calculate compliance score
        total_possible_violations = len(policy.rules) + 4  # 4 thresholds
        actual_violations = len(violations)
        compliance_score = max(0, (total_possible_violations - actual_violations) / total_possible_violations * 100)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(violations, findings_by_severity)
        
        # Determine overall compliance
        blocking_violations = [v for v in violations if v.action in [PolicyAction.FAIL, PolicyAction.BLOCK]]
        compliant = len(blocking_violations) == 0
        
        result = PolicyEvaluationResult(
            policy_id=policy.policy_id,
            compliant=compliant,
            violations=violations,
            compliance_score=compliance_score,
            total_findings=total_findings,
            findings_by_severity=findings_by_severity,
            recommendations=recommendations
        )
        
        # Save evaluation result
        if self.evaluations_collection:
            await self.evaluations_collection.insert_one({
                **result.dict(),
                'repository_url': repository_url,
                'branch': branch,
                'commit_hash': commit_hash,
                'scan_id': scan_report.report_id,
                'evaluated_at': datetime.utcnow()
            })
        
        # Save violations
        if self.violations_collection and violations:
            violation_docs = [v.dict() for v in violations]
            await self.violations_collection.insert_many(violation_docs)
        
        return result
    
    async def _evaluate_rule(
        self,
        rule: PolicyRule,
        scan_report: ScanReport,
        repository_url: str,
        branch: str,
        commit_hash: str,
        policy_id: str
    ) -> List[PolicyViolation]:
        """Evaluate a single rule against findings"""
        
        violations = []
        violating_findings = []
        
        for finding in scan_report.findings:
            if await self._finding_matches_rule(finding, rule):
                violating_findings.append({
                    'file_path': finding.file_path,
                    'line_number': finding.line_number,
                    'rule_id': finding.rule_id,
                    'severity': finding.severity.value,
                    'message': finding.title or finding.description
                })
        
        if violating_findings:
            violation = PolicyViolation(
                violation_id=f"rule_{rule.rule_id}_{scan_report.report_id}",
                policy_id=policy_id,
                rule_id=rule.rule_id,
                repository_url=repository_url,
                branch=branch,
                commit_hash=commit_hash,
                scan_id=scan_report.report_id,
                action=rule.action,
                message=rule.message,
                severity=rule.severity,
                violating_findings=violating_findings
            )
            violations.append(violation)
        
        return violations
    
    async def _finding_matches_rule(self, finding: VulnerabilityFinding, rule: PolicyRule) -> bool:
        """Check if a finding matches a rule's conditions"""
        
        condition_results = []
        
        for condition in rule.conditions:
            result = await self._evaluate_condition(finding, condition)
            condition_results.append(result)
        
        # Apply condition logic
        if rule.condition_logic == "AND":
            return all(condition_results)
        else:  # OR
            return any(condition_results)
    
    async def _evaluate_condition(self, finding: VulnerabilityFinding, condition: PolicyCondition) -> bool:
        """Evaluate a single condition against a finding"""
        
        # Get field value from finding
        field_value = getattr(finding, condition.field, None)
        
        # Handle special field mappings
        if condition.field == "severity":
            field_value = finding.severity.value
        elif condition.field == "scanner":
            field_value = finding.scanner.value
        
        if field_value is None:
            return False
        
        # Apply operator
        if condition.operator == "eq":
            return field_value == condition.value
        elif condition.operator == "ne":
            return field_value != condition.value
        elif condition.operator == "gt":
            return field_value > condition.value
        elif condition.operator == "gte":
            return field_value >= condition.value
        elif condition.operator == "lt":
            return field_value < condition.value
        elif condition.operator == "lte":
            return field_value <= condition.value
        elif condition.operator == "in":
            return field_value in condition.value
        elif condition.operator == "not_in":
            return field_value not in condition.value
        elif condition.operator == "contains":
            return condition.value in str(field_value)
        elif condition.operator == "regex":
            import re
            return bool(re.search(condition.value, str(field_value)))
        
        return False
    
    def _generate_recommendations(
        self,
        violations: List[PolicyViolation],
        findings_by_severity: Dict[str, int]
    ) -> List[str]:
        """Generate remediation recommendations"""
        
        recommendations = []
        
        # Threshold-based recommendations
        if findings_by_severity.get('critical', 0) > 0:
            recommendations.append("Immediately fix all critical vulnerabilities before deployment")
        
        if findings_by_severity.get('high', 0) > 3:
            recommendations.append("Prioritize fixing high severity vulnerabilities")
        
        # Rule-based recommendations
        hardcoded_secrets = any(
            v.rule_id == "no-hardcoded-secrets" for v in violations
        )
        if hardcoded_secrets:
            recommendations.append("Use environment variables or secret management systems instead of hardcoded secrets")
        
        # General recommendations
        if len(violations) > 0:
            recommendations.extend([
                "Run security scans regularly during development",
                "Implement pre-commit hooks for security scanning",
                "Provide security training for development team"
            ])
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    async def evaluate_all_policies(
        self,
        scan_report: ScanReport,
        repository_url: str,
        branch: str = "main",
        commit_hash: str = "HEAD",
        environment: str = "development"
    ) -> List[PolicyEvaluationResult]:
        """Evaluate all applicable policies"""
        
        applicable_policies = await self.get_applicable_policies(repository_url, branch, environment)
        results = []
        
        for policy in applicable_policies:
            result = await self.evaluate_policy(
                policy, scan_report, repository_url, branch, commit_hash
            )
            results.append(result)
        
        return results
    
    async def update_policy_from_git(self):
        """Update policies from Git repository"""
        try:
            repo = Repo(self.policies_repo_path)
            
            # Pull latest changes
            origin = repo.remotes.origin
            origin.pull()
            
            # Clear cache and reload
            self.policies_cache.clear()
            await self.load_policies()
            
            logger.info("Policies updated from Git repository")
        except Exception as e:
            logger.error(f"Error updating policies from Git: {e}")
    
    async def get_policy_compliance_report(
        self,
        repository_url: str,
        branch: str = "main",
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate policy compliance report"""
        
        if not self.evaluations_collection:
            return {'error': 'Database not available'}
        
        # Get recent evaluations
        since_date = datetime.utcnow() - timedelta(days=days)
        cursor = self.evaluations_collection.find({
            'repository_url': repository_url,
            'branch': branch,
            'evaluated_at': {'$gte': since_date}
        }).sort('evaluated_at', -1)
        
        evaluations = []
        async for eval_doc in cursor:
            evaluations.append(eval_doc)
        
        if not evaluations:
            return {'error': 'No evaluations found'}
        
        # Calculate compliance metrics
        total_evaluations = len(evaluations)
        compliant_evaluations = len([e for e in evaluations if e.get('compliant', False)])
        compliance_rate = (compliant_evaluations / total_evaluations) * 100 if total_evaluations > 0 else 0
        
        # Get average compliance score
        compliance_scores = [e.get('compliance_score', 0) for e in evaluations]
        avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        # Get most common violations
        violation_counts = {}
        for evaluation in evaluations:
            for violation in evaluation.get('violations', []):
                rule_id = violation.get('rule_id', 'unknown')
                violation_counts[rule_id] = violation_counts.get(rule_id, 0) + 1
        
        common_violations = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'repository_url': repository_url,
            'branch': branch,
            'period_days': days,
            'total_evaluations': total_evaluations,
            'compliance_rate': round(compliance_rate, 2),
            'average_compliance_score': round(avg_compliance_score, 2),
            'common_violations': [
                {'rule_id': rule_id, 'count': count}
                for rule_id, count in common_violations
            ],
            'latest_evaluation': evaluations[0] if evaluations else None
        }


# Global policy service instance
policy_service = PolicyAsCodeService()
