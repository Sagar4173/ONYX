# ONYX Development Roadmap

- **Updated:** 2026-10-28
- **Baseline:** `master` with 938 backend and 413 frontend tests passing

This roadmap describes work that is not yet complete. Implemented capabilities
are recorded in [PROJECT_STATUS.md](PROJECT_STATUS.md).

---

## Guiding Priorities

1. Correctness and security before new surface area.
2. Verified deployments before additional enterprise features.
3. Measured AI behavior before expanding autonomous actions.
4. Operational simplicity before horizontal-scale architecture.

---

## Completed

- Multi-scanner orchestration with 13 integrations
- Manual, scheduled, and webhook-triggered scans
- JWT, refresh sessions, API tokens, TOTP 2FA, Google SSO, RBAC
- AI provider failover, RAG chat, triage, investigation, and approval-gated fix
- Reports, PDF, SBOM, secret history, analytics, and compliance mappings
- Audit logging, retention, admin tooling, notifications, and monitoring
- Docker images and Compose deployment
- Compose hardening: private MongoDB/Ollama, same-origin nginx proxy, healthcheck
- GitHub Actions CI and the current Jenkins/EC2 deployment pipeline
- Jenkins backend/frontend test stages and fail-closed health checks
- E2E smoke tests aligned with current public routes and API endpoints
- Security regression fixes for credential-bearing repository URLs

---

## Now

| Work | Priority | Why |
|---|---|---|
| Verify hosted deployment and DNS | Critical | The documented hostname did not resolve during the audit |
| Jenkins rollback strategy | Critical | Test gates are present, but the pipeline has no automatic rollback |
| Live MongoDB and SCM integration tests | High | Unit tests do not prove persistence or provider behavior |
| Authenticated E2E flows | High | Current coverage is smoke-level and skips protected pages |
| Verify Compose hardening on a Docker host | High | Static validation cannot prove runtime networking |
| Rotate legacy SCM credentials | High | Older records may contain credentials even though new URLs reject them |

---

## Next

| Work | Notes |
|---|---|
| Shared scheduler/rate-limit state | Required before multiple backend workers |
| Durable ML storage | Add a dedicated volume and retention policy |
| Backups and restore drills | MongoDB, knowledge DB, ML state, environment |
| Dependency update policy | Automate audit review and pinned upgrades |
| Optional scanner installation | Document host packages or build scanner images |
| Better E2E test isolation | Dedicated test database and seeded accounts |

---

## Later

| Work | Notes |
|---|---|
| SAML/OIDC beyond Google | Enterprise identity-provider support |
| Organization/multi-tenant isolation | Requires data-model and authorization work |
| Jira and issue-tracker integrations | Approval and credential model required |
| Plugin API for scanners | Stable extension contract and sandboxing |
| Horizontal WebSocket/scan workers | Queue, shared state, sticky sessions |
| Custom dashboards | User-configurable reporting widgets |
| IDE extension | Reuse API and auth model |
| Vulnerability forecasting | Only with a measurable evaluation plan |

---

## Non-Goals for Now

- Claiming compliance certification from mapping features
- Running autonomous code changes without human approval
- Supporting multiple backend workers with the current scheduler
- Marketing comparisons based on competitor pricing that changes frequently
- Adding Redis, S3, or a queue without a concrete requirement and tests

---

## Known Issues

| Issue | Priority | Notes |
|---|---|---|
| Large repository timeouts | Medium | Streaming scan and resource limits needed |
| Slow PDF generation for large reports | Low | Profile before changing architecture |
| Partial cross-scanner deduplication | Low | Improve normalization rules |
| Container has no optional scanner binaries | Medium | Document or build a scanner-enabled image |
| ML state not persisted by default Compose volume | Medium | Add explicit volume |
| Hosted instance not independently verified | High | Verify DNS, TLS, services, and callbacks |
