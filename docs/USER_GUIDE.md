# 🎓 User Guide

## Welcome to ONYX Security Intelligence Platform

ONYX is an enterprise-grade security analysis tool that combines multiple security scanners with artificial intelligence to provide comprehensive vulnerability assessments, intelligent risk prioritization, and actionable remediation guidance.

This guide will help you get started with the platform, understand its features, and make the most of its capabilities.

---

## 🚀 Getting Started

### First Login

1. **Access the Platform**

   - Open your web browser and navigate to your ONYX Platform URL
   - Default development URL: `http://localhost:3000`

2. **Initial Setup**

   - If this is your first time accessing the platform, you'll need to create an admin account
   - Contact your system administrator for login credentials

3. **Dashboard Overview**
   - Upon login, you'll see the main dashboard with:
     - Recent scan results
     - Security metrics overview
     - Active scans status
     - Quick action buttons

---

## 📊 Understanding the Dashboard

### Main Dashboard Components

**1. Security Overview Card**

- Total vulnerabilities found across all projects
- Severity breakdown (Critical, High, Medium, Low)
- Trend indicators showing improvement or degradation

**2. Recent Scans Section**

- List of recent security scans
- Scan status (Completed, Running, Failed)
- Quick access to detailed reports

**3. Project Statistics**

- Number of projects monitored
- Average vulnerabilities per project
- Most critical projects requiring attention

**4. Scanner Status**

- Real-time status of all security scanners
- Last update times for scanner databases
- Health indicators for each tool

### Navigation Menu

**Projects** - View and manage all monitored projects
**Reports** - Access detailed scan reports and analytics
**Scans** - Monitor active scans and scan history
**Settings** - Configure platform settings and integrations
**Help** - Access documentation and support resources

---

## 🔍 Running Security Scans

### Manual Scan Submission

1. **Navigate to Scan Submission**

   - Click "New Scan" button on the dashboard
   - Or go to **Scans** → **Submit New Scan**

2. **Configure Scan Parameters**

   ```
   Repository URL: https://github.com/yourusername/your-repo.git
   Branch: main (or specify branch)
   Scan Types: Select desired security scans
   ```

3. **Available Scan Types**

   - **SAST (Static Analysis)**: Source code vulnerability scanning
   - **Secrets Detection**: Find exposed API keys and credentials
   - **Container Security**: Docker image vulnerability scanning
   - **Infrastructure**: Infrastructure-as-Code security analysis
   - **Dependency Check**: Third-party package vulnerability scanning

4. **Start the Scan**
   - Review your configuration
   - Click "Start Scan"
   - You'll receive a unique scan ID for tracking

### Automated Scans via Git Webhooks

**Set up automatic scanning when code is pushed:**

1. **Configure Webhook in Your Git Repository**

   **For GitHub:**

   - Go to repository **Settings** → **Webhooks**
   - Click "Add webhook"
   - Payload URL: `https://your-platform-url/webhook/`
   - Content type: `application/json`
   - Secret: Configure in platform settings
   - Events: Select "Push" events

   **For GitLab:**

   - Go to project **Settings** → **Webhooks**
   - URL: `https://your-platform-url/webhook/`
   - Secret Token: Configure in platform settings
   - Trigger: Push events

2. **Webhook Configuration in Platform**
   - Navigate to **Settings** → **Integrations**
   - Configure webhook secret keys
   - Enable automatic scanning
   - Set branch filters (e.g., only scan main/master branches)

### Monitoring Scan Progress

**Real-time Scan Monitoring:**

- Scans are displayed in real-time on the dashboard
- Progress indicators show completion percentage
- Estimated completion times are provided
- WebSocket updates provide live status updates

**Scan Statuses:**

- 🟡 **Pending**: Scan queued for processing
- 🔵 **Running**: Scan actively executing
- 🟢 **Completed**: Scan finished successfully
- 🔴 **Failed**: Scan encountered errors
- ⚫ **Cancelled**: Scan was manually stopped

---

## 📋 Understanding Scan Reports

### Unified Security Report Interface

Each scan report provides a comprehensive, unified view with **6 interactive tabs**:

#### **Tab 1: Overview**

The overview tab gives you an at-a-glance summary:

- **Security Score** (0-100) - AI-calculated overall security rating
- **Risk Score** (0-100) - Aggregated risk assessment
- **Severity Breakdown** - Critical, High, Medium, Low, Info counts
- **Key Metrics** - Total findings, scanner results, scan duration
- **Risk Trends** - Visual indicators of security posture

#### **Tab 2: Security Findings**

Detailed vulnerability listing with:

- **Filterable List** - Filter by severity, scanner, file
- **Vulnerability Details** - Title, severity, file location, line numbers
- **Code Context** - Vulnerable code snippets with highlighting
- **CWE/CVE References** - Links to vulnerability databases
- **Quick Actions** - Copy code, expand details

#### **Tab 3: AI Analysis**

GPT-4 or Gemini-powered intelligent analysis:

