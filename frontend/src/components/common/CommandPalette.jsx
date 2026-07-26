import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import Fuse from "fuse.js";
import { projectsAPI } from "../../services/api";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

const defaultActions = [
  { id: "nav-dashboard", label: "Go to Dashboard", category: "Navigation", path: "/dashboard" },
  { id: "nav-projects", label: "Go to Projects", category: "Navigation", path: "/projects" },
  { id: "nav-reports", label: "Go to Reports", category: "Navigation", path: "/reports" },
  { id: "nav-analytics", label: "Go to Analytics", category: "Navigation", path: "/analytics" },
  { id: "nav-compliance", label: "Go to Compliance", category: "Navigation", path: "/compliance" },
  { id: "nav-users", label: "Go to User Management", category: "Navigation", path: "/users" },
  { id: "nav-settings", label: "Go to Settings", category: "Navigation", path: "/settings" },
  { id: "nav-admin", label: "Go to Admin Dashboard", category: "Navigation", path: "/admin" },
];

export const CommandPalette = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const containerRef = useRef(null);
  const navigate = useNavigate();

  const { data: projectsData, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const res = await projectsAPI.list();
      return res.data?.projects || res.data || [];
    },
    enabled: isOpen,
    staleTime: 30000,
  });

  const projects = Array.isArray(projectsData) ? projectsData : [];

  const allItems = useMemo(() => {
    const projectItems = projects.map((p) => ({
      id: `project-${p.id || p._id}`,
      label: p.name,
      category: "Projects",
      path: `/project/${p.id || p._id}`,
    }));
    return [...defaultActions, ...projectItems];
  }, [projects]);

  const fuse = useMemo(
    () =>
      new Fuse(allItems, {
        keys: ["label", "category"],
        threshold: 0.4,
      }),
    [allItems]
  );

  const results = useMemo(() => {
    if (!query.trim()) return allItems;
    return fuse.search(query).map((r) => r.item);
  }, [query, fuse, allItems]);

  const grouped = useMemo(() => {
    const groups = {};
    results.forEach((item) => {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push(item);
    });
    return groups;
  }, [results]);

  const flattened = useMemo(() => {
    const items = [];
    Object.entries(grouped).forEach(([category, categoryItems]) => {
      items.push({ type: "category", label: category });
      categoryItems.forEach((item) => items.push({ type: "item", ...item }));
    });
    return items;
  }, [grouped]);

  const itemCount = flattened.filter((i) => i.type === "item").length;

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const container = containerRef.current;
    if (!container) return;
    const prevFocus = document.activeElement;
    const handleTab = (e) => {
      const focusable = container.querySelectorAll(FOCUSABLE);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleTab);
    return () => {
      document.removeEventListener("keydown", handleTab);
      prevFocus?.focus();
    };
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const selected = flattened[selectedIndex];
    if (selected?.type === "item" && listRef.current) {
      const el = listRef.current.querySelector(`[data-index="${selectedIndex}"]`);
      el?.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex, flattened]);

  const handleSelect = useCallback(
    (item) => {
      if (item.path) navigate(item.path);
      onClose();
    },
    [navigate, onClose]
  );

  const handleKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, flattened.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      const selected = flattened[selectedIndex];
      if (selected && selected.type === "item") handleSelect(selected);
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4"
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />
      <div className="relative w-full max-w-lg">
        <div className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-800/50">
            <MagnifyingGlassIcon
              className="w-5 h-5 text-gray-500 flex-shrink-0"
              aria-hidden="true"
            />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search pages, projects..."
              aria-label="Search pages and projects"
              className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-base"
            />
            <kbd
              className="hidden sm:flex items-center gap-1 text-[10px] px-2 py-1 bg-gray-700/50 rounded text-gray-500"
              aria-label="Close"
            >
              ESC
            </kbd>
          </div>

          <div
            ref={listRef}
            className="max-h-80 overflow-y-auto"
            role="listbox"
            aria-label="Search results"
          >
            {isLoading ? (
              <div className="px-5 py-4 space-y-3" role="status" aria-live="polite">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-4 animate-pulse">
                    <div className="w-8 h-8 rounded-full bg-gray-800/80 flex-shrink-0" />
                    <div className="flex-1 h-4 bg-gray-800/60 rounded" />
                  </div>
                ))}
              </div>
            ) : Object.keys(grouped).length === 0 ? (
              <div className="flex flex-col items-center py-12" role="status" aria-live="polite">
                <div className="p-4 rounded-2xl bg-gray-800/50 mb-4">
                  <MagnifyingGlassIcon className="w-8 h-8 text-gray-500" aria-hidden="true" />
                </div>
                <p className="text-gray-400">No matching pages or projects</p>
              </div>
            ) : (
              Object.entries(grouped).map(([category, categoryItems]) => (
                <div key={category}>
                  <div className="px-5 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {category}
                  </div>
                  {categoryItems.map((item) => {
                    const flatIdx = flattened.findIndex(
                      (f) => f.type === "item" && f.id === item.id
                    );
                    const isSelected = flatIdx === selectedIndex;
                    return (
                      <button
                        key={item.id}
                        data-index={flatIdx}
                        onClick={() => handleSelect(item)}
                        role="option"
                        aria-selected={isSelected}
                        className={`w-full flex items-center gap-4 px-5 py-3 text-left transition-colors ${
                          isSelected
                            ? "bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-cyan-300"
                            : "text-gray-300 hover:bg-gray-800/50"
                        }`}
                      >
                        <span
                          className={`flex items-center justify-center w-8 h-8 text-sm flex-shrink-0 ${
                            isSelected
                              ? "rounded-full bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/30"
                              : "rounded-full bg-gray-800/80"
                          }`}
                          aria-hidden="true"
                        >
                          {item.label.charAt(0)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{item.label}</p>
                        </div>
                        {item.path && (
                          <span className="text-xs text-gray-600 font-mono flex-shrink-0">↳</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {itemCount > 0 && (
            <div className="flex items-center gap-4 px-5 py-3 border-t border-gray-800/50 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">↑↓</kbd> Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">↵</kbd> Open
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">ESC</kbd> Close
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
