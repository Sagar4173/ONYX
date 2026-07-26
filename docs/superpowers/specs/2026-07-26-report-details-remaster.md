# ReportDetails Remaster — Design Spec

**Date:** 2026-07-26
**Status:** Approved Design
**Approach:** Full visual + structural overhaul

## Overview

Remaster the `/report/:id` page into a premium security report viewer matching the quality bar of the ProjectDetails and Dashboard remasters. Add ParticleBackground ambient layer, animated tab navigation with count badges, severity pill filters, stagger-animated finding cards, enhanced overview charts using existing project components, progress-ring compliance cards, and extract inline compliance logic to a reusable utility.

## Layout

```
PageContainer
├── ParticleBackground (ambient animated layer)
├── PageHeader (with ExportDropdown + Download PDF buttons)
├── Info Bar (glass container)
│   └── date · repo · branch · StatusBadge · Scan ID · duration
├── Tab Navigation (glass container, animated underline)
│   ├── Overview | Findings (N) | AI Analysis | Compliance | Scanners
│   └── Active tab has gradient bg + underline indicator
└── Tab Content Area
    ├── Overview: MetricsDashboard style stats + ReportCharts + AI summary + scanner grid
    ├── Findings: SecretDetectionSummary + severity pill filters + staggered FindingCard list
    ├── AI Analysis: AISection component (unchanged)
    ├── Compliance: ComplianceMapping with progress rings (enhanced)
    └── Scanners: Enhanced ScannerResultCard grid
```

## Changes

### 1. complianceMapping.js (NEW utility)
- Extract `mapFindingToCompliance` function from ReportDetails.jsx
- Pure function, no React hooks, testable independently
- Same logic, same COMPLIANCE_STANDARDS import
- Location: `frontend/src/utils/complianceMapping.js`

### 2. ReportDetails.jsx (REWRITE)
- Add `ParticleBackground` import and render at top
- Replace inline loading state with existing `LoadingState` layout component
- Replace inline error state with existing `ErrorState` layout component
- Import `complianceMapping` from utils instead of inline function
- Import `MetricCard`, `SecurityScoreGlobe`, `SeverityBar` from projects for overview charts
- Tab nav: add count badge for findings tab, animated underline indicator for active tab
- Findings tab: replace `<select>` with pill button filter bar (Critical/High/Medium/Low/All)
- Wrap findings list in framer-motion `motion.div` with stagger animation
- Compliance tab: enhanced card layout with circular progress ring per standard
- Scanners tab: enhanced ScannerResultCard with severity breakdown + animated entry
- Keep existing data fetching, PDF generation, severity state
- Keep existing print styles

### 3. Tab Navigation Enhancements
- Current gradient active tab is good — add subtle underline indicator
- Add count badge: `findings (12)` for Findings tab, `ai (1)` for AI tab if analysis exists
- Animate tab indicator via framer-motion layoutId

### 4. Findings Tab Enhancements
- Replace severity dropdown with horizontal pill buttons: All, Critical (red), High (orange), Medium (yellow), Low (blue)
- Active pill gets solid gradient bg, inactive gets subtle border
- Findings list wraps in framer-motion stagger container
- FindingCard already exists — no changes needed, just animation wrapper

### 5. Compliance Tab Enhancements
- Keep existing ComplianceMapping component interface
- Add circular progress ring per standard (Canvas mini donut, like ReportGridCard)
- Standard toggle pills with active/inactive styling
- Better findings-per-standard distribution bars

### 6. Scanner Tab Enhancements
- Enhanced ScannerResultCard: add severity breakdown bar, duration, findings count
- Animation: stagger entry for card grid
- Keep same data interface

## Files to Create
| File | Description |
|---|---|
| `frontend/src/utils/complianceMapping.js` | Extracted pure utility function |

## Files to Modify
| File | Changes |
|---|---|
| `frontend/src/components/reports/ReportDetails.jsx` | Orchestrator rewrite — ParticleBackground, LoadingState/ErrorState, animated tabs, pill filters, stagger animations |
| `frontend/src/components/reports/ScannerResultCard.jsx` | Enhanced — severity breakdown, animated entry |

## Dependencies
- No new npm packages
- Reuses: `ParticleBackground`, `MetricCard`, `SecurityScoreGlobe` from `components/projects/`
- Reuses: `LoadingState`, `ErrorState` from `layouts/`
- Uses: framer-motion for animations, Canvas API for progress rings

## Data Flow
- Report + AI analysis fetched in ReportDetails.jsx (unchanged)
- `complianceMapping` utility imported and called directly — no prop changes
- All sub-components keep their existing prop interfaces
- `mapFindingToCompliance(report, standard)` → array of category codes

## Non-Goals
- No changes to AISection, FindingCard, ReportCharts, ComplianceMapping, ReportExport, SecretDetectionSummary internals (unless visual only)
- No new API endpoints
- No changes to PDF generation
- No print style changes