- **Executive Summary** - Natural language security assessment
- **Risk Assessment** - AI-calculated risk score with breakdown
- **Threat Categories** - Categorized security threats identified
- **Attack Vectors** - Potential exploitation paths
- **Priority Findings** - Top vulnerabilities requiring attention
- **Compliance Impact** - Effects on regulatory compliance

#### **Tab 4: Compliance Mapping**

Interactive compliance framework analysis:

- **Standard Toggles** - Select OWASP, NIST, ISO27001, PCI-DSS
- **Compliance Rate** - Percentage compliance for each framework
- **Category Breakdown** - Status of each compliance category
- **Finding Mapping** - See which vulnerabilities affect each control
- **Risk Indicators** - Visual severity indicators per category
- **Recommendations** - Priority-based compliance improvement tips

**Supported Compliance Frameworks:**

- **OWASP Top 10 (2021)** - A01-A10 categories
- **NIST Cybersecurity Framework (1.1)** - Identify, Protect, Detect, Respond, Recover
- **ISO 27001:2013** - A.8-A.18 controls
- **PCI DSS** - Requirements 1-12

#### **Tab 5: Remediation Roadmap**

Prioritized action plan with timeline:

- **Immediate (0-48 hours)** - Critical and high severity issues
- **Short-term (1-2 weeks)** - Medium severity issues
- **Long-term (1+ month)** - Low severity and improvements
- **AI Remediation Plan** - When available, AI-generated specific actions
- **Quick Wins** - Easy security improvements to implement
- **Best Practices** - Security recommendations

#### **Tab 6: Scanner Results**

Individual scanner performance:

- **Scanner Status** - Success/failure for each tool
- **Findings Count** - Vulnerabilities found per scanner
- **Duration** - Execution time for each scan
- **Error Details** - Any issues during scanning

### Reading Vulnerability Details

**Vulnerability Information Includes:**

```
Title: SQL Injection in User Authentication
Severity: HIGH
File: src/auth/login.py
Line: 42
CWE ID: CWE-89
OWASP Category: A03:2021 – Injection
Confidence: High
```

**Code Context:**

- Vulnerable code snippets
- Line numbers and file locations
- Surrounding code context for better understanding

### AI-Powered Analysis

**Executive Summary:**

- Natural language summary of security posture
- Key security concerns highlighted
- Overall risk assessment
- Security and risk scores (0-100)

**Threat Intelligence:**

- **Threat Categories** - Injection attacks, authentication issues, data exposure, etc.
- **Attack Vectors** - How vulnerabilities could be exploited
- **Affected Components** - Files and functions at risk

**Priority Findings:**

- Most critical vulnerabilities requiring immediate attention
- Risk-based prioritization
- Business impact assessment

**Remediation Recommendations:**

- Specific fix suggestions for each vulnerability
- Secure coding examples
- Best practice recommendations
- Prioritized roadmap with timeline

**Compliance Impact:**

- Effects on OWASP, NIST, ISO27001, PCI-DSS compliance
- Control mapping per framework
- Audit preparation guidance

---

## 🔧 Platform Features

### Project Management

**Adding New Projects:**

1. Navigate to **Projects** → **Add Project**
2. Enter project details:
   - Project name
   - Repository URL
   - Primary branch
   - Scan frequency
   - Notification preferences

**Project Settings:**

- Configure automatic scan triggers
- Set notification preferences
- Define custom scan parameters
- Manage access permissions

### Report Management

**Viewing Reports:**

- **All Reports**: Comprehensive list of all scan reports
- **Filter Options**: Filter by project, date, severity, status
- **Search**: Search reports by project name or vulnerability type
- **Sorting**: Sort by date, severity, or project name

**Exporting Reports:**

- **PDF Export**: Professional reports for stakeholders
- **JSON Export**: Machine-readable format for integration
- **CSV Export**: Spreadsheet-compatible format for analysis

**Report Sharing:**

- Generate shareable links for specific reports
- Configure access permissions
- Set expiration dates for shared links

### Advanced Analytics

**Security Trends:**

- Vulnerability trends over time
- Project security score evolution
- Scanner effectiveness metrics

**Comparative Analysis:**

- Compare security posture across projects
- Benchmark against industry standards
- Track improvement over time

**Custom Dashboards:**

- Create custom views for different stakeholders
- Configure KPI displays
- Set up automated reports

---

## 🔔 Notifications & Integrations

### Slack Integration

**Setup Slack Notifications:**

1. Navigate to **Settings** → **Notifications**
2. Click "Configure Slack"
3. Add your Slack webhook URL
4. Configure notification triggers:
   - High/Critical vulnerabilities found
   - Scan completion
   - Scan failures

**Notification Examples:**

```
🚨 Critical vulnerability found in project-name
📊 Security scan completed for project-name: 5 issues found
✅ All vulnerabilities resolved in project-name
```

### Microsoft Teams Integration

**Setup Teams Notifications:**

1. Create an incoming webhook in your Teams channel
2. Add webhook URL in **Settings** → **Notifications**
3. Configure notification preferences
4. Test the integration

### Email Notifications

**Configure Email Alerts:**

- SMTP server configuration
- Email templates customization
- Recipient management
- Notification scheduling

---

## ⚙️ Platform Configuration

### Scanner Configuration

