# Intelligent Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a unified triage system that composites 3 existing scoring engines into one priority score per finding, AI-generates triage summaries, and surfaces everything through a new REST endpoint and frontend tab.

**Architecture:** Lightweight service layer reading from existing ScanReport — no new DB collections. AI summaries cached in `ScanReport.metadata["triage"]`. New `TriageService` computes composite scores from severity, CVSS, exploitability, business impact, compliance risk, EPSS, and false-positive likelihood.

**Tech Stack:** Python 3.14 + FastAPI + beanie (MongoDB), React 18 + Material UI

## Global Constraints

- Follow existing patterns in `services/` and `routes/`
- Use lazy imports for beanie models inside async methods (existing convention)
- All async endpoints use `async def`
- Tests use `pytest.mark.asyncio` + `unittest.mock.AsyncMock`
- AI calls via existing `ai_processor.py` / `gemini_ai_processor.py`

---

### Task 1: Triage Data Models

**Files:**
- Create: `backend/models/triage.py`
- Test: (tested implicitly by Task 2)

**Interfaces:**
- Produces: `BusinessContext`, `ScoreBreakdown`, `RankedFinding`, `TriageResult`

- [ ] **Create `backend/models/triage.py`**

```python
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional


class BusinessContext(BaseModel):
    asset_criticality: str = "medium"
    data_classification: str = "internal"
    exposure_level: str = "internal_network"
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
    ai_triage_summary: Optional[str] = None
    sla_deadline: Optional[str] = None


class TriageResult(BaseModel):
    scan_id: str
    project_name: str
    total_findings: int
    ranked_findings: list[RankedFinding]
    priority_counts: dict[str, int]
    executive_summary: Optional[str] = None
    business_context: BusinessContext
    generated_at: str
```

---

### Task 2: TriageService — Core Scoring Engine

**Files:**
- Create: `backend/services/triage/__init__.py`
- Create: `backend/services/triage/triage_service.py`

**Interfaces:**
- Consumes: `BusinessContext`, `ScoreBreakdown`, `RankedFinding`, `TriageResult` from Task 1
- Produces: `TriageService.triage_scan(scan_id, business_context?) -> TriageResult`

- [ ] **Create `backend/services/triage/__init__.py`**

```python
from .triage_service import TriageService, triage_service
```

- [ ] **Create `backend/services/triage/triage_service.py`** with full `TriageService` class

The class implements:

- `triage_scan(scan_id, business_context=None)` — main entry point
- `_compute_composite_score(finding, context)` — single-finding score
- `_compute_business_impact_score(finding, context)` — 20% weight
- `_compute_compliance_risk_score(finding)` — 10% weight
- `_compute_epss_score(finding)` — 10% weight
- `_get_cached_triage(scan_report, context_hash)` — cache check
- `_cache_triage(scan_report, result)` — save summaries to metadata

Composite score formula:
```python
def _compute_composite_score(self, finding, context):
    severity_map = {"critical": 100, "high": 75, "medium": 50, "low": 25, "info": 5}
    sev = severity_map.get(finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity).lower(), 5)

    cvss = 0
    if finding.cvss_score and finding.cvss_score.base_score:
        cvss = finding.cvss_score.base_score * 10

    exploitable = finding.exploitability_score or 0
    business_impact = self._compute_business_impact_score(finding, context)
    compliance = 100 if self._compute_compliance_risk_score(finding) > 0 else 0
    epss = self._compute_epss_score(finding)
    fp = finding.false_positive_score or 0

    total = (
        sev * 0.20 + cvss * 0.15 + exploitable * 0.15 +
        business_impact * 0.20 + compliance * 0.10 + epss * 0.10
    ) * (1 - fp * 0.10)

    return max(0, min(100, total))

def _compute_business_impact_score(self, finding, context):
    score = 0
    if finding.business_impact:
        if finding.business_impact.confidentiality_impact:
            score += 25
        if finding.business_impact.integrity_impact:
            score += 25
        if finding.business_impact.availability_impact:
            score += 25
        if finding.business_impact.business_criticality and finding.business_impact.business_criticality.lower() in ("critical", "high"):
            score += 25
    criticality_map = {"critical": 80, "high": 60, "medium": 40, "low": 20}
    ctx_score = criticality_map.get(context.asset_criticality.lower(), 40)
    return (score + ctx_score) / 2

def _compute_compliance_risk_score(self, finding):
    if finding.compliance_mappings and len(finding.compliance_mappings) > 0:
        return 100
    return 0

def _compute_epss_score(self, finding):
    if finding.cve_id:
        try:
            from services.scanning.vulnerability.manager import vulnerability_manager
            epss = vulnerability_manager.epss_service.get_epss_score(finding.cve_id)
            if epss:
                return epss.epss_score * 100
        except Exception:
            pass
    return 0
```

