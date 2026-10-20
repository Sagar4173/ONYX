# Post-QA Hardening — Design Spec

Date: 2026-10-20
Status: approved by user ("do all" of the follow-up list)
Predecessor: fix-PR re-hydration track (closed at `fcc4472`, pushed)

## Scope

Four follow-up workstreams from the fix-PR final/security reviews:

1. **Metadata redaction** — stop returning `metadata.pending_fixes` (which contains
   `patched_content`/`base_sha`) from report detail and JSON export.
2. **Atomic persistence & claim** — remove whole-document `save()` from the
   auto-fix writers; add an atomic approval claim and a DELETE conflict response.
3. **Read-side path disambiguation** — optional `file_path` on fix-state reads so
   duplicate `rule_id` entries across files hydrate the right outcome.
4. **UX polish & infra** — approve in-flight indicator, gate "Propose again"
   during approval, "View PR" copy when the PR number is unknown, and `.env`
   exclusion in `backend/.dockerignore`.

## Non-goals (remain documented follow-up debt)

- Composite finding ids / unique pending keys per (rule, path).
- "Outcome masks a newer pending after re-propose" behavior change.
- Backend cross-*process* approval locking beyond the single-writer claim
  guarantee described below (deployment is one uvicorn process).
- Redacting `pending_fixes` from the PDF path (PDF never renders `metadata`).
- Report-detail authorization model changes.

## 1. Metadata redaction

- New `backend/utils/report_metadata.py`:
  `redacted_report_metadata(metadata) -> dict` returns a shallow copy without
  the `pending_fixes` key; non-dict → `{}`; never mutates the input.
- Apply at the two serialization points only:
  - `routes/reports/detail.py` (`"metadata": redacted_report_metadata(report.metadata)`)
  - `routes/reports/export.py` (same expression in `report_data`)
- Everything else in `metadata` (e.g. `findings`, `triage`, `ai_status`) is
  preserved. The auto-fix GET endpoint keeps using its safe subset and is
  unaffected.

## 2. Atomic persistence & approval claim

### Why not dotted `$set` on `metadata.pending_fixes.<finding_id>`

`finding_id` is the raw scanner `rule_id`, and semgrep rule ids contain dots
(`python.lang.security…`). A dotted Mongo path would interpret them as nesting.
All atomic updates therefore operate on the **whole pending map** (a literal
key path `metadata.pending_fixes` is safe) or on array entries via
`arrayFilters` (ids only appear as filter values, never as field names).

### CAS helper

```python
async def _cas_pending_map(scan_report, expected: dict | None, updated: dict) -> bool
```
- `expected is None` → filter `{"_id": id, "metadata.pending_fixes": {"$exists": False}}`
- else → filter `{"_id": id, "metadata.pending_fixes": expected}` (embedded-doc equality)
- `updated` non-empty → `$set: {"metadata.pending_fixes": updated}`; empty → `$unset`
- Uses `ScanReport.get_motor_collection().update_one(...)` (precedent: `database.py:435`);
  returns `matched_count == 1`.
- Callers retry up to `_MAX_CAS_ATTEMPTS = 3` with a fresh `ScanReport.get(id)`
  (guarded by `isinstance(id, ObjectId)` so mock-based unit tests fall back to
  the in-memory object).

### Writers

- `_store_pending`: CAS expected→updated map; mirror into `scan_report.metadata`;
  no `save()`. On exhaustion raise `AutoFixError("Could not persist the proposal — try again")`.
- `discard_pending`: fresh map → CAS to map minus entry (empty → `$unset`);
  mirror; returns whether an entry was removed. Absent → `False`, no write.
- `_record_fix_outcome`: single `update_one` with
  `$set: {"metadata.findings.$[e].fix_status": …, "metadata.findings.$[e].fix_pr_url": …}`
  and `array_filters=[{"$and": [ident, path]}]` where
  - ident = `{"$or": [{"e.id": fid}, {"e.rule_id": fid}]}`
  - path (only when `finding.file_path`) =
    `{"$or": [{"e.file_path": {"$exists": False}}, {"e.file_path": None},
              {"e.file_path": {"$in": [file_path, normalized]}}]}`
  - Mirror the same entries in memory (existing `_entry_matches_finding` keeps
    suffix semantics locally; the DB filter uses exact path — a documented
    narrowing for hypothetical absolute-path entries, no such production data).
- `approve_fix` claim (before any await into clone/PR):
  1. Read pending entry; if `_approving` marker is fresh (< `APPROVAL_CLAIM_TTL_SECONDS = 900`)
     → `AutoFixError("Approval already in progress for this fix")`.
  2. CAS original map → marked map (`_approving: True`, `_approving_at: <epoch float>`).
     CAS miss → `AutoFixError("No pending fix for finding {fid} … already approved")` (race copy).
  3. On any failure after the claim, CAS marked map → original map (only if the
     marker we wrote is still present) and re-raise. Success removes the entry.
  4. Drop the final whole-document `await scan_report.save()`.
- `discard_pending` on a fresh marker → raises new `FixConflictError`;
  `routes/auto_fix.py` maps it to **409** with detail
  `"Approval already in progress for this fix — try again shortly"`.
  Stale markers (> TTL) are discarded normally.
- Frontend `classifyFixError` maps 409 / `already … in progress` to `race`.

Single-process semantics: the CAS guarantees exactly one approval claim and
one discard winner per pending map state; the marker makes DELETE report the
conflict instead of a misleading "discarded".

## 3. Read-side path disambiguation

- `get_fix_state(scan_report, finding_id, file_path=None)`:
  - Outcome entries identified by `id`/`rule_id`; when `file_path` is given,
    prefer entries whose path matches (suffix semantics via `_path_matches`,
    entries without a path remain acceptable). If no acceptable outcome entry →
    fall through to pending.
  - Pending entry with a path that does not match the requested `file_path` →
    treat as absent.
  - Without `file_path`: current behavior (first ident match) unchanged.
- Route: optional `file_path` query param on `GET …/auto-fix/{finding_id}`.
- Frontend: `autoFixGetState({scanId, findingId, filePath})` adds
  `params: {file_path}` only when provided; `useFixRun` gains `filePath`,
  includes it in the query key (`filePath ?? null`), and `FindingDetail` passes
  `finding?.file_path`.

## 4. UX polish & infra

- `FixReviewSection`: approve button shows `"Approving…"` and is disabled while
  `isApproving` (Reject already disabled).
- `FixTriggerCard`: "Propose again" disabled while `isApproving`.
- `PrCard`: `pr_number` known → `PR #{n}`; unknown → `"View PR"`.
- `backend/.dockerignore`: deny `.env` and `.env.*`, allow `!.env.example`.

## Verification

- Backend: full pytest suite; new unit tests for the redaction helper, both
  route redactions, CAS semantics (filter/update docs, retry, exhaustion),
  discard marker/409 path, claim concurrency, atomic outcome filtering, and
  path-aware state reads.
- Frontend: full vitest suite; new tests for approving label/gating, propose-again
  gating, "View PR" copy, filePath plumbing and query-key scoping.
- Lint 0 errors/10 warnings, build exit 0, prettier clean on touched files.
- Gates doc + final whole-branch review + security review; ledger updated.
