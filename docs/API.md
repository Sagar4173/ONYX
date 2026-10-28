# API Reference

ONYX exposes a FastAPI JSON API. This document covers the current conventions
and route inventory. Request bodies, response schemas, and live examples are
authoritative in the generated OpenAPI document.

- OpenAPI UI: `/docs`
- OpenAPI JSON: `/openapi.json`
- Health: `GET /health`
- Local API base: `http://localhost:8000`
- Same-origin Docker API base: `/api`

Last generated from the application schema: **2026-10-28**

- Schema size: **191 paths / 213 operations**
- Source of truth: `app.openapi()`; `/docs` and `/openapi.json` render it live.

---

## Authentication

Most `/api` routes require a bearer token:

```http
Authorization: Bearer <access-token>
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username_or_email": "analyst@example.com",
  "password": "your-password",
  "remember_me": false,
  "two_factor_code": "123456"
}
```

`two_factor_code` is required when the account has 2FA enabled. A 2FA challenge
response uses `requires_2fa: true`; retry the login with the current code.

### Refresh

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "..."
}
```

Logout endpoints revoke the current session or all sessions. Refresh tokens and
access tokens are different values.

### API tokens

API tokens can be used in the same `Authorization: Bearer` header. They are
created through the user or auth token endpoints. The token value is returned
only once at creation. Expiration is enforced; scopes are validated at creation
and IP allowlists are stored, but scope/IP enforcement is not yet applied by
route dependencies, so treat tokens as full user credentials.

### Public and special routes

- `GET /`, `GET /health`, `GET /api/scanners/health`, and
  `GET /api/stats/public` are public.
- Login, registration, email verification, password reset, and SSO config/login
  routes are public.
- `POST /api/webhook/` authenticates with `WEBHOOK_SECRET`, not a user JWT.
- Manual scan routes under `/api/webhook/scan` require a user JWT.
- `/ws?token=<access-token>` is the authenticated WebSocket endpoint.
- `/metrics` is exposed on the backend port for Prometheus. It is not part of
  the OpenAPI schema.

---

## Conventions

- JSON field names use `snake_case`.
- Timestamps are ISO 8601 UTC strings.
- List endpoints commonly accept `skip` and `limit`; defaults and maximums vary
  by route.
- Validation failures return HTTP 422 with FastAPI's structured `detail`.
- Most application errors use `{"detail": "message"}`.
- Rate-limit responses return HTTP 429 and expose `Retry-After`,
  `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- Request bodies are limited to 10 MB.
- File uploads (for example custom security-rule uploads) use multipart form
  data; confirm the route-specific schema in `/docs`.

Common status codes:

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Resource created |
| 400 | Invalid request or unsupported input |
| 401 | Missing/invalid credentials |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict or duplicate resource |
| 422 | Schema validation failure |
| 429 | Rate limit exceeded |
| 500 | Internal error |
| 503 | Dependency or authentication configuration unavailable |

---

## Permissions

| Area | Access |
|---|---|
| `/api/admin/*` | Admin |
| User/project administration | Admin or Security Manager where supported |
| Projects and reports | Owner, team member, or privileged role |
| Own profile, sessions, tokens | Authenticated user |
| Scan/webhook operations | Authenticated user with project access |
| Webhook ingestion | Shared secret or HMAC signature |

Role and ownership checks are enforced per route. Do not assume that a valid
token grants access to every project or report.

---

## Webhook Ingestion

`POST /api/webhook/` accepts GitHub, GitLab, Bitbucket, or a generic payload.

Authentication options:

- `x-onyx-webhook-secret: <WEBHOOK_SECRET>`
- `x-webhook-secret: <WEBHOOK_SECRET>`
- `x-hub-signature-256: sha256=<HMAC-SHA256 of raw body using WEBHOOK_SECRET>`

If `WEBHOOK_SECRET` is unset, the endpoint fails closed with HTTP 503. Requests
are limited to 20/minute. See [Webhook Setup](webhook-github-actions.md).

---

## Route Inventory

The routes below are generated from `app.openapi()`. Methods are shown only for
documented HTTP operations. `/docs` contains the full parameter and schema
details.

### Root and health

```text
GET  /
GET  /health
```

### Authentication (`/api/auth`)

```text
POST   /api/auth/login
POST   /api/auth/register
POST   /api/auth/refresh
POST   /api/auth/logout
POST   /api/auth/logout-all
GET    /api/auth/me
PUT    /api/auth/me
POST   /api/auth/change-password
GET    /api/auth/me/sessions
DELETE /api/auth/me/sessions
DELETE /api/auth/me/sessions/{session_id}
POST   /api/auth/me/2fa/setup
POST   /api/auth/me/2fa/enable
POST   /api/auth/me/2fa/disable
GET    /api/auth/me/2fa/status
POST   /api/auth/me/avatar
GET    /api/auth/me/notifications
PUT    /api/auth/me/notifications
GET    /api/auth/api-tokens
POST   /api/auth/api-tokens
DELETE /api/auth/api-tokens/{token_id}
POST   /api/auth/request-password-reset
POST   /api/auth/reset-password
POST   /api/auth/verify-email
POST   /api/auth/resend-verification
POST   /api/auth/test-email
GET    /api/auth/sso/google/config
POST   /api/auth/sso/google
```

