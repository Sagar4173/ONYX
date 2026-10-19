# ML Model Persistence (Hydration) — Gates & Live QA

Date: 2026-10-19 — branch: master — commits: c391da9 1c83611 9857475 (Tasks 1–3)

Spec: `docs/superpowers/specs/2026-10-19-ml-model-persistence-design.md` (commit 0cbb28f). Plan: `docs/superpowers/plans/2026-10-19-ml-model-persistence.md`. Track closes the "model state is in-memory" limitation left open in the UX design §7 — models already persisted (pickle + `ml_models` row since Phase 4); this track adds the missing **load/hydration** path at engine init.

## Automated gates

| Gate | Command | Expected | Actual | Status |
|---|---|---|---|---|
| Backend unit | `backend\.venv\Scripts\python.exe -m pytest` | 729 passed (720 + 9 new) | 729 passed in 80.60s; **734 passed** after security follow-ups (+5) | ok |
| Frontend unit | `npx vitest run` | 396/396 (58 files) | 396/396 | ok |
| Frontend lint | `npm run lint` | 0 err / 10 warn | 0 err / 10 warn | ok |
| Frontend build | `npm run build` | exit 0 | exit 0 | ok |
| Prettier | `npx prettier --check` on the two touched files | clean | "All matched files use Prettier code style!" | ok |

Suite growth: backend 720 → **729** (+9: 3 hydration tests in Task 1, 6 guard tests in Task 2 — `tests/test_ml_engine.py` 8 → 17 tests), then **734** after security follow-ups (+5 edge-case tests → 22 tests in that file). Frontend count unchanged (Task 3 modified the existing lifecycle-copy assertion in `MLStatusPanel.test.jsx`; no new test).

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

Environment: `ML_ISOLATION_FOREST_ENABLED` temporarily `true` + `ML_MIN_TRAINING_SCANS` temporarily `5` (`backend/.env` lines 165–166, restored to `false` / `30` after — `.env` is untracked, no git noise). Account: `qa.admin@example.com` / `<redacted>`.

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

## Security review + follow-ups (2026-10-19)

A `security` subagent review over the track diff `3685d16..HEAD` returned **REQUEST CHANGES** — one blocker (committed plaintext QA credential) plus five lower-severity findings. All resolved in the follow-up commit (`fix(ml-persistence): security review follow-ups`) except the explicitly accepted residual risk:

1. **[Medium, blocking] Plaintext QA credentials in tracked gates docs** — the `qa.admin` / `qa.live` passwords were recorded in this doc and the Phase 5 gates doc (commits `dad4a15`, `39b2bce`; both local-only — `origin/master` is still at `bbaaba1`, nothing was pushed). Fixed: credentials redacted to `<redacted>` across all docs (including untracked phase plans). **User action: rotate both QA passwords** — the literals remain in local git history; purging history before any future push requires explicit approval (rewrite is destructive).
2. **[Medium] `pickle.load` is inherently an RCE surface; the post-load structure/schema/shape checks are data-integrity guards, not security controls** — accepted risk, now explicitly documented. Deployment precondition: `backend/ml_models/` must be writable only by the backend's own account, and the backend must not run with broader privileges than that account (no shared/multi-writer volume). Existing mitigations: gate off by default, admin-only trigger path, no user-controlled artifact path or bytes, git + Docker build-context exclusions. If the precondition cannot hold (shared volume, root container, untrusted backups), migrate to `skops` or add keyed integrity verification at train time (future work).
3. **[Low] Relative `model_file_path` re-based containment to process CWD** — fixed: training now persists `str(model_file.resolve())` (absolute); regression test `test_trained_artifact_path_is_absolute` (RED → GREEN). Legacy rows with relative paths keep CWD-relative resolution (dev DB only; fail-soft on CWD move).
4. **[Low] WARNING logs disclosed absolute filesystem paths** — fixed: containment/missing-artifact warnings now log only the artifact basename; unexpected failures still use `logger.exception`.
5. **[Low] `backend/.dockerignore` did not exclude model artifacts** — fixed: added `ml_models/` and `*.pkl` (keeps stale/poisoned pickles out of Docker images; `docker-compose.yml` builds `./backend`). Pre-existing gap noted for a future hardening pass: `.dockerignore` does not exclude `.env` (only `.env.local`), so do not publish images built from a working tree with a real `.env` until fixed.
6. **[Low] Guard edge-case test gaps** — fixed: +5 tests — sibling-prefix directory (`models_evil`), non-dict artifact structure, corrupt `feature_importance_json` fail-soft, NULL-metrics checked before any file access (spy on `pickle.load`), absolute-path persist. Junction/symlink escape was verified manually by the reviewer (Windows/Python 3.14) but is intentionally unpinned in CI (requires `mklink /J`).

Post-follow-up gates: backend **734 passed**; frontend untouched (396/396 above); lint/build unchanged (no frontend changes).
