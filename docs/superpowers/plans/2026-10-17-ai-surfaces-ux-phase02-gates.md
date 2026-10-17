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

## Visual QA checklist (manual, dev servers up)

- [ ] /report/:reportId/finding/:findingId deep link from FindingCard title renders header, sections, action rail
- [ ] Unknown finding id → "Finding not found" EmptyState → Back to report
- [ ] Label from action rail: instant chip update, rollback toast on API failure (kill uvicorn to test)
- [ ] Triage tab: score AnimatedCounter re-ranks with layout animation on refetch; reduced-motion media emulation → instant swap, no count-up
- [ ] Triage rows: title deep links, expanded "Your label (human truth)" controls work
- [ ] Keyboard: A/F/D/U label, J/K move + scroll, ? overlay, hint strip; typing in chat/search does NOT trigger; guard toast when unfocused
- [ ] Keyboard AFTER bulk checkbox click (regression for 382b6da): J/K/A/F/D/U still respond while a checkbox holds focus
- [ ] Shortcuts are PAUSED while the `?` overlay is open; overlay still closes via Escape
- [ ] Bulk: checkbox + shift-range select, toolbar apply, 5s undo toast restores all, partial failure shows "N/M restored"
- [ ] LabelControls story renders in isolation
- [ ] Focus-visible rings on all new interactive elements

## Final whole-branch review (2026-10-18)

- Verdict: **With fixes** → both findings landed in `382b6da` (`fix: triage shortcuts survive checkbox focus and pause behind help overlay`); re-review accepted (allow-list `NON_TEXT_INPUT_TYPES` fails safe for exotic input types; `?` still closes via Modal Escape since hooks are gated on `!helpOpen`).
- Post-fix gates re-run: frontend **265/265 (39 files)**, lint **2907 err / 10 warn** (no delta), backend unchanged **714 + 36 evals**.
- Recorded Minor debt (acceptable, from review + per-task ledgers): undo priors can clobber a single-label made during the 5s undo window; finding-detail shows "not found" copy on fetch errors (plan copy); reduced-motion helper reads per render without matchMedia listener; J/K cursor is visual-only (no SR announcement — Phase-3 note); coverage-hardening minors per task in `.superpowers/sdd/progress.md`.
- Plan-level notes: T11's draft hint-strip regex contradicted T6's actual copy (implementation chose T6 — correct); the finding route intentionally ships without A/F/D/U (Phase 3/4 action rail scope).
