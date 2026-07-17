# 📊 ONYX Project Status

> **Last Updated**: December 2025  
> **Version**: 1.0.0  
> **Status**: Production Ready ✅

---

## 🎯 Mission: Beat GHAS & Snyk

**ONYX** is built to be a **superior alternative** to GitHub Advanced Security (GHAS) and Snyk. Our goal is to provide **better features at lower cost** with **AI-powered intelligence** that competitors lack.

### Why Users Choose ONYX Over Competitors

| Feature                    | ONYX ✅                    | GHAS           | Snyk               |
| -------------------------- | -------------------------- | -------------- | ------------------ |
| **AI-Powered Remediation** | ✅ GPT-4 + Gemini          | ❌ None        | ⚠️ Basic           |
| **Multi-AI Provider**      | ✅ OpenAI + Google         | ❌ None        | ❌ None            |
| **Unified Dashboard**      | ✅ All scanners in one     | ⚠️ GitHub only | ⚠️ Fragmented      |
| **Custom Rule Engine**     | ✅ Full customization      | ⚠️ Limited     | ⚠️ Limited         |
| **Self-Hosted Option**     | ✅ Full control            | ❌ SaaS only   | ⚠️ Enterprise only |
| **Cost**                   | ✅ Open Source             | 💰 $49/user/mo | 💰 $52/user/mo     |
| **Real-time WebSocket**    | ✅ Live progress           | ❌ Polling     | ❌ Polling         |
| **Multi-SCM Support**      | ✅ GitHub+GitLab+Bitbucket | ❌ GitHub only | ✅ Multi-SCM       |
| **SBOM Generation**        | ✅ SPDX + CycloneDX        | ⚠️ Basic       | ✅ Yes             |
| **Compliance Frameworks**  | ✅ 9 frameworks            | ⚠️ Limited     | ⚠️ Enterprise      |

### Our Competitive Advantages

1. **🤖 AI-First Approach** - GPT-4 + Gemini for intelligent vulnerability analysis (GHAS/Snyk have NO AI)
2. **💰 Zero Cost** - Open source vs $49-52/user/month
3. **🔧 Full Customization** - Custom rules, policies, and integrations
4. **📊 Unified Experience** - All security tools in one dashboard
5. **⚡ Real-time Feedback** - WebSocket-based live scan progress
6. **🏢 Self-Hosted** - Complete data sovereignty

---

## 🚀 Live Deployment

| Environment | Platform     | Status  |
| ----------- | ------------ | ------- |
| Frontend    | AWS          | ✅ Live |
| Backend     | AWS          | ✅ Live |
| Database    | MongoDB Atlas| ✅ Live |

---

## ✅ Completed Features

### 🔐 Authentication & Authorization

- [x] JWT-based authentication (access + refresh tokens)
- [x] User registration with email verification
- [x] Password reset via email
- [x] Role-based access control (Admin, Security Manager, Developer, Viewer)
- [x] Session management
- [x] Account lockout after failed attempts

### 👥 User Management

- [x] User CRUD operations
- [x] Profile management with avatar upload
- [x] Role assignment
- [x] User status management (Active, Inactive, Suspended)
- [x] Audit logging for user actions

### 📁 Project Management

- [x] Create/Edit/Delete projects
- [x] Git repository integration (GitHub, GitLab, Bitbucket)
- [x] Project categories and tags
- [x] Project-level scan configuration
- [x] Team collaboration (multi-user access)

### 🔍 Security Scanning

#### Core Scanners (Built-in, Always Available)

- [x] **Semgrep** - Static Application Security Testing (SAST)
- [x] **Bandit** - Python security analysis
- [x] **Safety** - Python dependency vulnerabilities
- [x] **GitLeaks/detect-secrets** - Secret detection

#### Optional Scanners (Require External Installation)

- [ ] **Trivy** - Container & dependency scanning (requires Trivy CLI)
- [ ] **ZAP** - Dynamic Application Security Testing (requires OWASP ZAP daemon)
- [ ] **Nuclei** - Vulnerability scanning (requires Nuclei CLI)
- [ ] **CodeQL** - Advanced SAST (requires CodeQL CLI)
- [ ] **Checkov** - Infrastructure as Code scanning
- [ ] **Lynis** - Infrastructure auditing

> ℹ️ Optional scanners gracefully degrade when not installed. Set `ENABLE_*=true` environment variables when tools are available.

#### Scanning Infrastructure

- [x] Real-time scan progress via WebSocket
- [x] Scan history and comparison
- [x] Centralized Service Registry
- [x] Graceful degradation for missing tools

### 🤖 AI-Powered Analysis

- [x] **OpenAI GPT-4** integration
- [x] **Google Gemini** integration (primary)
- [x] Vulnerability explanation and risk assessment
- [x] Automated remediation suggestions
- [x] Code fix generation
- [x] False positive detection

### 📊 Reporting & Analytics

- [x] Unified 6-tab security reports
- [x] PDF report generation
- [x] Compliance mapping (OWASP, NIST, ISO27001, PCI-DSS)
- [x] Security score calculation
- [x] Trend analysis dashboard
- [x] Severity breakdown charts

