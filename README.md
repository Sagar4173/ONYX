# ONYX - Security Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Open Source Alternative to GitHub Advanced Security & Snyk.  
AI-Powered Security Scanning Free & Self-Hosted Enterprise-Ready.

---

## Why ONYX Over GHAS & Snyk

| Feature | ONYX | GHAS | Snyk |
|---|---|---|---|
| AI Analysis | Ollama (local) + GPT-4 + Gemini | None | Basic |
| Cost | Free & Open Source | $49/user/mo | $52/user/mo |
| Self-Hosted | Full control | SaaS only | Enterprise only |
| Multi-SCM | GitHub, GitLab, Bitbucket | GitHub only | Yes |
| Real-time Updates | WebSocket | Polling | Polling |
| Custom Rules | Full engine | Limited | Limited |
| Compliance Frameworks | 10 | 3-4 | 5-6 |

---

## Key Features

### Security Scanning

**Core Scanners (Built-in):**
- Semgrep, Bandit, Safety, GitLeaks, Detect-Secrets, SOPS, Dependency Governance

**Optional Scanners (require external tooling):**
- Trivy (container), ZAP (DAST), Nuclei, CodeQL, Checkov (IaC), Lynis (infrastructure)

### AI-Powered
- Vulnerability explanation & risk assessment
- Automated remediation & code fix generation
- False positive detection
- AI Chat Assistant for natural-language vulnerability questions
- Intelligent Triage with business-context prioritization

### Automation
- Auto-Fix PRs (AI generates and submits fix PRs via GitHub/GitLab REST APIs)
- Scheduled Scans (cron-based automatic scanning)
- Real-time WebSocket notifications (Slack, Teams, Email)

### Reporting & Compliance
- Unified scan reports with 6 tabs
- PDF export with executive summary
- 10 compliance frameworks: OWASP, NIST, ISO 27001, PCI-DSS, HIPAA, SOC2, GDPR, CIS, SOX, MITRE ATT&CK
- SBOM generation (SPDX, CycloneDX)
- Secret history tracking across scans

### Enterprise
- Role-based access control (Admin, Security Manager, Developer, Viewer)
- Admin dashboard with system-wide monitoring
- Audit logging with integrity verification
- Data retention policies
- Webhook integrations
- Sentry error tracking + Prometheus metrics

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS |
| Backend | FastAPI, Python 3.13 |
| Database | MongoDB 7+ (via Beanie ODM) |
| AI | Ollama (local), OpenAI GPT-4, Google Gemini |
| Monitoring | Sentry, Prometheus |
| Infra | Docker, GitHub Actions CI |

---

## Quick Start

```bash
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX

# Backend
cd backend
cp .env.example .env
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

**Frontend:** http://localhost:5173  
**API Docs:** http://localhost:8000/docs

For detailed setup, see [Installation Guide](docs/INSTALLATION.md).  
For Docker deployment, see [Deployment Guide](docs/DEPLOYMENT.md).  

> **Zero-cost AI**: Set `AI_PROVIDER=auto` and run Ollama alongside ONYX. All AI features run locally with no API fees.

---

## Project Structure

```
ONYX/
├── backend/
│   ├── app.py               # FastAPI entry point
│   ├── config.py             # Settings via pydantic-settings
│   ├── database.py           # MongoDB + Beanie init
│   ├── models/               # Beanie documents + Pydantic schemas
│   ├── routes/               # API endpoints (auth, reports, scanning, admin, ...)
│   ├── services/             # Business logic
│   │   ├── ai/               # AI processors (Ollama + OpenAI + Gemini)
│   │   ├── scanning/         # Scanner orchestrator + all scanners
│   │   ├── compliance/       # Compliance engine
│   │   ├── notifications/    # Slack, Teams, Email, WebSocket
│   │   ├── auth/             # JWT authentication
│   │   ├── scheduling/       # Cron-based scan scheduler
│   │   ├── scm/              # Git operations + auto-fix PRs
│   │   └── infrastructure/   # Encryption, Monitoring
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── layouts/          # MainLayout, Sidebar, Header
│   │   ├── services/         # API client (axios)
│   │   └── styles/           # Tailwind theme
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .github/workflows/ci.yml
└── docs/
```

---

## Team

| Role | Name | GitHub |
|---|---|---|
| Lead Developer | Sagar Wavhal | [@Sagar4173](https://github.com/Sagar4173) |
| Security Expert | Piyush More | [@MorePiyush55](https://github.com/MorePiyush55) |
| DevOps Engineer | Rushikesh Phalke | [@rushiphalke247](https://github.com/rushiphalke247) |

---

## Documentation

| Document | Description |
|---|---|
| [Installation](docs/INSTALLATION.md) | Local & Docker setup |
| [API Reference](docs/API.md) | Full API documentation |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Deployment](docs/DEPLOYMENT.md) | Production deployment |
| [Contributing](docs/CONTRIBUTING.md) | Contribution guide |
| [Project Status](docs/PROJECT_STATUS.md) | Feature completeness |

---

## License

MIT License
