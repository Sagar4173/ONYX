# Users & Audit Logs Remaster — Implementation Plan

**Goal:** Remaster UserManagement + AuditLogs pages with particles, animated tabs, stagger, MetricCard, glassmorphism, unified theme.

**Architecture:** 11 files modified in-place. Two orchestrators + 9 sub-components. Helpers unchanged.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, @tanstack/react-query

## Global Constraints
- Zero new npm dependencies
- ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- `npx eslint src/` must pass with 0 errors, 0 warnings

---

### Task 1: UserManagement.jsx — Particles + Animated Tabs

**Files:** `frontend/src/components/users/UserManagement.jsx`

Replace inline tab buttons with `layoutId="user-tab"` spring indicator, add `ParticleBackground`, wrap tab content in `motion.div` slide-in, remove `StatCard` import (no longer needed inline).

### Task 2: UserTable.jsx — Staggered Rows + Glassmorphism

**Files:** `frontend/src/components/users/UserTable.jsx`

Wrap `<tbody>` children with `motion.tr` stagger, glassmorphism container, enhanced checkboxes.

### Task 3: UserFilters.jsx — Pill Filters + Stagger

**Files:** `frontend/src/components/users/UserFilters.jsx`

Replace role/status selects with pill buttons, stagger entry, animated bulk actions bar.

### Task 4: UserModal.jsx — Animated Tabs + Stagger

**Files:** `frontend/src/components/users/UserModal.jsx`

Glassmorphism backdrop, `layoutId="modal-tab"`, tab content stagger, session/token/activity stagger.

### Task 5: UserStatsTab.jsx — MetricCard + Animated Bars

**Files:** `frontend/src/components/users/UserStatsTab.jsx`

Replace `StatCard` with `MetricCard`, role distribution with animated horizontal bars.

### Task 6: UserSecurityTab.jsx — MetricCard + Stagger

**Files:** `frontend/src/components/users/UserSecurityTab.jsx`

Replace `StatCard` with `MetricCard`, stagger entry, enhanced overview.

### Task 7: UserSettingsTab.jsx — Stagger + Glassmorphism

**Files:** `frontend/src/components/users/UserSettingsTab.jsx`

Stagger entry, glassmorphism items with accent borders.

### Task 8: AuditLogs.jsx — Particles + Unified Theme

**Files:** `frontend/src/components/users/AuditLogs.jsx`

`ParticleBackground`, cyan/violet export button, framer-motion entry.

### Task 9: AuditTable.jsx — Unified Theme + Framer-motion Expand

**Files:** `frontend/src/components/users/AuditTable.jsx`

Replace purple with cyan/violet, framer-motion expanded row `layout` animation, glassmorphism table.

### Task 10: AuditFilters.jsx — Unified Theme + Glassmorphism

**Files:** `frontend/src/components/users/AuditFilters.jsx`

Replace purple with cyan/violet, stagger filter sections.

### Task 11: AuditPagination.jsx — Glassmorphism + Polish

**Files:** `frontend/src/components/users/AuditPagination.jsx`

Glassmorphism border, enhanced disabled states.
