# ONYX Backend - Render Deployment Guide

## 🚀 Quick Deploy to Render

### Option 1: One-Click Deploy (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your GitHub repo: `Sagar4173/ONYX`
4. Configure:
   - **Name**: `onyx-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
   - **Plan**: Free

### Option 2: Using Blueprint (render.yaml)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` and configure everything

---

## 🔑 Environment Variables (Required)

Set these in Render Dashboard → Your Service → **Environment**:

| Variable          | Value                                                                                                         | Required |
| ----------------- | ------------------------------------------------------------------------------------------------------------- | -------- |
| `MONGODB_URI`     | `mongodb+srv://GHOST4173:Ghost%405555@onyx.ueuztsg.mongodb.net/onyx?retryWrites=true&w=majority&appName=ONYX` | ✅ Yes   |
| `SECRET_KEY`      | (auto-generated or set your own secure key)                                                                   | ✅ Yes   |
| `ENVIRONMENT`     | `production`                                                                                                  | ✅ Yes   |
| `ALLOWED_ORIGINS` | `https://onyx-platform.vercel.app,http://localhost:5173`                                                      | ✅ Yes   |
| `OPENAI_API_KEY`  | Your OpenAI key                                                                                               | Optional |
| `GEMINI_API_KEY`  | Your Google Gemini AI key                                                                                     | Optional |

---

## 📋 After Deployment

1. **Get your Render URL**: It will be like `https://onyx-backend.onrender.com`

2. **Update Frontend**:

   - Go to Vercel Dashboard → ONYX Frontend → Settings → Environment Variables
   - Update `VITE_API_URL` to `https://onyx-backend.onrender.com/api`
   - Update `VITE_WS_URL` to `wss://onyx-backend.onrender.com`
   - Redeploy frontend

3. **Test Health Endpoint**: Visit `https://onyx-backend.onrender.com/health`

---

## ⚠️ Free Tier Notes

- **Cold Starts**: Free tier services sleep after 15 minutes of inactivity
- **Spin-up Time**: ~30-60 seconds on first request after sleeping
- **Tip**: Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your `/health` endpoint every 14 minutes to keep it awake

---

## 🔧 Troubleshooting

### Build Fails

- Check Render logs for errors
- Ensure `requirements.txt` has no version conflicts

### MongoDB Connection Issues

- Verify `MONGODB_URI` is correctly set
- Ensure MongoDB Atlas allows connections from `0.0.0.0/0` (Network Access)

### CORS Errors

- Add your frontend URL to `ALLOWED_ORIGINS`
- Format: comma-separated URLs without trailing slashes

---

## 📊 Monitoring

- **Logs**: Render Dashboard → Your Service → Logs
- **Metrics**: Render Dashboard → Your Service → Metrics
- **Health**: `https://onyx-backend.onrender.com/health`
