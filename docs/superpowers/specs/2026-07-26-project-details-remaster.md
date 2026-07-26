# ProjectDetails Remaster — Design Spec

**Date**: 2026-07-26
**Status**: Approved Design
**Platform**: ONYX Security Intelligence

---

## Overview

Complete remaster of the ProjectDetails page into a security intelligence command center. Combines layout restructuring (split-pane) with premium visual treatments (3D elements, canvas visualizations, circuit-board animations) and new capabilities (activity timeline, scan comparison, live console, functional settings).

The remaster spans 9 component files across `src/components/projects/`.

---

## 1. Layout Architecture

### Structure
```
┌────────────────────────────────────────────────────────────┐
│ PageHeader (gradient icon + name + status ribbon)          │
│ [Breadcrumb]                          [Start Scan] [⋮]    │
├──────────────┬────────────────────────────────────────────┤
│ LEFT PANEL   │ MAIN CONTENT AREA (scrollable)             │
│ 300px fixed  │                                            │
│ glass card   │  1. Scan Pipeline (circuit board)          │
│              │     [if scan active]                       │
│ Project      │  2. Metrics Dashboard (4 animated cards)   │
│ Snapshot     │     with spring counters + sparklines       │
│  Status      │  3. Tab Navigation                         │
│  Priority    │     Overview | Scans | Settings             │
│  Category    │  4. Tab Content Panel                      │
│  Tags        │                                            │
│              │                                            │
│ Security     │                                            │
│ Score Globe  │                                            │
│ (CSS 3D)     │                                            │
│              │                                            │
│ Repository   │                                            │
│ URL • Branch │                                            │
│              │                                            │
│ Scanners     │                                            │
│ (badges)     │                                            │
│              │                                            │
│ Quick        │                                            │
│ Actions      │                                            │
└──────────────┴────────────────────────────────────────────┘
```

### Key Decisions
- Left panel: `w-[300px]` fixed, glass card (`backdrop-blur-xl bg-gray-800/40`), border-right separator, sticky on scroll
- Main area: `flex-1` with vertical overflow, max-w remaining
- Ambient particle background: CSS-only (pseudo-element box-shadows, no canvas library)
- All sections: framer-motion staggered entrance with spring physics

### Component Tree
```
PageContainer
  PageHeader (enhanced with status ribbon)
  div.flex (main layout)
    ProjectSidebar (new)
      ProjectSnapshotBlock
        StatusBadge, PriorityBadge, CategoryBadge, TagPills
      SecurityScoreGlobe (CSS 3D sphere + orbiting particles)
      RepositoryBlock
        RepoURL (with copy), BranchBadge
      ScannerBadges
      QuickActions
        EditButton, DeleteButton, SettingsLink
    div.flex-1 (main content)
      ScanPipeline (if scan active)
        CircuitBoard (SVG nodes + tracer lines)
        LiveFindingsCounter (odometer digits)
        LiveConsole (collapsible terminal)
      MetricsDashboard
        MetricCard × 4 (spring counter + sparkline)
      TabBar (with animated sliding indicator)
      AnimatePresence
        OverviewTab
          SecurityRadar (canvas)
          VulnerabilityMatrix (grid)
          ActivityTimeline
          ProjectInfoCollapsible
          DependenciesSummary
        ScanHistoryTab
          TrendSparkline
          ScanCard × N (depth cards)
          CompareMode (split-pane overlay)
        SettingsTab
          GeneralPanel (inline edit)
          RepositoryPanel
          ScannersPanel
          ScanConfigPanel
          DangerZonePanel
  EditProjectModal (tabbed, live preview)
  DeleteProjectModal (animated, type-to-confirm)
```

---

## 2. Ambient Particle Background

### Implementation
- CSS-only particle system using `box-shadow` on a `::before` pseudo-element
- 50+ particles defined as comma-separated box-shadow values with randomized positions
- Keyframe animation: subtle Y-drift + opacity pulse
- Scan-active state: faster drift, additional particles revealed via class toggle
- Z-index: behind all content, above page background

