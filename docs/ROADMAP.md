# ONYX Development Roadmap

**Last Updated**: July 2026  
**Mission**: #1 alternative to GHAS & Snyk

---

## Competitive Position

| Our Advantage | Impact | Status |
|---|---|---|
| AI-Powered Analysis | GPT-4 + Gemini (competitors have none) | Live |
| Zero Cost | Open source vs $49-52/user/month | Live |
| Multi-SCM | GitHub + GitLab + Bitbucket | Live |
| Real-time WebSocket | Live scan progress (competitors poll) | Live |
| Custom Rule Engine | Full customization (competitors limited) | Live |
| Self-Hosted | Full data control | Live |

---

## Completed

### Phase 1: AI Advantages (Q1-Q2 2026)

- Ollama local LLM integration — zero-cost self-hosted AI (Qwen2.5-Coder:7B)
- Automatic provider fallback: Ollama → Gemini → OpenAI
- All AI features run fully offline when Ollama is available

- AI Chat Assistant - Natural-language vulnerability Q&A
- Auto-Fix PRs - AI generates and submits fix PRs
- Intelligent Triage - AI prioritizes by business impact
- Dual AI provider (OpenAI + Gemini) with fallback

### Phase 1: Scanning

- Parallel scanner execution
- 11 scanners integrated (7 core + 6 optional)
- Scheduled scans (cron-based)
- SOPS encryption auditing scanner
- Dependency governance scanner (malicious package blocklist)
- Secret history tracking across scans
- ZAP DAST real integration
- Lynis infrastructure scanner
- Detect-Secrets scanner

### Phase 1: Enterprise

- Admin dashboard with system monitoring
- Audit logging with integrity verification
- Data retention policies
- Webhook integrations (GitHub, GitLab)
- Slack + Teams notifications
- Email notifications
- 10 compliance frameworks (incl. MITRE ATT&CK)

### Phase 1: Infrastructure

- Docker Compose deployment
- GitHub Actions CI (3 jobs + E2E)
- Sentry error tracking
- Prometheus metrics
- Encryption service

---

## In Progress

| Task | Priority |
|---|---|
| Playwright E2E smoke tests | High |
| Secret scanning enhancements | Medium |

---

## Planned

### Q3-Q4 2026

| Feature | Notes |
|---|---|
| Multi-tenant organizations | User isolation per org |
| SSO/SAML | Enterprise auth |
| VS Code extension | IDE security |
| Redis caching | Performance |
| Custom dashboards | User-configurable widgets |
| Jira integration | Auto-create tickets |
| Vulnerability prediction | ML-based forecasting |
| Mobile app | iOS/Android |

### Future

- Plugin architecture for third-party scanners
- GraphQL API
- Real-time collaboration
- CI/CD plugin for Jenkins, Azure DevOps, CircleCI

---

## Known Issues

| Issue | Priority | Notes |
|---|---|---|
| Large repo timeout (>100MB) | Medium | Needs streaming scan |
| PDF generation slow for large reports | Low | |
| Duplicate findings across scanners | Low | Partially handled by dedup engine |
