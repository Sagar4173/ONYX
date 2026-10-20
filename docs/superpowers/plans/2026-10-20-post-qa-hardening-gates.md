# Post-QA Hardening — Gates & Verification Record

Date: 2026-10-20
Spec: `docs/superpowers/specs/2026-10-20-post-qa-hardening-design.md`
Plan: `docs/superpowers/plans/2026-10-20-post-qa-hardening.md`
Branch: `master` (no push during this track)
Start: `fcc4472` (fix-PR track closure, pushed)
Workflow: subagent-driven — one implementer per task, an independent `reviewer` subagent
dispatched by the controller after each task (the implementer environment itself has no
reviewer tool), controller-run gate verification, `security` + final whole-branch review at
closure.

## Tasks

| # | Scope | Commit | Task review | Additions |
|---|-------|--------|-------------|-----------|
| 1 | Metadata redaction (detail + JSON export) | `d4d0393` | APPROVE | 7 tests (6 helper/route + 1 export) |
| 2 | Atomic pending-map CAS + discard 409 | `c25f17c` | APPROVE WITH CONCERNS | 10 net backend tests; amendment `7b1a648` adds retry-refresh test + exact 409 copy |
| 3 | Atomic outcome write + approval claim | `9e447fe` | APPROVE WITH CONCERNS | 7 tests |
| 4 | Path-aware fix-state reads (end-to-end) | `401c483` | APPROVE WITH CONCERNS → fixes `ad8a1c3` → re-review APPROVE | +4 backend, +2 frontend initially; fix adds +3 backend, +2 frontend (navigation-safe cache keys, path preference) |
| 5 | Approve in-flight label, propose-again gating, "View PR" copy | `e66cfc8` | APPROVE | 0 new tests; existing 14-test file assertions updated (net +0) |
| 6 | `.env` exclusion + gate record + reviews | `99e9206` | — | `.dockerignore` rules + this record |
| 6a | Closure fixes: claim guard, post-PR restore, discard copy, diagnostics | `d01b192` + `2928aa0` | APPROVE (re-review) | +6 backend, +1 frontend; `2928aa0` corrects outcome no-op detection to `modified_count` |

Design spec commit: `3be9968` (docs only).

## Verification evidence (controller-run)

At `99e9206` (pre-closure-fix gate):

- `pytest -q` (backend) → 791 passed.
- `npx vitest run` (frontend) → 58 files / 410 tests passed.

At final code HEAD `2928aa0`:

- `pytest -q` (backend) → **797 passed** (32.11s)
- `cmd /c "npx vitest run"` → **58 files, 411 tests passed** (43.98s)
- `cmd /c "npm run lint"` → **0 errors, 10 warnings** (pre-existing baseline)
- `cmd /c "npm run build"` → **exit 0** (existing chunk-size warning only)
- `npx prettier --check <9 touched frontend files>` → clean
- `git diff --check` → clean

Delta from track start: backend 759 → 797 (+38); frontend 406 → 411 (+5).
Baselines were corroborated at the tracked start and by per-commit runs rather than re-run at
`fcc4472`; targeted counts: T1 12, T2 59→60, T3 67, T4 74, T6 fixes 80 (backend) and 20 (hook).

No backend server or live DB was required for the gate suites (all unit/route tests).

## Design decisions recorded during the track

- Whole-pending-map CAS is mandatory: scanner finding ids are rule ids containing dots
  (`python.lang.security…`), so dotted `$set` paths on `pending_fixes.<id>` are unsafe.
- Array-filtered outcome writes put ids only in filter *values* (`$[e].id`/`.rule_id`).
- Redaction is intentionally shallow: `redacted_report_metadata` copies the top level and
  drops `pending_fixes`; nested metadata values are shared, never mutated.
- `_store_pending` refuses to replace a pending entry carrying a fresh approval claim
  (`FixConflictError` → 409); stale claims (> 900s) remain replaceable.
- `get_fix_state` prefers path-matching outcomes (two passes: matching path, then pathless);
  legacy no-`file_path` reads keep first-ident-match behavior.
- `useFixRun` pins the cache key at mutation start (`onMutate` context) so completions after
  navigation cannot write into another finding's cache.
- Post-PR removal failure is logged and still returns success; the claim is never restored
  after `_open_pr` returns.

## Accepted limitations / follow-up debt

- DELETE returns `{"status": "discarded"}` after CAS exhaustion even though the entry may
  remain (brief-mandated; recoverable UX, no data loss). Candidate follow-up: tri-state or
  409/503 on exhaustion.
