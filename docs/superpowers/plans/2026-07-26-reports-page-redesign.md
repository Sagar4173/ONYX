# Reports Page Redesign Implementation Plan

> **For agentic workers:** Use subagent-driven-development or executing-plans.

**Goal:** Fix Reports listing page (pagination, debounce, sort), clean up ReportDetails (dedup badges, remove dead code), then fix all 52 lint warnings.

**Architecture:** Similar pattern to ProjectManagement — orchestrator + sub-components pattern for Reports listing. Detail page cleanup is surgical.

**Tech Stack:** React 18, TanStack React Query v5, Tailwind CSS, Heroicons

---
### Task 1: ReportCard Component

**Files:**
- Create: `src/components/reports/ReportCard.jsx`

```jsx
import { Link } from "react-router-dom";
import { ChevronRightIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import { Badge } from "../../styles/components";

const statusConfig = {
  completed: { badge: "success", label: "Completed" },
  running: { badge: "warning", label: "Running" },
  pending: { badge: "info", label: "Pending" },
  failed: { badge: "danger", label: "Failed" },
};

const scanTypeIcons = {
  sast: "🔍",
  secrets: "🔑",
  dependency: "📦",
  container: "🐳",
  iac: "🏗️",
};

const ReportCard = ({ report }) => {
  const status = statusConfig[report.status] || statusConfig.pending;
  const scanType = report.scan_type || report.type || "sast";

  return (
    <Link
      to={`/report/${report.id}`}
      className="group flex items-center gap-4 p-4 bg-gray-900/50 border border-gray-800/50 rounded-xl
        hover:border-gray-700/50 hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200"
    >
      <div className="p-3 rounded-2xl bg-gradient-to-r from-violet-500 to-purple-600 shadow-lg flex-shrink-0">
        <DocumentTextIcon className="w-6 h-6 text-white" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-white font-semibold truncate">
            {report.project_name || report.repository_url?.replace(/^https?:\/\//, "") || "Untitled"}
          </h3>
          <Badge variant={status.badge} size="xs">{status.label}</Badge>
        </div>
        {report.repository_url && (
          <p className="text-gray-500 text-xs truncate font-mono mb-1">
            {report.repository_url.replace(/^https?:\/\//, "")}
          </p>
        )}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{scanTypeIcons[scanType] || "🔍"} {scanType.toUpperCase()}</span>
          {report.created_at && <span>{new Date(report.created_at).toLocaleDateString()}</span>}
        </div>
      </div>

      {/* Severity badges */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {report.critical_count > 0 && <Badge variant="critical" size="xs">{report.critical_count}</Badge>}
        {report.high_count > 0 && <Badge variant="high" size="xs">{report.high_count}</Badge>}
        {report.medium_count > 0 && <Badge variant="medium" size="xs">{report.medium_count}</Badge>}
        {!report.critical_count && !report.high_count && !report.medium_count && (
          <Badge variant="success" size="xs">Clean</Badge>
        )}
      </div>

      <ChevronRightIcon className="w-5 h-5 text-gray-600 group-hover:text-gray-400 transition-colors flex-shrink-0" />
    </Link>
  );
};

export default ReportCard;
```

- [ ] **Step 1:** Create file, run eslint, verify 0 errors.

---
### Task 2: ReportFilters Component

**Files:**
- Create: `src/components/reports/ReportFilters.jsx`

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
            <input type="text" value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search reports by project or repo..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl
                text-white placeholder-gray-500 text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
          </div>

          <select value={filters.status} onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white">
            {statusOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          <select value={sort} onChange={(e) => onSortChange(e.target.value)}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white">
            {sortOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        {activeFilters.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {activeFilters.map((f) => (
              <span key={f.key} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                {f.label}
                <button onClick={() => onFilterChange({ ...filters, [f.key]: "" })} className="hover:text-white">
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            ))}
            <button onClick={() => { onFilterChange({ search: "", status: "" }); setSearchInput(""); }}
              className="text-xs text-gray-500 hover:text-gray-300">Clear all</button>
          </div>
        )}

        {total !== undefined && <p className="text-xs text-gray-500">{total} report{total !== 1 ? "s" : ""}</p>}
      </div>
    </GlassCard>
  );
};

