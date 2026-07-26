# Reports List Remaster — Design Spec

**Date:** 2026-07-26
**Status:** Approved Design
**Approach:** Enhanced List + Grid Toggle (Approach A)

## Overview

Remaster the `/reports` page with a list/grid toggle view, visually richer report cards, enhanced filter bar, and staggered animations — matching the quality bar of the ProjectDetails and Dashboard remasters.

## Layout

```
PageContainer
├── PageHeader (title + Refresh button + List/Grid toggle)
├── ReportFilters (enhanced select styling, active chips)
├── ReportList
│   ├── List View: ReportListItem[]
│   │   ┌──────────────────────────────────────────────────────┐
│   │   │ [severity bar] [icon] Project Name        [severity] │
│   │   │               scan_type · date             badges   │
│   │   ├──────────────────────────────────────────────────────┤
│   │   │ ... staggered framer-motion animation               │
│   │   └──────────────────────────────────────────────────────┘
│   ├── Grid View: ReportGridCard[]
│   │   ┌──────────┐ ┌──────────┐ ┌──────────┐
│   │   │  [donut] │ │  [donut] │ │  [donut] │
│   │   │  Score   │ │  Score   │ │  Score   │
│   │   │  Project │ │  Project │ │  Project │
│   │   │  type    │ │  type    │ │  type    │
│   │   │  finds   │ │  finds   │ │  finds   │
│   │   └──────────┘ └──────────┘ └──────────┘
│   └── Pagination (unchanged)
```

## Components

### 1. ReportListItem.jsx (NEW)
- Severity color bar on left edge (red=has critical, orange=has high, yellow=has medium, transparent=clean)
- Rich status icon with pulse animation for running/pending states
- SVG scan type icons (replace emoji) — colored gradient boxes like QuickActions
- Project name + repository URL (truncated)
- Per-severity count badges (CRIT 3 HIGH 5 MED 2 LOW 1) or "Clean" badge
- Scan type label + date
- framer-motion `motion.div` with stagger animation
- Click navigates to `/report/:id`

### 2. ReportGridCard.jsx (NEW)
- Glass card container (`bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl`)
- Canvas mini donut chart showing score (0-100) with color coding (green ≥ 80, yellow ≥ 60, red < 60)
- Score number centered in donut
- Project name (truncated, semibold)
- Scan type badge (colored pill)
- Findings summary: "12 findings (3 critical, 5 high, 2 medium, 2 low)"
- Hover: scale + glow effect
- framer-motion stagger animation for grid entries
- Click navigates to `/report/:id`

### 3. ReportList.jsx (REWRITE)
- Accepts `viewMode` prop ("list" | "grid")
- Renders `ReportListItem` array in list mode, `ReportGridCard` grid in grid mode
- Keeps existing pagination component (already well-built)
- Loading state: 5 skeleton rows (list) or 6 skeleton cards (grid)
- Error state: same as current but with enhanced button
- Empty state: same as current (EmptyState component)

### 4. ReportFilters.jsx (ENHANCED)
- Same interface and props — purely visual upgrade
- Search input: gradient focus ring, refined placeholder
- Status and Sort selects: cyan focus ring, consistent dark styling
- Active filter chips: same design, subtle animation on add/remove
- Report count: consistent placement

### 5. Reports.jsx (MINOR UPDATE)
- Add `const [viewMode, setViewMode] = useState("list")`
- Pass `viewMode` and `onViewModeChange` to ReportList
- Add toggle button in PageHeader actions (two SVG icons: list bars + grid squares)
- All other state and data fetching unchanged

## Files to Create
| File | Description |
|---|---|
| `frontend/src/components/reports/ReportListItem.jsx` | Enhanced list item with severity bar |

## Files to Modify
| File | Changes |
|---|---|
| `frontend/src/components/reports/ReportList.jsx` | Accept viewMode, render list/grid, enhanced skeletons |
| `frontend/src/components/reports/ReportCard.jsx` | Replaced by ReportListItem + ReportGridCard (delete) |
| `frontend/src/components/reports/ReportFilters.jsx` | Visual upgrade (selects, chips, search) |
| `frontend/src/pages/Reports.jsx` | Add viewMode state + toggle button |

## Dependencies
- No new npm packages
- Canvas API for mini donut chart in ReportGridCard
- framer-motion for staggered animations
- Existing: `Badge`, `Skeleton`, `Button`, `EmptyState` from `styles/components`
- Existing: `GlassCard` from `layouts/`

## Data Flow
- `Reports.jsx` owns `viewMode` state, `filters`, `sort`, `pagination`
- All data fetching unchanged (`reportsAPI.getReports`)
- `ReportList` receives viewMode, reports, pagination, loading, error, callbacks
- `ReportListItem` and `ReportGridCard` receive `report` object + `onClick`
- `ReportFilters` receives `filters`, `onFilterChange`, `sort`, `onSortChange`, `total`

## Edge Cases
- **No reports**: EmptyState with DocumentTextIcon (unchanged, keep)
- **Loading**: Skeleton per view mode — row skeletons for list, card skeletons for grid
- **Error**: Error state with retry button (keep, upgrade button)
- **Toggle while loading**: Graceful — loading state re-renders with correct skeleton layout
- **Toggle mid-pagination**: View switches instantly, pagination state preserved
- **Single report**: Both views render one item/card fine
- **Very long project names**: CSS truncation with ellipsis

## Non-Goals
- No inline scan status polling (that's project-level)
- No drag-and-drop column customization
- No column sorting in list view (filter/sort in header is sufficient)
- No bulk select/actions
