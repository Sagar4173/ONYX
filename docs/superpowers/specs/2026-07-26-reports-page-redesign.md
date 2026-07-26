# ONYX Reports Page — Redesign & Polish

## Goal

Fix the Reports listing page (`/reports`) which currently fetches 50 records client-side with no real pagination, and clean up `ReportDetails.jsx` by extracting components, deduplicating badges, and removing dead code. Followed by a project-wide lint warning cleanup.

---

## Part 1: Reports Listing Page (`Reports.jsx`)

### Current State
- 304 lines, inline `ReportCard` component
- Fetches `reportsAPI.getReports({ limit: 50 })` — client-side-only filtering
- "Showing X of Y" text but no page controls
- No debounced search
- Status filter + sort dropdowns (client-side only)

### Target Architecture

```
src/pages/Reports.jsx         → ~50 line orchestrator
src/components/reports/
├── ReportCard.jsx             → Extracted from inline (grid card for listing)
├── ReportFilters.jsx          → Debounced search + status filter + sort
├── ReportList.jsx             → Paginated list + loading/empty/error states
└── (existing files unchanged)
```

### Changes
- `ReportCard.jsx`: Card with status accent, severity badges, scan type icon, hover effect
- `ReportFilters.jsx`: Debounced search, status dropdown, sort dropdown, filter chips
- `ReportList.jsx`: Pagination (prev/page numbers/next, per-page), loading skeleton, empty/error states
- `Reports.jsx`: Wires state, queries, and sub-components
- API: fetch with `page`, `per_page`, `search`, `status`, `sort_by` params. Fallback to client-side if backend doesn't support server-side pagination.

---

## Part 2: ReportDetails Cleanup

- Remove duplicate `SeverityBadgeInline` from `ReportSummary.jsx` → import from `ReportBadges.jsx`
- Remove duplicate `SeverityBadgeInline` from `VulnerabilityList.jsx` → import from `ReportBadges.jsx`
- Remove unused state: `_selectedFinding`, `_expandedFindings`, `_showCodeContext`
- Remove unreachable `activeTab === "remediation"` rendering (no tab button for it)
- Fix `key={index}` → use unique IDs where available
- Remove dead `console.log` and `console.error` statements (already logged by React Query)

---

## Part 3: Lint Warning Cleanup (Polish)

Fix all 52 pre-existing `npm run lint` warnings across the project:
- Unused imports/variables → remove or prefix with `_`
- Missing `react-hooks/exhaustive-deps` → add deps or suppress with eslint-disable comment where intentional
- `react-refresh/only-export-components` → split exports into separate files or add `// eslint-disable-next-line` comments

Target: 0 warnings, 0 errors from `npm run lint`.
