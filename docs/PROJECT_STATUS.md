# ONYX Project Status

**Last Updated**: July 2026  
**Version**: 1.0.0  
**Status**: Production Ready

---

## Completed Features

### Authentication & Authorization
- JWT-based authentication (access + refresh tokens)
- User registration with email verification
- Password reset via email
- Role-based access control (Admin, Security Manager, Developer, Viewer)
- Session management
- Account lockout after failed attempts

### User Management
- User CRUD operations
- Profile management with avatar upload
- Role assignment
- User status management (Active, Inactive, Suspended)
- Audit logging for user actions

### Project Management
- Create/Edit/Delete projects
- Git repository integration (GitHub, GitLab, Bitbucket)
- Project categories and tags
- Project-level scan configuration
- Team collaboration (multi-user access)

### Security Scanning

**Core Scanners (Built-in):**
- Semgrep - Static Application Security Testing (SAST)
- Bandit - Python security analysis
- Safety - Python dependency vulnerabilities
- GitLeaks - Secret detection
- Detect-Secrets - High-entropy secret detection
- SOPS - SOPS encryption configuration auditing
- Dependency Governance - Malicious/deprecated package blocklist

**Optional Scanners (require external tooling):**
- Trivy - Container & dependency scanning
- ZAP - Dynamic Application Security Testing (OWASP ZAP)
- Nuclei - Vulnerability scanning
- CodeQL - Advanced SAST
- Checkov - Infrastructure as Code scanning
- Lynis - Infrastructure auditing

**Scanning Infrastructure:**
- Parallel scanner execution with graceful degradation
- Real-time scan progress via WebSocket
- Scan history and comparison
- Centralized Service Registry
- Suppression engine (inline + file-based)
- Deduplication across scanners

### AI-Powered Analysis
- OpenAI GPT-4 integration
- Google Gemini integration (primary)
- Vulnerability explanation and risk assessment
- Automated remediation suggestions
- Code fix generation
- False positive detection
- AI Chat Assistant - natural-language vulnerability Q&A
- Intelligent Triage - business-context priority scoring

### AI Chat Assistant (USP)
- Natural-language questions about vulnerabilities
- Scan-aware context injection
- Secure code examples inline

### Auto-Fix PRs (USP)
- AI generates fix patches
- Clones repo, applies patch, commits, pushes branch
- Creates Pull Request via GitHub/GitLab REST APIs
- Configurable branch/PR title prefix

### Intelligent Triage (USP)
- 6-factor weighted priority scoring (severity, exploitability, CVSS, business impact, trend, age)
- AI-generated triage summaries
- Interactive TriageDashboard with score breakdown bars
- Business context editor per scan

### Scheduled Scans
- Cron-based automatic scanning
- MongoDB-persisted schedules with AsyncIOScheduler
- 8 REST endpoints for CRUD + toggle + run-now
- Frontend ScheduleCard/ScheduleForm with cron presets + timezone

### Secret History Tracking
- Persistent secret tracking across scans (fingerprinted by hashed_secret + file_path)
- Auto-resolve secrets not found in latest scan
- Trend chart (active/resolved over time)
- Status management (active/resolved/dismissed)
- Frontend SecretHistoryPanel with filterable table

### Reporting & Analytics
- Unified multi-tab security reports
- PDF report generation with executive summary
- Compliance mapping (10 frameworks)
- Security score calculation
- Trend analysis dashboard
- Severity breakdown charts
- SBOM generation (SPDX, CycloneDX)

### Enterprise Features
- Admin Dashboard - system-wide monitoring
- User management with role/status controls from admin panel
- Project oversight across all users
- Activity monitoring and audit trail
- Admin-protected routes with access control
- Audit logging with integrity verification
- Data retention policies
- Data isolation per user/project
- Webhook integrations
- Email notifications (Gmail SMTP)
- Real-time WebSocket notifications
- Slack & Teams notification integration

