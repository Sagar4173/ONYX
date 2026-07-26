# Project Management Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan.

**Goal:** Split the 1287-line `ProjectManagement.jsx` monolith into 7 focused component files, add proper pagination, bulk actions, sort, debounced search, list view, and loading states.

**Architecture:** Orchestrator pattern — `ProjectManagement.jsx` owns all state and passes it down via props. Each sub-component handles its own rendering and states independently. Data fetching via React Query with cache invalidation at the orchestrator level.

**Tech Stack:** React 18, React Router v6, TanStack React Query v5, Tailwind CSS, Framer Motion (`AnimatePresence`), Heroicons

## Global Constraints

- No new dependencies — use existing packages
- Follow ONYX design language: dark glass, cyan/violet gradients, gray-900/800/700 palette
- All new components go under `src/components/projects/`
- Use existing `StatCard`, `Button`, `Badge`, `Skeleton`, `Modal`, `EmptyState` from `src/styles/components.jsx`
- Use existing `PageContainer`, `PageHeader`, `GlassCard` from `src/layouts/UIComponents.jsx`
- Use existing `projectsAPI` from `src/services/api.js`
- Keep `ProjectDetails.jsx` untouched
- Every component handles loading, empty, error states

---
### Task 1: ProjectCard Component

**Files:**
- Create: `src/components/projects/ProjectCard.jsx`

**Interfaces:**
- Consumes: project object shape from `projectsAPI.getProjects()` response
- Produces: `<ProjectCard project={object} selected={bool} onSelect={fn} onView={fn} onEdit={fn} onDelete={fn} />`

- [ ] **Step 1: Create ProjectCard component**

