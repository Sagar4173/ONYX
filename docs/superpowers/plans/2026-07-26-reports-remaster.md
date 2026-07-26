# Reports List Remaster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster the `/reports` page with list/grid toggle, enhanced report cards with severity bars and Canvas mini donuts, upgraded filter bar, and staggered animations.

**Architecture:** Page-level orchestrator (`Reports.jsx`) composes `ReportFilters` + `ReportList`. `ReportList` delegates to `ReportListItem` (list mode) or `ReportGridCard` (grid mode) based on `viewMode` state. Same data fetching, same API, purely visual upgrade.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, Canvas API, react-router-dom, @tanstack/react-query

## Global Constraints
- Zero new npm dependencies — Canvas API and framer-motion already available
- Follow ONYX design language: cyan-400/violet-500/cyan-400 gradients, glassmorphism, dark theme, Inter font
- All new components go in `frontend/src/components/reports/`
- Lint: `npx eslint src/` must pass with 0 errors, 0 warnings

---
### File Structure

```
frontend/src/components/reports/
├── ReportListItem.jsx     (NEW)
├── ReportGridCard.jsx     (NEW)
├── ReportList.jsx         (REWRITE — viewMode, enhanced skeletons)
├── ReportFilters.jsx      (ENHANCE — visual polish)
├── ReportCard.jsx         (DELETE — replaced by ReportListItem + ReportGridCard)

frontend/src/pages/
└── Reports.jsx            (MODIFY — add viewMode + toggle)
```

---
### Task 1: ReportListItem.jsx

**Files:**
- Create: `frontend/src/components/reports/ReportListItem.jsx`

**Interfaces:**
- Consumes: `report` (object — same shape as current ReportCard receives), `index` (number for stagger delay)
- Produces: animated list item row with severity bar, status icon, scan type badge, severity badges

- [ ] **Step 1: Create ReportListItem.jsx**

```jsx
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { CheckCircleIcon, ClockIcon, XCircleIcon } from "@heroicons/react/24/outline";
import { Badge } from "../../styles/components";

const statusConfig = {
  completed: { icon: CheckCircleIcon, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Completed" },
  running: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  in_progress: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  pending: { icon: ClockIcon, color: "text-amber-400", bg: "bg-amber-500/10", label: "Pending" },
  failed: { icon: XCircleIcon, color: "text-red-400", bg: "bg-red-500/10", label: "Failed" },
  cancelled: { icon: XCircleIcon, color: "text-gray-400", bg: "bg-gray-500/10", label: "Cancelled" },
};

const scanTypeColors = {
  sast: "from-cyan-500 to-blue-600",
  secrets: "from-purple-500 to-pink-600",
  dependency: "from-amber-500 to-orange-600",
  container: "from-teal-500 to-emerald-600",
  iac: "from-violet-500 to-indigo-600",
  dast: "from-rose-500 to-red-600",
};

const itemAnim = { hidden: { opacity: 0, x: -10 }, show: { opacity: 1, x: 0 } };

const ScanTypeBadge = ({ type }) => {
  const color = scanTypeColors[type] || "from-gray-500 to-gray-600";
  const label = (type || "sast").toUpperCase();
  return (
    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[10px] font-bold text-white bg-gradient-to-r ${color}`}>
      {label}
    </span>
  );
};

