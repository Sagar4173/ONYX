# Deployment Guide

ONYX has two supported deployment shapes:

1. **Current hosted path:** Jenkins deploys to an EC2 host running the backend
   under systemd, nginx serving the frontend build, MongoDB, and optional
   Ollama.
2. **Self-hosted path:** Docker Compose runs the frontend, backend, MongoDB, and
   optional Ollama on one host.

Reusable systemd, nginx, environment, and bootstrap assets live under `deploy/`.
The operator runbook is `deploy/README.md`. Credentials are not stored in the
repository. The `Jenkinsfile` is the source of truth for the current pipeline.
The configured production hostname `onyx.ajuna.website` did not resolve during
the October 2026 audit; verify DNS, TLS, and service health before treating that
instance as live.

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

### Reusable host assets

| Path | Purpose |
|---|---|
| `deploy/systemd/onyx-backend.service.template` | systemd unit for Uvicorn |
| `deploy/nginx/onyx.conf.template` | host nginx site and API/WebSocket proxies |
| `deploy/env/backend.production.env.example` | production backend env template |
| `deploy/env/frontend.production.env.example` | production frontend build env |
| `deploy/scripts/install-packages.sh` | install AL2023 runtime packages |
| `deploy/scripts/bootstrap-app.sh` | create venv, install deps, build, publish |
| `deploy/scripts/install-host-config.sh` | install systemd/nginx and restart |
| `deploy/scripts/preflight.sh` | read-only host readiness check |
| `deploy/scripts/smoke-test.sh` | verify services through nginx |
| `deploy/scripts/enable-tls.sh` | request and install Let's Encrypt TLS |
| `deploy/README.md` | complete operator runbook |

Templates use `__ONYX_DOMAIN__`, `__ONYX_USER__`, `__ONYX_PROJECT_DIR__`, and
`REPLACE_WITH_...` placeholders. Never commit filled-in production files.

### Host layout

```text
/home/ec2-user/ONYX/
├── backend/
│   ├── .env                 # untracked, not in Git
│   ├── venv/
│   └── app.py
├── frontend/
│   ├── .env                 # untracked, not in Git
│   └── dist/
├── deploy/
└── Jenkinsfile

/var/www/onyx/               # nginx document root, rebuilt from frontend/dist
/etc/systemd/system/onyx-backend.service
/etc/nginx/conf.d/onyx.conf
MongoDB                      # MONGODB_URI
Ollama                       # optional, $HOME/ollama
```

Nginx serves `/var/www/onyx` rather than a directory under
`/home/ec2-user/ONYX` to avoid home-directory traversal restrictions. The
pipeline publishes the frontend there after a successful build.

### First-time host setup

```bash
git clone https://github.com/Sagar4173/ONYX.git /home/ec2-user/ONYX
cd /home/ec2-user/ONYX
chmod +x deploy/scripts/*.sh
./deploy/scripts/install-packages.sh

cp deploy/env/backend.production.env.example backend/.env
cp deploy/env/frontend.production.env.example frontend/.env
chmod 600 backend/.env frontend/.env
# Fill in real values, then:
./deploy/scripts/bootstrap-app.sh
./deploy/scripts/preflight.sh

sudo env \
  ONYX_DOMAIN=onyx.ajuna.website \
  ONYX_USER=ec2-user \
  ONYX_PROJECT_DIR=/home/ec2-user/ONYX \
  ./deploy/scripts/install-host-config.sh

./deploy/scripts/smoke-test.sh
```

After DNS points at the Elastic IP:

```bash
sudo env ONYX_EMAIL=admin@example.com \
  ./deploy/scripts/enable-tls.sh onyx.ajuna.website
```

See `deploy/README.md` for prerequisites, security-group rules, MongoDB setup,
Jenkins configuration, and the handoff checklist.

### Pipeline behavior

`Jenkinsfile` currently:

1. Cleans old workspaces, package caches, logs, and old backups.
2. Clones `/home/ec2-user/ONYX` on a fresh host, or records the last successful
   deployment, marks the deploy in progress, and hard-resets an existing
   checkout to `origin/master`.
3. Verifies production env files, rejects untouched environment templates, and
   checks that the host systemd/nginx configuration is installed.
4. Creates or validates the backend venv and installs backend dependencies.
5. Runs backend tests.
6. Installs scanner binaries.
7. Sets up and starts Ollama, pulling the configured small model if absent.
8. Installs frontend dependencies with `npm ci`, runs tests, and builds.
9. Publishes `frontend/dist/` to `/var/www/onyx`.
10. Restarts Ollama, `onyx-backend`, and nginx.
11. Checks the backend directly and through nginx, then checks service status
    and optional Ollama.
12. Records the current commit as the last successful deployment and clears the
    deploy marker after all checks pass.

The deployment checkout is intentionally separate from the Jenkins workspace so
workspace cleanup cannot delete `.env` files or the venv.

