# Deployment Guide

ONYX has two supported deployment shapes:

1. **Current hosted path:** Jenkins deploys to an EC2 host running the backend
   under systemd, nginx serving the frontend build, MongoDB, and optional
   Ollama.
2. **Self-hosted path:** Docker Compose runs the frontend, backend, MongoDB, and
   optional Ollama on one host.

The repository does not contain the systemd unit, host nginx configuration, or
credentials for the EC2 deployment. The `Jenkinsfile` is the source of truth for
the current pipeline. The configured production hostname
`onyx.ajuna.website` did not resolve during the October 2026 audit; verify DNS,
TLS, and service health before treating that instance as live.

---

## Deployment Requirements

| Component | Requirement |
|---|---|
| Python | 3.13 |
| Node.js | 22 for frontend builds |
| MongoDB | 7+ |
| Reverse proxy | nginx or equivalent |
| TLS | Valid certificate for the public hostname |
| Memory | 4 GB minimum for cloud AI; 8 GB+ recommended for Ollama |
| Disk | 10 GB+ for application and scans; more for models and backups |

For production, prefer a host with 8 GB+ RAM, MongoDB with authentication and
backups, a least-privilege SCM token, and external monitoring.

---

## Option A: Current Jenkins/EC2 Deployment

### Host layout assumed by `Jenkinsfile`

```text
/home/ec2-user/ONYX/
├── backend/
│   ├── .env
│   ├── venv/
│   └── app.py
├── frontend/
│   ├── .env
│   └── dist/
└── Jenkinsfile

systemd service: onyx-backend
nginx: serves the frontend build and proxies /api, /ws, /health, /docs
MongoDB: reachable through MONGODB_URI
Ollama: optional, installed under $HOME/ollama
```

The pipeline runs on the same EC2 host as the application and assumes sudo
access to restart `onyx-backend` and reload nginx.

### Pipeline behavior

`Jenkinsfile` currently:

1. Cleans old workspaces, package caches, logs, and old backups.
2. Records the currently deployed commit in `$HOME/.onyx_previous_commit` and
   clears any stale deploy marker.
3. Fetches and hard-resets the host checkout to `origin/master`.
4. Verifies backend and frontend `.env` files exist.
5. Installs backend dependencies in `backend/venv`.
6. Runs backend tests.
7. Installs scanner binaries.
8. Sets up and starts Ollama, pulling the configured small model if absent.
9. Installs frontend dependencies, runs tests, and builds the frontend.
10. Marks the deployment in progress, then restarts Ollama, `onyx-backend`, and
    nginx.
11. Retries backend health checks, then checks nginx, services, and optional
    Ollama; required failures stop the build.
12. Clears the deploy marker after all checks pass.

If a failure occurs after the deploy marker is set, the `post` block runs
`scripts/rollback.sh`. The script resets the checkout to
`$HOME/.onyx_previous_commit`, reinstalls backend dependencies, rebuilds the
frontend, restarts services, and retries the backend health check. If rollback
fails, Jenkins restarts the current services as a last resort.

Rollback restores code and services, not MongoDB data. Take a database backup
before each release. The state files must be writable by the Jenkins user, and
the rollback path should be exercised once on the EC2 host because service names
and permissions are host-specific.

The Jenkins pipeline uses `qwen2.5-coder:3b` to fit the host; the backend example
configuration uses `qwen2.5-coder:7b`. Set the model explicitly in
`backend/.env` and confirm it exists in Ollama.

### Required host configuration

Create `backend/.env` with at least:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<random-32+-character-secret>
MONGODB_URI=<authenticated MongoDB URI>
FRONTEND_URL=https://your-domain.example
CORS_ORIGINS=https://your-domain.example
WEBHOOK_SECRET=<random-secret>
```

Create `frontend/.env` for the production build:

```env
VITE_API_URL=/api
VITE_WS_URL=wss://your-domain.example
VITE_ENVIRONMENT=production
```

For a same-origin nginx deployment, `VITE_API_URL=/api` is usually correct.
For a split API domain, use its full HTTPS URL.

The host nginx must:

- serve `frontend/dist` and fall back to `index.html` for SPA routes
- proxy `/api/` to the backend
- proxy `/ws` with HTTP/1.1 upgrade headers
- proxy `/health`, `/docs`, and `/openapi.json` if those should be public
- enforce HTTPS and suitable security headers
- limit request bodies consistently with the backend's 10 MB limit

The backend systemd service should:

- run as a non-root user
- load `backend/.env`
- start Uvicorn/Gunicorn on `127.0.0.1:8000`
- restart on failure
- send logs to journald
- have a working directory of `/home/ec2-user/ONYX/backend`

The repository does not include a reusable systemd unit; add one if the host is
rebuilt.

### Configure Jenkins

- Point the job at `https://github.com/Sagar4173/ONYX.git`.
- Trigger on `master`.
- Ensure the Jenkins user can write the deploy directory, restart
  `onyx-backend`, and reload nginx.
- Keep `.env` files out of Git; they are untracked and must survive the
  hard-reset deployment.
- Do not store credentials in the Jenkinsfile or console output.
- Confirm the health check can actually fail the build.

---

## Option B: Docker Compose

### 1. Configure

