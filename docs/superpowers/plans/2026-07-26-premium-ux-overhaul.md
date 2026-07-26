# Premium UX Overhaul Implementation Plan

> **Goal:** Elevate ONYX from functional dashboard to premium security intelligence platform with fluid animations, refined interactions, and polished UX.

**Architecture:** Enhance existing components with framer-motion animations, add toast/notification system, improve empty/loading/error states, polish command palette, refine responsive behavior, and optimize performance.

**Tech Stack:** React 18, framer-motion (already installed but unused), Tailwind CSS, Recharts

---

### Phase 1: Animation & Motion

**Task 1.1: PageTransition wrapper**
- Create `src/components/common/PageTransition.jsx` using framer-motion
- Wrap routes in App.jsx with staggered fade/slide
- Files: `App.jsx`, create `PageTransition.jsx`

**Task 1.2: Animated presence for modals/dialogs**
- Add framer-motion `AnimatePresence` to Modal, ConfirmDialog
- Slide-up + fade-in for modals, scale for tooltips
- Files: `components.jsx` (Modal, ConfirmDialog, Tooltip)

**Task 1.3: Staggered list animations**
- Add `AnimatedListItem` improvements with framer-motion
- Apply to DataTable rows, project lists, findings lists
- Files: `components.jsx`, domain list components

**Task 1.4: Micro-interactions**
- Button hover scale effect (already partial), click ripple
- Card hover lift + glow
- Sidebar item active indicator animation
- Files: `components.jsx`, `Sidebar.jsx`, `classNames.js`

### Phase 2: Toast & Notification System

**Task 2.1: Toast context + component**
- Create `ToastContext.jsx`, `ToastContainer.jsx`
- Stacking toasts with auto-dismiss, types (success/error/info/warning)
- Files: create in `src/components/common/`

**Task 2.2: Integrate with auth, reports, export**
- Add toasts for login/logout, report export, settings save
- Files: `AuthContext.jsx`, `EnhancedReportDetails.jsx`, `Settings.jsx`

### Phase 3: Enhanced Command Palette

**Task 3.1: Upgrade CommandPalette**
- Fuzzy search across pages, recent items, keyboard hints
- Dark backdrop blur, smooth open/close animation
- Files: `CommandPalette.jsx`

### Phase 4: Empty/Loading/Error States

**Task 4.1: Premium EmptyState**
- Animated illustrations (SVG), helpful CTAs, contextual suggestions
- Files: `EmptyState.jsx`, `UIComponents.jsx`

**Task 4.2: Skeleton animation**
- Shimmer effect on all Skeleton variants
- Files: `Skeleton.jsx`, `index.css`

### Phase 5: Content Polish

**Task 5.1: LandingPage premium**
- Animated hero gradient, stats counters, staggered feature reveals
- Refined copy, CTA polish
- Files: `LandingPage.jsx`

**Task 5.2: AboutPage**
- Rich content, team/vision section, platform highlights
- Files: `AboutPage.jsx`

### Phase 6: Performance & Polish

**Task 6.1: Bundle analysis**
- Run `vite build --report`, identify large deps
- Lazy-load non-critical routes
- Files: `vite.config.js`

**Task 6.2: Responsive polish**
- Tablet sidebar behavior, touch targets, safe areas
- Files: `MainLayout.jsx`, `Sidebar.jsx`
