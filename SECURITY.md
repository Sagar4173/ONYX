# Security Policy

## Reporting Security Vulnerabilities

Please do not report security vulnerabilities through public GitHub issues.  
Report them privately via GitHub Issues (mark as security).

We acknowledge receipt within 24 hours and work to resolve critical issues within 1-3 days.

### What to Include

1. Description of the vulnerability
2. Impact (what an attacker could achieve)
3. Steps to reproduce
4. Environment details (version, deployment method, OS)
5. Proof of concept (if applicable)

---

## Security Features

### Authentication & Authorization
- JWT-based authentication with configurable expiration
- Password hashing using bcrypt with salt
- Rate limiting on authentication endpoints
- Role-based access control (Admin, Security Manager, Developer, Viewer)

### API Security
- Input validation using Pydantic models
- NoSQL injection prevention through Beanie ODM
- CORS configuration
- Request size limits

### Data Protection
- All secrets in environment variables (never in code)
- Sensitive data masking in logs
- Encryption service (Fernet AES-128-CBC+HMAC via PBKDF2)

### Infrastructure Security
- Docker container deployment
- Sentry error tracking (no PII)
- Prometheus metrics
- Dependency scanning via Safety
- Secret detection via GitLeaks + detect-secrets + SOPS

---

## Incident Response

| Timeframe | Action |
|---|---|
| 24 hours | Acknowledge and investigate |
| 72 hours | Initial assessment and severity |
| 1 week | Develop and test fix (critical) |
| 2 weeks | Release patch and advisory |

### Severity Levels
- **Critical** (CVSS 9.0-10.0): 24h response, 1-3 day fix
- **High** (CVSS 7.0-8.9): 48h response, 1 week fix
- **Medium** (CVSS 4.0-6.9): 1 week response, 2 week fix
- **Low** (CVSS 0.1-3.9): 2 week response, next release

---

## Security Scanning

The platform scans itself regularly:

| Scanner | Scope |
|---|---|
| Semgrep | Code SAST |
| Safety | Python dependencies |
| GitLeaks + detect-secrets | Secret detection |
| Trivy | Docker images |

---

## Secure Development

### Input Validation
```python
from pydantic import BaseModel, constr

class ScanRequest(BaseModel):
    repository_url: constr(regex=r'^https://github\.com/[\w\-\.]+/[\w\-\.]+\.git$')
    branch: constr(min_length=1, max_length=255)
```

### Authentication
```python
class AuthService:
    def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30),
        }
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")
```

---

## Security Checklist

### Deployment
- [ ] All secrets in environment variables (never in code)
- [ ] HTTPS enforced in production
- [ ] MongoDB authentication enabled
- [ ] Firewall restricts port access
- [ ] Regular dependency updates

### Code
- [ ] All inputs validated via Pydantic
- [ ] No hardcoded secrets
- [ ] No sensitive data in logs
- [ ] Tests pass before merge

---

## Contact

| Role | GitHub |
|---|---|
| Security Lead | [@MorePiyush55](https://github.com/MorePiyush55) |
| Lead Developer | [@Sagar4173](https://github.com/Sagar4173) |
| DevOps Engineer | [@rushiphalke247](https://github.com/rushiphalke247) |
