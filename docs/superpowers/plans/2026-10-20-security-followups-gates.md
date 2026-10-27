# Security Follow-Ups - Gates & Verification Record

Date closed: 2026-10-27
Spec: `docs/superpowers/specs/2026-10-20-security-followups-design.md`
Plan: `docs/superpowers/plans/2026-10-20-security-followups.md`
Branch: `master` (nothing pushed during this track)
Start: `0f9ef31` (post-QA hardening closure, pushed)
Finish: `16100de`
Workflow: one implementer task at a time with an independent `reviewer` pass, controller-run
gates, a `security` review at closure, and a final whole-branch review. Post-review fixes
were re-reviewed by `security`.

## Tasks

| # | Scope | Commit | Review |
|---|-------|--------|--------|
| 1 | Auto-fix write authorization + forbidden UX | `e5a344e` | APPROVE WITH CONCERNS |
| 2 | SCM/URL credential hygiene | `25ac6a7` | APPROVE WITH CONCERNS (3 rounds) |
| 3 | Targeted triage/label metadata writes | `f81304e` | APPROVE WITH CONCERNS |
| 4 | Frontend image env exclusion | `fb4abfd` | Gate-only |
| 5 | Security-review fixes: project-bound tokens, path traversal, SCP/URL redaction, host allowlist | `2a40ef9` | Security re-review: ACCEPTABLE WITH CONCERNS |
| 6 | Review follow-ups: SSH multi-`@`, scanner clone paths/cleanup, legacy token lookup, repeated-scp redaction | `ee579e1` + `16100de` | Reviewer follow-up: APPROVE WITH CONCERNS; non-residual lows fixed |

Design/plan commit: `e3fb6e2`.

## Verification evidence (controller-run)

At frontend commit `fb4abfd`:

- `pytest -q` (backend) -> **876 passed**.
- `cmd /c "npx vitest run"` (frontend) -> **58 files / 413 tests passed**.
- `cmd /c "npm run lint"` -> **0 errors, 10 warnings** (pre-existing baseline).
- `cmd /c "npm run build"` -> **exit 0** (existing chunk-size warning only).
- `npx prettier --check <T1 frontend files>` -> clean.

At final code HEAD `16100de`:

- `pytest -q` (backend) -> **903 passed** (35.00s).
- Focused security suites (`test_auto_fix_service`, `test_repo_clone_validation`,
  `test_scrub`, `test_url_redaction`, `test_real_scanner_paths`) -> **106 passed**.
- `ruff check` on all touched backend files -> clean.
- `git diff --check 0f9ef31..HEAD` -> clean.
- Frontend gates not re-run after `fb4abfd` because no frontend files changed afterwards.

No live MongoDB, SCM host, or clone/push operation was used; verification is unit/route
level with mocked external boundaries.

## Design decisions

- Auto-fix writes require project `scan` permission; personal reports stay owner-only.
  A missing project falls back to owner-only per the approved spec (see residual risk).
- Auto-fix token resolution is project-bound: a token is returned only when the report
  repository URL matches the project repository URL after stripping credentials, query
  data, trailing slashes, and `.git`. There is no global token fallback.
- `AUTO_FIX_TOKEN` was removed from settings and `.env.example`. Auto-fix PR creation now
  requires a per-project `repository.access_token`.
- PR API calls are limited to exact public hosts (`github.com`/`www.github.com`,
  `gitlab.com`/`www.gitlab.com`; Bitbucket is detected but still unsupported for PR
  creation). Self-hosted/lookalike hosts fail closed instead of sending tokens to a public
  SaaS API.
- Clone paths are derived from parsed URL/scp paths, sanitized to `[A-Za-z0-9._-]`, and
  the resolved clone directory is checked against the temp base directory. The scanner
  creates a unique per-scan directory with `tempfile.mkdtemp` and removes it on clone
  failure.
- Multiple-`@`/encoded SSH userinfo, bracketed IPv6 scp hosts, and credential-bearing scp
  URLs are rejected; standard, protocol-relative, repeated-userinfo, and repeated-scp
  credentials are redacted by `scrub_text`/`strip_url_credentials`.
