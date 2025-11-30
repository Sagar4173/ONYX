# 🏢 Enterprise Features Documentation

## Overview

The ONYX Platform now includes comprehensive enterprise-grade features for audit logging, data retention, advanced compliance reporting, and enhanced notifications.

## 🎯 Features Implemented

### 1. 📝 Audit Logging System

Comprehensive audit trail for all user actions, system events, and data changes.

#### Features:

- **Complete Event Tracking**: 30+ event types covering all system operations
- **User Activity Monitoring**: Track all user actions with detailed context
- **Resource Change History**: Complete audit trail for every resource
- **Compliance Reporting**: Generate audit reports for compliance requirements
- **Integrity Verification**: SHA-256 hashing for log integrity verification
- **Suspicious Activity Detection**: Automatic detection of unusual patterns
- **Export Capabilities**: Export audit logs for archival or external analysis

#### Event Types:

- User management (login, logout, role changes, etc.)
- Project management (create, update, delete, permissions)
- Scan operations (initiated, completed, failed)
- Security events (vulnerabilities, policy violations)
- Configuration changes
- Access control events
- Data operations (export, import, delete)
- Compliance events

#### API Endpoints:

```bash
# Query audit logs
GET /api/v1/enterprise/audit-logs/query
  ?start_date=2024-01-01
  &end_date=2024-12-31
  &event_types=user_login,project_created
  &user_id=user123
  &severity=critical
  &limit=100
  &skip=0

# Get user activity
GET /api/v1/enterprise/audit-logs/user/{user_id}?days=30&limit=100

# Get resource history
GET /api/v1/enterprise/audit-logs/resource/{resource_type}/{resource_id}

# Generate compliance audit report
POST /api/v1/enterprise/audit-logs/compliance-report
{
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "report_type": "full"
}

# Export audit logs
GET /api/v1/enterprise/audit-logs/export
  ?start_date=2024-01-01
  &end_date=2024-12-31
  &format=json

# Verify log integrity
GET /api/v1/enterprise/audit-logs/verify/{event_id}
```

#### Usage Example:

```python
from services.audit_logging_service import get_audit_service, AuditEventType, AuditSeverity

# Log an audit event
audit_service = get_audit_service(db)
await audit_service.log_event(
    event_type=AuditEventType.USER_LOGIN,
    user_id="user123",
    resource_type="authentication",
    resource_id="session456",
    action="successful_login",
    details={"ip_address": "192.168.1.1"},
    severity=AuditSeverity.INFO,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Query audit logs
result = await audit_service.query_audit_logs(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    event_types=[AuditEventType.USER_LOGIN, AuditEventType.PROJECT_CREATED],
    severity=AuditSeverity.CRITICAL,
    limit=100
)

# Get user activity
activity = await audit_service.get_user_activity("user123", days=30)

# Generate compliance report
report = await audit_service.generate_compliance_report(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    report_type="full"
)
```

---

### 2. 🗄️ Data Retention Policies

Automated data cleanup with configurable retention periods and compliance-driven archiving.

#### Features:

- **Configurable Retention Periods**: Set retention policies per data type
- **Multiple Actions**: Delete, archive, compress, or anonymize data
- **Automated Execution**: Schedule or manual policy execution
- **Compliance-Aware**: 7-year retention for audit logs and compliance reports
- **Compression Support**: Gzip compression for archived data
- **Storage Statistics**: Track storage usage and optimization
- **Default Policies**: Pre-configured policies for common data types

#### Retention Policy Types:

- Scan results (default: 365 days)
- Audit logs (default: 2555 days / 7 years)
- User sessions (default: 90 days)
- Notifications (default: 180 days)
- Temporary files (default: 7 days)
- Archived reports (default: 730 days)
- Compliance reports (default: 2555 days / 7 years)

#### Retention Actions:

- **DELETE**: Permanently remove data
- **ARCHIVE**: Move to archive collection with compression
- **COMPRESS**: Compress data in place
- **ANONYMIZE**: Remove sensitive information but keep records

#### API Endpoints:

```bash
# Create retention policy
POST /api/v1/enterprise/retention/policies
{
  "policy_type": "scan_results",
  "retention_days": 365,
  "action": "archive",
  "enabled": true
}

# Execute specific policy
POST /api/v1/enterprise/retention/policies/{policy_id}/execute

# Execute all enabled policies
POST /api/v1/enterprise/retention/policies/execute-all

# Get storage statistics
GET /api/v1/enterprise/retention/statistics

# Initialize default policies
POST /api/v1/enterprise/retention/initialize-defaults
```

#### Usage Example:

