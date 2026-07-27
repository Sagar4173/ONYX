# User Guide

## Welcome to ONYX

ONYX combines multiple security scanners with artificial intelligence to provide comprehensive vulnerability assessment, intelligent risk prioritization, and actionable remediation guidance.

---

## Getting Started

### Login
Navigate to your ONYX URL and log in with your credentials. 
Default development URL: `http://localhost:5173`

### Dashboard
- Security overview with severity breakdown and trend indicators
- Recent scan results with quick access to reports
- Project statistics
- Scanner health status

---

## Running Scans

### Manual Scan
1. Click "New Scan" on the dashboard
2. Enter repository URL and branch
3. Select scan types (SAST, Secrets, SCA, IaC, DAST, Container)
4. Click "Start Scan" and monitor real-time progress via WebSocket

### Automated Scan via Webhook
Configure webhooks in your Git provider (GitHub/GitLab) to point to `POST /webhook/scan`. Scans trigger automatically on push.

### Scheduled Scans
Navigate to **Scheduled Scans** in the sidebar:
1. Click "Create Schedule"
2. Configure cron expression (or use presets: hourly, daily, weekly)
3. Select project, branch, and scan types
4. Set timezone
5. Enable the schedule

---

## Understanding Reports

Each scan generates a multi-tab report:

| Tab | Content |
|---|---|
| Overview | Security score, severity breakdown, key metrics |
| Findings | Filterable vulnerability list with code context |
| AI Analysis | GPT-4/Gemini executive summary, risk assessment, remediation |
| Compliance | 10 framework mapping with compliance rates |
| AI Chat | Natural-language Q&A about vulnerabilities |
| Compare | Side-by-side scan comparison |

### AI Chat Assistant
Ask questions about your scan results in natural language:
- "What's the most critical vulnerability?"
- "How do I fix the SQL injection in login.py?"
- "Which findings affect our PCI-DSS compliance?"

### Intelligent Triage
The triage dashboard ranks findings by a composite priority score (0-100) considering severity, exploitability, CVSS, business impact, trend, and age. Add business context to re-score.

---

## Secret History

Track secrets detected across scans over time:
- View secret history by project
- Filter by status (active, resolved, dismissed)
- Mark secrets as resolved or dismissed
- Trend chart shows discovery/resolution patterns

---

## Security Scanning

### Core Scanners (Built-in)
- **Semgrep** - Multi-language SAST
- **Bandit** - Python security analysis
- **Safety** - Python dependency vulnerabilities
- **GitLeaks** - Git-based secret detection
- **Detect-Secrets** - High-entropy secret detection
- **SOPS** - SOPS encryption configuration audit
- **Dependency Governance** - Malicious/deprecated package blocklist

### Optional Scanners (external tools required)
Trivy, ZAP, Nuclei, CodeQL, Checkov, Lynis

Enable via environment variables (`ENABLE_TRIVY=true`, etc.) when tools are installed.

---

## Compliance Frameworks (10)

OWASP, NIST, ISO 27001, PCI-DSS, HIPAA, SOC2, GDPR, CIS, SOX, MITRE ATT&CK

Each scan report shows where findings map to specific compliance controls.

---

## Auto-Fix PRs

For reports with AI analysis enabled:
1. Open a report
2. Click "Auto-Fix PR"
3. ONYX clones the repo, applies AI-generated patches, creates a branch, commits, and opens a PR
4. Review the PR and merge if appropriate

---

## Notifications

Configure in Settings:
- **Slack** - Real-time scan completion and critical vulnerability alerts
- **Teams** - Same as Slack via webhook
- **Email** - SMTP-based notifications
- **In-app** - WebSocket real-time notifications

---

## Navigation

| Page | Description |
|---|---|
| Dashboard | Overview and quick actions |
| Projects | Manage monitored repositories |
| Reports | All scan reports |
| Compliance | Cross-project compliance view |
| Scheduled Scans | Cron-based scan automation |
| Secret History | Cross-scan secret tracking |
| Admin | System-wide management (admin only) |
| Settings | User preferences and integrations |
