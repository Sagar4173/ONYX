# GitHub Actions → ONYX Webhook Integration

Trigger automated ONYX security scans from GitHub using a simple webhook
payload. No GitHub App, no OAuth — just a shared secret header.

## How it works

1. GitHub Actions sends a POST to the ONYX webhook endpoint whenever a
   push (or PR) happens on your repository.
2. ONYX verifies the shared secret, records the event, clones the repo,
   and runs the full scan workflow (SAST, secrets, dependency checks, ...).
3. Results appear in the ONYX dashboard like any other scan.

## Endpoint

| Item | Value |
| --- | --- |
| URL | `https://<your-onyx-domain>/api/webhook/` |
| Method | `POST` |
| Auth | `x-onyx-webhook-secret: <secret>` header |
| Rate limit | 20 requests/minute |

Alternative auth: GitHub-style `x-hub-signature-256: sha256=<hex>`
(HMAC-SHA256 of the raw body with the shared secret).

### Response codes

| Code | Meaning |
| --- | --- |
| `200` | Event accepted, scan scheduled |
| `400` | Invalid payload |
| `401` | Missing or invalid secret |
| `429` | Rate limit exceeded |

## 1. Get (or rotate) the secret

- **Admin UI:** Settings → API & Integration → Webhook Integration →
  copy the URL, rotate the secret if needed.
- After rotating, restart the backend service so all workers pick up the
  new secret: `systemctl restart onyx-backend` (on the EC2 host).

## 2. Add the secret to GitHub

1. In your repository: **Settings → Secrets and variables → Actions** →
   **New repository secret**.
2. Name: `ONYX_WEBHOOK_SECRET` — value: the secret from step 1.

## 3. Example workflow

Create `.github/workflows/onyx-scan.yml`:

```yaml
name: ONYX Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  onyx-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Send scan request to ONYX
        run: |
          curl -sf -X POST "$ONYX_WEBHOOK_URL/api/webhook/" \
            -H "Content-Type: application/json" \
            -H "x-onyx-webhook-secret: ${{ secrets.ONYX_WEBHOOK_SECRET }}" \
            -d "{
              \"repository_url\": \"https://github.com/${{ github.repository }}.git\",
              \"branch\": \"${{ github.ref_name }}\",
              \"commit_hash\": \"${{ github.sha }}\",
              \"commit_message\": \"${{ github.event.head_commit.message }}\",
              \"commit_author\": \"${{ github.actor }}\",
              \"event_type\": \"${{ github.event_name }}\"
            }"
```

Set the ONYX URL as a repository variable (`ONYX_WEBHOOK_URL`, e.g.
`https://onyx.example.com`), or hard-code it in the workflow.

## 4. Verify

```bash
# Valid secret -> 200
curl -si -X POST https://<your-onyx-domain>/api/webhook/ \
  -H "Content-Type: application/json" \
  -H "x-onyx-webhook-secret: <secret>" \
  -d '{"repository_url":"https://github.com/<owner>/<repo>.git","commit_hash":"abc123"}' | head -3

# No secret -> 401
curl -si -X POST https://<your-onyx-domain>/api/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"repository_url":"https://github.com/<owner>/<repo>.git","commit_hash":"abc123"}' | head -3
```

## Payload reference

| Field | Required | Description |
| --- | --- | --- |
| `repository_url` | yes | Git clone URL of the repository |
| `branch` | no | Branch to scan (default `main`) |
| `commit_hash` | no | Commit SHA to scan |
| `commit_message` | no | Display metadata |
| `commit_author` | no | Display metadata |
| `event_type` | no | `push` / `pull_request` (default `push`) |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `401` | Secret mismatch: re-check the header value; after rotation, restart the backend |
| `400` | Payload missing `repository_url` or not valid JSON |
| `429` | Too many events — ONYX enforces 20/min per client |
| No scan appears | Check `journalctl -u onyx-backend` for `Scan workflow failed` errors |
