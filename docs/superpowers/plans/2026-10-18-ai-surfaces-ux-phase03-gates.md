# UX Track Plan 3 — Gates & Live QA (Investigate Agent)

Date: 2026-10-18 · branch: master · commits: 362b2b5 ff232b5 805f7b0 37c9091 089c05a d16dcca d4a222d (Tasks 1–7) · QA fix: 1ed519f (prevent investigate query from polling the paid agent) · review fixes: 08fb695 (reset panel per finding; cover unmapped errors)

Plan: `docs/superpowers/plans/2026-10-18-ai-surfaces-ux-phase03.md` (approved 2026-10-18). Phase 3 is frontend-only — the `POST /api/ai/investigate` endpoint, agent, screening, quota decorator, and kill switch already existed and were covered by prior phases' backend work.

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `backend\.venv\Scripts\python.exe -m pytest` | 719 passed (no backend changes) | 719 passed | ok |
| Frontend unit | `npx vitest run` | 267 + 36 new = 303 | 303/303 (44 files) | ok |
| Frontend lint | `npm run lint` | baseline 2907 err / 10 warn (Δ 0) | 2917 problems = 2907 err / 10 warn | ok |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |
| Storybook build | `npm run build-storybook` | exit 0 | exit 0 | ok |

Notes:

- All gates were last re-run at HEAD `08fb695` (after the review-fix commit). Earlier runs: `297/297` at `1ed519f` (after the QA polling fix) and `296/296` at `d4a222d`; lint/build results identical in all three.
- Lint spot-check: `npx eslint` + prettier on every file touched by `1ed519f` and `08fb695` → clean except one prettier wrap in the new FindingDetail test, fixed in `08fb695`. Net lint delta across the whole phase: 0 (2907 err / 10 warn, same as Phase 2 close).
- Build warnings are pre-existing (chunk-size >500 kB, Vite CJS-deprecation); no new warnings.
- Backend was not re-run after the frontend fixes (no backend changes in Phase 3); its last full run in this phase was 719 passed.

## Tests added (Tasks 1–7 + QA/review fixes, all TDD)

