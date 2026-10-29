# ONYX EC2 / Jenkins Deployment Runbook

This directory contains the host configuration and bootstrap procedures for the
current ONYX deployment shape:

- Amazon Linux 2023 EC2 instance
- Jenkins pipeline deploying to `/home/ec2-user/ONYX`
- Uvicorn managed by systemd on `127.0.0.1:8000`
- host nginx serving `/var/www/onyx` and proxying `/api`, `/ws`, `/health`,
  `/docs`, `/docs/oauth2-redirect`, `/redoc`, and `/openapi.json`
- MongoDB Atlas or an authenticated local MongoDB
- optional local Ollama

The templates contain placeholders only. Do not put real secrets in this
directory or commit `backend/.env` or `frontend/.env`.

---

## What to send another operator

Send:

- repository URL: `https://github.com/Sagar4173/ONYX.git`
- branch: `master`
- this file: `deploy/README.md`
- target hostname: `onyx.ajuna.website`
- preferred deployment user and directory: `ec2-user`,
  `/home/ec2-user/ONYX`
- EC2 Elastic IP after it is allocated
- the email address to use for Let's Encrypt
- whether MongoDB Atlas or a local MongoDB will be used
- Jenkins job name, agent label, and credential names, if Jenkins already exists

Do not send:

- SSH private keys
- AWS secret access keys
- Jenkins passwords or API tokens
- MongoDB passwords or connection strings
- AI provider keys
- the contents of `backend/.env` or `frontend/.env`

Use a password manager or the organisation's approved secrets channel for
secret values. Create separate credentials for each operator.

---

## Host assumptions

| Item | Value |
|---|---|
| OS | Amazon Linux 2023 |
| Application user | `ec2-user` |
| Checkout | `/home/ec2-user/ONYX` |
| Backend venv | `/home/ec2-user/ONYX/backend/venv` |
| Frontend web root | `/var/www/onyx` |
| systemd unit | `/etc/systemd/system/onyx-backend.service` |
| nginx site | `/etc/nginx/conf.d/onyx.conf` |
| Public port | 80 and 443 |
| Backend port | 8000, localhost only |

The Jenkins agent must run as `ec2-user`, or have equivalent access to the
checkout, the venv, and the scoped sudo commands below. The pipeline writes
deployment markers to `$HOME`; using a different user changes where those files
live.

---

## 1. Create the EC2 instance

Recommended sizing:

- cloud AI only: `t3.medium` or larger, 4 GB+ RAM
- local Ollama: `t3.large` or larger, 8 GB+ RAM
- disk: 30 GB gp3 minimum

Create or select a security group with:

| Port | Source | Purpose |
|---|---|---|
| 22 | administrator IP only | SSH/SSM administration |
| 80 | `0.0.0.0/0`, `::/0` | HTTP and ACME |
| 443 | `0.0.0.0/0`, `::/0` | HTTPS |

Do not expose ports 8000, 27017, or 11434 to the internet.

Allocate an Elastic IP and associate it with the instance. Record the address;
it is needed for DNS.

SSH in:

```bash
ssh -i /path/to/your-key.pem ec2-user@<elastic-ip>
```

Never copy a private key to the server or into this repository.

---

## 2. Install runtime packages

```bash
git clone https://github.com/Sagar4173/ONYX.git /home/ec2-user/ONYX
cd /home/ec2-user/ONYX
chmod +x deploy/scripts/*.sh
./deploy/scripts/install-packages.sh
```

Verify:

```bash
python3.13 --version
node --version
npm --version
nginx -v
certbot --version
```

`node` must report 22.x or newer. If it does not, select the `nodejs22`
alternative before continuing:

```bash
sudo alternatives --set node /usr/bin/node-22
sudo alternatives --set npm /usr/bin/npm-22
```

---

## 3. Configure MongoDB

### Option A: MongoDB Atlas

1. Create a cluster and database user.
2. Allow the EC2 Elastic IP in Atlas network access.
3. Use a URI shaped like:

```text
mongodb+srv://<user>:<password>@<cluster>/onyx?retryWrites=true&w=majority
```

### Option B: local MongoDB

Install MongoDB 7 from the official Amazon Linux 2023 repository, enable
authentication, and bind it to localhost. Example repository file:

```ini
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/7.0/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
```

Create a database user and use a URI shaped like:

```text
mongodb://onyx:<password>@127.0.0.1:27017/onyx?authSource=admin
```

Do not expose port 27017 or run an unauthenticated database.

---

## 4. Create environment files

```bash
cd /home/ec2-user/ONYX
cp deploy/env/backend.production.env.example backend/.env
cp deploy/env/frontend.production.env.example frontend/.env
chmod 600 backend/.env frontend/.env
```

