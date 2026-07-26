# ONYX Navigation Redesign — Design Spec

## Overview

Extend the premium dark-glass + neon-tech design language from the auth pages to the primary navigation layer: Sidebar, Header, and CommandPalette. Every button becomes a pill, every focus ring uses cyan, every dropdown animates smoothly, every icon container gets a gradient glow on active/selected state.

**Prerequisite:** Auth redesign (Phase 1) is complete — Button `gradientClasses` define the canonical pill gradient styling in `styles/components.jsx`.

---

## Component 1: Sidebar (`layouts/Sidebar.jsx`)

### Target State

| Property | Value |
|---|---|
| Collapse toggle shape | `rounded-full` (pill), no rect edges |
| Active indicator glow | `from-cyan-500 to-violet-600` + `shadow-cyan-500/50` |
| All focus rings | `focus-visible:ring-cyan-500 focus-visible:ring-offset-gray-900` |
| Nav items | Unchanged — icon gradient backgrounds, hover states, active background gradient all remain |

### Changes

1. **Collapse toggle button** — replace `rounded-xl` with `rounded-full`, ensure `bg-gray-800/30 hover:bg-gray-700/50` with `border-gray-700/30 hover:border-gray-600/50` and `focus-visible:ring-cyan-500`
2. **Nav-active-glow** — the active indicator div class changes from `from-blue-500 to-purple-600` and `shadow-blue-500/50` to `from-cyan-500 to-violet-600` and `shadow-cyan-500/50`
3. **NavLink focus ring** (line 124) — change `focus-visible:ring-blue-500` to `focus-visible:ring-cyan-500`
4. **Collapse toggle focus ring** (line 266) — same ring color change
5. **Mobile close button focus ring** (line 331) — same ring color change
6. **MobileMenuButton export focus ring** (line 384) — same ring color change

---

## Component 2: Header (`layouts/Header.jsx`)

### Target State

| Property | Value |
|---|---|
| Hamburger button (mobile) | Full focus-visible ring (currently missing — accessibility gap) |
| Search bar, notification, user menu buttons | `rounded-full` pill shape |
| Dropdown panels (notifications + user) | `animate-fade-in-up` on open |
| All focus rings | `focus-visible:ring-cyan-500` |

### Changes

1. **Mobile hamburger button** (line 352-358) — add `focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900`
2. **SearchBar button** (line 32-35) — replace `rounded-xl` with `rounded-full`, change ring to `ring-cyan-500`
3. **NotificationsDropdown trigger** (line 76-78) — replace `rounded-xl` with `rounded-full`, change ring to `ring-cyan-500`
4. **UserMenu trigger** (line 194-196) — replace `rounded-xl` with `rounded-full`, change ring to `ring-cyan-500`
5. **Notify dropdown panel** (line 97-99) — add `animate-fade-in-up` to the container div
6. **UserMenu dropdown panel** (line 241-243) — add `animate-fade-in-up` to the container div
7. **Dropdown glow** (lines 95, 239) — change `from-blue-500/10 to-purple-500/10` to `from-cyan-500/10 to-violet-500/10`
8. **Dropdown icon containers** (lines 103, 256) — change `from-blue-500 to-purple-600` to `from-cyan-500 to-violet-600`

---

## Component 3: CommandPalette (`components/common/CommandPalette.jsx`)

### Target State

| Property | Value |
|---|---|
| Mount animation | `animate-fade-in` on backdrop, `animate-fade-in-up` on container |
| Selected item background | `bg-gradient-to-r from-cyan-500/10 to-violet-500/10` |
| Selected item icon container | Gradient circle with `bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border-cyan-500/30` |
| Default icon container | `bg-gray-800/80 rounded-full` with first character |
| Dead code | `actionIcon()` function removed |
| Empty state | Improved message |
| Loading state | Skeleton items while projects load |

### Changes

1. **Backdrop** (line 172-174) — add `animate-fade-in`
2. **Container div** (line 176) — add `animate-fade-in-up`
3. **Remove `actionIcon` function** (lines 21-33) — dead code referencing Font Awesome classes never rendered
4. **Selected item row** (line 220-223) — change `bg-blue-600/20 text-blue-400` to `bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-cyan-300`
5. **Icon container** (line 225) — change `rounded-lg bg-gray-800/80` to `rounded-full bg-gray-800/80`
6. **Selected icon container** — change `bg-gray-800/80` to `bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/30`
7. **Empty state message** (line 199) — change to `No matching pages or projects`
8. **Loading state** — add skeleton placeholder items rendered when `projectsData` is undefined and query is enabled
9. **ESC indicator** (line 188) — change from `kbd` to semantic element, add proper aria

---

## Files Modified

| File | Changes |
|---|---|
| `layouts/Sidebar.jsx` | Collapse toggle shape + focus rings + active indicator colors |
| `layouts/Header.jsx` | Button shapes + focus rings + dropdown animations + glow colors |
| `components/common/CommandPalette.jsx` | Animations + gradient selection + dead code removal + loading state |

---

## Verification

- `npm run build` passes after every component
- Sidebar collapse toggle is visually pill-shaped
- Sidebar active indicator uses cyan/violet glow
- All focus rings across all three components use `ring-cyan-500`
- Header's mobile hamburger button receives keyboard focus ring
- All toolbar buttons are `rounded-full`
- Both dropdowns animate on open (`animate-fade-in-up`)
- CommandPalette fades in, selected items show gradient highlight
- CommandPalette icon containers are circular with gradient on selection
- No Font Awesome dead code remains
