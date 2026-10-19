# ML Model Persistence (Hydration) — Design

Date: 2026-10-19 — Status: approved (brainstorming session 2026-10-19) — Track: ML persistence follow-up

This spec supersedes the parenthetical in `2026-10-16-ai-surfaces-ux-design.md` §7 ("models do not persist across restarts **until hydration follow-up lands**") — this is that follow-up.

## Context (verified 2026-10-19)

The ML anomaly detection engine already **persists** all artifacts on training, but nothing ever **loads** them back:

- `MLAnomalyDetectionEngine.train_anomaly_model()` writes `ml_models/{model_id}.pkl` (`pickle.dump({model, scaler, features})`) at `backend/services/ai/ml_anomaly_detection_engine.py:398-401` and stores metrics + file path in the `ml_models` SQLite table (`_store_model_metrics`, `:616-635`, `status='active'`).
- The anomalies dashboard already reads the latest active model **from the DB** (`:682-688`) — so after a backend restart it shows an `active_model` while `anomaly_detection_status` says `training_required` (line `:726` checks the in-memory `self.models` only).
- `GET /api/ml/status` (`backend/routes/ml.py:24-45`) reports `model_trained` from in-memory state only → `false` after restart even though the artifact exists.
- `get_ml_engine()` is a lazy singleton (`:732-740`) with a documented "no sqlite/mkdir side effects until first use" property.
- `detect_anomalies()` has **no external callers** — the engine is operator-driven (train + dashboard only), so hydration affects status/dashboard consistency, not the scan path.

## Goal

Reload the latest persisted model at engine initialization so trained state survives backend restarts, and update the UI copy that claims models reset.

## Non-goals

- Auto-retrain / cron scheduling, staleness expiry or auto-purge of old models.
- Model versioning UI, multiple simultaneous models, cleanup of superseded `.pkl` files.
- New UI elements (badge/indicator) — the "Trained" card and `last_trained` timestamp already communicate state.
- ONNX/skops migration (sklearn `pickle` remains the artifact format, matching existing write path).

## Design

### Hydration trigger

`_hydrate_persisted_model()` runs at the end of `MLAnomalyDetectionEngine.__init__()` **only when `settings.ml_isolation_forest_enabled` is true**. Because the engine is a lazy singleton, hydration happens on the first ML request after restart — no FastAPI lifespan wiring, preserving the "no side effects until first use" property.

### Load steps (all read-only, no DB writes)

1. Query the latest active row: `SELECT model_id, model_type, training_data_size, last_trained, anomaly_rate, score_mean, score_std, feature_importance_json, model_file_path FROM ml_models WHERE status='active' ORDER BY last_trained DESC LIMIT 1` (same ordering as the dashboard).
2. Skip when no row exists, `model_file_path` is empty, or any of `anomaly_rate`/`score_mean`/`score_std` is NULL (legacy pre-honest-metrics rows; logged).
3. **Path containment guard:** `Path(model_file_path).resolve()` must be inside `self.models_path.resolve()` — refuses tampered DB rows pointing elsewhere.
4. `pickle.load` the artifact; require a dict containing `model`, `scaler`, `features`.
5. **Feature-drift guard:** `features` must equal the canonical list exactly (`total_findings, critical_ratio, high_ratio, avg_cvss_score, unique_cwe_count, findings_per_hour` — hoisted from `_prepare_feature_matrix` to a module-level constant).
6. **Shape guard:** `scaler.n_features_in_ == model.n_features_in_ == len(features)`.
7. Rebuild `MLModelMetrics` from the row (`feature_importance` from JSON) and populate `self.models["anomaly_detector"] = {model, scaler, features, metrics}` — the exact post-train shape.
8. Log success at info level (`model_id`, `training_data_size`).

### Failure handling

The whole sequence is fail-soft: any exception (missing file, corrupt pickle, sklearn `ImportError`, unpickling incompatibility) is logged (warning/exception) and the engine continues **untrained** — `__init__` must never raise because of hydration. No DB or file mutations on failure.

### Effects

- `GET /api/ml/status` returns `model_trained: true` and a populated `active_model` after restart; `isolation_forest_enabled=false` still shows Disabled + untrained (no load).
- Dashboard `anomaly_detection_status` becomes `active` after restart (line `:726` reads the now-hydrated in-memory state) — resolving the current restart inconsistency with its DB-sourced `active_model`.
- No route changes required.

### UI copy change

`frontend/src/components/admin/MLStatusPanel.jsx:66-68` — replace "Model state is in-memory and resets on backend restart until retrained." with persistence wording: "The trained model is saved and reloaded on backend restart; retrain to incorporate new scan data." Update the corresponding assertion in `MLStatusPanel.test.jsx` (`:66-72`).

### Repo hygiene

`backend/ml_models/` and `*.pkl` are currently **not** ignored (checked `backend/.gitignore`) — add both. The artifact directory stays at the existing default `ml_models/` (CWD-relative to `backend/`), unchanged.

## Security

- `pickle` deserialization is code execution if an artifact is tampered; this is the existing artifact format (written by the app itself, local dir). Mitigations: fixed app-written path, no user-controlled input, path-containment guard on the DB-sourced path, `backend/.gitignore` coverage so artifacts cannot be committed.
- Residual risk equals local write access to the backend working directory (an attacker at that level already controls the process). A `security` review of the diff runs before track closure.

## Testing (TDD — extend `backend/tests/test_ml_engine.py`, tmp-path fixture pattern `:26-29`)

1. **Restart round-trip:** train on engine A (monkeypatched settings + `_collect_training_data`), construct engine B on the same tmp `db_path`/`models_path` → `models["anomaly_detector"]` populated, same `model_id`, model usable on a 1×6 sample.
2. Flag disabled → no hydration even with row + file present.
3. No row → untrained.
4. Missing artifact file → fail-soft (untrained, no raise).
5. Corrupt artifact (garbage bytes) → fail-soft.
6. Artifact path outside `models_path` → refused.
7. Feature-schema mismatch → refused.
8. Legacy row with NULL honest-metric columns → skipped.
9. Frontend: updated persistence-note assertion in `MLStatusPanel.test.jsx`.

## Acceptance criteria

- Backend suite green with the new tests (720 + new); frontend suite green (396, one assertion updated); `npm run lint` 0 err / 10 warn; `npm run build` exit 0.
- Live QA (uvicorn :8000 + Vite :5173): temporarily enable `ML_ISOLATION_FOREST_ENABLED=true` (lowering `ML_MIN_TRAINING_SCANS` if dev scan history is short), train via UI → restart backend → status shows Trained + same `model_id` without retraining; anomalies `anomaly_detection_status: active`; `backend/.gitignore` covers the new artifact directory (no untracked noise); restore `.env` afterwards.
- Gates doc records the run (existing phase-gates pattern); `security` review of the diff before closure.

## Risks / known limitations

- sklearn version upgrades can make old pickles unloadable → fail-soft to untrained (retrain fixes).
- Feature-extraction changes invalidate stored models → feature-drift guard refuses load; retrain required.
- Loaded models can be stale relative to recent scans → `last_trained` is surfaced in the UI; manual retrain is the workflow (no auto-retrain by design).
- `ml_models/` is CWD-relative (unchanged behavior): backend must run from `backend/` for artifacts to be found — matches the existing write path.
