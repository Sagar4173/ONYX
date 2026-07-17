# 👥 ONYX Team Guide

> **Internal Reference Document**  
> **Last Updated**: December 2025  
> **🎯 MISSION: Build a BETTER platform than GitHub Advanced Security (GHAS) & Snyk**

---

## 💡 Why We're Building This

### The Problem with GHAS & Snyk

| Issue                 | GHAS           | Snyk                    | ONYX Solution        |
| --------------------- | -------------- | ----------------------- | -------------------- |
| **Cost**              | $49/user/month | $52/user/month          | ✅ FREE              |
| **AI Analysis**       | ❌ None        | ⚠️ Basic                | ✅ GPT-4 + Gemini    |
| **Platform Lock-in**  | GitHub only    | Multiple but fragmented | ✅ Unified + Any SCM |
| **Custom Rules**      | Limited        | Limited                 | ✅ Full rule engine  |
| **Self-Hosting**      | Impossible     | Enterprise $$$$         | ✅ Free              |
| **Real-time Updates** | Polling        | Polling                 | ✅ WebSocket         |

### Our Competitive Edge

```
🤖 AI-FIRST APPROACH
   - GPT-4 + Gemini for intelligent analysis
   - Auto-remediation suggestions
   - False positive detection
   - Code fix generation

   >>> GHAS and Snyk have NOTHING like this!
```

---

## 🧑‍💻 Team Members & Responsibilities

### Sagar Wavhal - Lead Developer

