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

Final whole-branch review (3513ff2..0dd18d1) verdict: **With fixes** � Critical: 429?QuotaNotice unreachable end-to-end (slowapi emitted no Retry-After; frontend conflated "no header" with "no 429"); Important: QuotaNotice double-announced every countdown tick. User approved backend fix + a11y fix in one round.

**What landed:**
- `backend/utils/rate_limit.py`: `headers_enabled=True` via `_FastAPILimiter` (skips slowapi's success-path `_inject_headers` when FastAPI passes no `Response` � plain `headers_enabled=True` crashes dict-returning endpoints). 429 handler now emits Retry-After + X-RateLimit-*.
- `backend/tests/test_rate_limit.py`: over-the-wire test � 30/minute login limit exceeded ? 429 carries Retry-After + X-RateLimit-Limit/Remaining (hermetic limiter reset + `require_beanie` override).
- `AIChatPanel`: quota state is now `{ retryAfter } | null` � a 429 always renders QuotaNotice (was hidden when Retry-After missing); "Try again" via retryLast.
- `QuotaNotice`: "Try again" shows immediately when indeterminate; visible countdown `aria-hidden` with a single sr-only announcement; interval cleared at expiry; no more "retry in 0s" copy (? "you can retry now" + "Ready to retry" announcement).
- `aiClient`: `Retry-After: 0` preserved as 0 (was mapped to null).

**Re-run gates (all green):**

| Gate | Result |
|---|---|
| Backend suite | **713 passed** (+1 new rate-limit test) |
| Evals | **36 passed** |
| Frontend tests | **219 passed (27 files)** (+6 new: quota delegation, aria contract, Retry-After 0/absent, indeterminate retry) |
| Frontend lint | **2951 errors / 10 warnings � delta 0** vs this record; touched files clean (eslint exit 0) |
| Frontend build | exit 0 |

**Still pending:** live over-the-wire visual QA items 1-6 (unchanged � needs warm API + auth + scan + AI provider); item 4's live check now has backend header + panel unit coverage behind it.
