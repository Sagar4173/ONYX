# 🔌 Render Deployment - ONYX Backend

## Overview

The ONYX backend (FastAPI) is deployed on Render.

**Live URL**: https://onyx-backend-dt4o.onrender.com

---

## 📋 Prerequisites

- GitHub account connected to Render
- Render account (free tier works)
- MongoDB Atlas database

---

## 🚀 Deployment Steps

### Option 1: Manual Setup (Recommended)

1. Go to [dashboard.render.com](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your GitHub repo: `Sagar4173/ONYX`
4. Configure:

| Setting            | Value                                                                     |
| ------------------ | ------------------------------------------------------------------------- |
| **Name**           | `onyx-backend`                                                            |
| **Root Directory** | `backend`                                                                 |
| **Runtime**        | Python 3                                                                  |
| **Build Command**  | `pip install -r requirements.txt`                                         |
| **Start Command**  | `gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT` |
| **Plan**           | Free                                                                      |

### Option 2: Using Blueprint

1. Go to [dashboard.render.com](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` and configures everything

---

## 🔑 Environment Variables (Required)

Set in Render Dashboard → Your Service → **Environment**:

| Variable            | Value                                                    | Required |
| ------------------- | -------------------------------------------------------- | -------- |
| `MONGODB_URI`       | Your MongoDB Atlas connection string                     | ✅ Yes   |
| `SECRET_KEY`        | Secure random string (auto-generated)                    | ✅ Yes   |
| `ENVIRONMENT`       | `production`                                             | ✅ Yes   |
| `ALLOWED_ORIGINS`   | `https://onyx-platform.vercel.app,http://localhost:5173` | ✅ Yes   |
| `OPENAI_API_KEY`    | Your OpenAI API key                                      | Optional |
| `GEMINI_API_KEY`    | Your Google Gemini API key                               | Optional |
| `GOOGLE_AI_API_KEY` | Your Google AI API key                                   | Optional |

### MongoDB Atlas Setup

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster
3. Create database user
4. Get connection string: `mongodb+srv://user:pass@cluster.xxx.mongodb.net/onyx`
5. **Important**: Add `0.0.0.0/0` to Network Access (allows Render to connect)

---

## ⚙️ Configuration

The `render.yaml` blueprint configures:

```yaml
services:
  - type: web
    name: onyx-backend
    runtime: python
    region: oregon
    plan: free
    branch: master
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
    healthCheckPath: /health
```

---

## ⚠️ Free Tier Limitations

| Limitation   | Impact                                | Solution                          |
| ------------ | ------------------------------------- | --------------------------------- |
| Cold starts  | Service sleeps after 15min inactivity | Use UptimeRobot to ping `/health` |
| Spin-up time | 30-60 seconds on first request        | Keep-alive ping every 14 min      |
| Memory       | 512MB RAM                             | Sufficient for normal use         |
| Bandwidth    | 100GB/month                           | Sufficient for most projects      |

### Keep-Alive Setup (Recommended)

1. Sign up at [uptimerobot.com](https://uptimerobot.com/)
2. Add new monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://onyx-backend-dt4o.onrender.com/health`
   - **Interval**: 14 minutes

---

## 🔧 Troubleshooting

### Build Fails

```bash
# Check Render logs for errors
# Common issues:
# - Missing dependencies in requirements.txt
# - Python version mismatch
# - Syntax errors in code
```

### MongoDB Connection Issues

- Verify `MONGODB_URI` format is correct
- Check MongoDB Atlas Network Access allows `0.0.0.0/0`
- Ensure database user has read/write permissions

### CORS Errors

- Add your frontend URL to `ALLOWED_ORIGINS`
- Format: comma-separated URLs without trailing slashes
- Example: `https://onyx-platform.vercel.app,http://localhost:5173`

### 502/503 Errors

- Check if service is sleeping (cold start)
- Review logs for application crashes
- Verify start command is correct

---

## 📊 Monitoring

| Feature  | Location                                      |
| -------- | --------------------------------------------- |
| Logs     | Render Dashboard → Your Service → Logs        |
| Metrics  | Render Dashboard → Your Service → Metrics     |
| Health   | https://onyx-backend-dt4o.onrender.com/health |
| API Docs | https://onyx-backend-dt4o.onrender.com/docs   |

---

## 🔄 Auto-Deployment

Render automatically deploys when you push to:

- `master` branch → Production deployment

To disable auto-deploy:

1. Go to Settings → Build & Deploy
2. Toggle off "Auto-Deploy"