```jsx
import { useState } from "react";
import { EllipsisVerticalIcon, PencilIcon, TrashIcon, PlayIcon } from "@heroicons/react/24/outline";
import { Badge } from "../../styles/components";
import { motion } from "framer-motion";

const priorityConfig = {
  critical: { color: "from-red-500 to-orange-500", badge: "danger" },
  high: { color: "from-orange-500 to-amber-500", badge: "warning" },
  medium: { color: "from-yellow-500 to-amber-500", badge: "warning" },
  low: { color: "from-cyan-500 to-blue-500", badge: "info" },
};

const statusConfig = {
  active: { border: "border-l-green-500", dot: "success" },
  inactive: { border: "border-l-yellow-500", dot: "warning" },
  archived: { border: "border-l-gray-500", dot: "neutral" },
};

const getScoreColor = (score) => {
  if (score >= 80) return { stroke: "#22c55e", text: "text-green-400" };
  if (score >= 50) return { stroke: "#eab308", text: "text-yellow-400" };
  return { stroke: "#ef4444", text: "text-red-400" };
};

const severityDots = [
  { key: "critical", color: "bg-red-500", label: "Critical" },
  { key: "high", color: "bg-orange-500", label: "High" },
  { key: "medium", color: "bg-yellow-500", label: "Medium" },
  { key: "low", color: "bg-cyan-500", label: "Low" },
];

const ProjectCard = ({ project, selected, onSelect, onView, onEdit, onDelete }) => {
  const [showActions, setShowActions] = useState(false);
  const status = statusConfig[project.status] || statusConfig.active;
  const priority = priorityConfig[project.priority] || priorityConfig.low;
  const score = project.security_score ?? 0;
  const scoreColor = getScoreColor(score);
  const issues = project.vulnerability_count || {};
  const totalIssues = (issues.critical || 0) + (issues.high || 0) + (issues.medium || 0) + (issues.low || 0);
  const displayTags = (project.tags || []).slice(0, 3);
  const extraTags = (project.tags || []).length - 3;

  const repoDisplay = project.repository_url
    ? project.repository_url.replace(/^https?:\/\//, "").replace(/\/$/, "")
    : "";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`group relative bg-gray-900/50 border border-gray-800/50 rounded-xl
        hover:border-gray-700/50 hover:-translate-y-0.5 hover:shadow-lg
        transition-all duration-200 cursor-pointer border-l-[3px] ${status.border}
        ${selected ? "ring-2 ring-cyan-500/50 border-cyan-500/50" : ""}`}
      onClick={() => onView?.(project)}
    >
      <div className="p-4">
        {/* Top row: checkbox + icon + name + actions */}
        <div className="flex items-start gap-3">
          {onSelect && (
            <div className="pt-1" onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={selected}
                onChange={() => onSelect(project.id)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500
                  focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
              />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-white font-semibold truncate">{project.name}</h3>
              <Badge variant={priority.badge} size="xs">{project.priority}</Badge>
              <Badge variant={status.dot === "success" ? "success" : status.dot === "warning" ? "warning" : "default"} size="xs">{project.status}</Badge>
            </div>
            {project.description && (
              <p className="text-gray-400 text-sm line-clamp-2 mb-2">{project.description}</p>
            )}
            {repoDisplay && (
              <p className="text-gray-500 text-xs truncate mb-3 font-mono">{repoDisplay}</p>
            )}
          </div>

          {/* Actions dropdown */}
          <div className="relative opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-all"
            >
              <EllipsisVerticalIcon className="w-5 h-5" />
            </button>
            {showActions && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowActions(false)} />
                <div className="absolute right-0 top-full mt-1 w-40 z-20 bg-gray-800 border border-gray-700 rounded-xl shadow-xl py-1">
                  <button onClick={() => { setShowActions(false); onEdit?.(project); }} className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 transition-colors">
                    <PencilIcon className="w-4 h-4" /> Edit
                  </button>
                  <button onClick={() => { setShowActions(false); onDelete?.(project); }} className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-700/50 transition-colors">
                    <TrashIcon className="w-4 h-4" /> Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Bottom row: score + severity + tags */}
        <div className="flex items-end justify-between mt-3 pt-3 border-t border-gray-800/50">
          {/* Score ring */}
          <div className="flex items-center gap-3">
            <div className="relative w-12 h-12 flex-shrink-0">
              <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#374151" strokeWidth="3" />
                <circle cx="18" cy="18" r="15.5" fill="none" stroke={scoreColor.stroke} strokeWidth="3"
                  strokeDasharray={`${(score / 100) * 97.4} 97.4`} strokeLinecap="round" />
              </svg>
              <span className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${scoreColor.text}`}>
                {score}
              </span>
            </div>

            {/* Severity dots */}
            <div className="flex items-center gap-1.5">
              {severityDots.map(({ key, color, label }) => (
                <div key={key} className="flex items-center gap-1" title={`${label}: ${issues[key] || 0}`}>
                  <span className={`w-2 h-2 rounded-full ${color} ${(issues[key] || 0) > 0 ? "opacity-100" : "opacity-20"}`} />
                  <span className="text-xs text-gray-500">{issues[key] || 0}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tags + last scan */}
          <div className="text-right">
            {displayTags.length > 0 && (
              <div className="flex items-center gap-1 mb-1 justify-end flex-wrap">
                {displayTags.map((tag) => (
                  <span key={tag} className="text-xs px-1.5 py-0.5 rounded-md bg-gray-800/80 text-gray-400 border border-gray-700/50">{tag}</span>
                ))}
                {extraTags > 0 && <span className="text-xs text-gray-500">+{extraTags}</span>}
              </div>
            )}
            {project.last_scan && (
              <p className="text-xs text-gray-500">Scanned {new Date(project.last_scan).toLocaleDateString()}</p>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ProjectCard;
```

- [ ] **Step 2: Verify the file is syntactically valid**

Run: `npx eslint src/components/projects/ProjectCard.jsx`
Expected: 0 errors (warnings ok)

---
### Task 2: ProjectRow Component

**Files:**
- Create: `src/components/projects/ProjectRow.jsx`

- [ ] **Step 1: Create ProjectRow component**

```jsx
import { useState } from "react";
import { EllipsisVerticalIcon, PencilIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Badge, StatusDot } from "../../styles/components";

const priorityBadgeMap = { critical: "danger", high: "warning", medium: "warning", low: "info" };
const statusDotMap = { active: "success", inactive: "warning", archived: "neutral" };

const getScoreColor = (score) => {
  if (score >= 80) return "text-green-400";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
};

const severityDotMap = [
  { key: "critical", color: "bg-red-500" },
  { key: "high", color: "bg-orange-500" },
  { key: "medium", color: "bg-yellow-500" },
  { key: "low", color: "bg-cyan-500" },
];

const ProjectRow = ({ project, selected, onSelect, onView, onEdit, onDelete }) => {
  const [showActions, setShowActions] = useState(false);
  const issues = project.vulnerability_count || {};
  const totalIssues = (issues.critical || 0) + (issues.high || 0) + (issues.medium || 0) + (issues.low || 0);

  return (
    <div
      className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer
        hover:bg-gray-800/50 border border-transparent hover:border-gray-700/50
        ${selected ? "bg-gray-800/50 border-gray-700/50" : ""}`}
      onClick={() => onView?.(project)}
    >
      {onSelect && (
        <div onClick={(e) => e.stopPropagation()}>
          <input type="checkbox" checked={selected}
            onChange={() => onSelect(project.id)}
            className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer" />
        </div>
      )}

      <StatusDot status={statusDotMap[project.status] || "neutral"} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium truncate">{project.name}</span>
          <Badge variant={priorityBadgeMap[project.priority] || "default"} size="xs">{project.priority}</Badge>
        </div>
        {project.description && (
          <p className="text-gray-500 text-sm truncate">{project.description}</p>
        )}
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className={`font-mono font-bold ${getScoreColor(project.security_score)}`}>
          {project.security_score ?? "—"}
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        {severityDotMap.map(({ key, color }) => (
          <span key={key} className={`w-2 h-2 rounded-full ${color} ${(issues[key] || 0) > 0 ? "" : "opacity-20"}`}
            title={`${key}: ${issues[key] || 0}`} />
        ))}
      </div>

      <span className="text-sm text-gray-500 w-24 text-right">
        {project.last_scan ? new Date(project.last_scan).toLocaleDateString() : "—"}
      </span>

      <div className="relative" onClick={(e) => e.stopPropagation()}>
        <button onClick={() => setShowActions(!showActions)}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-all">
          <EllipsisVerticalIcon className="w-5 h-5" />
        </button>
        {showActions && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowActions(false)} />
            <div className="absolute right-0 top-full mt-1 w-40 z-20 bg-gray-800 border border-gray-700 rounded-xl shadow-xl py-1">
              <button onClick={() => { setShowActions(false); onEdit?.(project); }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50">
                <PencilIcon className="w-4 h-4" /> Edit
              </button>
              <button onClick={() => { setShowActions(false); onDelete?.(project); }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-700/50">
                <TrashIcon className="w-4 h-4" /> Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProjectRow;
```

- [ ] **Step 2: Verify lint**

Run: `npx eslint src/components/projects/ProjectRow.jsx`
Expected: 0 errors

---
### Task 3: ProjectStatsBar Component

**Files:**
- Create: `src/components/projects/ProjectStatsBar.jsx`

- [ ] **Step 1: Create ProjectStatsBar component**

```jsx
import { FolderIcon, PlayIcon, ShieldCheckIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { StatCard } from "../../styles/components";

const ProjectStatsBar = ({ analytics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 bg-gray-800/30 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        title="Total Projects"
        value={analytics.total_projects ?? analytics.totalProjects ?? 0}
        icon={<FolderIcon className="w-6 h-6 text-white" />}
        gradient="from-blue-500 to-cyan-500"
      />
      <StatCard
        title="Active Scans"
        value={analytics.active_scans ?? analytics.activeScans ?? 0}
        icon={<PlayIcon className="w-6 h-6 text-white" />}
        gradient="from-violet-500 to-purple-500"
      />
      <StatCard
        title="Avg Security Score"
        value={(analytics.average_score ?? analytics.averageScore ?? 0) + "%"}
        icon={<ShieldCheckIcon className="w-6 h-6 text-white" />}
        gradient="from-emerald-500 to-green-500"
      />
      <StatCard
        title="Open Issues"
        value={analytics.total_issues ?? analytics.totalIssues ?? 0}
        icon={<ExclamationTriangleIcon className="w-6 h-6 text-white" />}
        gradient="from-red-500 to-orange-500"
      />
    </div>
  );
};

export default ProjectStatsBar;
```

- [ ] **Step 2: Verify lint**

Run: `npx eslint src/components/projects/ProjectStatsBar.jsx`
Expected: 0 errors

---
### Task 4: ProjectFilters Component

**Files:**
- Create: `src/components/projects/ProjectFilters.jsx`

- [ ] **Step 1: Create ProjectFilters component**

```jsx
import { useState, useEffect } from "react";
import { MagnifyingGlassIcon, FunnelIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { GlassCard } from "../../layouts/UIComponents";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
];

const sortOptions = [
  { value: "name", label: "Name" },
  { value: "created_at", label: "Created" },
  { value: "last_scan", label: "Last Scan" },
  { value: "security_score", label: "Security Score" },
];

const ProjectFilters = ({ filters, onFilterChange, sort, onSortChange, viewMode, onViewModeChange, categories, priorities, total }) => {
  const [searchInput, setSearchInput] = useState(filters.search || "");

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== (filters.search || "")) {
        onFilterChange({ ...filters, search: searchInput });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setSearchInput(filters.search || "");
  }, [filters.search]);

  const activeFilters = [];
  if (filters.status) activeFilters.push({ key: "status", label: `Status: ${filters.status}` });
  if (filters.category) activeFilters.push({ key: "category", label: `Category: ${filters.category}` });
  if (filters.priority) activeFilters.push({ key: "priority", label: `Priority: ${filters.priority}` });

  const removeFilter = (key) => {
    onFilterChange({ ...filters, [key]: "" });
  };

  const clearAll = () => {
    onFilterChange({ search: "", status: "", category: "", priority: "" });
    setSearchInput("");
  };

  return (
    <GlassCard className="mb-6" noPadding>
      <div className="p-4 space-y-4">
        {/* Search + view toggle row */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search projects..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl
                text-white placeholder-gray-500 text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
            />
          </div>

          {/* Filter dropdowns */}
          <select value={filters.status} onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white">
            {statusOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          {categories?.length > 0 && (
            <select value={filters.category} onChange={(e) => onFilterChange({ ...filters, category: e.target.value })}
              className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
                [&>option]:bg-gray-800 [&>option]:text-white">
              <option value="">All Categories</option>
              {categories.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          )}

          {priorities?.length > 0 && (
            <select value={filters.priority} onChange={(e) => onFilterChange({ ...filters, priority: e.target.value })}
              className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
                [&>option]:bg-gray-800 [&>option]:text-white">
              <option value="">All Priorities</option>
              {priorities.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          )}

          {/* Sort */}
          <select value={sort?.field || "name"} onChange={(e) => onSortChange?.({ ...sort, field: e.target.value })}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white">
            {sortOptions.map((o) => <option key={o.value} value={o.value}>Sort: {o.label}</option>)}
          </select>

          {/* Grid/List toggle */}
          <div className="flex items-center border border-gray-700/50 rounded-xl overflow-hidden">
            <button onClick={() => onViewModeChange("grid")}
              className={`p-2 transition-colors ${viewMode === "grid" ? "bg-gray-700/80 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800/50"}`}
              title="Grid view">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
            </button>
            <button onClick={() => onViewModeChange("list")}
              className={`p-2 transition-colors ${viewMode === "list" ? "bg-gray-700/80 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800/50"}`}
              title="List view">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
          </div>
        </div>

        {/* Active filter chips */}
        {activeFilters.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {activeFilters.map((f) => (
              <span key={f.key} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                {f.label}
                <button onClick={() => removeFilter(f.key)} className="hover:text-white transition-colors">
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            ))}
            <button onClick={clearAll} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
              Clear all
            </button>
          </div>
        )}

        {total !== undefined && (
          <p className="text-xs text-gray-500">{total} project{total !== 1 ? "s" : ""}</p>
        )}
      </div>
    </GlassCard>
  );
};

export default ProjectFilters;
```

- [ ] **Step 2: Verify lint**

Run: `npx eslint src/components/projects/ProjectFilters.jsx`
Expected: 0 errors

---
### Task 5: ProjectForm Component (Unified Create/Edit)

**Files:**
- Create: `src/components/projects/ProjectForm.jsx`

- [ ] **Step 1: Create ProjectForm with useReducer pattern**

```jsx
import { useReducer, useEffect } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { XMarkIcon, PlusIcon } from "@heroicons/react/24/outline";
import { toast } from "react-hot-toast";
import { Modal, Button } from "../../styles/components";
import { projectsAPI } from "../../services/api";

const INITIAL_STATE = {
  name: "",
  description: "",
  category: "other",
  priority: "medium",
  repository: { url: "", branch: "main", access_token: "", scan_paths: ["/"], exclude_paths: [] },
  scan_config: { enabled_scanners: ["sast", "secrets"], auto_scan_on_push: false, scan_timeout_minutes: 60, fail_on_critical: false },
  tags: [],
};

function formReducer(state, action) {
  switch (action.type) {
    case "SET_FIELD":
      return { ...state, [action.field]: action.value };
    case "SET_REPO_FIELD":
      return { ...state, repository: { ...state.repository, [action.field]: action.value } };
    case "SET_SCAN_FIELD":
      return { ...state, scan_config: { ...state.scan_config, [action.field]: action.value } };
    case "TOGGLE_SCANNER":
      return {
        ...state,
        scan_config: {
          ...state.scan_config,
          enabled_scanners: state.scan_config.enabled_scanners.includes(action.scanner)
            ? state.scan_config.enabled_scanners.filter((s) => s !== action.scanner)
            : [...state.scan_config.enabled_scanners, action.scanner],
        },
      };
    case "ADD_TAG":
      if (!action.tag.trim() || state.tags.includes(action.tag.trim())) return state;
      return { ...state, tags: [...state.tags, action.tag.trim()] };
    case "REMOVE_TAG":
      return { ...state, tags: state.tags.filter((t) => t !== action.tag) };
    case "RESET":
      return { ...INITIAL_STATE };
    case "LOAD_PROJECT":
      return {
        ...INITIAL_STATE,
        name: action.project.name || "",
        description: action.project.description || "",
        category: action.project.category || "other",
        priority: action.project.priority || "medium",
        repository: {
          url: action.project.repository_url || "",
          branch: action.project.repository?.branch || "main",
          access_token: "",
          scan_paths: action.project.repository?.scan_paths || ["/"],
          exclude_paths: action.project.repository?.exclude_paths || [],
        },
        scan_config: {
          enabled_scanners: action.project.scan_config?.enabled_scanners || ["sast", "secrets"],
          auto_scan_on_push: action.project.scan_config?.auto_scan_on_push || false,
          scan_timeout_minutes: action.project.scan_config?.scan_timeout_minutes || 60,
          fail_on_critical: action.project.scan_config?.fail_on_critical || false,
        },
        tags: action.project.tags || [],
      };
    default:
      return state;
  }
}

const scanners = [
  { value: "sast", label: "SAST", description: "Static code analysis" },
  { value: "secrets", label: "Secrets", description: "Credential detection" },
  { value: "dependency", label: "Dependencies", description: "Vulnerable packages" },
  { value: "container", label: "Container", description: "Image scanning" },
  { value: "iac", label: "IaC", description: "Infrastructure as Code" },
];

const ProjectForm = ({ isOpen, onClose, project, onSuccess }) => {
  const [state, dispatch] = useReducer(formReducer, INITIAL_STATE);
  const queryClient = useQueryClient();

  const { data: templates } = useQuery({
    queryKey: ["projectTemplates"],
    queryFn: projectsAPI.getTemplateCategories,
  });

  useEffect(() => {
    if (project) {
      dispatch({ type: "LOAD_PROJECT", project });
    } else {
      dispatch({ type: "RESET" });
    }
  }, [project, isOpen]);

  const mutation = useMutation({
    mutationFn: project
      ? (data) => projectsAPI.updateProject(project.id, data)
      : (data) => projectsAPI.createProject(data),
    onSuccess: (data) => {
      toast.success(project ? "Project updated successfully!" : "Project created successfully!");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["projectAnalytics"] });
      onSuccess?.(data);
      onClose();
    },
    onError: (error) => {
      toast.error(error.message || `Failed to ${project ? "update" : "create"} project`);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!state.name.trim() || !state.repository.url.trim()) {
      toast.error("Project name and repository URL are required");
      return;
    }
    mutation.mutate(state);
  };

  return (
    <Modal size="xl" isOpen={isOpen} onClose={onClose} title="">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600">
            <PlusIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">{project ? "Edit Project" : "Create New Project"}</h2>
            <p className="text-gray-400 text-sm">{project ? "Update project configuration" : "Set up a new security scanning project"}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all">
          <XMarkIcon className="w-6 h-6" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <fieldset>
          <legend className="text-lg font-semibold text-white mb-4">Basic Information</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Project Name *</label>
              <input type="text" value={state.name}
                onChange={(e) => dispatch({ type: "SET_FIELD", field: "name", value: e.target.value })}
                placeholder="My Awesome Project"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
              <select value={state.category}
                onChange={(e) => dispatch({ type: "SET_FIELD", field: "category", value: e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white">
                {templates?.categories?.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea value={state.description}
              onChange={(e) => dispatch({ type: "SET_FIELD", field: "description", value: e.target.value })}
              placeholder="Describe your project..." rows={3}
              className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none transition-all" />
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
            <select value={state.priority}
              onChange={(e) => dispatch({ type: "SET_FIELD", field: "priority", value: e.target.value })}
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white">
              {templates?.priorities?.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </div>
        </fieldset>

        {/* Repository Configuration */}
        <fieldset>
          <legend className="text-lg font-semibold text-white mb-4">Repository</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Repository URL *</label>
              <input type="url" value={state.repository.url}
                onChange={(e) => dispatch({ type: "SET_REPO_FIELD", field: "url", value: e.target.value })}
                placeholder="https://github.com/org/project" required
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Branch</label>
              <input type="text" value={state.repository.branch}
                onChange={(e) => dispatch({ type: "SET_REPO_FIELD", field: "branch", value: e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Access Token</label>
              <input type="password" value={state.repository.access_token}
                onChange={(e) => dispatch({ type: "SET_REPO_FIELD", field: "access_token", value: e.target.value })}
                placeholder="Optional" autoComplete="off"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all" />
            </div>
          </div>
        </fieldset>

        {/* Security Scanners */}
        <fieldset>
          <legend className="text-lg font-semibold text-white mb-4">Security Scanners</legend>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {scanners.map((scanner) => {
              const isEnabled = state.scan_config.enabled_scanners.includes(scanner.value);
              return (
                <button key={scanner.value} type="button" onClick={() => dispatch({ type: "TOGGLE_SCANNER", scanner: scanner.value })}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    isEnabled
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-gray-800/50 border-gray-700/50 text-gray-400 hover:border-gray-600"
                  }`}>
                  <div className="text-xs font-semibold">{scanner.label}</div>
                  <div className="text-[10px] opacity-70">{scanner.description}</div>
                </button>
              );
            })}
          </div>
        </fieldset>

        {/* Scan Config */}
        <fieldset>
          <legend className="text-lg font-semibold text-white mb-4">Scan Configuration</legend>
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={state.scan_config.auto_scan_on_push}
                onChange={(e) => dispatch({ type: "SET_SCAN_FIELD", field: "auto_scan_on_push", value: e.target.checked })}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0" />
              <span className="text-sm text-gray-300">Auto-scan on push</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={state.scan_config.fail_on_critical}
                onChange={(e) => dispatch({ type: "SET_SCAN_FIELD", field: "fail_on_critical", value: e.target.checked })}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0" />
              <span className="text-sm text-gray-300">Fail build on critical findings</span>
            </label>
          </div>
        </fieldset>

        {/* Tags */}
        <fieldset>
          <legend className="text-lg font-semibold text-white mb-4">Tags</legend>
          <div className="flex items-center gap-2 mb-3">
            <input type="text" placeholder="Add a tag..." id="tag-input"
              className="flex-1 px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  const input = e.target;
                  dispatch({ type: "ADD_TAG", tag: input.value });
                  input.value = "";
                }
              }} />
          </div>
          {state.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {state.tags.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                  bg-gray-800 text-gray-300 border border-gray-700/50">
                  {tag}
                  <button type="button" onClick={() => dispatch({ type: "REMOVE_TAG", tag })} className="hover:text-white transition-colors">
                    <XMarkIcon className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </fieldset>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-700/50">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>
            {project ? "Save Changes" : "Create Project"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default ProjectForm;
```

- [ ] **Step 2: Verify lint**

Run: `npx eslint src/components/projects/ProjectForm.jsx`
Expected: 0 errors

---
### Task 6: ProjectDeleteDialog Component

**Files:**
- Create: `src/components/projects/ProjectDeleteDialog.jsx`

- [ ] **Step 1: Create ProjectDeleteDialog**

```jsx
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { Modal, Button } from "../../styles/components";

const ProjectDeleteDialog = ({ project, isOpen, onClose, onConfirm, isLoading }) => {
  return (
    <Modal size="sm" isOpen={isOpen} onClose={onClose} title="">
      <div className="text-center">
        <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
          <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Delete Project</h3>
        <p className="text-gray-400 text-sm mb-1">
          Are you sure you want to delete <span className="text-white font-medium">{project?.name}</span>?
        </p>
        <p className="text-gray-500 text-xs mb-6">
          This action cannot be undone. All scan data, reports, and configurations will be permanently removed.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="danger" onClick={onConfirm} isLoading={isLoading}>Delete</Button>
        </div>
      </div>
    </Modal>
  );
};

export default ProjectDeleteDialog;
```

- [ ] **Step 2: Verify lint**

Run: `npx eslint src/components/projects/ProjectDeleteDialog.jsx`
Expected: 0 errors

---
### Task 7: ProjectGrid Component

**Files:**
- Create: `src/components/projects/ProjectGrid.jsx`

- [ ] **Step 1: Create ProjectGrid with pagination, bulk actions, and all states**

```jsx
import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import { FolderIcon, ChevronLeftIcon, ChevronRightIcon, ArchiveBoxIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Button, Skeleton } from "../../styles/components";
import { EmptyState } from "../../styles/components";
import ProjectCard from "./ProjectCard";
import ProjectRow from "./ProjectRow";

const LoadingGrid = () => (
  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} className="bg-gray-800/30 border border-gray-800/50 rounded-xl p-4 space-y-3">
        <Skeleton variant="title" className="!w-3/4" />
        <Skeleton variant="text" className="!w-full" />
        <Skeleton variant="text" className="!w-1/2" />
        <div className="flex items-center gap-2 pt-2">
          <Skeleton className="!w-12 !h-12 !rounded-full" />
          <Skeleton variant="text" className="!w-20" />
        </div>
      </div>
    ))}
  </div>
);

