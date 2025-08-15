# Enhanced Security Features Documentation

This document describes the three major enhanced security features implemented in the SecureDevOps AI Platform:

## 1. Custom Rule Engine

### Overview
The Custom Rule Engine allows users to create, manage, and deploy custom security rules that can be executed by various scanners (Semgrep, regex-based, etc.).

### Features

#### User-Defined Security Policies
- **YAML/JSON Rule Format**: Rules can be defined in both YAML and JSON formats
- **Multiple Rule Types**: Support for Semgrep rules, regex patterns, and custom logic
- **CWE Mapping**: Rules can be mapped to Common Weakness Enumeration (CWE) identifiers
- **Language Support**: Rules can target specific programming languages and file patterns

#### Rule Template Library
- **Pre-built Templates**: Ready-to-use rule templates for common vulnerabilities
- **CWE Coverage**: Templates mapped to specific CWE categories
- **Customizable Parameters**: Templates can be customized with user-specific parameters
- **Version Control**: Templates are version-controlled and maintained centrally

#### Rule Management
- **Validation Framework**: Rules are validated before deployment
- **Testing Support**: Built-in test case execution for rule validation
- **Version Control**: All rules are stored in Git for change tracking
- **Rule Libraries**: Organize rules into reusable libraries

### API Endpoints

#### Rule Management
```
POST   /api/security/rules                     # Create new rule
GET    /api/security/rules                     # List all rules
GET    /api/security/rules/{rule_id}          # Get specific rule
PUT    /api/security/rules/{rule_id}          # Update rule
DELETE /api/security/rules/{rule_id}          # Delete rule
POST   /api/security/rules/{rule_id}/validate # Validate rule
POST   /api/security/rules/{rule_id}/test     # Test rule
```

#### Template Management
```
GET    /api/security/templates                      # List templates
GET    /api/security/templates/{template_id}        # Get template
POST   /api/security/templates/{template_id}/rules  # Create rule from template
```

### Rule Format Example

```yaml
id: "custom-sql-injection"
name: "SQL Injection Detection"
description: "Detects potential SQL injection vulnerabilities"
type: "semgrep"
severity: "high"
pattern: |
  $QUERY = ... + $INPUT + ...
  ...
  $CURSOR.execute($QUERY)
author: "security-team"
cwe_ids: ["CWE-89"]
languages: ["python", "java"]
file_patterns: ["**/*.py", "**/*.java"]
test_cases:
  - content: |
      query = "SELECT * FROM users WHERE id = " + user_id
      cursor.execute(query)
    expected_matches: 1
  - content: |
      query = "SELECT * FROM users WHERE id = ?"
      cursor.execute(query, (user_id,))
    expected_matches: 0
```

## 2. Baseline Scanning

### Overview
Baseline Scanning provides historical comparison capabilities, allowing teams to track security improvements and identify regressions over time.

### Features

#### Historical Comparison
- **Scan Fingerprints**: Create unique fingerprints for each security finding
- **Baseline Creation**: Establish baselines from previous scans
- **Drift Detection**: Compare current scans against established baselines
- **Change Tracking**: Track which findings are new, fixed, or persisting

#### Security Drift Detection
- **Automated Comparison**: Automatic comparison with previous baselines
- **Regression Identification**: Identify when previously fixed issues reappear
- **Trend Analysis**: Analyze security trends over time
- **Scoring System**: Quantify security improvements or degradations

#### Baseline Management
- **Multiple Baselines**: Support for multiple baselines per repository/branch
- **Tagging System**: Tag baselines for easy organization and retrieval
- **Retention Policies**: Configurable retention for baseline data
- **Metadata Tracking**: Track baseline creation context and metadata

### API Endpoints

#### Baseline Operations
```
POST   /api/security/baselines                    # Create baseline
GET    /api/security/baselines                    # List baselines
GET    /api/security/baselines/{baseline_id}      # Get baseline
DELETE /api/security/baselines/{baseline_id}      # Delete baseline
POST   /api/security/baselines/{baseline_id}/compare # Compare with baseline
```

#### Drift Analysis
```
POST   /api/security/drift/analyze               # Analyze drift
GET    /api/security/drift/trends                # Get trend analysis
GET    /api/security/drift/regressions           # Get regression alerts
```

### Baseline Data Model

```python
class ScanBaseline:
    baseline_id: str
    repository_url: str
    branch: str
    commit_hash: str
    scan_report_id: str
    created_at: datetime
    created_by: str
    fingerprints: List[BaselineFingerprint]
    total_findings: int
    severity_counts: dict
    tags: List[str]
    metadata: dict
```

## 3. Policy as Code

### Overview
Policy as Code enables version-controlled security policies that are automatically enforced during scans, providing consistent security governance across projects.

### Features

#### Version-Controlled Security Configs
- **Git Integration**: Policies stored in Git repositories
- **Change Tracking**: Full audit trail of policy changes
- **Branch Support**: Different policies for different environments/branches
- **Merge Workflows**: Standard Git workflows for policy updates

#### Automated Policy Enforcement
- **Scan-time Evaluation**: Policies evaluated automatically during scans
- **Threshold Enforcement**: Configurable severity and count thresholds
- **Rule-based Policies**: Complex rule-based policy conditions
- **Environment-specific**: Different policies for different environments

#### Policy Compliance Reporting
- **Compliance Scoring**: Quantitative compliance assessment
- **Violation Tracking**: Detailed tracking of policy violations
- **Recommendations**: Automated recommendations for policy compliance
- **Historical Compliance**: Track compliance trends over time

### API Endpoints

#### Policy Management
```
GET    /api/security/policies                     # List policies
GET    /api/security/policies/{policy_id}         # Get policy
POST   /api/security/policies/sync                # Sync from Git
POST   /api/security/policies/evaluate            # Evaluate policies
```

