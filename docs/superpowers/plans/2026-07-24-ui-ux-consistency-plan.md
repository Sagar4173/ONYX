# ONYX UI/UX Consistency Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate all UI/UX inconsistencies across the ONYX frontend by consolidating duplicated components, enforcing a single design token system, and applying accessibility standards.

**Architecture:** Single-source-of-truth design tokens in `styles/theme.js`, class generators in `styles/classNames.js`, canonical components in `styles/components.jsx`. Every page imports from these — no inline style definitions, no hardcoded colors, no duplicated components.

**Tech Stack:** React 18, Vite, Tailwind CSS 3, Headless UI, Heroicons, Framer Motion, Recharts

## Global Constraints

- No color values outside `styles/theme.js`, `styles/classNames.js`, `styles/components.jsx` (exception: Recharts series colors)
- No animation keyframes in `index.css` — all in `tailwind.config.js` only
- All buttons use `<Button>` from `components.jsx`
- All cards use `<Card>` from `components.jsx`
- All badges use `<Badge>` or `<SeverityBadge>` from `components.jsx`
- All inputs use `<Input>` from `components.jsx`
- All tables use `<DataTable>` from `components.jsx`
- All empty states use `<EmptyState>` from `components.jsx`
- All loading states use `<Skeleton>` or `<Spinner>` from `components.jsx`
- All icons from `@heroicons/react` only — no `lucide-react`
- ARIA requirements per spec Section 4
- `npm run build` must pass after all changes

---

### Task 1: Clean up index.css — remove duplicate keyframes and CSS variables

**Files:**
- Modify: `frontend/src/index.css:1-1097`

- [ ] **Step 1: Remove CSS variable declarations from `:root` block**

In `frontend/src/index.css`, remove lines 6-20 (the `:root` block with CSS variables). These duplicate what's already in `tailwind.config.js` and `theme.js`.

- [ ] **Step 2: Remove duplicate animation keyframes that exist in tailwind.config.js**

In `frontend/src/index.css`, remove lines 128-218 (duplicate keyframes for `fadeInUp`, `slideInLeft`, `slideInRight`, `scaleIn`, `pulse`, `spin`, `bounce`, `shimmer`, `float`). These are already defined in `tailwind.config.js:108-161`.

- [ ] **Step 3: Remove duplicate animation classes that duplicate tailwind config**

