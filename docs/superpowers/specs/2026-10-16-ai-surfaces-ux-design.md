# AI Surfaces UX — Design Spec

**Date:** 2026-10-16 · **Status:** Approved (design) · **Deliverable of:** UX Track, parent spec §5.1 (`2026-10-06-onyx-ai-native-redesign-design.md`)
**Scope:** Frontend UI for every AI capability shipped in backend Phases 1-4 (gateway/RAG/agentic/ML), plus the shared foundations they need.

---

## 1. Context & Ground Rules

Backend Phases 1-4 (commits `851cf27`…`bbaaba1`, pushed) shipped: SSE chat streaming + citations, triage labels (`accepted|false_positive|dismissed`), investigate agent, auto-fix PR lifecycle with verification re-scan, `/api/ml` IsolationForest dashboard, kill switches, rate limits. The frontend (`frontend/`, Vite 5 + React 18 SPA, JS only, react-query v5 + axios, Tailwind 3, framer-motion, heroicons) was untouched — zero consumers exist for labels, investigate, auto-fix, `/api/ml`, SSE, and citations; chat is JSON-buffered plain text.

**Foundations (not a rewrite):** the July specs (`2026-07-24-ui-ux-consistency`, `2026-07-25-navigation-redesign`, `2026-07-25-ui-excellence`, `2026-07-26-brand-identity-redesign`) + the design system in `frontend/src/components/ui/StyleComponents.jsx`, `frontend/src/styles/` (theme.js, classNames.js), `frontend/src/layouts/UIComponents.jsx`, `constants/brand.js`. Glass/gradient identity, dark-first, heroicons-only, global `prefers-reduced-motion` kill-switch: all carry over.

**Quality bar (from parent §5.1, non-negotiable):** signature animated moments; motion language with reduced-motion respect; interactive (keyboard-fast triage, inline citation navigation, one-click fix approval); state completeness (loading/empty/error/quota/degraded — designed, not defaulted); judged against Linear/Vercel/Cursor; Storybook stories for new components.

### Locked decisions (design-phase Q&A)

