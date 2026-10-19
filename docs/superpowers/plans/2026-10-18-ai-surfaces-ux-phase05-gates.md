# UX Track Plan 5 — Gates & Live QA (ML Dashboard)

Date: 2026-10-18 — branch: master — commits: aadc183 876a27e 2b5adb1 113498e a458ffe f389c35 3829c4b (Tasks 1–7)

Plan: `docs/superpowers/plans/2026-10-18-ai-surfaces-ux-phase05.md` (approved 2026-10-18, amendments A1–A7). Phase 5 is frontend-only — the `GET /api/ml/status`, `POST /api/ml/train`, and `GET /api/ml/anomalies` endpoints, the IsolationForest engine, and the admin gate already existed and were covered by prior backend phases. One QA admin account was created directly in the dev DB for admin-path testing (temp script outside the repo, mirroring the Phase 1 pattern).

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `backend\.venv\Scripts\python.exe -m pytest` | 719 passed (no backend changes) | 719 passed in 41.12s | ok |
| Frontend unit | `npx vitest run` | 357 + new tests | 389/389 (58 files) | ok |
| Frontend lint | `npm run lint` | baseline 2907 err / 10 warn (≤ 0) | 2905 problems = 2905 err / 10 warn | ok (−2) |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |
| Storybook build | `npm run build-storybook` | exit 0 | exit 0 ("Storybook build completed successfully") | ok |

Notes:

- Final gate run at HEAD `3829c4b`: `npm test` **389/389 (58 files)**, lint **2905 err / 10 warn** — a net **improvement of 2 errors** versus the Phase 4 close (2907/10): the deleted dead config modules (`config/navigation.js`, `config/index.js`) carried 2 pre-existing lint errors. `npx eslint` on every file touched by this phase: zero findings attributable to Phase 5 code.
- Suite growth: 357 (Phase 4 close) → **389** (+32 new tests: 4 mlAPI, 5 MLStatusPanel, 8 MLTrainPanel, 5 MLAnomaliesPanel, 6 MLDashboard, 3 Sidebar, 1 CommandPalette). No pre-existing test files were modified.
- Build warnings are pre-existing (chunk-size >500 kB, Vite CJS-deprecation).
- Backend was only re-run to confirm the 719 baseline still holds; no backend changes were made.

## Tests added (Tasks 1–7, all TDD red → green)

- `mlAPI.test.js` +4 — `getStatus` GET `/ml/status`; `train` POST `/ml/train` with `null` body + `timeout: 300000`; `getAnomalies` GET `/ml/anomalies`; error propagation.
- `MLStatusPanel.test.jsx` +5 — three metric cards (flag/sklearn/trained); gate line "Minimum 30 scans within the last 90 days required to train."; active-model grid with `anomaly_rate × 100` two decimals; "No model trained yet" empty state; in-memory reset note.
- `MLTrainPanel.test.jsx` +8 — disabled + title tooltips (flag / sklearn); pending paragraph; success metrics (AnimatedCounter `anomaly_rate*100` 2dp `%`, `score_mean`/`score_std` 4dp, training scans), invalidation of `["ml-status"]` + `["ml-anomalies"]`, toast; **409 → gate panel (`AIStateBlock` + "Requires at least … days.") with no error toast**; 500 → error toast + re-enabled button.
- `MLAnomaliesPanel.test.jsx` +5 — degraded `AIStateBlock` with error text; `training_required` empty state; active alert rows (severity badge, type, timestamp, description) + statistics badges + "{total} alerts in the last 7 days"; empty-active state.
- `MLDashboard.test.jsx` +6 — internal non-admin fallback with no API calls; two cards; query config (`enabled: isAdmin`, 30 s poll, `retry: false`); per-section `ErrorState` + retry; status failure does not break the anomalies section.
- `Sidebar.test.jsx` +3 — single active item on `/admin/ml` (Admin Panel not also active); single active on `/admin`; prefix boundary (`/admin/ml` never activates `/admin*` siblings).
- `CommandPalette.test.jsx` +1 — "Go to ML Dashboard" action present and navigates.

## Live QA walkthrough (2026-10-18 late evening — Playwright MCP against uvicorn :8000 + Vite :5173)

