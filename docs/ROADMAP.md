# 🗺️ ONYX Development Roadmap

> **Team Reference Document**  
> **Last Updated**: December 2025  
> **Mission**: Build the #1 alternative to GHAS & Snyk

---

## 🎯 Competitive Strategy

### Why We Win Against GHAS & Snyk

| Our Advantage           | Impact                                   | Status  |
| ----------------------- | ---------------------------------------- | ------- |
| **AI-Powered Analysis** | GPT-4 + Gemini (competitors have NONE)   | ✅ Live |
| **Zero Cost**           | Open source vs $49-52/user/month         | ✅ Live |
| **Multi-SCM**           | GitHub + GitLab + Bitbucket              | ✅ Live |
| **Real-time WebSocket** | Live scan progress (competitors poll)    | ✅ Live |
| **Custom Rule Engine**  | Full customization (competitors limited) | ✅ Live |
| **Self-Hosted Option**  | Full data control (GHAS: impossible)     | ✅ Live |

### Features to Build That Competitors DON'T Have

| Feature                      | Why It's Game-Changing                                  | Priority  |
| ---------------------------- | ------------------------------------------------------- | --------- |
| **AI Chat Assistant**        | Ask questions about vulnerabilities in natural language | 🔴 HIGH   |
| **Auto-Fix PRs**             | AI generates and submits fix pull requests              | 🔴 HIGH   |
| **Cross-Repo Analysis**      | Find vulnerabilities across all projects                | 🟡 MEDIUM |
| **Security Copilot**         | VS Code extension with AI suggestions                   | 🟡 MEDIUM |
| **Vulnerability Prediction** | ML model predicts where bugs will appear                | 🟢 FUTURE |

---

## 📋 Current Sprint Focus

### Priority 1: Critical Improvements

| Task                                     | Assignee   | Status         | Notes                             |
| ---------------------------------------- | ---------- | -------------- | --------------------------------- |
| Performance optimization for large scans | DevOps     | 🔄 In Progress | Target: <30s for repos under 10MB |
| Rate limiting enhancement                | Backend    | 📋 Planned     | Add per-user rate limits          |
| Error handling improvements              | Full Stack | 📋 Planned     | Better user-facing error messages |

---

## 🚀 Feature Roadmap

### Phase 1: Beat Competitors (Q1 2026) 🔥

#### 🤖 AI Advantages (GHAS/Snyk don't have this)

- [ ] **AI Chat Assistant** - Natural language questions about vulnerabilities
- [ ] **Auto-Fix PRs** - AI generates and submits fix pull requests automatically
- [ ] **Intelligent Triage** - AI prioritizes vulnerabilities by business impact
- [ ] **Context-Aware Remediation** - AI understands your codebase for better fixes
- [ ] **False Positive Learning** - AI learns from your feedback to reduce noise

#### 🔍 Scanning Improvements

- [ ] **Parallel scanning** - Run multiple scanners simultaneously
- [ ] **Incremental scanning** - Scan only changed files
- [ ] **Scheduled scans** - Cron-based automatic scanning
- [ ] **Branch comparison** - Compare security between branches
- [ ] **PR integration** - Auto-scan on pull requests

#### 📊 Analytics & Reporting

- [ ] **Custom dashboards** - User-configurable widgets
- [ ] **Export formats** - CSV, Excel, JSON exports
- [ ] **Email reports** - Scheduled report delivery
- [ ] **Team metrics** - Per-developer security scores
- [ ] **SLA tracking** - Vulnerability fix time tracking

#### 🔗 Integrations

- [ ] **Slack notifications** - Real-time alerts
- [ ] **Microsoft Teams** - Webhook integration
- [ ] **Jira integration** - Auto-create tickets
- [ ] **GitHub Actions** - CI/CD pipeline integration
- [ ] **GitLab CI** - Pipeline integration

---

### Phase 2: Enterprise Features (Q2 2026)

#### 🚀 Features Competitors Charge $$$$ For (We're FREE)

- [ ] **Organizations** - Multi-tenant support (Snyk charges extra)
- [ ] **Teams** - Group users into teams (GHAS: GitHub Teams only)
- [ ] **SSO/SAML** - Enterprise authentication (both charge $$$$)
- [ ] **LDAP/AD** - Directory integration
- [ ] **API keys** - Per-user API tokens

#### 🛡️ Advanced Security (Our Edge)

- [ ] **DAST scanning** - Dynamic application testing
- [ ] **API security** - OpenAPI/Swagger scanning
- [ ] **Cloud security** - AWS/Azure/GCP scanning
- [ ] **Kubernetes** - K8s manifest scanning
- [ ] **IaC scanning** - Terraform, CloudFormation

#### 📋 Compliance