### Visual
- Particles: 2px diameter, rgba(6, 182, 212, 0.15) base color
- Slow vertical drift (10s cycle), gentle horizontal sway (15s cycle)
- During active scan: speed increases 2×, additional violet particles appear (rgba(139, 92, 246, 0.1))

---

## 3. Circuit Board Pipeline

### SVG Architecture
- Horizontal layout with 7 stage nodes
- Nodes connected by right-angle trace lines (PCB aesthetic)
- ViewBox: `0 0 900 120` for responsive scaling

### Node Design
- Hexagonal chip shape (SVG polygon)
- Inner: stage icon (scanner type) + label text
- Size: ~90×60px each
- Spacing: equally distributed with 30px gaps

### Node States
| State | Visual |
|-------|--------|
| Pending | `fill-gray-800 stroke-gray-700`, dashed border, text gray-500 |
| Active | `fill-cyan-900/50 stroke-cyan-400`, glow filter, pulsing ring, label white |
| Completed | `fill-green-900/50 stroke-green-400`, checkmark overlay, scale-bounce on enter |
| Failed | `fill-red-900/50 stroke-red-400`, shake animation on enter |

### Tracer Lines
- SVG path with `stroke-dasharray="4 4"` and `stroke-linecap="round"`
- Active tracer: `stroke-cyan-400` with animated `stroke-dashoffset` (electron flow)
- Completed tracer: `stroke-green-500` solid
- Electrons: small circles animated via `offset-path` or JS-updated position

### Findings Counter
- Individual digit spans, each with framer-motion `AnimatePresence`
- Digits roll up/down on count change (odometer-style)
- Color: severity-graded (red for critical count, etc.)

### Live Console
- Collapsible panel: `max-h-0` → `max-h-96` with framer-motion `animate`
- Content: `<pre><code>` styled as VS Code terminal
- Background: `bg-gray-950` with `caret-color: cyan`
- Log lines: accumulated in state array, auto-scroll to bottom via `useEffect` + `scrollIntoView`
- Format: `[TIMESTAMP] [LEVEL] message` — level colored (INFO=cyan, WARN=yellow, ERROR=red, DEBUG=gray)
- Fetch: new lines fetched each poll cycle (diff-based or offset-based)

---

## 4. Security Score Globe

### CSS 3D Architecture
- Container: `perspective: 600px`, `transform-style: preserve-3d`
- Sphere: concentric ellipses (latitude lines) and arcs (longitude lines) as absolutely positioned divs
- Each line: `border: 1px solid rgba(6, 182, 212, 0.3)`, `border-radius: 50%`
- Rotation: framer-motion `useAnimation` with `rotateX` and `rotateY` continuous

### Score Display
- Center: large number with `bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 bg-clip-text text-transparent`
- Ring around number: conic gradient matching score percentage, with animated `conic-gradient` rotation

### Color States
| Score | Globe Color | Pulse |
|-------|-------------|-------|
| ≥80 | `rgba(34, 197, 94, 0.4)` — green | Slow pulse (3s) |
| 60-79 | `rgba(234, 179, 8, 0.4)` — yellow | Medium pulse (2s) |
| <60 | `rgba(239, 68, 68, 0.4)` — red | Fast pulse (1s) |

### Orbiting Particles
- 4-8 dots at varying orbit radii (60-100px)
- Each dot: 4px diameter, severity-colored
- Orbit animation: CSS `transform-origin` + `rotate` keyframe, each at different speed/delay
- Active scan: additional particles, 2× orbit speed

---

## 5. Metrics Dashboard

### Card Design
- `bg-gray-800/40 backdrop-blur-sm` base
- `box-shadow: 0 20px 60px -15px rgba(0,0,0,0.5)` for depth
- `border: 1px solid rgba(75, 85, 99, 0.3)`
- Hover: `transform: translateY(-2px)`, shadow intensifies
- Icon container: gradient background with subtle glow pulse