Generate secrets locally on the host:

```bash
python3.13 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Fill in `backend/.env`:

- `SECRET_KEY`
- `WEBHOOK_SECRET`
- `MONGODB_URI`
- `FRONTEND_URL=https://onyx.ajuna.website`
- `CORS_ORIGINS=https://onyx.ajuna.website`
- `ALLOWED_ORIGINS=https://onyx.ajuna.website`
- AI provider keys, if used
- SMTP settings, only if email verification/password reset is enabled

Keep registration open only until the first administrator account exists. Set
`ALLOW_REGISTRATION=false` afterwards if the deployment should be closed.

The frontend production file should keep:

```env
VITE_API_URL=/api
VITE_WS_URL=
VITE_ENVIRONMENT=production
```

---

## 5. Bootstrap the application

Run as `ec2-user`, not root:

```bash
cd /home/ec2-user/ONYX
./deploy/scripts/bootstrap-app.sh
```

This creates the venv, installs backend dependencies, runs `npm ci`, builds the
frontend, and publishes `frontend/dist/` to `/var/www/onyx`.

Check readiness:

```bash
./deploy/scripts/preflight.sh
```

Fix every `FAIL` before continuing. `WARN` items should be understood and
accepted explicitly.

---

## 6. Install systemd and nginx

```bash
sudo env \
  ONYX_DOMAIN=onyx.ajuna.website \
  ONYX_USER=ec2-user \
  ONYX_PROJECT_DIR=/home/ec2-user/ONYX \
  /home/ec2-user/ONYX/deploy/scripts/install-host-config.sh
```

This installs the systemd unit and nginx site, tests nginx, starts the backend,
and waits for a healthy health response. The unit prepends the backend venv to
`PATH`, so scanners installed by Jenkins are visible to the service. The script
also refuses to run the backend as root.

If a Let's Encrypt certificate already exists, the script preserves the
certbot-managed nginx site only when it contains an SSL listener and certificate
directive. If the certificate exists but the site is HTTP-only, it fails instead
of silently dropping HTTPS. Set `ONYX_FORCE_NGINX=1` only when you intend to
replace that site and rerun `enable-tls.sh` afterwards. A failed nginx test
restores the previous site file when one exists.

Verify locally:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1/health
./deploy/scripts/smoke-test.sh
```

At this point the site should be reachable over HTTP using the Elastic IP:
`http://<elastic-ip>/`.

---

## 7. Configure Jenkins

The Jenkinsfile no longer relies on the Jenkins workspace. It clones or updates
`/home/ec2-user/ONYX` directly, so the deployment survives Jenkins workspace
cleanup and retains untracked `.env` files and the venv.

Recommended: run a Jenkins SSH agent on the EC2 host that connects as
`ec2-user`. If the built-in Jenkins node is used instead, grant the Jenkins user
access to the checkout and adapt the paths and ownership consistently.

Job configuration:

- Pipeline script from SCM
- repository: `https://github.com/Sagar4173/ONYX.git` (public)
- branch: `*/master`
- script path: `Jenkinsfile`
- GitHub webhook or polling enabled
- no secrets in the Jenkinsfile

The pipeline needs narrowly scoped passwordless sudo for:

- `systemctl restart onyx-backend`
- `systemctl reload nginx`
- `nginx -t`
- `rsync`
- `install`
- `chmod`
- `journalctl --vacuum-time=1d`
- `tee /etc/systemd/journald.conf.d/onyx-size.conf`
- `systemctl restart systemd-journald`

Review the exact commands in `Jenkinsfile` and verify with:

```bash
sudo -l -U <jenkins-agent-user>
```

Do not grant unrestricted `NOPASSWD: ALL` if a narrower rule is practical.
Unrestricted `sudo rsync`, `sudo install`, `sudo chmod`, or `sudo tee` is
effectively root-equivalent; scope each rule to the exact paths and arguments
used by the pipeline. The frontend is published as `root:root` and only nginx
needs read access to `/var/www/onyx`.

If the repository is made private later, configure a read-only SCM credential.
The current pipeline performs a plain `git clone` of the public repository.

The pipeline:

1. cleans disk space
2. clones or updates the deployment checkout and marks the deploy in progress
3. verifies production env files and host configuration
4. creates or validates the venv and installs backend dependencies
5. runs backend tests
6. installs scanners
7. sets up optional Ollama
8. runs frontend tests and builds the frontend
9. publishes `frontend/dist/` to `/var/www/onyx`
10. restarts the backend and reloads nginx
11. runs health checks through nginx
12. records the successful commit and clears the marker; rolls back code and
    frontend assets on failure or abort

