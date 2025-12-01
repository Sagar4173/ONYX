# 🐳 Docker Deployment - ONYX Platform

## Overview

Deploy ONYX using Docker for self-hosted environments.

---

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

---

## 🚀 Quick Start

### Development

```bash
cd deployment/docker
docker-compose up -d
```

### Production

```bash
cd deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

---

## ⚙️ Configuration

### 1. Create Environment File

```bash
cp ../env/.env.example .env
```

### 2. Edit Configuration

```bash
nano .env
```

Required variables:

```env
MONGODB_URI=mongodb://mongodb:27017/onyx
SECRET_KEY=your-super-secret-key-change-this
ENVIRONMENT=production
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                   Nginx                      │
│              (Reverse Proxy)                 │
│                Port: 80/443                  │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│   Frontend    │   │   Backend     │
│   (Vite)      │   │   (FastAPI)   │
│   Port: 3000  │   │   Port: 8000  │
└───────────────┘   └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   MongoDB     │
                    │   Port: 27017 │
                    └───────────────┘
```

---

## 📁 Files

| File                      | Purpose                     |
| ------------------------- | --------------------------- |
| `docker-compose.yml`      | Development setup           |
| `docker-compose.prod.yml` | Production setup with Nginx |
| `Dockerfile.frontend`     | Frontend container build    |
| `Dockerfile.backend`      | Backend container build     |
| `nginx.conf`              | Nginx reverse proxy config  |

---

## 🔧 Commands

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
docker-compose logs -f backend  # Specific service
```

### Stop Services

```bash
docker-compose down
```

### Rebuild

```bash
docker-compose up -d --build
```

### Check Status

```bash
docker-compose ps
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 🔐 SSL/HTTPS (Production)

### Option 1: Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Option 2: Cloudflare SSL

1. Add domain to Cloudflare
2. Enable "Full (strict)" SSL mode
3. Point DNS to your server

---

## 🔧 Troubleshooting

### Container Won't Start

```bash
docker-compose logs backend
docker-compose logs frontend
```

### MongoDB Connection Failed

- Check if MongoDB container is running: `docker-compose ps`
- Verify connection string uses container name: `mongodb://mongodb:27017/onyx`

### Port Already in Use

```bash
# Find process using port
netstat -tulpn | grep :8000
# Or change port in docker-compose.yml
```

### Out of Memory

```bash
# Check memory usage
docker stats
# Increase Docker memory limit in Docker Desktop settings
```

---

## 📊 Monitoring

### Built-in

- Health endpoint: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### With Prometheus/Grafana (Optional)

Add to `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
```
