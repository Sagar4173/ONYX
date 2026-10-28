# ONYX Project Status

- **Last verified:** 2026-10-28
- **Branch:** `master`
- **Status:** Active development; deployed environments exist but are not verified by
  this document.

---

## Verified Metrics

| Metric | Current value |
|---|---|
| Backend tests | 938 passing |
| Frontend tests | 413 passing |
| OpenAPI paths | 191 |
| OpenAPI operations | 213 |
| Scanner integrations | 13 |
| Deployment pipeline | Jenkins on EC2 with rollback; Docker Compose alternative |

Metrics describe the repository at the verified commit, not a promise about any
externally hosted instance.

---

## Implemented

### Identity and access

- JWT access/refresh authentication and session revocation
- Registration, email verification, password reset
- bcrypt password hashing and failed-login lockout
- TOTP 2FA setup, enable, disable, and status
- Google SSO with optional domain allowlist
- Role-based access: Admin, Security Manager, Developer, Viewer
- Hashed API tokens with expiration; scopes/IP allowlists are stored but not yet
  enforced at the route layer

### Projects and scanning

- Project CRUD, templates, categories, team membership, and analytics
- Manual scans, scheduled scans, and SCM-triggered scans
- Parallel scanner execution with graceful degradation
- 13 integrations: Semgrep, Bandit, Safety, GitLeaks, Detect-Secrets, SOPS,
  Dependency Governance, Trivy, ZAP, Nuclei, CodeQL, Checkov, Lynis
- Deduplication, suppressions, scan history, and progress updates
- GitHub, GitLab, and Bitbucket webhook payload handling
- Repository URL credential rejection and redaction

### AI and triage

- Provider failover: Gemini, Groq, OpenRouter, Ollama; OpenAI legacy support
- Vulnerability explanation, risk assessment, and remediation guidance
- RAG chat with citations over the local knowledge corpus
- Prompt-injection screening
- Investigation and triage workflows
- Approval-gated auto-fix generation and PR/MR creation
- Optional IsolationForest anomaly detection (disabled by default)

### Reporting and compliance

- Multi-section scan reports and PDF download
- Severity, trend, branch comparison, and remediation analytics
- SBOM generation in SPDX and CycloneDX
- Secret history, status updates, summaries, and trends
- Compliance frameworks, controls, risk summaries, trends, assessments, and
  reports, including custom identifiers

### Enterprise operations

- Admin dashboard, user/project/report administration
- Audit logging, query, export, and event-hash verification
- Retention policies and execution statistics
- Notification integrations for Slack, Teams, email, and WebSocket
- Sentry and Prometheus integration
- Fernet field encryption and URL/log scrubbing

### Delivery

- Backend and frontend Docker images
- Docker Compose with internal MongoDB/backend and same-origin nginx proxy
- GitHub Actions CI for backend, frontend, public and authenticated E2E, image
  builds, and a Compose runtime smoke test
- Jenkins deployment pipeline with previous-commit tracking and a marker-gated
  rollback script
- 938 backend and 413 frontend tests, plus public and authenticated E2E flows

---

## Current Limitations

- The current production deployment is not verified from this workspace.
  `onyx.ajuna.website` did not resolve during the documentation audit.
- Jenkins rollback is implemented and shell-tested, but it has not been
  exercised on the EC2 host. It restores code and services only; MongoDB data
  still requires a separate backup.
- E2E coverage now includes registration, login, dashboard, and sidebar
  navigation, but scan, WebSocket, and webhook flows are not authenticated E2E
  tests.
- Horizontal scaling is not production-ready: scheduler, WebSocket registry,
  scan cancellation state, and default rate limits are process-local.
- Optional scanner binaries must be installed on the host or added to the
  backend image.
- The default Compose Ollama service is started even when cloud AI is used.
  Pull a model before relying on local inference.
- ML databases/models are not persisted by a default dedicated volume.
- Redis settings exist but no current feature requires Redis.
- There is no S3/object-storage integration.
- Clone/push URLs created by older versions may still contain credentials;
  rotate affected tokens. New URLs reject embedded credentials.
- Compliance features produce mappings and reports; they do not certify an
  organization.
- No formal penetration test or live SCM/Mongo integration test is included in
  this repository.

---

## Technology

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS 3, TanStack Query 5 |
| Backend | FastAPI, Python 3.13, Pydantic v2 |
| Database | MongoDB 7+, Beanie |
| Authentication | PyJWT, bcrypt, TOTP, Google Identity Services |
| AI | Gemini, Groq, OpenRouter, OpenAI, Ollama |
| Retrieval | SQLite FTS5 and sqlite-vec |
| Real-time | FastAPI WebSocket |
| Monitoring | Sentry, Prometheus |
| Current deployment | Jenkins, EC2, systemd, nginx, MongoDB, optional Ollama |
| Alternative deployment | Docker Compose with nginx frontend |
| CI | GitHub Actions |

---

## Compatibility Notes

- Python 3.13 is the supported backend runtime.
- Node.js 22 is the supported frontend build runtime.
- MongoDB 7+ is required; the backend will not start without `MONGODB_URI`.
- FastAPI is pinned below 0.140 because direct route introspection relies on the
  older included-router structure. Use `app.openapi()["paths"]` for inventories.
- The frontend development server uses a hardcoded local backend URL; production
  values are build-time Vite variables.

---

## Next Work

Priority items, in practical order:

1. Verify the hosted deployment, DNS, TLS, systemd, nginx, and SCM callbacks.
2. Exercise the Jenkins rollback on the EC2 host, including state-file
   permissions, a health-check failure, and a database backup drill.
3. Expand authenticated E2E coverage to scans, WebSocket updates, and webhook
   events, preferably with a dedicated seeded test account.
4. Add shared rate-limit, scheduler, and WebSocket coordination before scaling
   beyond one backend worker.
5. Persist ML state and add backup/restore procedures for all runtime data.
6. Decide whether Redis and object storage are required, or remove unused
   configuration.
7. Add live integration tests for MongoDB and at least one SCM provider.
8. Rotate any credentials that may remain in historical repository URLs.

---

## Documentation

- [Installation](INSTALLATION.md)
- [API Reference](API.md)
- [Architecture](ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)
- [User Guide](USER_GUIDE.md)
- [Security Policy](../SECURITY.md)
- [Contributing](CONTRIBUTING.md)
