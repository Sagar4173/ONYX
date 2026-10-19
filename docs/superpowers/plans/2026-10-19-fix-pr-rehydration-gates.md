# Fix-PR State Persistence (Re-hydration) — Gates & Live QA

Date: 2026-10-19/20 — branch: master — commits: d7fd218 (spec) ce3a0df 2c49c2c 90f73ff 78dcc5a 8eac328 5406af5 e60489f (Tasks 1–7) df83e02 138f756 (Task 8a)

Spec: `docs/superpowers/specs/2026-10-19-fix-pr-rehydration-design.md`. Plan: `docs/superpowers/plans/2026-10-19-fix-pr-rehydration.md`. Track closes the "fix state is lost on reload; reject disappears on refresh" limitations of the fix-PR UX track: persisted pending proposals + fix outcomes are now hydrated from `ScanReport.metadata`, and reject/discard is server-persisted.

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `backend\.venv\Scripts\python.exe -m pytest` | 751 passed (Tasks 1–7) + 7 new (Task 8a) = 758 | **758 passed** in 55.82s | ok |
| Frontend unit | `npx vitest run` | 405/405 (58 files) | 405/405 (58 files) | ok |
| Frontend lint | `npm run lint` | 0 err / 10 warn | 0 err / 10 warn | ok |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |
| Prettier | `npx prettier --check` on the four touched frontend files | clean | "All matched files use Prettier code style!" | ok |

Suite growth: backend 734 → 751 (+17 across Tasks 1–4: `tests/test_fix_runner.py` 24, `tests/test_auto_fix_routes.py` 17), then 758 in Task 8a (+7: 4 implementer + 3 controller amendment → `test_fix_runner.py` 31). Frontend 396 → 405 (+9: `aiClient.test.js` 21, `useFixRun.test.jsx` 16, `FixReviewSection.test.jsx` 13, `FindingDetail.test.jsx` 9).

### TDD evidence

- Per-task RED→GREEN records live in `.superpowers/sdd/fix-pr-task-{1..8}-report.md` (untracked) and the ledger. Disclosed quirks: Task 3's RED phase had 2/6 route tests passing coincidentally (404s before the route existed) and Task 4 repeated that pattern; Task 2's RED error text was `ImportError` rather than the brief's `AttributeError` (report-only inconsistency). All tasks landed green on the named suites.
- Task 8a RED: 3 of 4 new/updated tests failed for the expected reason (`get_fix_state` returned `none`; `KeyError: 'fix_status'` in outcome tests); the guard test was green pre-fix by design.

## Implementation summary

- `GET /api/reports/{scan_id}/auto-fix/{finding_id}` → `FixStateResponse` (`status` = `none | awaiting_approval | pr_created | verified`; awaiting → `diff/file_path/model_used/created_at`; outcome → `pr_url`; **never** `patched_content`/`base_sha`). Outcome wins over a still-present pending key; absent returns `"none"` (200).
- `DELETE /api/reports/{scan_id}/auto-fix/{finding_id}` → `{"status":"discarded"}`, idempotent (re-pending a fix is only possible via a later explicit propose).
- Service layer: `get_fix_state` (safe subset) and `discard_pending` in `services/ai/fix_runner.py`; Task 8a added `_entry_matches_finding` (id-or-rule_id + path disambiguation) so outcome records match **real** `metadata.findings` entries (raw scanner dicts carry `rule_id`/`file_path`, not `id`).
- Auth: both routes resolve the report through the shared `_report_or_404` access check (same as propose/approve) → 404 for unknown or foreign scans, 401 unauthenticated.
- Frontend: `autoFixGetState`/`autoFixDiscard` in `aiClient.js`; `useFixRun` hydrates persisted state (`gcTime` 30 min, retry 1, fail-soft to `EMPTY`) and the reject action now calls `autoFixDiscard` (server-side discard) with optimistic UI; `FixReviewSection`/`FixTriggerCard`/`VerifiedBadge` render all four hydrated states; `FindingDetail` shows the section directly on deep-link/reload.

## Live QA walkthrough (2026-10-19/20 — Playwright MCP against uvicorn :8000 + Vite :5173)

Environment: backend restarted mid-QA to load Task 8a (`df83e02`; uvicorn runs without `--reload`). Account: `qa.live@example.com` (password reset via temp script `$TEMP\opencode\onyx-qa-live-reset.py` — **user action: rotate the QA passwords**; literals exist only in local history, nothing pushed). Target: report `qa-live-check-001`, finding `qa-f-001` (`app/repository.py`), state driven by temp seed script `$TEMP\opencode\onyx-qa-fix-seed.py` writing the **real raw entry shape** (`rule_id`/`file_path`).

Scenarios, all PASS:

