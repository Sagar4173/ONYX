# Architecture & Design

## Overview

ONYX is a modular monolith: one FastAPI application with domain route packages,
service modules, a React SPA, MongoDB, and one or more AI providers. The default
deployment runs the frontend behind nginx, the backend as a systemd service or
container, and MongoDB on a private interface.

The backend is asynchronous but is not fully stateless. The WebSocket
connection manager, scan cancellation state, in-process scheduler, and default
rate limiter all keep process-local state. Horizontal scaling requires shared
coordination and sticky WebSocket routing.

---

## System Architecture

```text
                       Browser (React 18 + Vite)
                       SPA routes, Axios API client
                       WebSocket /ws?token=...
                                  |
                       nginx (TLS, static SPA)
                       /api /ws /health /docs /redoc
                                  |
                       FastAPI application
                       JWT/API-token auth, CORS, rate limits
                       OpenAPI at /docs, /redoc, and /openapi.json
                                  |
        +-----------------+-------+-------+------------------+
        |                 |               |                  |
   Scan engine       AI services      Reporting          Enterprise
   orchestrator      providers, RAG,  compliance,         audit, RBAC,
   13 scanner        agents, ML       SBOM, PDF           retention
   integrations           |               |                  |
        |                 |               |                  |
        +-----------------+-------+-------+------------------+
                                  |
                             MongoDB 7+
                             Beanie models

   Optional: Ollama, cloud AI APIs, Slack/Teams/SMTP, SCM APIs,
             Sentry, Prometheus
```

---

## Technology

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS, TanStack Query, React Router |
| Backend | FastAPI, Python 3.13, Pydantic v2, Beanie |
| Database | MongoDB 7+ |
| Authentication | JWT (PyJWT), bcrypt, TOTP, Google ID tokens |
| AI | Gemini, Groq, OpenRouter, OpenAI, Ollama |
| AI retrieval | SQLite corpus with sqlite-vec vectors and FTS5 |
| Real-time | Native FastAPI WebSocket |
| Monitoring | Sentry, Prometheus |
| Deployment | Jenkins/EC2/nginx/systemd; Docker Compose alternative |

---

## Backend Structure

```text
backend/
├── app.py                  # App composition, lifespan, middleware, WebSocket
├── config.py               # Pydantic settings and provider selection
├── database.py             # MongoDB and Beanie initialization
├── main.py                 # Development Uvicorn runner
├── models/                 # Beanie documents and Pydantic schemas
│   ├── base.py             # Shared enums
│   ├── project.py
│   ├── report.py
│   ├── schedule.py
│   ├── secret_history.py
│   ├── triage.py
│   └── user.py
├── routes/
│   ├── auth/               # Login, sessions, 2FA, SSO, API tokens
│   ├── users/              # Profiles, admin user management, security views
│   ├── projects/           # Projects, templates, team membership
│   ├── reports/            # Reports, analytics, downloads, AI analysis
│   ├── webhook/            # Ingest, scan operations, processor
│   ├── admin/              # Dashboard, users, reports, webhook config
│   ├── security/           # Policies, rules, baselines, drift
│   ├── advanced_security/  # Threat intel, pentest, metrics, boundaries
│   ├── advanced_scanning/  # SAST/DAST/IaC/comprehensive workflows
│   ├── compliance/
│   ├── enterprise/         # Audit, compliance, retention
│   ├── enterprise_security/# SBOM, trends, comparisons, CVE enrichment
│   └── root modules        # AI, ML, schedules, triage, analytics, stats
├── services/
│   ├── ai/                 # Providers, gateway, RAG, agents, ML, enrichment
│   ├── scanning/           # Orchestrator, scanner implementations, findings
│   ├── compliance/
│   ├── notifications/
│   ├── infrastructure/     # Encryption and monitoring
│   ├── scheduling/
│   ├── scm/
│   ├── auth/
│   ├── analytics/
│   ├── rules/
│   ├── security/
│   └── triage/
├── knowledge/              # RAG corpus and ingestion instructions
├── data/                   # SQLite knowledge DB and runtime artifacts
├── tests/                  # Pytest suite (940 verified tests)
└── Dockerfile
```

All application routers are mounted with the `/api` prefix in `app.py`; health,
WebSocket, OpenAPI, and metrics live outside that prefix.

---

## Frontend Structure

```text
frontend/src/
├── App.jsx                 # Error boundary, QueryClient, AuthProvider, Router
├── components/
│   ├── auth/
│   ├── admin/
│   ├── compliance/
│   ├── reports/
│   ├── schedules/
│   ├── security/
│   ├── triage/
│   ├── users/
│   └── ui/
├── layouts/
│   ├── MainLayout.jsx
│   ├── Sidebar.jsx
│   └── Header.jsx
├── pages/
├── services/api.js         # Axios client and domain API methods
├── styles/
└── hooks/
```

The development server connects directly to `http://127.0.0.1:8000/api`.
Production builds use `VITE_API_URL` or default to same-origin `/api`. The nginx
container proxies API, WebSocket, health, and documentation paths so the SPA
and API share an origin.

