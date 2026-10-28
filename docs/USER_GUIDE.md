# ONYX User Guide

ONYX combines multi-tool security scanning, AI-assisted analysis, and compliance
reporting in one self-hosted platform.

---

## Getting Started

### Sign in

Open the ONYX URL for your deployment and sign in with your email/username and
password. Accounts with 2FA enabled must provide the current authenticator code.
Google SSO may be available depending on deployment configuration.

### Dashboard

The dashboard summarizes:

- security score and severity distribution
- recent scans and findings
- project activity
- scanner availability
- trend indicators

### Main navigation

| Page | Purpose |
|---|---|
| Dashboard | Security overview and quick actions |
| Projects | Repositories, teams, and scan configuration |
| Reports | Completed scan reports and downloads |
| Compliance | Framework coverage, controls, risk, and trends |
| Analytics | Cross-project security metrics |
| Scheduled Scans | Recurring scan configuration and history |
| Secret History | Secrets detected across scans |
| Settings | Profile, notifications, sessions, and API tokens |
| Admin | Users, projects, reports, audit logs, retention, ML, webhook configuration |

Some pages are role-restricted. Admin-only pages are hidden or rejected when the
account lacks permission.

---

## Running Scans

### Manual scan

1. Open a project or use the scan action on the dashboard.
2. Enter or confirm the repository URL and branch.
3. Select the scan types.
4. Start the scan.
5. Watch progress in real time. Results appear in the report when complete.

Repository URLs must not contain embedded credentials. Use the configured SCM
access token instead. A scan can be stopped while it is running.

### Webhook-triggered scans

Configure the repository provider to send push or merge-request events to:

```text
https://your-domain.example/api/webhook/
```

Set a `WEBHOOK_SECRET` in the backend and configure the same secret in the SCM
webhook. ONYX accepts the shared-secret header or a GitHub-style HMAC-SHA256
signature. If no secret is configured, ingestion fails closed with HTTP 503.

See [Webhook Setup](webhook-github-actions.md) for a GitHub Actions example.
Manual scan API calls use `POST /api/webhook/scan` with a user access token.

### Scheduled scans

Open **Scheduled Scans**:

1. Create a schedule.
2. Choose a project, branch, scan types, cron expression, and timezone.
3. Enable the schedule.
4. Use run-now to test it and history to inspect previous executions.

Schedules are stored in MongoDB and run through the backend scheduler. The
current scheduler is process-local, so run one backend worker unless the
deployment has shared scheduling.

---

## Reports and Findings

A scan report includes:

| Section | Content |
|---|---|
| Overview | Security score, severity counts, scan metadata |
| Findings | Filterable vulnerabilities with file/line and code context |
| AI Analysis | Explanation, impact, and remediation guidance |
| Compliance | Framework/control mappings and coverage |
| Chat | Scan-aware Q&A with citations |
| Compare | Changes between scans or branches |

Reports can be exported as PDF. SBOM exports are available in SPDX and
CycloneDX formats from the enterprise security views.

### Finding workflow

- Review severity, confidence, and code context.
- Add labels or suppressions when appropriate.
- Mark false positives with supporting context.
- Use triage scoring to prioritize business impact.
- Generate a fix preview when AI-assisted remediation is enabled.
- Approve an auto-fix before any branch or pull request is created.

Auto-fix is not autonomous. Review generated code and the resulting PR/MR before
merging.

### Secret history

Secret History tracks detected secrets across scans:

- filter by project, status, and time
- view active, resolved, and dismissed secrets
- mark items resolved or dismissed
- review discovery/resolution trends

Rotate any exposed credential even after the finding is marked resolved.

---

## AI Assistant and Triage

### AI Chat

Ask scan-aware questions such as:

- "What is the highest-risk issue in this scan?"
- "How do I fix the SQL injection in login.py?"
- "Which findings affect PCI-DSS access-control controls?"
- "Show the evidence for this finding."

Answers may include citations from the local knowledge corpus. AI output can be
wrong or incomplete; verify it against the code and the finding evidence.

### Intelligent Triage

Triage combines severity, exploitability, CVSS, business context, trend, and age
into a priority score. Add business context to improve prioritization. The score
is decision support, not a replacement for security judgment.

### AI provider behavior

When `AI_PROVIDER=auto`, ONYX tries configured providers in the order:

```text
Gemini -> Groq -> OpenRouter -> Ollama
```

Unconfigured providers are skipped. OpenAI remains available when explicitly
configured or included in the chain. If all providers fail, AI features may be
unavailable while scanning and reporting continue.

---

## Scanners

### Core integrations

Semgrep, Bandit, Safety, GitLeaks, Detect-Secrets, SOPS, and Dependency
Governance.

### Optional integrations

Trivy, OWASP ZAP, Nuclei, CodeQL, Checkov, and Lynis. These require their
binaries or services to be installed and may require environment flags:

```env
ENABLE_TRIVY=true
ENABLE_ZAP=true
ENABLE_NUCLEI=true
ENABLE_CODEQL=true
ENABLE_CHECKOV=true
ENABLE_LYNIS=true
```

Missing optional tools produce a degraded scan, not a failed application.
Scanner health is available from the dashboard or
`GET /api/scanners/health`. That endpoint checks Semgrep, Trivy, GitLeaks,
Bandit, and Safety; other integrations may still be available.

---

## Compliance

ONYX maps findings to compliance frameworks and identifiers, including commonly
used standards and custom framework IDs. Views include:

- framework coverage and control status
- risk summaries and trends
- project assessments
- compliance reports

Compliance features help organize evidence and remediation work. They do not
constitute certification or legal advice.

---

## Notifications

Configure supported integrations in Settings or deployment configuration:

- in-app WebSocket notifications
- Slack
- Microsoft Teams
- SMTP email

Notification failures do not block a completed scan, but repeated delivery
failures should be investigated in the backend logs.

---

## Account and API Access

### Sessions

View and revoke active sessions, or sign out of all sessions. Revoke unknown
sessions immediately and change the password.

### API tokens

Create API tokens for automation. The token value is shown only once.
Use it as a bearer token:

```http
Authorization: Bearer <token>
```

Set an expiration when creating a token and revoke unused tokens. Scopes and IP
allowlists can be recorded, but they are not yet enforced; treat every token as
having full access to your account.

### Notifications and profile

Update display name, avatar, organization, department, and notification
preferences in Settings. Changing email or password requires the current
credentials.

---

## Troubleshooting

| Problem | Check |
|---|---|
| Cannot sign in | Credentials, account status, lockout, 2FA code, SSO configuration |
| Scan will not start | Repository URL, branch, SCM access, project access |
| Scan finds fewer results | Scanner binaries, optional scanner flags, scanner health |
| AI features unavailable | Provider keys, provider chain, Ollama availability |
| No webhook scans | URL `/api/webhook/`, secret/signature, SCM delivery logs |
| Schedule does not run | Backend scheduler, timezone, project access, backend worker count |
| Report missing | Scan status, backend logs, MongoDB connectivity |
| Charts or live updates stale | WebSocket connection and reverse-proxy upgrade headers |

For deployment failures, see [Deployment](DEPLOYMENT.md). For a suspected
vulnerability, follow [SECURITY.md](../SECURITY.md).
