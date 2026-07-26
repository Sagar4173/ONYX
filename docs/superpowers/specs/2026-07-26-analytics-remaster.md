# Analytics Page Remaster — Design Spec

## Goal
Remaster the Analytics page and all 6 sub-components with premium visual upgrades: ParticleBackground ambient layer, framer-motion staggered animations, Canvas mini donut charts, animated severity bars, glassmorphism elevation, and a clean custom hook for data aggregation.

## Architecture
Single-page orchestrator (`Analytics.jsx`) + 6 focused sub-components. Data aggregation logic extracted from inline `useMemo` into a `useAnalyticsData` custom hook. ParticleBackground as ambient backdrop.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, Canvas API, @tanstack/react-query
**Zero new npm dependencies.**

---

## File Changes

### 1. `frontend/src/hooks/useAnalyticsData.js` (NEW)
Extract the heavy `useMemo` from Analytics.jsx into a well-named custom hook.

```js
useAnalyticsData(daysBack) → {
  vulnSummary, totalVulnerabilities, totalScans, successRate,
  avgSecurityScore, totalProjects, topProjects, scannerPerformance,
  isLoading, hasError, refetch
}
```

Consumes 3 queries internally:
- `reportsAPI.getAnalyticsOverview(daysBack)`
- `projectsAPI.getAnalyticsOverview()`
- `reportsAPI.getReports({ limit: 50 })`

Aggregates fallback data when API fields are empty (same logic as current inline `useMemo`).

### 2. `frontend/src/components/analytics/SeverityDistribution.jsx`
Current: simple horizontal bars.  
Enhanced:
- Framer-motion entry with `initial={{ width: 0 }}` and `animate={{ width: pct + '%' }}` on each bar
- `whileInView` with `once: true` for scroll-triggered animation
- Glassmorphism container (`bg-gray-800/40 backdrop-blur-sm border border-gray-700/50`)
- Legend dots matching existing `MetricCard` pattern
- Gradient bars (e.g. `bg-gradient-to-r from-red-500 to-red-400`)

### 3. `frontend/src/components/analytics/ScanTypeDistribution.jsx`
Current: 2×2 grid with count and label.  
Enhanced:
- Each card gets a Canvas mini donut chart showing the scan type's proportion of total scans
- Canvas rendered in a `useEffect` + `useRef` for each card (75×75 canvas, 2px stroke, gradient colors)
- Framer-motion staggered entry (`staggerChildren: 0.08`)
- Hover-lift effect (`hover:-translate-y-1 hover:shadow-xl`)
- Glassmorphism card styling

### 4. `frontend/src/components/analytics/RecentScansTimeline.jsx`
Current: scrollable list with status icons.  
Enhanced:
- Framer-motion slide-in per item with `x: -20 → 0` stagger
- Severity-colored timeline dots + connecting line (CSS `::before` pseudo-element on the left)
- Glassmorphism card items
- Enhanced empty state with gradient icon
- Date/time formatting preserved

### 5. `frontend/src/components/analytics/TopProjects.jsx`
Current: ranked list with severity badges.  
Enhanced:
- Framer-motion stagger entry
- Animated rank badges with gradient (`layoutId` spring for 1st/2nd/3rd distinction)
- Inline mini severity bars (proportional horizontal stacked bars for critical/high/medium within each project)
- Glassmorphism styling
- Preserve rank number display

### 6. `frontend/src/components/analytics/ScannerPerformance.jsx`
Current: scanner list with success rate badge.  
Enhanced:
- Mini horizontal success/fail ratio bar (green/red segments proportional to success rate)
- Framer-motion stagger entry
- Glassmorphism container per scanner
- Enhanced duration display with icons

### 7. `frontend/src/components/analytics/TimePeriodSelector.jsx`
Current: simple button group.  
Enhanced:
- Glassmorphism background
- Active pill gets gradient background (`bg-gradient-to-r from-cyan-500 to-violet-500`)
- Framer-motion layout shift on active indicator

### 8. `frontend/src/pages/Analytics.jsx`
Current: 398-line orchestrator with inline `useMemo`, manual loading/error states, StatCard imports.  
Enhanced:
- Import `ParticleBackground` and place as ambient layer
- Import `useAnalyticsData` hook (replaces inline `useMemo`)
- Use `ErrorState` from layouts (replaces inline error UI)
- Replace `StatCard` with `MetricCard` from dashboard components (reuse existing)
- Framer-motion staggered stat cards (`staggerChildren: 0.06`)
- Framer-motion staggered chart sections
- Glassmorphism info bar for period display
- Export unchanged (still default export `Analytics`)

---

## Data Flow

```
Analytics.jsx
  ├── ParticleBackground (ambient, no props)
  ├── PageHeader + TimePeriodSelector
  ├── MetricCard row (4 cards, staggered)
  ├── SeverityDistribution (vulnSummary)
  ├── ScanTypeDistribution (scannerPerformance)
  ├── TopProjects (topProjects)
  ├── ScannerPerformance (scannerPerformance)
  └── RecentScansTimeline (scans)

useAnalyticsData(daysBack)
  ├── getAnalyticsOverview → analytics
  ├── getAnalyticsOverview → projectAnalytics
  └── getReports → reportsData
```

## States

| State | Behavior |
|-------|----------|
| **Loading** | `LoadingState` from layouts (shared skeleton) |
| **Error** | `ErrorState` from layouts with retry callback |
| **Empty data** | Individual `EmptyState` per sub-component (existing pattern) |
| **Edge case** — zero vulnerabilities | SeverityDistribution shows all bars at 0% |
| **Edge case** — no scanner activity | ScanTypeDistribution shows 0 counts, donuts show empty circles |

## Constraints
- Zero new npm dependencies
- All visualizations use Canvas, SVG, CSS, or framer-motion only
- ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- `npx eslint src/` must pass with 0 errors, 0 warnings
- Commit after each task

## Files to Create
- `frontend/src/hooks/useAnalyticsData.js`

## Files to Modify
- `frontend/src/pages/Analytics.jsx`
- `frontend/src/components/analytics/SeverityDistribution.jsx`
- `frontend/src/components/analytics/ScanTypeDistribution.jsx`
- `frontend/src/components/analytics/RecentScansTimeline.jsx`
- `frontend/src/components/analytics/TopProjects.jsx`
- `frontend/src/components/analytics/ScannerPerformance.jsx`
- `frontend/src/components/analytics/TimePeriodSelector.jsx`