Jenkins records the last successful deployment in
`$HOME/.onyx_deployed_commit` and copies it to `$HOME/.onyx_previous_commit` at
the start of each deploy. It sets the deploy marker before resetting the
checkout, so failures and aborts after that point trigger
`scripts/rollback.sh`. The script resets to the previous commit, reinstalls
backend dependencies, rebuilds and republishes the frontend, restarts services,
and retries the backend health check. A successful rollback records the
restored commit as the last successful deployment. If rollback fails, Jenkins
restarts the current services as a last resort.

Rollback restores code and frontend assets, not MongoDB data. Take a database
backup before each release. The state files must be writable by the Jenkins
agent user, and the rollback path should be exercised once on the EC2 host.

The Jenkins pipeline uses `qwen2.5-coder:3b` to fit the host; the backend example
configuration uses `qwen2.5-coder:3b`. Set the model explicitly in
`backend/.env` and confirm it exists in Ollama.

### Required host configuration

Create `backend/.env` from
`deploy/env/backend.production.env.example`. At minimum, set:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<random-32+-character-secret>
MONGODB_URI=<authenticated MongoDB URI>
FRONTEND_URL=https://onyx.ajuna.website
CORS_ORIGINS=https://onyx.ajuna.website
ALLOWED_ORIGINS=https://onyx.ajuna.website
WEBHOOK_SECRET=<random-secret>
```

Create `frontend/.env` from
`deploy/env/frontend.production.env.example`:

```env
VITE_API_URL=/api
VITE_WS_URL=
VITE_ENVIRONMENT=production
```

For a same-origin nginx deployment, `VITE_API_URL=/api` is correct. For a split
API domain, use its full HTTPS URL.

The installed nginx site:

- serves `/var/www/onyx` (published `root:root`, readable by nginx) and falls
  back to `index.html` for SPA routes
- proxies `/api/` to the backend
- proxies `/ws` with HTTP/1.1 upgrade headers
- proxies `/health`, `/docs`, `/docs/oauth2-redirect`, `/redoc`, and
  `/openapi.json`
- limits request bodies to 10 MB
- adds security headers and static asset caching

The installed systemd unit:

- runs as the deployment user
- loads `backend/.env`
- starts Uvicorn on `127.0.0.1:8000` with one worker
- restarts on failure
- sends logs to journald with Uvicorn access logging disabled
- prepends the backend venv to `PATH` so Jenkins-installed scanners are visible
- uses `PrivateTmp`, `ProtectSystem=full`, and `NoNewPrivileges`

### Configure Jenkins

- Point the job at `https://github.com/Sagar4173/ONYX.git`.
- Use branch `*/master` and script path `Jenkinsfile`.
- Prefer a Jenkins SSH agent running as `ec2-user`; the pipeline writes the
  deployment checkout and `$HOME/.onyx_*` state files.
- Grant narrowly scoped passwordless sudo for the commands in `Jenkinsfile`.
  Verify with `sudo -l -U <agent-user>`. Unrestricted `sudo rsync`, `install`,
  `chmod`, or `tee` rules are effectively root-equivalent; scope them to exact
  paths and arguments.
- Keep `.env` files out of Git; they are untracked and survive the hard reset.
  Preflight and Jenkins require `backend/.env` and `frontend/.env` to be mode
  `600` or `400`.
- Do not store credentials in the Jenkinsfile or console output.
- Confirm the health check can actually fail the build.

If the repository becomes private, configure a read-only SCM credential; the
current pipeline performs a plain `git clone` of the public repository.

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

Open http://localhost. API documentation is at http://localhost/docs and
http://localhost/redoc.

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

On Amazon Linux 2023, install packages once:

```bash
./deploy/scripts/install-packages.sh
```

After DNS points at the Elastic IP and HTTP health passes:

```bash
sudo env ONYX_EMAIL=admin@example.com \
  ./deploy/scripts/enable-tls.sh your-domain.example
```

The script runs `certbot --nginx --redirect`, enables the renewal timer, and
checks HTTPS. Verify renewal:

```bash
sudo certbot renew --dry-run
```

Use the EC2 security group rather than host `ufw`:

| Port | Source |
|---|---|
| 22 | administrator IP only |
| 80 | anywhere, for HTTP and ACME |
| 443 | anywhere, for HTTPS |

Do not expose MongoDB (27017), Ollama (11434), or the backend (8000) publicly.
Restrict SSH to trusted addresses.

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

- Health: `GET /health` through nginx or directly on the backend; require
  `"status": "healthy"`
- Metrics: `GET /metrics` on the backend port; nginx does not proxy it by default
- Errors: configure `SENTRY_DSN`
- Logs: journald, nginx logs, Docker logs, and Ollama logs. Uvicorn access
  logging is disabled and `/ws` access logging is off; nginx error logs can
  still contain request URIs (including WebSocket query tokens) on upstream
  errors, so restrict access and retention.
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
6. deployment-asset checks: shell syntax, nginx template syntax, and required
   template placeholders

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