```powershell
Copy-Item backend\.env.example backend\.env
# Set SECRET_KEY and FRONTEND_URL; Compose supplies MONGODB_URI
```

For a public domain, set in `backend/.env`:

```env
ENVIRONMENT=production
DEBUG=false
FRONTEND_URL=https://your-domain.example
CORS_ORIGINS=https://your-domain.example
WEBHOOK_SECRET=<random-secret>
```

The Compose file overrides container-internal MongoDB and AI URLs. It does not
inject a public hostname; configure `FRONTEND_URL` and `CORS_ORIGINS` explicitly.

### 2. Start

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

### 3. Pull a local model (optional)

```powershell
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

Cloud AI can be used instead by setting provider keys.

### 4. Ports

| Service | Host exposure | Internal |
|---|---|---|
| frontend | 80 | 80 |
| backend | none | 8000 |
| MongoDB | none | 27017 |
| Ollama | none | 11434 |

Do not add host mappings for MongoDB or Ollama on an internet-facing host.
Use `docker compose exec` for administrative access.

### 5. Verify

```powershell
curl.exe -fsS http://localhost/health
curl.exe -fsS http://localhost/api/stats/public
```

Open http://localhost. API documentation is at http://localhost/docs.

---

## Standalone Backend and Frontend

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1
```

Use one worker with the current scheduler and WebSocket manager. If using
Gunicorn with Uvicorn workers, confirm scheduled jobs and WebSocket coordination
before increasing worker count.

### Frontend

```bash
cd frontend
npm ci
npm run build
```

Serve `dist/` with nginx or another static server that supports SPA fallback.
Do not use `vite preview` as a production server.

---

## TLS and Firewall

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Do not expose MongoDB or Ollama publicly. Restrict SSH to trusted addresses.

---

## Product Sizing Guidance

### Free or evaluation

- 4 GB VM, 2 vCPU, cloud AI keys
- external or local MongoDB
- Cloudflare or Let's Encrypt for TLS
- accept slower scans and no high availability

A 4 GB host is usually too small for a 7B local model and concurrent scans.
Use cloud AI or a smaller model.

### Production

- 8 GB+ RAM, 2-4 vCPU, SSD
- MongoDB with authentication, TLS, and tested backups
- 8 GB+ extra capacity if running Ollama
- external uptime monitoring and log retention
- least-privilege SCM tokens and a documented key-rotation process
- regular dependency and host patching

---

## Backups

### MongoDB

```bash
mongodump --uri="$MONGODB_URI" --out="/backup/$(date +%Y%m%d)"
```

Example cron entry:

```cron
0 2 * * * mongodump --uri="$MONGODB_URI" --out="/backup/$(date +\%Y\%m\%d)"
```

Also back up:

- `backend/.env` through an approved secrets mechanism
- `backend/data/knowledge.db`
- ML state if enabled
- the deployed commit SHA
- host nginx and systemd configuration

Restore-test backups. A backup that has never been restored is unverified.

---

## Monitoring

- Health: `GET /health` through nginx or directly on the backend
- Metrics: `GET /metrics` on the backend port; nginx does not proxy it by default
- Errors: configure `SENTRY_DSN`
- Logs: journald, nginx logs, Docker logs, and Ollama logs
- Scanner availability: `GET /api/scanners/health`

Recommended alerts:

- backend process down
- 5xx rate increase
- MongoDB connectivity failure
- disk usage above 80%
- TLS expiration
- repeated webhook authentication failures
- AI provider failure rate
- scan failure rate or stuck scans

---

## CI/CD

`.github/workflows/ci.yml` runs on pushes and pull requests to `master`/`main`:

1. backend pytest
2. frontend lint, tests, and production build
3. Playwright smoke and authenticated flows: registration, login, dashboard,
   and sidebar navigation
4. backend and frontend Docker image builds
5. Compose smoke test: starts MongoDB, backend, and frontend, then checks nginx
   health, API docs, security headers, and that backend port 8000 is not
   published on the host

GitHub Actions is verification, not the current deployment mechanism. The
Jenkins pipeline is the current EC2 deployment path.

Before promoting a release:

1. CI is green.
2. Database backup exists.
3. Environment changes are applied.
4. The deployed commit is recorded.
5. Health, login, scan, WebSocket, and webhook smoke tests pass.
6. A rollback target is known.

---

## Troubleshooting

| Problem | Check |
|---|---|
| Jenkins build fails | Console log, `.env` presence, disk space, sudo permissions |
| Backend fails after deploy | `journalctl -u onyx-backend`, `MONGODB_URI`, `SECRET_KEY`, dependency install |
| nginx returns 502 | Backend process and port 8000 |
| Login works but assets are stale | Frontend build contents, nginx root, cache headers |
| WebSocket fails | `/ws` proxy upgrade headers, token, mixed HTTP/HTTPS |
| Webhook returns 503 | `WEBHOOK_SECRET` unset; restart backend after setting it |
| AI unavailable | Provider keys, provider chain, Ollama memory/model |
| Mongo connection refused | Authentication, bind address, TLS, firewall |
| Disk fills during deploy | Workspaces, Docker images, journald, Ollama models, backups |
| Production hostname missing | DNS record, TLS certificate, nginx server name |