---

## 8. DNS and TLS

After the Elastic IP is associated and the HTTP site is healthy, create a DNS
record:

```text
onyx.ajuna.website.  A  <elastic-ip>
```

If using Cloudflare, use DNS-only (“grey cloud”) until the certificate is
issued. After TLS is working, proxy mode can be enabled with SSL/TLS mode
`Full (strict)`.

Wait for DNS:

```bash
getent ahostsv4 onyx.ajuna.website
```

Then request the certificate:

```bash
sudo env ONYX_EMAIL=admin@example.com \
  /home/ec2-user/ONYX/deploy/scripts/enable-tls.sh onyx.ajuna.website
```

The script:

- verifies HTTP health first
- runs `certbot --nginx --redirect`
- enables the renewal timer
- verifies HTTPS health

Test renewal without consuming a certificate:

```bash
sudo certbot renew --dry-run
```

Verify:

```bash
curl -fsS https://onyx.ajuna.website/health
ONYX_TLS_DOMAIN=onyx.ajuna.website ./deploy/scripts/smoke-test.sh
```

---

## 9. Manual redeploy

```bash
cd /home/ec2-user/ONYX
git pull --ff-only
./deploy/scripts/bootstrap-app.sh
sudo systemctl restart onyx-backend
sudo systemctl reload nginx
./deploy/scripts/smoke-test.sh
```

If the smoke test passes and you want the next Jenkins rollback to target this
manual deployment, record it:

```bash
if [ -f "$HOME/.onyx_deployed_commit" ]; then
    cp "$HOME/.onyx_deployed_commit" "$HOME/.onyx_previous_commit"
fi
git rev-parse HEAD > "$HOME/.onyx_deployed_commit"
rm -f "$HOME/.onyx_deploy_in_progress"
```

The Jenkins pipeline is the tracked deployment path and also runs tests.

---

## 10. Rollback

Jenkins records the last successful commit in `$HOME/.onyx_deployed_commit`.
At the start of each deploy it copies that commit to
`$HOME/.onyx_previous_commit` and sets `$HOME/.onyx_deploy_in_progress` before
updating the deployment checkout. On failure or abort, `scripts/rollback.sh`:

1. resets the checkout to the previous commit
2. reinstalls backend dependencies
3. rebuilds the frontend
4. republishes `/var/www/onyx`
5. restarts the backend and reloads nginx
6. checks backend health
7. records the restored commit as the last successful deployment

Manual rollback:

```bash
cd /home/ec2-user/ONYX
ONYX_FORCE_ROLLBACK=1 bash scripts/rollback.sh
```

The marker is normally present only during a failed deployment. The explicit
flag is required for an intentional rollback after a deployment succeeded.

Rollback restores code and frontend assets, not MongoDB data. Take a database
backup before risky releases. The first deployment has no previous commit to
restore; fix forward if it fails before a successful deploy establishes one.

---

## 11. Backups and monitoring

Back up:

- MongoDB through Atlas snapshots or `mongodump`
- `backend/.env` through the approved secrets manager
- `backend/data/knowledge.db`
- the deployed commit SHA
- host nginx and systemd configuration

Do not rely on `/var/www/onyx` as the source of truth; it is rebuilt from Git.

Monitor:

- `GET /health` through nginx; require `"status": "healthy"`
- systemd status for `onyx-backend` and `nginx`
- nginx access and error logs; Uvicorn access logging is disabled and `/ws`
  access logging is off, so WebSocket query tokens do not reach journald or
  nginx access logs. nginx error logs can still contain request URIs on
  upstream errors; restrict access and retention accordingly.
- disk space
- MongoDB connectivity
- TLS expiry
- Jenkins build status

Useful commands:

```bash
journalctl -u onyx-backend -n 100 --no-pager
sudo nginx -t
sudo tail -n 100 /var/log/nginx/error.log
systemctl status onyx-backend nginx
```

---

## Definition of done

- `./deploy/scripts/preflight.sh` reports zero failures
- `./deploy/scripts/smoke-test.sh` reports zero failures
- `http://<elastic-ip>/health` reports `"status": "healthy"` before DNS/TLS
- `https://onyx.ajuna.website/health` reports `"status": "healthy"` after DNS/TLS
- `certbot renew --dry-run` succeeds
- a Jenkins push to `master` deploys successfully
- a deliberately failed deployment rolls back successfully
- ports 22, 80, and 443 are the only public inbound ports
- MongoDB and Ollama are not publicly reachable
- no secret has been committed to Git or printed in Jenkins logs
