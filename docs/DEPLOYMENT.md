# Deployment Guide

ONYX is deployed on AWS. This guide covers Docker-based production deployment.

---

## Docker Compose (Recommended)

### Prerequisites
- Docker 24+ and Docker Compose 2+
- 4GB+ RAM, 10GB+ disk
- MongoDB-compatible storage

### Configuration

```bash
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX
cp .env.example .env
```

Required environment variables:

```env
MONGODB_URI=mongodb://mongodb:27017/onyx
SECRET_KEY=<random-32-char-min>
OPENAI_API_KEY=sk-...
# or
GEMINI_API_KEY=...
```

Full variable list: see `.env.example`

### Deploy

```bash
docker compose up -d
docker compose ps
docker compose logs -f
```

| Service | Internal Port | Exposed |
|---|---|---|
| mongodb | 27017 | - |
| backend | 8000 | 8000 |
| frontend | 80 | 80 |

### Health Check

```bash
curl http://localhost:8000/health
curl http://localhost/api/docs
```

---

## Build & Run (Standalone)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend
npm run build
# Serve dist/ via nginx or vite preview
npx vite preview --port 5173 --host 0.0.0.0
```

### nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name app.your-domain.com;

    root /opt/ONYX/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## Production Security

### SSL/TLS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Firewall

```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### MongoDB Security

Enable authentication and bind to internal network only. Do not expose port 27017 publicly.

---

## Backup

### MongoDB

```bash
mongodump --uri="$MONGODB_URI" --out=/backup/$(date +%Y%m%d)
```

Cron (daily at 2 AM):
```bash
0 2 * * * mongodump --uri="$MONGODB_URI" --out=/backup/$(date +%%Y%%m%%d)
```

---

## Monitoring

- **Health**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus)
- **Errors**: Sentry (configure `SENTRY_DSN`)

---

## CI/CD

GitHub Actions workflow at `.github/workflows/ci.yml`:
1. Backend tests (pytest)
2. Frontend tests, lint, build
3. E2E smoke tests (Playwright)
4. Docker image build

---

## Troubleshooting

| Issue | Check |
|---|---|
| Backend crash | `docker compose logs backend` |
| MongoDB connection | Verify `MONGODB_URI` and network |
| Port conflict | Change port mapping in `docker-compose.yml` |
| Slow scans | Ensure sufficient CPU/memory for containers |