- [ ] **Custom frameworks** - User-defined compliance
- [ ] **Attestation** - Compliance sign-off workflow
- [ ] **Evidence collection** - Automated audit evidence
- [ ] **Gap analysis** - Compliance gap reporting
- [ ] **Remediation tracking** - Fix verification

---

### Phase 3: Scale & Performance (Q3 2026)

#### ⚡ Performance

- [ ] **Redis caching** - Query result caching
- [ ] **Background jobs** - Celery task queue
- [ ] **Database sharding** - MongoDB sharding
- [ ] **CDN integration** - Static asset delivery
- [ ] **Load balancing** - Multiple backend instances

#### 📱 Platform Expansion

- [ ] **Mobile app** - iOS/Android companion
- [ ] **VS Code extension** - IDE integration
- [ ] **CLI tool** - Command-line scanner
- [ ] **Desktop app** - Electron wrapper
- [ ] **Browser extension** - Quick scan from browser

---

## 🐛 Known Issues & Technical Debt

### High Priority

| Issue                   | Impact                   | Owner    | ETA     |
| ----------------------- | ------------------------ | -------- | ------- |
| Large repo timeout      | Scans fail >100MB repos  | Backend  | Q1 2026 |
| WebSocket reconnection  | Occasional disconnect    | Frontend | Q1 2026 |
| Memory usage in Semgrep | High RAM for large files | DevOps   | Q1 2026 |

### Medium Priority

| Issue                 | Impact                           | Owner    | ETA     |
| --------------------- | -------------------------------- | -------- | ------- |
| PDF generation slow   | 5-10s for large reports          | Frontend | Q2 2026 |
| Duplicate findings    | Same vuln from multiple scanners | Backend  | Q2 2026 |
| Mobile responsiveness | Some pages not mobile-friendly   | Frontend | Q2 2026 |

### Low Priority

| Issue              | Impact                   | Owner    | ETA     |
| ------------------ | ------------------------ | -------- | ------- |
| Dark mode toggle   | Only dark mode available | Frontend | Q3 2026 |
| Keyboard shortcuts | No hotkey support        | Frontend | Q3 2026 |
| Bulk operations    | No bulk delete/archive   | Backend  | Q3 2026 |

---

## 👥 Team Assignments

### 🎯 Team Goal: Make ONYX Better Than GHAS & Snyk

### Sagar Wavhal (Lead Developer)

**Focus Areas**: AI Integration, Architecture, Features That Competitors Don't Have

- [ ] AI Chat Assistant for vulnerabilities
- [ ] Auto-Fix PR generation
- [ ] AI model optimization
- [ ] New scanner integrations
- [ ] API design & documentation
- [ ] Code review & architecture decisions

### Piyush More (Security Expert)

**Focus Areas**: Security Scanning, Compliance, Making Our Scanners BETTER Than Competitors

- [ ] Custom rule library (beat Snyk's rules)
- [ ] Compliance framework expansion (more than GHAS)
- [ ] False positive reduction (AI-powered)
- [ ] Scanner rule optimization
- [ ] Security testing
- [ ] Vulnerability database updates

### Rushikesh Phalke (DevOps Engineer)

**Focus Areas**: Infrastructure, Performance, Making ONYX FASTER Than Competitors

- [ ] Scan speed optimization (target: faster than Snyk)
- [ ] CI/CD pipeline improvements
- [ ] Monitoring & alerting
- [ ] Performance optimization
- [ ] Infrastructure scaling

---

## 📅 Release Schedule

| Version | Target Date | Focus                      |
| ------- | ----------- | -------------------------- |
| v1.1.0  | Jan 2026    | Performance & Bug Fixes    |
| v1.2.0  | Mar 2026    | Integrations (Slack, Jira) |
| v1.3.0  | May 2026    | Enterprise Features        |
| v2.0.0  | Aug 2026    | Multi-tenant & Scale       |

---

## 💡 Feature Requests (Backlog)

### From Users

1. Dark/Light mode toggle
2. Custom scan profiles
3. Vulnerability false positive marking
4. Scan scheduling
5. Team dashboards

### From Team

1. Plugin architecture
2. GraphQL API
3. Real-time collaboration
4. AI chat assistant
5. Automated fix PRs

---

## 📝 Notes for Developers

### Before Starting Work

1. Check this roadmap for priorities
2. Create a branch from `master`
3. Update relevant documentation
4. Add tests for new features
5. Request code review

### Code Standards

- Backend: Python 3.11+, type hints required
- Frontend: React 18, functional components only
- Tests: Minimum 80% coverage for new code
- Docs: Update API.md for new endpoints

### Git Workflow

```
master (production)
  └── develop (staging)
       └── feature/xxx (feature branches)
       └── fix/xxx (bug fixes)
```
