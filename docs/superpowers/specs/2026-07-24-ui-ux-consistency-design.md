# ONYX UI/UX Consistency Overhaul — Design Spec

**Date:** 2026-07-24
**Status:** Approved Design
**Objective:** Eliminate all UI/UX inconsistencies across the ONYX platform and establish a single-source-of-truth design system that is maintainable, accessible, and visually cohesive.

---

## Table of Contents

1. [Architecture & Design Token System](#1-architecture--design-token-system)
2. [Component Consolidation](#2-component-consolidation)
3. [Page-by-Page Migration](#3-page-by-page-migration)
4. [Accessibility Standards](#4-accessibility-standards)
5. [Animation & Motion System](#5-animation--motion-system)
6. [Responsive Behavior](#6-responsive-behavior)
7. [Verification Criteria](#7-verification-criteria)
8. [Implementation Order](#8-implementation-order)

---

## 1. Architecture & Design Token System

### 1.1 Current Problems

- Colors defined in 3 places: `tailwind.config.js`, `styles/theme.js`, `index.css` CSS variables — they drift apart
- Spacing uses arbitrary Tailwind values (`p-5`, `gap-6`, `mt-3`) with no semantic layer
- Border radius values mixed: `rounded-lg` (8px), `rounded-xl` (12px), `rounded-2xl` (16px) used interchangeably for cards
- Shadows use both Tailwind defaults and custom `shadow-glow` from config
- Typography is entirely inline — no semantic text style hierarchy
- Animations duplicated in `tailwind.config.js` keyframes and `index.css` keyframes

### 1.2 Target Architecture

```
styles/theme.js          ← Single source of all design tokens
styles/classNames.js     ← Class generator helpers using theme tokens
styles/components.jsx    ← Canonical React component implementations
  ↓ imports from
tailwind.config.js       ← References theme.js values for Tailwind JIT

index.css                ← Only global resets, font loading, scrollbar, print styles
                           NO animation keyframes, NO color variables, NO component classes
```

### 1.3 Design Tokens

#### Colors

Keep the existing semantic palette in `theme.js` (primary, secondary, success, warning, danger, info, severity). Remove CSS variable declarations from `index.css:root`. `tailwind.config.js` imports colors from `theme.js`.

**Enforcement:** No file outside `theme.js`/`classNames.js`/`components.jsx` may contain hardcoded color values like `#1a1a2e`, `bg-[#16213e]`, etc.

**Exception:** Data visualization colors (Recharts series colors, chart tooltip custom colors) are exempt — they are data-driven, not structural. Keep these in the component that uses them, documented with a comment referencing the chart purpose.

#### Spacing — 7-Tier Semantic Scale

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | `0.25rem` (4px) | Icon gaps, badge padding |
| `sm` | `0.5rem` (8px) | Button padding (sm), form element gap |
| `md` | `1rem` (16px) | Card padding, section gap |
| `lg` | `1.5rem` (24px) | Page section padding, card (lg) padding |
| `xl` | `2rem` (32px) | Page padding, modal padding |
| `2xl` | `3rem` (48px) | Large page sections |
| `3xl` | `4rem` (64px) | Hero sections, landing page |

#### Border Radius — 4-Tier Scale

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | `0.375rem` (6px) | Inputs, badges, small elements |
| `md` | `0.5rem` (8px) | Buttons, alerts |
| `lg` | `0.75rem` (12px) | Cards, modals, dropdowns, tooltips |
| `xl` | `1rem` (16px) | Large containers, modals (lg+) |

#### Shadows — 5-Tier Semantic Scale

| Token | Usage |
|-------|-------|
| `card` | Default card shadow |
| `elevated` | Elevated cards, hover states |
| `modal` | Modal backdrop + container |
| `dropdown` | Dropdowns, tooltips, popovers |
| `glow` | Active nav item, selected state |

#### Typography — Semantic

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `page-title` | `text-2xl` / `text-3xl` (xl screens) | `font-bold` | Main page heading `<h1>` |
| `section-title` | `text-xl` | `font-semibold` | Section heading `<h2>` |
| `card-title` | `text-lg` | `font-semibold` | Card heading `<h3>` |
| `body` | `text-sm` / `text-base` | `font-normal` | Body text, table cells |
| `caption` | `text-xs` | `font-normal` | Helper text, timestamps |
| `code` | `text-sm` | `font-mono` | Code blocks, inline code |

---

## 2. Component Consolidation

### 2.1 Duplicate Elimination

| Component | Files to Remove | Migrate Consumers To |
|-----------|----------------|---------------------|
| StatCard (pages/Dashboard.jsx inline) | Inline implementation | `styles/components.jsx` `StatCard` |
| StatCard (pages/AdminDashboard.jsx inline) | Inline implementation | `styles/components.jsx` `StatCard` |
| StatCard (pages/Analytics.jsx inline) | Inline implementation | `styles/components.jsx` `StatCard` |
| EmptyState (components/ui/EmptyState.jsx) | Delete file | `styles/components.jsx` `EmptyState` |
| Layout (components/ui/Layout.jsx) | Delete file | `styles/components.jsx` `Layout` helpers |
| lucide-react dependency | Remove package | Replace all imports with `@heroicons/react` |
| Duplicate keyframes in index.css | Remove from index.css | Already defined in `tailwind.config.js` |
| Duplicate animation classes in index.css | Remove from index.css | Already defined in `tailwind.config.js` |

### 2.2 Canonical Component Set

All components live in `styles/components.jsx`. Every page imports from here.

#### Button
```jsx
<Button variant="primary|secondary|success|danger|warning|ghost|outline|link"
        size="xs|sm|md|lg|xl"
        isLoading loadingText leftIcon rightIcon disabled />
```
- `rounded-lg` always
- Focus ring: `focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900`
- Loading state: show `Spinner` + optional `loadingText`
- Icon-only: use `IconButton` (requires `aria-label`)

#### Card
```jsx
<Card variant="default|elevated|outlined|success|danger|warning|info"
      padding="none|sm|md|lg|xl" hoverable>
  <CardHeader><CardTitle /><CardDescription /></CardHeader>
  <CardContent />
  <CardFooter />
</Card>
```
- `rounded-xl` always
- `bg-gray-800/50 backdrop-blur-sm border border-gray-700/50`

#### Badge
```jsx
<Badge variant="default|primary|success|danger|warning|info|critical|high|medium|low"
       size="xs|sm|md|lg" />
<SeverityBadge severity="critical|high|medium|low|info" />
```
- `rounded-full` always
- Severity colors map directly to security terminology

#### Form Inputs
```jsx
<Input variant="default|error|success" size="sm|md|lg" error="message" />
<Textarea rows={3} error />
<Select options={[{value, label}]} placeholder error />
<FormGroup><FormLabel required /><FormHint /><FormError /></FormGroup>
```
- `rounded-lg` always
- Focus ring: `focus:ring-2 focus:ring-blue-500/20`
- Error state: `border-red-500` + red text hint

#### Feedback Components
```jsx
<Alert variant="success|danger|warning|info" title icon onClose />
<Modal isOpen onClose title size="sm|md|lg|xl|full" footer />
<Skeleton variant="text|title|avatar|button|card" />
<EmptyState icon title description action />
<Spinner size="sm|md|lg|xl" />
<LoadingOverlay message="Loading..." />
```

#### Data Display
```jsx
<DataTable columns={[{key, label, render}]} data={[]} isLoading emptyMessage />
<Tabs tabs={[{id, label, icon, count}]} activeTab onChange />
<Code inline block>{children}</Code>
<DonutChart value max size strokeWidth color>
<SeverityProgressBar critical high medium low />
```

#### Navigation & Status
```jsx
<Tooltip content position="top|bottom|left|right">{children}</Tooltip>
<StatusDot status="success|warning|danger|info|neutral" />
<StatusIndicator status label />
<Avatar src alt name size="xs|sm|md|lg|xl" />
<Truncate text maxLength />
```

#### Layout Helpers
```jsx
<Layout.Page>       // <main> with max-w-7xl + responsive padding
<Layout.Section>    // <section> with consistent spacing
<Layout.Grid cols={2|3|4}>  // responsive grid
<Layout.Flex between|center|start|end>
```
- These are NOT new files — they are exported from `components.jsx`

---

## 3. Page-by-Page Migration

### 3.1 Dashboard (`pages/Dashboard.jsx`)
- Replace inline stat card map with `<StatCard>` canonical component
- Ensure all 4 stat cards use the same icon container style (`p-3 bg-gray-700/50 rounded-lg`)
- Replace any raw Heroicons markup with `<IconButton>` where applicable
- Loading state: use `<Skeleton variant="card" />` × 4 grid

### 3.2 Analytics (`pages/Analytics.jsx`)
- Replace inline stat cards with `<StatCard>`
- Wrap each Recharts chart in `<Card>` with `<CardHeader><CardTitle>`
- Add `<EmptyState>` when API returns no data
- Standardize chart tooltip styling to match `chartStyles.tooltip`

### 3.3 AdminDashboard (`pages/AdminDashboard.jsx`)
- Replace inline admin stat cards with `<StatCard>`
- Replace hardcoded color values (e.g., `bg-[#1a1a2e]`) with theme classes
- Use `<Skeleton variant="card" />` for loading rows

### 3.4 Reports (`pages/Reports.jsx`)
- Ensure all tab navigation uses `<Tabs>` canonical component
- Replace direct severity badge spans with `<SeverityBadge>`
- Replace inline code blocks with `<Code block>`
- Ensure PDF export button is `<Button variant="primary" leftIcon={<DocumentArrowDownIcon />}>`

### 3.5 Auth Components (`LoginForm`, `RegisterForm`, etc.)
- All inputs: `<Input>` with `<FormGroup>` + `<FormLabel required>` + `<FormError>`
- All submit buttons: `<Button variant="primary" size="lg" isLoading={isSubmitting}>`
- Unify loading state pattern: all submit buttons use `<Button isLoading={isSubmitting}>`, all load-in-progress states show `<Spinner>` in the form container, all initial data loading uses `<Skeleton>`

### 3.6 Marketing Pages (`LandingPage`, `AboutPage`, `DocumentationPage`)
- Apply consistent `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` container
- Standardize heading hierarchy (h1: `page-title`, h2: `section-title`, h3: `card-title`)
- Apply consistent glass-card pattern (already exists in CSS, apply uniformly)

### 3.7 Security Components
- **Remove `lucide-react` import** — replace every icon with `@heroicons/react/24/outline`
- Specific replacements:
  - `Shield` → `ShieldCheckIcon`
  - `AlertTriangle` → `ExclamationTriangleIcon`
  - `TrendingUp` / `TrendingDown` → `ArrowTrendingUpIcon` / `ArrowTrendingDownIcon`
  - `Search` → `MagnifyingGlassIcon`
  - `Download` → `ArrowDownTrayIcon`
  - `Copy` → `ClipboardIcon`
  - `CheckCircle` → `CheckCircleIcon`
  - `XCircle` → `XCircleIcon`
  - `ChevronDown` / `ChevronUp` → `ChevronDownIcon` / `ChevronUpIcon`
  - All others → map to closest Heroicons equivalent
- Then remove `lucide-react` from `package.json`
- Standardize SBOM viewer to use `<DataTable>` instead of custom table markup

### 3.8 Settings, Projects, Compliance, Users
- Tables → `<DataTable>` canonical component
- Empty states → `<EmptyState>`
- Buttons → `<Button>` canonical
- Modals → `<Modal>` canonical (check for inline modal implementations)
- Loading → `<Skeleton>` or `<Spinner>` consistent patterns

---

## 4. Accessibility Standards

### 4.1 Mandatory ARIA

| Component | Role | Key Attributes | Keyboard |
|-----------|------|----------------|----------|
| Button (native) | — (implicit) | `aria-disabled` when disabled | Enter/Space |
| IconButton | `button` | `aria-label="description"` **(required, enforced)** | Enter/Space |
| Tabs container | `tablist` | `aria-orientation="horizontal"` | Arrow keys |
| Tab button | `tab` | `aria-selected`, `aria-controls="panel-id"` | — |
| Tab panel | `tabpanel` | `aria-labelledby="tab-id"` | Tab into panel |
| Modal overlay | `presentation` | — | — |
| Modal container | `dialog` | `aria-modal="true"`, `aria-labelledby` | Escape, focus trap |
| Dropdown trigger | `button` (composite) | `aria-expanded`, `aria-haspup` | Enter/Space |
| Dropdown menu | `menu` | — | Arrow keys, Escape |
| Menu item | `menuitem` | — | Enter |
| Tooltip trigger | — | `aria-describedby="tooltip-id"` | Focus shows |
| Tooltip | `tooltip` | `id` matched to trigger's `aria-describedby` | — |
| Progress bar | `progressbar` | `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"` | — |
| Alert (error/danger) | `alert` | — | Announce on render |
| Table | — (native) | `<th scope="col">` on headers | — |
| Sortable header | `columnheader` | `aria-sort="ascending|descending"` | Enter to toggle |

### 4.2 Focus Management

- **Focus ring:** Every interactive element must show visible focus ring (`focus:ring-2 focus:ring-blue-500`)
- **Skip to content:** Add hidden skip-link as first focusable element
- **Modal focus trap:** Focus wraps within modal, returns to trigger on close
- **Dropdown focus return:** Focus returns to trigger on menu close
- **Page title:** Update `<title>` on route change

### 4.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important; }
}
```
Already exists in `index.css` — keep and verify it works.

---

## 5. Animation & Motion System

### 5.1 Single Source of Truth

All animation keyframes live in `tailwind.config.js` ONLY. Remove all keyframe definitions from `index.css` that duplicate Tailwind config.

### 5.2 Canonical Animations

| Name | Duration | Easing | Usage |
|------|----------|--------|-------|
| `fade-in` | 0.3s | ease-out | Page transitions, element entrance |
| `fade-in-up` | 0.5s | ease-out | Staggered card entrance |
| `slide-up` | 0.3s | ease-out | Modal, dropdown open |
| `scale-in` | 0.2s | ease-out | Tooltip, popover |
| `shimmer` | 2s | linear | Skeleton loading |
| `pulse-subtle` | 2s | ease-in-out | Status indicators |

### 5.3 Framer Motion Integration

`PageTransition` already wraps routes with `framer-motion`. Keep as-is — it is the only place `framer-motion` is used for route-level animations.

Remove any isolated `framer-motion` usage in individual components unless it provides meaningful UX value (not just decorative).

---

## 6. Responsive Behavior

### 6.1 Breakpoints

| Breakpoint | Tailwind | Usage |
|------------|----------|-------|
| Mobile | `< 640px` | Single column, collapsed sidebar |
| Tablet | `sm: 640px` — `lg: 1024px` | 2-column grid, compact sidebar |
| Desktop | `lg: 1024px`+ | Full layout, expanded sidebar |
| Wide | `xl: 1280px`+ | Max content width `max-w-7xl` |

### 6.2 Grid Standard

- Stat cards: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`
- Section cards: `grid grid-cols-1 lg:grid-cols-2 gap-6`
- Charts: full-width on mobile, side-by-side on desktop

### 6.3 Mobile

- Sidebar collapses to hamburger menu
- Tables horizontally scrollable (`overflow-x-auto`)
- Touch targets ≥ 44px (already in index.css `.mobile-touch-target`)
- Reduced animation duration (already in index.css `.mobile-reduced-motion`)

---

## 7. Verification Criteria

A page passes UI/UX consistency when:

1. **No hardcoded colors** appear outside `theme.js`/`tailwind.config.js`
2. **No hardcoded animation keyframes** exist in `index.css` (except print/reset)
3. **All buttons** use `<Button>` from `components.jsx`
4. **All cards** use `<Card>` from `components.jsx` (or semantic wrapper)
5. **All badges** use `<Badge>` from `components.jsx`
6. **All inputs** use `<Input>` from `components.jsx`
7. **All tables** use `<DataTable>` from `components.jsx`
8. **All empty states** use `<EmptyState>` from `components.jsx`
9. **All loading states** use `<Skeleton>` or `<Spinner>` from `components.jsx`
10. **No `lucide-react` imports** remain — all icons from `@heroicons/react`
11. **No duplicate component files** remain (`ui/EmptyState.jsx`, `ui/Layout.jsx` removed)
12. **No duplicate animation keyframes** in `index.css`
13. **ARIA requirements** met per Section 4 table
14. **`npm run build`** completes with no errors (type-check + build)
15. **`npm run lint`** passes (no eslint errors on changed files)

---

## 8. Implementation Order

The plan is executed in order — each step builds on the previous:

### Phase 1: Foundation (no visible changes)
1. Clean up `index.css` — remove duplicate keyframes, CSS variables, animation classes
2. Audit `theme.js` — ensure all tokens are complete and correct
3. Audit `classNames.js` — ensure all getter functions exist
4. Audit `components.jsx` — ensure all canonical components are present and correct

### Phase 2: Components (internal quality)
5. Add missing ARIA roles to `Tabs`, `Dropdown`, `Tooltip`, `Progress`, `Modal`
6. Ensure `IconButton` enforces `aria-label`
7. Remove `components/ui/EmptyState.jsx` and `components/ui/Layout.jsx`
8. Remove `lucide-react` dependency and replace all usages in security components

### Phase 3: Pages (visible consistency)
9. **Dashboard** — migrate inline stat cards
10. **Analytics** — migrate stat cards + chart containers
11. **AdminDashboard** — migrate stat cards + hardcoded colors
12. **Reports** — migrate tabs + severity badges
13. **Auth forms** — migrate inputs + buttons
14. **Settings / Projects / Compliance / Users** — migrate tables + empty states
15. **Marketing pages** — standardize containers + typography

### Phase 4: Polish
16. Verify all animations are consistent
17. Verify responsive behavior on mobile/tablet/desktop
18. Run full build + lint
19. Final accessibility audit

Each phase produces a working, deployable state before the next begins.

---

## Appendix A: Files to Delete

| File | Reason |
|------|--------|
| `src/components/ui/EmptyState.jsx` | Duplicate of `styles/components.jsx` version |
| `src/components/ui/Layout.jsx` | Abandoned — `layouts/UIComponents.jsx` is the active one |
| `node_modules/lucide-react` | Remove from package.json + delete |

## Appendix B: Files to Modify

| File | Changes |
|------|---------|
| `src/index.css` | Remove `:root` CSS vars, remove duplicate keyframes/animation classes, keep only reset/scrollbar/print/reduced-motion |
| `src/styles/theme.js` | Ensure all tokens present per Section 1.3 |
| `src/styles/classNames.js` | Ensure all getter functions return consistent values |
| `src/styles/components.jsx` | Add missing ARIA, ensure IconButton enforces aria-label |
| `src/pages/Dashboard.jsx` | Replace inline stat cards |
| `src/pages/Analytics.jsx` | Replace inline stat cards + chart containers |
| `src/pages/AdminDashboard.jsx` | Replace inline stat cards + hardcoded colors |
| `src/pages/Reports.jsx` | Standardize tabs/badges/code blocks |
| `src/components/auth/*.jsx` | Standardize inputs/buttons/loading |
| `src/components/security/SecurityTrendsDashboard.jsx` | Replace lucide-react icons |
| `src/components/security/ScanComparison.jsx` | Replace lucide-react icons |
| `src/components/security/SBOMViewer.jsx` | Replace lucide-react icons + standardize DataTable |
| `src/components/marketing/*.jsx` | Apply `<main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">`, heading hierarchy per typography tokens, glass-card pattern for info sections |
| `src/components/settings/Settings.jsx` | Replace inline buttons → `<Button>`, inline inputs → `<Input>`, inline cards → `<Card>`, add `<EmptyState>` for empty sections |
| `src/components/projects/*.jsx` | Replace inline tables → `<DataTable>`, inline buttons → `<Button>`, inline modals → `<Modal>`, inline empty states → `<EmptyState>` |
| `src/components/compliance/*.jsx` | Replace inline badges → `<SeverityBadge>`, inline tables → `<DataTable>`, inline progress → `<ProgressBar>` |
| `src/components/users/*.jsx` | Replace inline tables → `<DataTable>`, inline buttons → `<Button>`, inline empty states → `<EmptyState>` |
| `package.json` | Remove `lucide-react` dependency |
