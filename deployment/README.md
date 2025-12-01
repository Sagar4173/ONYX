# 🚀 ONYX Deployment Guide

## Deployment Structure

This folder contains all deployment configurations for the ONYX Security Intelligence Platform.

```
deployment/
├── README.md              # This file - deployment overview
├── vercel/               # Frontend deployment (Vercel)
│   ├── vercel.json       # Vercel configuration
│   └── README.md         # Frontend deployment guide
├── render/               # Backend deployment (Render)
│   ├── render.yaml       # Render Blueprint
│   └── README.md         # Backend deployment guide
├── docker/               # Docker deployment
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── README.md         # Docker deployment guide
└── env/                  # Environment templates
    ├── .env.example
    ├── .env.frontend.example
    └── .env.backend.example
```

---

## 🌐 Live Deployments

| Service      | Platform | URL                                           |
| ------------ | -------- | --------------------------------------------- |
| Frontend     | Vercel   | https://onyx-platform.vercel.app              |
| Backend      | Render   | https://onyx-backend-dt4o.onrender.com        |
| API Docs     | Render   | https://onyx-backend-dt4o.onrender.com/docs   |
| Health Check | Render   | https://onyx-backend-dt4o.onrender.com/health |

---

## 🚀 Quick Start

### Option 1: Vercel + Render (Recommended - Free Tier)

**Frontend (Vercel):**

1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Deploy automatically

**Backend (Render):**

1. Connect GitHub repo to Render
2. Set root directory to `backend`
3. Configure environment variables
4. Deploy

See detailed guides in `vercel/` and `render/` folders.

### Option 2: Docker (Self-Hosted)

```bash
cd deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

See detailed guide in `docker/` folder.

---

## 🔐 Environment Variables

### Frontend (.env)

```env
VITE_API_URL=https://onyx-backend-dt4o.onrender.com/api
VITE_WS_URL=wss://onyx-backend-dt4o.onrender.com
VITE_APP_NAME=ONYX
```

### Backend (.env)

```env
MONGODB_URI=mongodb+srv://...
SECRET_KEY=your-secret-key
ENVIRONMENT=production
ALLOWED_ORIGINS=https://onyx-platform.vercel.app
OPENAI_API_KEY=sk-...  # Optional
GEMINI_API_KEY=...     # Optional
```

See `env/` folder for complete templates.

---

## 📋 Deployment Checklist

- [ ] MongoDB Atlas configured with network access
- [ ] Backend environment variables set
- [ ] Frontend environment variables set
- [ ] CORS origins configured correctly
- [ ] Health endpoint responding
- [ ] API docs accessible
- [ ] Frontend can connect to backend

---

## 🆘 Troubleshooting

| Issue                    | Solution                                       |
| ------------------------ | ---------------------------------------------- |
| CORS errors              | Add frontend URL to `ALLOWED_ORIGINS`          |
| MongoDB connection fails | Check Atlas network access (allow 0.0.0.0/0)   |
| Backend cold starts      | Use UptimeRobot to ping `/health` every 14 min |
| Build fails              | Check logs for dependency conflicts            |

For detailed troubleshooting, see individual deployment guides.
