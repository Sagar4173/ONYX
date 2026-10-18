# UX Track Plan 4 — Gates & Live QA (Fix-PR Review Flow)

Date: 2026-10-18 · branch: master · commits: 69d2040 0779d2e 04a7e9e 1a592c1 1cea290 62786ae c10704f (Tasks 1–7) · QA fix: c878e13 (Escape close + focus trap for ConfirmDialog) · review fixes: df883d3 (request timeouts aligned to server budgets; diff retained when the approve response omits it; dialog focus/typed-text hardening; in-hunk `--`/`++` diff lines; `role="alert"` on run-kept errors)

Plan: `docs/superpowers/plans/2026-10-18-ai-surfaces-ux-phase04.md` (approved 2026-10-18, amendments A1–A6). Phase 4 is frontend-only plus one new dependency (`react-diff-viewer-continued@4.4.0`, peer `@emotion/react@11.14.0`) — the `POST /reports/{scan_id}/auto-fix` + `approve` endpoints, fix runner, gates, and re-scan verification already existed and were covered by prior backend phases.

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `backend\.venv\Scripts\python.exe -m pytest` | 719 passed (no backend changes) | 719 passed | ok |
| Frontend unit | `npx vitest run` | 303 + new tests | 357/357 (51 files) | ok |
| Frontend lint | `npm run lint` | baseline 2907 err / 10 warn (Δ 0) | 2917 problems = 2907 err / 10 warn | ok |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |
| Storybook build | `npm run build-storybook` | exit 0 | exit 0 | ok |

Notes:

- Final gate re-run at HEAD `df883d3` (after QA + review fixes): `npm test` **357/357 (51 files)**, lint **2907 err / 10 warn** (Δ 0 vs Phase 3 close), `npm run build` exit 0, `npm run build-storybook` exit 0; `npx eslint` + prettier on every file touched by `c878e13` and `df883d3` → clean.
- Suite growth: 303 (Phase 3 close) → 322 after Task 4's dependency install (Tasks 1–3 tests) → 344 after Task 6 → 351 after the QA fix → **357** after review fixes. No pre-existing tests were modified except the two `aiClient` auto-fix assertions extended for the timeout contract.
- Build warnings are pre-existing (chunk-size >500 kB, Vite CJS-deprecation); `react-diff-viewer-continued` bundles cleanly (worker code path builds; real-library smoke test covers jsdom rendering).
- Backend was not re-run after the frontend fixes (no backend changes); its last full run in this phase was 719 passed.

## Tests added (Tasks 1–7 + QA/review fixes, all TDD)

- `aiClient.test.js` +0 net (2 existing auto-fix tests extended: propose posts `finding_id` query param + `timeout: 120000`; approve posts `timeout: 600000` — review fix F1)
- `fixDiff.test.js` +7 (single hunk split/counts; CRLF + no-newline marker; **in-hunk `--`/`++` content lines** from review fix F5; null/empty; gap marker; truncation cap; Infinity expansion)
- `useFixRun.test.jsx` +12 (classifyFixError matrix + sanitization; idle mount; propose pending-scoped + toast; propose error clears run; approve→verified + toast; **diff retained when approve response omits it** from review fix F2; race clears run; 502 keeps run; reject toast; cache restore on remount with 0 calls; per-finding pending scoping)
- `FixDiffViewer.test.jsx` +4 + `FixDiffViewer.smoke.test.jsx` +1 (mocked unit: texts/truncation/empty state; **real-library smoke** against `react-diff-viewer-continued` proving async worker compute resolves in jsdom)
- `FixStatusRail.test.jsx` +6 (four statuses, `aria-current="step"` on the li, unknown-status fallback)
- `FixReviewSection.test.jsx` +11 (hidden until activity; propose→diff+rail+actions; type-to-confirm→verified badge; race no-retry; gate 400 + propose-again; dry-run explain + disabled apply; not-verified warning; **diff retention when approve response omits diff** (F2); **no diff area when a run has no diff** (F2); reject flow; **`role="alert"` on run-kept error** (F6); stale-base 400 keeps diff + retry path)
- `FindingDetail.test.jsx` +2 (fix card mounts on rail + section expands on propose; **navigation isolation f-1→f-2 — no auto-propose, state does not bleed**)
- `ConfirmDialog.test.jsx` +9 (new file from QA fix `c878e13` + review fixes F3/F4: null when closed; Escape closes; Tab wrap; initial focus without input; autofocus preserved with type-to-confirm; typed gate; **no focus bounce when onClose identity changes** + latest onClose used (F3); **typed text resets on reopen** (F4); focus restored to opener on close)

