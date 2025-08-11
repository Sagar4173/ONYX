# 🚀 Deployment Guide - SecureDevOps AI Platform

## 📋 Current Status

✅ **Frontend**: Deployed on Vercel  
🔄 **Backend**: Ready for Railway deployment  
🎯 **Target**: Full-stack deployment with proper API connectivity

## 🌐 Frontend Deployment (Vercel) - ✅ COMPLETED

**URL**: https://secure-dev-ops-ai-platform.vercel.app/

### Configuration:

- **Framework**: Other
- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Output Directory**: `dist`

### Environment Variables (Vercel):

```
VITE_DEMO_MODE=true
NODE_ENV=production
```

## 🖥️ Backend Deployment (Railway) - 🔄 READY TO DEPLOY

### Step-by-Step Deployment:

#### 1. Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Connect your repository

#### 2. Deploy Backend

1. Click "New Project" → "Deploy from GitHub repo"
2. Select `SecureDevOpsAI-Platform`
3. Railway will auto-detect Python and use our configuration

#### 3. Environment Variables (Railway Dashboard)

Add these in Railway dashboard → Your Service → Variables:

```bash
# Database
MONGODB_URI=mongodb+srv://Ghost4173:Ghost%405555@securedevopsai-db.munpiyz.mongodb.net/securedevops?retryWrites=true&w=majority&appName=SecureDevOpsAI-DB

# Application
SECRET_KEY=85M$$wWl2YR8tS!5aX62cx1$$6dhdSQOWLc+kaxgzYFe4jiCk1aF2CZi3hjeHBox3w
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# CORS - Allow your Vercel frontend
CORS_ORIGINS=https://secure-dev-ops-ai-platform.vercel.app,http://localhost:5173

# OpenAI API (Required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Slack Notifications
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_CHANNEL=#security-alerts
```

#### 4. Custom Domain (Optional)

1. Railway → Settings → Networking → Custom Domain
2. Add domain like `api-secure-devops.railway.app`

## 🔗 Connect Frontend to Backend

After Railway deployment, update Vercel environment variables:

### Vercel Dashboard → Your Project → Settings → Environment Variables:

```bash
# Replace with your actual Railway URL
VITE_API_URL=https://your-railway-app.railway.app/api
VITE_WS_URL=wss://your-railway-app.railway.app
VITE_DEMO_MODE=false
```

## 🧪 Testing Deployment

### Backend Health Check:

```bash
curl https://your-railway-app.railway.app/health
```

### Frontend API Connection:

1. Visit your Vercel app
2. Check browser console for API calls
3. Test scanning functionality

## 🔧 Troubleshooting

### Common Issues:

#### 1. CORS Errors

- Add your Vercel URL to `CORS_ORIGINS` in Railway
- Include both `https://` and `http://` versions

#### 2. Database Connection

- Verify MongoDB URI in Railway environment
- Check Railway logs for connection errors

#### 3. OpenAI API Issues

- Ensure `OPENAI_API_KEY` is set in Railway
- Check API key validity and billing

#### 4. Build Failures

- Check Railway build logs
- Verify `requirements.txt` dependencies

## 📊 Alternative Deployment Options

### Option 1: Railway (Recommended)

- ✅ Easy Python deployment
- ✅ MongoDB support
- ✅ Auto-scaling
- ✅ Custom domains

### Option 2: Render

- ✅ Similar to Railway
- ✅ Good for full-stack apps
- ✅ PostgreSQL included

### Option 3: DigitalOcean App Platform

- ✅ Multiple services support
- ✅ Database integration
- ✅ Good scaling options

## 🎯 Next Steps

1. **Deploy backend on Railway** using the steps above
2. **Get Railway URL** from dashboard
3. **Update Vercel environment variables** with Railway URL
4. **Test full-stack functionality**
5. **Set up monitoring and logging**

## 📞 Support

If you encounter issues:

1. Check Railway logs: Dashboard → Your Service → Logs
2. Check Vercel build logs: Dashboard → Deployments → View Build Logs
3. Verify environment variables are correctly set
4. Test API endpoints individually

---

**Current URLs:**

- **Frontend**: https://secure-dev-ops-ai-platform.vercel.app/
- **Backend**: Deploy on Railway next