const ReportListItem = ({ report, index }) => {
  const navigate = useNavigate();
  const status = statusConfig[report.status] || statusConfig.pending;
  const StatusIcon = status.icon;
  const sev = report.findings_by_severity || {};
  const critical = sev.critical || 0;
  const high = sev.high || 0;
  const medium = sev.medium || 0;
  const low = sev.low || 0;
  const total = critical + high + medium + low;

  return (
    <motion.div
      variants={itemAnim}
      onClick={() => navigate(`/report/${report.id}`)}
      className="group relative flex items-center gap-4 p-4 rounded-xl bg-gray-800/20 hover:bg-gray-800/40 border border-transparent hover:border-gray-700/50 transition-all cursor-pointer overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") navigate(`/report/${report.id}`); }}
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${critical > 0 ? "bg-red-500" : high > 0 ? "bg-orange-500" : medium > 0 ? "bg-yellow-500" : "bg-transparent"}`} />
      <div className={`p-2.5 rounded-xl ${status.bg} flex-shrink-0`}>
        <StatusIcon className={`h-5 w-5 ${status.color} ${(status.label === "Running" || status.label === "Pending") ? "animate-pulse" : ""}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-sm font-semibold text-white truncate">{report.project_name || report.repository_url?.replace(/^https?:\/\//, "") || "Untitled"}</h3>
          <ScanTypeBadge type={report.scan_type || report.type} />
          {report.security_score != null && (
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${report.security_score >= 80 ? "bg-emerald-500/20 text-emerald-400" : report.security_score >= 60 ? "bg-amber-500/20 text-amber-400" : "bg-red-500/20 text-red-400"}`}>
              {report.security_score}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <StatusIcon className={`w-3 h-3 ${status.color}`} />
            {status.label}
          </span>
          {report.created_at && <span>{new Date(report.created_at).toLocaleDateString()}</span>}
          {total > 0 && <span>{total} findings</span>}
        </div>
      </div>
      <div className="flex items-center gap-1 flex-shrink-0">
        {critical > 0 && <Badge variant="critical" size="xs">{critical}</Badge>}
        {high > 0 && <Badge variant="high" size="xs">{high}</Badge>}
        {medium > 0 && <Badge variant="medium" size="xs">{medium}</Badge>}
        {low > 0 && <Badge variant="low" size="xs">{low}</Badge>}
        {total === 0 && <Badge variant="success" size="xs">Clean</Badge>}
      </div>
    </motion.div>
  );
};

export default ReportListItem;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/reports/ReportListItem.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/reports/ReportListItem.jsx
git commit -m "feat: Task 1 — ReportListItem with severity bar, status icons, scan type badges"
```

---
### Task 2: ReportGridCard.jsx

**Files:**
- Create: `frontend/src/components/reports/ReportGridCard.jsx`

**Interfaces:**
- Consumes: `report` (object), `index` (number for stagger)
- Produces: glass card with Canvas mini donut, score, findings summary

- [ ] **Step 1: Create ReportGridCard.jsx**

```jsx
import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { DocumentTextIcon } from "@heroicons/react/24/outline";
import { Badge } from "../../styles/components";

const scanTypeColors = {
  sast: "from-cyan-500 to-blue-600",
  secrets: "from-purple-500 to-pink-600",
  dependency: "from-amber-500 to-orange-600",
  container: "from-teal-500 to-emerald-600",
  iac: "from-violet-500 to-indigo-600",
  dast: "from-rose-500 to-red-600",
};

const donutColors = [
  { stroke: "#22d3ee", text: "#22d3ee" },
  { stroke: "#fbbf24", text: "#fbbf24" },
  { stroke: "#f87171", text: "#f87171" },
];

const MiniDonut = ({ score, size = 64 }) => {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const cx = size / 2, cy = size / 2, r = size / 2 - 6, lineW = 6;
    const color = score >= 80 ? donutColors[0] : score >= 60 ? donutColors[1] : donutColors[2];
    const fraction = Math.min(score, 100) / 100;
    ctx.clearRect(0, 0, size, size);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(75, 85, 99, 0.3)";
    ctx.lineWidth = lineW;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * fraction);
    ctx.strokeStyle = color.stroke;
    ctx.lineWidth = lineW;
    ctx.lineCap = "round";
    ctx.stroke();
    ctx.fillStyle = color.text;
    ctx.font = `bold ${size * 0.23}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(Math.round(score).toString(), cx, cy);
  }, [score, size]);
  return <canvas ref={canvasRef} style={{ width: size, height: size }} />;
};

