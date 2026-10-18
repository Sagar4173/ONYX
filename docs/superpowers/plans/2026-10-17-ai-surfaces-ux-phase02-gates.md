# UX Track Plan 2 — Gates & Visual QA

Date: 2026-10-18 · branch: master · commits: e4cffcc c145b5d ede939c 5d3ab08 e8fbc05 cd92cd6 136c637 618223b 3aa426f 9406c09 2dbab72 1ecf3a0 (Tasks 1–11) · formatting: dcc1f42 (style: prettier pass on plan-2 files)

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `pytest tests/ -q` | 714 passed | 714 passed (33.36s) | ok |
| Backend evals | `pytest evals/ -q -m eval` | 36 passed | 36 passed (3.25s) | ok |
| Frontend unit | `npm test` | all pass | 263/263 (39 files) at Task 12; **265/265 after final-fix 382b6da** | ok |
| Frontend lint | `npm run lint` | <= 2951 err / 10 warn | 2907 err / 10 warn | ok |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |

Notes:

- Evals: the brief's `pytest tests/ -q -m eval` selects 0 tests (eval goldens live in `backend/evals/`, excluded by `testpaths = tests`); the project-standard command `pytest evals/ -q -m eval` (Plan-1 gates doc, Phases 1–4) was run and gives the expected 36.
- Lint: gate baseline **2951 errors / 10 warnings**; current **2907 errors / 10 warnings** (Δ −44 errors / 0 new warnings — the prettier pass in dcc1f42 auto-fixed ~38 of the remaining baseline errors in plan-touched files). Total warnings unchanged at 10.
- Lint spot-check: `npx eslint` on all 28 plan-touched files → 0 errors; 1 warning (`TriageDashboard.jsx:223` unused `result`) pre-dates this plan (present before e4cffcc, part of the 10-warning baseline).
- Prettier pass (Step 1) rewrote 4 tracked files (api.js, TriageDashboard.jsx, ReportDetails.jsx, MainLayout.jsx — formatting only) and was committed as dcc1f42 before this doc; all other touched files were already clean. Brief paths corrected: `useBulkLabel.js` → `useBulkLabel.jsx`, `components/triage/LabelControls.stories.jsx` → `src/stories/LabelControls.stories.jsx`; touched files omitted from the brief list (LabelControls.test.jsx, ShortcutOverlay.test.jsx, AnimatedCounter.test.jsx, labelsAPI.test.js) were included.
- Build: pre-existing chunk-size (>500 kB) + Vite CJS-deprecation warnings only; no new warnings.

## Visual QA walkthrough (2026-10-18, live — Playwright MCP against uvicorn :8000 + Vite :5173, seeded scan qa-live-check-001 / qa.live@example.com)

- [x] /report/:reportId/finding/:findingId deep link from FindingCard title renders header, sections, action rail — all 3 FindingCard titles link to their finding routes; detail page renders severity/CWE/CVSS header, Description/Code/Remediation sections, triage rail, Back to report
- [x] Unknown finding id → "Finding not found" EmptyState → Back to report — `does-not-exist` shows EmptyState; Back navigates to the report
- [x] Label from action rail: instant chip update, rollback toast on API failure — optimistic chip observed ≤250 ms with a 1.5 s-delayed route, then persisted after server 200; failure path (route abort, equivalent to API down) → toast "Couldn't save your label — change reverted" + chip reverted; "Untriage" optimistic clear observed ≤200 ms + "Label cleared (untriaged)" toast; `POST …/label` 200 confirmed. Method note: network failure simulated via Playwright `page.route` abort instead of killing uvicorn (process-kill not permitted in this environment; identical failure mode)
- [x] Triage tab: score AnimatedCounter re-ranks; reduced-motion → instant swap — context change + "Re-score" refetch; MutationObserver captured a 41-frame ramp `0.0 → 0.6 → … → 23.9` on normal motion; with `reducedMotion: reduce` emulated → single stable value, no transient frame; "Triage re-scored with updated context" toast observed
- [x] Triage rows: title deep links, expanded "Your label (human truth)" controls — 3 row titles deep-link; expanded row shows AI Triage Summary + LabelControls with pressed state; rail-set label propagates to row badge via invalidation
- [x] Keyboard: A/F/D/U label, J/K move, ? overlay, hint strip; typing does NOT trigger; guard toast when unfocused — J moved cyan cursor ring row1→row2 (scrollIntoView effect); `f` labeled row2 "False positive"; `?` opened "Triage shortcuts" dialog; guard toast "No row focused — press J first" fired with no cursor; with a select focused, J/A were suppressed (no cursor move, no guard toast) and the hook re-armed after blur; keyboard-after-checkbox regression verified separately below. Text-input suppression is covered by unit tests (no text input exists on the triage tab)
- [x] Keyboard AFTER bulk checkbox click (382b6da regression) — clicking a row checkbox focuses it; J then moved the cursor and F labeled the cursor row while the checkbox held focus; checkbox state untouched
- [x] Shortcuts PAUSED while `?` overlay open; Escape closes — with dialog open, J did not move the cursor; Escape closed it; shortcuts responded immediately after close
- [x] Bulk: checkbox + shift-range, toolbar apply, undo restores — checkbox clicks → "1 selected"; shift-click row3 → "3 selected" (all checked); toolbar "Dismissed" → Undo toast found and clicked → end state verified restored (all labels `null`, `excluded_by_label: 0`, rows back); Clear removes toolbar. Note: dismissed findings leave the ranked list mid-flow (by-design exclusion, see below). Partial-failure path "N/M restored" not exercised live (unit-covered in useBulkLabel.test.jsx)
- [x] LabelControls story renders in isolation — Storybook 6006; `full-untriaged` (3 buttons, none pressed, no Untriage), `full-accepted` (Accept pressed + Untriage + "Your label: Accepted" badge), `compact` (icon-only chips with aria-pressed)
- [x] Focus-visible rings on new interactive elements — Tab sweep: cyan 2px ring on row checkboxes, title links, and expand chevrons across all rows. Pre-existing header/menu controls lack rings (out of Plan-2 scope, noted for a future a11y pass)