Environment: live backend with **`ML_ISOLATION_FOREST_ENABLED=false`** (`backend/.env` lines 165–167), scikit-learn installed (status honestly reports `Available`). Accounts: `qa.live@example.com` / `QaLive!2026x` (viewer — Phase 1 seeded user) for the non-admin path, and `qa.admin@example.com` / `QaAdmin!2026x` (admin — created directly in the dev DB via a temp script beside `$TEMP\opencode\onyx-qa-admin.py`, using the app's own `init_database()`; username `qa_admin` because the model rejects dots).

12 scenarios, all PASS:

- [x] **Live default (disabled)** — cards "Disabled / Isolation Forest", "Available / scikit-learn", "Not trained / Model"; gate line; "No model trained yet" empty state; in-memory reset note; Train disabled with title "Isolation Forest is disabled on the server (ML_ISOLATION_FOREST_ENABLED=false)"; anomalies section `training_required` empty state ("Train a model to enable anomaly alerts.")
- [x] **Canned enabled+trained status** — cards flip Enabled / Available / Trained; active-model grid (Model ID `if-qa-001`, 42 scans, 4.76%, formatted timestamp); Train button enabled
- [x] **Canned train success** (1.2 s route delay) — pending paragraph "Training model… this may take a few minutes." visible while spinner replaces button label; toast "Model trained"; result metrics "Anomaly rate 2.38% / Score mean 0.5123 / Score std 0.0456 / Training scans 42"; both queries refetched — anomalies flipped to active: "2 alerts in the last 7 days", CRITICAL 1 / HIGH 2 / MEDIUM 3 badges, alert rows with timestamps + descriptions
- [x] **Canned 409** — `AIStateBlock` "Training unavailable" + backend detail, requirement line "Requires at least 30 scans within the last 90 days.", Train disabled; **no error toast**
- [x] **Canned 500** — toast with backend detail ("Simulated training failure"); button re-enabled; no lingering gate panel
- [x] **Status failure → Retry** — `ErrorState` "Failed to load ML status" + detail + "Try Again"; anomalies section unaffected (still rendering alerts — degradation isolation); after flipping the route, Retry recovers the section and the Train panel returns
- [x] **Degraded anomalies** — "Anomaly detection unavailable" + error text from payload
- [x] **Canned 403 on status** — detail ("Admin access required") inline in `ErrorState` + global interceptor toast (accepted per amendment A2)
- [x] **Non-admin (viewer `qa.live`)** — `/admin/ml` blocked by `AdminRoute` ("Access Denied", return link); sidebar shows no Administration section; no fabricated data
- [x] **Navigation** — Sidebar "ML Dashboard" under Administration; **exactly one** `aria-current="page"` at `/admin/ml` (`/admin/ml`) and at `/admin` (`/admin`); command palette (Ctrl+K / search button) filters to "Go to ML Dashboard" and navigates; page header "ML Dashboard" with breadcrumb Home / Admin / ML Dashboard
- [x] **Mobile 375×812** — 0 px horizontal overflow (scrollWidth 370); status cards stacked single-column; sidebar hidden with "Open navigation menu" toggle; drawer renders all items including ML Dashboard (active-styled)
- [x] **Console + reduced motion** — 0 application errors across the whole session (only the two pre-existing React Router v7 future-flag warnings, the expected framer-motion reduced-motion notice under emulation, and expected network/axios log lines during injected 409/500/403 responses); page renders under `prefers-reduced-motion: reduce`, and a canned train success renders counter **final values synchronously** (2.50% / 0.6100 / 0.0200) — no IntersectionObserver dependency in that path

### QA method notes

- Canned states via Playwright `page.route` fulfill with `access-control-allow-origin` (+ `OPTIONS` handling); the frontend calls `127.0.0.1:8000` directly (bearer auth), same approach as Phases 2–4.
- Two tooling quirks, not app issues: (1) Playwright aria snapshots omit names of icon+text buttons ("Sign In", "Train Model") — verified via `textContent`/DOM; (2) hidden desktop duplicates of nav links/palette items can shadow `getByText(...).first()` — scoped queries to the drawer/dialog.
- The expected console entries during injected failures are the browser's network log for non-2xx plus the `console.error` inside the `mlAPI` wrappers — same idiom as all existing API clients.

## Implementation discoveries (beyond the plan)

- **Sidebar active-state shadowing** (T6): the naive fix `location.pathname.startsWith(item.path + "/")` still double-highlights `/admin` when at `/admin/ml` (prefix match). Implemented a generalized sibling check: `NavItem` receives `paths` (all sibling nav paths) and deactivates an item when a more specific sibling path matches the current location. Additionally, React Router's `NavLink` auto-applies `aria-current="page"` via its destructured default when `aria-current` is `undefined` — passing explicit `null` for inactive items suppresses it. Both behaviors covered by the 3 new `Sidebar` tests and verified live in both directions.
- **scikit-learn availability**: the backend venv has sklearn installed, so the live status honestly shows "Available" while the flag is "Disabled" — a combination worth keeping in mind for manual checks.
- **Counter under reduced motion**: `AnimatedCounter` with a `suffix` animates via IntersectionObserver; under reduced motion it synchronously renders the final value (verified live with a canned success).

## Independent review

- The subagent review dispatch was aborted mid-run; an inline verification pass over the full phase range `fd92821..3829c4b` was performed instead (package: `.superpowers/sdd/review-package-phase05.md`): no stale imports of the deleted config modules (grep clean); Sidebar shadowing edge cases (`/admin` vs `/admin/ml`, prefix boundary, exact match, `/dashboard` special case); `mlAPI` contract + 300 s timeout; query config (`enabled: isAdmin`, 30 s poll, `retry: false`); per-section error isolation; non-admin no-call fallback; stories CSF3 consistency. No new defects found.
- Recommendation: run the independent subagent review before merge if a third-party pass is desired; the phase is otherwise ready.

## Behavioral notes (not defects)

- After a 409 the gate panel persists until a successful train or a page reload (deliberate: the button stays disabled while the gate is known-blocked; reload clears it).
- 403s surface twice by design: inline `ErrorState` plus the global axios interceptor toast (amendment A2, accepted).
- When the status query is in error, the Train panel is intentionally not rendered (training is meaningless without status); the anomalies card remains independent.
- The non-admin fallback renders inside the page component (no API calls) in addition to the `AdminRoute` guard — defense in depth for direct SPA entry during role changes.

## Deliverables beyond the web app

- Storybook: `AI/MLStatusPanel` (Disabled / Ready / Trained), `AI/MLTrainPanel` (GatedDisabled / Ready, QueryClientProvider decorator), `AI/MLAnomaliesPanel` (Active / EmptyActive / TrainingRequired / Degraded) — `npm run build-storybook` exit 0.
- Removed dead code: `frontend/src/config/navigation.js` (90 lines) and `frontend/src/config/index.js` (5 lines) — superseded by `Sidebar`'s own `getNavigation` and `UIComponents.pageConfig`; verified no remaining importers anywhere in `frontend/src`.