### Users (`/api/users`)

```text
GET    /api/users
POST   /api/users/bulk-update
GET    /api/users/export/data
GET    /api/users/statistics
GET    /api/users/me
PUT    /api/users/me
POST   /api/users/me/change-password
PUT    /api/users/me/settings
GET    /api/users/me/settings
GET    /api/users/me/activity
GET    /api/users/me/api-tokens
POST   /api/users/me/api-tokens
DELETE /api/users/me/api-tokens/{token_id}
GET    /api/users/me/sessions
DELETE /api/users/me/sessions/{session_id}
GET    /api/users/security/overview
GET    /api/users/security/suspicious-activity
GET    /api/users/{user_id}
PUT    /api/users/{user_id}
DELETE /api/users/{user_id}
PUT    /api/users/{user_id}/role
PUT    /api/users/{user_id}/status
GET    /api/users/{user_id}/activity
GET    /api/users/{user_id}/api-tokens
DELETE /api/users/{user_id}/api-tokens/{token_id}
GET    /api/users/{user_id}/sessions
DELETE /api/users/{user_id}/sessions
DELETE /api/users/{user_id}/sessions/{session_id}
```

### Projects (`/api/projects`)

```text
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/templates
GET    /api/projects/templates/categories
GET    /api/projects/analytics/overview
GET    /api/projects/{project_id}
PUT    /api/projects/{project_id}
DELETE /api/projects/{project_id}
GET    /api/projects/{project_id}/stats
POST   /api/projects/{project_id}/team
DELETE /api/projects/{project_id}/team/{member_user_id}
```

### Reports and findings (`/api/reports`)

```text
GET    /api/reports/
GET    /api/reports/analytics/overview
GET    /api/reports/project/{project_name}
GET    /api/reports/{report_id}
GET    /api/reports/{report_id}/summary
GET    /api/reports/{report_id}/download
GET    /api/reports/{report_id}/ai-analysis
POST   /api/reports/{scan_id}/auto-fix
GET    /api/reports/{scan_id}/auto-fix/{finding_id}
DELETE /api/reports/{scan_id}/auto-fix/{finding_id}
POST   /api/reports/{scan_id}/auto-fix/{finding_id}/approve
POST   /api/reports/{scan_id}/findings/{finding_id}/label
```

### Webhooks and scans (`/api/webhook`)

```text
POST   /api/webhook/
GET    /api/webhook/events
GET    /api/webhook/events/{event_id}
POST   /api/webhook/scan
GET    /api/webhook/scan/{scan_id}/status
POST   /api/webhook/scan/{scan_id}/stop
```

### Scheduled scans (`/api/schedules`)

```text
GET    /api/schedules
POST   /api/schedules
GET    /api/schedules/{schedule_id}
PUT    /api/schedules/{schedule_id}
DELETE /api/schedules/{schedule_id}
PATCH  /api/schedules/{schedule_id}/toggle
POST   /api/schedules/{schedule_id}/run
GET    /api/schedules/{schedule_id}/history
```

### Secret history (`/api/secret-history`)

```text
GET    /api/secret-history
GET    /api/secret-history/summary
GET    /api/secret-history/trends
PATCH  /api/secret-history/{record_id}
```

### Scanners and analytics

```text
GET    /api/scanners/health
GET    /api/stats/public
GET    /api/analytics/overview
```

### AI (`/api/ai`)

```text
POST   /api/ai/chat
POST   /api/ai/chat/stream
GET    /api/ai/features
POST   /api/ai/investigate
```

### Triage (`/api/triage`)

```text
GET    /api/triage/{scan_id}
POST   /api/triage/{scan_id}
```

### ML (`/api/ml`)

```text
GET    /api/ml/status
POST   /api/ml/train
GET    /api/ml/anomalies
```

### Compliance (`/api/compliance`)

```text
GET    /api/compliance/frameworks
GET    /api/compliance/framework/{framework}/controls
GET    /api/compliance/risk-summary
GET    /api/compliance/trends
POST   /api/compliance/report
```

### Enterprise (`/api/enterprise`)

```text
GET    /api/enterprise/health
GET    /api/enterprise/audit-logs
GET    /api/enterprise/audit-logs/query
GET    /api/enterprise/audit-logs/export
GET    /api/enterprise/audit-logs/users
GET    /api/enterprise/audit-logs/user/{user_id}
GET    /api/enterprise/audit-logs/resource/{resource_type}/{resource_id}
GET    /api/enterprise/audit-logs/verify/{event_id}
POST   /api/enterprise/audit-logs/compliance-report
GET    /api/enterprise/compliance/frameworks
POST   /api/enterprise/compliance/assess
GET    /api/enterprise/compliance/assessments
POST   /api/enterprise/compliance/assessments
GET    /api/enterprise/compliance/framework-summary
GET    /api/enterprise/compliance/project/{project_id}/assessments
GET    /api/enterprise/compliance/trend/{project_id}/{framework}
POST   /api/enterprise/compliance/report
GET    /api/enterprise/retention-policies
POST   /api/enterprise/retention/policies
POST   /api/enterprise/retention/policies/{policy_id}/execute
POST   /api/enterprise/retention/policies/execute-all
POST   /api/enterprise/retention/initialize-defaults
GET    /api/enterprise/retention/statistics
```