- [x] **Deep-link hydration (pending)** — full page load (F5-equivalent) of the finding URL renders the Fix-PR card "Awaiting approval" + the "Fix-PR review" section with diff table, "Approve & open PR"/"Reject", and "🤖 Fix by qa/seed" — nothing was clicked first. Screenshot: `.playwright-mcp/qa-fix-pending.png` (untracked).
- [x] **Owner API read** — `GET …/auto-fix/qa-f-001` → 200 `awaiting_approval` with `file_path`, `model_used`, `created_at`, `diff`; raw response contains **no** `patched_content`, `base_sha`, or seeded patch text (safe-subset proof).
- [x] **Cross-user access (live IDOR check)** — the same GET as `qa.admin@example.com` (different user) → **404** "Scan report not found or access denied".
- [x] **Reject persists** — Reject → in-app dialog ("Reject this proposal? …") → "Reject proposal" → section disappears, card back to idle; server `GET` → `none`; **reload stays idle**; a second `DELETE` → 200 `{"status":"discarded"}` (idempotent).
- [x] **PR outcome hydration (real raw shape)** — seed entry `{rule_id: "qa-f-001", file_path: "app/repository.py", fix_pr_url: …, fix_status: "pr_created"}` → API `GET` → 200 `pr_created` + PR URL, no sensitive fields; browser reload renders "PR opened" badge, lifecycle stepper, and link "PR #open" → `https://github.com/example/repo/pull/999`.
- [x] **Clear → idle** — seed cleared → API `GET` → `none` → browser reload renders the idle Fix-PR card (no review section, no badges).
- [x] **Pre-fix boundary witness (why 8a exists)** — with the original id-only matcher, the raw-shape PR entry returned `none` and the browser stayed idle after reload; after `df83e02` + backend restart the same scenario hydrates. This is the live reproduction of the defect below.

### QA method notes

- QA user password was reset through a temp script (user DB record only) because the prior QA track's rotation left the literal unknown; rotate both QA passwords afterwards (carried action).
- Access tokens expired mid-session (re-login) — normal session TTL, not track-related.
- `vite --force` printed a dependency-resolution error for `@emotion/is-prop-valid` (imported by files under `frontend/storybook-static/`): dev-server dep-scan noise from the built Storybook output; the app served fine and all scenarios passed. Pre-existing, unrelated to this track.
- Playwright MCP wrote snapshots/logs to `.playwright-mcp/` (untracked tooling output, outside committed scope).

## Defect found by this QA and fixed in-track (Task 8a)

- **Symptom:** `pr_created`/`verified` outcomes never re-hydrated on real scans (fresh reload showed idle); `awaiting_approval` worked.
- **Root cause:** `process_real_scan` writes `metadata.findings` as raw scanner dicts (`routes/webhook/scan_operations.py:406,499`); those entries carry `rule_id`/`file_path` and **never `id`** (DB probe: 0/87 entries across 8 real reports). `VulnerabilityFinding.id` is assigned the raw `rule_id` (`scan_operations.py:354`). `_record_fix_outcome` (introduced 96055e3a) and the new `get_fix_state` matched `entry["id"]` only → write-side no-op and read-side miss on real data. Unit fixtures had fabricated `{"id": …}` entries, masking it.
- **Fix (`df83e02`):** `_entry_matches_finding` = match on `entry["id"] or entry["rule_id"]` with `file_path` preference (reusing `_path_matches`) when both sides have a path; applied in `_record_fix_outcome` and `get_fix_state`. Fixtures now mirror the production raw shape; +4 tests.
- **Controller amendment (`138f756`):** +3 tests pinning the production invariant (`id == rule_id`), legacy `id` write-side back-compat, and the entry-lacks-path fallback.
- **Review verdict:** APPROVE WITH CONCERNS (independent reviewer; no critical/major findings in the change). Resolved before QA: the seed script's id-only join (temp-file fix) and the stale gate counts in the Task 8 brief (751/24 → 758/31).

## Risks / notes / follow-up debt

- **Duplicate `rule_id` is not a unique finding id (pre-existing):** `_find_finding` and `get_fix_state` return the first occurrence, so on real scans only the first finding with a given rule is addressable end-to-end; `_record_fix_outcome` updates every matching entry, with the path check disambiguating across files when paths are present. Longer-term fix: composite finding ids or a path-aware state endpoint.
- **"PR #open" copy:** hydrated outcome state has no `pr_number` (safe subset), so `FixReviewSection.jsx:54` (`PR #{pr_number ?? "open"}`) renders "PR #open". Cosmetic follow-up (e.g., render "View PR" when the number is unknown).
- **Fail-soft trade-offs (spec-mandated):** a failed hydration GET caches `EMPTY` for up to 30 min; the hook's broad try/catch also covers the mapper (mapper bugs surface as "empty" rather than errors).
- **Minor test gaps (accepted):** route-level outcome test still uses the legacy `id`-shaped entry (thin wrapper, service test covers raw shape); `entry.get("id") or entry.get("rule_id")` lets a truthy stale `id` shadow `rule_id` on hypothetical mixed-shape entries (no such data exists today).
- **Concurrency:** outcome writes are read-modify-write over the whole report (same pre-existing pattern as `approve_fix`); concurrent finishing fixes on one report can lose one outcome. Not exercised in QA; candidate for an atomic `$set` follow-up.
- **Carried from the ML track:** `backend/.dockerignore` still does not exclude `.env` — do not publish images built from a working tree with a real `.env` until fixed.
- **Pending user actions:** rotate QA passwords (`qa.admin@example.com`, `qa.live@example.com`); history purge (if ever wanted) requires explicit approval — nothing has been pushed (`origin/master` is still `bbaaba1`).
