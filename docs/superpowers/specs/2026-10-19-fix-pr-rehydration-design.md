# Fix-PR Re-hydration — Design

Date: 2026-10-19 — Status: approved (brainstorming session 2026-10-19) — Track: fix-PR re-hydration

This spec closes the recorded follow-up from `docs/superpowers/plans/2026-10-18-ai-surfaces-ux-phase04-gates.md:73`: after a full page reload an already-opened PR (or a pending proposal) is not re-hydrated from the persisted `fix_pr_url` / `fix_status` / `pending_fixes` — the frontend never reads them because no GET endpoint exists.

## Context (verified 2026-10-19)

Fix state is already **persisted but never read back**:

- **Pending proposals** (approval required path): `propose_fix` stores `ScanReport.metadata.pending_fixes[finding_id] = {file_path, patched_content, base_sha, diff, model_used, created_at}` (`backend/services/ai/fix_runner.py:54-59`, payload `:198-205`). There is no status field — presence of the key means "awaiting approval".
- **PR outcomes**: after approve, `_record_fix_outcome` patches the raw `metadata.findings[*]` entry with `fix_pr_url` and `fix_status` ∈ `{pr_created, verified}` (`fix_runner.py:113-132`). `branch` / `pr_number` / `verification` / `gate_failures` are **response-only** — never persisted.
- **`dry_run` never persists** (`fix_runner.py:193` returns before any write).
- No GET endpoint exposes this state. `GET /api/reports/{report_id}` includes the raw `metadata` blob as an undocumented side channel (`backend/routes/reports/detail.py:101`) but the per-finding serialization (`:120-138`) omits fix fields, and the frontend never reads `report.metadata`.
- Frontend `useFixRun` is a **pure client cache**: `useQuery({enabled: false, queryFn: () => EMPTY_STATE, staleTime: Infinity, gcTime: 30 min})` (`frontend/src/hooks/useFixRun.js:40-49`); `FixReviewSection` renders `null` when idle (`FixReviewSection.jsx:90`); `reject` clears client state only, with no API call (`useFixRun.js:115-121`). After reload: `FixTriggerCard` shows "Propose fix" again.
- Endpoint conventions live in `backend/routes/auto_fix.py` (router prefix `/reports`, `get_current_user` + `get_accessible_scan_report` + `_report_or_404`, Pydantic response models, `AutoFixError → 400`, unexpected → 502).

## Goal

Persisted fix state (pending proposal or opened/verified PR) is restored into the finding detail UI after a page reload, and rejecting a pending proposal is persisted so it does not resurrect on reload.

## Non-goals

- Findings-list / report-list badges or indicators (detail page only).
- Backfilling `branch`, `pr_number`, `verification`, or `gate_failures` (they are not persisted; no schema change in this track).
- A persisted `failed` / `rejected` status enum (failures still surface as in-session errors only; reject discards rather than records).
- Changes to propose/approve flows, agent behavior, or scan-flow metadata writers.
- Redacting `patched_content` from the pre-existing `GET /reports/{id}` metadata side channel (recorded follow-up; see Security).
- Polling/live updates of fix state (fetch-once semantics).

## Design

### Backend — state read endpoint (new)

`GET /api/reports/{scan_id}/auto-fix/{finding_id}` in `backend/routes/auto_fix.py`, auth + `_report_or_404` identical to propose/approve.

Response model `FixStateResponse` (flat, optional fields — mirrors `FixRunResponse` style):

- `status`: `none | awaiting_approval | pr_created | verified`
- `finding_id`: str
- `file_path`: Optional[str]
- `diff`: str = "" (only for `awaiting_approval`)
- `pr_url`: Optional[str] (only for PR states)
- `model_used`: str = "" (only for `awaiting_approval`)
- `created_at`: Optional[str] (only for `awaiting_approval`)

Resolution priority (single source: `ScanReport.metadata`):

1. **Outcome** — `metadata.findings[*]` entry with `id == finding_id` and `fix_status ∈ {pr_created, verified}` → return that status + `fix_pr_url` (file_path from the entry when present).
2. **Pending** — `metadata.pending_fixes[finding_id]` exists → `awaiting_approval` + `{file_path, diff, model_used, created_at}` from the stored payload.
3. Otherwise → `none`.

**Never returns `patched_content` or `base_sha`.**

Service helper `get_fix_state(scan_report, finding_id) -> Dict[str, Any]` in `fix_runner.py` (pure read, no I/O beyond the in-memory report document — testable without git/scanner fakes). The route wraps it in `FixStateResponse`.