### Enterprise security (`/api/enterprise-security`)

```text
GET    /api/enterprise-security/sbom/formats
POST   /api/enterprise-security/sbom/generate
POST   /api/enterprise-security/sbom/generate/download
POST   /api/enterprise-security/scans/compare
GET    /api/enterprise-security/scans/{project_id}/branches/compare
GET    /api/enterprise-security/scans/{project_id}/compare-with-latest
GET    /api/enterprise-security/scans/{project_id}/remediation-progress
GET    /api/enterprise-security/scans/{project_id}/fix-velocity
GET    /api/enterprise-security/trends/comparison
GET    /api/enterprise-security/trends/dashboard
GET    /api/enterprise-security/trends/metrics
GET    /api/enterprise-security/trends/severity
GET    /api/enterprise-security/vulnerabilities/cve/{cve_id}
POST   /api/enterprise-security/vulnerabilities/enrich
POST   /api/enterprise-security/vulnerabilities/packages
```

### Security policies, rules, and drift (`/api/security`)

```text
GET    /api/security/baselines
POST   /api/security/baselines
POST   /api/security/drift-analysis
GET    /api/security/drift-history
POST   /api/security/full-security-analysis
GET    /api/security/policies
POST   /api/security/policies/evaluate
POST   /api/security/policies/update-from-git
GET    /api/security/policy-compliance-report
GET    /api/security/policy-violations
GET    /api/security/regression-alerts
GET    /api/security/rule-templates
GET    /api/security/rules
POST   /api/security/rules
GET    /api/security/rules/{rule_id}
POST   /api/security/rules/from-template
POST   /api/security/rules/upload
POST   /api/security/rules/validate
GET    /api/security/trends
```

### Advanced security (`/api/advanced-security`)

```text
GET    /api/advanced-security/health
GET    /api/advanced-security/status
GET    /api/advanced-security/baseline/status
GET    /api/advanced-security/boundaries/status
GET    /api/advanced-security/compliance/dashboard
GET    /api/advanced-security/compliance/frameworks
GET    /api/advanced-security/metrics/dashboard
GET    /api/advanced-security/metrics/security-score
GET    /api/advanced-security/vulnerabilities/dashboard
POST   /api/advanced-security/vulnerabilities/scan
GET    /api/advanced-security/threat-intel/feeds
POST   /api/advanced-security/threat-intel/analyze
POST   /api/advanced-security/policy/evaluate
POST   /api/advanced-security/policy/enforce
POST   /api/advanced-security/rules/parse
GET    /api/advanced-security/rules/test-status/{rule_id}
POST   /api/advanced-security/scan/execute
POST   /api/advanced-security/scan/boundaries/test
POST   /api/advanced-security/pentest/execute
```

### Advanced scanning (`/api/advanced-scanning`)

```text
GET    /api/advanced-scanning/config
POST   /api/advanced-scanning/scan/sast
POST   /api/advanced-scanning/scan/dast
POST   /api/advanced-scanning/scan/iac
POST   /api/advanced-scanning/scan/comprehensive
GET    /api/advanced-scanning/scan/{scan_id}/findings
GET    /api/advanced-scanning/scan/{scan_id}/summary
GET    /api/advanced-scanning/suppressions
POST   /api/advanced-scanning/suppressions
```

### Administration (`/api/admin`)

```text
GET    /api/admin/dashboard/stats
GET    /api/admin/activity/recent
GET    /api/admin/users/all
GET    /api/admin/users/{user_id}/activity
PUT    /api/admin/users/{user_id}/role
PUT    /api/admin/users/{user_id}/status
DELETE /api/admin/users/{user_id}
GET    /api/admin/projects/all
DELETE /api/admin/projects/{project_id}
GET    /api/admin/reports/all
GET    /api/admin/webhook/status
POST   /api/admin/webhook/rotate
```

---

## Examples

### Manual scan

```bash
curl -X POST http://localhost:8000/api/webhook/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/example/repo.git",
    "branch": "main"
  }'
```

The response contains a `scan_id`. Poll:

```bash
curl http://localhost:8000/api/webhook/scan/$SCAN_ID/status \
  -H "Authorization: Bearer $TOKEN"
```

### Public stats

```bash
curl http://localhost:8000/api/stats/public
```

### Admin webhook status

```bash
curl http://localhost:8000/api/admin/webhook/status \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Changing the API

Route changes must update:

1. the route module under `backend/routes/`
2. the relevant tests
3. this route inventory or the generated OpenAPI reference
4. any frontend service method that calls the affected route
5. the user guide or webhook guide when behavior changes

Do not document endpoints that are not present in `app.openapi()` unless they
are intentionally excluded infrastructure routes such as `/metrics`.