### 🏢 Enterprise Features

- [x] **Admin Dashboard** - Comprehensive system management for administrators
- [x] System-wide statistics and monitoring
- [x] User management with role/status controls from admin panel
- [x] Project oversight across all users
- [x] Activity monitoring and audit trail
- [x] Admin-protected routes with access control
- [x] Audit logging with integrity verification
- [x] Data retention policies
- [x] Data isolation per user/project
- [x] Advanced compliance reporting (9 frameworks)
- [x] Webhook integrations
- [x] Email notifications (Gmail SMTP + Brevo API)
- [x] Real-time WebSocket notifications

### 🛡️ Advanced Security

- [x] Custom rule engine
- [x] Rule template library
- [x] Baseline scanning with drift detection
- [x] Policy-as-Code enforcement
- [x] Security boundary protection
- [x] SBOM generation (SPDX, CycloneDX)

---

## 🔧 Technical Stack

### Backend

| Component | Technology        | Version           |
| --------- | ----------------- | ----------------- |
| Framework | FastAPI           | Latest            |
| Database  | MongoDB Atlas     | 7.0+              |
| ODM       | Beanie            | Latest            |
| Auth      | JWT (PyJWT)       | -                 |
| AI        | OpenAI / Gemini   | GPT-4 / 1.5-flash |
| Email     | SMTP (Gmail)      | -                 |
| WebSocket | FastAPI WebSocket | -                 |

### Frontend

| Component     | Technology   | Version |
| ------------- | ------------ | ------- |
| Framework     | React        | 18      |
| Build Tool    | Vite         | 5.4     |
| Styling       | Tailwind CSS | 3.3     |
| State         | React Query  | 5.0     |
| Router        | React Router | 6.20    |
| Charts        | Recharts     | 2.8     |
| UI Components | Headless UI  | 1.7     |

### Infrastructure

| Component        | Technology    |
| ---------------- | ------------- |
| Frontend Hosting | AWS           |
| Backend Hosting  | AWS           |
| Database         | MongoDB Atlas |
| Version Control  | GitHub        |

---

## 📁 Project Structure

```
ONYX/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── config.py           # Configuration
│   ├── database.py         # MongoDB connection
│   ├── models/             # Database models
│   ├── routes/             # API endpoints (14 files)
│   ├── services/           # Business logic (9 modules)
│   │   ├── ai/             # AI processors
│   │   ├── analytics/      # Metrics & audit
│   │   ├── auth/           # Authentication
│   │   ├── compliance/     # Compliance engines
│   │   ├── infrastructure/ # Core services
│   │   ├── notifications/  # Email & WebSocket
│   │   ├── rules/          # Rule engine
│   │   ├── scanning/       # Security scanners
│   │   └── security/       # Security features
│   ├── configs/            # Scanner configs
│   └── data/               # Runtime data
├── frontend/
│   ├── src/
│   │   ├── components/     # React components (9 modules)
│   │   ├── layouts/        # Layout components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── styles/         # Theme & styling
│   └── public/             # Static assets
└── docs/                   # Documentation
```

---

## 📈 Metrics

| Metric                | Count          |
| --------------------- | -------------- |
| Backend Services      | 45+ files      |
| API Endpoints         | 100+ routes    |
| Frontend Components   | 30+ components |
| Security Scanners     | 6 integrated   |
| Compliance Frameworks | 9 supported    |
| Lines of Code         | ~50,000+       |

---

## 🆚 Feature Comparison Deep Dive

### vs GitHub Advanced Security (GHAS)

| Category             | ONYX Advantage                                         |
| -------------------- | ------------------------------------------------------ |
| **Secret Scanning**  | GitLeaks + custom patterns (GHAS: basic patterns only) |
| **Code Scanning**    | Semgrep + Bandit + AI remediation (GHAS: CodeQL only)  |
| **Dependency Scan**  | Trivy + Safety + SBOM (GHAS: Dependabot only)          |
| **AI Analysis**      | Full GPT-4/Gemini integration (GHAS: None)             |
| **Platform Lock-in** | Works with any Git provider (GHAS: GitHub only)        |
| **Pricing**          | Free & Open Source (GHAS: $49/user/month)              |

### vs Snyk

| Category              | ONYX Advantage                                                |
| --------------------- | ------------------------------------------------------------- |
| **AI Remediation**    | Intelligent code fixes with context (Snyk: Template-based)    |
| **Unified Dashboard** | All tools in one view (Snyk: Separate products)               |
| **Custom Rules**      | Full rule engine with templates (Snyk: Limited customization) |
| **Self-Hosting**      | Free self-hosted (Snyk: Enterprise tier only)                 |
| **Real-time Updates** | WebSocket live progress (Snyk: Polling-based)                 |
| **Pricing**           | Free & Open Source (Snyk: $52/developer/month)                |

---

## 🔗 Quick Links

- [Installation Guide](INSTALLATION.md)
- [API Documentation](API.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Development Roadmap](ROADMAP.md)
- [Contributing Guidelines](CONTRIBUTING.md)
