import { useState, useEffect } from "react";
import { motion } from "framer-motion";
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
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
    <GlassCard className="mb-6" noPadding>
      <div className="p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search reports by project or repo..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl
                text-white placeholder-gray-500 text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
            />
          </div>

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

          <select
            value={sort}
            onChange={(e) => onSortChange(e.target.value)}
            className="px-3 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white text-sm
              focus:outline-none focus:ring-2 focus:ring-cyan-500/50 appearance-none cursor-pointer
              [&>option]:bg-gray-800 [&>option]:text-white"
          >
            {sortOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

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
                  onClick={() => onFilterChange({ ...filters, [f.key]: "" })}
                  className="hover:text-white"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            ))}
            <button
              onClick={() => {
                onFilterChange({ search: "", status: "" });
                setSearchInput("");
              }}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Clear all
            </button>
          </div>
        )}

        {total !== undefined && (
          <p className="text-xs text-gray-500">
            {total} report{total !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </GlassCard>
    </motion.div>
  );
};

export default ReportFilters;