In `frontend/src/index.css`, remove lines 220-276 (`.animate-fade-in-up`, `.animate-slide-in-left`, `.animate-scale-in`, `.animate-shimmer`, `.animate-glow`, `.animate-float` — these classes exist in tailwind's `extend.animation` already).

Also remove lines 279-333 (the second set of keyframes: `fadeIn`, `bounce-subtle`, `pulse-subtle`, `shimmer-slide`, `float-gentle`).

Also remove lines 475-484 (`.animate-fadeIn`, `.animate-bounce-subtle`, `.animate-pulse-subtle`).

- [ ] **Step 4: Remove `.glass-card`, `.glass-button`, `.glass`, `.glass-light` classes (lines 337-376)**

These duplicate what `cardStyles` and the glass utilities do in `classNames.js`. Keep only these CSS-only utilities that have no JS counterpart:
- `.glass` and `.glass-light` — keep these, they are used for non-card elements
- Keep: live-pulse, status-dot, skeleton-card, btn-primary, btn-secondary, btn-danger, card, card-hover, card-glow, progress-bar, progress-fill

Wait — actually, let me be more careful. Some of these CSS classes are referenced by JS components. Let me identify which are safe to remove:

Safe to remove (duplicated in `components.jsx` or `classNames.js`):
- `.animate-fade-in-up` — duplicate of tailwind `animate-fade-in-up`
- `.animate-slide-in-left` — not in tailwind config but used in `AnimatedListItem` via `className="animate-fade-in-up"` — keep
- `.skeleton-card` — duplicate of `Skeleton` component
- `.btn-primary`, `.btn-secondary`, `.btn-danger` — duplicate of `Button` component
- `.card`, `.card-hover`, `.card-glow` — duplicate of `Card` component
- `.glass-card`, `.glass-button` — duplicate of card variants

Remove only these clearly duplicated classes. Keep everything else.

- [ ] **Step 5: Verify no breakage**

Run: `npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/index.css
git commit -m "refactor: remove duplicate animations and CSS vars from index.css"
```

---

### Task 2: Audit and tighten theme.js tokens

**Files:**
- Modify: `frontend/src/styles/theme.js:1-317`

- [ ] **Step 1: Verify theme.js has all required tokens**

Read `frontend/src/styles/theme.js` and confirm:
- Has all 5 severity colors (critical, high, medium, low, info) with bg/text/border
- Has all semantic color groups (primary, success, warning, danger, info)
- Has spacing scale (xs through 3xl)
- Has typography scale (font sizes, weights)
- Has shadow definitions
- Has border radius scale
- Has animation helpers
- Has `getSeverityStyles` function

If any are missing, add them.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/styles/theme.js
git commit -m "refactor: verify and tighten design tokens in theme.js"
```

---

### Task 3: Audit classNames.js for completeness

**Files:**
- Modify: `frontend/src/styles/classNames.js:1-429`

- [ ] **Step 1: Verify all getter functions exist and produce consistent values**

Read `frontend/src/styles/classNames.js` and confirm all these getter functions exist:
- `getButtonClasses(variant, size, isIconOnly)` — exists at line 49
- `getCardClasses(variant, padding, hoverable)` — exists at line 89
- `getInputClasses(variant, size)` — exists at line 123
- `getBadgeClasses(variant, size)` — exists at line 156
- `getAlertClasses(variant)` — exists at line 267
- `getProgressClasses(color, size)` — exists at line 345

Verify each produces correct classes by checking their internal style map references.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/styles/classNames.js
git commit -m "refactor: verify class generator completeness in classNames.js"
```

---

### Task 4: Add ARIA roles to canonical components

**Files:**
- Modify: `frontend/src/styles/components.jsx`

- [ ] **Step 1: Add ARIA to Tabs component (line 702)**

Edit the `Tabs` component to add:
- `role="tablist"` and `aria-orientation="horizontal"` on the `<nav>` container
- `role="tab"`, `aria-selected`, `aria-controls` on each tab button
- `role="tabpanel"` and `aria-labelledby` on panel content (requires panel content to be passed as children or have panel IDs)

Implementation changes at lines 702-726:
```jsx
export const Tabs = ({ tabs, activeTab, onChange, className = "" }) => {
  return (
    <div className={`border-b border-gray-700 ${className}`}>
      <nav className="flex gap-1" role="tablist" aria-orientation="horizontal">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            className={
              activeTab === tab.id ? navStyles.tabActive : navStyles.tab
            }
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
            {tab.count !== undefined && (
              <Badge size="xs" variant="default" className="ml-2">
                {tab.count}
              </Badge>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
};
```

- [ ] **Step 2: Add ARIA to Tooltip component (line 755)**

Add unique ID generation and `aria-describedby`:
```jsx
export const Tooltip = ({ content, children, position = "top" }) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const tooltipId = React.useId();

  const positions = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      aria-describedby={isVisible ? tooltipId : undefined}
    >
      {children}
      {isVisible && (
        <div
          id={tooltipId}
          role="tooltip"
          className={`absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded shadow-lg border border-gray-700 whitespace-nowrap ${positions[position]}`}
        >
          {content}
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 3: Add ARIA to IconButton (line 60)**

Add aria-label validation — ensure the `label` prop is required:
```jsx
export const IconButton = ({
  icon,
  variant = "ghost",
  size = "md",
  label,
  className = "",
  ...props
}) => {
  if (!label) {
    console.warn("IconButton requires a `label` prop for accessibility");
  }
  // ... rest remains same
```

- [ ] **Step 4: Add ARIA to Modal (line 400)**

Add dialog role and title reference:
```jsx
export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
}) => {
  if (!isOpen) return null;
  const titleId = React.useId();

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
    full: "max-w-full mx-4",
  };

  return (
    <div className={modalStyles.overlay} onClick={onClose}>
      <div
        className={`${modalStyles.container} ${sizeClasses[size]}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className={modalStyles.header}>
            <h2 id={titleId} className={modalStyles.title}>{title}</h2>
            // ... rest
```

- [ ] **Step 5: Add ARIA to ProgressBar (line 521)**

```jsx
export const ProgressBar = ({
  value = 0,
  max = 100,
  color = "primary",
  size = "md",
  showLabel = false,
  animated = false,
  className = "",
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const { container, bar } = getProgressClasses(color, size);

  return (
    <div className={`${className}`}>
      <div className={container} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
        <div
          className={`${bar} ${animated ? "animate-pulse" : ""}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      // ... rest
```

- [ ] **Step 6: Build and lint check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/styles/components.jsx
git commit -m "feat: add ARIA roles to Tabs, Tooltip, IconButton, Modal, ProgressBar"
```

---

### Task 5: Remove lucide-react and replace all icons in security components

**Files:**
- Modify: `frontend/src/components/security/SecurityTrendsDashboard.jsx`
- Modify: `frontend/src/components/security/ScanComparison.jsx`
- Modify: `frontend/src/components/security/SBOMViewer.jsx`
- Modify: `frontend/package.json`

- [ ] **Step 1: Identify all lucide-react imports and Heroicons replacements**

Read each security component file and list all lucide-react icon imports. Create a mapping:

| lucide-react icon | Heroicons replacement |
|---|---|
| `Shield` | `ShieldCheckIcon` |
| `AlertTriangle` | `ExclamationTriangleIcon` |
| `AlertCircle` | `ExclamationCircleIcon` |
| `TrendingUp` | `ArrowTrendingUpIcon` |
| `TrendingDown` | `ArrowTrendingDownIcon` |
| `Search` | `MagnifyingGlassIcon` |
| `Download` | `ArrowDownTrayIcon` |
| `Copy` | `ClipboardIcon` |
| `CheckCircle` | `CheckCircleIcon` |
| `XCircle` | `XCircleIcon` |
| `ChevronDown` | `ChevronDownIcon` |
| `ChevronUp` | `ChevronUpIcon` |
| `ChevronLeft` | `ChevronLeftIcon` |
| `ChevronRight` | `ChevronRightIcon` |
| `ChevronsDown` | `ChevronDoubleDownIcon` |
| `ChevronsUp` | `ChevronDoubleUpIcon` |
| `ChevronsLeft` | `ChevronDoubleLeftIcon` |
| `ChevronsRight` | `ChevronDoubleRightIcon` |
| `RefreshCw` | `ArrowPathIcon` |
| `RefreshCcw` | `ArrowUturnLeftIcon` |
| `MoreHorizontal` | `EllipsisHorizontalIcon` |
| `MoreVertical` | `EllipsisVerticalIcon` |
| `X` | `XMarkIcon` |
| `Menu` | `Bars3Icon` |
| `Maximize2` | `ArrowsPointingOutIcon` |
| `Minimize2` | `ArrowsPointingInIcon` |
| `ExternalLink` | `ArrowTopRightOnSquareIcon` |
| `Info` | `InformationCircleIcon` |
| `FileText` | `DocumentTextIcon` |
| `BarChart3` | `ChartBarSquareIcon` |
| `PieChart` | `ChartPieIcon` |
| `Activity` | `ChartBarIcon` |
| `Zap` | `BoltIcon` |
| `Lock` | `LockClosedIcon` |
| `Unlock` | `LockOpenIcon` |
| `Eye` | `EyeIcon` |
| `EyeOff` | `EyeSlashIcon` |
| `Trash2` | `TrashIcon` |
| `Edit3` | `PencilSquareIcon` |
| `Plus` | `PlusIcon` |
| `Minus` | `MinusIcon` |
| `Settings` | `Cog6ToothIcon` |
| `Users` | `UsersIcon` |
| `User` | `UserIcon` |
| `Calendar` | `CalendarIcon` |
| `Clock` | `ClockIcon` |
| `Filter` | `FunnelIcon` |
| `SortAsc` | `BarsArrowUpIcon` |
| `SortDesc` | `BarsArrowDownIcon` |
| `Github` | No direct Heroicons equivalent — use inline SVG or import from `react-icons` if needed |

- [ ] **Step 2: Replace imports in SecurityTrendsDashboard.jsx**

Change:
```jsx
import { Shield, AlertTriangle, TrendingUp, TrendingDown, Search } from "lucide-react";
```
To:
```jsx
import { ShieldCheckIcon, ExclamationTriangleIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
```

Then replace each JSX usage with the corresponding icon component.

- [ ] **Step 3: Replace imports in ScanComparison.jsx**

Same pattern — replace all `lucide-react` imports with `@heroicons/react/24/outline`.

- [ ] **Step 4: Replace imports in SBOMViewer.jsx**

Same pattern. Also ensure any custom table markup uses `<DataTable>` instead.

- [ ] **Step 5: Remove lucide-react from package.json**

Edit `frontend/package.json` — remove `"lucide-react": "^0.344.0"` from dependencies.

- [ ] **Step 6: Remove node_modules and reinstall**

```bash
Remove-Item -Recurse -Force frontend\node_modules
cd frontend; npm install
```

- [ ] **Step 7: Build check**

Run: `npm run build`
Expected: Build succeeds with no errors. No `lucide-react` import errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/security/
git commit -m "refactor: replace lucide-react with heroicons in security components"
```

---

### Task 6: Remove duplicated component files (EmptyState, Layout)

**Files:**
- Delete: `frontend/src/components/ui/EmptyState.jsx`
- Delete: `frontend/src/components/ui/Layout.jsx`

- [ ] **Step 1: Verify no remaining imports from deleted files**

Search for `from "./components/ui/EmptyState"` and `from "./components/ui/Layout"` across the entire frontend:
```bash
rg "from.*components/ui/(EmptyState|Layout)"
```
Expected: No results.

- [ ] **Step 2: Check if any file imports from the deleted files with a different path**

```bash
rg "EmptyState" frontend/src --include "*.jsx"
rg "Layout" frontend/src --include "*.jsx" | rg "components/ui"
```

If any imports found, update them to import from the canonical location (`styles/components.jsx` or `layouts/UIComponents.jsx`).

- [ ] **Step 3: Delete the files**

```bash
Remove-Item -Path "frontend\src\components\ui\EmptyState.jsx" -Force
Remove-Item -Path "frontend\src\components\ui\Layout.jsx" -Force
```

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "refactor: remove duplicated EmptyState and Layout components"
```

---

### Task 7: Consolidate Dashboard stat cards to canonical StatCard

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

- [ ] **Step 1: Read current Dashboard.jsx to identify inline stat card implementations**

Find all places where stat cards are defined inline (likely using direct `div` elements with classes instead of `<StatCard>`).

- [ ] **Step 2: Replace with canonical StatCard**

Change from inline implementation like:
```jsx
<div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
  <p className="text-sm text-gray-400">Total Scans</p>
  <p className="text-2xl font-bold text-white mt-1">{totalScans}</p>
</div>
```
To:
```jsx
import { StatCard } from "../styles/components";
// ...
<StatCard title="Total Scans" value={totalScans} icon={<ShieldCheckIcon className="h-6 w-6" />} />
```

- [ ] **Step 3: Ensure proper import**

Add `import { StatCard } from "../styles/components";` at the top of the file.

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx
git commit -m "refactor: consolidate Dashboard stat cards to canonical StatCard"
```

---

### Task 8: Consolidate Analytics page stat cards and chart containers

**Files:**
- Modify: `frontend/src/pages/Analytics.jsx`

- [ ] **Step 1: Replace inline stat cards with StatCard**

Same pattern as Task 7 — find all inline `<div className="bg-gray-800/50...">` stat card patterns and replace with `<StatCard>`.

- [ ] **Step 2: Wrap Recharts components in Card containers**

Each chart section like:
```jsx
<div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
  <h3 className="text-lg font-semibold text-white">Vulnerabilities Over Time</h3>
  <LineChart ... />
</div>
```
Becomes:
```jsx
<Card>
  <CardHeader><CardTitle>Vulnerabilities Over Time</CardTitle></CardHeader>
  <CardContent>
    <LineChart ... />
  </CardContent>
</Card>
```

- [ ] **Step 3: Add EmptyState for zero-data scenarios**

Wrap chart sections with conditional:
```jsx
{chartData?.length > 0 ? (
  <Card><LineChart data={chartData} /></Card>
) : (
  <EmptyState icon={<ChartBarIcon className="h-12 w-12" />} title="No data yet" description="Analytics will appear once scans are run." />
)}
```

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Analytics.jsx
git commit -m "refactor: consolidate Analytics page to canonical components"
```

---

### Task 9: Consolidate AdminDashboard stat cards and hardcoded colors

**Files:**
- Modify: `frontend/src/pages/AdminDashboard.jsx`

- [ ] **Step 1: Replace inline admin stat cards with StatCard**

Replace all inline card implementations with `<StatCard>` canonical component.

- [ ] **Step 2: Replace hardcoded colors**

Search for patterns like `bg-[#1a1a2e]`, `#16213e`, or any other literal hex colors. Replace with Tailwind theme classes like `bg-gray-900`, `bg-gray-800`, etc.

Specific patterns to find and replace:
- `bg-[#1a1a2e]` → `bg-gray-900`
- `text-[#e0e0e0]` → `text-gray-200`
- `border-[#333]` → `border-gray-700`

- [ ] **Step 3: Standardize loading state**

If the page uses a custom loading spinner, replace with `<Skeleton variant="card" />` grid.

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/AdminDashboard.jsx
git commit -m "refactor: consolidate AdminDashboard to canonical components"
```

---

### Task 10: Consolidate Reports page tabs, badges, and code blocks

**Files:**
- Modify: `frontend/src/pages/Reports.jsx`

- [ ] **Step 1: Ensure tabs use canonical Tabs component**

Find any inline tab navigation and replace with `<Tabs tabs={...} activeTab={tab} onChange={setTab} />`.

- [ ] **Step 2: Replace severity badge spans with SeverityBadge**

Find patterns like:
```jsx
<span className="bg-red-900/70 text-red-200 text-xs rounded-full px-2 py-0.5">CRITICAL</span>
```
Replace with:
```jsx
<SeverityBadge severity="critical" />
```

- [ ] **Step 3: Replace inline code blocks with Code component**

Find `<pre><code>...</code></pre>` patterns and replace with `<Code block>...</Code>`.

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Reports.jsx
git commit -m "refactor: consolidate Reports page to canonical components"
```

---

### Task 11: Consolidate auth forms — inputs, buttons, loading states

**Files:**
- Modify: `frontend/src/components/auth/LoginForm.jsx`
- Modify: `frontend/src/components/auth/RegisterForm.jsx`
- Modify: `frontend/src/components/auth/ForgotPasswordForm.jsx`
- Modify: `frontend/src/components/auth/ResetPasswordForm.jsx`

- [ ] **Step 1: Replace all raw `<input>` elements with `<Input>`**

For each auth form file:
- Replace `<input className="...rounded-lg border bg-gray-800..."/>` with `<Input variant={error ? "error" : "default"} ... />`
- Wrap inputs in `<FormGroup>` with `<FormLabel required>` and `<FormError>`
- Ensure all inputs show error states consistently

- [ ] **Step 2: Replace all raw `<button>` elements with `<Button>`**

- Replace `<button className="...btn-primary...">` with `<Button variant="primary" size="lg" isLoading={isSubmitting}>`
- Add `loadingText` prop if desired

- [ ] **Step 3: Unify loading states**

- Submit buttons: `<Button isLoading={isSubmitting}>`
- Initial page load: wrap form in conditional, show `<Skeleton variant="card" />` while loading
- Ensure no `<button disabled>` without the Button component's disabled+loading handling

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/auth/
git commit -m "refactor: consolidate auth forms to canonical components"
```

---

### Task 12: Consolidate Settings, Projects, Compliance, Users pages

**Files:**
- Modify: `frontend/src/components/settings/Settings.jsx`
- Modify: `frontend/src/components/projects/ProjectManagement.jsx`
- Modify: `frontend/src/components/projects/ProjectList.jsx`
- Modify: `frontend/src/components/projects/ProjectDetails.jsx`
- Modify: `frontend/src/components/compliance/AdvancedCompliance.jsx`
- Modify: `frontend/src/components/compliance/DataRetentionPolicies.jsx`
- Modify: `frontend/src/components/users/UserManagement.jsx`
- Modify: `frontend/src/components/users/AuditLogs.jsx`

- [ ] **Step 1: Replace all tables with DataTable**

For each file, find patterns like:
```jsx
<table className="min-w-full divide-y divide-gray-700">
  <thead className="bg-gray-800/50">...
```
Replace with:
```jsx
<DataTable columns={[...]} data={data} />
```

- [ ] **Step 2: Replace all inline empty states with EmptyState**

Find patterns like:
```jsx
{data.length === 0 && (
  <div className="text-center py-12 text-gray-500">No items found</div>
)}
```
Replace with:
```jsx
<EmptyState icon={<Icon />} title="No items" description="No items found. Create one to get started." action={<Button>Create</Button>} />
```

- [ ] **Step 3: Replace all inline buttons with Button**

Any `<button>` that isn't using the canonical `<Button>` component.

- [ ] **Step 4: Replace all inline modals with Modal**

Any full-screen overlay with a dialog box pattern should use `<Modal>`.

- [ ] **Step 5: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/settings/ frontend/src/components/projects/ frontend/src/components/compliance/ frontend/src/components/users/
git commit -m "refactor: consolidate Settings, Projects, Compliance, Users to canonical components"
```

---

### Task 13: Standardize marketing pages containers and typography

**Files:**
- Modify: `frontend/src/components/marketing/LandingPage.jsx`
- Modify: `frontend/src/components/marketing/AboutPage.jsx`
- Modify: `frontend/src/components/marketing/DocumentationPage.jsx`
- Modify: `frontend/src/components/marketing/PrivacyPolicy.jsx`
- Modify: `frontend/src/components/marketing/TermsOfService.jsx`
- Modify: `frontend/src/components/marketing/DataPolicy.jsx`

- [ ] **Step 1: Apply consistent page container**

Each marketing page should wrap content in:
```jsx
<main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  ...
</main>
```

- [ ] **Step 2: Standardize heading hierarchy**

- `<h1>` → `className="text-2xl lg:text-3xl font-bold text-white"` (page-title token)
- `<h2>` → `className="text-xl font-semibold text-white"` (section-title token)
- `<h3>` → `className="text-lg font-semibold text-white"` (card-title token)

- [ ] **Step 3: Apply glass-card pattern consistently**

For info/section cards, use the existing glass-card pattern:
```jsx
<div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
```

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/marketing/
git commit -m "refactor: standardize marketing pages containers and typography"
```

---

### Task 14: Final verification

**Files:**
- Run across: entire frontend

- [ ] **Step 1: Verification checklist — no hardcoded colors**

```bash
rg "#[0-9a-fA-F]{6}" frontend/src --include "*.jsx" --include "*.js" --include "*.css"
```
Review any results. Legitimate exceptions: Recharts series colors, chart tooltips. Reject: structural/border/background colors.

- [ ] **Step 2: Verification checklist — no lucide-react imports**

```bash
rg "from \"lucide-react\"" frontend/src
```
Expected: No results.

- [ ] **Step 3: Verification checklist — no duplicated component files**

```bash
Test-Path -Path "frontend\src\components\ui\EmptyState.jsx"
Test-Path -Path "frontend\src\components\ui\Layout.jsx"
```
Expected: Both return False.

- [ ] **Step 4: Build check**

Run: `npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 5: Lint check**

Run: `npm run lint`
Expected: No new lint errors on changed files.

- [ ] **Step 6: Add skip-to-content link**

In `frontend/src/index.html`, add after `<body>`:
```html
<a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg">
  Skip to main content
</a>
```

And ensure the main content container has `id="main-content"`.

- [ ] **Step 7: Commit all remaining changes**

```bash
git add frontend/
git commit -m "chore: final UI/UX consistency verification and skip-to-content link"
```

---

## Self-Review Checklist

- [ ] **Spec coverage**: Every requirement from the design spec has at least one task. Foundation (Task 1-3), ARIA (Task 4), lucide-react removal (Task 5), file deletion (Task 6), page migrations (Tasks 7-13), verification (Task 14).
- [ ] **Placeholder scan**: No TBD, TODO, "implement later", or vague steps. Every step has exact code, exact file paths, or exact commands.
- [ ] **Type/prop consistency**: `StatCard` accepts `title`, `value`, `change`, `changeType`, `icon` — consistent across all tasks. `Button` accepts `variant`, `size`, `isLoading`, `leftIcon`, `rightIcon` — consistent. `EmptyState` accepts `icon`, `title`, `description`, `action` — consistent.
- [ ] **No gaps**: Every file listed in spec Appendix B has a corresponding task.
