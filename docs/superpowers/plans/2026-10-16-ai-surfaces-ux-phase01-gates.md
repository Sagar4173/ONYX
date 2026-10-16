# Plan 1 Gate Results (Phase 0 + Phase 1)

**Date:** 2026-10-16 · **HEAD:** e415608 (controller gates run after Task 8; Task 9 record)

| Gate | Result |
|---|---|
| Backend suite | **712 passed** (708 baseline + 2 citation + 2 features) — `pytest tests/ -q`, 25.86s |
| Evals | **36 passed** — `pytest evals/ -q -m eval` |
| Frontend tests | **213 passed (27 files)** — `npm test` |
| Frontend lint | **2951 errors / 10 warnings** vs recorded baseline 2955/10 → **delta −4 errors, 0 new** (delta gate per Global Constraints; 0 errors deferred to prettier-baseline-reset chore) |
| Frontend build | **exit 0** (`npm run build`; pre-existing chunk-size + CJS-deprecation warnings only) |
| Storybook build | exit 0 (run during Task 6; `AI/` stories collect) |
| Visual QA (7 checks) | see below |

## Visual QA checklist

| # | Check | Result |
|---|---|---|
| 1 | Chat streams tokens visibly with caret; Stop mid-stream keeps partial + "Partial response" note | **DEFERRED** — needs running API + auth + existing scan + configured AI provider; API cold-start in this environment blocks on threat-feed (CISA KEV/OSV/GitHub advisory) network ingestion. Behavior unit-tested (Task 7 suite: stop swap, settle partial path). Schedule live pass before UX Track sign-off. |
| 2 | Citation chips appear during streaming as `[n]…` and hydrate to full labels on completion | **DEFERRED** (same session constraints). parseSegments + hydration unit-tested (Task 8 suite). |
| 3 | Chip click opens CWE side-panel modal with source text; Esc closes; focus returns to chip | **DEFERRED** for live chat (same constraints); panel dialog role + Esc→onClose unit-tested; Modal focus-restore verified in primitive (StyleComponents.jsx:416,438). |
| 4 | 429 shows countdown notice; error states show retry | **PARTIAL** — QuotaNotice countdown verified live in Storybook (`AI/QuotaNotice` ticking: "retry in 19s" observed); full 429-over-the-wire needs live API. |
| 5 | All new motion neutralized under OS reduced-motion | **BY CONSTRUCTION + inspection** — all new motion rides existing Skeleton/Spinner CSS classes covered by the global `*`-selector kill-switch (index.css:596-601); no new framer-motion in primitives. OS-toggle pass deferred with #1. |
| 6 | Keyboard: Tab reaches input/send/chips/panel close; Enter sends; screen-reader announcer reads completed answer once | **PARTIAL** — chips are native buttons (aria-labels verified in Storybook: "Citation 1: CWE-89: SQL Injection"); Enter-to-send + aria-live single-announcement unit-tested; full Tab-order walk deferred with #1. |
| 7 | Storybook: `AI/AIStateBlock`, `AI/QuotaNotice`, `AI/CitationChip` stories render all variants | **PASS** — verified in browser (Storybook 6006): AIStateBlock Loading (role=status + skeleton), QuotaNotice With Countdown actively ticking, CitationChip Hydrated with correct aria-label; 0 console errors. |

## Follow-ups recorded

1. Live visual-QA pass for checklist items 1-6 in an environment with a warm API, auth session, existing scan, and configured AI provider — required before UX Track sign-off (spec success criterion 6).
2. Prettier-baseline-reset chore (`prettier --write` ~2951 auto-fixable errors) so the lint gate can return to strict 0-errors (user-approved deferral 2026-10-16).
3. Backend cold-start: threat-feed ingestion blocks first-boot `/docs` availability >2.5 min in offline-ish environments (pre-existing, out of plan scope).

---

## Fix-round addendum (final-review fixes, same date)