**Semgrep (SAST)**

- Rule sets: Enable/disable specific rule categories
- Custom rules: Add organization-specific rules
- Exclusions: Configure files/paths to exclude

**Trivy (Container Security)**

- Severity filtering
- Database update frequency
- Registry authentication

**GitLeaks (Secrets Detection)**

- Custom patterns for organization-specific secrets
- Whitelist management
- False positive handling

### AI Analysis Settings

**OpenAI Configuration:**

- API key management
- Model selection (GPT-4, GPT-3.5)
- Token limits and cost management
- Custom prompts for analysis

**Analysis Depth:**

- Executive summary generation
- Detailed technical analysis
- Compliance mapping
- Remediation guidance level

### User Management

**User Roles:**

- **Admin**: Full platform access and configuration
- **Security Manager**: View all reports, configure scans
- **Developer**: View reports for assigned projects
- **Viewer**: Read-only access to reports

**Access Control:**

- Project-based permissions
- Role-based access control (RBAC)
- API token management
- Audit trail logging

---

## 🛠️ Troubleshooting

### Common Issues

**1. Scan Failures**

_Symptoms:_ Scans fail with error messages
_Causes:_

- Repository access issues
- Scanner tool problems
- Resource limitations

_Solutions:_

- Verify repository URL and access permissions
- Check scanner status in **Settings** → **System Health**
- Contact administrator if resource issues persist

**2. Missing Vulnerabilities**

_Symptoms:_ Expected vulnerabilities not detected
_Causes:_

- Scanner configuration issues
- File exclusions
- Rule set limitations

_Solutions:_

- Review scanner configurations
- Check file exclusion patterns
- Update scanner rule sets

**3. Slow Scan Performance**

_Symptoms:_ Scans take longer than expected
_Causes:_

- Large repositories
- Resource limitations
- Network issues

_Solutions:_

- Consider excluding non-essential files
- Contact administrator about resource allocation
- Break large repositories into smaller components

### Getting Help

**Documentation:**

- User Guide (this document)
- API Documentation
- Integration guides

**Support Channels:**

- GitHub Issues for bug reports
- GitHub Discussions for questions
- Email support for enterprise customers

**Self-Service Tools:**

- System health dashboard
- Log viewing for scan details
- Configuration validation tools

---

## 📚 Best Practices

### Effective Security Scanning

**1. Regular Scanning**

- Set up automatic scans for all active branches
- Schedule daily scans for critical projects
- Perform immediate scans after security-related changes

**2. Proper Configuration**

- Configure appropriate exclusions for third-party code
- Customize rules for your technology stack
- Set up meaningful notification thresholds

**3. Result Management**

- Review all high and critical vulnerabilities immediately
- Establish SLAs for vulnerability remediation
- Track progress on security improvements

### Workflow Integration

**1. Development Process**

- Integrate scanning into CI/CD pipelines
- Require security approval for production deployments
- Train developers on secure coding practices

**2. Security Team Workflow**

- Use the platform for security assessments
- Generate reports for compliance audits
- Track security metrics and trends

**3. Management Reporting**

- Use executive summaries for stakeholder communication
- Create custom dashboards for different audiences
- Schedule automated reports for regular updates

### Optimization Tips

**1. Performance Optimization**

- Use file exclusions to reduce scan time
- Schedule heavy scans during off-hours
- Monitor resource usage and optimize accordingly

**2. Result Quality**

- Regularly review and update custom rules
- Maintain whitelists for false positives
- Provide feedback on AI analysis accuracy

**3. Cost Management**

- Monitor AI analysis token usage
- Optimize scan frequency based on project activity
- Use severity filtering to focus on critical issues

---

## 🔄 Advanced Usage

### API Integration

**Using the REST API:**

- Submit scans programmatically
- Retrieve reports in various formats
- Integrate with existing security tools

**Webhook Integration:**

- Receive real-time notifications
- Trigger external workflows
- Integrate with SIEM systems

### Custom Dashboards

**Creating Custom Views:**

- Filter data by project, severity, or time period
- Create role-specific dashboards
- Export dashboard data for external reporting

### Automation Workflows

**Automated Response:**

- Set up automated ticket creation for vulnerabilities
- Configure automatic notifications for different severity levels
- Integrate with change management systems

---

## 📞 Support & Resources

### Getting Additional Help

**Community Support:**

- [GitHub Discussions](https://github.com/Sagar4173/ONYX/discussions)
- [User Forum](https://forum.onyx-security.ai)
- [Community Slack](https://slack.onyx-security.ai)

**Enterprise Support:**

- Dedicated support team
- Priority response times
- Custom integration assistance
- Training and onboarding

**Documentation:**

- [Installation Guide](./INSTALLATION.md)
- [API Documentation](./API.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Contributing Guide](./CONTRIBUTING.md)

### Feature Requests & Feedback

We welcome feedback and feature requests! Please use our GitHub repository to:

- Report bugs
- Request new features
- Share usage feedback
- Contribute improvements

---

**Thank you for using ONYX Security Intelligence Platform!**

We're committed to helping you build more secure software through intelligent automation and comprehensive security analysis.
