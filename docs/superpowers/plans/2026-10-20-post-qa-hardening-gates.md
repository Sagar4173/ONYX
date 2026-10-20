# Post-QA Hardening — Gates & Verification Record

Date: 2026-10-20
Spec: `docs/superpowers/specs/2026-10-20-post-qa-hardening-design.md`
Plan: `docs/superpowers/plans/2026-10-20-post-qa-hardening.md`
Branch: `master` (no push during this track)
Start: `fcc4472` (fix-PR track closure, pushed)
Workflow: subagent-driven — one implementer per task, independent `reviewer` per task,
controller-run gate verification, `security` + final whole-branch review at closure.

## Tasks

| # | Scope | Commit | Task review | Additions |
|---|-------|--------|-------------|-----------|
| 1 | Metadata redaction (detail + JSON export) | `d4d0393` | APPROVE | 7 tests (6 helper/route + 1 export) |
| 2 | Atomic pending-map CAS + discard 409 | `c25f17c` | APPROVE WITH CONCERNS | 9 tests; amendment `7b1a648` (retry-refresh test + exact 409 copy) |
| 3 | Atomic outcome write + approval claim | `9e447fe` | APPROVE WITH CONCERNS | 7 tests |
| 4 | Path-aware fix-state reads (end-to-end) | `401c483` | APPROVE WITH CONCERNS → fixes `ad8a1c3` → re-review APPROVE | 3 backend + 2 frontend tests; fix adds navigation-safe cache keys + path-preference pass |
| 5 | Approve in-flight label, propose-again gating, "View PR" copy | `e66cfc8` | APPROVE | 2 test updates (same 14-test file) |
| 6 | `.env` exclusion + gate record + reviews | this commit | — | `.dockerignore` rules |

Design spec commit: `3be9968` (docs only).

## Verification evidence (controller-run, final HEAD before review commits)

Run from `backend`:

- `.\\.venv\\Scripts\\python.exe -m pytest -q` → **791 passed** (55.18s)
  - Baseline at track start: 759. Delta +32 (T1–T4 tests).
- Targeted task runs: T1 12, T2 59→60, T3 67, T4 74 (each passed).

Run from `frontend`:

- `cmd /c "npx vitest run"` → **58 files, 410 tests passed** (40.05s)
  - Baseline: 406. Delta +4 (T4 path-key/navigation tests, T5 label/copy updates net +2).
- `cmd /c "npm run lint"` → **0 errors, 10 warnings** (pre-existing baseline)
- `cmd /c "npm run build"` → **exit 0** (existing chunk-size warning only)
- `cmd /c "npx prettier --check <9 touched frontend files>"` → clean

Repository:

- `git diff --check` clean (whitespace).
- No backend server or live DB was required for the gate suites (all unit/route tests).

## Design decisions recorded during the track

- Whole-pending-map CAS is mandatory: scanner finding ids are rule ids containing dots
  (`python.lang.security…`), so dotted `$set` paths on `pending_fixes.<id>` are unsafe.
- Array-filtered outcome writes put ids only in filter *values* (`$[e].id`/`.rule_id`).
- Redaction is intentionally shallow: `redacted_report_metadata` copies the top level and
  drops `pending_fixes`; nested metadata values are shared, never mutated.
- `get_fix_state` prefers path-matching outcomes (two passes: matching path, then pathless);
  legacy no-`file_path` reads keep first-ident-match behavior.
- `useFixRun` pins the cache key at mutation start (`onMutate` context) so completions after
  navigation cannot write into another finding's cache.

## Accepted limitations / follow-up debt

- DELETE returns `{"status": "discarded"}` after CAS exhaustion even though the entry may
  remain (brief-mandated; misleading-but-recoverable UX, no data loss). Candidate follow-up:
  tri-state result or 409/503 on exhaustion.
- `$exists: False` CAS filter cannot repair a pre-existing `null`/non-dict `pending_fixes`
  field; unreachable through current writers.
- Success-removal CAS miss leaves the fresh claim marker until the 900s TTL
  (never-clobber requirement; disclosed by T3 review).
- Outcome write prefers `id` in memory but matches `id` or `rule_id` in the DB; entries
  carrying both with conflicting values are not updated in memory (no production shape).
- No real-Mongo integration test for embedded-document CAS equality or `arrayFilters`;
  filters/updates are asserted exactly against fake collections.
- Existing non-goals unchanged: composite finding ids, outcome-masks-pending behavior,
  cross-process locking, PDF redaction.

## Security review

Pending at time of this commit.

## Final whole-branch review

Pending at time of this commit.
