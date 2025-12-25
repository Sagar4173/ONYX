# ONYX Backend - Fly.io Deployment Guide

## 🚀 Quick Deploy to Fly.io (Free Tier)

### Prerequisites

1. **Install Fly CLI:**

   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

   # macOS/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up & Login:**
   ```bash
   fly auth signup    # Create account (free)
   fly auth login     # Login to existing account
   ```

---

## 📦 Deployment Steps

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Launch Your App

```bash
fly launch --no-deploy
```

- When prompted, choose:
  - App name: `onyx-backend` (or your preferred name)
  - Region: Choose closest to your users (e.g., `sjc` for San Jose)
  - Don't set up PostgreSQL or Redis (we use MongoDB Atlas)

### Step 3: Set Environment Variables (Secrets)

```bash
# Required
fly secrets set MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/onyx?retryWrites=true&w=majority"
fly secrets set SECRET_KEY="your-secure-random-secret-key-here"
fly secrets set ALLOWED_ORIGINS="https://your-frontend.vercel.app,http://localhost:5173"

# Optional - AI Features
fly secrets set GEMINI_API_KEY="your-gemini-api-key"
fly secrets set OPENAI_API_KEY="your-openai-api-key"

# Optional - Notifications
fly secrets set SLACK_WEBHOOK_URL="your-slack-webhook-url"
```

### Step 4: Deploy

```bash
fly deploy
```

### Step 5: Verify Deployment

```bash
# Check app status
fly status

# View logs
fly logs

# Open your app
fly open
```

---

## 🔧 Configuration

### Update Frontend Environment Variables (Vercel)

After deployment, get your Fly.io URL:

```bash
fly status
# Look for: Hostname = onyx-backend.fly.dev
```

Update these in Vercel Dashboard → Your Project → Settings → Environment Variables:

```
VITE_API_URL=https://onyx-backend.fly.dev/api
VITE_API_BASE_URL=https://onyx-backend.fly.dev/api
VITE_WS_URL=wss://onyx-backend.fly.dev
VITE_WEBSOCKET_URL=wss://onyx-backend.fly.dev
```

---

## 📊 Pricing & Resources

This deployment uses **1GB RAM** for full features (ML, scanning, etc.)

| Resource  | Your Config | Cost        |
| --------- | ----------- | ----------- |
| Memory    | 1GB         | ~$3-5/month |
| CPU       | Shared      | Included    |
| Bandwidth | 160GB/month | Free        |

**Note:** Fly.io charges based on usage. With auto_stop_machines=true,
you only pay when the app is running. Estimated cost: **$3-5/month**.

---

## 🛠️ Useful Commands

```bash
# View app info
fly info

# View logs (streaming)
fly logs

# SSH into container
fly ssh console

# Scale memory
fly scale memory 1024    # 1GB

# Restart app
fly apps restart onyx-backend

# Check secrets
fly secrets list

# Update a secret
fly secrets set KEY="new-value"

# View metrics
fly dashboard
```

---

## ⚠️ Troubleshooting

### Memory Issues

If you see "out of memory" errors:

1. Check current memory: `fly scale show`
2. Increase memory: `fly scale memory 1024`

### Cold Starts

Free tier machines stop when idle. First request may take 5-10 seconds.
To keep alive (uses more free tier hours):

```bash
# In fly.toml, set:
# min_machines_running = 1
```

### MongoDB Connection Issues

1. Ensure MongoDB Atlas Network Access allows `0.0.0.0/0`
2. Verify connection string: `fly secrets list`

### CORS Errors

Update ALLOWED_ORIGINS:

```bash
fly secrets set ALLOWED_ORIGINS="https://your-frontend.vercel.app"
```

---

## 🔄 Continuous Deployment

### GitHub Actions (Optional)

Create `.github/workflows/fly-deploy.yml`:

```yaml
name: Fly Deploy
on:
  push:
    branches:
      - master
    paths:
      - "backend/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        working-directory: backend
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Get your deploy token:

```bash
fly tokens create deploy -x 999999h
```

Add it to GitHub → Repository → Settings → Secrets → `FLY_API_TOKEN`

---

## 📈 Monitoring

- **Dashboard:** https://fly.io/dashboard
- **Logs:** `fly logs` or dashboard
- **Metrics:** `fly dashboard` → Metrics tab
- **Health Check:** `https://your-app.fly.dev/health`