**GitHub**: [@Sagar4173](https://github.com/Sagar4173)

#### 🎯 Mission: Build AI Features That Competitors Don't Have

#### Primary Responsibilities

- Platform architecture decisions
- Backend API development (FastAPI)
- Frontend development (React)
- **AI integration (OpenAI/Gemini)** ← Our biggest advantage!
- Database design (MongoDB)
- Code review & mentoring

#### Current Focus - Beat Competitors

- [ ] **AI Chat Assistant** - Ask questions about vulnerabilities (GHAS/Snyk don't have this!)
- [ ] **Auto-Fix PRs** - AI generates fix PRs automatically
- [ ] **Intelligent Triage** - AI prioritizes by business impact
- [ ] Performance optimization
- [ ] AI response quality improvement

#### Key Files Owned

```
backend/
├── app.py
├── config.py
├── services/ai/
├── routes/
frontend/
├── src/App.jsx
├── src/services/api.js
```

---

### Piyush More - Security Expert

**GitHub**: [@MorePiyush55](https://github.com/MorePiyush55)

#### 🎯 Mission: Make Our Scanning BETTER Than Snyk's

#### Primary Responsibilities

- Security scanner integration
- Vulnerability assessment rules
- **Compliance framework mapping** ← We support 9 frameworks (more than GHAS!)
- Security testing
- Threat analysis

#### Current Focus - Beat Competitors

- [ ] **Custom rule library** - More rules than Snyk
- [ ] **AI-powered false positive reduction** - Snyk doesn't have this!
- [ ] **Expand compliance** - Add more frameworks than competitors
- [ ] Custom rule development
- [ ] Compliance coverage expansion

#### Key Files Owned

```
backend/
├── services/scanning/
├── services/compliance/
├── services/security/
├── services/rules/
├── configs/
│   ├── custom-semgrep-rules.yaml
│   ├── gitleaks-custom.toml
│   └── compliance_mapping.json
```

---

### Rushikesh Phalke - DevOps Engineer

**GitHub**: [@rushiphalke247](https://github.com/rushiphalke247)

#### 🎯 Mission: Make ONYX FASTER Than Competitors

#### Primary Responsibilities

- Deployment automation
- Infrastructure management
- CI/CD pipelines
- **Performance monitoring** ← Speed is a competitive advantage!
- Server administration

#### Current Focus - Beat Competitors

- [ ] **Scan speed optimization** - Target: faster than Snyk
- [ ] **Real-time performance** - WebSocket already beats their polling
- [ ] **Zero-downtime deploys** - Better reliability than competitors
- [ ] AWS infrastructure optimization
- [ ] MongoDB performance
- [ ] Monitoring setup

#### Key Files Owned

```
backend/
├── requirements.txt
frontend/
├── vite.config.js
docs/
├── DEPLOYMENT.md
```

---

## 🔧 Development Setup

### Prerequisites

```bash
# Backend
Python 3.11+
MongoDB (local or Atlas)
Git

# Frontend
Node.js 18+
npm or yarn
```

### Quick Start

```bash
# Clone repository
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX

# Backend setup
cd backend
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt
python main.py

# Frontend setup (new terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Environment Variables

#### Backend (.env)

```env
MONGODB_URI=your-mongodb-uri
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:5173
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
```

#### Frontend (.env)

```env
VITE_API_URL=http://127.0.0.1:8000/api
VITE_WS_URL=ws://127.0.0.1:8000
```

---

## 📂 Codebase Overview

### Backend Structure (FastAPI)

```
backend/
├── app.py              # Main application entry
├── main.py             # Uvicorn runner
├── config.py           # Environment configuration
├── database.py         # MongoDB connection
│
├── models/             # Beanie ODM models
│   ├── user.py         # User model
│   ├── project.py      # Project model
│   └── report.py       # Report model
│
├── routes/             # API endpoints
│   ├── auth.py         # /api/auth/*
│   ├── users.py        # /api/users/*
│   ├── projects.py     # /api/projects/*
│   ├── reports.py      # /api/reports/*
│   ├── security.py     # /api/security/*
│   └── ...
│
├── services/           # Business logic
│   ├── ai/             # AI processors
│   ├── auth/           # Authentication
│   ├── scanning/       # Security scanners
│   ├── compliance/     # Compliance engines
│   └── ...
│
├── configs/            # Configuration files
│   ├── custom-semgrep-rules.yaml
│   └── gitleaks-custom.toml
│
└── data/               # Runtime data storage
```

### Frontend Structure (React)

```
frontend/src/
├── App.jsx             # Main app component
├── main.jsx            # React entry point
│
├── components/         # Reusable components
│   ├── auth/           # Authentication
│   ├── projects/       # Project management
│   ├── reports/        # Report views
│   ├── security/       # Security dashboards
│   └── ...
│
├── layouts/            # Page layouts
│   ├── MainLayout.jsx  # Authenticated layout
│   ├── Sidebar.jsx     # Navigation sidebar
│   └── Header.jsx      # Top header
│
├── pages/              # Page components
│   ├── Dashboard.jsx
│   ├── Analytics.jsx
│   └── Reports.jsx
│
├── services/           # API communication
│   └── api.js          # Axios API client
│
└── styles/             # Styling utilities
```

---

## 🔄 Git Workflow

### Branches

| Branch      | Purpose                    |
| ----------- | -------------------------- |
| `master`    | Production code (deployed) |
| `develop`   | Development staging        |
| `feature/*` | New features               |
| `fix/*`     | Bug fixes                  |
| `hotfix/*`  | Urgent production fixes    |

### Commit Convention

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructure
- test: Tests
- chore: Maintenance

Examples:
feat(auth): add password reset functionality
fix(scanner): resolve timeout issue for large repos
docs(api): update endpoint documentation
```

### Pull Request Process

1. Create feature branch from `develop`
2. Make changes and commit
3. Push branch and create PR
4. Request review from relevant team member
5. Address feedback
6. Merge after approval

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Manual Testing Checklist

- [ ] User registration/login
- [ ] Project creation
- [ ] Security scan execution
- [ ] Report generation
- [ ] PDF export
- [ ] WebSocket notifications

---

## 📞 Communication

### Daily Sync

- Time: 10:00 AM IST
- Duration: 15 minutes
- Focus: Blockers & priorities

### Weekly Review

- Day: Friday
- Duration: 1 hour
- Focus: Progress & planning

### Channels

| Channel            | Purpose                |
| ------------------ | ---------------------- |
| GitHub Issues      | Bug reports & features |
| GitHub Discussions | Technical discussions  |
| WhatsApp Group     | Quick communication    |

---

## 🚨 Incident Response

### If Production is Down

1. Check AWS console for backend/frontend status
2. Check MongoDB Atlas for database issues
3. Notify team immediately
4. Document incident in GitHub Issues

### Rollback Process

```bash
# Use your CI/CD pipeline or AWS console to redeploy the previous version
```

---

## 📚 Resources

### Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [MongoDB Manual](https://www.mongodb.com/docs/manual/)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Security Tools

- [Semgrep Rules](https://semgrep.dev/explore)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [GitLeaks](https://github.com/gitleaks/gitleaks)

### AI APIs

- [OpenAI API](https://platform.openai.com/docs)
- [Google Gemini](https://ai.google.dev/docs)

### Competitor Research

- [GitHub Advanced Security](https://docs.github.com/en/code-security)
- [Snyk Documentation](https://docs.snyk.io/)
- [GHAS Pricing](https://github.com/pricing) - $49/user/month
- [Snyk Pricing](https://snyk.io/plans/) - $52/developer/month

---

## 🏆 Competitive Battle Plan

### What We Have That GHAS Doesn't

| Feature                    | Status  | Impact                      |
| -------------------------- | ------- | --------------------------- |
| AI Analysis (GPT-4/Gemini) | ✅ Live | 🔥 HUGE - They have NOTHING |
| Multi-SCM Support          | ✅ Live | Users not locked to GitHub  |
| Custom Rule Engine         | ✅ Live | Full flexibility            |
| Real-time WebSocket        | ✅ Live | Better UX than polling      |
| Self-Hosted Option         | ✅ Live | Data sovereignty            |
| Free & Open Source         | ✅ Live | $0 vs $49/user/month        |

### What We Have That Snyk Doesn't

| Feature                    | Status  | Impact                         |
| -------------------------- | ------- | ------------------------------ |
| AI Analysis (GPT-4/Gemini) | ✅ Live | 🔥 HUGE - They only have basic |
| Unified Dashboard          | ✅ Live | All tools in one place         |
| Free Self-Hosting          | ✅ Live | Snyk charges $$$ for this      |
| Real-time WebSocket        | ✅ Live | Better UX than polling         |
| Custom Rules               | ✅ Live | More flexibility               |
| Free & Open Source         | ✅ Live | $0 vs $52/user/month           |

### Features to Build to CRUSH Competition

| Priority | Feature                      | Why It Wins                                        |
| -------- | ---------------------------- | -------------------------------------------------- |
| 🔴 P0    | **AI Chat Assistant**        | Ask questions about vulns - NO competitor has this |
| 🔴 P0    | **Auto-Fix PRs**             | AI creates fix PRs automatically - Game changer    |
| 🟡 P1    | **VS Code Extension**        | Security in the IDE - Better developer experience  |
| 🟡 P1    | **Slack/Teams Alerts**       | Real-time notifications where teams work           |
| 🟢 P2    | **Vulnerability Prediction** | ML predicts where bugs will appear - UNIQUE        |

### Team Weekly Goals

```
Every sprint, ask yourself:

1. "Does this feature make us better than GHAS?"
2. "Does this feature make us better than Snyk?"
3. "Would a user choose ONYX over competitors because of this?"

If the answer is YES to any - prioritize it! 🚀
```

### Competitive Metrics to Track

| Metric               | Our Goal           | GHAS     | Snyk     |
| -------------------- | ------------------ | -------- | -------- |
| Scan Speed           | <30s for 10MB repo | ~1 min   | ~45s     |
| AI Response Time     | <5s                | N/A      | N/A      |
| Supported Frameworks | 9+ compliance      | 3-4      | 5-6      |
| Custom Rules         | Unlimited          | Limited  | Limited  |
| Price                | $0                 | $49/user | $52/user |
