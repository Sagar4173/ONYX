# ONYX Team Guide

**Last Updated**: July 2026  
**Mission**: Build a better platform than GitHub Advanced Security (GHAS) & Snyk

---

## Why We're Building This

| Issue | GHAS | Snyk | ONYX |
|---|---|---|---|
| Cost | $49/user/month | $52/user/month | Free |
| AI Analysis | None | Basic | GPT-4 + Gemini |
| Platform Lock-in | GitHub only | Fragmented | Any SCM |
| Custom Rules | Limited | Limited | Full rule engine |
| Self-Hosting | Impossible | Enterprise $$$ | Free |
| Real-time Updates | Polling | Polling | WebSocket |

---

## Team Members

### Sagar Wavhal - Lead Developer
**GitHub**: [@Sagar4173](https://github.com/Sagar4173)

**Responsibilities:**
- Platform architecture
- Backend API (FastAPI)
- Frontend (React)
- AI integration (OpenAI/Gemini)
- Database design (MongoDB)

**Key features delivered:**
- AI Chat Assistant
- Auto-Fix PRs
- Intelligent Triage
- Secret History
- Sentry + Prometheus monitoring
- Docker + CI infrastructure
- Route standardization & codebase cleanup

**Key files:**
```
backend/app.py, config.py
backend/services/ai/
backend/routes/
frontend/src/App.jsx
frontend/src/services/api.js
```

### Piyush More - Security Expert
**GitHub**: [@MorePiyush55](https://github.com/MorePiyush55)

**Responsibilities:**
- Security scanner integration
- Vulnerability assessment rules
- Compliance framework mapping
- Security testing
- Threat analysis

**Key features delivered:**
- 10 compliance frameworks (OWASP, NIST, ISO 27001, PCI-DSS, HIPAA, SOC2, GDPR, CIS, SOX, MITRE)
- ZAP DAST scanner integration
- Lynis infrastructure scanner
- Detect-Secrets scanner
- MITRE ATT&CK compliance
- Threat intelligence engine (NVD, OSV, GitHub Advisory)

**Key files:**
```
backend/services/scanning/
backend/services/compliance/
backend/services/security/
backend/services/rules/
```

### Rushikesh Phalke - DevOps Engineer
**GitHub**: [@rushiphalke247](https://github.com/rushiphalke247)

**Responsibilities:**
- Deployment automation
- Infrastructure management
- CI/CD pipelines
- Performance monitoring
- Server administration

**Key features delivered:**
- Docker Compose (MongoDB + Backend + Frontend)
- Multi-stage Dockerfiles
- GitHub Actions CI (3 jobs)
- nginx reverse proxy config
- AWS deployment
- .env.example documentation

**Key files:**
```
backend/Dockerfile
frontend/Dockerfile, nginx.conf
docker-compose.yml
.github/workflows/ci.yml
.env.example
```

---

## Development Setup

```bash
# Prerequisites: Python 3.13+, Node.js 22+, MongoDB 7+

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

---

## Codebase Structure

### Backend
```
backend/
├── app.py                 # FastAPI entry, lifespan, router includes
├── config.py              # pydantic-settings (all env vars)
├── database.py            # MongoDB + Beanie init
├── main.py                # Uvicorn runner
├── models/                # Beanie documents + Pydantic schemas
├── routes/                # 30+ route modules (auth, reports, scanning, triage, ...)
├── services/              # 15+ service modules
│   ├── ai/                # AI processors
│   ├── scanning/          # Orchestrator, 11 scanners
│   ├── compliance/        # Compliance analyzer
│   ├── notifications/     # Slack, Teams, Email, WebSocket
│   ├── infrastructure/    # Encryption, Monitoring
│   ├── scheduling/        # Cron scheduler
│   └── scm/               # Git + auto-fix
├── tests/                 # 347 tests
└── Dockerfile
```

### Frontend
```
frontend/src/
├── components/            # auth, compliance, reports, security, schedules, triage, ...
├── layouts/               # MainLayout, Sidebar, Header
├── services/              # api.js (all API modules)
├── styles/                # Tailwind theme
├── App.jsx                # Routes + providers
└── main.jsx               # Entry point
```

---

## Testing

```bash
# Backend
cd backend
pytest tests/ -q    # 347 tests

# Frontend
cd frontend
npm test             # 172 tests
npm run build        # Production build
```

---

## Git Workflow

| Branch | Purpose |
|---|---|
| `main` | Production |
| `feature/*` | New features |
| `fix/*` | Bug fixes |

Commit convention: `type(scope): description`

---

## Competitive Position

### Features GHAS Doesn't Have
- AI Analysis (GPT-4/Gemini)
- Multi-SCM support
- Custom rule engine
- Real-time WebSocket
- Self-hosted
- Free & open source

### Features Snyk Doesn't Have
- GPT-4 + Gemini AI
- Unified dashboard
- Free self-hosting
- WebSocket real-time
- Full custom rules

### What We've Built That Competitors Don't Have
- AI Chat Assistant
- Auto-Fix PRs
- Intelligent Triage by business impact
- Secret history tracking
- SOPS encryption auditing
- Dependency governance blocklist
