# ONYX Platform UI Excellence Program — Design Spec

## Overview

Elevate the ONYX Security Intelligence Platform from a functional dark-themed UI to a world-class security dashboard experience. Every pixel intentional, every interaction polished, every page consistent.

**Status:** Approved  
**Date:** 2026-07-25  
**Priority:** P0 — Full Overhaul  

---

## Current State Assessment

### Strengths (preserve & extend)
- Dark theme foundation (`bg-slate-950`, `gray-900`, glass morphism)
- Comprehensive design system in `styles/` (theme.js, classNames.js, components.jsx) with 40+ reusable components
- Custom gradient backgrounds with mesh-drift animation
- Glass morphism card system (`.glass-card`, `GlassCard`)
- Strong severity color system (Tailwind + inline support)
- Breadcrumb, PageHeader, SectionHeader layout components
- Loading/Error/Empty state components in layouts
- Custom Tailwind config with colors, animations, box shadows
- Mobile responsive utilities
- WebSocket real-time notifications

### Gaps (to address)
- Many pages bypass the centralized design system — raw Tailwind instead of `<Button>`, `<Card>`, `<Badge>`, `<Input>`
- `styles/components.jsx` components exist but are not enforced or universally used
- `UserProfile.jsx` (~2312 lines) and `EnhancedReportDetails.jsx` (~3455 lines) are monoliths
- No command palette, keyboard shortcuts, or consistent confirmation dialogs
- Page transitions and micro-interactions inconsistently applied
- Accessibility gaps (aria labels, focus management, keyboard nav)
- No route-level code splitting
- No consistent DataTable pattern
- Long lists lack virtualization

---

## Design Principles

1. **Consistency First** — One component, one way. Every button, card, badge, input, and table uses the design system.
2. **Glass + Gradient Design Language** — The existing glass morphism + gradient accents define ONYX's visual identity. Lock it in universally.
3. **Dark-First, Always** — No remnants of light-mode classes anywhere. The dark theme is the only theme.
4. **Performance is UX** — Code splitting, memoization, and virtualization are not optional.
5. **Accessibility is Quality** — Keyboard navigation, focus management, aria labels, color contrast.
6. **Micro-Interactions Matter** — Hover lifts, click scales, entrance staggers, animated counters.

---

## Phase 1: Design System Hardening

### New Shared Components

| Component | File | Purpose |
|---|---|---|
| `DataTable` | `styles/components.jsx` | Sortable, filterable, paginated table — replaces ad-hoc table HTML |
| `ConfirmDialog` | `styles/components.jsx` | Reusable confirmation modal for destructive actions |
| `PageTransition` | `styles/components.jsx` | Wraps route content with entrance animation |
| `MetricCard` | `styles/components.jsx` | Standard KPI metric card (icon, value, label, trend) |
| `FindingCard` | `styles/components.jsx` | Security finding display card (severity, title, metadata) |
| `StatusBadge` | `styles/components.jsx` | Status badge (active/inactive/suspended/pending) — generic version |

### Consolidated Barrel Export

Create a single import path from `components/common`:
```js
export { Button, Card, Badge, Input, Modal, Tabs, Select, Textarea, DataTable, ConfirmDialog, MetricCard, FindingCard, StatusBadge, Avatar, Tooltip, Spinner, Skeleton, ProgressBar, SeverityProgressBar, Code, Divider, AnimatedListItem, DonutChart, EmptyState, StatCard, PageTransition } from "../../styles/components";
export { CommandPalette } from "./CommandPalette";
```

### Convention
- All new components must use the design system internally.
- Existing pages are grandfathered but targeted for migration in Phase 3.
- Linting rule: prefer imports from `styles/components` over raw Tailwind for structural classes.

---

## Phase 2: Monolith Decomposition

### UserProfile.jsx (~2312 lines) → 6 files

| File | Responsibility | Est. Lines |
|---|---|---|
| `UserProfile.jsx` | Shell — tab layout, orchestrates sub-views, modal close | ~100 |
| `ProfileInfo.jsx` | Avatar upload, name/email/bio editing | ~250 |
| `SecuritySettings.jsx` | Password change, 2FA setup/disable, active sessions list | ~350 |
| `ApiTokens.jsx` | Token creation, revoke, copy-to-clipboard, expiry display | ~300 |
| `NotificationPreferences.jsx` | Email/in-app notification toggle groups | ~200 |
| `ActivityLog.jsx` | Recent account activity timeline with pagination | ~250 |

