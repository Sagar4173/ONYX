# ONYX Project Management Page — Full Redesign

## Goal

Transform the 1287-line monolithic `ProjectManagement.jsx` into a modular, maintainable, and visually cohesive set of components. Improve UX with proper pagination, bulk actions, sort controls, debounced search, list view, and loading states — all while simplifying the codebase.

---

## Architecture

### File Layout

```
frontend/src/components/projects/
├── index.js                   # Re-exports all
├── ProjectManagement.jsx      # Orchestrator (~80 lines)
├── ProjectStatsBar.jsx        # 4 analytics stat cards
├── ProjectFilters.jsx         # Search, filters, sort, view toggle
├── ProjectGrid.jsx            # Grid/list rendering, pagination, bulk actions
├── ProjectCard.jsx            # Individual project card (grid view)
├── ProjectRow.jsx             # Individual project row (list view)
├── ProjectForm.jsx            # Unified create + edit modal (useReducer)
└── ProjectDeleteDialog.jsx    # Delete confirmation dialog
```

### Component Tree

```
ProjectManagement
├── PageHeader + "New Project" CTA button
├── ProjectStatsBar
│   └── 4× StatCard (total projects, active scans, avg security score, open issues)
├── ProjectFilters
│   ├── Search input (debounced 300ms)
│   ├── Status dropdown (All / Active / Inactive / Archived)
│   ├── Category dropdown
│   ├── Priority dropdown
│   ├── Sort dropdown (Name / Created / Last Scan / Security Score)
│   ├── Grid/List toggle buttons
│   └── Active filter chips (removable)
├── ProjectGrid
│   ├── Bulk selection bar (appears when items checked)
│   ├── Transition wrapper (AnimatePresence)
│   ├── ├── ProjectCard[] (grid mode)
│   │   └── ProjectRow[]  (list mode)
│   ├── Pagination (prev / page numbers / next, per-page selector)
│   ├── Empty state (no projects, or no filter matches)
│   ├── Loading state (skeleton cards/rows)
│   └── Error state (with retry)
├── ProjectForm (modal, create or edit based on `project` prop)
└── ProjectDeleteDialog (simple confirm modal)
```

---

## Component Specifications

### ProjectManagement (orchestrator)

**Props:** none

**State owned:**
- `filters` — `{ search, status, category, priority }`
- `sort` — `{ field, direction }`
- `pagination` — `{ page, perPage }`
- `viewMode` — `"grid" | "list"`
- `selectedIds` — `Set<number>`
- `showCreateModal`, `editingProject`, `deletingProject`

**Data fetching:**
- `useQuery(["projects", filters, sort, pagination])` — paginated project list
- `useQuery(["projectAnalytics"])` — stat card data
- Mutations: create, update, delete
- On mutation success: `queryClient.invalidateQueries(["projects"])` + `["projectAnalytics"]`

**Data flow:** Passes state down, receives callbacks up. No prop drilling beyond one level — every sub-component gets exactly what it needs.

---

### ProjectStatsBar

**Props:** none

**Data:** `useQuery(["projectAnalytics"])`

**Renders:** 4 `StatCard` components in a responsive grid:
1. **Total Projects** — count, FolderIcon, gradient from-blue-500 to-cyan-500
2. **Active Scans** — currently running, PlayIcon, gradient from-violet-500 to-purple-500
3. **Avg Security Score** — percentage, ShieldCheckIcon, gradient from-emerald-500 to-green-500
4. **Open Issues** — count of critical+high, ExclamationIcon, gradient from-red-500 to-orange-500

**States:** Loading (skeleton StatCards), Error (hidden, no fatal), Success

---

### ProjectFilters

**Props:**
- `filters`, `onFilterChange`
- `sort`, `onSortChange`
- `viewMode`, `onViewModeChange`
- `loading` (boolean — disables controls during fetch)

**Behavior:**
- Search input debounced at 300ms — does not trigger API call on every keystroke
- Dropdown filters (status, category, priority) trigger immediate refetch on change
- Sort dropdown: Name, Created (newest), Last Scan, Security Score
- Grid/List toggle: two icon buttons, active state highlighted
- Active filters shown as removable chips below the search row
- "Clear all" button when 2+ filters active

**Visual:**
- Search: glass input with magnifying glass icon, `rounded-full` for premium feel
- Dropdowns: consistent `Select` component from styles/components
- Toggle: `Button` with icon-only variant

---

### ProjectGrid

**Props:**
- `projects` — array of project objects
- `viewMode` — `"grid" | "list"`
- `pagination` — `{ page, perPage, total, totalPages }`
- `onPageChange`, `onPerPageChange`
- `selectedIds`, `onSelectionChange`
- `onView`, `onEdit`, `onDelete`
- `loading`, `error`, `onRetry`

**Renders:**
- Loading: 6 skeleton cards (3 cols × 2 rows) or 5 skeleton rows
- Empty (no projects at all): EmptyState with "Create your first project" icon + CTA
- Empty (filtered): EmptyState with "No matches" + "Clear filters" button
- Error: ErrorState with retry
- Success:
  - Bulk bar (when `selectedIds.size > 0`): fixed bar showing count + "Archive Selected" + "Delete Selected" buttons
  - Grid mode: responsive grid `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4` with AnimatePresence
  - List mode: single-column card layout (wider, less vertical space)
  - Pagination bar: "Showing X-Y of Z" text, per-page select (12/24/48), prev/page numbers/next buttons

---

### ProjectCard (grid view)

**Props:** `project`, `selected`, `onSelect`, `onView`, `onEdit`, `onDelete`