Final whole-branch review (3513ff2..0dd18d1) verdict: **With fixes** — Critical: 429 to QuotaNotice unreachable end-to-end (slowapi emitted no Retry-After; frontend conflated "no header" with "no 429"); Important: QuotaNotice double-announced every countdown tick. User approved backend fix + a11y fix in one round (batched question, 2026-10-16).

**What landed (commit 3d47ab4):**

- `backend/utils/rate_limit.py`: `headers_enabled=True` via `_FastAPILimiter` (skips slowapi's success-path `_inject_headers` when FastAPI passes no `Response`; plain `headers_enabled=True` crashes dict-returning endpoints with "parameter `response` must be an instance of starlette.responses.Response"). 429 handler now emits Retry-After + X-RateLimit-*.
- `backend/tests/test_rate_limit.py`: over-the-wire test: 30/minute login limit exceeded, 429 carries Retry-After + X-RateLimit-Limit/Remaining (hermetic `limiter.reset()` before/after + `require_beanie` override, since the auth router 503s pre-limiter).
- `AIChatPanel`: quota state is now `{ retryAfter } | null`; a 429 always renders QuotaNotice (was hidden when Retry-After was missing); "Try again" via retryLast.
- `QuotaNotice`: "Try again" shows immediately when indeterminate; visible countdown `aria-hidden` with a single sr-only announcement; interval cleared at expiry; no more "retry in 0s" copy (becomes "you can retry now" + "Ready to retry" announcement).
- `aiClient`: `Retry-After: 0` preserved as 0 (was mapped to null); negative values clamped to 0.

**Focused re-review of 3d47ab4: Approved** (all fixes verified, no regressions; targeted re-runs green). Follow-up findings from re-review, both fixed in the follow-up commit below:

- **CORS:** `Retry-After` was not in `expose_headers`, so cross-origin browsers (Vite dev at :5173 against API at :8000, split-domain prod) could not read it and would show only the indeterminate notice. `app.py` now exposes `Retry-After` + `X-RateLimit-*`. Same-origin nginx prod was unaffected. Pre-existing config gap, not introduced by the fix round.
- Mojibake in this addendum repaired (this section rewritten as clean UTF-8/ASCII).

**Residual notes (recorded per re-review):**

- `_FastAPILimiter` overrides slowapi's private `_inject_headers` and relies on its `kwargs.get("response")` wrapper pattern (verified across all call sites in installed slowapi 0.1.10, sync + async wrappers). Slowapi is effectively frozen, but any future bump must re-check `extension.py`.
- The rate-limit test exercises the 429 path; the no-crash success path for dict-returning decorated endpoints is covered indirectly by the wider suite (`test_investigate_route.py` happy path) rather than by a dedicated assertion.
- Screen-reader countdown announces once per second (single channel now); threshold announcements (30/10/5/0) would be optional polish.

**Re-run gates (all green):**

| Gate | Result |
|---|---|
| Backend suite | **713 passed** (+1 new rate-limit test) |
| Evals | **36 passed** |
| Frontend tests | **220 passed (27 files)** (+7 new: quota delegation, aria contract, Retry-After 0/absent/negative, indeterminate retry) |
| Frontend lint | **2951 errors / 10 warnings - delta 0** vs this record; touched files clean (eslint exit 0) |
| Frontend build | exit 0 |

**Still pending:** live over-the-wire visual QA items 1-6 (unchanged: needs warm API + auth + scan + AI provider); item 4's live check now has backend header + CORS exposure + panel unit coverage behind it.

---

## Live visual QA (items 1-6) - 2026-10-17

Environment: backend uvicorn on 127.0.0.1:8000 (fresh process, Atlas `onyx` DB), Vite on 127.0.0.1:5173, Gemini key configured (provider `gemini/gemini-2.5-flash`). QA user `qa.live@example.com` (activated directly in DB; registration flow itself sends welcome/verification mail via the configured SMTP and swallows send failures). Seeded `ScanReport` scan_id `qa-live-check-001` (3 findings: CWE-89 critical, CWE-79 high, CWE-327 medium + AI analysis) owned by the QA user.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Streaming caret + Stop partial | **PASS** | Stop button (`aria-label="Stop response"`) visible from first frame (+3ms); Connecting -> Responding labels; caret `span.animate-pulse` observed mid-stream; input disabled while active; Stop clicked at 561 chars -> "Partial response - connection ended early." shown; button restored to Send |
| 2 | Citation chips during stream + hydrate | **PASS** | Live pending chip observed mid-stream (`aria-label="Citation 2 loading"`, disabled, label `2...`); at `done` frame chips hydrated to full headers (e.g. `Citation 2: CWE-89: Remediation`); raw deltas carried `[[2]]`/`[[3]]` markers pre-hydration (curl trace) |
| 3 | Chip -> CWE panel / Esc / focus | **PASS** (after fix) | Chip click opens `role="dialog" aria-modal="true"` with title `Citation [n] - <header>`, source/CWE badges, source text; Escape closes; focus restored to invoking chip |
| 4 | 429 quota countdown end-to-end | **PASS** | Exactly 30 requests accepted on `/api/ai/chat/stream`, 31st -> 429 with `Retry-After: 23`, `X-RateLimit-Remaining: 0` (cross-origin readable - CORS expose_headers fix); browser send inside window renders QuotaNotice: "retry in 2s." -> "you can retry now." ticking each second; single sr-only announcement ("Rate limit reached. Ready to retry."); "Try again" appears enabled at expiry. Browser logs the 429 fetch as a console error (expected network log, not an app error) |
| 5 | OS reduced-motion | **PASS** (after fix) | Before: framer-motion entrance tweened opacity 0->0.22->0.70->0.97->1 under `prefers-reduced-motion: reduce` (CSS override in index.css does not gate JS animations). After `<MotionConfig reducedMotion="user">` in App.jsx: transform tween suppressed (only start offset + rest observed; no intermediate matrices); opacity fade retained - this is Framer Motion's documented `user` behavior (transforms/layout disabled, opacity kept). CSS animations remain killed by the existing media query |
| 6 | Keyboard / tab order / announcer | **PASS** | Enter in input sends (used throughout QA); send/stop and chips are real buttons (Tab-focusable, focus-visible rings in markup); sr-only `aria-live="polite"` announcer carries `Answer: ...` for completed replies and the quota channel announced once per state (see item 4) |

**Defects found live and fixed in this pass (frontend):**

- **Modal never focused into the dialog on open** (`StyleComponents.jsx`): focus stayed on the invoking chip; the Tab trap only wraps focus already inside the container, so keyboard users could tab through the page behind the dialog. Fix: focus first focusable (fallback: dialog via `tabIndex={-1}`) on open; keep existing trap + restore-on-close. Verified live: focus lands on "Close dialog" button; Esc restores to the invoking chip.
- **Chat auto-scroll scrolled the whole page** (`AIChatPanel.jsx`): `messagesEndRef.scrollIntoView` moved the outer document (captured in screenshot: header/messages scrolled out of view, input row stuck under the tab bar). Fix: container-scoped `listRef` + `el.scrollTo` (with `scrollTop` fallback for jsdom).
- **Framer-motion ignored OS reduced-motion** (`App.jsx`): added `MotionConfig reducedMotion="user"`. Note this is app-wide (all `motion.*` usage), matching the documented Framer semantics.

**Re-run gates after fixes (all green):** frontend tests **220 passed (27 files)**; build **exit 0**; eslint on touched files (`App.jsx`, `AIChatPanel.jsx`, `StyleComponents.jsx`) **exit 0**. Backend untouched this pass (still 713 + 36 evals).

**Residual notes:**

- Pending-chip mid-stream state is model-timing dependent (markers must appear before `done`); observed live once and covered deterministically by unit tests.
- QA artifacts (seeded scan `qa-live-check-001`, QA user) remain in the Atlas `onyx` DB; they are owned by the QA user and do not affect other accounts.
- Backend `.env` on the QA machine now carries real Atlas + SMTP + AI provider credentials; `.env` stays gitignored. The two tracked `.env.example` files are modified (empty AI key slots documented) but intentionally left uncommitted pending a request.