```python
from services.data_retention_service import get_retention_service, RetentionPolicyType, RetentionAction

retention_service = get_retention_service(db)

# Create a retention policy
result = await retention_service.create_retention_policy(
    policy_type=RetentionPolicyType.SCAN_RESULTS,
    retention_days=365,
    action=RetentionAction.ARCHIVE,
    enabled=True,
    metadata={"description": "Archive scan results after 1 year"}
)

# Execute a specific policy
execution = await retention_service.execute_retention_policy(policy_id)

# Execute all policies
result = await retention_service.execute_all_policies()

# Get statistics
stats = await retention_service.get_retention_statistics()

# Initialize default policies
await retention_service.initialize_default_policies()
```

---

### 3. ⚖️ Advanced Compliance Reporting

Comprehensive compliance assessment for SOX, HIPAA, ISO 27001, PCI DSS, GDPR, and more.

#### Supported Frameworks:

- **SOX** (Sarbanes-Oxley Act) - Financial reporting compliance
- **HIPAA** - Healthcare data privacy and security
- **ISO 27001** - Information security management
- **PCI DSS** - Payment card data security
- **GDPR** - EU data protection regulation
- **SOC2** - Service organization controls
- **NIST** - Cybersecurity framework
- **CIS** - Security benchmarks
- **OWASP** - Web application security

#### Features:

- **Framework-Specific Assessments**: Tailored control evaluation
- **Compliance Scoring**: 0-100% compliance score calculation
- **Control-Level Analysis**: Detailed assessment of each control
- **Trend Tracking**: Monitor compliance over time
- **Executive Summaries**: Business-focused compliance reports
- **Action Items**: Prioritized remediation tasks
- **Multi-Framework Reports**: Assess multiple frameworks simultaneously

#### Compliance Statuses:

- **COMPLIANT**: ≥95% compliance score
- **PARTIALLY_COMPLIANT**: 70-94% compliance score
- **NON_COMPLIANT**: <70% compliance score
- **NOT_APPLICABLE**: Control doesn't apply
- **UNDER_REVIEW**: Assessment in progress

#### API Endpoints:

```bash
# Assess compliance against a framework
POST /api/v1/enterprise/compliance/assess
{
  "project_id": "project123",
  "framework": "sox"
}

# Generate comprehensive compliance report
POST /api/v1/enterprise/compliance/report
{
  "project_id": "project123",
  "frameworks": ["sox", "hipaa", "iso_27001"],
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z"
}

# Get compliance trend
GET /api/v1/enterprise/compliance/trend/{project_id}/{framework}?days=90

# List supported frameworks
GET /api/v1/enterprise/compliance/frameworks

# Get project assessments
GET /api/v1/enterprise/compliance/project/{project_id}/assessments?limit=10
```

#### Usage Example:

```python
from services.advanced_compliance_service import get_compliance_service, ComplianceFramework

compliance_service = get_compliance_service(db)

# Assess compliance
assessment = await compliance_service.assess_compliance(
    project_id="project123",
    framework=ComplianceFramework.SOX,
    scan_results=scan_data
)

# Generate comprehensive report
report = await compliance_service.generate_compliance_report(
    project_id="project123",
    frameworks=[
        ComplianceFramework.SOX,
        ComplianceFramework.HIPAA,
        ComplianceFramework.ISO_27001
    ],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Get compliance trend
trend = await compliance_service.get_compliance_trend(
    project_id="project123",
    framework=ComplianceFramework.SOX,
    days=90
)
```

---

### 4. 🔔 Enhanced Notification System

Multi-channel notifications with smart alerting and activity feeds.

#### Features (Existing - Enhanced):

- Multi-channel support (Email, Slack, Teams, In-App)
- Smart severity-based routing
- Activity feed tracking
- Alert rules with conditions
- Notification preferences per user
- Real-time delivery status

---

## 📊 Compliance Framework Details

### SOX (Sarbanes-Oxley Act)

**Controls Assessed:**

- SOX-302: Corporate Responsibility for Financial Reports

  - Access controls for financial systems
  - Audit trail for financial data changes
  - Segregation of duties
  - Change management procedures

- SOX-404: Management Assessment of Internal Controls

  - Documented security policies
  - Regular security assessments
  - Vulnerability management process
  - Incident response procedures

- SOX-409: Real-Time Issuer Disclosures
  - Real-time security monitoring
  - Immediate incident reporting
  - Automated alerting systems

### HIPAA (Health Insurance Portability and Accountability Act)

**Controls Assessed:**

- HIPAA-164.308: Administrative Safeguards
- HIPAA-164.310: Physical Safeguards
- HIPAA-164.312: Technical Safeguards
- HIPAA-164.316: Policies and Procedures

### ISO 27001:2013

**Controls Assessed:**

- ISO-A.12.6: Technical Vulnerability Management
- ISO-A.12.4: Logging and Monitoring
- ISO-A.9.2: User Access Management
- ISO-A.18.1: Compliance with Legal Requirements

