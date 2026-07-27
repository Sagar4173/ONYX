# Architecture & Design

## Overview

ONYX is designed as a modern, scalable security scanning platform. Architecture follows a modular monolith pattern with clear separation of concerns, running as a single FastAPI application with async workers.

---

## System Architecture

```
                    Frontend (React 18 + Vite)
                    Dark UI + Glassmorphism
                    Real-time WebSocket Updates
                            |
                    API Gateway (FastAPI)
                    JWT Auth, Rate Limiting, CORS
                    OpenAPI docs at /docs
                            |
              +-------------+-------------+
              |             |             |
       Scan Engine    AI Analysis    Notification
       Orchestrator   (Local/Ollama)  (Slack/Teams/
              |        GPT-4/Gemini   Email/WS)
              |        (fallback)        |
      +-------+-------+  |     +--------+--------+
      |       |       |  |     |        |        |
   Semgrep  Bandit  Safety |  Webhook  Scheduler SCM
   GitLeaks Trivy   ZAP   |  Handler  (cron)   (auto-fix)
   Lynis    SOPS    ...   |    |        |        |
      |       |       |   |    |        |        |
      +-------+-------+   +----+--------+--------+
              |                   |
         MongoDB 7+      Ollama (local LLM)
         (Beanie ODM)    Qwen2.5-Coder:7b
              |          (zero-cost inference)
        Monitoring
        Sentry + Prometheus
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS, React Query 5 |
| Backend | FastAPI, Python 3.13, Pydantic v2 |
| Database | MongoDB 7+, Beanie ODM |
| AI | Ollama (local, zero-cost), OpenAI GPT-4, Google Gemini 1.5 |
| Auth | JWT (PyJWT) |
| Monitoring | Sentry SDK, Prometheus (prometheus-fastapi-instrumentator) |
| Real-time | WebSocket (FastAPI native) |
| Container | Docker + Docker Compose |

---

## Backend Structure

```
backend/
├── app.py              # FastAPI app, lifespan, middleware, router includes
├── config.py           # pydantic-settings (all env vars documented)
├── database.py         # MongoDB + Beanie initialization
├── main.py             # Uvicorn runner
├── models/             # Beanie documents + Pydantic schemas
│   ├── report.py       # ScanReport, VulnerabilityFinding, ScanResult, ...
│   ├── user.py         # User, UserRole, ...
│   ├── project.py      # Project, ProjectMember, ...
│   ├── secret_history.py # SecretRecord, SecretTrendPoint
│   ├── schedule.py     # ScanSchedule
│   ├── triage.py       # TriageResult, BusinessContext
│   └── base.py         # Shared enums (ScannerType, SeverityLevel, ...)
├── routes/             # 30+ route modules organized by domain
│   ├── auth/           # login, register, refresh, password, api_tokens
│   ├── reports/        # listing, detail, analytics, export, ai_analysis
│   ├── security/       # combined, baselines, policies
│   ├── compliance/     # frameworks, reports, helpers
│   ├── admin/          # dashboard, users, projects, reports, activity
│   ├── advanced_security/ # scanning, rules, policies, baselines, metrics
│   ├── enterprise/     # audit_logs, compliance, sbom, trends, comparison
│   ├── webhook/        # processor, events, scan_operations
│   └── ...
├── services/           # Business logic
│   ├── ai/             # AI processors (OpenAI + Gemini)
│   ├── scanning/       # Orchestrator, 11 scanners, vulnerability manager
│   ├── compliance/     # Compliance analysis service
│   ├── notifications/  # Slack, Teams, Email, WebSocket
│   ├── infrastructure/ # EncryptionService, MonitoringService
│   ├── scheduling/     # ScanSchedulerService (cron)
│   ├── scm/            # AutoFixService (GitHub/GitLab PRs)
│   ├── auth/           # AuthService
│   ├── triage/         # TriageService
│   └── service_registry.py
├── tests/              # 347 tests
└── Dockerfile
```

### Route Prefix Convention

All routers define their prefix without `/api`:
```python
router = APIRouter(prefix="/security", tags=["Security"])
```

`app.py` adds `/api` consistently:
```python
app.include_router(security_router, prefix="/api")
```

---

## Frontend Structure

```
frontend/src/
├── App.jsx               # ErrorBoundary > QueryClient > AuthProvider > Router
├── main.jsx              # React entry point
├── components/
│   ├── auth/             # LoginForm, RegisterForm, AuthModal, AuthContext
│   ├── compliance/       # ComplianceDashboard, DataRetentionPolicies
│   ├── reports/          # ReportDetails, ReportList
│   ├── security/         # SBOMViewer, SecurityTrendsDashboard, SecretHistoryPanel
│   ├── schedules/        # ScheduledScansPage, ScheduleCard, ScheduleForm
│   ├── triage/           # TriageDashboard
│   ├── users/            # UserManagement, AuditLogs
│   ├── admin/            # AdminDashboard
│   └── ui/               # StyleComponents (shared)
├── layouts/
│   ├── MainLayout.jsx    # Authenticated layout with routes
│   ├── Sidebar.jsx       # Navigation
│   └── Header.jsx        # Top header
├── services/
│   └── api.js            # Axios client + all API modules
├── styles/
│   └── index.js          # Re-exports + theme
└── hooks/                # Custom hooks
```

---

## Security Scanner Architecture

### Scanner Types

| Type | Scanners |
|---|---|
| SAST | Semgrep, Bandit, CodeQL |
| DAST | ZAP, Nuclei |
| SECRETS | GitLeaks, Detect-Secrets, SOPS |
| SCA | Safety, Dependency Governance |
| IAC | Checkov |
| INFRASTRUCTURE | Lynis |
| CONTAINER | Trivy |

### Orchestrator Flow

```
ScanRequest
  -> ScanOrchestrator.run_scan()
     -> parallel scanner execution
     -> deduplication by (rule_id, file, line)
     -> ScanResult with findings
  -> EnhancedScanningWorkflow
     -> AI analysis (GPT-4 or Gemini)
     -> Compliance analysis
     -> Vulnerability management
     -> Secret history tracking
     -> Notifications (Slack/Teams/Email)
```

---

## Security

- JWT authentication (access + refresh tokens)
- Role-based access control (Admin > Security Manager > Developer > Viewer)
- Password hashing via bcrypt
- Rate limiting via slowapi
- NoSQL injection prevention via Beanie ODM
- Data encryption via EncryptionService (Fernet)
- Sentry error tracking (no PII)
- Prometheus metrics

---

## Scalability

- Stateless backend (horizontal scaling behind load balancer)
- Async/await throughout for I/O-bound operations
- Database indexes on common query patterns
- Graceful degradation for optional scanners
