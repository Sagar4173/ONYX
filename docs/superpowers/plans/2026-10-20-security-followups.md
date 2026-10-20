# Security Follow-ups — Implementation Plan

Date: 2026-10-20
Spec: `docs/superpowers/specs/2026-10-20-security-followups-design.md`
Source findings: `docs/superpowers/plans/2026-10-20-post-qa-hardening-gates.md`

## Goal

Close the auto-fix authorization gap and the SCM/URL/metadata hygiene concerns recorded at
hardening closure, with task-level reviews, security + final whole-branch review, and a gate
record.

## Approach

- Same workflow as the hardening track: fresh implementer subagent per task, independent
  reviewer per task, TDD (RED → GREEN), controller verifies gates and commits.
- Four tasks, sequential (T2 touches files T1's tests use only incidentally; T3 independent
  of T1/T2; order kept for review clarity).

## T1 — Auto-fix write authorization

Files:
- `backend/routes/reports/report_dependencies.py` — add `user_can_write_auto_fix`.
- `backend/routes/auto_fix.py` — `_write_report_or_403` guard on POST propose/approve and
  DELETE discard; GET state unchanged.
- `backend/tests/test_auto_fix_authz.py` (new) — helper + route tests.
- `frontend/src/features/scan/hooks/useFixRun.js` (or current classifier location) —
  `forbidden` kind for 403.
- `frontend/src/features/scan/components/FixReviewSection.jsx` — `forbidden` copy.
- Frontend tests for classification/copy.

Behavior:
- project `scan` permission required for all write endpoints; report owner always allowed;
  personal reports (no project) stay owner-only; missing project falls back to owner check.
- 403 detail: "Auto-fix requires scan permission on this project".
- GET state remains accessible to project viewers.

## T2 — Error and URL credential hygiene

Files:
- `backend/utils/scrub.py` (new) — `scrub_text(text, limit=300)`.
- `backend/utils/url_redaction.py` (new) — `strip_url_credentials(url)`.
- `backend/services/ai/gateway.py` — `_scrub` delegates to `scrub_text`.
- `backend/services/scm/auto_fix_service.py` — generic client-facing errors; scrubbed logs.
- `backend/utils/repo_clone.py` — reject http(s) userinfo and ssh passwords.
- `backend/routes/reports/detail.py`, `backend/routes/reports/export.py`,
  `backend/utils/pdf_generator.py` — strip URL credentials; PDF metadata redacted.
- Tests: `backend/tests/test_scrub.py` (new), extend `test_repo_clone_validation.py`,
  `test_auto_fix_service.py` (existing SCM tests), report detail/export redaction tests.

Behavior:
- no raw stderr/response bodies/repo URLs in 400 details;
- `https://user:token@host/...` and `https://token@host/...` rejected at validation;
- display paths never include userinfo; PDF no `pending_fixes`.

## T3 — Whole-metadata writers

Files:
- `backend/services/triage/triage_service.py::_cache_result` — targeted
  `$set: {"metadata.triage": cache}`.
- `backend/routes/finding_labels.py::set_finding_label` — atomic array-filter update +
  `$unset metadata.triage`; remove `report.save()`.
- Tests: `backend/tests/test_triage_service.py` (+ targeted-write test),
  `backend/tests/test_finding_labels.py` (update shape, filters, in-memory mirror).

Behavior:
- no whole-map `metadata` writes from either path; pending fixes and approval markers
  preserved; warnings unchanged.

## T4 — Defense-in-depth + closure gates

Files:
- `frontend/.dockerignore` — `.env`, `.env.*`, `!.env.example`.
- `docs/superpowers/plans/2026-10-20-security-followups-gates.md` (new).
- `.superpowers/sdd/progress.md` (UTF-16 ledger).

Verification:
- backend full pytest, frontend full vitest, lint 0/10, build exit 0, prettier clean,
  `git diff --check`.
- Reviewer per task; `security` review of branch; final whole-branch review; fix rounds;
  gate record.

## Constraints

- PowerShell 5.1; backend tests from `backend` with `.\\.venv\\Scripts\\python.exe -m pytest`;
  frontend `cmd /c "npx vitest run"` from `frontend`.
- Do not commit, push, or change unrelated files from implementer subagents.
- Never reproduce/commit secrets; scrub logs only.
- No push without explicit user approval.

## Completion Criteria

- Authorization: viewer receives 403 on all auto-fix writes and can still read state;
  owner/scanner unaffected.
- No client-visible raw SCM error text or credential URLs; credential URLs rejected.
- Triage/label writes preserve unrelated metadata keys.
- All gates pass; security + final reviews approve; ledger updated; residual risks documented.
