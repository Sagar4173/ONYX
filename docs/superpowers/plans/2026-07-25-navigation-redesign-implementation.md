# Navigation Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the premium dark-glass + neon-tech design language from the auth pages to Sidebar, Header, and CommandPalette.

**Architecture:** Targeted edits to 3 existing files — no new components, no new dependencies. Each task produces an independently verifiable result (build passes + visual inspection).

**Tech Stack:** React 18, Tailwind CSS 3, Heroicons

## Global Constraints

- Dark theme is the only theme — no light-mode fallbacks
- Every focus ring uses `focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900`
- All toolbar/utility buttons become `rounded-full` pill shape
- Dropdown panels use `animate-fade-in-up` (already defined in tailwind config)
- Active/selected states use cyan/violet gradient palette (`from-cyan-500 to-violet-600`)
- `npm run build` must pass after every task
- No new npm packages
- No breaking changes to component interfaces

---
## File Structure

| File | Task | Responsibility |
|---|---|---|
| `layouts/Sidebar.jsx` | 1 | Collapse toggle pill shape, cyan active indicator, cyan focus rings |
| `layouts/Header.jsx` | 2 | Pill toolbar buttons, dropdown animations, mobile hamburger focus ring, glow colors |
| `components/common/CommandPalette.jsx` | 3 | Mount animations, gradient selection, dead code removal, loading state |

---

### Task 1: Sidebar — pill toggle, cyan active indicator, cyan focus rings

**Files:**
- Modify: `frontend/src/layouts/Sidebar.jsx`

**Interfaces:**
- No interface changes — exact same component exports, props, and usage

- [ ] **Step 1: Update collapse toggle focus ring and shape**

Change line 266 — replace `rounded-xl` with `rounded-full` and `ring-blue-500` with `ring-cyan-500`:

```jsx
className={`
  w-full flex items-center gap-3 px-4 py-3 rounded-full
  text-gray-400 hover:text-white bg-gray-800/30 hover:bg-gray-800/50
  border border-gray-700/30 hover:border-gray-600/50
  transition-all duration-300
  focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900
  ${collapsed ? "justify-center" : ""}
`}
```

- [ ] **Step 2: Update NavLink focus ring**

Line 124 — change `ring-blue-500` to `ring-cyan-500`:

```jsx
className="group relative block focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded-xl"
```

- [ ] **Step 3: Update active indicator glow colors**

Lines 131-133 — change `from-blue-500 to-purple-600` and `shadow-blue-500/50` to `from-cyan-500 to-violet-600` and `shadow-cyan-500/50`:

```jsx
<div
  className="nav-active-glow absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full 
               bg-gradient-to-b from-cyan-500 to-violet-600 shadow-lg shadow-cyan-500/50"
/>
```

- [ ] **Step 4: Update mobile close button focus ring**

Line 331 — change `ring-blue-500` to `ring-cyan-500`:

```jsx
className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50
         hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all
         focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
```

- [ ] **Step 5: Update MobileMenuButton export focus ring**

Line 384 — change `ring-blue-500` to `ring-cyan-500`:

```jsx
className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50
         hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all
         focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
```

- [ ] **Step 6: Verify build passes**

Run: `npm run build`

Expected: Build succeeds with no errors. Previous chunk-size warning is acceptable.

---

### Task 2: Header — pill buttons, dropdown animation, mobile hamburger focus ring

**Files:**
- Modify: `frontend/src/layouts/Header.jsx`

**Interfaces:**
- No interface changes — exact same component exports, props, and usage

- [ ] **Step 1: Add focus ring to mobile hamburger button**

Line 352-358 — replace the existing className with one that includes the full focus ring:

Find:
```jsx
<button
  onClick={onMenuClick}
  className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50 
           hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all"
>
  <Bars3Icon className="w-5 h-5 lg:w-6 lg:h-6" />
</button>
```

Replace with:
```jsx
<button
  onClick={onMenuClick}
  className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50 
           hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all
           focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
>
  <Bars3Icon className="w-5 h-5 lg:w-6 lg:h-6" />
</button>
```

- [ ] **Step 2: Make SearchBar button pill-shaped + cyan ring**