## Post-QA behavioral notes (not defects)

- Triage excludes labeled findings: bulk-Dismissed emptied `ranked_findings` (`excluded_by_label: 3`) and the list showed "No findings to display". Working as designed; labels cleared afterwards and QA data left in a clean (all untriaged) state.
- Session handling: access token expires mid-session; the axios refresh interceptor silently recovered (one 401 on a triage fetch, subsequent calls 200). After a long idle window the refresh token also expired → re-login required. Expected behavior.
- No Plan-2 code changes were needed during QA; no code was modified in this pass.

## Pre-existing defects observed during QA (out of Plan-2 scope, not regressions) — FIXED 2026-10-18

- (a) "View PDF" / Export→PDF throws `ReferenceError: Cannot access 'gradeColor' before initialization` — `frontend/src/utils/pdfReportGenerator.js:211` uses `gradeColor` before its declaration in the same scope. Last touched `3b0a654` (pre-Plan-2). User-triggered during the walkthrough. **Fixed:** `securityGrade`/`gradeColor` and `riskLevel`/`riskColor` declarations moved above the `coverPage` template (a second latent TDZ on `riskColor` was exposed once the first was fixed; regression tests added in `pdfReportGenerator.test.js`).
- (b) `GET /api/reports/{id}/download?format=json|csv` → 404 for non-ObjectId report ids — `backend/routes/reports/export.py:34` requires `ObjectId.is_valid(report_id)`, so custom/seed ids (like qa-live-check-001) 404 even though the detail endpoint supports them. Last touched `02414d7` (pre-Plan-2). Only affects custom-id reports. **Fixed:** export route now falls back to `ScanReport.find_one({"scan_id": report_id})` like `detail.py`, and the access-denied 403 is no longer swallowed by the DB error handler; regression tests in `backend/tests/test_report_export_download.py`.
- Recommended follow-up task: DONE — both fixes landed with live re-verification (UI PDF export downloaded successfully with success toast; `/download` returned 200 JSON/CSV for `qa-live-check-001`).

## Final whole-branch review (2026-10-18)

- Verdict: **With fixes** → both findings landed in `382b6da` (`fix: triage shortcuts survive checkbox focus and pause behind help overlay`); re-review accepted (allow-list `NON_TEXT_INPUT_TYPES` fails safe for exotic input types; `?` still closes via Modal Escape since hooks are gated on `!helpOpen`).
- Post-fix gates re-run: frontend **265/265 (39 files)**, lint **2907 err / 10 warn** (no delta), backend unchanged **714 + 36 evals**.
- Recorded Minor debt (acceptable, from review + per-task ledgers): undo priors can clobber a single-label made during the 5s undo window; finding-detail shows "not found" copy on fetch errors (plan copy); reduced-motion helper reads per render without matchMedia listener; J/K cursor is visual-only (no SR announcement — Phase-3 note); coverage-hardening minors per task in `.superpowers/sdd/progress.md`.
- Plan-level notes: T11's draft hint-strip regex contradicted T6's actual copy (implementation chose T6 — correct); the finding route intentionally ships without A/F/D/U (Phase 3/4 action rail scope).
