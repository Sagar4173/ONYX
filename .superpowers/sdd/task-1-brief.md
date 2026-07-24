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

- [ ] **Step 4: Keep only these CSS-only utilities that have no JS counterpart**

Keep:
- `.glass` and `.glass-light` — these are global utility classes
- `live-pulse`, `scanning-pulse` — status indicators
- `status-dot`, `status-success`, `status-warning`, `status-error`, `status-info` — status indicators
- `skeleton-card` — used in global context
- `btn-primary`, `btn-secondary`, `btn-danger` — global button styles
- `card`, `card-hover`, `card-glow` — global card styles
- `progress-bar`, `progress-fill` — global progress styles
- Loading states: `.skeleton`, `.loading-spinner`
- Interactive: `.interactive`
- Tooltip: `.tooltip` (CSS-only tooltip)
- Scroll: `.scroll-smooth`, `.hide-scrollbar`
- Focus: `.focus-ring`
- All mobile/tablet responsive utilities
- Print styles
- Reduced motion
- Page transition: `.page-enter`
- Gradient text: `.gradient-text`

Remove only these clearly duplicated classes:
- `.animate-fade-in-up` — duplicate of tailwind `animate-fade-in-up`
- `.animate-slide-in-left`, `.animate-scale-in`, `.animate-shimmer`, `.animate-glow`, `.animate-float` — duplicates
- `.animate-stagger-1` through `.animate-stagger-8` — not used anywhere, duplicate concept
- `.animate-fadeIn`, `.animate-bounce-subtle`, `.animate-pulse-subtle` — duplicates
- All duplicate keyframes

- [ ] **Step 5: Verify no breakage**

Run: `cd frontend; npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/index.css
git commit -m "refactor: remove duplicate animations and CSS vars from index.css"
```
