# Security Follow-ups — Design Spec

Date: 2026-10-20
Status: approved by user ("both: push + security")
Predecessor: post-QA hardening track (closed at `0f9ef31`, pushed)
Source: closure security review (ACCEPTABLE WITH CONCERNS) and final review findings

## Scope

Four workstreams from the hardening closure reviews:

1. **Auto-fix write authorization** — project `viewer` (read-only) must not be able to
   propose/approve/discard fixes through the API; require the project `scan` permission for
   all auto-fix write actions while keeping state reads read-only-accessible.
2. **Error and URL credential hygiene** — stop echoing Git/SCM stderr, provider response
   bodies, and repository URLs in auto-fix 400 details; reject credential-bearing repository
   URLs; redact URL userinfo from report responses and the PDF data path; redact
   `pending_fixes` from the PDF data path.
3. **Whole-metadata writers** — triage cache writes and finding-label writes must not
   persist a stale whole `metadata` snapshot that can erase `pending_fixes`/approval markers.
   Use targeted Mongo updates.
4. **Defense-in-depth + gates** — `frontend/.dockerignore` env exclusions, gate verification,
   security + final reviews, ledger.

## Non-goals

- Historical credential assessment/rotation (`backend/.env.railway` at `783f3ba`) — user/ops
  action; values are never reproduced.
- Binding/authenticating the dev `docker-compose.yml` MongoDB.
- Full RBAC redesign of report reads; other routes keep current behavior.
- Retrofitting project-token resolution (`auto_fix_service._resolve_token`) beyond the authz
  lookup described here.

## 1. Auto-fix write authorization

- New helper in `routes/reports/report_dependencies.py`:

  ```python
  AUTO_FIX_WRITE_PERMISSION = "scan"

  async def user_can_write_auto_fix(report, user_id: str) -> bool
  ```
  - `report.project_id` falsy → allow only when `report.user_id == user_id`
    (personal reports; access was already owner-scoped).
  - `project_id` ObjectId-valid → `Project.get(ObjectId(...))`; else
    `Project.find_one({"project_id": project_id})` (legacy shape).
  - Project missing → allow only when `report.user_id == user_id` (deleted-project race
    cannot grant project-member writes).
  - Else return `project.has_permission(user_id, "scan")` (owner always True).
- `routes/auto_fix.py`: wrap the three write routes (propose, approve, discard) with
  `_write_report_or_403(scan_id, user)` → 404 via existing access check, then
  `403 "Auto-fix requires scan permission on this project"` when denied. `GET` state keeps
  `_report_or_404` only.
- Frontend: `classifyFixError` maps status 403 to kind `forbidden`;
  `FixReviewSection.ERROR_COPY.forbidden` = title "Auto-fix not permitted", description
  "You need scan permission on this project to run auto-fix."

## 2. Error and URL credential hygiene

- New `utils/scrub.py`:
  - `scrub_text(text, limit=300)` redacts URL userinfo (`scheme://user:pass@` →
    `scheme://[REDACTED]@`), known token shapes (`sk-`, `AIza`, `Bearer …`, `ghp_`,
    `glpat-`), and bounds length.
  - `services/ai/gateway.py::_scrub` delegates to `scrub_text` (behavior superset; keeps the
    300-char bound).
- New `utils/url_redaction.py`: `strip_url_credentials(url)` removes userinfo from
  scheme URLs (used for display; scp-style `git@host:path` unchanged).
- `services/scm/auto_fix_service.py`: client-facing `AutoFixError` copies become generic:
  - clone/push: "Git clone failed — check repository access and try again" /
    "Git push failed — check repository access and try again";
  - PR HTTP failures: `(HTTP {status})` only, no `response.text`;
  - platform/parse: no embedded repo URL.
  - Raw exception/provider text is logged only through `scrub_text(..., limit=500)`.
- `utils/repo_clone.py::validate_repo_url`: reject `http(s)` URLs with any userinfo and
  `ssh` URLs with a password (`RepoCloneError` "Repository URL must not embed credentials —
  use a project access token"). `ssh://git@host/...` and scp-style `git@host:path` stay valid.
- `routes/reports/detail.py`, `routes/reports/export.py`, `utils/pdf_generator.py`:
  `repository_url` goes through `strip_url_credentials`; PDF `metadata` uses
  `redacted_report_metadata`.

## 3. Whole-metadata writers

- `services/triage/triage_service.py::_cache_result`: replace the whole-metadata
  `$set` with a targeted update:
  `$set: {"metadata.triage": cache}` (no read-modify-write). Keep the existing
  swallow-and-warn behavior.
- `routes/finding_labels.py`: remove `report.save()`; persist atomically:
  - `update_one({"_id": report.id},
    {"$set": {"scan_results.$[sr].findings.$[f].triage_label": new_label},
     "$unset": {"metadata.triage": ""}},
    array_filters=[{"sr.findings.id": finding_id}, {"f.id": finding_id}])`
  - mirror the label and triage-cache removal in memory; keep the 404 checks and response.
- Tests assert the exact update documents contain no whole `metadata` `$set` and use the
  targeted paths/filters.

## 4. Defense-in-depth + gates

- `frontend/.dockerignore`: add `.env`, `.env.*`, `!.env.example` (keep `.env.local`).
- Gate record `docs/superpowers/plans/2026-10-20-security-followups-gates.md` with counts,
  review outcomes, and residual findings.
- Security + final whole-branch reviews before closure.

## Verification

- Backend: full pytest; new tests for permission helper (owner/member/viewer/missing project),
  route 403s vs 200s, scrub/URL utilities, repo URL rejection, generic SCM errors, credential
  URL redaction in detail/export, triage targeted write, label atomic update.
- Frontend: full vitest; `forbidden` classification + copy.
- Lint 0/10, build exit 0, prettier clean; security + final reviews; ledger updated.