| Decision | Choice |
|---|---|
| Spec structure | **One spec, phased delivery** (parent mandate); implementation planned per phase |
| Phase order | **Dependency order, chat first** (foundations → chat → triage/finding → investigate → fix-PR → ML) |
| Diff viewer | **New runtime dep** (`react-diff-viewer-continued` or equivalent MIT lib), restyled to identity |
| Verification | **Storybook story + vitest interaction test per new primitive**, manual visual-QA checklist per phase; no new Playwright e2e |
| Finding host | **Dedicated route** `/report/:reportId/finding/:findingId` |
| Shared wiring | **`aiClient` module + hooks + one new `GET /api/ai/features` backend endpoint** (spec's only backend touch) |

### Non-goals

- No changes to July specs or `styles/` tokens; no general dashboard/page overhaul (only AI surfaces + components each phase touches).
- Backend changes limited to `GET /api/ai/features` (plus its tests) **and one additive field — `text` (chunk body, whitespace-normalized, capped 1500 chars) on chat citation payloads in `services/ai/chat_grounding.py` (plan-time amendment, user-approved 2026-10-16: no endpoint serves knowledge-chunk text, and the CWE side-panel needs content)**. No chat-history persistence endpoint — conversation state is session-scoped (module-level store, clears on reload).
- No global AI context provider; no Redux/Zustand; no TypeScript migration; no icon-library changes.

---

## 2. Phase 0 — Shared Foundations

| Piece | Design |
|---|---|
| `src/services/aiClient.js` | Wraps all five domains: `streamChat()` (fetch + `ReadableStream`, manual `Authorization` header — `EventSource` cannot set headers; follows `components/reports/ReportExport.jsx:17-26` precedent), `setFindingLabel()`, `runInvestigate()`, `mlStatus()/mlTrain()/mlAnomalies()`, `autoFixPropose()/autoFixApprove()`. All non-stream calls go through the existing axios instance (JWT refresh, error mapping). 429s parse `Retry-After` and surface a typed rate-limit error (not the generic toast). |
| `GET /api/ai/features` (backend) | New route file `backend/routes/ai_features.py` (mounted `/api`): returns kill-switch/config booleans — `investigate_agent_enabled`, `ml_isolation_forest_enabled`, `ml_min_training_scans`, `ml_training_window_days`, `auto_fix_requires_approval`, and limiter hints. Authed (same `get_current_user` dependency); no admin requirement. Small backend test alongside. |
| `useAIFeatureFlags()` | react-query hook, `["ai-features"]`, staleTime 5 min, refetch on window focus (default react-query). Surfaces gate UI declaratively; toggles picked up without reload. |
| `useSSEStream()` | Single streaming hook: `fetch` → parse SSE frames → typed event callbacks; returns `{status: 'idle'\|'connecting'\|'streaming'\|'done'\|'error'\|'rate_limited', error, send(), abort()}` — no `data` key: delta text is caller-accumulated via the per-call `onEvent` (amended 2026-10-16, reconciled with the plan's Task 4/7 briefs after review flagged the mismatch). Handles mid-stream disconnect (keeps partial), abort (stop button), 429-with-Retry-After, malformed-frame tolerance (log + surface schema-retry notice). |
| `AIStateBlock` | One component over existing primitives (`Card`, `Alert`, `EmptyState`, `Skeleton`) with variants: `loading` (long-analysis skeleton w/ shimmer), `empty`, `error` (+retry), `degraded` (provider fallback / degraded dashboard), `rate_limited` (delegates to QuotaNotice), `disabled` (feature off — explains the flag). Storybook story required. |
| `QuotaNotice` | 429 state: countdown from `Retry-After`, quota-window context copy, disabled-until-expiry action. Storybook story required. |
| Design-system policy | Every **new** component uses canonical primitives (`Button`, `Card`, `Badge`, `Modal`, `Alert`, `EmptyState`, `Skeleton`, `ConfirmDialog`, `StatCard`, …). Legacy AI components (**`AIChatPanel`, `TriageDashboard`, `FindingCard`**) are migrated to primitives only as their phases modify them — no opportunistic rewrites of untouched pages. |
| Nav maintenance | New nav entries (Phase 5) update `layouts/Sidebar.jsx` (authoritative), `CommandPalette.jsx:14-23` default actions, `layouts/UIComponents.jsx` `pageConfig`; stale `config/navigation.js` is deleted (dead code, July-spec-sanctioned). |

**Infra note:** nginx `proxy_read_timeout 120s` — safe for SSE only if frames arrive <120s apart (backend heartbeats); the chat client's 300s axios timeout becomes moot once streaming.

---

## 3. Phase 1 — Chat: Streaming + Citations

Extends `components/reports/AIChatPanel.jsx` (mounted as the AI Chat tab of `ReportDetails`); migrates it to primitives while touched.

- **Transport:** `POST /api/ai/chat/stream` via `useSSEStream()` replaces buffered `POST /api/ai/chat` (`services/api.js:365-372`). Message store: `useConversation(scanId)` — module-level `Map` keyed by scanId (survives in-app navigation, clears on reload); sends last 20 messages as `conversation_history` (backend contract unchanged).
- **Signature moment — live citation chips:** assistant bubble renders with a shimmer caret during streaming; citation markers (backend cite-by-index) turn into `Badge` chips the moment they appear, in DOM order of arrival. Chip click opens the **CWE side-panel**: existing `Modal` at `xl`/`max-w-4xl` (focus trap), content = the citation's `text` field (knowledge chunk body ≤1500 chars, from the plan-time-approved citation amendment) plus header/source/`source_id`/`cwe_id` metadata — page never left. Chips keyboard-reachable; panel restores focus to the invoking chip on close.
- **States:** `AIStateBlock` loading/error; mid-stream disconnect keeps the partial answer + reconnect affordance; **Stop** button aborts fetch (idempotent); `QuotaNotice` on 429; backend SSE event types for provider-fallback and schema-retry map to notice events (never silent failures). `model_used` footer and suggested-question chips retained.

---

## 4. Phase 2 — Triage Labels + Finding Route

Largest phase. Hosts Phase 3 and 4.

### Finding route

- `/report/:reportId/finding/:findingId`, lazy route in `layouts/MainLayout.jsx` inside existing `ErrorBoundary`.
- Layout: severity/header block (scanner, CVE/CWE, CVSS vector, file:line, secret-heuristics chips when applicable) · body sections (description, code context, remediation — content of migrated `FindingCard`) · **right action rail**: label controls now; investigate (Phase 3) and fix (Phase 4) slot in later.
- 404-safe: finding absent from report → `EmptyState` + back-link. Triage rows and `FindingCard` titles deep-link here.

### Label workflow

- Three controls + **Untriage** when labeled: **Accept · False positive · Dismissed** (`POST /api/reports/{scan_id}/findings/{finding_id}/label`).
- Optimistic react-query mutation with rollback toast on failure; on success `invalidateQueries(["report", id])` + `invalidateQueries(["triage", scanId])`.
- **Signature moment — visible risk recompute:** triage rows animate score/rank changes (`AnimatedCounter` + framer-motion layout shift); all motion behind the global `prefers-reduced-motion` switch (instant swap when reduced).
- Placement: compact icon-row on `FindingCard` (Findings tab), full controls in the action rail and expanded triage rows.
- **Copy:** existing Triage tab = AI scoring (unchanged); labels = human truth feeding ML. UI distinguishes "AI rank" from "Your label" everywhere they co-appear.

### Keyboard-fast triage (parent non-negotiable)

- Focused triage/finding surface: `A`/`F`/`D`/`U` apply labels, `J`/`K` move selection, `?` opens shortcut overlay; keys suppressed while typing in inputs.
- **Bulk:** multi-select rows (checkbox/shift-click) → apply label to N → **undo toast** (5 s) restores prior labels sequentially; partial failure reports "N/M restored" (no false success).
- Discoverable footer hint strip.

---

## 5. Phase 3 — Investigate Agent

On the finding route (action rail → inline section).

- **Trigger:** "Investigate" button (disabled + `AIStateBlock disabled` when `investigate_agent_enabled` is false via `useAIFeatureFlags()`). Optional question field (≤2000 chars, live counter) → `runInvestigate()`.
- **Report rendering** (`InvestigateReport`) as stacked `Card`s: **Blast radius** (prose) · **Evidence** (≤8 items: paths as `Code` chips, findings as deep-links) · **FP reasons** (≤5 — each with an "agree" one-click label action reusing Phase 2 controls) · **Recommended actions**. Model/usage footer consistent with `AISection`.
- **States:** inline skeleton cards while running · 400 injection-block → inline `role="alert"` warning (never toast-only) · 503 → retry · 502 → `AIStateBlock error` · kill-switch off → disabled with explanation. Result cached in react-query keyed by `(findingId, question)`.

---

## 6. Phase 4 — Fix-PR Review Flow

Finding route action rail → full-width review view (route stays the host; review section expands).

- **Lifecycle rail** driven by `FixRunResponse.status` (`backend/routes/auto_fix.py:18`):
  1. `dry_run` → diff + "Apply fix" (re-propose path preserved).
  2. `awaiting_approval` → diff + **Approve & open PR** / **Reject** — `ConfirmDialog` with type-to-confirm (July destructive-action rule).
  3. `pr_created` → PR link card + "Run verification re-scan".
  4. `verified` → **signature badge**: gradient check that *animates the re-scan result in* (sweep across previously-failing checks now passing — static checkmark forbidden by parent).
- Run history kept in react-query cache; every transition toasts.
- **Diff viewer:** `react-diff-viewer-continued` (approved dep), themed via its props to dark/glass tokens — cyan additions, violet context, red removals aligned with severity palette; split↔unified toggle; split default desktop / unified mobile; render cap on very long files with progressive expand.
- **States:** `auto_fix_requires_approval` off → explain-mode (disabled + config tooltip) · 409 → "already approved elsewhere" race notice · gate failures (secrets/cap/diff-size from Phase 3 backend gates) → `Alert` blocks above the diff · fix-agent disabled → disabled state.

---

## 7. Phase 5 — ML Dashboard

ADMIN-gated page: `AdminRoute` + Sidebar "Administration" section (`Sidebar.jsx` authoritative; update `CommandPalette` actions + `pageConfig`; delete stale `config/navigation.js`).

- **Status panel:** gate flags, `sklearn_available`, `model_trained`, active-model summary — `StatCard`/`MetricCard`. Note: `model_trained` reflects the in-memory engine (backend restart resets until retrain) — copy must say so ("models do not persist across restarts" until hydration follow-up lands).
- **Train panel:** `POST /api/ml/train` button; gate unmet → disabled with tooltip showing `ml_min_training_scans` + window; success → honest metrics appear in place (`AnimatedCounter` on `anomaly_rate`/`score_mean`/`score_std`).
- **Anomalies panel:** recent alerts list + dashboard dict; `anomaly_detection_status === "degraded"` → `AIStateBlock degraded` variant with the response's `error` surfaced.
- **States:** `ErrorState` retry when endpoint down; 403 (defense-in-depth) → `ErrorState`; 409 → explanatory disabled panel (not an error).

---

## 8. Cross-Cutting

### Accessibility

Streaming region `aria-live="polite"` (finished answers announced, not per-token) · citation chips in arrival DOM order, keyboard-reachable · shortcut guard while typing · `focus-visible:ring-cyan-500` + `ring-offset-gray-900` on all new focusables · diff viewer keyboard navigation verified · global `prefers-reduced-motion` respected by all new motion · toasts `role="status"`, injection-block `role="alert"`.

### Testing & verification (per approved bar)

- **Storybook story** for each new primitive: `AIStateBlock`, `QuotaNotice`, citation chip, label controls, fix status rail, feature-flag badge (existing pattern: `src/stories/`, 6 today).
- **vitest + Testing Library** interaction tests per new component (`ScanComparison.test.jsx` pattern): label optimistic-update + rollback; `useSSEStream` state machine fed a mock `ReadableStream`; keyboard triage `A/F/D/U` + bulk undo; fix lifecycle transitions; feature-flag gating.
- Per phase gate: `npm run lint` (delta ≤ 0 vs the 2026-10-16 recorded baseline of 2955 pre-existing prettier errors + 10 warnings — amended 2026-10-16 after discovering the drift predates this track; touched files must lint clean), `npm test`, `npm run build` all green; backend suite untouched except Phase 0's features-endpoint test.
- **Manual visual-QA checklist per phase** vs the Linear/Vercel/Cursor bar, recorded in the phase plan. No Playwright additions.

### Edge cases (routed to their phase)

SSE disconnect keeps partial + reconnect · 429 `Retry-After` countdown on chat + investigate · label-write vs triage-cache race tolerates stale-by-one recompute (backend follow-up recorded) · finding deleted mid-session → 404 path · kill-switch toggled mid-session picked up on focus refetch · over-cap diffs render-capped · bulk undo partial failure reports exact N/M.

### Risks & assumptions

- `react-diff-viewer-continued` maintenance unknown (MIT, widely used) — fallback: custom minimal renderer (pre-scoped alternative).
- SSE event vocabulary must be enumerated from `routes/ai_chat.py` + `services/ai/investigate_agent.py` at Phase 1 plan time (assumption: existing `StreamEvent`/chat-stream types are the contract).
- `GET /api/ai/features` is the track's only backend touch — keep to one route file + test.
- New Storybook stories must not break `npm test` collection (vitest add-on wiring exists).

## Success criteria

1. Every AI surface ships designed loading / empty / error / quota / degraded states.
2. Three signature moments present and reduced-motion-safe: live citation chips, visible risk recompute on label, animated verified-by-rescan badge.
3. Zero raw structural Tailwind in new components; touched legacy AI components migrated to canonical primitives.
4. Keyboard triage (labels, bulk, undo) matches the parent bar.
5. Per-phase gates green: lint, test, build; stories + vitest coverage for every new primitive.
6. Manual visual-QA checklist passed per phase.