### Counter Animation
```jsx
const count = useSpring(0, { damping: 20, stiffness: 100 })
const display = useTransform(count, (v) => Math.round(v))
// useEffect to update count.set(targetValue) on data change
```

### Sparkline
- Inline SVG: 80×24px viewBox
- 10 data points as polyline
- Stroke: color-matching card theme (cyan, red, green, purple)
- Fill: gradient below line with opacity 0.1
- No axes, no labels — pure trend indicator

### Card Layout
| Card | Icon | Sparkline Color |
|------|------|-----------------|
| Total Scans | ChartBarIcon (cyan) | cyan-400 |
| Vulnerabilities | ExclamationTriangleIcon (red) | red-400 |
| Security Score | ShieldCheckIcon (green) | green-400 |
| Last Scan | ClockIcon (purple) | purple-400 |

---

## 6. Overview Tab

### 6a. Security Radar (Canvas)
- HTML5 Canvas, 280×280px
- 6 axes: SAST, Secrets, Dependencies, Container, IaC, DAST
- Each axis: line from center to edge, labeled at endpoint
- Data polygon: filled with gradient, stroke on edges
- Sweep line: rotating radial gradient line with trail (fading opacity)
- Animation: `requestAnimationFrame` loop, sweep completes one rotation per 4s
- Legend below: severity distribution bars

### 6b. Vulnerability Matrix
- CSS Grid: auto-fill, minmax(80px, 1fr)
- Each cell: severity color intensity = `rgba(severityRGB, min(1, count/10))`
- Cell size scales with count (inline style `--cell-size: max(60px, count * 8px)`)
- Hover: `z-index: 10`, scale(1.15), detailed tooltip overlay
- Tooltip: vulnerability name, CVE count, severity badge, fix version (if available), trend arrow
- Empty state: min-sized gray cells with "No findings" text

### 6c. Activity Timeline
- Vertical layout with left-aligned connector line
- Connector: gradient line (top cyan → bottom violet) animated with CSS
- Event nodes: circular dots on the line, severity-colored
- Event content: icon + relative timestamp + description, right of the line
- Scroll container: `max-h-96 overflow-y-auto` with custom scrollbar
- New events: animate in from bottom with `layout: true`

### 6d. Project Info Block
- Collapsible `GlassCard` with `Accordion` behavior
- Contents: status badge, priority badge, category badge, created date, tags
- Repository section: URL (clickable, with copy button), branch badge
- Compact layout: 2-column grid inside

### 6e. Dependencies Summary
- Shows if dependency scan data exists in the latest scan
- Header: total packages, vulnerable count, critical count
- Top 5 vulnerable packages: name + severity + fix version
- Link: "View Full Dependency Report →"

---

## 7. Scan History Tab

### 7a. List View
- Cards with depth styling (same as Metrics cards but horizontal)
- Layout per card: scan ID | status badge | mini severity bar | duration | branch | time
- Mini severity bar: inline 4-color stacked bar (2px height, full width) — shows distribution visually
- Hover: subtle lift, reveals action buttons (View Report, Compare checkbox, Re-run)
- Entrance: staggered spring animation from bottom

### 7b. Timeline View (Alternative)
- Cards arranged vertically on a central timeline
- Alternating left/right placement (odd left, even right)
- 3D perspective: `rotateX(2deg)` and `rotateY(var(--side-deg))` with depth shadow
- Connector dots on the center line, colored by scan status
- Entrance: cards slide in from respective side

### 7c. Compare Mode
- Toggle: checkbox "Compare" on each scan card (max 2 selected)
- When 2 selected: "Compare" button appears in tab header
- Overlay slides down: split-pane with scan A (left) vs scan B (right)
- Each pane: severity breakdown as bars, findings list with diff indicators
- Diff: green highlight = new in B, red = fixed since A, yellow = count changed
- Close button collapses overlay

### 7d. Trend Sparkline
- Full-width SVG chart (100% × 80px)
- X-axis: scan dates, Y-axis: vulnerability count
- Line + gradient fill
- Optional: severity breakdown as stacked area

