# GitHub Actions to ONYX Webhook Integration

Trigger an ONYX scan from GitHub Actions with a shared secret. This is separate
from GitHub's native repository webhooks, which can also post directly to ONYX.

## How It Works

1. A workflow sends a POST request to the ONYX ingestion endpoint on push or
   pull request.
2. ONYX verifies the shared secret or HMAC signature, stores the event, and
   starts the scan workflow.
3. The scan appears in the ONYX dashboard and reports.

## Endpoint

| Item | Value |
|---|---|
| URL | `https://<your-onyx-domain>/api/webhook/` |
| Method | `POST` |
| Auth | `x-onyx-webhook-secret: <secret>` or HMAC |
| Rate limit | 20 requests/minute per client |
| Body | JSON, maximum request size 10 MB |

Accepted authentication headers:

- `x-onyx-webhook-secret: <WEBHOOK_SECRET>`
- `x-webhook-secret: <WEBHOOK_SECRET>`
- `x-hub-signature-256: sha256=<HMAC-SHA256 of raw body using WEBHOOK_SECRET>`

The endpoint fails closed with HTTP 503 when `WEBHOOK_SECRET` is not configured.

### Response codes

| Code | Meaning |
|---|---|
| 200 | Event accepted and scan processing started |
| 400 | Invalid payload |
| 401 | Missing or invalid secret/signature |
| 429 | Rate limit exceeded |
| 503 | Webhook authentication is not configured |

## 1. Configure the ONYX Secret

Set a random secret in `backend/.env`:

```env
WEBHOOK_SECRET=<random-secret>
```

Restart the backend after changing it. On the current EC2 deployment:

```bash
sudo systemctl restart onyx-backend
```

Admins can check status or rotate the secret through:

```text
GET  /api/admin/webhook/status
POST /api/admin/webhook/rotate
```

Rotation persists the new value to `backend/.env`. Restart the backend and then
update the GitHub secret.

## 2. Add the GitHub Variables

In the repository, open **Settings → Secrets and variables → Actions**:

- Repository variable `ONYX_WEBHOOK_URL`: `https://your-domain.example`
- Repository secret `ONYX_WEBHOOK_SECRET`: the ONYX webhook secret

Do not put either value directly in the workflow file.

## 3. Example Workflow

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
    env:
      ONYX_WEBHOOK_URL: ${{ vars.ONYX_WEBHOOK_URL }}
      ONYX_WEBHOOK_SECRET: ${{ secrets.ONYX_WEBHOOK_SECRET }}
    steps:
      - name: Send scan request
        run: |
          set -euo pipefail
          payload=$(jq -n \
            --arg repository_url "https://github.com/${GITHUB_REPOSITORY}.git" \
            --arg branch "${GITHUB_HEAD_REF:-${GITHUB_REF_NAME}}" \
            --arg commit_hash "${GITHUB_SHA}" \
            --arg commit_message "${GITHUB_EVENT_NAME} ${GITHUB_SHA}" \
            --arg commit_author "${GITHUB_ACTOR}" \
            --arg event_type "${GITHUB_EVENT_NAME}" \
            '{
              repository_url: $repository_url,
              branch: $branch,
              commit_hash: $commit_hash,
              commit_message: $commit_message,
              commit_author: $commit_author,
              event_type: $event_type
            }')

          curl --fail-with-body --silent --show-error \
            -X POST "${ONYX_WEBHOOK_URL}/api/webhook/" \
            -H "Content-Type: application/json" \
            -H "x-onyx-webhook-secret: ${ONYX_WEBHOOK_SECRET}" \
            --data "$payload"
```

`jq` is preinstalled on GitHub-hosted Ubuntu runners. The `commit_hash` field is
required by the generic payload parser.

## 4. Verify

```bash
# Valid secret -> expected 200
curl --fail-with-body -si -X POST https://<your-onyx-domain>/api/webhook/ \
  -H "Content-Type: application/json" \
  -H "x-onyx-webhook-secret: <secret>" \
  -d '{"repository_url":"https://github.com/<owner>/<repo>.git","branch":"main","commit_hash":"abc123"}' | head -3

# Secret configured but missing from request -> 401
curl -si -X POST https://<your-onyx-domain>/api/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"repository_url":"https://github.com/<owner>/<repo>.git","commit_hash":"abc123"}' | head -3
```

After submission, confirm the event in ONYX and monitor the backend log.

## Payload Reference

For the generic payload path:

| Field | Required | Description |
|---|---|---|
| `repository_url` | yes | HTTPS clone URL; embedded credentials are rejected |
| `commit_hash` | yes | Commit SHA to scan |
| `branch` | no | Branch to scan; defaults to `main` |
| `commit_message` | no | Display metadata |
| `commit_author` | no | Display metadata |
| `event_type` | no | Event label; defaults to `push` |

Aliases accepted by the parser:

- repository: `repository_url`, `repo_url`, `clone_url`
- branch: `branch`, `ref`
- commit: `commit_hash`, `commit`, `sha`

Native GitHub push and pull-request payloads are also parsed when the
`x-github-event` header is present. In that case repository, branch, and commit
data come from GitHub's payload structure.

## Manual Scans

The ingestion endpoint is for SCM events. To trigger a scan as a signed-in user,
call:

```http
POST /api/webhook/scan
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "repository_url": "https://github.com/example/repo.git",
  "branch": "main",
  "scan_types": ["sast", "secrets", "container"]
}
```

The response contains `scan_id`. Poll:

```http
GET /api/webhook/scan/{scan_id}/status
Authorization: Bearer <access-token>
```

Do not send user JWTs to the public SCM ingestion endpoint; use the webhook
secret there.

## Troubleshooting

| Symptom | Fix |
|---|---|
| 503 | `WEBHOOK_SECRET` is unset; set it and restart the backend |
| 401 | Secret mismatch or invalid HMAC; check exact header and raw body |
| 400 | Missing `repository_url` or `commit_hash`, or invalid JSON |
| 429 | Reduce event volume; limit is 20/minute per client |
| 404 on POST | Include the trailing slash on `/api/webhook/` |
| No scan appears | Check backend logs, event status, project access, SCM credentials |
| Workflow fails before curl | Confirm repository variable and secret are configured |
| Payload JSON breaks | Build it with `jq` rather than interpolating untrusted text |

For a suspected secret leak, rotate `WEBHOOK_SECRET`, update GitHub, and review
backend and SCM logs.
