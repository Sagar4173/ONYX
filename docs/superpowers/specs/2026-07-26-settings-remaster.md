# Settings Page Remaster — Design Spec

## Goal
Remaster the Settings page and all 8 sub-components with premium visual upgrades: ParticleBackground ambient layer, framer-motion sidebar tab indicator, staggered tab content transitions, glassmorphism SettingCard with colored accent stripes, smooth Toggle animation, and enhanced status displays.

## Architecture
Single-page orchestrator (`Settings.jsx`) + 5 tab components + 2 shared components (`SettingCard`, `Toggle`) + 1 info component (`SystemInfo`). ParticleBackground as ambient backdrop. Sidebar with `layoutId` spring-animated indicator.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, @tanstack/react-query
**Zero new npm dependencies.**

## File Changes

### `frontend/src/components/settings/Settings.jsx` (REWRITE)
- Add `ParticleBackground` ambient layer
- Replace inline tab button styling with `motion.div` `layoutId="tab-indicator"` spring animation
- Wrap tab content in `motion.div` with `x: 10 → 0` slide-in and `opacity` fade on tab switch
- Sticky save button (remains visible when scrolling)
- Glassmorphism sidebar container

### `frontend/src/components/settings/SettingCard.jsx` (ENHANCE)
- Glassmorphism styling (`bg-gray-800/40 backdrop-blur-sm border`)
- Colored left accent stripe using `border-l-4` with colors per type:
  - `warning` → `border-l-yellow-500`
  - `danger` → `border-l-red-500`
  - default → `border-l-cyan-500/50`
- `whileInView={{ opacity: 1, y: 0 }}` with `viewport={{ once: true }}`

### `frontend/src/components/settings/Toggle.jsx` (ENHANCE)
- Replace CSS transition knob with `motion.div` `layout` spring for smooth knob movement
- Glassmorphism track (`bg-gray-700/50` when off, `bg-cyan-600/80` when on)
- Focus ring with `focus-visible:ring-2 focus-visible:ring-cyan-500`
- Label prop removed (unused — aria-label already present)

### `frontend/src/components/settings/SecurityTab.jsx` (ENHANCE)
- Wrapped content in `motion.div` with `staggerChildren: 0.05`
- Each SettingCard gets `variants` slide-up entry
- Select inputs get glassmorphism styling
- Password policy section uses grid layout for compactness

### `frontend/src/components/settings/NotificationTab.jsx` (ENHANCE)
- Stagger entry same pattern
- Group items implicitly (no structural change to data)

### `frontend/src/components/settings/ScanningTab.jsx` (ENHANCE)
- Stagger entry
- Scanner toggle list with icons per scanner type
  - sast → CodeBracketIcon
  - secrets → EyeIcon
  - container → CubeIcon
  - infrastructure → ServerIcon

### `frontend/src/components/settings/ApiTab.jsx` (ENHANCE)
- Stagger entry
- Add copy-to-clipboard button for API key
- Enhanced input glassmorphism

### `frontend/src/components/settings/SystemTab.jsx` (ENHANCE)
- Stagger entry
- Enhanced system info display

### `frontend/src/components/settings/SystemInfo.jsx` (ENHANCE)
- Replace text status with LiveIndicator-style dots
- Glassmorphism info container
- Scanner active/total with mini bar
- Version/build in monospace font

## Data Flow

```
Settings.jsx (useState for settings)
  ├── ParticleBackground
  ├── Sidebar (tabs + Save button)
  └── Tab content (SecurityTab / NotificationTab / ScanningTab / ApiTab / SystemTab)
       └── SettingCard (shared wrapper)
            ├── Toggle (shared control)
            ├── select / input (inline)
            └── SystemInfo (system tab only)
```

## States

| State | Behavior |
|-------|----------|
| **Default** | All settings loaded into initial useState, component is uncontrolled-form-like |
| **Saving** | `saveSettingsMutation.isPending` disables button, shows spinner |
| **Success** | Toast "Settings saved successfully!" |
| **Error** | Toast error message from API |
| **Edge case** — API key hidden by default | EyeIcon toggle to reveal |
| **Edge case** — maintenance mode disabled for non-admin | Toggle disabled with info toast |

## Constraints
- Zero new npm dependencies
- All visualizations use CSS or framer-motion only
- ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- `npx eslint src/` must pass with 0 errors, 0 warnings
- No changes to the settings data model or save logic

## Files to Modify
- `frontend/src/components/settings/Settings.jsx`
- `frontend/src/components/settings/SettingCard.jsx`
- `frontend/src/components/settings/Toggle.jsx`
- `frontend/src/components/settings/SecurityTab.jsx`
- `frontend/src/components/settings/NotificationTab.jsx`
- `frontend/src/components/settings/ScanningTab.jsx`
- `frontend/src/components/settings/ApiTab.jsx`
- `frontend/src/components/settings/SystemTab.jsx`
- `frontend/src/components/settings/SystemInfo.jsx`
