# 🌐 Vercel Deployment - ONYX Frontend

## Overview

The ONYX frontend is deployed on Vercel for fast, global CDN delivery.

**Live URL**: https://onyx-platform.vercel.app

---

## 📋 Prerequisites

- GitHub account connected to Vercel
- Vercel account (free tier works)

---

## 🚀 Deployment Steps

### 1. Connect Repository

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import `Sagar4173/ONYX` from GitHub
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### 2. Set Environment Variables

In Vercel Dashboard → Settings → Environment Variables:

| Variable        | Value                                        | Environment |
| --------------- | -------------------------------------------- | ----------- |
| `VITE_API_URL`  | `https://onyx-backend-dt4o.onrender.com/api` | Production  |
| `VITE_WS_URL`   | `wss://onyx-backend-dt4o.onrender.com`       | Production  |
| `VITE_APP_NAME` | `ONYX`                                       | All         |

### 3. Deploy

Click **Deploy** - Vercel will automatically build and deploy.

---

## ⚙️ Configuration

The configuration file is located at `frontend/vercel.json` (required location for Vercel).

### Key Settings:

### API Rewrites

Routes `/api/*` requests to the Render backend:

```json
{
  "source": "/api/(.*)",
  "destination": "https://onyx-backend-dt4o.onrender.com/api/$1"
}
```

### Security Headers

```json
{
  "key": "X-Content-Type-Options",
  "value": "nosniff"
},
{
  "key": "X-Frame-Options",
  "value": "DENY"
},
{
  "key": "X-XSS-Protection",
  "value": "1; mode=block"
}
```

### SPA Routing

All routes fallback to `index.html` for React Router:

```json
{
  "source": "/((?!api/|webhook/|health).*)",
  "destination": "/index.html"
}
```

---

## 🔄 Auto-Deployment

Vercel automatically deploys when you push to:

- `master` branch → Production deployment
- Other branches → Preview deployment

---

## 🔧 Troubleshooting

### Build Fails

- Check Node.js version (use 18.x or 20.x)
- Verify all dependencies in `package.json`
- Check build logs for errors

### API Calls Fail

- Verify `VITE_API_URL` is set correctly
- Check CORS settings on backend
- Ensure backend is running

### Blank Page

- Check browser console for errors
- Verify routes in `vercel.json`
- Check if `dist/index.html` exists after build

---

## 📊 Monitoring

- **Deployments**: Vercel Dashboard → Deployments
- **Analytics**: Vercel Dashboard → Analytics
- **Logs**: Vercel Dashboard → Logs (Runtime logs)
- **Functions**: Vercel Dashboard → Functions (if using serverless)