### EnhancedReportDetails.jsx (~3455 lines) → 7 files

| File | Responsibility | Est. Lines |
|---|---|---|
| `EnhancedReportDetails.jsx` | Shell — report header, tab navigation, data fetching | ~200 |
| `ReportSummary.jsx` | Security score ring, stat cards, report metadata | ~350 |
| `VulnerabilityList.jsx` | Filterable, sortable, paginated findings table | ~400 |
| `ReportCharts.jsx` | Severity breakdown bar, trend line chart, donut chart | ~300 |
| `ComplianceMapping.jsx` | Framework-to-finding mapping, gap analysis table | ~350 |
| `ReportExport.jsx` | Export to PDF/CSV/SARIF, format selection | ~200 |
| `ReportComparison.jsx` | Side-by-side diff view between two scans/reports | ~300 |

---

## Phase 3: Page Migration Priority

| Order | Page | Key Design System Components to Use |
|---|---|---|
| 1 | `Dashboard.jsx` | `GlassCard`, `StatCard`, `SectionHeader`, `AnimatedListItem`, `LiveIndicator` |
| 2 | `ProjectManagement.jsx` | `Card`, `Badge`, `Button`, `EmptyState`, `DataTable` |
| 3 | `ProjectDetails.jsx` | `GlassCard`, `DataTable`, `SeverityBadge`, `MetricCard`, `SeverityProgressBar` |
| 4 | `Reports.jsx` | `PageHeader`, `GlassCard`, `DataTable`, `Badge`, `Button` |
| 5 | `Analytics.jsx` | `PageHeader`, `GlassCard`, `StatCard`, `DonutChart`, `DataTable` |
| 6 | Security widgets (x3) | `GlassCard`, `SectionHeader`, `MetricCard`, `Badge`, `SeverityBadge` |
| 7 | `AdminDashboard.jsx` | `GlassCard`, `StatCard`, `DataTable`, `SectionHeader` |
| 8 | `AdvancedCompliance.jsx` | `GlassCard`, `DataTable`, `Badge`, `Button`, `ProgressBar` |
| 9 | `DataRetentionPolicies.jsx` | `GlassCard`, `Card`, `Button`, `Badge`, `ConfirmDialog` |
| 10 | `UserManagement.jsx` | `PageHeader`, `GlassCard`, `DataTable`, `Button`, `Badge`, `Avatar` |
| 11 | `AuditLogs.jsx` | `PageHeader`, `GlassCard`, `DataTable`, `Badge` |
| 12 | `Settings.jsx` | `PageHeader`, `GlassCard`, `Card`, `Input`, `Select`, `Button` |
| 13 | Auth components | `Card`, `Input`, `Button`, `Alert` |

Each migration step is identical:
1. Import design system components
2. Replace raw Tailwind structural classes with component equivalents
3. Visual verification — page looks identical or better
4. No regressions in functionality

---

## Phase 4: UX Excellence Layer

### 4.1 Command Palette
- Trigger: `Cmd+K` / `Ctrl+K` globally
- Search scope: navigation routes, project names, recent reports, quick actions
- UI: Modal overlay with search input, category groups, keyboard navigation (arrows + enter)
- Fuzzy matching on search terms
- Component: `CommandPalette.jsx` → mounted in `MainLayout.jsx`
- Tech: `fuse.js` for lightweight fuzzy search

### 4.2 Page Transitions
- Wrap `<Routes>` children with `<PageTransition>` that applies `animate-fade-in-up`
- Stagger child cards with `AnimatedListItem` using incremental `animationDelay`
- Transitions use existing CSS keyframes (no new animation library needed)

### 4.3 Micro-Interactions

