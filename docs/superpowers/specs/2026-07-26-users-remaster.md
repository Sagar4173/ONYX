# Users & Audit Logs Remaster — Design Spec

## Goal
Remaster the User Management page (UserManagement + 6 sub-components) and Audit Logs page (AuditLogs + 3 sub-components) with ParticleBackground ambient layer, framer-motion staggered animations, animated tab indicators, MetricCard replacements, glassmorphism elevation, and unified cyan/violet theme.

## Architecture
Two orchestrators — `UserManagement.jsx` (tabbed: Users, Statistics, Security, Settings) and `AuditLogs.jsx` (paginated log viewer). Shared helpers remain unmodified (pure utility functions).

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, @tanstack/react-query
**Zero new npm dependencies.**

## File Changes (11 files)

### `UserManagement.jsx` (REWRITE)
- `ParticleBackground` ambient layer
- Replace inline tab buttons with `motion.div` `layoutId="user-tab"` spring indicator
- Tab content wrapped in `motion.div` with `x: 8 → 0` fade slide-in
- Sticky tabs row

### `UserTable.jsx` (ENHANCE)
- Wrap table body rows with `motion.tr` stagger (`staggerChildren: 0.03`)
- Each row: `x: -10 → 0` entry
- Glassmorphism table container (current: flat `bg-gray-900/50`)
- Enhanced checkbox with custom styled `input[type="checkbox"]`
- Action buttons with hover tooltip effects

### `UserFilters.jsx` (ENHANCE)
- Stagger entry for filter section
- Pill-style role/status buttons instead of selects (like Analytics SEVERITY_PILLS)
- Glassmorphism container (already uses `GlassCard`)
- Bulk actions bar with framer-motion presence animation

### `UserModal.jsx` (ENHANCE)
- Glassmorphism modal backdrop + container
- Animated tab indicator `layoutId="modal-tab"`
- Tab content fade slide-in
- Sessions/tokens/activity items with stagger `x: -5` entry
- Enhanced grid info layout with icons

### `UserStatsTab.jsx` (ENHANCE)
- Replace `StatCard` with `MetricCard` from projects
- Role distribution with animated horizontal bars (reusing SeverityDistribution pattern)
- Stagger entry for stat cards

### `UserSecurityTab.jsx` (ENHANCE)
- Replace `StatCard` with `MetricCard`
- Enhanced security overview with icon-accented data points
- Stagger entry

### `UserSettingsTab.jsx` (ENHANCE)
- Stagger entry for setting items
- Glassmorphism items with accent left border
- Configure buttons consistent gradient styling

### `AuditLogs.jsx` (ENHANCE)
- `ParticleBackground` ambient layer
- Unified cyan/violet gradient for export button (replaces purple/pink)
- Framer-motion entry

### `AuditTable.jsx` (ENHANCE)
- Unified cyan/violet theme (replaces purple everywhere)
- Framer-motion expanded row with `layout` animation
- Loading state with branded spinner
- Glassmorphism table container

### `AuditFilters.jsx` (ENHANCE)
- Unified cyan/violet theme (replaces purple)
- Glassmorphism filter panel
- Stagger for filter sections

### `AuditPagination.jsx` (ENHANCE)
- Glassmorphism border
- Enhanced disabled button styling
- Framer-motion page button hover

## Data Flow
```
UserManagement.jsx
  ├── ParticleBackground
  ├── Tab bar (Users / Statistics / Security / Settings)
  ├── [tab=users] UserFilters + UserTable + UserModal
  ├── [tab=statistics] UserStatsTab
  ├── [tab=security] UserSecurityTab
  └── [tab=settings] UserSettingsTab

AuditLogs.jsx
  ├── ParticleBackground
  ├── AuditFilters
  └── AuditTable + AuditPagination
```

## Constraints
- Zero new npm dependencies
- All visualizations use CSS or framer-motion only
- ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- `npx eslint src/` must pass with 0 errors, 0 warnings
- No changes to data fetching logic, helpers, or API interfaces
