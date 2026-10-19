# ML Model Persistence (Hydration) — Gates & Live QA

Date: 2026-10-19 — branch: master — commits: c391da9 1c83611 9857475 (Tasks 1–3)

Spec: `docs/superpowers/specs/2026-10-19-ml-model-persistence-design.md` (commit 0cbb28f). Plan: `docs/superpowers/plans/2026-10-19-ml-model-persistence.md`. Track closes the "model state is in-memory" limitation left open in the UX design §7 — models already persisted (pickle + `ml_models` row since Phase 4); this track adds the missing **load/hydration** path at engine init.

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `backend\.venv\Scripts\python.exe -m pytest` | 729 passed (720 + 9 new) | 729 passed in 80.60s | ok |
| Frontend unit | `npx vitest run` | 396/396 (58 files) | 396/396 | ok |
| Frontend lint | `npm run lint` | 0 err / 10 warn | 0 err / 10 warn | ok |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |
| Prettier | `npx prettier --check` on the two touched files | clean | "All matched files use Prettier code style!" | ok |

Suite growth: backend 720 → **729** (+9: 3 hydration tests in Task 1, 6 guard tests in Task 2 — `tests/test_ml_engine.py` 8 → 17 tests). Frontend count unchanged (Task 3 modified the existing lifecycle-copy assertion in `MLStatusPanel.test.jsx`; no new test).

### TDD evidence

- Task 1 RED: collection error `ImportError: cannot import name 'FEATURE_NAMES'` → GREEN 11/11 after implementation.
- Task 2: all 6 guard tests passed on first run (guards shipped in Task 1); containment RED **witnessed** by temporarily removing the path-containment guard → `test_refuses_artifact_outside_models_dir` failed (artifact loaded from outside `ml_models/`) → guard restored → 17/17 green.

## Implementation summary

- `FEATURE_NAMES` hoisted to a module constant (exact canonical 6-feature order); `_prepare_feature_matrix` consumes it.
- `MLAnomalyDetectionEngine.__init__` → `_hydrate_persisted_model()`: loads the latest `status='active'` row (same `ORDER BY last_trained DESC` as the dashboard), fail-soft, only when `ML_ISOLATION_FOREST_ENABLED=true`.
- Guards: path containment under `models_path` (`resolve()` + parents check), artifact existence, structure check (`{model, scaler, features}`), exact feature list match, `n_features_in_` match on model **and** scaler, skip legacy rows with NULL honest metrics. Any failure logs a warning (or exception) and starts untrained.
- No DB or file mutations during hydration; no auto-retrain; artifact path remains CWD-relative (`ml_models/`).
- `backend/.gitignore:61` now ignores `ml_models/` and `*.pkl`.
- UI: `MLStatusPanel` lifecycle note now reads "The trained model is saved and reloaded on backend restart; retrain to incorporate new scan data."

## Live QA walkthrough (2026-10-19 evening — Playwright MCP against uvicorn :8000 + Vite :5173)

Environment: `ML_ISOLATION_FOREST_ENABLED` temporarily `true` + `ML_MIN_TRAINING_SCANS` temporarily `5` (`backend/.env` lines 165–166, restored to `false` / `30` after — `.env` is untracked, no git noise). Account: `qa.admin@example.com` / `QaAdmin!2026x`.

Scan history (temp script `$TEMP\opencode\onyx-qa-scan-count.py`, mirrors the engine's exact collector query: `started_at >= now-90d`, `status=COMPLETED`, ≥1 finding): **13 completed reports total, 5 inside the 90-day window**.

Scenarios, all PASS:

- [x] **Enabled, untrained (fresh boot)** — cards "Enabled / Isolation Forest", "Available / scikit-learn", "Not trained / Model"; gate line "Minimum 13 scans within the last 90 days required to train."; new persistence note rendered; anomalies section `training_required` ("Train a model to enable anomaly alerts.")
- [x] **Real-data gate (unplanned bonus)** — first Train attempt with min=13 returned **409** live: UI `AIStateBlock` "Training unavailable" + "Training skipped: insufficient scan history or sklearn unavailable" + "Requires at least 13 scans…"; backend log `Insufficient scan history for IsolationForest: 5 < 13`. The gate works on real data.
- [x] **Restart with min=5** — gate line updates to "Minimum 5 scans…"; fresh boot log: `No persisted ML model found; engine starts untrained` (new code path live).
- [x] **Train** — status flips to "Trained"; **Model ID `anomaly_model_20261019_162849`**; Training data 5 scans; Anomaly rate 20.00%; timestamp 10/19/2026, 9:58:49 PM; anomalies section active state ("0 alerts in the last 7 days").
- [x] **Artifact + DB (pre-restart)** — `backend/ml_models/anomaly_model_20261019_162849.pkl` (62,570 bytes); DB row `('anomaly_model_20261019_162849', 5, 'active', 0.2, 0.1259, 0.1259, 'ml_models\\anomaly_model_20261019_162849.pkl')` in `backend/ml_anomaly_detection.db`.
- [x] **Backend restart → hydration (core proof)** — after a real Ctrl+C + relaunch, `/admin/ml` reload shows **Trained** with the **same Model ID** `anomaly_model_20261019_162849`, same 5 scans / 20.00% / original timestamp, anomalies section in active state. Pre-track behavior after a restart was "Not trained" (in-memory reset) — the trained card can only render post-restart because hydration populated the in-memory model.
- [x] **Gitignore proof** — `git check-ignore -v` → `backend/.gitignore:61:ml_models/`; `git status --short` contains no `ml_models/` or `*.pkl` entries.
- [x] **Env restore** — `.env` lines restored to `false` / `30`; final backend restart returns the live process to clean defaults (pending user restart, same as any restart in this session).

### QA method notes

- Training went through the real UI (**Train Model** button) against real scan data — no canned routes this time.
- The 401/WS-403 console noise before login is pre-existing dev-server behavior (stale token from a previous session), not related to this track.
- Playwright MCP wrote snapshots to `.playwright-mcp/` in the repo root (untracked tooling output, outside committed scope).

## Risks / notes

- Score metrics on the QA model are tiny (mean=std=0.1259) because the window held 5 scans — a data-shape quirk of the dev DB, not a code issue.
- Hydration silently degrades to untrained on any guard failure (by design, fail-soft); the reason is logged at WARNING and is visible in backend logs. No UI surface for hydration failure was added (spec: no new UI).
- Feature-schema drift (legacy artifacts trained on an older feature order) is intentionally treated as "retrain required" rather than mapped.
- `ML_MIN_TRAINING_SCANS` improvements only apply to *which rows train*; stale models are never auto-retrained (spec decision).

## Security checkpoint (pending)

A `security` subagent review over the track diff `3685d16..HEAD` (pickle deserialization surface, path containment, fail-soft logging) is the final closure step for this track.