| Element | Before | After |
|---|---|---|
| Interactive cards | No hover effect | `hover:-translate-y-1 hover:shadow-lg hover:border-blue-500/30` |
| Primary buttons | Color change only | Add `hover:scale-[1.02] active:scale-[0.98]` |
| Sidebar nav items | Static | `hover:scale-105` on icon, active indicator glow |
| Severity badges | Static | `animate-pulse-subtle` on critical/high |
| Stat values | Static number | `AnimatedCounter` on mount + intersection observer |
| Table rows | `hover:bg-gray-800/30` | Add `transition-colors duration-150` |
| Form inputs | Basic border change | Add focus ring + label float animation |
| Loading skeletons | Static shimmer | Staggered appear with `animationDelay` |

### 4.4 Accessibility
- All interactive elements get `focus-visible:ring-2 focus-visible:ring-blue-500`
- All modals implement focus trapping (tab stays within modal)
- All form inputs with errors get `aria-describedby` + `aria-invalid`
- All icon-only buttons get `aria-label`
- Color contrast: all text meets WCAG AA (4.5:1 for normal, 3:1 for large)
- All tables get proper `<th>` scope attributes
- All tab panels get `role="tablist"` + `aria-selected` + `aria-controls`
- All expandable sections get `aria-expanded`

### 4.5 State Components
- Every data-fetching view uses one of:
  - `LoadingState` — skeleton cards + spinner
  - `EmptyState` — icon + title + description + optional action
  - `ErrorState` — icon + message + retry button
- No more inline "Loading...", "No data", or raw error text

### 4.6 Confirmation Dialogs
- `ConfirmDialog` component with:
  - Title, description, confirm button variant (danger/warning), cancel
  - Optional "type to confirm" for high-risk actions (delete project, purge data)
  - Focus trap, escape to close, click-outside to close

---

## Phase 5: Performance

### 5.1 Route-Level Code Splitting
```jsx
const Dashboard = React.lazy(() => import("../pages/Dashboard"));
const ProjectManagement = React.lazy(() => import("../components/projects/ProjectManagement"));
// ... every route
```
Wrap in `<Suspense fallback={<LoadingScreen />}>`.

### 5.2 Component Memoization
- `React.memo` on: `StatCard`, `Badge`, `SeverityBadge`, `FindingRow`, `PackageRow`, table rows
- `useMemo` on: filtered/sorted lists, aggregated stats, chart data
- `useCallback` on: event handlers passed as props to memoized children

### 5.3 Virtualized Lists
- `react-window` for: vulnerability findings list, package list, user list, audit log entries
- Replace `.map()` + `overflow-y-auto` with `<FixedSizeList>` or `<VariableSizeList>`

### 5.4 Import Cleanup
- All pages import from two places: `"../layouts"` and `"../components/common"` or `"../styles/components"`
- No more scattered imports from deep paths
- Tree-shakeable barrel exports

---

## Verification Strategy

| Phase | Verification Method |
|---|---|
| 1 (Design System) | Storybook-style manual check of each component in isolation |
| 2 (Decomposition) | Each sub-file renders identically to original — visual diff |
| 3 (Migration) | Before/after screenshots for each page. Confirm all functionality works |
| 4 (UX) | Manual interaction testing. Lighthouse accessibility audit. Keyboard nav walkthrough |
| 5 (Performance) | Lighthouse performance score. Bundle size before/after. Render profiling |

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Regressions during decomposition | Medium | One sub-file at a time, visual diff after each, feature freeze on those pages during work |
| Migration scope creep | Medium | Each page has a clear before/after checklist. No scope expansion mid-migration |
| Performance regression from new components | Low | Bundle size CI check. Lazy-load all new heavy components |
| Design system components breaking existing pages | Low | Backward-compatible API. No breaking changes to existing component interfaces |

---

## Completion Criteria

- [ ] All 15+ new shared components are built and documented
- [ ] `UserProfile.jsx` and `EnhancedReportDetails.jsx` are decomposed into focused sub-files
- [ ] All 13 pages/groups use the design system (no raw Tailwind for structural classes)
- [ ] Command palette works globally with fuzzy search
- [ ] Page transitions animate consistently on route change
- [ ] Micro-interactions applied to all interactive elements
- [ ] Lighthouse accessibility score >= 90
- [ ] All long lists are virtualized
- [ ] Route-level code splitting implemented
- [ ] Bundle size reduced by at least 40%