- Legacy non-ObjectId report project ids use the same `project_id` lookup as the T1
  authorization helper; the repository-URL match still gates token release.
- Triage cache and finding-label writes use targeted `$set`/`$unset`/array-filter updates
  instead of whole `metadata` or whole-report saves.

## Security review

Initial verdict: **CHANGES REQUIRED**. HIGH finding: a personal report could trigger
auto-fix, the broken `project_id` lookup fell back to the global `AUTO_FIX_TOKEN`, and the
token was embedded in a clone URL for an attacker-controlled repository. This was the
global-token exfiltration chain fixed in `2a40ef9`.

Re-review of `2a40ef9`: **ACCEPTABLE WITH CONCERNS**. Confirmed resolved:

- HIGH global-token exfiltration.
- MEDIUM self-hosted SCM tokens being sent to public SaaS APIs.
- LOW Windows clone-path traversal.
- LOW scp/multiple-`@` credential leakage and protocol-relative scrub gaps.
- LOW bracketed IPv6 scp host validation.

No new critical/high issue was found. A reviewer follow-up on `ee579e1` confirmed the
targeted fixes and found one temp-directory cleanup regression plus a repeated-scp display
redaction gap; both were fixed in `16100de`. Residual findings are listed below.

## Accepted limitations / follow-up debt

- **LOW (security)** - SCM tokens are still embedded in clone/push URLs; Git records the
  clone URL in `.git/config` and it can appear in process diagnostics. Prefer
  `GIT_ASKPASS`/credential helper and repository-scoped short-lived tokens.
- **MEDIUM (pre-existing, final review finding 1)** - Credential-bearing repository URLs
  can still reach surfaces outside clone-time validation: project create/update
  (`models/project.py`, `routes/projects/crud.py`), report submission/schema/response/logs
  (`routes/webhook/schemas.py`, `routes/webhook/scan_operations.py`), webhook event
  responses (`routes/webhook/events.py`), and scanner logs/naming
  (`services/scanning/scanners/real_scanner.py`). The final review output was truncated
  after this finding in the controller transcript; retrieve the full task result if a
  complete list is required.
- **LOW (spec-mandated)** - `user_can_write_auto_fix` falls back to owner-only when a
  project lookup definitively returns no project. The security review flags this
  fail-open behavior; it is retained because the approved spec and T1 tests require it.
  The plan wording ("report owner always allowed") differs from the stricter
  project-permission behavior in the spec; the spec is authoritative.
- **MEDIUM (pre-existing)** - The finding-label endpoint requires only report read access,
  so a project viewer can still label/hide findings. Follow-up authorization change.
- **LOW** - Remaining T2 gaps: other raw webhook-processor URL logs, missing route-level
  admin/listing redaction tests, query parameters beyond the five known keys not scrubbed,
  PDF binary not parsed, and approve/discard 403 responses still expose retry affordances.
- **LOW** - No real-Mongo integration test for the array-filtered label update or the
  project-bound token path; filters and lookups are asserted with fakes/mocks.
- **Operational** - Removing `AUTO_FIX_TOKEN` is a behavior change for deployments that
  relied on the global token. Remove the variable from deployed secret stores and rotate
  any token that was configured. Self-hosted GitHub/GitLab PR creation is no longer
  supported by auto-fix (it previously attempted a public SaaS API call).
- **INFO** - `docker-compose.yml` publishes unauthenticated Mongo for development only;
  historical `backend/.env.railway` values should be assessed/rotated if that history was
  shared. No live QA/SCM clone/push re-test was performed in this track.

## Completion criteria status

- Authorization: viewer gets 403 on auto-fix writes and can read state; owner/scanner
  behavior covered by tests.
- No client-visible raw SCM error text; credential URLs are rejected at clone validation
  and redacted at the covered display/log surfaces.
- Triage/label writes preserve unrelated metadata keys.
- Gates pass; security review accepted with documented residuals; final review approved
  with concerns; ledger updated.
