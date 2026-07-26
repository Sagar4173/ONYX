# Dashboard Remaster — Design Spec

**Date:** 2026-07-26
**Status:** Approved Design
**Approach:** Command Center (Hybrid A)

## Overview

Remaster the landing `/dashboard` page into a security command center that matches the visual quality of the ProjectDetails remaster. The dashboard becomes the organization-level security posture hub — the first thing users see when they log in.

## Layout

```
┌──────────────────────────────────────────────────────┐
│  ParticleBackground (ambient animated layer)          │
│                                                       │
│  ┌───────────────╥────────────────────────────┐       │
│  │  Globe        ║  Security Score            │  Hero  │
│  │  (left half)  ║  Animated counter + trend   │        │
│  └───────────────╨────────────────────────────┘       │
│                                                       │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐         │
│  │Metric │  │Metric │  │Metric │  │Metric │  Stats   │
│  │Card   │  │Card   │  │Card   │  │Card   │  Row     │
│  └───────┘  └───────┘  └───────┘  └───────┘         │
│                                                       │
│  ┌─────────────────┬─────────────┬──────────────┐    │
│  │ ScoreTrendChart │ QuickActions│ RecentScans  │    │
│  │ (Canvas line)   │ (icon grid) │ (list)       │  Grid │
│  └─────────────────┴─────────────┴──────────────┘    │
│                                                       │
│  ┌──────────────────────────────────────────────────┐│
│  │  Live Activity (auto-scrolling feed)              ││
│  └──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

## Components

### 1. DashboardHero.jsx (NEW)
- Split layout: left half renders `SecurityScoreGlobe` at dashboard scale, right half shows org security score as large `AnimatedCounter` with score trend arrow
- Props: `securityScore`, `scoreTrend`
- Uses existing `SecurityScoreGlobe` component (import from `../components/projects/`)
- Displays "Organization Security Posture" label + "Last updated" timestamp
- Wrapped in glassmorphism container (`bg-gray-800/40 backdrop-blur-xl border border-gray-700/50 rounded-2xl`)

### 2. MetricCard row
- Reuse existing `MetricCard` from `../components/projects/MetricCard.jsx`
- 4 cards in a responsive grid: Projects, Scans, Open Issues, Avg Score
- Each card shows animated counter + sparkline + trend percentage
- Data: `dashboardAPI.getQuickStats()` response

### 3. ScoreTrendChart.jsx (NEW — Canvas)
- Canvas-based line chart showing security score trend over time
- Computes score history from `reportsData` (each report has `created_at` + `security_score`)
- X-axis: dates, Y-axis: score (0-100)
- Gradient fill beneath the line (cyan-to-violet at high scores, red-to-orange at low)
- Smooth bezier curve, subtle grid lines
- Falls back to empty state when no report data exists
- Replaces `SecurityScoreChart` (the old SVG donut) in the first column

### 4. QuickActions.jsx (ENHANCED)
- Current 4-action grid (New Project, New Scan, View Reports, View Projects)
- Add: hover scale animations, gradient icon backgrounds, keyboard shortcut hints
- Keep same actions, same layout, same props — purely visual upgrade

### 5. RecentScans.jsx (ENHANCED)
- Current scan list with animated list items via framer-motion
- Per-scan: project name, scan type, status badge, severity breakdown, date
- Add: severity color bar on left edge of each item, staggered entry animation
- Empty state uses `EmptyState` with shimmer

### 6. LiveActivity.jsx (ENHANCED — renamed from inline section)
- Auto-scrolling feed with type-specific icons:
  - `scan_completed`: green checkmark circle
  - `scan_started`: blue spinner
  - `scan_error`: red X circle
  - Default: gray bolt
- Entries animate in with slide-down + fade
- Auto-scroll pauses on hover
- Empty state: subtle shimmer + "No recent activity" message
- Max height with overflow scroll (same as current 200px)

### 7. Dashboard.jsx (UPDATED orchestrator)
- Add `ParticleBackground` at the top of the return
- Replace `DashboardStatsBar` with `MetricCard` row
- Replace `SecurityScoreChart` with `ScoreTrendChart` in column 1
- Wrap the grid in glass container
- Add `DashboardHero` between PageHeader and stats row
- Keep existing data fetching, mutation logic, and refresh behavior

## Files to Create
| File | Description |
|---|---|
| `frontend/src/components/dashboard/DashboardHero.jsx` | Hero section with globe + score |
| `frontend/src/components/dashboard/ScoreTrendChart.jsx` | Canvas-based score trend line chart |

## Files to Modify
| File | Changes |
|---|---|
| `frontend/src/components/dashboard/QuickActions.jsx` | Visual upgrade (animations, gradients, key hints) |
| `frontend/src/components/dashboard/RecentScans.jsx` | Visual upgrade (staggered animation, severity bars) |
| `frontend/src/components/dashboard/DashboardStatsBar.jsx` | Deleted (replaced by MetricCard row) |
| `frontend/src/pages/Dashboard.jsx` | Orchestrator — add hero, MetricCard row, ScoreTrendChart |
| `frontend/src/components/dashboard/index.js` | Export new components |

## Dependencies
- No new npm packages
- Reuses: `ParticleBackground`, `SecurityScoreGlobe`, `MetricCard` from `components/projects/`
- Reuses: `PageContainer`, `PageHeader`, `GlassCard`, `SectionHeader`, `EmptyState` from `layouts/`
- Reuses: `AnimatedCounter` from `styles/components`
- Uses: Canvas API for `ScoreTrendChart`, framer-motion for animations

## Data Flow
- `dashboardAPI.getQuickStats()` → stats object → MetricCard row + DashboardHero
- `reportsAPI.getReports()` → reports data → ScoreTrendChart (score history) + RecentScans
- `notifications` prop → LiveActivity
- All data fetching stays in `Dashboard.jsx`, passed down as props

## Edge Cases
- **No data / first visit**: Hero shows score as "—" with "Run your first scan" CTA. MetricCards show 0. ScoreTrendChart shows empty state. RecentScans shows empty state.
- **Loading state**: Skeleton loaders for each section (already handled by parent query states)
- **Error state**: Existing error handling in parent, components render gracefully with null/zero data
- **Empty state after data**: "No recent scans" / "No recent activity" with appropriate icons
- **Single report**: ScoreTrendChart shows a single point or flat line with note

## Non-Goals
- No real-time WebSocket integration (feed works on polled data via `refetchInterval`)
- No drag-and-drop widget rearrangement
- No user-customizable layout
- No mobile-specific layout (responsive grid is sufficient)