#### Compliance Operations
```
GET    /api/security/compliance/status            # Get compliance status
GET    /api/security/compliance/violations        # Get violations
GET    /api/security/compliance/trends            # Get compliance trends
POST   /api/security/compliance/evaluate          # Evaluate compliance
```

### Policy Format Example

```yaml
policy_id: "production-security-policy"
name: "Production Security Policy"
description: "Security policy for production environments"
version: "2.1.0"
scope: "repository"
target_repositories: ["org/critical-app"]
target_branches: ["main", "release/*"]
environments: ["production"]
owner: "security-team"

# Threshold-based policies
max_critical: 0
max_high: 2
max_medium: 10
max_low: 50

# Rule-based policies
rules:
  - rule_id: "no-hardcoded-secrets"
    name: "No Hardcoded Secrets"
    description: "Block any hardcoded secrets"
    conditions:
      - field: "cwe_id"
        operator: "in"
        value: ["CWE-798", "CWE-259"]
    action: "fail"
    message: "Hardcoded secrets must be removed"
    
  - rule_id: "sql-injection-check"
    name: "SQL Injection Prevention"
    description: "Block SQL injection vulnerabilities"
    conditions:
      - field: "cwe_id"
        operator: "eq"
        value: "CWE-89"
      - field: "severity"
        operator: "gte"
        value: "medium"
    action: "warn"
    message: "SQL injection vulnerabilities should be fixed"

# Notification settings
notifications:
  on_violation: true
  channels: ["slack", "email"]
  recipients: ["security-team@company.com"]
```

## Integration and Workflows

### Complete Security Workflow

1. **Rule Development**: Create custom rules using the Rule Engine
2. **Baseline Establishment**: Create baselines from initial scans
3. **Policy Definition**: Define policies as code in Git
4. **Automated Scanning**: Run scans with custom rules
5. **Drift Analysis**: Compare results against baselines
6. **Policy Evaluation**: Evaluate scan results against policies
7. **Compliance Reporting**: Generate compliance reports and recommendations

### Example Workflow Implementation

```python
# 1. Create custom rule
rule = CustomRule(
    id="api-key-detection",
    name="API Key Detection",
    type=RuleType.REGEX,
    pattern=r"api_key\s*=\s*['\"]([A-Za-z0-9]{32,})['\"]",
    severity=RuleSeverity.HIGH
)
await rule_engine.save_rule(rule)

# 2. Run scan and create baseline
scan_report = await scanner.scan_repository(repo_url)
baseline = await baseline_service.create_baseline(
    scan_report=scan_report,
    repository_url=repo_url,
    branch="main",
    commit_hash="abc123",
    created_by="ci-system"
)

# 3. Define and save policy
policy = SecurityPolicy(
    policy_id="api-security-policy",
    max_high=0,  # No high severity findings allowed
    rules=[
        PolicyRule(
            rule_id="no-api-keys",
            conditions=[
                PolicyCondition(field="rule_id", operator="eq", value="api-key-detection")
            ],
            action=PolicyAction.FAIL
        )
    ]
)
await policy_service.save_policy(policy)

# 4. Evaluate future scans
new_scan = await scanner.scan_repository(repo_url)

# Compare with baseline
drift = await baseline_service.compare_with_baseline(new_scan, baseline.baseline_id)

# Evaluate against policies
compliance = await policy_service.evaluate_all_policies(
    scan_report=new_scan,
    repository_url=repo_url,
    branch="main"
)
```

## Configuration

### Environment Variables

```bash
# Rule Engine Configuration
CUSTOM_RULES_REPO_URL=https://github.com/org/security-rules.git
CUSTOM_RULES_BRANCH=main
RULE_TEMPLATES_PATH=/app/templates

# Baseline Configuration
BASELINE_RETENTION_DAYS=90
BASELINE_MAX_PER_REPO=50

# Policy Engine Configuration
POLICY_REPO_URL=https://github.com/org/security-policies.git
POLICY_SYNC_INTERVAL=300
POLICY_ENFORCEMENT_MODE=strict
```

### Database Collections

The enhanced features use the following MongoDB collections:

- `custom_rules`: Stores custom security rules
- `rule_templates`: Stores rule templates
- `scan_baselines`: Stores baseline fingerprints
- `security_drift`: Stores drift analysis results
- `security_policies`: Stores security policies
- `policy_violations`: Stores policy violation records

## Monitoring and Alerting

### Metrics Tracked

- Rule usage statistics
- Baseline drift trends
- Policy compliance rates
- Scan comparison performance
- Rule validation success rates

### Alert Conditions

- New critical vulnerabilities detected
- Security drift beyond threshold
- Policy violations in production
- Baseline comparison failures
- Rule validation errors

## Security Considerations

- **Rule Validation**: All custom rules are validated before deployment
- **Access Control**: Role-based access to rule and policy management
- **Audit Logging**: Complete audit trail of all security operations
- **Secure Storage**: Encrypted storage of sensitive rule and policy data
- **Git Security**: Secure Git integration with proper authentication

## Best Practices

1. **Rule Development**:
   - Always include test cases with custom rules
   - Map rules to relevant CWE identifiers
   - Use descriptive names and documentation
   - Version control all rule changes

2. **Baseline Management**:
   - Create baselines after major releases
   - Tag baselines with meaningful descriptions
   - Regular cleanup of old baselines
   - Monitor drift trends regularly

3. **Policy Management**:
   - Use environment-specific policies
   - Regular policy reviews and updates
   - Test policies in development first
   - Document policy rationale and exceptions

4. **Integration**:
   - Integrate with CI/CD pipelines
   - Set up proper monitoring and alerting
   - Regular training on new features
   - Continuous improvement based on metrics