Frontend application routes include login and registration, dashboard,
projects and project detail, reports and finding detail, compliance, analytics,
scheduled scans, secret history, settings, user administration, audit logs,
retention policies, general admin, and ML administration. Authenticated unknown
routes render the 404 page; unauthenticated unknown routes redirect to the
landing page.

---

## Scan Flow

```text
Manual scan request or SCM webhook
  -> validate repository URL and authentication
  -> create ScanReport / WebhookEvent in MongoDB
  -> dispatch background scan work
  -> scanner orchestrator runs available scanners in parallel
  -> normalize findings and deduplicate
  -> persist findings and update progress
  -> post-scan AI enrichment and triage
  -> compliance and secret-history updates
  -> WebSocket and notification delivery
  -> report/trend/SBOM queries
```

Scanner availability is checked at runtime. Missing optional binaries degrade
the scan instead of crashing the application. Current integrations:

| Category | Integrations |
|---|---|
| SAST | Semgrep, Bandit, CodeQL |
| DAST | OWASP ZAP, Nuclei |
| Secrets | GitLeaks, Detect-Secrets, SOPS |
| SCA | Safety, Dependency Governance |
| IaC | Checkov |
| Infrastructure | Lynis |
| Container | Trivy |

---

## AI Architecture

`AI_PROVIDER=auto` walks `AI_PROVIDER_CHAIN` in order. The default is
`gemini,groq,openrouter,ollama`; providers without usable credentials are
skipped. OpenAI remains available as an explicit/legacy provider.

AI capabilities are split into:

- provider adapters and a failover gateway
- prompt-injection screening
- RAG retrieval over a local CWE/knowledge corpus
- vulnerability explanation, remediation, and chat with citations
- investigation and triage agents
- auto-fix generation behind explicit approval gates
- optional IsolationForest anomaly detection

Model output is untrusted. Structured outputs are validated before use, and
auto-fix actions require approval before code changes or SCM submissions.

---

## Data and Persistence

MongoDB stores users, sessions, projects, reports, findings, schedules, audit
records, webhook events, compliance data, and settings. Beanie provides schema
models and indexes.

The knowledge corpus is stored in `backend/data/knowledge.db` (SQLite with
vectors and FTS5). Other runtime files include scan/knowledge metrics and policy
state under `backend/data/`.

Docker Compose persists MongoDB data and `/app/data`. Optional ML databases and
model artifacts are not included in the default Compose volumes; add a dedicated
volume before relying on trained models across container recreation.

Redis configuration exists but current features do not require Redis. There is
no S3/object-storage integration in the current codebase.

---

## Authentication and Authorization

- JWT access and refresh tokens; refresh rotates the session response.
- API tokens are SHA-256 hashed at rest. Expiration is enforced; scopes are
  validated at creation and IP allowlists are stored, but route-level scope/IP
  enforcement is not yet implemented.
- Roles: Admin, Security Manager, Developer, Viewer.
- Route dependencies enforce authentication; administrative routes require
  admin access; project/report access checks ownership or team membership.
- TOTP 2FA, Google SSO, lockout, session listing, and session revocation are
  implemented.
- WebSocket connections require a token.

---

## Security Boundaries

- In the Compose deployment, frontend nginx proxies public traffic to the
  internal backend. The included server block listens on HTTP only; terminate
  TLS with an upstream proxy or an additional nginx server block. The backend is
  not published directly.
- MongoDB and Ollama should remain on a private network with authentication.
- Webhook ingestion authenticates with a shared secret or HMAC and fails closed
  when `WEBHOOK_SECRET` is absent.
- Sensitive fields are encrypted with Fernet; `SECRET_KEY` signs JWTs and
  derives that encryption key, so rotation requires a data migration.
- URLs are redacted before storage/exposure, but operators should rotate any
  credential that may have been stored by older versions.
- Audit hashes provide tamper evidence, not tamper-proof storage.

See [SECURITY.md](../SECURITY.md) for the deployment checklist and limitations.

---

## Scalability and Operational Constraints

- Async I/O supports concurrent scans and API requests, but scan execution,
  cancellation state, the scheduler, the WebSocket registry, and the default
  rate limiter are process-local.
- Running multiple backend workers can duplicate scheduled work and split
  WebSocket clients. Use a single worker for the current scheduler, or add a
  shared scheduler/queue before horizontal scaling.
- MongoDB indexes support common report, project, and user queries.
- Scans are resource-intensive. Container and host memory should be sized for
  the selected scanners and AI model.
- External scanners and AI providers are optional dependencies; degraded mode
  must remain usable.
- Jenkins automatically rolls back code and frontend assets after a failed
  deployment. It does not restore MongoDB data, so keep database and
  environment backups before upgrades.

---

## Deployment View

The current production path is Jenkins on an EC2 host, a systemd-managed
backend, nginx serving the frontend build, MongoDB, and optionally Ollama.
`docker-compose.yml` is the self-hosted alternative: frontend nginx on port 80,
backend and MongoDB internal-only, and an optional Ollama service.

See [DEPLOYMENT.md](DEPLOYMENT.md) for both paths.
