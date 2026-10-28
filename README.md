# ONYX - Security Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open-source, self-hosted security scanning and intelligence. ONYX combines
multi-tool scanning, AI-assisted triage and remediation, compliance reporting,
and enterprise controls in one platform.

---

## What ONYX Provides

### Security scanning

ONYX orchestrates 13 scanner integrations:

- **Core:** Semgrep, Bandit, Safety, GitLeaks, Detect-Secrets, SOPS, Dependency
  Governance
- **Optional:** Trivy, OWASP ZAP, Nuclei, CodeQL, Checkov, Lynis

Bandit, Safety, and Detect-Secrets ship with the backend requirements.
Semgrep is installed on demand. External binaries such as GitLeaks, SOPS, Trivy,
ZAP, Nuclei, CodeQL, Checkov, and Lynis must be installed separately and be on
`PATH`. `GET /api/scanners/health` reports the availability of Semgrep, Trivy,
GitLeaks, Bandit, and Safety.

### AI analysis

- Vulnerability explanations, severity/risk assessment, and remediation guidance
- Retrieval-augmented chat with citations from the local knowledge corpus
- Prompt-injection screening before AI analysis
- Investigation and triage workflows
- Approval-gated auto-fix generation and pull/merge request creation
- Optional IsolationForest anomaly detection for unusual scan results

`AI_PROVIDER=auto` follows `AI_PROVIDER_CHAIN` from left to right. The default
chain is **Gemini → Groq → OpenRouter → Ollama**, with OpenAI available as a
legacy provider. Ollama is the final fallback and is used when it is reachable;
it is not required in production.

### Automation and reporting

- Scheduled scans with run history
- GitHub, GitLab, and Bitbucket push/merge-request webhooks
- Real-time WebSocket notifications plus Slack, Teams, and email integrations
- SBOM generation in SPDX and CycloneDX formats
- PDF reports, scan trends, branch comparisons, and remediation tracking
- Compliance mappings, control status, risk summaries, and trends across major
  frameworks plus custom identifiers
- Secret-history tracking across scans

### Enterprise controls

- Role-based access control: Admin, Security Manager, Developer, Viewer
- JWT access/refresh tokens, session management, API tokens, and TOTP 2FA
- Google SSO with an optional email-domain allowlist
- Audit logging with integrity verification
- Retention policies and configurable data cleanup
- Sentry error tracking and Prometheus metrics
- Admin dashboard and user/project administration

---

## Technology

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS, TanStack Query |
| Backend | FastAPI, Python 3.13, Pydantic |
| Database | MongoDB 7+ with Beanie |
| AI | Google Gemini, Groq, OpenRouter, OpenAI, Ollama |
| Monitoring | Sentry, Prometheus |
| Deployment | Jenkins on EC2 with nginx; Docker Compose alternative |

MongoDB is required. Redis is present in configuration but is not required for
current functionality. Optional ML state is stored on local disk and is not
persisted by the default Compose volumes.

---

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 22+
- MongoDB 7+ (local, Atlas, or Docker)
- Git

### Backend

```powershell
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set at least `SECRET_KEY` and `MONGODB_URI` in `backend/.env`. Generate a key
with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the API:

```powershell
python main.py
```

### Frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

In development, the frontend connects directly to
`http://127.0.0.1:8000/api`; `VITE_API_URL` is used by production builds. Create
`frontend/.env` from `.env.example` only when a production build needs a
non-default API or WebSocket URL.

- Frontend: http://localhost:5173
- API: http://localhost:8000
- OpenAPI UI: http://localhost:8000/docs

Detailed setup: [Installation Guide](docs/INSTALLATION.md).

---

## Docker Compose

```powershell
Copy-Item backend\.env.example backend\.env
# Edit backend/.env: SECRET_KEY, FRONTEND_URL, and optional AI keys
docker compose up -d
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

The frontend is published on port 80. The backend, MongoDB, and Ollama are only
reachable on the Compose network; nginx proxies same-origin `/api`, `/ws`,
`/health`, `/docs`, and `/openapi.json` requests. If `AI_PROVIDER=auto` and no
cloud AI key is configured, pull the Ollama model before relying on local AI.

For HTTPS and production settings, see [Deployment](docs/DEPLOYMENT.md).

---

## Google SSO

Create an OAuth 2.0 **Web application** client ID in the
[Google Cloud Console](https://console.cloud.google.com/apis/credentials), then
configure the backend:

```env
GOOGLE_CLIENT_ID=1234567890-abc.apps.googleusercontent.com
GOOGLE_ALLOWED_DOMAINS=yourcompany.com
```

Setting `GOOGLE_CLIENT_ID` enables the **Sign in with Google** button. SSO users
are auto-provisioned as Viewers when registration is enabled and still pass
through 2FA, suspension, and email-verification checks.

---

## Testing

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
cmd /c "npm test -- --reporter=dot"
cmd /c "npm run lint"
cmd /c "npm run build"
```

Current verified counts: **938 backend tests** and **413 frontend tests**.

---

## Project Structure

```text
ONYX/
├── backend/
│   ├── app.py                 # FastAPI entry point and router composition
│   ├── config.py              # Pydantic settings
│   ├── database.py            # MongoDB and Beanie initialization
│   ├── models/                # Documents and request/response schemas
│   ├── routes/                # API route packages
│   ├── services/
│   │   ├── ai/                # Providers, RAG, agents, ML, enrichment
│   │   ├── scanning/          # Scanner orchestration and implementations
│   │   ├── compliance/        # Compliance mappings and reporting
│   │   ├── notifications/     # WebSocket, Slack, Teams, email
│   │   ├── auth/              # JWT, sessions, 2FA
│   │   ├── scheduling/        # Scheduled scans
│   │   ├── scm/               # Git operations and auto-fix PRs
│   │   └── infrastructure/    # Encryption and monitoring
│   ├── knowledge/             # RAG corpus sources and ingestion notes
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── e2e/
│   ├── Dockerfile
│   └── nginx.conf
├── Jenkinsfile                # Current EC2 deployment pipeline
├── docker-compose.yml         # Self-hosted alternative
├── .github/workflows/ci.yml
└── docs/
```

---

## Documentation

| Document | Description |
|---|---|
| [Installation](docs/INSTALLATION.md) | Local development and Docker setup |
| [API Reference](docs/API.md) | Authentication, conventions, and route inventory |
| [Architecture](docs/ARCHITECTURE.md) | Components, data flow, and design |
| [Deployment](docs/DEPLOYMENT.md) | Jenkins/EC2 and Docker production paths |
| [User Guide](docs/USER_GUIDE.md) | End-user workflows and features |
| [Security](SECURITY.md) | Security model and deployment checklist |
| [Contributing](docs/CONTRIBUTING.md) | Development workflow and verification |
| [Team Guide](docs/TEAM_GUIDE.md) | Ownership, runtime context, and operations |
| [Roadmap](docs/ROADMAP.md) | Current priorities and known issues |
| [Project Status](docs/PROJECT_STATUS.md) | Implemented capabilities and known gaps |

---

## Team

| Role | Name | GitHub |
|---|---|---|
| Lead Developer | Sagar Wavhal | [@Sagar4173](https://github.com/Sagar4173) |
| Security Expert | Piyush More | [@MorePiyush55](https://github.com/MorePiyush55) |
| DevOps Engineer | Rushikesh Phalke | [@rushiphalke247](https://github.com/rushiphalke247) |

---

## Security

Report vulnerabilities privately through
[GitHub Security Advisories](https://github.com/Sagar4173/ONYX/security/advisories/new).
Do not open a public issue for an undisclosed vulnerability.

---

## License

MIT License
