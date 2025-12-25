# ONYX Backend - Render Deployment Guide

## 🚀 Quick Deploy to Render

### Option 1: One-Click Deploy (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your GitHub repo: `your-username/ONYX`
4. Configure:
   - **Name**: `onyx-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
   - **Plan**: Free (or Starter for better performance)

### Option 2: Using Blueprint (render.yaml)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` and configure everything

---

## 🔑 Environment Variables (Required)

Set these in Render Dashboard → Your Service → **Environment**:

| Variable          | Description                       | Required |
| ----------------- | --------------------------------- | -------- |
| `MONGODB_URI`     | MongoDB Atlas connection string   | ✅ Yes   |
| `SECRET_KEY`      | JWT secret (auto-generate or set) | ✅ Yes   |
| `ENVIRONMENT`     | `production`                      | ✅ Yes   |
| `ALLOWED_ORIGINS` | Frontend URL(s), comma-separated  | ✅ Yes   |
| `OPENAI_API_KEY`  | OpenAI API key (for AI features)  | Optional |
| `GEMINI_API_KEY`  | Google Gemini API key             | Optional |

**Example `ALLOWED_ORIGINS`:**

```
https://your-frontend.vercel.app,http://localhost:5173
```

---

## 📋 After Deployment

1. **Get your Render URL**: It will be like `https://your-service-name.onrender.com`

2. **Update Frontend Environment Variables** (in Vercel):

   ```
   VITE_API_URL=https://your-service-name.onrender.com/api
   VITE_API_BASE_URL=https://your-service-name.onrender.com/api
   VITE_WS_URL=wss://your-service-name.onrender.com
   VITE_WEBSOCKET_URL=wss://your-service-name.onrender.com
   ```

3. **Test Health Endpoint**: Visit `https://your-service-name.onrender.com/health`

---

## ⚠️ Free Tier Notes

- **Cold Starts**: Free tier services sleep after 15 minutes of inactivity
- **Spin-up Time**: ~30-60 seconds on first request after sleeping
- **Tip**: Use [UptimeRobot](https://uptimerobot.com/) to ping `/health` every 14 minutes

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
- **Health**: `https://your-service-name.onrender.com/health`