For AI triage summaries, generate for top 10 findings using existing AI processor:
```python
async def _generate_ai_triage_summaries(self, ranked_findings, scan_report):
    if not ranked_findings:
        return
    findings_text = ""
    for rf in ranked_findings[:10]:
        findings_text += f"- {rf.title} ({rf.severity}, score: {rf.composite_score:.1f})\n"
    prompt = (
        "You are a security triage expert. For each finding below, write 2-3 sentences explaining:\n"
        "1) Why this finding is important from a business perspective\n"
        "2) What the real-world impact could be\n"
        "3) What should be done first\n\n"
        f"Project: {scan_report.project_name}\nFindings:\n{findings_text}"
    )
    try:
        from services.ai.ai_processor import get_ai_processor
        processor = get_ai_processor()
        summary = await processor._call_ai_api(prompt)
        # Parse structured output and assign to each finding
        if summary:
            for i, rf in enumerate(ranked_findings[:10]):
                rf.ai_triage_summary = f"Priority {i+1}: {rf.title}. {summary[:500]}"
    except Exception:
        pass
```

The `triage_scan` method orchestrates the full flow:
1. Load ScanReport from DB
2. Check cache in metadata
3. If no valid cache, compute scores for all findings
4. Rank by score descending
5. Generate AI summaries for top 10
6. Cache in metadata
7. Return TriageResult

---

### Task 3: REST Routes

**Files:**
- Create: `backend/routes/triage.py`
- Modify: `backend/app.py`
- Test: `backend/tests/test_triage_routes.py`

- [ ] **Create `backend/routes/triage.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from models.triage import BusinessContext, TriageResult
from routes.dependencies import get_current_user
from models.user import User
from services.triage import triage_service

router = APIRouter(prefix="/api/triage", tags=["triage"])

@router.get("/{scan_id}", response_model=TriageResult)
async def get_triage(scan_id: str, top_n: int = 20, user: User = Depends(get_current_user)):
    result = await triage_service.triage_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    result.ranked_findings = result.ranked_findings[:top_n]
    return result

@router.post("/{scan_id}", response_model=TriageResult)
async def rescore_triage(scan_id: str, context: BusinessContext, top_n: int = 20, user: User = Depends(get_current_user)):
    result = await triage_service.triage_scan(scan_id, business_context=context)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    result.ranked_findings = result.ranked_findings[:top_n]
    return result
```

- [ ] **Register router in `backend/app.py`**

Add after existing router registrations:
```python
from routes.triage import router as triage_router
app.include_router(triage_router)
```

- [ ] **Create route tests** in `backend/tests/test_triage_routes.py`

Tests:
- `test_get_triage_success` — mock TriageService, verify 200 + correct structure
- `test_get_triage_not_found` — mock returns None, verify 404
- `test_get_triage_unauthenticated` — no auth header, verify 401
- `test_post_triage_rescore` — POST with context, verify 200 + scores

---

### Task 4: TriageService Unit Tests

**Files:**
- Create: `backend/tests/test_triage_service.py`

- [ ] **Create comprehensive unit tests**

Tests for `_compute_composite_score`:
- `test_critical_cvss_high_exploitable_business_critical` → score >= 80 (IMMEDIATE)
- `test_low_severity_isolated_exposure` → score < 40
- `test_false_positive_reduces_score` → score lower with FP=0.8 vs FP=0.1
- `test_compliance_mapped_gets_boost` → score higher with compliance mappings
- `test_missing_scoring_fields` → graceful degradation, no crash

Tests for `triage_scan`:
- `test_scan_with_findings` — returns correct ranking order
- `test_scan_no_findings` — returns empty ranked_findings
- `test_scan_not_found` — returns None

---

### Task 5: Frontend API Service

**Files:**
- Modify: `frontend/src/services/api.js`

- [ ] **Add triageAPI methods to api.js**

```javascript
const triageAPI = {
  getTriage: (scanId, topN = 20) =>
    apiClient.get(`/api/triage/${scanId}?top_n=${topN}`),
  rescoreTriage: (scanId, context, topN = 20) =>
    apiClient.post(`/api/triage/${scanId}?top_n=${topN}`, context),
};
```

Export `triageAPI` from the api module.

---

### Task 6: TriageDashboard Frontend Component

**Files:**
- Create: `frontend/src/components/reports/TriageDashboard.jsx`
- Create: `frontend/src/components/reports/TriageDashboard.test.jsx`

- [ ] **Create `TriageDashboard.jsx`**

Component renders:
- Executive summary section (when available)
- Priority distribution bars (IMMEDIATE / HIGH / MEDIUM / LOW / INFO counts)
- Ranked findings table:
  - Composite score badge (colored: red ≥80, orange ≥60, yellow ≥40, green <40)
  - Finding title
  - Severity badge
  - Priority label with SLA
  - Click to expand: show score breakdown bars + AI triage summary
- Business context sidebar:
  - Asset criticality dropdown (low/medium/high/critical)
  - Data classification dropdown (public/internal/confidential/restricted)
  - Exposure level dropdown
  - "Re-score" button that calls POST

- [ ] **Add "Triage" tab to ReportDetails.jsx**

Follow the same pattern as the existing "Compare" tab:
```jsx
import TriageDashboard from './TriageDashboard';
// ...
{selectedTab === 'triage' && (
  <TriageDashboard scanId={scanId} projectId={projectId} />
)}
```

Add `triage` to the tabs array.

- [ ] **Add TriageDashboard tests**

Tests:
- Renders findings list
- Shows executive summary
- Score badge colors match priority
- Business context sidebar opens/closes