const itemAnim = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const ReportGridCard = ({ report, index }) => {
  const navigate = useNavigate();
  const sev = report.findings_by_severity || {};
  const critical = sev.critical || 0;
  const high = sev.high || 0;
  const medium = sev.medium || 0;
  const total = critical + high + medium + (sev.low || 0);
  const scanType = report.scan_type || report.type || "sast";

  return (
    <motion.div variants={itemAnim}
      onClick={() => navigate(`/report/${report.id}`)}
      className="group bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 hover:border-cyan-500/40 hover:shadow-lg hover:shadow-cyan-500/5 transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") navigate(`/report/${report.id}`); }}
    >
      <div className="flex items-center justify-between mb-4">
        <MiniDonut score={report.security_score || 0} size={64} />
        <div className="flex flex-col items-end gap-1">
          <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[10px] font-bold text-white bg-gradient-to-r ${scanTypeColors[scanType] || "from-gray-500 to-gray-600"}`}>
            {scanType.toUpperCase()}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${report.security_score >= 80 ? "bg-emerald-500/20 text-emerald-400" : report.security_score >= 60 ? "bg-amber-500/20 text-amber-400" : "bg-red-500/20 text-red-400"}`}>
            Score: {report.security_score ?? "—"}
          </span>
        </div>
      </div>
      <h3 className="text-sm font-semibold text-white truncate mb-2">{report.project_name || "Untitled"}</h3>
      {report.created_at && <p className="text-xs text-gray-500 mb-3">{new Date(report.created_at).toLocaleDateString()}</p>}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {critical > 0 && <Badge variant="critical" size="xs">{critical}</Badge>}
          {high > 0 && <Badge variant="high" size="xs">{high}</Badge>}
          {medium > 0 && <Badge variant="medium" size="xs">{medium}</Badge>}
          {total === 0 && <Badge variant="success" size="xs">Clean</Badge>}
        </div>
        <span className="text-xs text-gray-500">{total} findings</span>
      </div>
    </motion.div>
  );
};

export default ReportGridCard;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/reports/ReportGridCard.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/reports/ReportGridCard.jsx
git commit -m "feat: Task 2 — ReportGridCard with Canvas mini donut, score, findings"
```

---
### Task 3: ReportList.jsx — Rewrite with viewMode

**Files:**
- Rewrite: `frontend/src/components/reports/ReportList.jsx`

**Interfaces:**
- Consumes: `reports` (array), `pagination` (object), `onPageChange` (fn), `onPerPageChange` (fn), `isLoading` (bool), `error` (any), `onRetry` (fn), `viewMode` ("list" | "grid")
- Produces: paginated report list with correct view mode

- [ ] **Step 1: Rewrite ReportList.jsx**

```jsx
import { motion } from "framer-motion";
import { ChevronLeftIcon, ChevronRightIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import { Button, Skeleton } from "../../styles/components";
import { EmptyState } from "../../styles/components";
import ReportListItem from "./ReportListItem";
import ReportGridCard from "./ReportGridCard";

const container = { hidden: {}, show: { transition: { staggerChildren: 0.04 } } };

const LoadingList = () => (
  <div className="space-y-3">
    {Array.from({ length: 5 }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 bg-gray-800/30 border border-gray-800/50 rounded-xl p-4">
        <Skeleton className="!w-12 !h-12 !rounded-2xl" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="title" className="!w-1/3" />
          <Skeleton variant="text" className="!w-1/2" />
          <Skeleton variant="text" className="!w-1/4" />
        </div>
        <Skeleton variant="button" />
      </div>
    ))}
  </div>
);

const LoadingGrid = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} className="bg-gray-800/30 border border-gray-800/50 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="!w-16 !h-16 !rounded-full" />
          <Skeleton className="!w-16 !h-6 !rounded-md" />
        </div>
        <Skeleton variant="title" className="!w-2/3 mb-2" />
        <Skeleton variant="text" className="!w-1/2 mb-3" />
        <Skeleton variant="text" className="!w-1/4" />
      </div>
    ))}
  </div>
);