### Advanced Security
- Custom rule engine
- Rule template library
- Baseline scanning with drift detection
- Policy-as-Code enforcement
- Security boundary protection

### Infrastructure
- Docker Compose (MongoDB + Backend + Frontend + nginx)
- Multi-stage Dockerfiles
- GitHub Actions CI (backend tests, frontend tests/build/lint, Docker build)
- Sentry error tracking
- Prometheus metrics via prometheus-fastapi-instrumentator
- Encryption service (Fernet AES-128-CBC+HMAC via PBKDF2)

### Compliance Frameworks (10)
OWASP, NIST, ISO 27001, PCI-DSS, HIPAA, SOC2, GDPR, CIS, SOX, MITRE ATT&CK

---

## Technical Stack

### Backend
| Component | Technology |
|---|---|
| Framework | FastAPI |
| Python | 3.13 |
| Database | MongoDB 7+ |
| ODM | Beanie |
| Auth | JWT (PyJWT) |
| AI | OpenAI GPT-4 / Google Gemini 1.5 |
| Monitoring | Sentry SDK / Prometheus |
| Notifications | Slack, Teams, Email, WebSocket |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18 |
| Build Tool | Vite 5 |
| Styling | Tailwind CSS 3 |
| State | React Query 5 |
| Router | React Router 6 |
| Testing | Vitest + Playwright (E2E) |

### Infrastructure
| Component | Technology |
|---|---|
| Hosting | AWS |
| Database | MongoDB Atlas |
| CI/CD | GitHub Actions |
| Containers | Docker + Docker Compose |

---

## Metrics

| Metric | Count |
|---|---|
| Backend Python files | 100+ |
| API Endpoints | 100+ routes |
| Frontend Components | 50+ |
| Security Scanners | 11 (7 core + 6 optional) |
| Compliance Frameworks | 10 |
| Backend Tests | 347 (all passing) |
| Frontend Tests | 172 (all passing) |
| Lines of Code | ~60,000+ |

---

## Feature Comparison

### vs GitHub Advanced Security (GHAS)
| Category | ONYX Advantage |
|---|---|
| Secret Scanning | GitLeaks + detect-secrets + SOPS (GHAS: basic patterns) |
| Code Scanning | Semgrep + Bandit + AI remediation (GHAS: CodeQL only) |
| Dependency Scan | Safety + Trivy + Dependency Governance + SBOM (GHAS: Dependabot only) |
| AI Analysis | Full GPT-4/Gemini integration (GHAS: none) |
| Platform Lock-in | Works with any Git provider (GHAS: GitHub only) |
| Pricing | Free & Open Source (GHAS: $49/user/month) |

### vs Snyk
| Category | ONYX Advantage |
|---|---|
| AI Remediation | Intelligent code fixes with context (Snyk: template-based) |
| Unified Dashboard | All tools in one view (Snyk: separate products) |
| Custom Rules | Full rule engine with templates (Snyk: limited) |
| Self-Hosting | Free (Snyk: Enterprise tier only) |
| Real-time Updates | WebSocket (Snyk: polling) |
| Pricing | Free (Snyk: $52/developer/month) |

---

## Project Structure

```
ONYX/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── models/            # Beanie documents (report, user, project, secret_history, ...)
│   ├── routes/            # 30+ route modules
│   ├── services/          # 15+ service modules
│   │   ├── ai/
│   │   ├── scanning/      # Orchestrator, engines, 11 scanners
│   │   ├── compliance/
│   │   ├── notifications/
│   │   ├── infrastructure/ # encryption_service, monitoring
│   │   ├── scheduling/    # ScanSchedulerService
│   │   ├── scm/           # Auto-fix PRs
│   │   └── ...
│   ├── tests/             # 347 tests
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # auth, compliance, reports, security, schedules, ...
│   │   ├── layouts/       # MainLayout, Sidebar, Header
│   │   ├── services/      # api.js with all API modules
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Quick Links

- [Installation Guide](INSTALLATION.md)
- [API Documentation](API.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