export default ReportFilters;
```

- [ ] **Step 1:** Create file, run eslint, verify 0 errors.

---
### Task 3: ReportList Component

**Files:**
- Create: `src/components/reports/ReportList.jsx`

```jsx
import { ChevronLeftIcon, ChevronRightIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import { Button, Skeleton } from "../../styles/components";
import { EmptyState } from "../../styles/components";
import ReportCard from "./ReportCard";

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

const ReportList = ({ reports, pagination, onPageChange, onPerPageChange, isLoading, error, onRetry }) => {
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

  if (isLoading) return <LoadingList />;

  if (!reports || reports.length === 0) {
    return (
      <EmptyState
        icon={DocumentTextIcon}
        title="No reports found"
        description="Reports will appear here once scans are completed."
      />
    );
  }

  return (
    <div>
      <div className="space-y-3">
        {reports.map((report) => <ReportCard key={report.id} report={report} />)}
      </div>

      {pagination && pagination.totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-800/50">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              Showing {((pagination.page - 1) * pagination.perPage) + 1}–
              {Math.min(pagination.page * pagination.perPage, pagination.total)} of {pagination.total}
            </span>
            <select value={pagination.perPage}
              onChange={(e) => onPerPageChange?.(Number(e.target.value))}
              className="px-2 py-1 bg-gray-800 border border-gray-700/50 rounded-lg text-xs text-gray-300
                focus:outline-none focus:ring-1 focus:ring-cyan-500/50 [&>option]:bg-gray-800">
              <option value={12}>12 / page</option>
              <option value={24}>24 / page</option>
              <option value={48}>48 / page</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <button onClick={() => onPageChange?.(pagination.page - 1)} disabled={pagination.page <= 1}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 transition-all">
              <ChevronLeftIcon className="w-4 h-4" />
            </button>
            {Array.from({ length: pagination.totalPages }, (_, i) => i + 1)
              .filter((p) => p === 1 || p === pagination.totalPages || Math.abs(p - pagination.page) <= 1)
              .map((p, idx, arr) => (
                <span key={p} className="flex items-center">
                  {idx > 0 && arr[idx - 1] !== p - 1 && <span className="px-1 text-gray-600 text-xs">...</span>}
                  <button onClick={() => onPageChange?.(p)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                      p === pagination.page
                        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                        : "text-gray-400 hover:text-white hover:bg-gray-800"
                    }`}>{p}</button>
                </span>
              ))}
            <button onClick={() => onPageChange?.(pagination.page + 1)} disabled={pagination.page >= pagination.totalPages}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 transition-all">
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

- [ ] **Step 1:** Create file, run eslint, verify 0 errors.

---
### Task 4: Rewrite Reports.jsx as Orchestrator

**Files:**
- Modify: `src/pages/Reports.jsx` (currently 304 lines, rewrite completely)

```jsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowPathIcon } from "@heroicons/react/24/outline";
import { Button } from "../styles/components";
import { PageContainer, PageHeader } from "../layouts/UIComponents";
import { reportsAPI } from "../services/api";
import { DocumentTextIcon } from "@heroicons/react/24/outline";
import ReportFilters from "../components/reports/ReportFilters";
import ReportList from "../components/reports/ReportList";

const Reports = () => {
  const [filters, setFilters] = useState({ search: "", status: "" });
  const [sort, setSort] = useState("newest");
  const [pagination, setPagination] = useState({ page: 1, perPage: 24 });

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["reports", filters, sort, pagination],
    queryFn: () => reportsAPI.getReports({
      ...filters,
      sort_by: sort === "newest" ? "created_at" : "created_at",
      sort_order: sort === "newest" ? "desc" : "asc",
      page: pagination.page,
      per_page: pagination.perPage,
    }).then((res) => res.data || res),
  });

  const reports = data?.reports ?? data ?? [];
  const paginationInfo = data?.pagination || { page: 1, perPage: 24, total: reports.length, totalPages: 1 };

  return (
    <PageContainer>
      <PageHeader
        title="Scan Reports"
        description="View detailed security scan results"
        icon={DocumentTextIcon}
        breadcrumb={["Reports"]}
        actions={
          <Button variant="ghost" leftIcon={<ArrowPathIcon className="w-4 h-4" />}
            onClick={refetch} isLoading={isFetching}>Refresh</Button>
        }
      />

      <ReportFilters
        filters={filters} onFilterChange={(next) => { setFilters(next); setPagination((p) => ({ ...p, page: 1 })); }}
        sort={sort} onSortChange={(next) => { setSort(next); setPagination((p) => ({ ...p, page: 1 })); }}
        total={paginationInfo.total}
      />

      <ReportList
        reports={reports}
        pagination={paginationInfo}
        onPageChange={(page) => setPagination((prev) => ({ ...prev, page }))}
        onPerPageChange={(perPage) => setPagination((prev) => ({ ...prev, perPage, page: 1 }))}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
      />
    </PageContainer>
  );
};

export default Reports;
```

- [ ] **Step 1:** Read current file, then overwrite with new content, run eslint, verify 0 errors.

---
### Task 5: ReportDetails Cleanup

**Files:**
- Modify: `src/components/reports/ReportDetails.jsx`
- Modify: `src/components/reports/ReportSummary.jsx`
- Modify: `src/components/reports/VulnerabilityList.jsx`

**Sub-tasks:**

- [ ] **5a: Remove duplicate `SeverityBadgeInline` from `ReportSummary.jsx`**

Read `ReportSummary.jsx`. Find the `SeverityBadgeInline` component definition. Remove it and replace its usage with the import from `ReportBadges.jsx` (`import { SeverityBadge } from "./ReportBadges"`).

- [ ] **5b: Remove duplicate `SeverityBadgeInline` from `VulnerabilityList.jsx`**

Same approach — remove local `SeverityBadgeInline`, import `SeverityBadge` from `ReportBadges.jsx`.

- [ ] **5c: Remove unused state from `ReportDetails.jsx`**

Read `ReportDetails.jsx`. Find and remove these state declarations:
```jsx
const [_selectedFinding, _setSelectedFinding] = useState(null);
const [_expandedFindings, _setExpandedFindings] = useState(new Set());
const [_showCodeContext, _setShowCodeContext] = useState(false);
```

- [ ] **5d: Remove unreachable "remediation" tab rendering**

In `ReportDetails.jsx`, find the block that renders when `activeTab === "remediation"` and remove it since there's no tab button for remediation.

- [ ] **5e: Fix `key={index}` patterns**

Find places using `key={index}` in ReportDetails.jsx map() calls and replace with `key={item.id || item.name || item.scanner}`.

- [ ] After all sub-tasks, run `npx eslint src/components/reports/ReportDetails.jsx src/components/reports/ReportSummary.jsx src/components/reports/VulnerabilityList.jsx` and verify 0 errors.

---
### Task 6: Lint Warning Cleanup

**Files:** All files with warnings from `npm run lint`

Run `npm run lint` to get the current list, then fix each category:

1. **Unused imports/variables** (most common): Remove the unused symbol, or prefix with `_` if it's a destructured prop that must exist
2. **`react-hooks/exhaustive-deps`**: For effects that intentionally exclude deps, add `// eslint-disable-next-line react-hooks/exhaustive-deps`. For real bugs, add the missing deps.
3. **`react-refresh/only-export-components`**: Where a file exports both components and non-components, add `// eslint-disable-next-line react-refresh/only-export-components`

Order of files to fix (by warning count):
1. `Reports.jsx` (already rewritten in Task 4 — verify clean)
2. Various auth components (unused imports)
3. API service files (unused variables)
4. Report components (unused imports, deduped badges)
5. Test files (unused imports)
6. All remaining

- [ ] Run `npm run lint` and record number of warnings
- [ ] Fix all unused imports/variables across the project
- [ ] Fix all `react-hooks/exhaustive-deps` warnings
- [ ] Fix all `react-refresh/only-export-components` warnings  
- [ ] Run `npm run lint` again and verify 0 errors, 0 warnings
- [ ] Run `npm run build` and verify it passes
