# Installation Guide

## Prerequisites

- Python 3.13+
- Node.js 22+
- MongoDB 7+ (local, Atlas, or Docker)
- Git
- PowerShell on Windows, or a POSIX shell on Linux/macOS
- Optional: Docker 24+ and Docker Compose 2+ for container deployment
- Optional: Ollama, or API keys for cloud AI providers
- Optional: external scanner binaries

---

## Local Development

### 1. Clone

```bash
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX
```

### 2. Backend environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set these values in `backend/.env`:

```env
MONGODB_URI=mongodb://localhost:27017/onyx
SECRET_KEY=<random-value-at-least-32-characters>
ENVIRONMENT=development
```

Generate a secret:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Do not use the example secret outside local development.

### 3. Database

Choose one:

- **Local MongoDB:** install MongoDB 7+, start the service, and use
  `mongodb://localhost:27017/onyx`.
- **Docker MongoDB:** `docker run -d --name onyx-mongo -p 127.0.0.1:27017:27017 mongo:7`.
- **MongoDB Atlas:** create a cluster and set the full connection string in
  `MONGODB_URI`.

MongoDB is required. The backend will not start successfully without it.

### 4. AI configuration

ONYX works without AI, but AI analysis, chat, triage summaries, and auto-fix
generation are unavailable.

`AI_PROVIDER=auto` follows `AI_PROVIDER_CHAIN` from left to right:

```env
AI_PROVIDER=auto
AI_PROVIDER_CHAIN=gemini,groq,openrouter,ollama
```

Providers without usable credentials are skipped. `OPENAI_API_KEY` is supported
as an explicit/legacy provider.

#### Cloud providers

Set one or more keys:

```env
GEMINI_API_KEY=...
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
```

#### Local Ollama

Install Ollama separately, pull a model, and configure the backend:

```bash
ollama pull qwen2.5-coder:7b
```

```env
AI_LOCAL_BASE_URL=http://localhost:11434/v1
AI_LOCAL_MODEL=qwen2.5-coder:7b
```

A 7B model generally needs roughly 8 GB of available memory. Use a smaller model
on limited hosts. Ollama is used only when configured or included in the
provider chain.

### 5. Optional scanners

The backend includes Python-native scanners and lazy integration for others.
External binaries must be installed and on `PATH`:

| Scanner | Requirement | Enable |
|---|---|---|
| Semgrep | Installed lazily by the backend or install manually | default integration |
| Bandit | Included in backend requirements | default integration |
| Safety | Included in backend requirements | default integration |
| Detect-Secrets | Included in backend requirements | default integration |
| SOPS | `sops` binary for full checks; config validation works without it | default integration |
| Dependency Governance | Included in the backend | default integration |
| GitLeaks | GitHub release binary | default integration when available |
| Trivy | Trivy binary | `ENABLE_TRIVY=true` |
| ZAP | ZAP daemon / API endpoint | `ENABLE_ZAP=true` |
| Nuclei | Nuclei binary | `ENABLE_NUCLEI=true` |
| CodeQL | CodeQL CLI | `ENABLE_CODEQL=true` |
| Checkov | `pip install checkov` | `ENABLE_CHECKOV=true` |
| Lynis | Lynis binary | `ENABLE_LYNIS=true` |

Check availability after startup:

```bash
curl http://localhost:8000/api/scanners/health
```

Missing optional scanners degrade results but do not prevent the application
from running.

### 6. Start the backend

```powershell
.\.venv\Scripts\python.exe main.py
```

or:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

- API: http://localhost:8000
- OpenAPI UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 7. Frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173

The development server connects to `http://127.0.0.1:8000/api`. Production
builds use `VITE_API_URL` and `VITE_WS_URL`; if they are unset, the API defaults
to same-origin `/api`.

For a local production build:

```powershell
Copy-Item .env.example .env
# Same-origin nginx build: leave VITE_API_URL=/api
# Local preview without proxy: VITE_API_URL=http://127.0.0.1:8000/api
# Set VITE_WS_URL when the WebSocket uses a different host
npm run build
```

Do not deploy a build with `VITE_API_URL=http://127.0.0.1:8000/api` unless the
browser is expected to reach a backend on its own machine.

---

## Docker Compose

### 1. Configure the backend

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` and set at least:

```env
SECRET_KEY=<random-value-at-least-32-characters>
MONGODB_URI=mongodb://mongodb:27017/onyx
FRONTEND_URL=http://localhost
```

Compose overrides MongoDB and container networking values, but the environment
file still needs a valid secret and any AI keys.

### 2. Start

```powershell
docker compose up -d --build
docker compose ps
```

| Service | Visibility |
|---|---|
| Frontend | Host port 80 |
| Backend | Compose network only |
| MongoDB | Compose network only |
| Ollama | Compose network only |

Open http://localhost. The frontend nginx proxy serves `/api`, `/ws`, `/health`,
`/docs`, and `/openapi.json`.

### 3. Pull the local model (optional)

```powershell
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

This is only needed when local Ollama is part of the provider chain. Cloud AI
keys can be used instead.

### 4. Verify

```powershell
curl.exe http://localhost/health
curl.exe http://localhost/api/stats/public
docker compose logs -f backend
```

The backend port 8000 is intentionally not exposed to the host in the default
Compose file.

### 5. Stop

```powershell
docker compose down
```

Use `docker compose down -v` only when you intentionally want to remove the
MongoDB and backend data volumes.

---

## Verification

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m pytest -q

# Frontend
cd ..\frontend
cmd /c "npm test -- --reporter=dot"
cmd /c "npm run lint"
cmd /c "npm run build"
```

Current verified suite sizes: 938 backend tests and 413 frontend tests.

A minimal post-install smoke test:

1. Sign in or register.
2. Create a project.
3. Run a scan against a small repository.
4. Confirm findings appear in the report.
5. Confirm WebSocket progress updates.

---

## Troubleshooting

| Problem | Check |
|---|---|
| Backend exits at startup | `SECRET_KEY` length, `MONGODB_URI`, MongoDB reachability |
| `ModuleNotFoundError` | Activate `.venv` and reinstall `requirements.txt` |
| Frontend cannot reach API | Backend on port 8000, browser network tab, Vite build variables |
| Login fails after config change | `SECRET_KEY` changed, lockout, email verification, 2FA |
| No AI output | Provider keys, `AI_PROVIDER_CHAIN`, Ollama model and base URL |
| Scanner missing | Binary on `PATH`, enable flag, `/api/scanners/health` |
| Docker frontend cannot reach API | Check nginx proxy and Compose backend health |
| MongoDB unreachable | `MONGODB_URI`, MongoDB service status, Compose health |
| Slow local AI | Use a smaller model or cloud provider |

For production deployment, continue to [DEPLOYMENT.md](DEPLOYMENT.md).