- `aiClient.test.js` +2 (`runInvestigate` payload shape: question omitted when blank; explicit question passed through)
- `useInvestigate.test.jsx` +6 (disabled until submit; fetch on empty-string question; per-question keys; same-question remount = 0 fetches; **regression: no polling under app-level `refetchInterval: 30000`** from QA fix `1ed519f`; **regression: no refetch on reconnect after failure** from review fix `08fb695`)
- `investigateEvidence.test.js` +7 (path token split, finding-id segmentation, plain text untouched)
- `InvestigateReport.test.jsx` +6 (sections, confidence badge, evidence deep links, model footer, FP-agree button matrix)
- `InvestigatePanel.test.jsx` +12 (submit flow, counter/disable, 400/403 inline alert, 404 no-retry, 429 countdown, 502 no-retry, 503 retry, disabled state; **added in `08fb695`: 404 branch, unmapped 500 + Retry recovery, network-error branch, kill-switch hides a stale error**)
- `FindingDetail.test.jsx` +3 (panel mounted on rail; flag-off disabled state; **added in `08fb695`: panel state resets on finding navigation — integration regression for the review's HIGH finding**) 

## Live QA walkthrough (2026-10-18 evening — Playwright MCP against uvicorn :8000 + Vite :5173, report `qa-live-check-001`, finding `qa-f-001`, user `qa.live@example.com`)

- [x] Panel visible on finding rail — heading "Investigate", description "Read-only agent analysis of this finding.", textarea placeholder, live counter `0/2000`, enabled button (kill switch ON from real `/api/ai/features`)
- [x] Empty-question run → full report renders: Confidence badge, "Blast radius" (+ nested Exploitability), "Evidence" list, "False-positive indicators" empty state, "Recommended actions", model footer `🤖 Investigation by groq/openai/gpt-oss-120b · 3808 tokens`; evidence included a finding-ID deep link (`qa-f-001` → correct href `/report/qa-live-check-001/finding/qa-f-001`)
- [x] Question flow — counter updated live (58/2000), submit ran agent with the question; running state captured atomically: button "Investigating...", `role="status"` skeleton region visible, textarea disabled
- [x] Cost controls — same-question re-click: report preserved, 0 new requests; SPA round-trip (Back to report → Findings tab → re-enter finding): panel remounts in empty state (documented behavior, `submitted` resets), re-submitting restored the cached report in **69 ms with 0 network requests**
- [x] No background polling (regression found in QA, fixed in `1ed519f`) — before the fix the app-level `refetchInterval: 30000` silently re-ran the paid agent every 30s (observed 4 requests/90s incl. 2×503); after the fix, 60s+ idle after success produced exactly **1 request total**
- [x] 429 rate limit — route fulfill with `retry-after: 20` → QuotaNotice countdown "AI requests are limited — retry in 19s.", sr-only "19s remaining", Try again hidden until countdown ends. Method note: the first fulfill lacked `access-control-expose-headers`, so the header was invisible to JS (indeterminate copy shown) — correct CORS semantics; the real backend `app.py` exposes `Retry-After`, and the second fulfill with expose headers proved the countdown path end-to-end
- [x] 502 — "Investigation failed" + server detail text, **no** Retry button (by design)
- [x] 503 → Retry recovery — "Investigation temporarily unavailable" + server detail + Retry; after un-routing, Retry issued a real request and the real report rendered
- [x] 403 blocked question — inline `role="alert"`: "Question blocked by safety screening" + server detail; question text preserved (67/2000), textarea re-enabled for rewrite
- [x] Kill switch — `/api/ai/features` fulfill `investigate_agent_enabled: false` + reload → "Investigate agent disabled" + explanation, textarea and button disabled; restored after un-routing
- [x] Keyboard — Tab walk reaches textarea → Investigate button; focused button shows a visible ring (box-shadow) under keyboard focus (`:focus-visible`)
- [x] Console — happy-path session: **0 console errors** (2 pre-existing warnings). Simulated-failure sims produce expected browser network console entries (Chrome logs 4xx/5xx resources) — not application errors

### QA method notes

- Error/flag simulations via Playwright `page.route` fulfill (with `access-control-allow-origin`; plus expose header where a header must be readable by JS). Process-kill is not permitted in this environment — same approach as Phase 2 QA.
- Request counting via `performance.getEntriesByType('resource')` (persists across SPA navigation) — reliable for the no-extra-request assertions.
- Skeleton/loading capture was done atomically inside one `run_code` call to beat tool round-trip latency (an earlier attempt missed it).

### Not exercised live (unit-covered)

- Agree-FP flow (button → "Your label: False Positive" toast → badge flip → Triage exclusion): both live agent runs returned "No false-positive indicators identified.", so the button never rendered. Covered by `InvestigateReport.test.jsx` + `useLabelFinding`/Triage tests.
- Inline `path:line` Code chips: the agent's live evidence format was "File: app/repository.py lines 42-44" (no leading path token) — the path-splitting util only chips leading tokens by design, so nothing to chip. Covered by `investigateEvidence.test.js`.
- Sibling-finding evidence deep links: the agent referenced only the current finding; the deep-link rendering path is covered by unit tests (and the self-link rendered correctly live).
- Storybook visual pass of `AI/InvestigateReport` stories: stories build cleanly; visual inspection deferred (optional per plan).

## Live QA findings resolved

- **Paid-agent polling** (`1ed519f`): app-level `refetchInterval: 30000` (App.jsx:26) applied to the investigate query → repeated paid provider calls + error/skeleton flicker every 30s. Fixed with `refetchInterval: false` in `useInvestigate` + regression test with an app-default-style QueryClient (`advanceTimersByTime(90s)` must not refetch). Plan doc updated with the global-defaults constraint.
- **Panel state leaked across findings** (`08fb695`, found by independent review, reproduced live): after running on finding A, navigating to finding B (same route component → panel state preserved) kept `submitted`, so the query auto-ran the paid agent for finding B with A's question and showed the stale report. Fixed with `key={`${reportId}:${findingId}`}` on the mount site + integration regression test. Re-verified live with a canned (route-fulfilled) envelope: run on `qa-f-001` → SPA-navigate to `qa-f-002` → request count stayed 1, textarea reset, no stale report.

## Post-fix live re-verification (2026-10-18 late, same environment)

- Finding navigation (canned envelope via `page.route`, no provider cost): run on `qa-f-001` ("nav-test why?") → Back to report → Findings tab → `qa-f-002` → **no auto-run** (performance count unchanged at 1), empty textarea, no stale report, button enabled. PASS.
- Unmapped status branch: route fulfill 500 `{"detail": "Proxy exploded."}` → inline `role="alert"` "Investigation failed / Proxy exploded. / Retry" rendered; 1 expected browser network console entry. PASS.
- Session: the long QA session hit the documented refresh-token expiry (401s → redirect to landing); re-login worked normally. Not a Phase 3 issue.

## Behavioral notes (not defects)

- Returning to the finding remounts the panel empty (`submitted` resets to `null`, a different query key than the cached `""`); re-submitting shows the cached report instantly with zero network. Accepted for Phase 3 (cost control preserved); plan doc wording corrected to match.
- During the 429 fulfill sim, a second `role="status"` region with "Rate limit exceeded. Please try again later." also appeared — pre-existing global toast infrastructure reacting to the API error, independent of the panel's inline QuotaNotice. (Review nit: the same interceptor shows a permissions toast for 403 screening alongside the inline alert — pre-existing wording, not Phase 3 scope.)
- Accepted review nits (not fixed): a previously fetched report stays visible if the kill switch flips off mid-session (viewing prior output costs nothing); a 422 would show a Retry button (harmless).

## Independent review (2026-10-18)

- Verdict: **REQUEST CHANGES → APPROVE**. Review of `371e3d0..1ed519f` found one HIGH cost-control defect (panel state persisting across finding navigation → silent paid auto-run; reproduced live by the reviewer with route-fulfilled calls), plus lows: unmapped statuses (500/422) rendering nothing, `refetchOnReconnect` default re-running failed queries on reconnect, disabled + stale error co-rendering, and gates-doc/test coverage overstatements.
- Resolution: all findings fixed in `08fb695` with 6 regression tests (all verified to fail pre-fix, pass post-fix); gates doc corrections applied (this file). Focused re-review of the delta: **APPROVE** — no blocking issues; `running = isFetching` semantics validated for the retry-while-errored flow; no new issues beyond two accepted nits (above).
- Review notes verified OK: error matrix, key semantics, `enabled` gating, tokenizer safety (no ReDoS, no dangerous HTML, deep links validated against `allFindingIds`), StrictMode tolerance, mock-factory regression risk, a11y roles.

## Final gate re-run after review fixes (HEAD `08fb695`)

- Frontend **303/303 (44 files)**; lint **2907 err / 10 warn** (Δ 0); build exit 0; storybook build exit 0; backend 719 passed (unchanged).