Lines 32-35 — replace `rounded-xl` with `rounded-full`, change `ring-blue-500` to `ring-cyan-500`:

```jsx
className="flex items-center gap-3 px-4 py-2.5 bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 
           rounded-full text-gray-400 hover:text-white hover:border-gray-600/50 hover:bg-gray-800/70
           transition-all duration-300 group min-w-[240px]
           focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
```

- [ ] **Step 3: Make notification button pill-shaped + cyan ring**

Lines 76-78 — replace `rounded-xl` with `rounded-full`, change `ring-blue-500` to `ring-cyan-500`:

```jsx
className="relative p-2.5 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700/50 
           border border-gray-700/50 hover:border-gray-600/50 rounded-full transition-all duration-300
           focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
```

- [ ] **Step 4: Make user menu button pill-shaped + cyan ring**

Lines 194-196 — replace `rounded-xl` with `rounded-full`, change `ring-blue-500` to `ring-cyan-500`:

```jsx
className="flex items-center gap-3 p-2 rounded-full bg-gray-800/50 hover:bg-gray-700/50 
           border border-gray-700/50 hover:border-gray-600/50 transition-all duration-300
           focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
```

- [ ] **Step 5: Add fade-in-up animation to notifications dropdown**

Lines 97-99 — add `animate-fade-in-up` to the notifications dropdown panel:

```jsx
<div
  className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 
               rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up"
>
```

- [ ] **Step 6: Change notification dropdown glow color**

Line 95 — change `from-blue-500/10 to-purple-500/10` to `from-cyan-500/10 to-violet-500/10`:

```jsx
<div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-violet-500/10 rounded-2xl blur-xl" />
```

- [ ] **Step 7: Change notification header icon gradient**

Line 103 — change `from-blue-500 to-purple-600` to `from-cyan-500 to-violet-600`:

```jsx
<div className="p-2 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-600">
```

- [ ] **Step 8: Add fade-in-up animation to user menu dropdown**

Lines 241-243 — add `animate-fade-in-up`:

```jsx
<div
  className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 
               rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up"
>
```

- [ ] **Step 9: Change user dropdown glow color**

Line 239 — change `from-blue-500/10 to-purple-500/10` to `from-cyan-500/10 to-violet-500/10`:

```jsx
<div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-violet-500/10 rounded-2xl blur-xl" />
```

- [ ] **Step 10: Change user avatar gradient color**

Line 256 — change `from-blue-500 to-purple-600` to `from-cyan-500 to-violet-600`:

Plus line 211 (the user menu trigger avatar). Find both occurrences of `from-blue-500 to-purple-600` in `UserMenu` and replace with `from-cyan-500 to-violet-600`:

Line 211 (trigger avatar):
```jsx
<div
  className={`w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 
               flex items-center justify-center text-white text-sm font-semibold
               shadow-lg shadow-cyan-500/25 ${
                 user?.avatar_url ? "hidden" : ""
               }`}
>
```

Line 256 (dropdown avatar):
```jsx
<div
  className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 
               flex items-center justify-center text-white font-semibold shadow-lg"
>
```

- [ ] **Step 11: Verify build passes**

Run: `npm run build`

Expected: Build succeeds with no errors.

---

### Task 3: CommandPalette — animations, gradient selection, dead code removal, loading state

**Files:**
- Modify: `frontend/src/components/common/CommandPalette.jsx`

**Interfaces:**
- No interface changes — same props (`isOpen`, `onClose`)

- [ ] **Step 1: Remove dead `actionIcon` function**

Delete lines 21-33 (the entire `actionIcon` function):

```jsx
// DELETE this entire block:
const actionIcon = (label) => {
  const map = {
    "Go to Dashboard": "fas fa-chart-pie",
    "Go to Projects": "fas fa-folder",
    "Go to Reports": "fas fa-file-alt",
    "Go to Analytics": "fas fa-chart-line",
    "Go to Compliance": "fas fa-shield-alt",
    "Go to Users": "fas fa-users",
    "Go to Settings": "fas fa-cog",
    "Go to Admin Dashboard": "fas fa-shield-halved",
  };
  return map[label] || "fas fa-link";
};
```

- [ ] **Step 2: Add fade-in animation to backdrop**

Line 172-174 — add `animate-fade-in`:

```jsx
<div
  className="fixed inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
  onClick={onClose}
/>
```

- [ ] **Step 3: Add fade-in-up animation to container**

Line 176 — add `animate-fade-in-up`:

```jsx
<div className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up">
```

- [ ] **Step 4: Update selected item background to gradient**

Lines 219-223 — change the selected item classes:

```jsx
className={`w-full flex items-center gap-4 px-5 py-3 text-left transition-colors ${
  isSelected
    ? "bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-cyan-300"
    : "text-gray-300 hover:bg-gray-800/50"
}`}
```

- [ ] **Step 5: Update icon container shape and gradient coloring**

Line 225 — change `rounded-lg bg-gray-800/80 text-sm` to `rounded-full bg-gray-800/80 text-sm`. Also add selected-state gradient to the icon span:

```jsx
<span
  className={`flex items-center justify-center w-8 h-8 text-sm flex-shrink-0 ${
    isSelected
      ? "rounded-full bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/30"
      : "rounded-full bg-gray-800/80"
  }`}
  aria-hidden="true"
>
  {item.label.charAt(0)}
</span>
```

To make `isSelected` available inside the `categoryItems.map()`, the `flatIdx` variable already exists at line 208-210. The `isSelected` variable is already defined at line 211. The icon span needs to use it.

Replace lines 225-227:
```jsx
<span className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-800/80 text-sm flex-shrink-0" aria-hidden="true">
  {item.label.charAt(0)}
</span>
```

With:
```jsx
<span
  className={`flex items-center justify-center w-8 h-8 text-sm flex-shrink-0 ${
    isSelected
      ? "rounded-full bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/30"
      : "rounded-full bg-gray-800/80"
  }`}
  aria-hidden="true"
>
  {item.label.charAt(0)}
</span>
```

- [ ] **Step 6: Improve empty state message**

Line 199 — change message:

```jsx
<p className="text-gray-400">No matching pages or projects</p>
```

- [ ] **Step 7: Add loading state**

After the `const projects = Array.isArray(projectsData) ? projectsData : [];` line (53), add a loading indicator that shows during initial data fetch:

```jsx
const isLoading = useQuery(...).isLoading;
```

Wait — `isLoading` is available from the existing `useQuery` hook on line 43. We need to destructure it. Change line 43:

```jsx
const { data: projectsData, isLoading } = useQuery({
```

Then in the results area, between the empty state check and the results map, show skeleton items during loading:

After the `{Object.keys(grouped).length === 0 ? (` line (194), change the condition to also check for loading:

```jsx
{isLoading ? (
  <div className="px-5 py-4 space-y-3" role="status" aria-live="polite">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex items-center gap-4 animate-pulse">
        <div className="w-8 h-8 rounded-full bg-gray-800/80 flex-shrink-0" />
        <div className="flex-1 h-4 bg-gray-800/60 rounded" />
      </div>
    ))}
  </div>
) : Object.keys(grouped).length === 0 ? (
```

Replace the existing `{Object.keys(grouped).length === 0 ? (` with the loading state check above.

- [ ] **Step 8: Verify build passes**

Run: `npm run build`

Expected: Build succeeds with no errors.

---

## Verification Checklist

- [ ] `npm run build` passes
- [ ] Sidebar collapse toggle is pill-shaped (`rounded-full`)
- [ ] Sidebar active indicator uses `from-cyan-500 to-violet-600` glow
- [ ] All focus rings across Sidebar, Header use `ring-cyan-500`
- [ ] Header mobile hamburger button receives keyboard focus ring
- [ ] SearchBar, notification, user menu buttons are `rounded-full`
- [ ] Notifications and UserMenu dropdowns animate on open (`animate-fade-in-up`)
- [ ] Notification dropdown glow uses `from-cyan-500/10 to-violet-500/10`
- [ ] User avatar gradient uses `from-cyan-500 to-violet-600`
- [ ] CommandPalette backdrop fades in, container fade-in-up
- [ ] CommandPalette selected items show cyan/violet gradient
- [ ] CommandPalette icon containers are circular with gradient on selection
- [ ] No Font Awesome dead code in CommandPalette
- [ ] CommandPalette shows loading skeleton while projects load