## Live QA walkthrough (2026-10-18 evening — Playwright MCP against uvicorn :8000 + Vite :5173, report `qa-live-check-001`, finding `qa-f-001`, user `qa.live@example.com`)

12 scenarios, all PASS after fixes:

- [x] **Real propose (no `AUTO_FIX_TOKEN`)** — "Last attempt failed" badge, section expands, `role="alert"` "Auto-fix could not run" + real git-clone detail (repo 404 from `example/qa-demo-app`), "Propose again" offered. Graceful, no stack trace, 1 expected browser network console entry (400)
- [x] **Full lifecycle** (canned awaiting_approval → approve → verified): rail step 2 "Awaiting approval" cyan; diff rendered with Split/Unified toggle, hunk header, `+2 −2`, fold controls; Approve/Reject present; approve dialog title "Open a pull request?"; **type-to-confirm gate**: confirm disabled → disabled at "APPROV" → enabled at "APPROVE"; verified render: full-width badge sweep (`data-testid="verified-sweep"`), "Verified — re-scan no longer detects this finding", "PR #42" link → correct GitHub href, branch `onyx-fix/qa-f-001`, model footer, rail step 4 active
- [x] **Dry-run** — rail step 1 "Proposed" only; "Apply fix" disabled with explanation "Dry-run mode / Apply is unavailable while dry-run mode is on."; no Approve/Reject
- [x] **Race 400 on approve** — "No pending fix for finding qa-f-001" → inline "Already handled elsewhere" + detail, run cleared, **no retry button**, card back to "Propose fix"
- [x] **Gate 400 on propose** — "Fix agent produced a patch over the 50-line cap" → "Auto-fix could not run" + detail + "Last attempt failed" badge; "Propose again" issued a 2nd request (counted), error re-shown
- [x] **Approval flow off** (`auto_fix_requires_approval: false` via `/api/ai/features` fulfill) — Propose disabled, title tooltip + inline explanation "Approval flow disabled (AUTO_FIX_REQUIRES_APPROVAL=false)…"
- [x] **Reject** — dialog "Reject this proposal?" (no textbox), confirm "Reject proposal" → toast "Proposal rejected — nothing was applied", section collapses, card idle, **no network call**
- [x] **Navigation isolation + cache restore** — propose on `qa-f-001` (awaiting) → Triage tab → `qa-f-002`: section hidden, card idle, no auto-propose; back to `qa-f-001`: awaiting state + diff restored from cache with **no new request**
- [x] **Keyboard** — diff region `tabindex="0"` focusable; dialog autofocuses the type-to-confirm input; keyboard-typed APPROVE enables confirm; Tab order input→Cancel→confirm; **Escape closes the dialog** (after QA fix `c878e13`) leaving the run intact; focus returns to opener
- [x] **Reduced motion** — `prefers-reduced-motion: reduce` emulation: verified badge renders statically, sweep element absent (`count = 0`)
- [x] **Console** — entire multi-scenario session: 4 console error entries, all expected browser network logs for intentional 400s; 0 application errors
- [x] **Mobile 375×812** — Unified view auto-selected (`aria-pressed`), 0px horizontal overflow, rail stacks above the review section

### QA method notes

- Canned lifecycle/error sims via Playwright `page.route` fulfill with `access-control-allow-origin` (+ `OPTIONS` preflight handling for the bearer-auth POSTs). Process-kill/token-injection not available in this environment — same approach as Phases 2–3.
- The long session hit the documented refresh-token expiry (redirect to `/`); re-login worked normally. Not a Phase 4 issue.
- One tooling quirk: Playwright's aria snapshot omitted the name of icon+text buttons (`Propose fix`) while the live DOM and RTL ARIA assertions both resolve it — verified via `textContent` + accessible-name queries; not an app issue.

## Live QA findings resolved

