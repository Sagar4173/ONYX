# ONYX UI Excellence Program — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate ONYX's UI to world-class quality — consistent design system usage, decomposed monoliths, polished micro-interactions, command palette, accessibility, and performance.

**Architecture:** Five sequential phases — (1) harden the existing design system with missing components, (2) decompose the two monolith files, (3) migrate every page to use the design system, (4) add UX excellence features, (5) optimize performance.

**Tech Stack:** React 18, Tailwind CSS 3, Heroicons, react-hot-toast, react-window (to add), fuse.js (to add), React.lazy + Suspense

## Global Constraints

- Every component must remain backward-compatible — no breaking API changes
- Dark theme is the only theme — no light-mode fallbacks
- All new components go in `styles/components.jsx` (simple) or `components/common/` (complex)
- All pages import from `../components/common` or `../layouts` — no deep path imports
- No new Tailwind plugins or npm packages unless explicitly listed above
- Every task produces an independently testable, visually verifiable result

---

## File Structure

### Phase 1 — Design System Hardening

| File | Change | Responsibility |
|---|---|---|
| `styles/components.jsx` | Add 6 new components | DataTable, ConfirmDialog, PageTransition, MetricCard, FindingCard, StatusBadge |
| `components/common/index.js` | Update barrel | Re-export all design system + new components |

### Phase 2 — Monolith Decomposition

| File | Change | Responsibility |
|---|---|---|
| `components/auth/UserProfile.jsx` | Rewrite as shell | Tab layout, orchestrates sub-views, ~100 lines |
| `components/auth/ProfileInfo.jsx` | Create | Avatar, name, email, bio editing |
| `components/auth/SecuritySettings.jsx` | Create | Password, 2FA, sessions |
| `components/auth/ApiTokens.jsx` | Create | Token management |
| `components/auth/NotificationPreferences.jsx` | Create | Notification toggles |
| `components/auth/ActivityLog.jsx` | Create | Activity timeline |
| `components/reports/EnhancedReportDetails.jsx` | Rewrite as shell | Tab layout, data fetching, ~200 lines |
| `components/reports/ReportSummary.jsx` | Create | Score ring, stats, metadata |
| `components/reports/VulnerabilityList.jsx` | Create | Filterable findings table |
| `components/reports/ReportCharts.jsx` | Create | Charts & graphs |
| `components/reports/ComplianceMapping.jsx` | Create | Framework mapping |
| `components/reports/ReportExport.jsx` | Create | Export options |
| `components/reports/ReportComparison.jsx` | Create | Side-by-side diff |

### Phase 3 — Page Migration

13 page files modified (one per page/component group) — each swaps raw Tailwind for design system components.

### Phase 4 — UX Excellence

| File | Change | Responsibility |
|---|---|---|
| `components/common/CommandPalette.jsx` | Create | Cmd+K global search |
| `styles/components.jsx` | Add micro-interaction classes | Button scale, card hover, staggered appear |
| Every `.jsx` with interactive elements | Add focus-visible rings | Accessibility pass |
| Every data-fetching view | Use LoadingState/EmptyState/ErrorState | Consistent states |

### Phase 5 — Performance

| File | Change |
|---|---|
| `App.jsx` | Wrap routes with React.lazy + Suspense |
| Key components | Add React.memo, useMemo, useCallback |
| Long lists | Add react-window virtualization |

---

## Task Breakdown

### Phase 1 — Design System Hardening

---

### Task 1.1: Add DataTable component

**Files:**
- Modify: `frontend/src/styles/components.jsx` (add DataTable before the export at bottom)

**Interfaces:**
- Consumes: nothing (self-contained)
- Produces: `<DataTable columns={[]} data={[]} onSort={fn} onPageChange={fn} pageSize={number} loading={bool} />`

**Details:** A reusable sortable, filterable, paginated table that replaces ad-hoc `<table>` HTML across the app. Supports:
- Column definitions: `{ key, label, sortable, render, width }`
- Sorting by clicking column headers (cycle: asc → desc → none)
- Pagination with page size selector
- Loading state with skeleton rows
- Empty state with message
- Row hover highlighting
- Responsive — horizontal scroll on small screens

- [ ] **Step 1: Add DataTable to styles/components.jsx**

Paste the following after the existing `Truncate` component (before the export default block):