---

## 8. Settings Tab

### Panels
Each panel is a `GlassCard` with:
- Title + description header
- Inline form controls
- Discrete Save button (visible only after modification)

### Panels List
| Panel | Fields |
|-------|--------|
| General | name (text), description (textarea), category (select), priority (select), status (select) |
| Repository | URL (text), branch (text), access_token (password), Test Connection button |
| Scanners | toggle per scanner type (SAST, Secrets, Dependencies, Container, IaC, DAST) |
| Scan Config | auto_scan_on_push (toggle), fail_on_critical (toggle), timeout (range slider with number display) |
| Notifications | webhook_url (text), email_alerts (toggle) |
| Danger Zone | bordered red, collapsed by default, "Delete Project" button opens DeleteProjectModal |

### Behavior
- Each panel independently tracks dirty state
- Save button: gradient CTA `from-cyan-400 via-violet-500 to-cyan-400`
- On save: optimistic UI update, toast confirmation, invalidate queries

---

## 9. Modals

### EditProjectModal
- Header: gradient icon box + "Edit Project" title
- Tabs: Basic | Repository | Scanners | Tags
  - Each tab is a framer-motion `AnimatePresence` with crossfade
- **Basic tab**: Name, Description, Category, Priority, Status
- **Repository tab**: URL, Branch, Access Token
- **Scanners tab**: toggle grid (same SCANNER_OPTIONS) + auto-scan + fail-on-critical + timeout
- **Tags tab**: input + tag pills with remove
- Live preview: mini card in the modal showing current name + status + priority as they change
- Footer: Cancel (ghost) + Save Changes (gradient, loading state)

### DeleteProjectModal
- Danger icon container: shimmer red background with shake on mount
- Warning text: project name highlighted in red
- Consequences list: scans count, config, associations
- "Type DELETE to confirm": input with character-by-character validation
  - As user types, each matching character highlights in green
  - Delete button enables only when exact match
- Confirm button: "Delete Forever" with double-confirm step:
  - First click: button changes to "Are you sure? Click again"
  - Second click: triggers mutation
  - This prevents accidental deletion
- Loading state: "Deleting..." with spinner
- Success: toast + navigate to /projects

---

## 10. Animation & Micro-interaction System

### Page Entrance
```jsx
// Parent container
<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
  {/* Stagger children */}
  <motion.div variants={staggerContainer} initial="hidden" animate="visible">
    <motion.div variants={fadeInUp} /> {/* sidebar */}
    <motion.div variants={fadeInUp} /> {/* pipeline */}
    <motion.div variants={fadeInUp} /> {/* metrics */}
    <motion.div variants={fadeInUp} /> {/* tabs */}
  </motion.div>
</motion.div>
```

### Stagger Config
```js
const staggerContainer = { hidden: {}, visible: { transition: { staggerChildren: 0.1 } } }
const fadeInUp = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: 'spring', damping: 20, stiffness: 100 } } }
```

### Tab Switching
- `LayoutGroup` wraps tab bar + content
- `layoutId="tab-indicator"` on the active tab underline for smooth slide
- Content: `AnimatePresence mode="wait"` with crossfade

### Scan Status Transitions
- `AnimatePresence` for scan banner enter/exit
- Color morphing: `motion.div` with `animate={{ backgroundColor }}` for smooth panel color transitions
- Completion: brief scale pulse on score globe, optional CSS spark particles

### Hover Effects
- Cards: `whileHover={{ y: -2 }}` with spring
- Buttons: `whileHover={{ scale: 1.03 }}`, `whileTap={{ scale: 0.98 }}`
- Icons in metric cards: `whileHover={{ scale: 1.1, rotate: 5 }}`

### Loading States
- Skeleton loaders matching each component shape
- Shimmer animation: `animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}`
- Pulse glow on skeleton borders

---

## 11. Data Flow