### PCI DSS

**Controls Assessed:**

- PCI-6.5: Secure Coding Practices
- PCI-11.2: Vulnerability Scanning

### GDPR

**Controls Assessed:**

- GDPR-32: Security of Processing
- GDPR-33: Breach Notification

---

## 🔧 Configuration

### Environment Variables

```bash
# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
FROM_EMAIL=noreply@onyx-security.ai

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_TOKEN=xoxb-...

# Microsoft Teams Configuration
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

### Database Collections

The enterprise features create the following MongoDB collections:

- `audit_logs` - Audit event records
- `compliance_assessments` - Compliance assessment results
- `compliance_reports` - Generated compliance reports
- `retention_policies` - Data retention policy configurations
- `archived_audit_logs` - Archived audit log data
- `archived_scan_reports` - Archived scan results
- `archived_compliance_reports` - Archived compliance reports
- `notifications` - Notification records
- `alert_rules` - Smart alert rule configurations

---

## 🚀 Getting Started

### 1. Initialize Default Retention Policies

```bash
POST http://localhost:8000/api/v1/enterprise/retention/initialize-defaults
```

### 2. Enable Audit Logging

Audit logging is automatically enabled for all API operations. No configuration needed.

### 3. Run Compliance Assessment

```bash
POST http://localhost:8000/api/v1/enterprise/compliance/assess
Content-Type: application/json

{
  "project_id": "your-project-id",
  "framework": "sox"
}
```

### 4. View Audit Logs

```bash
GET http://localhost:8000/api/v1/enterprise/audit-logs/query?limit=50
```

---

## 📈 Best Practices

### Audit Logging

1. **Log All Critical Operations**: User authentication, permission changes, data modifications
2. **Include Context**: IP address, user agent, session ID for forensic analysis
3. **Regular Reviews**: Schedule periodic audit log reviews
4. **Integrity Verification**: Periodically verify log integrity using checksums
5. **Retention Compliance**: Maintain logs per regulatory requirements (7 years for SOX/HIPAA)

### Data Retention

1. **Define Policies Early**: Set retention policies before data accumulation
2. **Test Archival**: Verify archive/restore processes work correctly
3. **Monitor Storage**: Track storage usage and optimize regularly
4. **Compliance First**: Ensure retention periods meet regulatory requirements
5. **Automate Execution**: Schedule regular policy execution

### Compliance Reporting

1. **Regular Assessments**: Run compliance assessments after each scan
2. **Track Trends**: Monitor compliance scores over time
3. **Prioritize Actions**: Focus on high-priority non-compliant controls
4. **Document Evidence**: Maintain evidence for all compliance controls
5. **Multi-Framework**: Assess against all applicable frameworks

---

## 🔒 Security Considerations

1. **Audit Log Protection**: Audit logs are tamper-evident with SHA-256 hashing
2. **Access Control**: Restrict access to audit logs and compliance reports
3. **Data Anonymization**: Use ANONYMIZE action for GDPR compliance
4. **Secure Archival**: Archived data is compressed and encrypted
5. **Retention Enforcement**: Automated policies prevent manual data retention violations

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

1. **Audit Log Volume**: Events per day/hour
2. **Storage Usage**: Total storage per collection
3. **Compliance Scores**: Trend over time per framework
4. **Policy Execution**: Success rate and processed items
5. **Retention Statistics**: Data cleaned up vs. archived

---

## 🆘 Troubleshooting

### Issue: Audit Logs Not Appearing

**Solution**: Check that the audit service is properly initialized:

```python
from services.audit_logging_service import get_audit_service
audit_service = get_audit_service(db)
```

### Issue: Retention Policy Not Executing

**Solution**: Verify policy is enabled:

```bash
GET /api/v1/enterprise/retention/statistics
```

### Issue: Compliance Assessment Shows 0%

**Solution**: Ensure scan results exist for the project:

```bash
GET /api/v1/reports/{project_id}
```

---

## 📚 Additional Resources

- [API Documentation](../API.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [Security Best Practices](../SECURITY.md)
- [Deployment Guide](../DEPLOYMENT.md)

---

## ✅ Implementation Status

| Feature                | Status      | API Endpoints | Documentation |
| ---------------------- | ----------- | ------------- | ------------- |
| Audit Logging          | ✅ Complete | 7 endpoints   | ✅ Complete   |
| Data Retention         | ✅ Complete | 5 endpoints   | ✅ Complete   |
| Advanced Compliance    | ✅ Complete | 6 endpoints   | ✅ Complete   |
| Enhanced Notifications | ✅ Enhanced | Existing      | ✅ Complete   |

---

**All enterprise features are production-ready and fully integrated!** 🎉