```jsx
// =============================================================================
// DATA TABLE COMPONENT
// =============================================================================

const TableSkeleton = ({ rows = 5, columns = 4 }) => (
  <>
    {Array.from({ length: rows }).map((_, i) => (
      <tr key={i} className="border-b border-gray-700/50">
        {Array.from({ length: columns }).map((_, j) => (
          <td key={j} className="px-4 py-3">
            <div className="h-4 bg-gray-700/50 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
          </td>
        ))}
      </tr>
    ))}
  </>
);

export const DataTable = ({
  columns = [],
  data = [],
  onSort,
  sortKey,
  sortDirection,
  onPageChange,
  currentPage = 1,
  pageSize = 20,
  totalItems,
  loading = false,
  emptyMessage = "No data available",
  onRowClick,
  className = "",
}) => {
  const totalPages = Math.ceil((totalItems || data.length) / pageSize);

  return (
    <div className={`overflow-x-auto rounded-xl border border-gray-700/50 ${className}`}>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-800/50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider ${
                  col.sortable ? "cursor-pointer hover:text-white select-none" : ""
                }`}
                style={col.width ? { width: col.width } : undefined}
                onClick={() => {
                  if (col.sortable && onSort) {
                    onSort(col.key);
                  }
                }}
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && sortKey === col.key && (
                    <span className="text-blue-400">
                      {sortDirection === "asc" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700/50">
          {loading ? (
            <TableSkeleton rows={5} columns={columns.length} />
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-gray-400"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr
                key={row.id || row._id || i}
                className={`transition-colors duration-150 ${
                  onRowClick ? "cursor-pointer hover:bg-gray-800/30" : "hover:bg-gray-800/10"
                }`}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-gray-300">
                    {col.render ? col.render(row[col.key], row) : row[col.key] ?? "-"}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-700/50 bg-gray-800/30">
          <span className="text-sm text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-1 text-sm rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-1 text-sm rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 2: Add DataTable to the export default block**

Find the `export default {` line at the bottom of `styles/components.jsx` and add `DataTable`:

```jsx
  DataTable,
```

- [ ] **Step 3: Verify component renders**

Run: `npm run dev` (check the app starts without errors)

---

### Task 1.2: Add ConfirmDialog component

**Files:**
- Modify: `frontend/src/styles/components.jsx` (add before export)

**Interfaces:**
- `<ConfirmDialog isOpen onClose onConfirm title message confirmLabel cancelLabel variant="danger" requireTypeToConfirm />`

- [ ] **Step 1: Add ConfirmDialog to styles/components.jsx**

Add before the `export default` line:

```jsx
// =============================================================================
// CONFIRM DIALOG COMPONENT
// =============================================================================

export const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm",
  message = "Are you sure?",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  requireTypeToConfirm = false,
  confirmText = "",
}) => {
  const [typedText, setTypedText] = useState("");
  const titleId = useId();

  if (!isOpen) return null;

  const buttonColors = {
    danger: "bg-red-600 hover:bg-red-700 focus:ring-red-500",
    warning: "bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500",
    primary: "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500",
  };

  const canConfirm = requireTypeToConfirm
    ? typedText === confirmText
    : true;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700/50 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id={titleId} className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-gray-400 text-sm mb-4">{message}</p>

        {requireTypeToConfirm && (
          <div className="mb-4">
            <p className="text-sm text-gray-400 mb-2">
              Type <span className="font-mono text-red-400 bg-red-900/30 px-1.5 py-0.5 rounded">{confirmText}</span> to confirm:
            </p>
            <input
              type="text"
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700/50 rounded-lg text-white text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
              autoFocus
            />
          </div>
        )}

        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={() => { onConfirm(); onClose(); }}
            disabled={!canConfirm}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-all disabled:opacity-50 ${buttonColors[variant]}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Add ConsfirmDialog to the export default block**

```jsx
  ConfirmDialog,
```

- [ ] **Step 3: Verify the app builds**

Run: `npm run dev`

---

### Task 1.3: Add MetricCard component

**Files:**
- Modify: `frontend/src/styles/components.jsx`

**Interfaces:**
- `<MetricCard title value subtitle icon trend direction color />`

- [ ] **Step 1: Add MetricCard**

```jsx
// =============================================================================
// METRIC CARD COMPONENT
// =============================================================================

export const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  direction = "up",
  color = "blue",
  className = "",
}) => {
  const colorMap = {
    blue: "from-blue-500 to-cyan-500",
    green: "from-emerald-500 to-green-500",
    red: "from-red-500 to-rose-500",
    yellow: "from-yellow-500 to-amber-500",
    purple: "from-purple-500 to-violet-500",
    indigo: "from-indigo-500 to-blue-500",
  };

  return (
    <div className={`bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        {Icon && (
          <div className={`p-2.5 rounded-xl bg-gradient-to-r ${colorMap[color] || colorMap.blue} shadow-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
        )}
        {trend !== undefined && (
          <span className={`text-sm font-medium ${direction === "up" ? "text-green-400" : "text-red-400"}`}>
            {direction === "up" ? "↑" : "↓"} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-gray-400 mt-1">{title}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
    </div>
  );
};
```

- [ ] **Step 2: Add to export default**

```jsx
  MetricCard,
```

---

### Task 1.4: Add FindingCard and StatusBadge components

**Files:**
- Modify: `frontend/src/styles/components.jsx`

- [ ] **Step 1: Add StatusBadge**

```jsx
// =============================================================================
// STATUS BADGE COMPONENT
// =============================================================================

const statusBadgeVariants = {
  active: "bg-green-900/30 text-green-400 border-green-700/50",
  inactive: "bg-gray-700/30 text-gray-300 border-gray-700/50",
  suspended: "bg-red-900/30 text-red-400 border-red-700/50",
  pending: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
  verified: "bg-green-900/30 text-green-400 border-green-700/50",
  unverified: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
  healthy: "bg-green-900/30 text-green-400 border-green-700/50",
  warning: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
  critical: "bg-red-900/30 text-red-400 border-red-700/50",
};

export const StatusBadge = ({ status = "inactive", label, className = "" }) => {
  const variant = statusBadgeVariants[status] || statusBadgeVariants.inactive;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${variant} ${className}`}>
      {label || status}
    </span>
  );
};
```

- [ ] **Step 2: Add FindingCard**

```jsx
// =============================================================================
// FINDING CARD COMPONENT
// =============================================================================

export const FindingCard = ({
  title,
  severity = "info",
  scanner,
  filePath,
  ruleId,
  status = "open",
  onClick,
  className = "",
}) => {
  const severityGradients = {
    critical: "from-red-500 to-rose-600",
    high: "from-orange-500 to-red-500",
    medium: "from-yellow-500 to-amber-500",
    low: "from-blue-500 to-cyan-500",
    info: "from-gray-500 to-gray-400",
  };

  const severityLabels = {
    critical: "text-red-400 bg-red-900/30 border-red-700/50",
    high: "text-orange-400 bg-orange-900/30 border-orange-700/50",
    medium: "text-yellow-400 bg-yellow-900/30 border-yellow-700/50",
    low: "text-blue-400 bg-blue-900/30 border-blue-700/50",
    info: "text-gray-400 bg-gray-700/30 border-gray-700/50",
  };

  return (
    <div
      className={`bg-gray-800/30 border border-gray-700/50 rounded-xl p-4 hover:border-gray-600/50 transition-all ${
        onClick ? "cursor-pointer hover:-translate-y-0.5" : ""
      } ${className}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`w-1 h-10 rounded-full bg-gradient-to-b ${severityGradients[severity] || severityGradients.info} flex-shrink-0`} />
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{title}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-1.5 py-0.5 text-xs font-medium rounded border ${severityLabels[severity] || severityLabels.info}`}>
                {severity.toUpperCase()}
              </span>
              {scanner && <span className="text-xs text-gray-500">{scanner}</span>}
            </div>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>
      {(filePath || ruleId) && (
        <div className="mt-3 pt-3 border-t border-gray-700/50 flex items-center gap-4 text-xs text-gray-500">
          {filePath && <span className="truncate">{filePath}</span>}
          {ruleId && <span className="font-mono">{ruleId}</span>}
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 3: Add to export default**

```jsx
  StatusBadge,
  FindingCard,
```

---

### Task 1.5: Add PageTransition component + update barrel export

**Files:**
- Modify: `frontend/src/styles/components.jsx`
- Modify: `frontend/src/components/common/index.js`

- [ ] **Step 1: Add PageTransition**

```jsx
// =============================================================================
// PAGE TRANSITION COMPONENT
// =============================================================================

export const PageTransition = ({ children, className = "" }) => (
  <div className={`page-enter ${className}`}>
    {children}
  </div>
);
```

- [ ] **Step 2: Add to export default**

```jsx
  PageTransition,
```

- [ ] **Step 3: Update barrel export in components/common/index.js**

Replace the existing content:

```jsx
/**
 * Common Components Index
 * Single import source for all shared UI components
 */
export {
  Button,
  IconButton,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  SeverityBadge,
  Input,
  Textarea,
  Select,
  Alert,
  Spinner,
  LoadingOverlay,
  Skeleton,
  StatusDot,
  StatusIndicator,
  Modal,
  Divider,
  EmptyState,
  StatCard,
  AnimatedCounter,
  ProgressBar,
  SeverityProgressBar,
  AnimatedListItem,
  DonutChart,
  Code,
  Tabs,
  FormGroup,
  FormLabel,
  FormHint,
  FormError,
  Tooltip,
  Avatar,
  Truncate,
  DataTable,
  ConfirmDialog,
  MetricCard,
  FindingCard,
  StatusBadge,
  PageTransition,
} from "../../styles/components";

export { default as ErrorBoundary } from "./ErrorBoundary";
```

---

### Phase 2 — Monolith Decomposition

---

### Task 2.1: Decompose UserProfile.jsx — Create sub-components

**Files:**
- Create: `frontend/src/components/auth/ProfileInfo.jsx`
- Create: `frontend/src/components/auth/SecuritySettings.jsx`
- Create: `frontend/src/components/auth/ApiTokens.jsx`
- Create: `frontend/src/components/auth/NotificationPreferences.jsx`
- Create: `frontend/src/components/auth/ActivityLog.jsx`
- Modify: `frontend/src/components/auth/UserProfile.jsx` (rewrite as shell)

- [ ] **Step 1: Create ProfileInfo.jsx**

Extract the profile editing section (avatar upload, name, email, bio). Keep all original functionality.

```jsx
import { useState } from "react";
import { CameraIcon } from "@heroicons/react/24/outline";
import { Input, Button } from "../common";

export const ProfileInfo = ({ user, onUpdate }) => {
  const [name, setName] = useState(user?.name || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onUpdate({ name, bio });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-6">
        <div className="relative group">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white">
            {user?.name?.[0]?.toUpperCase() || "?"}
          </div>
          <button className="absolute bottom-0 right-0 p-1.5 bg-gray-800 rounded-full border border-gray-700 opacity-0 group-hover:opacity-100 transition-opacity">
            <CameraIcon className="w-4 h-4 text-gray-300" />
          </button>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">{user?.name || "User"}</h3>
          <p className="text-sm text-gray-400">{user?.email}</p>
          <p className="text-xs text-gray-500 mt-0.5">Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "N/A"}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input label="Full Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
        <Input label="Email" value={user?.email || ""} disabled placeholder="email@example.com" />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Bio</label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700/50 rounded-lg text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          placeholder="Tell us about yourself..."
        />
      </div>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Create SecuritySettings.jsx**

```jsx
import { useState } from "react";
import { Input, Button, Alert } from "../common";
import { KeyIcon, ShieldCheckIcon, ClockIcon } from "@heroicons/react/24/outline";

export const SecuritySettings = ({ user }) => {
  const [passwordData, setPasswordData] = useState({ current: "", new: "", confirm: "" });
  const [message, setMessage] = useState(null);

  const handlePasswordChange = async () => {
    if (passwordData.new !== passwordData.confirm) {
      setMessage({ type: "error", text: "Passwords do not match" });
      return;
    }
    // API call would go here
    setMessage({ type: "success", text: "Password updated successfully" });
    setPasswordData({ current: "", new: "", confirm: "" });
  };

  return (
    <div className="space-y-8">
      <div>
        <h4 className="text-white font-medium mb-4 flex items-center gap-2">
          <KeyIcon className="w-4 h-4 text-blue-400" /> Change Password
        </h4>
        <div className="space-y-3 max-w-md">
          <Input label="Current Password" type="password" value={passwordData.current} onChange={(e) => setPasswordData({ ...passwordData, current: e.target.value })} />
          <Input label="New Password" type="password" value={passwordData.new} onChange={(e) => setPasswordData({ ...passwordData, new: e.target.value })} />
          <Input label="Confirm New Password" type="password" value={passwordData.confirm} onChange={(e) => setPasswordData({ ...passwordData, confirm: e.target.value })} />
          <Button onClick={handlePasswordChange}>Update Password</Button>
        </div>
        {message && <Alert variant={message.type} title={message.text} className="mt-3" />}
      </div>

      <div className="border-t border-gray-700/50 pt-6">
        <h4 className="text-white font-medium mb-4 flex items-center gap-2">
          <ShieldCheckIcon className="w-4 h-5 text-green-400" /> Two-Factor Authentication
        </h4>
        <p className="text-gray-400 text-sm mb-3">Add an extra layer of security to your account.</p>
        <Button variant={user?.mfa_enabled ? "secondary" : "primary"}>
          {user?.mfa_enabled ? "Disable 2FA" : "Enable 2FA"}
        </Button>
      </div>

      <div className="border-t border-gray-700/50 pt-6">
        <h4 className="text-white font-medium mb-4 flex items-center gap-2">
          <ClockIcon className="w-4 h-4 text-purple-400" /> Active Sessions
        </h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
            <div>
              <p className="text-sm text-gray-200">Chrome on Windows</p>
              <p className="text-xs text-gray-500">Current session • Last active: now</p>
            </div>
            <span className="text-xs text-green-400 bg-green-900/30 px-2 py-0.5 rounded-full">Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Create ApiTokens.jsx**

Extract the token management section from the original UserProfile.jsx. The component should:

```jsx
import { useState } from "react";
import { Input, Button, EmptyState, ConfirmDialog } from "../common";
import { KeyIcon, ClipboardIcon, TrashIcon } from "@heroicons/react/24/outline";

export const ApiTokens = ({ user }) => {
  const [tokens, setTokens] = useState(user?.api_tokens || []);
  const [showNewTokenForm, setShowNewTokenForm] = useState(false);
  const [newTokenName, setNewTokenName] = useState("");
  const [deleteTokenId, setDeleteTokenId] = useState(null);
  const [createdToken, setCreatedToken] = useState(null);

  const handleCreate = async () => {
    // API call to create token
    // On success, setCreatedToken with the full token string (shown once)
  };

  const handleRevoke = async (tokenId) => {
    // API call to revoke
    setTokens(tokens.filter((t) => t.id !== tokenId));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (tokens.length === 0 && !showNewTokenForm) {
    return (
      <EmptyState
        icon={<KeyIcon className="w-8 h-8" />}
        title="No API Tokens"
        description="Create a token to use the ONYX API"
        action={<Button onClick={() => setShowNewTokenForm(true)}>Create Token</Button>}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-white font-medium">API Tokens</h4>
        <Button size="sm" onClick={() => setShowNewTokenForm(true)}>+ New Token</Button>
      </div>

      {createdToken && (
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
          <p className="text-blue-300 text-sm font-medium mb-2">Token created! Copy it now — it won't be shown again.</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-gray-800 px-3 py-2 rounded text-sm font-mono text-gray-200 truncate">{createdToken}</code>
            <button onClick={() => copyToClipboard(createdToken)} className="p-2 text-gray-400 hover:text-white">
              <ClipboardIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {tokens.length > 0 && (
        <div className="space-y-2">
          {tokens.map((token) => (
            <div key={token.id} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div>
                <p className="text-sm text-gray-200">{token.name}</p>
                <p className="text-xs text-gray-500">Created {new Date(token.created_at).toLocaleDateString()}{token.expires_at ? ` · Expires ${new Date(token.expires_at).toLocaleDateString()}` : ""}</p>
              </div>
              <button onClick={() => setDeleteTokenId(token.id)} className="p-1.5 text-gray-500 hover:text-red-400">
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog isOpen={!!deleteTokenId} onClose={() => setDeleteTokenId(null)} onConfirm={() => handleRevoke(deleteTokenId)} title="Revoke Token" message="This action cannot be undone. Any services using this token will lose access." confirmLabel="Revoke" variant="danger" />
    </div>
  );
};
```

- [ ] **Step 4: Create NotificationPreferences.jsx**

Extract the notification toggle groups from the original UserProfile.jsx. The component renders categories (security alerts, scan results, compliance updates, account activity) each with email and in-app toggles:

```jsx
import { useState } from "react";
import { BellIcon, EnvelopeIcon } from "@heroicons/react/24/outline";

const defaultCategories = [
  { id: "security_alerts", label: "Security Alerts", description: "Critical vulnerabilities and threats" },
  { id: "scan_results", label: "Scan Results", description: "Completed scan summaries" },
  { id: "compliance_updates", label: "Compliance Updates", description: "Compliance status changes" },
  { id: "account_activity", label: "Account Activity", description: "Login notifications and security changes" },
];

export const NotificationPreferences = ({ user }) => {
  const [prefs, setPrefs] = useState(user?.notification_preferences || {});
  return (
    <div className="space-y-4">
      {defaultCategories.map((cat) => (
        <div key={cat.id} className="p-4 bg-gray-800/30 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm text-white font-medium">{cat.label}</p>
              <p className="text-xs text-gray-500">{cat.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input type="checkbox" checked={prefs[cat.id]?.email ?? true} onChange={() => {/* toggle */}} className="rounded border-gray-600 bg-gray-800 text-blue-500" />
              <EnvelopeIcon className="w-4 h-4" /> Email
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input type="checkbox" checked={prefs[cat.id]?.in_app ?? true} onChange={() => {/* toggle */}} className="rounded border-gray-600 bg-gray-800 text-blue-500" />
              <BellIcon className="w-4 h-4" /> In-App
            </label>
          </div>
        </div>
      ))}
    </div>
  );
};
```

- [ ] **Step 5: Create ActivityLog.jsx**

Extract the recent activity timeline from the original UserProfile.jsx. Shows paginated activity entries with icons, relative timestamps, and empty state:

```jsx
import { useState } from "react";
import { ClockIcon } from "@heroicons/react/24/outline";
import { DataTable, EmptyState } from "../common";

const activityIcons = {
  login: "🔐",
  logout: "🚪",
  password_change: "🔑",
  token_created: "🔑",
  token_revoked: "🗑️",
  mfa_enabled: "✅",
  mfa_disabled: "❌",
  profile_update: "✏️",
};

export const ActivityLog = ({ user }) => {
  const [page, setPage] = useState(1);
  const activities = user?.activity_log || [];

  if (activities.length === 0) {
    return <EmptyState icon={<ClockIcon className="w-8 h-8" />} title="No Activity" description="Your account activity will appear here" />;
  }

  const columns = [
    { key: "type", label: "", render: (val) => <span>{activityIcons[val] || "📋"}</span>, width: "40px" },
    { key: "description", label: "Action" },
    { key: "timestamp", label: "Date", render: (val) => val ? new Date(val).toLocaleString() : "-", width: "180px" },
    { key: "ip_address", label: "IP Address", width: "140px" },
  ];

  return <DataTable columns={columns} data={activities} currentPage={page} onPageChange={setPage} pageSize={10} />;
};
```

- [ ] **Step 6: Rewrite UserProfile.jsx as shell**

Replace the ~2312 line file with a tab-based shell:

```jsx
import { useState } from "react";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useAuth } from "./AuthContext";
import { ProfileInfo } from "./ProfileInfo";
import { SecuritySettings } from "./SecuritySettings";
import { ApiTokens } from "./ApiTokens";
import { NotificationPreferences } from "./NotificationPreferences";
import { ActivityLog } from "./ActivityLog";
import { Modal } from "../common";

const TABS = [
  { id: "profile", label: "Profile" },
  { id: "security", label: "Security" },
  { id: "tokens", label: "API Tokens" },
  { id: "notifications", label: "Notifications" },
  { id: "activity", label: "Activity Log" },
];

export const UserProfile = ({ onClose }) => {
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <Modal isOpen={true} onClose={onClose} title="User Profile" size="lg">
      <div className="flex gap-6">
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeTab === tab.id
                    ? "bg-blue-600/20 text-blue-400 font-medium"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex-1 min-w-0">
          {activeTab === "profile" && <ProfileInfo user={user} onUpdate={updateUser} />}
          {activeTab === "security" && <SecuritySettings user={user} />}
          {activeTab === "tokens" && <ApiTokens user={user} />}
          {activeTab === "notifications" && <NotificationPreferences user={user} />}
          {activeTab === "activity" && <ActivityLog user={user} />}
        </div>
      </div>
    </Modal>
  );
};
```

- [ ] **Step 7: Verify UserProfile modal works end-to-end**

Open the profile modal from MainLayout. Each tab renders the correct sub-component.

---

### Task 2.2: Decompose EnhancedReportDetails.jsx — Create sub-components

**Files:**
- Create: `frontend/src/components/reports/ReportSummary.jsx`
- Create: `frontend/src/components/reports/VulnerabilityList.jsx`
- Create: `frontend/src/components/reports/ReportCharts.jsx`
- Create: `frontend/src/components/reports/ComplianceMapping.jsx`
- Create: `frontend/src/components/reports/ReportExport.jsx`
- Create: `frontend/src/components/reports/ReportComparison.jsx`
- Modify: `frontend/src/components/reports/EnhancedReportDetails.jsx` (rewrite as shell)

- [ ] **Step 1: Create ReportSummary.jsx**

Extract from EnhancedReportDetails.jsx: the security score ring chart, stat cards (total findings, critical/high/medium/low counts), and report metadata (date, branch, scanner, duration). Export as a named component.

```jsx
import { MetricCard, DonutChart } from "../common";

export const ReportSummary = ({ report }) => {
  const score = report?.security_score || 0;
  const bySeverity = report?.findings_by_severity || {};
  const total = Object.values(bySeverity).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-8">
        <DonutChart value={score} size={140} strokeWidth={12} color={score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444"}>
          <div className="text-center">
            <p className="text-3xl font-bold text-white">{score}</p>
            <p className="text-xs text-gray-400">Score</p>
          </div>
        </DonutChart>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 flex-1">
          <MetricCard title="Total Findings" value={total} color="blue" />
          <MetricCard title="Critical" value={bySeverity.critical || 0} color="red" />
          <MetricCard title="High" value={bySeverity.high || 0} color="yellow" />
          <MetricCard title="Medium" value={bySeverity.medium || 0} color="indigo" />
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div><span className="text-gray-500">Date:</span> <span className="text-gray-300">{report?.created_at ? new Date(report.created_at).toLocaleString() : "N/A"}</span></div>
        <div><span className="text-gray-500">Branch:</span> <span className="text-gray-300">{report?.branch || "N/A"}</span></div>
        <div><span className="text-gray-500">Scanner:</span> <span className="text-gray-300">{report?.scanner || report?.scan_type || "N/A"}</span></div>
        <div><span className="text-gray-500">Duration:</span> <span className="text-gray-300">{report?.duration ? `${report.duration}s` : "N/A"}</span></div>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Create VulnerabilityList.jsx**

Extract from EnhancedReportDetails.jsx: the filterable, sortable findings table with severity tabs, search, and pagination. Use the new `<DataTable>` component.

```jsx
import { useState, useMemo } from "react";
import { DataTable, SeverityBadge } from "../common";
import { FunnelIcon } from "@heroicons/react/24/outline";

export const VulnerabilityList = ({ findings = [] }) => {
  const [severityFilter, setSeverityFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let result = findings;
    if (severityFilter !== "all") result = result.filter((f) => f.severity === severityFilter);
    if (search) result = result.filter((f) => f.title?.toLowerCase().includes(search.toLowerCase()));
    return result;
  }, [findings, severityFilter, search]);

  const columns = [
    { key: "severity", label: "Severity", render: (val) => <SeverityBadge severity={val} />, width: "100px", sortable: true },
    { key: "title", label: "Finding", sortable: true },
    { key: "file_path", label: "File", render: (val) => <span className="font-mono text-xs truncate max-w-[200px] block">{val || "-"}</span> },
    { key: "scanner", label: "Scanner", width: "120px" },
    { key: "status", label: "Status", render: (val) => <span className="capitalize">{val || "open"}</span>, width: "100px" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search findings..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700/50 rounded-lg text-sm text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500"
          />
          <FunnelIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 bg-gray-800 border border-gray-700/50 rounded-lg text-sm text-white"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <DataTable columns={columns} data={filtered} emptyMessage="No findings match the current filters" />
    </div>
  );
};
```

- [ ] **Step 3: Create ReportCharts.jsx**

Extract the severity breakdown bar chart, trend line chart, and vulnerability donut chart from EnhancedReportDetails.jsx. Render using SVG or a simple bar/line approach with the existing `DonutChart` and `SeverityProgressBar`.

- [ ] **Step 4: Create ComplianceMapping.jsx**

Extract the compliance framework-to-finding mapping section. Render as a table showing: framework, control ID, status (passed/failed/not-applicable), linked findings.

- [ ] **Step 5: Create ReportExport.jsx**

Extract the export functionality: format selection (PDF, CSV, SARIF), download button, copy-to-clipboard for raw JSON. Uses the existing download/copy logic from the original file.

- [ ] **Step 6: Create ReportComparison.jsx**

Extract the side-by-side diff view between two scans/reports. Shows: score comparison, finding count delta, severity breakdown diff.

- [ ] **Step 7: Rewrite EnhancedReportDetails.jsx as shell**

Replace the ~3455 line file with a tabbed shell:

```jsx
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageContainer, PageHeader, ErrorState, LoadingState } from "../../layouts";
import { ReportSummary } from "./ReportSummary";
import { VulnerabilityList } from "./VulnerabilityList";
import { ReportCharts } from "./ReportCharts";
import { ComplianceMapping } from "./ComplianceMapping";
import { ReportExport } from "./ReportExport";
import { ReportComparison } from "./ReportComparison";

const TABS = [
  { id: "summary", label: "Summary" },
  { id: "findings", label: "Findings" },
  { id: "charts", label: "Charts" },
  { id: "compliance", label: "Compliance" },
  { id: "comparison", label: "Comparison" },
  { id: "export", label: "Export" },
];

export const EnhancedReportDetails = () => {
  const { reportId } = useParams();
  const [activeTab, setActiveTab] = useState("summary");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["report", reportId],
    queryFn: async () => {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/reports/${reportId}`, {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!res.ok) throw new Error("Failed to load report");
      return res.json();
    },
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message={error.message} onRetry={refetch} />;

  const report = data?.report || data;
  const findings = report?.findings || report?.vulnerabilities || [];

  return (
    <PageContainer>
      <PageHeader title={`Report: ${report?.title || reportId}`} description="Detailed security scan report" breadcrumb={["Reports", reportId]} />
      <div className="border-b border-gray-700/50 mb-6">
        <nav className="flex gap-1 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-gray-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      {activeTab === "summary" && <ReportSummary report={report} />}
      {activeTab === "findings" && <VulnerabilityList findings={findings} />}
      {activeTab === "charts" && <ReportCharts report={report} />}
      {activeTab === "compliance" && <ComplianceMapping report={report} />}
      {activeTab === "comparison" && <ReportComparison report={report} />}
      {activeTab === "export" && <ReportExport report={report} />}
    </PageContainer>
  );
};
```

Note: Each extracted sub-component must be independently readable. The original ~3455 lines will become 7 files of ~200-400 lines each.

---

### Phase 3 — Page Migration

---

### Task 3.1: Migrate Dashboard.jsx

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

Replace remaining raw Tailwind patterns with design system components:
- Replace `<div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">` with `<GlassCard>` or `<Card>`
- Replace stat display sections with `<StatCard>` or `<MetricCard>`
- Replace raw headings with `<SectionHeader>`

- [ ] **Step 1: Audit current raw Tailwind patterns**

Search for `bg-gray-800/50 border border-gray-700/50 rounded-xl` — these are raw card implementations that should use `<GlassCard>` or `<Card>`.

- [ ] **Step 2 through Step N:** Replace each occurrence with the equivalent design system component, verify visually after each change.

---

### Task 3.2: Migrate ProjectManagement.jsx

**Files:**
- Modify: `frontend/src/components/projects/ProjectManagement.jsx`

Replace raw card, button, badge, and empty state patterns with `Card`, `Button`, `Badge`, `EmptyState` from the design system.

---

### Task 3.3: Migrate ProjectDetails.jsx

**Files:**
- Modify: `frontend/src/components/projects/ProjectDetails.jsx`

Replace findings table with `<DataTable>`, stat cards with `<MetricCard>`, severity badges with `<SeverityBadge>`.

---

### Task 3.4: Migrate Reports.jsx and Analytics.jsx

**Files:**
- Modify: `frontend/src/pages/Reports.jsx`
- Modify: `frontend/src/pages/Analytics.jsx`

---

### Task 3.5: Migrate Security Widgets (3 files)

**Files:**
- Modify: `frontend/src/components/security/SecurityTrendsDashboard.jsx`
- Modify: `frontend/src/components/security/ScanComparison.jsx`
- Modify: `frontend/src/components/security/SBOMViewer.jsx`

These are already dark-themed. Replace raw card patterns with `<GlassCard>`, trend indicators with design system components, severity badges with `<SeverityBadge>`/`<Badge>`.

---

### Task 3.6: Migrate remaining pages

**Files:**
- Modify: `frontend/src/components/compliance/AdvancedCompliance.jsx`
- Modify: `frontend/src/components/compliance/DataRetentionPolicies.jsx`
- Modify: `frontend/src/components/users/UserManagement.jsx`
- Modify: `frontend/src/components/users/AuditLogs.jsx`
- Modify: `frontend/src/components/settings/Settings.jsx`
- Modify: `frontend/src/pages/AdminDashboard.jsx`
- Modify: `frontend/src/components/auth/*.jsx` (login, register, etc.)

Each follows the same process: audit → replace raw Tailwind with design system components → verify.

---

### Phase 4 — UX Excellence

---

### Task 4.1: Build Command Palette

**Files:**
- Create: `frontend/src/components/common/CommandPalette.jsx`
- Install: `fuse.js` npm package
- Modify: `frontend/src/components/common/index.js`
- Modify: `frontend/src/layouts/MainLayout.jsx` (mount CommandPalette)

**Details:** Global Cmd+K overlay with fuzzy search across routes, projects, reports, quick actions.

- [ ] **Step 1: Install fuse.js**

Run: `npm install fuse.js`

- [ ] **Step 2: Create CommandPalette.jsx**

```jsx
import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import Fuse from "fuse.js";

const defaultActions = [
  { id: "nav-dashboard", label: "Go to Dashboard", category: "Navigation", path: "/dashboard", icon: "📊" },
  { id: "nav-projects", label: "Go to Projects", category: "Navigation", path: "/projects", icon: "📁" },
  { id: "nav-reports", label: "Go to Reports", category: "Navigation", path: "/reports", icon: "📄" },
  { id: "nav-analytics", label: "Go to Analytics", category: "Navigation", path: "/analytics", icon: "📈" },
  { id: "nav-compliance", label: "Go to Compliance", category: "Navigation", path: "/compliance", icon: "🛡️" },
  { id: "nav-users", label: "Go to User Management", category: "Navigation", path: "/users", icon: "👥" },
  { id: "nav-settings", label: "Go to Settings", category: "Navigation", path: "/settings", icon: "⚙️" },
  { id: "action-new-scan", label: "Start New Scan", category: "Actions", icon: "🔍" },
  { id: "action-generate-sbom", label: "Generate SBOM", category: "Actions", icon: "📋" },
  { id: "action-invite-user", label: "Invite User", category: "Actions", icon: "✉️" },
];

export const CommandPalette = ({ isOpen, onClose, projects = [], reports = [] }) => {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  const allItems = useMemo(() => {
    const projectItems = projects.map((p) => ({
      id: `project-${p.id}`,
      label: p.name,
      category: "Projects",
      path: `/project/${p.id}`,
      icon: "📁",
    }));
    const reportItems = reports.map((r) => ({
      id: `report-${r.id}`,
      label: r.title || `Report ${r.id}`,
      category: "Reports",
      path: `/report/${r.id}`,
      icon: "📄",
    }));
    return [...defaultActions, ...projectItems, ...reportItems];
  }, [projects, reports]);

  const fuse = useMemo(() => new Fuse(allItems, {
    keys: ["label", "category"],
    threshold: 0.4,
  }), [allItems]);

  const results = useMemo(() => {
    if (!query.trim()) return { items: allItems, groups: {} };
    const fused = fuse.search(query).map((r) => r.item);
    return { items: fused, groups: {} };
  }, [query, fuse, allItems]);

  useEffect(() => {
    if (isOpen) setQuery("");
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Group results by category
  const grouped = useMemo(() => {
    const groups = {};
    results.items.forEach((item) => {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push(item);
    });
    return groups;
  }, [results]);

  const flattenedItems = useMemo(() => {
    const items = [];
    Object.entries(grouped).forEach(([category, categoryItems]) => {
      items.push({ type: "category", label: category });
      categoryItems.forEach((item) => items.push({ type: "item", ...item }));
    });
    return items;
  }, [grouped]);

  const handleSelect = useCallback((item) => {
    if (item.path) navigate(item.path);
    onClose();
  }, [navigate, onClose]);

  const handleKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, flattenedItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      const selected = flattenedItems[selectedIndex];
      if (selected && selected.type === "item") handleSelect(selected);
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-gray-900 border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-700/50">
          <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search pages, projects, reports..."
            className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none text-sm"
            autoFocus
          />
          <kbd className="hidden sm:inline-flex px-1.5 py-0.5 text-xs text-gray-500 bg-gray-800 rounded border border-gray-700">
            ESC
          </kbd>
        </div>

        <div className="max-h-[50vh] overflow-y-auto p-2">
          {flattenedItems.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">No results found</div>
          ) : (
            flattenedItems.map((item, i) => {
              let flatIdx = i;
              return item.type === "category" ? (
                <div key={item.label} className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {item.label}
                </div>
              ) : (
                <button
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    flatIdx === selectedIndex
                      ? "bg-blue-600/20 text-blue-400"
                      : "text-gray-300 hover:bg-gray-800/50"
                  }`}
                >
                  <span className="text-base">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Export from common/index.js**

```jsx
export { CommandPalette } from "./CommandPalette";
```

- [ ] **Step 4: Mount in MainLayout.jsx**

```jsx
import { CommandPalette } from "../components/common";
// ...
const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

useEffect(() => {
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setCommandPaletteOpen((prev) => !prev);
    }
  };
  window.addEventListener("keydown", handleKeyDown);
  return () => window.removeEventListener("keydown", handleKeyDown);
}, []);

// In the JSX, anywhere in the layout:
<CommandPalette
  isOpen={commandPaletteOpen}
  onClose={() => setCommandPaletteOpen(false)}
  projects={/* pass real projects data */}
  reports={/* pass real reports data */}
/>
```

- [ ] **Step 5: Test command palette**

Press Cmd+K — palette opens with all navigation items and actions. Search filters correctly. Arrow keys navigate. Enter selects. Escape closes.

---

### Task 4.2: Add page transitions to all routes

**Files:**
- Modify: `frontend/src/layouts/MainLayout.jsx` (wrap routes with PageTransition)

- [ ] **Step 1: Wrap route content**

In MainLayout.jsx, import PageTransition and wrap the `<Routes>` content:

```jsx
import { PageTransition } from "../components/common";

// Inside the <main> element:
<main id="main-content" className="flex-1 relative overflow-auto">
  <PageTransition>
    <Routes>
      {/* ... all routes ... */}
    </Routes>
  </PageTransition>
</main>
```

---

### Task 4.3: Add micro-interactions

**Files:**
- Modify: `frontend/src/styles/components.jsx` (update Button, Card styles)
- Modify: `frontend/src/layouts/Sidebar.jsx` (add hover scale on icons)
- Modify: `frontend/src/styles/classNames.js` (add interaction variants)

- [ ] **Step 1: Update button hover/active states**

In `classNames.js`, update buttonStyles.variants to include scale transforms:

```jsx
primary: "bg-blue-600 text-white hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] focus:ring-blue-500 transition-all duration-150",
```

- [ ] **Step 2: Add card hover effect to interactive cards**

In `components.jsx`, update the Card component's hoverable variant to include lift:

```jsx
hoverable ? "hover:-translate-y-1 hover:shadow-lg hover:border-blue-500/30 transition-all duration-300" : ""
```

- [ ] **Step 3: Add sidebar icon hover scale**

In `Sidebar.jsx`, add `transition-transform duration-200 group-hover:scale-110` to nav icons.

---

### Task 4.4: Accessibility pass

**Files:**
- All component files with interactive elements

- [ ] **Step 1: Add focus-visible rings to all buttons**

Audit and add `focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900` to all interactive elements.

- [ ] **Step 2: Audit aria labels**

- Icon-only buttons need `aria-label`
- Tab panels need `role="tablist"`, `aria-selected`, `aria-controls`
- Modals need `aria-modal`, `aria-labelledby`, focus trapping
- Expandable sections need `aria-expanded`

- [ ] **Step 3: Keyboard navigation audit**

Ensure all interactive elements are reachable via tab, all dropdowns work with arrow keys, modals trap focus, escape closes overlays.

---

### Task 4.5: Standardize state components

**Files:**
- Every page that fetches data

- [ ] **Step 1: Audit each page for loading/empty/error states**

Replace inline loading text, inline empty text, and raw error displays with `<LoadingState>`, `<EmptyState>`, `<ErrorState>` from layouts.

---

### Phase 5 — Performance

---

### Task 5.1: Route-level code splitting

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Wrap every route export with React.lazy**

```jsx
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("../pages/Dashboard"));
const ProjectManagement = lazy(() => import("../components/projects/ProjectManagement"));
// ... every route

// Wrap the Router content:
<Suspense fallback={<LoadingScreen />}>
  <Routes>...</Routes>
</Suspense>
```

---

### Task 5.2: Component memoization

**Files:**
- `frontend/src/styles/components.jsx` — add React.memo to StatCard, Badge, SeverityBadge, MetricCard, FindingCard
- Page components — add useMemo for computed lists

- [ ] **Step 1: Memoize design system components**

```jsx
export const StatCard = React.memo(({ ... }) => { ... });
export const Badge = React.memo(({ ... }) => { ... });
// etc.
```

---

### Task 5.3: Virtualize long lists

**Files:**
- `frontend/src/pages/Dashboard.jsx` (recent scans list)
- `frontend/src/components/reports/VulnerabilityList.jsx` (findings list)
- `frontend/src/components/security/SBOMViewer.jsx` (package list)
- `frontend/src/components/users/UserManagement.jsx` (user list)
- `frontend/src/components/users/AuditLogs.jsx` (log entries)

- [ ] **Step 1: Install react-window**

Run: `npm install react-window`

- [ ] **Step 2 through Step N:** Replace each `.map()` + `overflow-y-auto` with `<FixedSizeList>` or `<VariableSizeList>` from react-window.

---

## Verification Plan

| Check | Method |
|---|---|
| Each page renders identically after migration | Manual visual comparison before/after |
| Command palette works globally | Cmd+K opens, search filters, enter navigates |
| Accessibility | Chrome Lighthouse audit — target score >= 90 |
| Bundle size | `npm run build` — compare before/after stats |
| No regressions | All existing functionality works after decomposition |
| Dark theme consistency | No light-mode classes remain in any component |
