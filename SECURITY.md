# Security Policy and Deployment Security

## Reporting a Vulnerability

Report security issues privately through
[GitHub Security Advisories](https://github.com/Sagar4173/ONYX/security/advisories/new).

Include:

- affected version or commit
- reproduction steps
- realistic impact
- any suggested remediation

Do not open a public issue for an undisclosed vulnerability. Do not include
live credentials, tokens, or customer data in a report.

ONYX does not currently operate a paid bug-bounty program. Security fixes are
applied to the `master` branch. There is no long-term support branch.

---

## Implemented Controls

### Authentication and sessions

- Passwords are hashed with bcrypt; plaintext passwords are never stored.
- Access and refresh tokens are JWTs signed with `SECRET_KEY`.
- Account lockout defaults to 5 failed attempts for 30 minutes.
- TOTP 2FA is available for password and SSO accounts.
- Google SSO verifies the ID token signature and audience and supports an
  optional email-domain allowlist.
- Session records support listing and revocation, including logout-all.
- API tokens are stored as SHA-256 hashes, have a visible prefix, and support
  expiration. Token values are returned only at creation. Scopes are validated
  at creation and IP allowlists are stored, but scope/IP enforcement is not yet
  applied by route dependencies; treat tokens as full user credentials.
- WebSocket connections require a valid JWT.

### Authorization

- Role-based access: Admin, Security Manager, Developer, Viewer.
- Administrative routes require the admin role.
- Project and report routes check ownership or team membership.
- Webhook scan status checks reject access to another user's scan.

### Data protection

- Sensitive fields are encrypted at rest with Fernet, using a key derived from
  `SECRET_KEY` through PBKDF2.
- URLs and logs are scrubbed to remove embedded credentials before they are
  exposed through APIs or logs.
- Audit records include a SHA-256 event hash and a verification endpoint.
  This is tamper-evident, not tamper-proof: an actor with database write access
  could recompute hashes.
- Webhook payloads are sanitized before storage, and only a limited set of
  non-secret headers is persisted.

### Application protections

- Request bodies are limited to 10 MB based on `Content-Length`.
- SlowAPI rate limits cover login, webhooks, AI, and other sensitive endpoints.
- CORS origins are explicit; production does not default to permissive origins.
- Webhook requests fail closed with HTTP 503 when `WEBHOOK_SECRET` is unset.
- Webhooks accept either `x-onyx-webhook-secret` / `x-webhook-secret` or a
  GitHub-style `x-hub-signature-256` HMAC-SHA256 signature.
- Global exception handling avoids returning raw internal errors.
- Security headers and HTTPS termination must be provided by the deployed nginx
  or an upstream reverse proxy.

---

## Required Production Configuration

Set these in `backend/.env`:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<at-least-32-random-characters>
MONGODB_URI=<authenticated MongoDB connection string>
FRONTEND_URL=https://your-domain.example
CORS_ORIGINS=https://your-domain.example
WEBHOOK_SECRET=<random-webhook-secret>
```

Additional recommendations:

- Use a unique `SECRET_KEY` per environment. It signs JWTs and derives the
  field-encryption key. Changing it invalidates existing sessions and makes
  previously encrypted fields undecryptable unless they are migrated first.
- Configure `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, or
  `OPENAI_API_KEY` if Ollama is not available.
- Configure `SENTRY_DSN` if error reporting is required.
- Set `AUTO_FIX_TOKEN` only when auto-fix push/PR automation is enabled. Use a
  least-privilege token and rotate it after suspected exposure.
- Configure SMTP for password reset and email verification.
- Configure `GOOGLE_CLIENT_ID` and, preferably, `GOOGLE_ALLOWED_DOMAINS` for SSO.

Repository and deployment secrets must be supplied through the environment,
not committed to the repository.

---

## Deployment Checklist

### Network and TLS

- Terminate HTTPS with a valid certificate.
- Expose only ports 80/443 publicly.
- Do not publish MongoDB (`27017`) or Ollama (`11434`) to the internet.
- Restrict SSH to trusted source addresses.
- Add security headers at nginx or the upstream proxy, including HSTS after
  HTTPS is verified, `X-Content-Type-Options`, `Referrer-Policy`, and a suitable
  Content-Security-Policy.
- Keep `/docs`, `/openapi.json`, and `/metrics` restricted if they should not be
  public. nginx currently proxies `/docs` and `/openapi.json`; metrics are
  available on the backend's internal port.

### MongoDB

- Enable authentication and bind MongoDB to a private interface.
- Use TLS for remote connections.
- Use a dedicated database user with access limited to the ONYX database.
- Back up the database and restore-test backups regularly.
- Do not treat MongoDB as a secrets vault; rotate any credential previously
  stored in scan data or auto-fix URLs.

### AI providers and Ollama

- Prefer cloud AI credentials when the host has limited memory.
- Ollama needs roughly 8 GB or more for a 7B model and is the final fallback in
  the default `AI_PROVIDER_CHAIN`; it is used when reachable.
- Do not expose Ollama without authentication or a private network.
- Treat all model output as untrusted. Auto-fix changes require approval before
  they are applied or submitted.

### Webhooks and SCM

- Generate a strong `WEBHOOK_SECRET`; rotate it through the admin API, restart
  the backend, then update the SCM webhook.
- Prefer least-privilege SCM tokens scoped to the required repositories.
- Review generated fix PRs before merging.
- Rotate tokens that were ever embedded in clone or push URLs.

### Frontend

- Build with the intended `VITE_API_URL` and `VITE_WS_URL`. The Docker/nginx
  default is same-origin `/api`, which avoids CORS and hostname drift.
- Do not deploy a development build that hardcodes `127.0.0.1`.
- Keep dependencies updated and review npm audit output.

---

## Known Limitations

- No built-in secrets manager or automatic key rotation.
- `SECRET_KEY` rotation requires a migration plan for encrypted fields.
- Rate limits are process-local. Run a single backend worker or implement shared
  storage and coordination before scaling out.
- The default Compose MongoDB has no authentication; it is isolated on the
  Compose network but still requires a trusted host.
- ML training data and models are stored on local disk and are not covered by
  the default Compose volume for ML state.
- No automatic deployment rollback. Back up before deploys.
- No formal certifications or compliance attestations are claimed by the
  project. Compliance features produce mappings and reports, not certification.
- Automated tests do not replace a live deployment, penetration test, or
  dependency and infrastructure review.

If you find a vulnerability or a mismatch between this document and the code,
report it privately and treat the code as authoritative until it is resolved.
