### Task 5: Remove lucide-react and replace all icons in security components

**Background:** lucide-react is imported in 3 security component files but NOT declared in package.json and NOT installed. This creates a dual-icon-library problem with the rest of the app using `@heroicons/react`.

**Files to modify:**
- `frontend/src/components/security/SecurityTrendsDashboard.jsx`
- `frontend/src/components/security/SBOMViewer.jsx`
- `frontend/src/components/security/ScanComparison.jsx`

**Files to NOT delete:** The security component files themselves — only the imports change.

**Icon mapping (lucide-react → @heroicons/react/24/outline):**

| lucide-react | Heroicons | Context in app |
|---|---|---|
| `AlertTriangle` | `ExclamationTriangleIcon` | Warnings/alerts |
| `ArrowDown` | `ArrowDownIcon` | Directional |
| `ArrowRight` | `ArrowRightIcon` | Navigation/linking |
| `ArrowUp` | `ArrowUpIcon` | Directional |
| `ArrowUpDown` | `ArrowsUpDownIcon` | Sort/compare |
| `BarChart3` | `ChartBarIcon` | Charts/metrics |
| `Calendar` | `CalendarIcon` | Dates |
| `CheckCircle` | `CheckCircleIcon` | Success/passed |
| `ChevronDown` | `ChevronDownIcon` | Expand/collapse |
| `ChevronRight` | `ChevronRightIcon` | Expand/collapse |
| `Clock` | `ClockIcon` | Time/duration |
| `Copy` | `ClipboardIcon` | Copy to clipboard |
| `Download` | `ArrowDownTrayIcon` | Export/download |
| `ExternalLink` | `ArrowTopRightOnSquareIcon` | External links |
| `FileJson` | `CodeBracketIcon` | JSON/code files |
| `FileText` | `DocumentTextIcon` | Documents/reports |
| `Filter` | `FunnelIcon` | Filtering |
| `GitBranch` | `ArrowRightLeftIcon` | Branch comparison |
| `Info` | `InformationCircleIcon` | Info tooltips |
| `Lock` | `LockClosedIcon` | Security/locked |
| `Minus` | `MinusIcon` | Neutral/no change |
| `Package` | `CubeIcon` | Package/SBOM |
| `RefreshCw` | `ArrowPathIcon` | Refresh/loading |
| `Search` | `MagnifyingGlassIcon` | Search |
| `Shield` | `ShieldCheckIcon` | Security (this is a security platform — check mark is appropriate) |
| `Target` | `ViewfinderCircleIcon` | Scan target/focus |
| `TrendingDown` | `ArrowTrendingDownIcon` | Decreasing trend |
| `TrendingUp` | `ArrowTrendingUpIcon` | Increasing trend |
| `XCircle` | `XCircleIcon` | Failure/error |
| `Activity` | `ChartBarSquareIcon` | Activity metrics |

- [ ] **Step 1: Replace icons in SecurityTrendsDashboard.jsx**

Replace the lucide-react import block with Heroicons equivalents. Update all JSX tag usage. Remove unused imports.

- [ ] **Step 2: Replace icons in SBOMViewer.jsx**

Same pattern. Note: `Filter` is imported but unused in this file — remove it.

- [ ] **Step 3: Replace icons in ScanComparison.jsx**

Same pattern. Note: `Clock` is imported but unused in this file — remove it.

- [ ] **Step 4: Build check**

Run: `cd frontend; npm run build`
Expected: Build succeeds with no lucide-react related errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/security/
git commit -m "refactor: replace lucide-react with heroicons in security components"
```
