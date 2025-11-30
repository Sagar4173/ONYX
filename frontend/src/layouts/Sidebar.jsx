// f:\Project\SecureDevOpsAI-Platform\frontend\src\layouts\Sidebar.jsx
// Enterprise Premium Sidebar with Real API Integration
// Features: Real-time stats, smooth animations, glassmorphism, professional navigation

import { useState, useEffect, useCallback, memo, useMemo } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  XMarkIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  Bars3Icon,
  ArrowLeftIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

// Import navigation configuration
import { navigation, getNavigationByCategory } from "../config/navigation";

// Import real dashboard service
import dashboardService from "../services/dashboardService";

// ============================================================================
// QUICK STATS COMPONENT - REAL API DATA
// ============================================================================
const QuickStats = memo(function QuickStats({ collapsed }) {
  const [stats, setStats] = useState({
    projects: { value: "-", trend: null },
    scans: { value: "-", trend: null },
    issues: { value: "-", trend: null },
    score: { value: "-", trend: null },
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch real stats from API
  useEffect(() => {
    let isMounted = true;
    let retryTimeout = null;

    const fetchStats = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const data = await dashboardService.getQuickStats();

        if (isMounted) {
          setStats({
            projects: {
              value: data.totalProjects?.toString() || "0",
              trend: data.projectsTrend || null,
              color: "from-blue-500 to-cyan-500",
            },
            scans: {
              value: data.totalScans?.toString() || "0",
              trend: data.scansTrend || null,
              color: "from-violet-500 to-purple-500",
            },
            issues: {
              value: data.openIssues?.toString() || "0",
              trend: data.issuesTrend || null,
              color: "from-amber-500 to-orange-500",
            },
            score: {
              value: data.avgSecurityScore
                ? `${Math.round(data.avgSecurityScore)}%`
                : "-",
              trend: data.scoreTrend || null,
              color: "from-emerald-500 to-green-500",
            },
          });
          setIsLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Failed to fetch quick stats:", err);
          setError("Unable to load stats");
          setIsLoading(false);

          // Retry after 30 seconds on error
          retryTimeout = setTimeout(fetchStats, 30000);
        }
      }
    };

    fetchStats();

    // Refresh stats every 2 minutes
    const interval = setInterval(fetchStats, 120000);

    return () => {
      isMounted = false;
      clearInterval(interval);
      if (retryTimeout) clearTimeout(retryTimeout);
    };
  }, []);

  // Collapsed view - compact stat icons
  if (collapsed) {
    return (
      <div className="px-2 py-3 space-y-2">
        {Object.entries(stats)
          .slice(0, 4)
          .map(([key, stat], index) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="relative group"
            >
              <div
                className={clsx(
                  "w-10 h-10 mx-auto rounded-xl flex items-center justify-center",
                  "bg-gradient-to-br shadow-lg transition-all duration-300",
                  "hover:scale-110 hover:shadow-xl cursor-default",
                  stat.color || "from-gray-500 to-gray-600"
                )}
              >
                <span className="text-xs font-bold text-white">
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    stat.value?.toString().slice(0, 3) || "-"
                  )}
                </span>
              </div>

              {/* Tooltip */}
              <div
                className="absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50
                          opacity-0 group-hover:opacity-100 pointer-events-none
                          transition-opacity duration-200"
              >
                <div
                  className="bg-slate-900 text-white text-xs px-3 py-2 rounded-lg shadow-xl
                            whitespace-nowrap border border-white/10"
                >
                  <span className="capitalize">{key}</span>: {stat.value}
                  {stat.trend && (
                    <span
                      className={clsx(
                        "ml-2",
                        stat.trend > 0 ? "text-green-400" : "text-red-400"
                      )}
                    >
                      {stat.trend > 0 ? "↑" : "↓"} {Math.abs(stat.trend)}%
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
      </div>
    );
  }

  // Expanded view - full stats grid
  const statItems = [
    { key: "projects", label: "Projects", icon: "📁" },
    { key: "scans", label: "Scans", icon: "🔍" },
    { key: "issues", label: "Issues", icon: "⚠️" },
    { key: "score", label: "Score", icon: "🛡️" },
  ];

  return (
    <div className="px-4 py-4">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
          Quick Stats
        </h3>
        {isLoading && (
          <div className="w-3 h-3 border border-blue-400/50 border-t-blue-400 rounded-full animate-spin" />
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="text-xs text-red-400 mb-2 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2">
        {statItems.map((item, index) => {
          const stat = stats[item.key];
          return (
            <motion.div
              key={item.key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={clsx(
                "relative overflow-hidden rounded-xl p-3",
                "bg-gradient-to-br backdrop-blur-sm",
                "border border-white/10 dark:border-slate-700/50",
                "hover:border-white/20 transition-all duration-300",
                "group cursor-default"
              )}
              style={{
                background: `linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%)`,
              }}
            >
              {/* Gradient Overlay */}
              <div
                className={clsx(
                  "absolute inset-0 opacity-20 group-hover:opacity-30 transition-opacity",
                  "bg-gradient-to-br",
                  stat?.color || "from-gray-500 to-gray-600"
                )}
              />

              {/* Content */}
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">{item.icon}</span>
                  {stat?.trend && (
                    <span
                      className={clsx(
                        "text-[10px] font-medium px-1.5 py-0.5 rounded-full",
                        stat.trend > 0
                          ? "bg-green-500/20 text-green-400"
                          : "bg-red-500/20 text-red-400"
                      )}
                    >
                      {stat.trend > 0 ? "+" : ""}
                      {stat.trend}%
                    </span>
                  )}
                </div>

                <div className="text-lg font-bold text-white">
                  {isLoading ? (
                    <div className="h-6 w-12 bg-slate-700/50 rounded animate-pulse" />
                  ) : (
                    stat?.value || "-"
                  )}
                </div>

                <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wide mt-0.5">
                  {item.label}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
});

// ============================================================================
// CONNECTION STATUS COMPONENT
// ============================================================================
const ConnectionStatus = memo(function ConnectionStatus({ collapsed }) {
  const [status, setStatus] = useState({
    api: { connected: false, latency: null },
    websocket: { connected: false },
  });

  useEffect(() => {
    let isMounted = true;

    const checkStatus = async () => {
      try {
        const start = performance.now();
        const healthData = await dashboardService.getSystemHealth();
        const latency = Math.round(performance.now() - start);

        if (isMounted) {
          setStatus({
            api: {
              connected:
                healthData?.status === "healthy" || healthData !== null,
              latency,
            },
            websocket: {
              connected: healthData?.websocket?.connected ?? false,
            },
          });
        }
      } catch {
        if (isMounted) {
          setStatus({
            api: { connected: false, latency: null },
            websocket: { connected: false },
          });
        }
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  if (collapsed) {
    return (
      <div className="px-2 py-2 flex justify-center">
        <div
          className={clsx(
            "w-2.5 h-2.5 rounded-full",
            status.api.connected
              ? "bg-green-400 shadow-lg shadow-green-400/50 animate-pulse"
              : "bg-red-400 shadow-lg shadow-red-400/50"
          )}
        />
      </div>
    );
  }

  return (
    <div className="px-4 py-3 border-t border-white/5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={clsx(
              "w-2 h-2 rounded-full",
              status.api.connected
                ? "bg-green-400 shadow-md shadow-green-400/50 animate-pulse"
                : "bg-red-400 shadow-md shadow-red-400/50"
            )}
          />
          <span className="text-xs text-slate-400">
            {status.api.connected ? "API Connected" : "API Disconnected"}
          </span>
        </div>

        {status.api.connected && status.api.latency && (
          <span
            className={clsx(
              "text-[10px] font-mono px-1.5 py-0.5 rounded",
              status.api.latency < 100
                ? "text-green-400 bg-green-500/10"
                : status.api.latency < 300
                ? "text-amber-400 bg-amber-500/10"
                : "text-red-400 bg-red-500/10"
            )}
          >
            {status.api.latency}ms
          </span>
        )}
      </div>
    </div>
  );
});

// ============================================================================
// NAV LINK COMPONENT
// ============================================================================
const NavItem = memo(function NavItem({ item, collapsed, depth = 0 }) {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);

  const isActive =
    location.pathname === item.path ||
    location.pathname.startsWith(item.path + "/");

  const hasChildren = item.children && item.children.length > 0;

  // Auto-expand if child is active
  useEffect(() => {
    if (hasChildren) {
      const childActive = item.children.some(
        (child) =>
          location.pathname === child.path ||
          location.pathname.startsWith(child.path + "/")
      );
      if (childActive) setIsExpanded(true);
    }
  }, [location.pathname, hasChildren, item.children]);

  const Icon = item.icon;

  // Collapsed state - icon only
  if (collapsed) {
    return (
      <div className="relative group">
        <NavLink
          to={item.path}
          className={({ isActive: active }) =>
            clsx(
              "flex items-center justify-center w-10 h-10 mx-auto rounded-xl",
              "transition-all duration-300 relative overflow-hidden group",
              active || isActive
                ? "bg-gradient-to-br from-blue-500/20 to-purple-500/20 text-blue-400 shadow-lg shadow-blue-500/20"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            )
          }
        >
          {/* Glow effect */}
          {isActive && (
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 blur-xl" />
          )}

          {Icon && <Icon className="w-5 h-5 relative z-10" />}

          {/* Badge */}
          {item.badge && (
            <span
              className={clsx(
                "absolute -top-1 -right-1 min-w-[16px] h-4 px-1",
                "flex items-center justify-center rounded-full",
                "text-[9px] font-bold text-white",
                item.badge.type === "error"
                  ? "bg-red-500"
                  : item.badge.type === "warning"
                  ? "bg-amber-500"
                  : item.badge.type === "success"
                  ? "bg-green-500"
                  : "bg-blue-500"
              )}
            >
              {item.badge.count}
            </span>
          )}
        </NavLink>

        {/* Tooltip */}
        <div
          className="absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50
                      opacity-0 group-hover:opacity-100 pointer-events-none
                      transition-opacity duration-200"
        >
          <div
            className="bg-slate-900 text-white text-xs px-3 py-2 rounded-lg shadow-xl
                        whitespace-nowrap border border-white/10 font-medium"
          >
            {item.name}
            {item.beta && (
              <span className="ml-2 px-1.5 py-0.5 text-[9px] bg-purple-500/30 text-purple-300 rounded">
                BETA
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Expanded state - full nav item
  return (
    <div>
      {hasChildren ? (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={clsx(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl",
              "transition-all duration-300 group relative",
              isExpanded
                ? "bg-white/5 text-white"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            )}
            style={{ paddingLeft: `${12 + depth * 12}px` }}
          >
            {Icon && (
              <Icon
                className={clsx(
                  "w-5 h-5 flex-shrink-0 transition-colors",
                  isExpanded ? "text-blue-400" : "group-hover:text-blue-400"
                )}
              />
            )}
            <span className="flex-1 text-sm font-medium text-left truncate">
              {item.name}
            </span>
            <ChevronDownIcon
              className={clsx(
                "w-4 h-4 transition-transform duration-300",
                isExpanded && "rotate-180"
              )}
            />
          </button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="py-1 ml-3 border-l border-white/10">
                  {item.children.map((child) => (
                    <NavItem
                      key={child.path}
                      item={child}
                      collapsed={false}
                      depth={depth + 1}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      ) : (
        <NavLink
          to={item.path}
          className={({ isActive: active }) =>
            clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl",
              "transition-all duration-300 group relative overflow-hidden",
              active || isActive
                ? "bg-gradient-to-r from-blue-500/15 to-purple-500/15 text-white shadow-lg"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            )
          }
          style={{ paddingLeft: `${12 + depth * 12}px` }}
        >
          {/* Active indicator */}
          {isActive && (
            <>
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-400 to-purple-400 rounded-r-full" />
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-transparent" />
            </>
          )}

          {Icon && (
            <Icon
              className={clsx(
                "w-5 h-5 flex-shrink-0 transition-colors relative z-10",
                isActive ? "text-blue-400" : "group-hover:text-blue-400"
              )}
            />
          )}

          <span className="flex-1 text-sm font-medium truncate relative z-10">
            {item.name}
          </span>

          {/* Badges */}
          {item.badge && (
            <span
              className={clsx(
                "px-2 py-0.5 rounded-full text-[10px] font-bold relative z-10",
                item.badge.type === "error"
                  ? "bg-red-500/20 text-red-400"
                  : item.badge.type === "warning"
                  ? "bg-amber-500/20 text-amber-400"
                  : item.badge.type === "success"
                  ? "bg-green-500/20 text-green-400"
                  : "bg-blue-500/20 text-blue-400"
              )}
            >
              {item.badge.count}
            </span>
          )}

          {item.beta && (
            <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-purple-500/20 text-purple-400 rounded relative z-10">
              BETA
            </span>
          )}

          {item.new && (
            <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-green-500/20 text-green-400 rounded relative z-10">
              NEW
            </span>
          )}
        </NavLink>
      )}
    </div>
  );
});

// ============================================================================
// NAV SECTION COMPONENT
// ============================================================================
const NavSection = memo(function NavSection({ title, items, collapsed }) {
  if (!items || items.length === 0) return null;

  return (
    <div className="space-y-1">
      {!collapsed && title && (
        <h4 className="px-4 text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2">
          {title}
        </h4>
      )}
      <div className="space-y-1 px-2">
        {items.map((item) => (
          <NavItem key={item.path} item={item} collapsed={collapsed} />
        ))}
      </div>
    </div>
  );
});

// ============================================================================
// SIDEBAR HEADER COMPONENT
// ============================================================================
const SidebarHeader = memo(function SidebarHeader({
  collapsed,
  onToggle,
  onClose,
  isMobile,
}) {
  return (
    <div
      className={clsx(
        "h-16 flex items-center border-b border-white/5",
        collapsed ? "justify-center px-2" : "justify-between px-4"
      )}
    >
      {/* Logo */}
      {!collapsed && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className="relative">
            <div
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 
                          flex items-center justify-center shadow-lg shadow-blue-500/25"
            >
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-slate-900" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-tight">
              SecureDevOps
            </h1>
            <p className="text-[10px] text-slate-400 font-medium">
              AI Security Platform
            </p>
          </div>
        </motion.div>
      )}

      {collapsed && (
        <div
          className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 
                      flex items-center justify-center shadow-lg shadow-blue-500/25"
        >
          <span className="text-white font-bold text-lg">S</span>
        </div>
      )}

      {/* Toggle/Close Button */}
      {isMobile ? (
        <button
          onClick={onClose}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      ) : (
        !collapsed && (
          <button
            onClick={onToggle}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors
                   opacity-0 group-hover/sidebar:opacity-100"
          >
            <ArrowLeftIcon className="w-4 h-4" />
          </button>
        )
      )}
    </div>
  );
});

// ============================================================================
// DESKTOP SIDEBAR
// ============================================================================
const DesktopSidebar = memo(function DesktopSidebar({ collapsed, onToggle }) {
  const categorizedNav = useMemo(() => getNavigationByCategory(), []);

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 280 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={clsx(
        "fixed left-0 top-0 h-screen z-40",
        "bg-slate-900/95 backdrop-blur-xl",
        "border-r border-white/5",
        "flex flex-col",
        "group/sidebar",
        // Glass effect
        "shadow-2xl shadow-black/20"
      )}
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-900/98 to-slate-950 pointer-events-none" />

      {/* Subtle pattern */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`,
          backgroundSize: "24px 24px",
        }}
      />

      {/* Header */}
      <div className="relative z-10">
        <SidebarHeader collapsed={collapsed} onToggle={onToggle} />
      </div>

      {/* Quick Stats */}
      <div className="relative z-10">
        <QuickStats collapsed={collapsed} />
      </div>

      {/* Navigation */}
      <nav
        className="flex-1 overflow-y-auto overflow-x-hidden py-4 space-y-6 relative z-10
                    scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent"
      >
        {/* Main Navigation */}
        <NavSection
          title="Main"
          items={categorizedNav.main}
          collapsed={collapsed}
        />

        {/* Security Section */}
        <NavSection
          title="Security"
          items={categorizedNav.security}
          collapsed={collapsed}
        />

        {/* Analysis Section */}
        <NavSection
          title="Analysis"
          items={categorizedNav.analysis}
          collapsed={collapsed}
        />

        {/* Reports Section */}
        <NavSection
          title="Reports"
          items={categorizedNav.reports}
          collapsed={collapsed}
        />

        {/* Settings Section */}
        <NavSection
          title="Settings"
          items={categorizedNav.settings}
          collapsed={collapsed}
        />
      </nav>

      {/* Connection Status */}
      <div className="relative z-10">
        <ConnectionStatus collapsed={collapsed} />
      </div>

      {/* Collapse toggle button (visible on hover when not collapsed) */}
      {collapsed && (
        <button
          onClick={onToggle}
          className="absolute -right-3 top-20 w-6 h-6 
                   bg-slate-800 border border-white/10 rounded-full
                   flex items-center justify-center
                   text-slate-400 hover:text-white hover:bg-slate-700
                   transition-all duration-200 shadow-lg
                   opacity-0 group-hover/sidebar:opacity-100"
        >
          <ArrowRightIcon className="w-3 h-3" />
        </button>
      )}
    </motion.aside>
  );
});

// ============================================================================
// MOBILE SIDEBAR
// ============================================================================
const MobileSidebar = memo(function MobileSidebar({ isOpen, onClose }) {
  const categorizedNav = useMemo(() => getNavigationByCategory(), []);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Sidebar */}
          <motion.aside
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 250 }}
            className={clsx(
              "fixed left-0 top-0 h-screen w-80 z-50",
              "bg-slate-900/98 backdrop-blur-xl",
              "border-r border-white/5",
              "flex flex-col",
              "shadow-2xl"
            )}
          >
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-900/98 to-slate-950 pointer-events-none" />

            {/* Header */}
            <div className="relative z-10">
              <SidebarHeader collapsed={false} onClose={onClose} isMobile />
            </div>

            {/* Quick Stats */}
            <div className="relative z-10">
              <QuickStats collapsed={false} />
            </div>

            {/* Navigation */}
            <nav
              className="flex-1 overflow-y-auto py-4 space-y-6 relative z-10
                          scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent"
            >
              <NavSection
                title="Main"
                items={categorizedNav.main}
                collapsed={false}
              />
              <NavSection
                title="Security"
                items={categorizedNav.security}
                collapsed={false}
              />
              <NavSection
                title="Analysis"
                items={categorizedNav.analysis}
                collapsed={false}
              />
              <NavSection
                title="Reports"
                items={categorizedNav.reports}
                collapsed={false}
              />
              <NavSection
                title="Settings"
                items={categorizedNav.settings}
                collapsed={false}
              />
            </nav>

            {/* Connection Status */}
            <div className="relative z-10">
              <ConnectionStatus collapsed={false} />
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
});

// ============================================================================
// MOBILE MENU BUTTON
// ============================================================================
export const MobileMenuButton = memo(function MobileMenuButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="p-2 rounded-xl text-slate-400 hover:text-white 
               hover:bg-white/5 transition-all duration-200
               active:scale-95"
      aria-label="Open menu"
    >
      <Bars3Icon className="w-6 h-6" />
    </button>
  );
});

// ============================================================================
// MAIN SIDEBAR EXPORT
// ============================================================================
export default function Sidebar({
  collapsed = false,
  onToggle,
  mobileOpen = false,
  onMobileClose,
}) {
  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <DesktopSidebar collapsed={collapsed} onToggle={onToggle} />
      </div>

      {/* Mobile Sidebar */}
      <div className="lg:hidden">
        <MobileSidebar isOpen={mobileOpen} onClose={onMobileClose} />
      </div>
    </>
  );
}