- **ConfirmDialog had no Escape handling and no focus trap** (`c878e13`, found by live keyboard QA): the shared `ConfirmDialog` predates Phase 4 and (unlike `Modal`) implemented neither. Fixed by mirroring `Modal`'s proven handler (Escape → onClose, Tab/Shift+Tab wrap, initial focus, restore on close) with a new 7-test `ConfirmDialog.test.jsx`. Blast radius: 2 consumers (`RetentionConfirmDialog`, `FixReviewSection`); both re-tested. Re-verified live: Escape closes the approve dialog, run preserved.
- **Approve response omits `diff`** (review fix F2, `df883d3`): the backend `_open_pr` result carries no diff, so the highest-stakes success state showed "No changes" above the PR card. Fixed by merging (`run.diff || prev.run?.diff`) + section gating; re-verified live: diff remains visible after approve-without-diff, no false "No changes", PR card + badge intact.

## Independent review (2026-10-18)

- Verdict: **APPROVE WITH FIXES** over `7c236d8..c878e13` (8 commits, 24 files). Confirmed correct: error sanitization (no raw axios leakage), the enabled:false no-polling query (no GET on mount, restore-on-remount, no 30s paid polling), per-finding pending scoping, race/stale semantics, XSS/`rel="noopener"` hygiene, worker bundling. Verifier independently re-ran: frontend 351/351, touched-file eslint clean, production build exit 0.
- Fixes applied in `df883d3` (all TDD, 9 new failing assertions → green):
  - **F1 (High)** — propose/approve inherited the global 30s axios timeout while server budgets are 300–600s (and the UI copy itself says "up to a minute"): misleading "network error" + PR could complete server-side after client abort. Per-request timeouts now 120s (propose) / 600s (approve = server `GIT_SCAN_TIMEOUT`), asserted in tests.
  - **F2 (Medium)** — diff retention (above).
  - **F3 (Low)** — dialog re-focused the first control when parent re-renders every 30s (unstable `onClose` identity): `onClose` now behind a ref with `[isOpen]`-only deps; regression test observes the focus-restore bounce via a focus listener.
  - **F4 (Low)** — typed confirm text persisted across dialog close/reopen, defeating type-to-confirm on repeat use: reset on close + test.
  - **F5 (Low)** — parser dropped in-hunk lines starting `---`/`+++` (e.g. removed SQL comments): header-skip now only before the first hunk + test.
  - **F6 (Low)** — run-kept inline errors (502 etc.) lacked a live region: `Alert` gained an optional `role` prop, the run-kept error uses `role="alert"` + assertion. (`AIStateBlock` error variant already had it.)
- Recorded, not fixed (Phase-5 candidates / nits): unknown fix status silently maps to step 1 (no test); `gate_failures` keyed by message (duplicates would warn); no explicit "never polls" regression test (the `enabled: false` query makes polling impossible but Phase 3 added an analogous test for the same trap); double-submit Approve unguarded (server claim makes it safe; dialog close guard covers the common path); after a full page reload an already-opened PR is not re-hydrated from the backend's persisted `fix_pr_url`/`fix_status` — the frontend never reads them (deliberate: no GET endpoint exists for fix runs); the module-level QueryClient survives logout within a tab (pre-existing pattern; fix-run cache gcTime 30 min).

## Behavioral notes (not defects)

- Navigating away and back within the SPA restores the fix run (cache-backed by design; `gcTime` 30 min, keyed `["fix-run", scanId, findingId]`) — contrast with Phase 3's investigate panel which intentionally resets. The plan's "navigation isolation" requirement is about **no auto-run and no cross-finding bleed**, both verified.
- Race/not_found errors are inline-only (no toast) by design; propose/approve/reject successes toast; approve 502 keeps the run and shows the inline alert.
- "Propose again" after a terminal error is intentionally offered for gate/agent 400s, 502/503, and network errors; never for race/not_found.

## Deliverables beyond the web app

- Storybook: `AI/FixStatusRail` (4 statuses), `AI/VerifiedBadge` (with/without total), `AI/FixDiffViewer` (typical, truncated 15-hunk, empty) — `npm run build-storybook` exit 0.
- Dependency: `react-diff-viewer-continued@^4.4.0` + peer `@emotion/react@^11.14.0` (the only new runtime deps; `npm ls` clean; lockfile committed in `1a592c1`).