### Queries (Existing, unchanged)
```js
queryKey: ["project", projectId]               // project data
queryKey: ["projectScans", projectId]          // scan history
queryKey: ["projectAnalytics", projectId]      // analytics/stats
```

### Polling (Enhanced)
- During active scan: 2s polling interval via `setInterval`
- New: diff-based log line accumulation
  - Each poll returns `{ scan_id, status, progress, current_scanner, findings: {}, logs: [...newLines], total_findings, findings_by_severity }`
  - New log lines appended to `logLines` state array
  - Progress used for pipeline + metrics animation targets

### Mutations (Existing, unchanged)
```js
startScanMutation    // POST /scans
stopScanMutation     // POST /scans/:id/stop
updateProjectMutation // PUT /projects/:id
deleteProjectMutation // DELETE /projects/:id
```

### State Additions
```js
const [logLines, setLogLines] = useState([])         // console log accumulation
const [scanProgress, setScanProgress] = useState(0)   // 0-100
const [activeScan, setActiveScan] = useState(null)    // current scan object
const [isPolling, setIsPolling] = useState(false)     // polling flag
const [scanCompleted, setScanCompleted] = useState(false)
const hasShownCompletionToast = useRef(false)
```

---

## 12. File Structure

### New/Modified Files
| File | Status | Lines (est.) |
|------|--------|-------------|
| `ProjectDetails.jsx` | Modified (orchestrator) | ~250 |
| `ProjectSidebar.jsx` | **New** | ~120 |
| `SecurityScoreGlobe.jsx` | **New** | ~180 |
| `ScanPipeline.jsx` | **New** (replaces ScanProgressBanner) | ~250 |
| `LiveConsole.jsx` | **New** | ~80 |
| `MetricsDashboard.jsx` | **New** (replaces QuickStatsCards) | ~150 |
| `MetricCard.jsx` | **New** | ~100 |
| `SecurityRadar.jsx` | **New** | ~150 |
| `VulnerabilityMatrix.jsx` | **New** | ~120 |
| `ActivityTimeline.jsx` | **New** | ~100 |
| `OverviewTab.jsx` | **New** (replaces ProjectOverviewTab) | ~80 (orchestrator) |
| `ScanHistoryTab.jsx` | Modified | ~200 |
| `SettingsTab.jsx` | Modified (was ProjectSettingsTab) | ~180 |
| `EditProjectModal.jsx` | Modified | ~220 |
| `DeleteProjectModal.jsx` | Modified | ~70 |
| `index.js` | Modified (add exports) | ~5 |

### Removed Files
| File | Replaced By |
|------|-------------|
| `ScanProgressBanner.jsx` | `ScanPipeline.jsx` + `LiveConsole.jsx` |
| `QuickStatsCards.jsx` | `MetricsDashboard.jsx` + `MetricCard.jsx` |
| `ProjectOverviewTab.jsx` | `OverviewTab.jsx` (orchestrates sub-components) |

---

## 13. Dependencies

### Existing (Already in project)
- `@tanstack/react-query` — data fetching
- `framer-motion` — animations
- `@heroicons/react` — icons
- `tailwindcss` — styling
- `react-hot-toast` — notifications
- `react-router-dom` — navigation

### No New Dependencies Required
All visualizations use native Canvas API or CSS — no Three.js, D3.js, or chart libraries needed.

---

## 14. Verification Criteria

| Check | Method |
|-------|--------|
| Linting | `npx eslint src/components/projects/` — 0 errors, 0 warnings |
| Build | `npm run build` — no errors |
| All scan states render | Manual: pending, running, completed, failed, cancelled |
| Empty states | No scans, no vulnerabilities, no activity, no dependencies |
| Loading states | Skeleton placeholders for all async data |
| Error states | Project not found, API failures, scan failures |
| Responsive | Left panel collapses on <1024px (sidebar → top bar) |
| Animation off | `prefers-reduced-motion: reduce` respected |
| Keyboard nav | All interactive elements reachable and activatable by keyboard |