Absent/unknown finding → `none` (idempotent read; the finding's existence is already governed by the report query on the page — no second 404 contract).

### Backend — discard endpoint (new, Reject persistence)

`DELETE /api/reports/{scan_id}/auto-fix/{finding_id}` → `{"status": "discarded"}`, idempotent (no pending entry → still 200). Same auth + access check.

Service helper `discard_pending(scan_report, finding_id) -> bool`:

- Pops `metadata.pending_fixes[finding_id]`; removes the `PENDING_FIXES` key entirely when the map becomes empty; saves **only if something changed**; returns whether an entry existed.

**Why server-side reject** (decision made in brainstorming): the UI semantics of Reject are "discard this proposal" (client returns to idle). With hydration, a client-only dismiss would visibly resurrect the patch after reload — contradicting the user's action. A tiny idempotent DELETE keeps visible state and stored state honest, and reuses the exact authz pattern of propose/approve. No `rejected` status is recorded (YAGNI — nothing displays it).

### Frontend — hydration via the existing hook

`frontend/src/services/aiClient.js` — add:

- `autoFixGetState({scanId, findingId})` → `GET /reports/{scanId}/auto-fix/{findingId}` (default timeout).
- `autoFixDiscard({scanId, findingId})` → `DELETE ...` (default timeout).

`frontend/src/hooks/useFixRun.js` — the react-query entry becomes live but fetch-once:

- `queryFn`: call `autoFixGetState`; map server state into the existing `run` shape, or `EMPTY_STATE` for `none`:
  - `awaiting_approval` → `run = {status, finding_id, file_path, diff, model_used, created_at}`
  - `pr_created` / `verified` → `run = {status, finding_id, pr_url, file_path?}`
- `enabled: !!scanId && !!findingId` (report query supplies `scan_id`; stays disabled until loaded).
- `staleTime: Infinity` + existing `gcTime`, `retry: false`, `refetchInterval: false`, `refetchOnReconnect: false` retained → in-session mutations still win; no refetch on remount or window focus; **no polling**.
- **Fail-soft:** a failed state GET resolves to `EMPTY_STATE` — it must NOT be mapped into the `error` state (`error` means "a fix attempt failed"; `FixTriggerCard` renders "Last attempt failed" for it).
- Mutations (`propose`/`approve`) unchanged: they keep writing through `setQueryData`.
- `reject` becomes a discard mutation: success → clear `run`/`error` + history entry ("reject", "dismissed") + existing toast; failure → **keep the run visible** + error toast ("Could not discard the proposal") so the UI never lies about server state.

Components (`FixReviewSection`, `FixTriggerCard`, `FixStatusRail`, `PrCard`, `VerifiedBadge`, `VerificationNotice`) need no structural changes — verified null-safe for absent `verification` (`VerificationNotice.jsx:64` returns null; `VerifiedBadge.jsx:6` uses `verification?.total_findings`) and `PrCard` falls back to "PR #open" without `pr_number`. Hydrated PR state renders: status rail + PR link (+ generic verified badge when `verified`); no verification notice, no gate-failure alerts, no branch chip.

Known edge (documented, no extra UI): hydrated `awaiting_approval` while `AUTO_FIX_REQUIRES_APPROVAL=false` renders the diff with no action buttons (the pending key should not exist in that mode; only stale state can produce it).

## Security

- The new GET returns a **safe subset only** (`status`, `diff`, `file_path`, `pr_url`, `model_used`, `created_at`) — `patched_content`/`base_sha` remain server-side.
- Both endpoints enforce ownership via `get_accessible_scan_report` (same IDOR posture as propose/approve; existing route tests pin 404-for-foreign-scan).
- DELETE is idempotent and non-destructive to anything but the pending map.
- **Pre-existing issue recorded, out of scope:** `GET /reports/{id}` still exposes `metadata.pending_fixes[*].patched_content` to authorized users via the raw metadata blob (`routes/reports/detail.py:101`). Follow-up candidate; not addressed here to keep the report contract stable.
- `security` subagent review of the diff runs before track closure (repo convention).

## Testing (TDD)

Backend — extend `backend/tests/test_fix_runner.py` (17 tests; fix_runner fakes: git fixture + monkeypatched agent/PR/storage) and `backend/tests/test_auto_fix_routes.py` (7 tests; `TestClient` + dependency overrides + patched `ScanReport.find_one`):

1. `get_fix_state`: no state → `none`; pending present → `awaiting_approval` with exactly `{file_path, diff, model_used, created_at}` (no `patched_content`/`base_sha` in the dict); outcome present → `pr_created`/`verified` with `pr_url`; outcome takes priority when both exist.
2. `discard_pending`: pops + saves + returns True; absent → returns False and does **not** save; last pending removed → `PENDING_FIXES` key dropped.
3. Route GET: 200 `none`; 200 `awaiting_approval` shape; 200 pr states; 404 foreign/unknown scan; 401 unauthenticated.
4. Route DELETE: 200 `discarded`; idempotent second call 200; 404/401 as above.

Frontend — extend `useFixRun.test.jsx` (12 tests), `FixReviewSection.test.jsx` (11), `FindingDetail.test.jsx` (8), `aiClient.test.js`:

5. `aiClient`: GET + DELETE request shapes (path/params/method).
6. `useFixRun`: empty cache → GET called once, `run` hydrated (awaiting + pr shapes); populated cache (post-propose) + remount → no GET refetch (cache-first); GET failure → `run: null, error: null`; reject success → DELETE called, run cleared, toast; reject failure → run kept + error toast.
7. `FixReviewSection`: hydrated `awaiting_approval` renders diff + Approve/Reject; hydrated `verified` without `verification` renders badge + PrCard and no verification notice.
8. `FixTriggerCard`: hydrated status badge ("Awaiting approval" / "Verified").
9. `FindingDetail` integration: report + seeded GET state → reload-style render shows the review section (regression for the actual follow-up).

## Acceptance criteria

- Backend suite green with new tests (734 → ~744); frontend suite green (396 → ~+12); `npm run lint` 0 err / 10 warn; `npm run build` exit 0; prettier clean on touched files.
- Live QA (uvicorn :8000 + Vite :5173): propose a fix with approval enabled → reload → review section + diff restored with Approve/Reject → approve → reload → PR state restored; propose → reload → reject → reload → gone; `none` state still renders idle ("Propose fix"); dry-run unchanged.
- Gates doc records the run; `security` review of the diff before closure.

## Risks / known limitations

- Hydrated PR state lacks `branch`/`pr_number`/`verification` → PrCard shows the "PR #open" fallback and the generic verified copy (no backfill by design).
- Brief idle flicker possible while the state GET resolves (no loading UI added — YAGNI).
- Multi-tab races (two tabs approving/rejecting) keep the existing server-side claim semantics; hydration simply reflects the latest persisted truth on next mount.
- If metadata is absent/corrupt, `get_fix_state` returns `none` (fail-soft read; no exceptions from shape issues).
