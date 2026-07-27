# Intelligent Triage — Design Spec

## Objective

Add an Intelligent Triage system to ONYX that unifies the 3 existing independent scoring
systems (AI processor weighted-sum, compliance 4-factor model, vulnerability manager
composite risk) into a single composite priority score per finding, ranks findings by
business impact, and generates AI triage summaries for the highest-priority findings.

---

## Architecture

A lightweight service layer on top of the existing `ScanReport` document. No new database
collections. AI summaries cached in `ScanReport.metadata["triage"]`.

```
Frontend  ──GET/POST──>  triage.py route  ──>  TriageService
                                                    │
                                          ┌─────────┼──────────┐
                                          ▼         ▼          ▼
                                    ScanReport  AIProcessor  Asset DB
                                    (MongoDB)   (GPT/Gemini) (SQLite)
```

---

## Composite Priority Score Algorithm

Each finding receives a unified score (0–100) computed from these weighted factors:

| Factor           | Weight | Source                                                  |
|------------------|--------|---------------------------------------------------------|
| Severity         | 20%    | `finding.severity` → critical=100, high=75, medium=50   |
| CVSS Score       | 15%    | `finding.cvss_score.base_score` (0–10 → 0–100)          |
| Exploitability   | 15%    | `finding.exploitability_score` (0–10) or computed from threat categories |
| Business Impact  | 20%    | `finding.business_impact` CIA + `asset_criticality` from context |
| Compliance Risk  | 10%    | Finding mapped to PCI-DSS/GDPR/HIPAA gets 100, else 0   |
| EPSS             | 10%    | Exploit prediction score (0–1 → 0–100)                  |
| False Pos. Adj.  | -10%   | `finding.false_positive_score` (0–1), subtractive       |

**Formula:**

```
raw_score = (
    severity_score      * 0.20 +
    cvss_normalized     * 0.15 +
    exploitability      * 0.15 +
    business_impact     * 0.20 +
    compliance_risk     * 0.10 +
    epss_normalized     * 0.10
) * (1 - false_positive_probability * 0.10)
```

**Priority mapping:**

| Score Range | Priority        | SLA    |
|-------------|-----------------|--------|
| >= 80       | IMMEDIATE       | 24h    |
| >= 60       | HIGH            | 7d     |
| >= 40       | MEDIUM          | 30d    |
| >= 20       | LOW             | 90d    |
| < 20        | INFORMATIONAL   | —      |

---

## Components

### 1. `models/triage.py`

```python
class BusinessContext(BaseModel):
    asset_criticality: str = "medium"          # low/medium/high/critical
    data_classification: str = "internal"      # public/internal/confidential/restricted
    exposure_level: str = "internal_network"   # internet_facing/internal/isolated
    compliance_frameworks: list[str] = []

class ScoreBreakdown(BaseModel):
    total: float
    severity: float
    cvss: float
    exploitability: float
    business_impact: float
    compliance_risk: float
    epss: float
    false_positive_adjustment: float

class RankedFinding(BaseModel):
    finding_id: str
    title: str
    severity: str
    file_path: str
    composite_score: float
    priority: str
    score_breakdown: ScoreBreakdown
    ai_triage_summary: str | None = None
    sla_deadline: str | None = None

class TriageResult(BaseModel):
    scan_id: str
    project_name: str
    total_findings: int
    ranked_findings: list[RankedFinding]
    priority_counts: dict[str, int]
    executive_summary: str | None = None
    business_context: BusinessContext | None = None
    generated_at: str
```

### 2. `services/triage/triage_service.py`

`TriageService` class:

- `triage_scan(scan_id, business_context=None)` — loads ScanReport, iterates findings,
  computes composite scores, ranks by descending score, generates AI summaries for top 10,
  caches in metadata, returns `TriageResult`
- `_compute_composite_score(finding, context)` — single-finding scoring
- `_compute_business_impact_score(finding, context)` — business impact computation
- `_compute_compliance_risk_score(finding)` — framework mapping check
- `_compute_epss_score(finding)` — exploit prediction lookup
- `_generate_ai_triage_summaries(findings, report)` — batch AI call for top N findings
- `_generate_executive_summary(triage_result, report)` — overall triage summary via AI

The AI prompts are designed for structured output — they ask the model to explain WHY
this finding is urgent, what business assets are affected, and what to do first.

### 3. `routes/triage.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/triage/{scan_id}` | Return triage result (default top_n=20) |
| POST | `/api/triage/{scan_id}` | Re-score with provided `BusinessContext` in body |

Authentication: Requires authenticated user. The scan must belong to the user or user
must be an admin. Uses the same `get_current_user` dependency as other routes.

### 4. Frontend: `TriageDashboard.jsx`

New component rendered as a tab in `ReportDetails.jsx` (same pattern as Compare tab):

- **Header bar**: Project name, total findings, priority distribution bars
- **Findings table/list**: Ranked by composite score, each row shows score badge + title +
  severity + priority label + SLA deadline
- **Expansion panel**: Click a finding to see score breakdown bars + AI triage summary
- **Business context sidebar**: Toggle panel to set asset criticality, data classification,
  exposure level; triggers POST re-score
- **Executive summary section**: AI-generated overview at top

---

## Caching Strategy

AI summaries are expensive to generate. Cache in `ScanReport.metadata["triage"]`:

```json
{
  "triage": {
    "business_context": { ... },
    "summaries": {
      "finding-abc": "This SQL injection ...",
      "finding-def": "..."
    },
    "executive_summary": "...",
    "generated_at": "2026-07-27T..."
  }
}
```

On subsequent GET requests, if cached data exists for the same business context, return
it without re-generating AI summaries. The POST endpoint always re-computes.

---

## Testing

- **Unit tests** for `TriageService.compute_composite_score()`:
  - Critical vuln with critical asset → IMMEDIATE
  - Low severity with isolated exposure → LOW
  - False positive → score reduced
  - Compliance-mapped finding gets boost
  - All score factors at zero → INFORMATIONAL

- **Unit tests** for `TriageService.triage_scan()`:
  - Scan with mixed findings → correct ranking order
  - Empty scan → empty result
  - Scan not found → 404

- **Route tests**:
  - GET returns 200 with correct structure
  - POST with business context re-scores
  - Unauthenticated returns 401

- **Frontend tests**:
  - TriageDashboard renders ranked findings
  - Score breakdown expandable

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/models/triage.py` | Create — triage data models |
| `backend/services/triage/__init__.py` | Create — package init |
| `backend/services/triage/triage_service.py` | Create — triage engine |
| `backend/routes/triage.py` | Create — REST endpoints |
| `backend/app.py` | Modify — register triage router |
| `backend/tests/test_triage_service.py` | Create — service tests |
| `backend/tests/test_triage_routes.py` | Create — route tests |
| `frontend/src/services/api.js` | Modify — add triageAPI |
| `frontend/src/components/reports/TriageDashboard.jsx` | Create — triage UI |
| `frontend/src/components/reports/ReportDetails.jsx` | Modify — add Triage tab |
| Tests for TriageDashboard | Create |

---

## Edge Cases & Error Handling

- **Scan not found**: 404
- **No findings**: Return empty ranked_findings list, executive_summary = "No findings to triage"
- **AI service unavailable**: Generate triage result with scores only, mark AI summaries as null, include warning
- **Invalid business context values**: Accept with defaults, log warning
- **Finding missing scoring fields (no CVSS, no exploitability)**: Gracefully degrade — score with available factors only
- **Concurrent re-score requests**: Stateless — each request loads fresh from DB and re-computes
