# ONYX Team Guide

- **Updated:** 2026-10-28
- **Purpose:** Shared operating context for developers, security engineers, and
  deployment owners.

---

## Team Ownership

### Sagar Wavhal - Lead Developer

GitHub: [@Sagar4173](https://github.com/Sagar4173)

Primary ownership:

- backend architecture and API composition
- frontend application and integration
- AI providers, retrieval, agents, and triage
- MongoDB models and service boundaries
- security-sensitive application changes

Key files: `backend/app.py`, `backend/config.py`, `backend/routes/`,
`backend/services/ai/`, `frontend/src/App.jsx`, `frontend/src/services/api.js`.

### Piyush More - Security Expert

GitHub: [@MorePiyush55](https://github.com/MorePiyush55)

Primary ownership:

- scanner integrations and finding normalization
- compliance mappings and reporting
- security rules, baselines, and drift analysis
- threat intelligence and vulnerability assessment
- security review of scanner and AI workflows

Key files: `backend/services/scanning/`, `backend/services/compliance/`,
`backend/services/security/`, `backend/services/rules/`.

### Rushikesh Phalke - DevOps Engineer

GitHub: [@rushiphalke247](https://github.com/rushiphalke247)

Primary ownership:

- Jenkins/EC2 deployment and rollback procedures
- Docker images, Compose, and nginx
- GitHub Actions CI
- host capacity, logs, backups, and monitoring
- environment configuration and secret handling

Key files: `Jenkinsfile`, `docker-compose.yml`, `backend/Dockerfile`,
`frontend/Dockerfile`, `frontend/nginx.conf`, `.github/workflows/ci.yml`.

---

## Current Runtime Shape

- Frontend: React 18 SPA built with Vite, served by nginx.
- Backend: FastAPI on Python 3.13, run by systemd on EC2 or by Uvicorn in
  Compose.
- Database: MongoDB 7+; required.
- AI: Gemini → Groq → OpenRouter → Ollama by default when `AI_PROVIDER=auto`.
  OpenAI is legacy/explicit.
- Scanning: 13 integrations; external binaries are optional and degrade
  gracefully when absent.
- Current deployment: Jenkins + EC2 + systemd + nginx, optionally Ollama.
- Alternative deployment: Docker Compose with internal backend/MongoDB and
  frontend nginx.

---

## Local Setup

```powershell
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

In another terminal:

```powershell
cd ONYX\frontend
npm install
npm run dev
```

URLs: frontend `http://localhost:5173`, API `http://localhost:8000`, OpenAPI
`http://localhost:8000/docs`.

Set `SECRET_KEY` and `MONGODB_URI` before starting. Do not use the example
secret outside local development.

---

## Repository Map

```text
backend/
├── app.py                 # middleware, router composition, WebSocket
├── config.py              # settings and AI provider chain
├── database.py            # Beanie initialization
├── models/                # documents and schemas
├── routes/                # domain route packages
├── services/              # business logic
│   ├── ai/                # providers, RAG, agents, ML, enrichment
│   ├── scanning/          # orchestrator and scanner implementations
│   ├── compliance/
│   ├── notifications/
│   ├── infrastructure/    # encryption and monitoring
│   ├── scheduling/
│   ├── scm/
│   ├── auth/
│   ├── analytics/
│   ├── rules/
│   ├── security/
│   └── triage/
├── knowledge/             # RAG corpus sources
├── data/                  # runtime SQLite and generated artifacts
└── tests/                 # pytest suite

frontend/
├── src/components/
├── src/layouts/
├── src/pages/
├── src/services/api.js
├── src/styles/
├── e2e/                   # Playwright smoke tests
├── nginx.conf
└── Dockerfile
```

---

## Verification Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
cmd /c "npm test -- --reporter=dot"
cmd /c "npm run lint"
cmd /c "npm run build"

cd ..
git diff --check
```

Current verified counts: 938 backend tests, 413 frontend tests.

Before declaring a change complete:

1. Run targeted tests for the changed area.
2. Run the broader suite when the change crosses modules.
3. Check authentication/authorization on new routes.
4. Check external input, secrets, URLs, and error messages.
5. Update living docs and route inventories.
6. Record anything not verified.

---

## Git and Review Rules

- Default branch: `master`.
- Use focused branches: `feature/*`, `fix/*`, `docs/*`, `refactor/*`.
- Commit format: `type(scope): description`.
- Stage explicit paths; never stage `.env`, credentials, generated artifacts, or
  `.superpowers/` ledgers.
- Do not force-push shared branches.
- Do not merge with unresolved critical correctness or security findings.
- Deployment changes need rollback and verification steps.

---

## Operational Checks

### Health

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost/health
curl -fsS http://localhost:11434/api/tags   # only for local Ollama
```

### Scanner availability

```bash
curl -fsS http://localhost:8000/api/scanners/health
```

This checks Semgrep, Trivy, GitLeaks, Bandit, and Safety. Other scanner
integrations may still be available.

### AI configuration

The backend logs the configured provider chain at startup. Confirm which
providers have usable keys and whether Ollama is reachable at
`AI_LOCAL_BASE_URL`.

### Logs

- systemd: `journalctl -u onyx-backend`
- Compose: `docker compose logs -f backend`
- nginx: `/var/log/nginx/error.log`
- Ollama: `$HOME/ollama/ollama.log` in the current Jenkins setup

---

## Deployment Ownership

Before deploying:

- confirm database backup
- confirm `SECRET_KEY`, `MONGODB_URI`, `FRONTEND_URL`, `CORS_ORIGINS`, and
  `WEBHOOK_SECRET` are set
- confirm frontend production URL is not `127.0.0.1`
- confirm optional scanner binaries and AI model availability
- run tests locally or in CI

After deploying:

- verify `/health` through nginx
- verify login and one authenticated page
- verify a manual scan and webhook event in a non-production project
- verify WebSocket updates
- check backend and nginx logs
- record the deployed commit

The Jenkins pipeline records the previous commit and invokes
`scripts/rollback.sh` when a post-restart failure occurs. Rollback restores code
and services only; keep a database backup before changing production. Verify the
rollback path on the EC2 host after pipeline changes.

---

## Secrets and Data

- Never place secrets in code, docs, logs, or issue reports.
- Use least-privilege SCM tokens.
- Rotate `AUTO_FIX_TOKEN` after exposure or team changes.
- Rotate `WEBHOOK_SECRET` through the admin endpoint, restart the backend, then
  update the SCM webhook.
- Avoid changing `SECRET_KEY` without a migration plan: it signs JWTs and
  derives the field-encryption key.
- Treat AI output and fetched repository content as untrusted input.

---

## Documentation Responsibilities

- API routes: update `docs/API.md`.
- Feature status: update `docs/PROJECT_STATUS.md`.
- Deployment behavior: update `docs/DEPLOYMENT.md` and `SECURITY.md`.
- Architecture: update `docs/ARCHITECTURE.md` when data flow or components change.
- Dated plans under `docs/superpowers/` are historical records. Do not rewrite
  them; add a new dated note when superseded.