const ReportList = ({ reports, pagination, onPageChange, onPerPageChange, isLoading, error, onRetry, viewMode = "list" }) => {
  if (error) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
          <DocumentTextIcon className="w-10 h-10 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Failed to load reports</h3>
        <p className="text-gray-400 text-sm mb-4">{error.message || "An error occurred."}</p>
        <Button variant="primary" onClick={onRetry}>Try Again</Button>
      </div>
    );
  }

  if (isLoading) return viewMode === "grid" ? <LoadingGrid /> : <LoadingList />;

  if (!reports || reports.length === 0) {
    return <EmptyState icon={DocumentTextIcon} title="No reports found" description="Reports will appear here once scans are completed." />;
  }

  return (
    <div>
      {viewMode === "grid" ? (
        <motion.div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" variants={container} initial="hidden" animate="show">
          {reports.map((report, i) => <ReportGridCard key={report.id} report={report} index={i} />)}
        </motion.div>
      ) : (
        <motion.div className="space-y-3" variants={container} initial="hidden" animate="show">
          {reports.map((report, i) => <ReportListItem key={report.id} report={report} index={i} />)}
        </motion.div>
      )}

      {pagination && pagination.totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-800/50">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              Showing {(pagination.page - 1) * pagination.perPage + 1}–{Math.min(pagination.page * pagination.perPage, pagination.total)} of {pagination.total}
            </span>
            <select value={pagination.perPage} onChange={(e) => onPerPageChange?.(Number(e.target.value))}
              className="px-2 py-1 bg-gray-800 border border-gray-700/50 rounded-lg text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 [&>option]:bg-gray-800">
              <option value={12}>12 / page</option>
              <option value={24}>24 / page</option>
              <option value={48}>48 / page</option>
            </select>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => onPageChange?.(pagination.page - 1)} disabled={pagination.page <= 1}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
              <ChevronLeftIcon className="w-4 h-4" />
            </button>
            {Array.from({ length: pagination.totalPages }, (_, i) => i + 1)
              .filter((p) => p === 1 || p === pagination.totalPages || Math.abs(p - pagination.page) <= 1)
              .map((p, idx, arr) => (
                <span key={p} className="flex items-center">
                  {idx > 0 && arr[idx - 1] !== p - 1 && <span className="px-1 text-gray-600 text-xs">...</span>}
                  <button onClick={() => onPageChange?.(p)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                      p === pagination.page ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "text-gray-400 hover:text-white hover:bg-gray-800"
                    }`}>
                    {p}
                  </button>
                </span>
              ))}
            <button onClick={() => onPageChange?.(pagination.page + 1)} disabled={pagination.page >= pagination.totalPages}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
              <ChevronRightIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportList;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/reports/ReportList.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/reports/ReportList.jsx
git commit -m "feat: Task 3 — ReportList with list/grid view mode, enhanced skeletons"
```

---
### Task 4: ReportFilters.jsx — Visual Upgrade

**Files:**
- Modify: `frontend/src/components/reports/ReportFilters.jsx`

- [ ] **Step 1: Update ReportFilters.jsx**

Replace the content. Only visual changes — same interface, same debounce logic, same props:

```jsx
import { useState, useEffect } from "react";
import { MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { GlassCard } from "../../layouts/UIComponents";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "completed", label: "Completed" },
  { value: "running", label: "Running" },
  { value: "pending", label: "Pending" },
  { value: "failed", label: "Failed" },
];

const sortOptions = [
  { value: "newest", label: "Newest First" },
  { value: "oldest", label: "Oldest First" },
];

const ReportFilters = ({ filters, onFilterChange, sort, onSortChange, total }) => {
  const [searchInput, setSearchInput] = useState(filters.search || "");

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== (filters.search || "")) {
        onFilterChange({ ...filters, search: searchInput });
      }
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  useEffect(() => {
    setSearchInput(filters.search || "");
  }, [filters.search]);

  const activeFilters = [];
  if (filters.status) activeFilters.push({ key: "status", label: `Status: ${filters.status}` });

  return (
    <GlassCard className="mb-6" noPadding>
      <div className="p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input type="text" value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search reports by project or repo..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
          </div>
          <select value={filters.status} onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer [&>option]:bg-gray-800 [&>option]:text-white">
            {statusOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <select value={sort} onChange={(e) => onSortChange(e.target.value)}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer [&>option]:bg-gray-800 [&>option]:text-white">
            {sortOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        {activeFilters.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {activeFilters.map((f) => (
              <span key={f.key} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                {f.label}
                <button onClick={() => onFilterChange({ ...filters, [f.key]: "" })} className="hover:text-white focus:outline-none"><XMarkIcon className="w-3 h-3" /></button>
              </span>
            ))}
            <button onClick={() => { onFilterChange({ search: "", status: "" }); setSearchInput(""); }} className="text-xs text-gray-500 hover:text-gray-300 focus:outline-none">Clear all</button>
          </div>
        )}
        {total !== undefined && <p className="text-xs text-gray-500">{total} report{total !== 1 ? "s" : ""}</p>}
      </div>
    </GlassCard>
  );
};

export default ReportFilters;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/reports/ReportFilters.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/reports/ReportFilters.jsx
git commit -m "feat: Task 4 — ReportFilters visual polish"
```

---
### Task 5: Reports.jsx — viewMode + Toggle + Cleanup

**Files:**
- Modify: `frontend/src/pages/Reports.jsx`
- Delete: `frontend/src/components/reports/ReportCard.jsx`

- [ ] **Step 1: Update Reports.jsx**

Replace the file:

```jsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowPathIcon, DocumentTextIcon, Bars3Icon, Squares2X2Icon } from "@heroicons/react/24/outline";
import { Button } from "../styles/components";
import { PageContainer, PageHeader } from "../layouts/UIComponents";
import { reportsAPI } from "../services/api";
import ReportFilters from "../components/reports/ReportFilters";
import ReportList from "../components/reports/ReportList";

const Reports = () => {
  const [viewMode, setViewMode] = useState("list");
  const [filters, setFilters] = useState({ search: "", status: "" });
  const [sort, setSort] = useState("newest");
  const [pagination, setPagination] = useState({ page: 1, perPage: 24 });

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["reports", filters, sort, pagination],
    queryFn: () => reportsAPI.getReports({
      ...filters, sort_by: "created_at", sort_order: sort === "newest" ? "desc" : "asc",
      page: pagination.page, per_page: pagination.perPage,
    }).then((res) => res.data || res),
  });

  const reports = data?.reports ?? data ?? [];
  const paginationInfo = data?.pagination || { page: 1, perPage: 24, total: reports.length, totalPages: 1 };

  const handleFilterChange = (next) => { setFilters(next); setPagination((p) => ({ ...p, page: 1 })); };
  const handleSortChange = (next) => { setSort(next); setPagination((p) => ({ ...p, page: 1 })); };

  return (
    <PageContainer>
      <PageHeader title="Scan Reports" description="View detailed security scan results" icon={DocumentTextIcon} breadcrumb={["Reports"]}
        actions={
          <div className="flex items-center gap-2">
            <div className="flex bg-gray-800/50 border border-gray-700/50 rounded-lg p-0.5">
              <button onClick={() => setViewMode("list")}
                className={`p-2 rounded-md transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${viewMode === "list" ? "bg-gray-700/70 text-white" : "text-gray-400 hover:text-white"}`}
                title="List view">
                <Bars3Icon className="w-4 h-4" />
              </button>
              <button onClick={() => setViewMode("grid")}
                className={`p-2 rounded-md transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${viewMode === "grid" ? "bg-gray-700/70 text-white" : "text-gray-400 hover:text-white"}`}
                title="Grid view">
                <Squares2X2Icon className="w-4 h-4" />
              </button>
            </div>
            <Button variant="ghost" leftIcon={<ArrowPathIcon className="w-4 h-4" />} onClick={refetch} isLoading={isFetching}>Refresh</Button>
          </div>
        }
      />
      <ReportFilters filters={filters} onFilterChange={handleFilterChange} sort={sort} onSortChange={handleSortChange} total={paginationInfo.total} />
      <ReportList reports={reports} pagination={paginationInfo} onPageChange={(page) => setPagination((prev) => ({ ...prev, page }))} onPerPageChange={(perPage) => setPagination((prev) => ({ ...prev, perPage, page: 1 }))} isLoading={isLoading} error={error} onRetry={refetch} viewMode={viewMode} />
    </PageContainer>
  );
};

export default Reports;
```

- [ ] **Step 2: Delete old ReportCard**

```bash
git rm frontend/src/components/reports/ReportCard.jsx
```

- [ ] **Step 3: Full lint**

Run: `npx eslint src/`
Expected: 0 errors, 0 warnings

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: Task 5 — Reports page with viewMode toggle, delete old ReportCard"
```

---

## Execution

Plan complete. After user confirmation, execute inline (recommended for this scope).