const LoadingList = () => (
  <div className="space-y-2">
    {Array.from({ length: 5 }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 bg-gray-800/30 border border-gray-800/50 rounded-xl p-4">
        <Skeleton className="!w-4 !h-4 !rounded" />
        <Skeleton className="!w-3 !h-3 !rounded-full" />
        <div className="flex-1 space-y-1">
          <Skeleton variant="title" className="!w-1/3" />
          <Skeleton variant="text" className="!w-1/2" />
        </div>
        <Skeleton className="!w-12 !h-4" />
        <Skeleton className="!w-16 !h-4" />
        <Skeleton className="!w-8 !h-4" />
      </div>
    ))}
  </div>
);

const ProjectGrid = ({
  projects = [],
  viewMode = "grid",
  pagination,
  onPageChange,
  onPerPageChange,
  selectedIds = new Set(),
  onSelectionChange,
  onView,
  onEdit,
  onDelete,
  onBulkArchive,
  onBulkDelete,
  isLoading,
  isFetching,
  error,
  onRetry,
}) => {
  const [selectAll, setSelectAll] = useState(false);

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
          <FolderIcon className="w-10 h-10 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Failed to load projects</h3>
        <p className="text-gray-400 text-sm mb-4">{error.message || "An error occurred while fetching projects."}</p>
        <Button variant="primary" onClick={onRetry}>Try Again</Button>
      </div>
    );
  }

  if (isLoading) {
    return viewMode === "grid" ? <LoadingGrid /> : <LoadingList />;
  }

  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FolderIcon}
        title="No projects found"
        description="Get started by creating your first security scanning project."
        action={<Button variant="primary" gradient onClick={() => onView?.({ action: "create" })}>Create Project</Button>}
      />
    );
  }

  const toggleSelect = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id); else next.add(id);
    onSelectionChange?.(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === projects.length) {
      onSelectionChange?.(new Set());
    } else {
      onSelectionChange?.(new Set(projects.map((p) => p.id)));
    }
  };

  return (
    <div>
      {/* Bulk actions bar */}
      {selectedIds.size > 0 && (
        <div className="sticky top-0 z-10 mb-4 flex items-center justify-between px-4 py-3
          bg-gray-800/90 backdrop-blur-xl border border-gray-700/50 rounded-xl">
          <span className="text-sm text-gray-300">{selectedIds.size} selected</span>
          <div className="flex items-center gap-2">
            {onBulkArchive && (
              <Button variant="ghost" size="sm" leftIcon={<ArchiveBoxIcon className="w-4 h-4" />}
                onClick={() => onBulkArchive(selectedIds)}>Archive</Button>
            )}
            {onBulkDelete && (
              <Button variant="danger" size="sm" leftIcon={<TrashIcon className="w-4 h-4" />}
                onClick={() => onBulkDelete(selectedIds)}>Delete</Button>
            )}
          </div>
        </div>
      )}

      {/* Select all toggle for list view */}
      {viewMode === "list" && (
        <div className="flex items-center gap-4 px-4 py-2 mb-2">
          <input type="checkbox"
            checked={selectedIds.size === projects.length && projects.length > 0}
            onChange={toggleSelectAll}
            className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer" />
          <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Select All</span>
        </div>
      )}

      {/* Grid/List content */}
      <div className={viewMode === "grid"
        ? "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4"
        : "space-y-1"}>
        <AnimatePresence mode="popLayout">
          {projects.map((project) =>
            viewMode === "grid" ? (
              <ProjectCard key={project.id} project={project}
                selected={selectedIds.has(project.id)} onSelect={toggleSelect}
                onView={onView} onEdit={onEdit} onDelete={onDelete} />
            ) : (
              <ProjectRow key={project.id} project={project}
                selected={selectedIds.has(project.id)} onSelect={toggleSelect}
                onView={onView} onEdit={onEdit} onDelete={onDelete} />
            )
          )}
        </AnimatePresence>
      </div>

      {/* Refetching overlay */}
      {isFetching && !isLoading && (
        <div className="flex justify-center py-4">
          <div className="w-5 h-5 border-2 border-gray-600 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      )}

      {/* Pagination */}
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
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
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
                    }`}>
                    {p}
                  </button>
                </span>
              ))}
            <button onClick={() => onPageChange?.(pagination.page + 1)} disabled={pagination.page >= pagination.totalPages}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
              <ChevronRightIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectGrid;
```

- [ ] **Step 2: Verify lint**

Run: `npx eslint src/components/projects/ProjectGrid.jsx`
Expected: 0 errors

---
### Task 8: Rewrite ProjectManagement Orchestrator

**Files:**
- Modify: `src/components/projects/ProjectManagement.jsx`
- Delete (old inline components): removed from same file

- [ ] **Step 1: Rewrite ProjectManagement.jsx as orchestrator**

```jsx
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PlusIcon } from "@heroicons/react/24/outline";
import { toast } from "react-hot-toast";
import { Button } from "../../styles/components";
import { PageContainer, PageHeader } from "../../layouts/UIComponents";
import { projectsAPI } from "../../services/api";
import { UsersIcon } from "@heroicons/react/24/outline";
import ProjectStatsBar from "./ProjectStatsBar";
import ProjectFilters from "./ProjectFilters";
import ProjectGrid from "./ProjectGrid";
import ProjectForm from "./ProjectForm";
import ProjectDeleteDialog from "./ProjectDeleteDialog";
import { useAuth } from "../auth";

const ProjectManagement = () => {
  useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // View state
  const [viewMode, setViewMode] = useState("grid");

  // Filter + sort state
  const [filters, setFilters] = useState({ search: "", status: "", category: "", priority: "" });
  const [sort, setSort] = useState({ field: "name" });

  // Pagination state
  const [pagination, setPagination] = useState({ page: 1, perPage: 24 });

  // Selection
  const [selectedIds, setSelectedIds] = useState(new Set());

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [deletingProject, setDeletingProject] = useState(null);

  // Data
  const { data: projectsData, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ["projects", filters, sort, pagination],
    queryFn: () => projectsAPI.getProjects({
      ...filters,
      sort_by: sort.field,
      page: pagination.page,
      per_page: pagination.perPage,
    }).then((res) => res.data || res),
  });

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["projectAnalytics"],
    queryFn: () => projectsAPI.getAnalyticsOverview().then((res) => res.data || res),
  });

  const { data: templates } = useQuery({
    queryKey: ["projectTemplates"],
    queryFn: projectsAPI.getTemplateCategories,
  });

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: (id) => projectsAPI.deleteProject(id),
    onSuccess: () => {
      toast.success("Project deleted");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["projectAnalytics"] });
      setDeletingProject(null);
    },
    onError: (err) => toast.error(err.message || "Failed to delete project"),
  });

  const bulkArchiveMutation = useMutation({
    mutationFn: (ids) => Promise.all(ids.map((id) => projectsAPI.updateProject(id, { status: "archived" }))),
    onSuccess: () => {
      toast.success("Projects archived");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setSelectedIds(new Set());
    },
    onError: (err) => toast.error(err.message || "Failed to archive projects"),
  });

  const projects = projectsData?.projects ?? projectsData ?? [];
  const paginationInfo = projectsData?.pagination || { page: 1, perPage: 24, total: projects.length, totalPages: 1, has_more: false };

  const handleView = useCallback((project) => {
    if (project?.action === "create") { setShowCreateModal(true); return; }
    if (project?.id) navigate(`/project/${project.id}`);
  }, [navigate]);

  const handleCreate = () => setShowCreateModal(true);
  const handleEdit = (project) => setEditingProject(project);
  const handleDelete = (project) => setDeletingProject(project);

  const handleFilterChange = (next) => {
    setFilters(next);
    setPagination((prev) => ({ ...prev, page: 1 }));
    setSelectedIds(new Set());
  };

  const handleSortChange = (next) => {
    setSort(next);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleBulkDelete = (ids) => {
    if (window.confirm(`Delete ${ids.size} selected projects?`)) {
      Promise.all([...ids].map((id) => projectsAPI.deleteProject(id)))
        .then(() => {
          toast.success(`Deleted ${ids.size} projects`);
          queryClient.invalidateQueries({ queryKey: ["projects"] });
          queryClient.invalidateQueries({ queryKey: ["projectAnalytics"] });
          setSelectedIds(new Set());
        })
        .catch((err) => toast.error(err.message || "Failed to delete projects"));
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title="Projects"
        description="Manage your security scanning projects"
        icon={UsersIcon}
        breadcrumb={["Projects"]}
        actions={
          <Button variant="primary" gradient leftIcon={<PlusIcon className="w-5 h-5" />} onClick={handleCreate}>
            New Project
          </Button>
        }
      />

      <ProjectStatsBar analytics={analytics} isLoading={analyticsLoading} />

      <ProjectFilters
        filters={filters} onFilterChange={handleFilterChange}
        sort={sort} onSortChange={handleSortChange}
        viewMode={viewMode} onViewModeChange={setViewMode}
        categories={templates?.categories} priorities={templates?.priorities}
        total={paginationInfo.total}
      />

      <ProjectGrid
        projects={projects}
        viewMode={viewMode}
        pagination={paginationInfo}
        onPageChange={(page) => setPagination((prev) => ({ ...prev, page }))}
        onPerPageChange={(perPage) => setPagination((prev) => ({ ...prev, perPage, page: 1 }))}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onView={handleView}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onBulkArchive={(ids) => bulkArchiveMutation.mutate([...ids])}
        onBulkDelete={handleBulkDelete}
        isLoading={isLoading}
        isFetching={isFetching}
        error={error}
        onRetry={refetch}
      />

      <ProjectForm
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        project={null}
        onSuccess={() => { setShowCreateModal(false); }}
      />

      {editingProject && (
        <ProjectForm
          isOpen={!!editingProject}
          onClose={() => setEditingProject(null)}
          project={editingProject}
          onSuccess={() => setEditingProject(null)}
        />
      )}

      <ProjectDeleteDialog
        project={deletingProject}
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={() => deleteMutation.mutate(deletingProject.id)}
        isLoading={deleteMutation.isPending}
      />
    </PageContainer>
  );
};

export default ProjectManagement;
```

- [ ] **Step 2: Remove old inline components from ProjectManagement.jsx**

The old file had inline `ProjectCard`, `CreateProjectModal`, `EditProjectModal` components. The rewrite replaces all of them. No manual cleanup needed since the file is completely rewritten.

- [ ] **Step 3: Verify lint**

Run: `npx eslint src/components/projects/ProjectManagement.jsx`
Expected: 0 errors

---
### Task 9: Update Exports and Cleanup

**Files:**
- Modify: `src/components/projects/index.js`

- [ ] **Step 1: Update index.js to export all new components**

```javascript
export { default as ProjectManagement } from "./ProjectManagement";
export { default as ProjectDetails } from "./ProjectDetails";
export { default as ProjectCard } from "./ProjectCard";
export { default as ProjectForm } from "./ProjectForm";
export { default as ProjectFilters } from "./ProjectFilters";
export { default as ProjectGrid } from "./ProjectGrid";
export { default as ProjectStatsBar } from "./ProjectStatsBar";
export { default as ProjectDeleteDialog } from "./ProjectDeleteDialog";
export { default as ProjectRow } from "./ProjectRow";
```

Note: Removes `ProjectList` export (it's a different component — a Security Scan Reports Dashboard, not a project management component). Verify nothing else imports `ProjectList` from this barrel.

- [ ] **Step 2: Check for any remaining references to old imports**

Search for any other files that import `ProjectList` from `../projects` or `./projects`.

Run: `rg "from.*projects.*ProjectList" src/`
Expected: only the index.js barrel and the file itself

Run: `rg "from.*projects" src/layouts/MainLayout.jsx`
Expected: only `ProjectManagement` and `ProjectDetails`

- [ ] **Step 3: Final build verification**

Run: `npx eslint src/components/projects/ --ext js,jsx`
Expected: 0 errors

Run: `npm run build`
Expected: Build succeeds (exit 0)
