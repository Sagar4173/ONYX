# 🔮 ONYX - Security Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)](https://www.mongodb.com/)
[![AI Powered](https://img.shields.io/badge/AI-GPT--4%20%7C%20Gemini-orange.svg)](https://openai.com/)

> **The Open Source Alternative to GitHub Advanced Security & Snyk**  
> _AI-Powered Security Scanning • Free & Self-Hosted • Enterprise-Ready_

---

## 🚀 Live Demo

| Service            | URL                                                                                |
| ------------------ | ---------------------------------------------------------------------------------- |
| 🌐 **Frontend**    | [onyx-platform.vercel.app](https://onyx-platform.vercel.app)                       |
| 🔌 **Backend API** | [onyx-backend-dt4o.onrender.com](https://onyx-backend-dt4o.onrender.com)           |
| 📚 **API Docs**    | [onyx-backend-dt4o.onrender.com/docs](https://onyx-backend-dt4o.onrender.com/docs) |

---

## 🏆 Why ONYX Over GHAS & Snyk?

| Feature               | ONYX                         | GHAS           | Snyk               |
| --------------------- | ---------------------------- | -------------- | ------------------ |
| **AI Analysis**       | ✅ GPT-4 + Gemini            | ❌ None        | ⚠️ Basic           |
| **Cost**              | ✅ Free & Open Source        | 💰 $49/user/mo | 💰 $52/user/mo     |
| **Self-Hosted**       | ✅ Full control              | ❌ SaaS only   | ⚠️ Enterprise only |
| **Multi-SCM**         | ✅ GitHub, GitLab, Bitbucket | ❌ GitHub only | ✅ Yes             |
| **Real-time Updates** | ✅ WebSocket                 | ❌ Polling     | ❌ Polling         |
| **Custom Rules**      | ✅ Full engine               | ⚠️ Limited     | ⚠️ Limited         |

---

## ✨ Key Features

### 🔍 Security Scanning

- **Semgrep** - Static code analysis (SAST)
- **Trivy** - Container & dependency scanning
- **GitLeaks** - Secret detection
- **Bandit/Safety** - Python security
- **Lynis** - Infrastructure auditing

### 🤖 AI-Powered Analysis

- Vulnerability explanation & risk assessment
- Automated remediation suggestions
- Code fix generation
- False positive detection

### 📊 Reporting & Compliance

- Unified 6-tab security reports
- PDF export with executive summary
- **9 Compliance Frameworks**: OWASP, NIST, ISO27001, PCI-DSS, HIPAA, SOC2, GDPR, CIS, MITRE
- SBOM generation (SPDX, CycloneDX)

### 🏢 Enterprise Features

- Role-based access control
- Audit logging
- Webhook integrations
- Real-time notifications

---

## 🛠️ Tech Stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| **Frontend** | React 18, Vite, Tailwind CSS        |
| **Backend**  | FastAPI, Python 3.11                |
| **Database** | MongoDB Atlas                       |
| **AI**       | OpenAI GPT-4, Google Gemini         |
| **Hosting**  | Vercel (Frontend), Render (Backend) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+

### Installation

```bash
# Clone
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX

# Backend
cd backend
cp .env.example .env
# Edit .env with your API keys
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Access

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

> 📖 For detailed setup, see [Installation Guide](docs/INSTALLATION.md)

---

## 📁 Project Structure

```
ONYX/
├── backend/
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic (AI, scanning, compliance)
│   ├── models/          # Database models
│   └── configs/         # Scanner configurations
├── frontend/
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page views
│       └── services/    # API client
└── docs/                # Documentation
```

---

## 👥 Team

| Role                   | Name             | GitHub                                               |
| ---------------------- | ---------------- | ---------------------------------------------------- |
| 💻 **Lead Developer**  | Sagar Wavhal     | [@Sagar4173](https://github.com/Sagar4173)           |
| 🔒 **Security Expert** | Piyush More      | [@MorePiyush55](https://github.com/MorePiyush55)     |
| ⚙️ **DevOps Engineer** | Rushikesh Phalke | [@rushiphalke247](https://github.com/rushiphalke247) |

---

## 📚 Documentation

| Document                             | Description           |
| ------------------------------------ | --------------------- |
| [Installation](docs/INSTALLATION.md) | Setup guide           |
| [API Reference](docs/API.md)         | API documentation     |
| [Architecture](docs/ARCHITECTURE.md) | System design         |
| [Deployment](docs/DEPLOYMENT.md)     | Production deployment |
| [Contributing](docs/CONTRIBUTING.md) | Contribution guide    |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

```bash
# Fork, clone, branch, commit, PR
git checkout -b feature/your-feature
```

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/Sagar4173/ONYX/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Sagar4173/ONYX/discussions)
- 🔒 **Security**: See [SECURITY.md](SECURITY.md)

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

[![GitHub stars](https://img.shields.io/github/stars/Sagar4173/ONYX?style=social)](https://github.com/Sagar4173/ONYX/stargazers)

**Made with ❤️ by the ONYX Team**

_Secure your code. Beat the competition._

</div>
