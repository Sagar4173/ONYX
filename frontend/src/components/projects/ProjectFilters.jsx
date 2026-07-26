import { useState, useEffect } from "react";
import { MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";
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

const ProjectFilters = ({
  filters,
  onFilterChange,
  sort,
  onSortChange,
  viewMode,
  onViewModeChange,
  categories,
  priorities,
  total,
}) => {
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
  if (filters.category)
    activeFilters.push({ key: "category", label: `Category: ${filters.category}` });
  if (filters.priority)
    activeFilters.push({ key: "priority", label: `Priority: ${filters.priority}` });

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
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white"
          >
            {statusOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>

          {categories?.length > 0 && (
            <select
              value={filters.category}
              onChange={(e) => onFilterChange({ ...filters, category: e.target.value })}
              className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
                [&>option]:bg-gray-800 [&>option]:text-white"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          )}

          {priorities?.length > 0 && (
            <select
              value={filters.priority}
              onChange={(e) => onFilterChange({ ...filters, priority: e.target.value })}
              className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
                [&>option]:bg-gray-800 [&>option]:text-white"
            >
              <option value="">All Priorities</option>
              {priorities.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          )}

          {/* Sort */}
          <select
            value={sort?.field || "name"}
            onChange={(e) => onSortChange?.({ ...sort, field: e.target.value })}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white"
          >
            {sortOptions.map((o) => (
              <option key={o.value} value={o.value}>
                Sort: {o.label}
              </option>
            ))}
          </select>

          {/* Grid/List toggle */}
          <div className="flex items-center border border-gray-700/50 rounded-xl overflow-hidden">
            <button
              onClick={() => onViewModeChange("grid")}
              className={`p-2 transition-colors ${viewMode === "grid" ? "bg-gray-700/80 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800/50"}`}
              title="Grid view"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                />
              </svg>
            </button>
            <button
              onClick={() => onViewModeChange("list")}
              className={`p-2 transition-colors ${viewMode === "list" ? "bg-gray-700/80 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800/50"}`}
              title="List view"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Active filter chips */}
        {activeFilters.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {activeFilters.map((f) => (
              <span
                key={f.key}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
              >
                {f.label}
                <button
                  onClick={() => removeFilter(f.key)}
                  className="hover:text-white transition-colors"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            ))}
            <button
              onClick={clearAll}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              Clear all
            </button>
          </div>
        )}

        {total !== undefined && (
          <p className="text-xs text-gray-500">
            {total} project{total !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </GlassCard>
  );
};

export default ProjectFilters;
