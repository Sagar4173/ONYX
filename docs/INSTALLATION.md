# Installation Guide

## Prerequisites

- Python 3.13+
- Node.js 22+
- MongoDB 7.0+ (local, Atlas, or Docker)
- Git

---

## Local Development Setup

### 1. Clone

```bash
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Database

**Option A: Local MongoDB** - Install MongoDB 7+ and start the service.  
**Option B: Docker** - `docker run -d -p 27017:27017 mongo:7`  
**Option C: MongoDB Atlas** - Create free cluster and use connection string.

### 5. Environment Variables

Key variables in `backend/.env`:

```env
# Required
MONGODB_URI=mongodb://localhost:27017/onyx
SECRET_KEY=your-32-char-min-secret-key

# AI (at least one)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
SENTRY_DSN=https://...@o....ingest.sentry.io/...
```

Full list: see `.env.example`

### 6. Start

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Frontend:** http://localhost:5173  
**API Docs:** http://localhost:8000/docs

---

## Docker Deployment

### Prerequisites

- Docker 24+ and Docker Compose 2+

### Quick Start

```bash
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX
cp .env.example .env
# Edit .env with required values
docker compose up -d
```

Services:

| Service | Port | URL |
|---|---|---|
| Frontend | 80 | http://localhost |
| Backend | 8000 | http://localhost:8000 |
| API Docs | - | http://localhost:8000/docs |
| MongoDB | 27017 | Internal |

### Verify

```bash
curl http://localhost:8000/health
```

---

## Verification

```bash
# Run backend tests
cd backend
python -m pytest tests/ -q

# Run frontend tests
cd frontend
npm test

# Frontend build
npm run build
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Backend won't start | Check Python 3.13+ and `pip install -r requirements.txt` |
| MongoDB connection | Verify `MONGODB_URI` and MongoDB is running |
| Frontend build fails | Delete `node_modules`, re-run `npm install` |
| Port conflicts | Change `PORT` in `.env` or `vite.config.js` |