**Layout:**
```
┌─────────────────────────────────────┐
│ [status accent bar - left border]    │
│  Icon │ Name                         │
│        │ Description (2 lines max)   │
│        │ repo URL (truncated)        │
│                                     │
│  ┌─────────┐  ┌───┐ ┌───┐ ┌───┐   │
│  │ Score    │  │ ●│ │ ●│ │ ●│   │
│  │   85     │  │cr│ │hi│ │me│   │
│  └─────────┘  └───┘ └───┘ └───┘   │
│                                     │
│  Tags: [react] [api] [sast]         │
│  Last scan: 2h ago                  │
│                                     │
│  [hover: Edit] [hover: Delete]      │
└─────────────────────────────────────┘
```

**Details:**
- Status accent: 3px colored left border (green=active, yellow=inactive, gray=archived)
- Score: circular ring (SVG circle, color based on value: green ≥ 80, yellow ≥ 50, red < 50)
- Severity dots: 4 tiny colored circles showing critical/high/medium/low counts
- Tags: up to 3 shown, "+N more" if overflow
- Hover: subtle lift (`-translate-y-1`), shadow increase, action buttons slide in from right
- Selected: checkbox in top-left, subtle border highlight

---

### ProjectRow (list view)

**Props:** same as ProjectCard

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ ☐ │ Icon │ Name        │ Status │ Score │ Issues │ Last Scan │ Actions │
│   │      │ Description │        │  ◎85  │ ●●○     │ 2h ago    │ [⋯]     │
└─────────────────────────────────────────────────────────────┘
```

- One row per project, columns: checkbox, icon+name+description, status badge, score ring (small), severity dots (compact), last scan relative time, dropdown actions
- Responsive: on smaller screens, collapse to card-like layout

---

### ProjectForm (unified create/edit)

**Props:**
- `isOpen`, `onClose`
- `project` — `null` for create mode, project object for edit mode
- `onSuccess`

**State:** `useReducer` with action types for each field, replaces nested `useState` spread pattern

**Form sections:**
1. **Basic Information** — name (required), category (select), priority (select), description (textarea)
2. **Repository Configuration** — URL (required), branch, access token
3. **Security Scanners** — toggle buttons for sast, secrets, dependency, container, iac
4. **Scan Configuration** — auto-scan toggle, timeout slider, fail-on-critical toggle
5. **Tags** — tag input with add/remove chips

**Differences from current:**
- Uses `useReducer` instead of multiple `useState` + spread operators
- Single component handles both create and edit (previously two files)
- Repository section shown in both modes (currently hidden in edit)
- Form sections use `fieldset` elements for accessibility
- Submit button text: "Create Project" vs "Save Changes"
- Loading state on submit button when `mutation.isPending`

---

### ProjectDeleteDialog

**Props:** `project`, `isOpen`, `onClose`, `onConfirm`

**Renders:**
- Warning icon + "Delete project `{name}`?"
- Explanation text: "This action cannot be undone. All scan data, reports, and configurations will be permanently removed."
- Cancel + Delete buttons (Delete is red/danger variant)

---

## Data Flow

```
User action → Callback → ProjectManagement (state update) → 
  → React Query refetch → Loading skeleton → New data → AnimatePresence renders new cards
```

- Filter/sort/page changes update state → query key changes → automatic refetch via `useQuery`
- Search is debounced → updates filter state after 300ms → refetch
- Mutations (create/update/delete) → invalidate `["projects"]` and `["projectAnalytics"]`
- Bulk actions → confirm dialog (for delete) → mutation per item → cache invalidation
- All loading states derived from `isLoading` / `isFetching` from React Query

---

## States Coverage

| State | Component | Handling |
|---|---|---|
| **Loading (initial)** | ProjectGrid | 6× SkeletonCard or 5× skeleton rows |
| **Loading (refetch)** | ProjectGrid | `isFetching` — subtle opacity dim on existing cards + spinner overlay |
| **Empty (no projects exist)** | ProjectGrid | EmptyState: FolderIcon + "No projects yet" + "Create your first project" button |
| **Empty (no filter matches)** | ProjectGrid | EmptyState: MagnifyingGlassIcon + "No projects match your filters" + "Clear filters" button |
| **Error (fetch failed)** | ProjectGrid | ErrorState: message + "Try Again" button calling `onRetry` (which refetches) |
| **Error (mutation failed)** | ProjectForm / ProjectManagement | `toast.error()` from mutation `onError` |
| **Bulk selection active** | ProjectGrid | Floating bar showing count + action buttons |
| **No analytics data** | ProjectStatsBar | Graceful — show dashes or 0, no error state |

---

## API Contract

No new API endpoints required. Existing `projectsAPI` methods cover all needs. The pagination query params (`page`, `per_page`, `sort_by`, `sort_order`) need to be supported by the backend.

Expected backend query params:
```
GET /projects/?search=foo&status=active&category=web&priority=high&
  page=1&per_page=24&sort_by=name&sort_order=asc
```

If backend does not support pagination/sort params, the frontend falls back to client-side pagination and sorting of the full list (existing behavior).

---

## Migration Path

1. Create new files (ProjectStatsBar, ProjectFilters, ProjectGrid, ProjectCard, ProjectRow, ProjectForm, ProjectDeleteDialog)
2. Build each component in isolation
3. Rewrite ProjectManagement.jsx to import and wire them together
4. Delete old inline components (ProjectCard, CreateProjectModal, EditProjectModal)
5. Update `components/projects/index.js` exports
6. Run lint + build
7. Manual smoke test: create, edit, delete, filter, sort, paginate, bulk select, list/grid toggle

---

## Out of Scope

- Drag-and-drop reordering
- Saved filter presets
- Project archiving as a distinct action (archive = status change, already supported)
- Export/import projects
- Multi-user collaboration features in the list view