- `$exists: False` CAS filter cannot repair a pre-existing `null`/non-dict `pending_fixes`
  field; unreachable through current writers.
- Success-removal CAS miss leaves the fresh claim marker until the 900s TTL
  (never-clobber requirement; disclosed by T3 review).
- Outcome write prefers `id` in memory but matches `id` or `rule_id` in the DB; entries
  carrying both with conflicting values are not updated in memory (no production shape).
- The propose conflict check runs inside `_store_pending`, after the fix agent completes:
  integrity is preserved, but a conflicting propose still pays clone/LLM cost before the 409.
- `_open_pr` creates the remote PR and then records the outcome before returning. If that
  internal step raises (or `_create_pr` succeeds remotely but raises), `approve_fix` still
  releases the claim; a retry could open a duplicate PR. Narrow debt; requires remote success
  followed by an outcome/API failure. Fix would need branch/PR idempotency.
- Pre-existing whole-metadata writers can clobber auto-fix state: triage cache
  (`services/triage/triage_service.py` `$set: {"metadata": meta}`) and finding-label saves
  (`routes/finding_labels.py` `report.save()`). Out of this track's scope; undermines the
  claim guarantee under concurrent triage/label traffic.
- No real-Mongo integration test for embedded-document CAS equality or `arrayFilters`;
  filters/updates are asserted exactly against fake collections.
- Existing non-goals unchanged: composite finding ids, outcome-masks-pending behavior,
  cross-process locking, PDF redaction.

## Security review

Verdict: **ACCEPTABLE WITH CONCERNS** at `99e9206`, with the medium claim-integrity finding
addressed in `d01b192` (propose fresh-claim 409 guard + no restore after PR). Positive
controls: pending-fix redaction at both report surfaces, `file_path` confined to in-memory
filtering after report authorization, no NoSQL operator injection path, exact-CAS restore,
`.dockerignore` rules effective for the `./backend` build context, and the auto-fix GET safe
subset.

Residual findings (not introduced by this track unless noted):

- **MEDIUM (pre-existing)** — auto-fix write endpoints authorize by report *read* membership
  (`routes/reports/report_dependencies.py`); project `viewer` role has no permission check, so
  a viewer can propose/approve/discard via the API and cause branch/PR side effects. Fix:
  dedicated auto-fix permission dependency + viewer-denied tests.
- **LOW** — raw SCM/Git error text (clone/push stderr, provider HTTP bodies, repo URLs) is
  returned as the 400 detail and rendered (`routes/auto_fix.py`, `services/scm/auto_fix_service.py`).
  Map to generic client copy, scrub server-side, log sanitized detail.
- **LOW** — credential-bearing repository URLs (`https://TOKEN@host/...`) pass
  `validate_repo_url`, are echoed in report detail/export, and can appear in errors. Reject or
  strip userinfo; prefer header-based token auth; rotate any token stored this way.
- **INFO** — `frontend/.dockerignore` does not exclude `.env*` (current frontend env holds only
  public `VITE_*` values); `pdf_generator` still loads raw metadata internally (not rendered);
  `docker-compose.yml` publishes unauthenticated Mongo on 27017 (dev posture).
- **HISTORICAL** — `backend/.env.railway` at `783f3ba` contained non-placeholder-looking
  `MONGODB_URI`/`SECRET_KEY` values and was later removed. Values were not reproduced or
  validated. If that history was ever shared/pushed, assess and rotate those credentials.

## Final whole-branch review

Verdict at `99e9206`: **APPROVE WITH CONCERNS** (no Critical/High). Both track-code Mediums
(`_store_pending` claim overwrite and post-PR removal restore) were fixed in `d01b192`; the Low
items (discard error classification, refresh/outcome diagnostics) were also fixed there, and
the outcome no-op counter was corrected in `2928aa0`. Remaining accepted debt: Low-severity
track items (DELETE exhaustion copy, `_open_pr` post-PR window, doc/test gaps — real-Mongo
integration, separate-instance concurrency) plus the pre-existing security findings above
(including the Medium auto-fix write-authorization gap and the whole-metadata clobber), which
remain outside this track's scope.

Re-review verdict after fixes: **APPROVE** (both Mediums closed, Lows closed, no regressions;
full suites green).

Gates record corrections applied in this revision (per final review): per-task test deltas
above corrected; workflow wording clarified; security/final records added.
