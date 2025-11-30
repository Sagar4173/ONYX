/**
 * Premium Header Component
 * Enterprise-grade header with real-time search, notifications, and user profile
 */
import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  BellIcon,
  MagnifyingGlassIcon,
  Bars3Icon as MenuIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  BookOpenIcon,
  ChevronDownIcon,
  XMarkIcon,
  ShieldCheckIcon,
  BoltIcon,
  SparklesIcon,
  ChevronRightIcon,
  HomeIcon,
  FolderIcon,
  DocumentMagnifyingGlassIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "../components/auth";
import { dashboardAPI } from "../services/dashboardService";

// Debounce hook for search
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Dynamic Breadcrumb Component
 */
const Breadcrumb = () => {
  const location = useLocation();
  const pathSegments = location.pathname.split("/").filter(Boolean);

  const breadcrumbMap = {
    dashboard: { label: "Dashboard", icon: HomeIcon },
    projects: { label: "Projects", icon: FolderIcon },
    project: { label: "Project Details", icon: FolderIcon },
    scans: { label: "Scans", icon: DocumentMagnifyingGlassIcon },
    reports: { label: "Reports", icon: DocumentMagnifyingGlassIcon },
    report: { label: "Report Details", icon: DocumentMagnifyingGlassIcon },
    analytics: { label: "Analytics", icon: ChartBarIcon },
    settings: { label: "Settings", icon: Cog6ToothIcon },
    compliance: { label: "Compliance", icon: ShieldCheckIcon },
    users: { label: "Users", icon: UserCircleIcon },
    "audit-logs": { label: "Audit Logs", icon: ClockIcon },
    "retention-policies": { label: "Data Retention", icon: ClockIcon },
  };

  // Import ChartBarIcon if not already
  const ChartBarIcon = () => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className="w-4 h-4"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"
      />
    </svg>
  );

  if (pathSegments.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <HomeIcon className="h-4 w-4 text-blue-400" />
        <span className="text-white font-medium">Dashboard</span>
      </div>
    );
  }

  return (
    <nav className="flex items-center gap-1.5 text-sm">
      <Link
        to="/"
        className="p-1 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all"
      >
        <HomeIcon className="h-4 w-4" />
      </Link>
      {pathSegments.map((segment, index) => {
        const path = `/${pathSegments.slice(0, index + 1).join("/")}`;
        const isLast = index === pathSegments.length - 1;
        const config = breadcrumbMap[segment] || { label: segment };

        return (
          <React.Fragment key={path}>
            <ChevronRightIcon className="h-3 w-3 text-gray-600" />
            {isLast ? (
              <span className="px-2 py-1 text-white font-medium capitalize bg-white/5 rounded-lg">
                {config.label}
              </span>
            ) : (
              <Link
                to={path}
                className="px-2 py-1 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all capitalize"
              >
                {config.label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

/**
 * Real-time Search Component with API Integration
 */
const SearchDropdown = ({ query, isOpen, onClose, onSelect }) => {
  const navigate = useNavigate();
  const debouncedQuery = useDebounce(query, 300);

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ["globalSearch", debouncedQuery],
    queryFn: () => dashboardAPI.globalSearch(debouncedQuery),
    enabled: isOpen && debouncedQuery.length >= 2,
    staleTime: 30000,
  });

  if (!isOpen) return null;

  const handleNavigate = (path) => {
    navigate(path);
    onClose();
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: "bg-red-500",
      high: "bg-orange-500",
      medium: "bg-yellow-500",
      low: "bg-blue-500",
      info: "bg-gray-500",
    };
    return colors[severity] || colors.info;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircleIcon className="h-4 w-4 text-green-400" />;
      case "failed":
        return <XCircleIcon className="h-4 w-4 text-red-400" />;
      case "in_progress":
      case "scanning":
        return <ArrowPathIcon className="h-4 w-4 text-blue-400 animate-spin" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900/98 backdrop-blur-2xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden">
      {/* Search Header */}
      <div className="px-4 py-3 border-b border-gray-800/50 bg-gradient-to-r from-blue-500/5 to-purple-500/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MagnifyingGlassIcon className="h-4 w-4 text-blue-400" />
            <span className="text-sm text-gray-400">
              {isLoading ? "Searching..." : `Results for "${query}"`}
            </span>
          </div>
          <kbd className="px-2 py-1 bg-gray-800/50 rounded text-xs text-gray-500 border border-gray-700/50">
            ESC to close
          </kbd>
        </div>
      </div>

      <div className="max-h-[70vh] overflow-y-auto">
        {/* Quick Actions */}
        {query.length < 2 && (
          <div className="p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Quick Actions
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleNavigate("/projects?action=new")}
                className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-500/10 to-blue-600/10 hover:from-blue-500/20 hover:to-blue-600/20 rounded-xl transition-all group"
              >
                <div className="p-2 rounded-lg bg-blue-500/20 group-hover:bg-blue-500/30 transition-colors">
                  <SparklesIcon className="h-4 w-4 text-blue-400" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-white">New Project</p>
                  <p className="text-xs text-gray-500">Start security scan</p>
                </div>
              </button>
              <button
                onClick={() => handleNavigate("/reports")}
                className="flex items-center gap-3 p-3 bg-gradient-to-r from-purple-500/10 to-purple-600/10 hover:from-purple-500/20 hover:to-purple-600/20 rounded-xl transition-all group"
              >
                <div className="p-2 rounded-lg bg-purple-500/20 group-hover:bg-purple-500/30 transition-colors">
                  <DocumentMagnifyingGlassIcon className="h-4 w-4 text-purple-400" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-white">View Reports</p>
                  <p className="text-xs text-gray-500">Scan results</p>
                </div>
              </button>
            </div>
            <p className="mt-4 text-xs text-gray-500 text-center">
              Type at least 2 characters to search
            </p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && query.length >= 2 && (
          <div className="p-8 text-center">
            <ArrowPathIcon className="h-8 w-8 text-blue-400 animate-spin mx-auto mb-3" />
            <p className="text-gray-400">
              Searching across projects, scans, and vulnerabilities...
            </p>
          </div>
        )}

        {/* Search Results */}
        {!isLoading && searchResults && query.length >= 2 && (
          <div className="p-4 space-y-4">
            {/* Projects */}
            {searchResults.projects?.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FolderIcon className="h-4 w-4 text-blue-400" />
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Projects ({searchResults.projects.length})
                  </p>
                </div>
                <div className="space-y-1">
                  {searchResults.projects.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavigate(item.path)}
                      className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                          <FolderIcon className="h-4 w-4 text-blue-400" />
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-medium text-white">
                            {item.name}
                          </p>
                          <p className="text-xs text-gray-500 capitalize">
                            {item.status}
                          </p>
                        </div>
                      </div>
                      <ChevronRightIcon className="h-4 w-4 text-gray-600 group-hover:text-white transition-colors" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Scans */}
            {searchResults.scans?.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <DocumentMagnifyingGlassIcon className="h-4 w-4 text-purple-400" />
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Scans ({searchResults.scans.length})
                  </p>
                </div>
                <div className="space-y-1">
                  {searchResults.scans.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavigate(item.path)}
                      className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon(item.status)}
                        <div className="text-left">
                          <p className="text-sm font-medium text-white">
                            {item.name}
                          </p>
                          <div className="flex items-center gap-2">
                            <div
                              className={`w-2 h-2 rounded-full ${getSeverityColor(
                                item.severity
                              )}`}
                            />
                            <p className="text-xs text-gray-500 capitalize">
                              {item.severity} severity
                            </p>
                          </div>
                        </div>
                      </div>
                      <ChevronRightIcon className="h-4 w-4 text-gray-600 group-hover:text-white transition-colors" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Vulnerabilities */}
            {searchResults.vulnerabilities?.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <ExclamationTriangleIcon className="h-4 w-4 text-amber-400" />
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Vulnerabilities ({searchResults.vulnerabilities.length})
                  </p>
                </div>
                <div className="space-y-1">
                  {searchResults.vulnerabilities.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavigate(item.path)}
                      className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-2 h-2 rounded-full ${getSeverityColor(
                            item.severity
                          )}`}
                        />
                        <div className="text-left">
                          <p className="text-sm font-medium text-white">
                            {item.name}
                          </p>
                          <p className="text-xs text-gray-500 capitalize">
                            {item.severity}
                          </p>
                        </div>
                      </div>
                      <ChevronRightIcon className="h-4 w-4 text-gray-600 group-hover:text-white transition-colors" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* No Results */}
            {!searchResults.projects?.length &&
              !searchResults.scans?.length &&
              !searchResults.vulnerabilities?.length && (
                <div className="py-8 text-center">
                  <MagnifyingGlassIcon className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400 font-medium">No results found</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Try different keywords or create a new project
                  </p>
                </div>
              )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-800/50 bg-gray-900/50">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-gray-800 rounded">↑</kbd>
              <kbd className="px-1.5 py-0.5 bg-gray-800 rounded">↓</kbd>
              navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-gray-800 rounded">↵</kbd>
              select
            </span>
          </div>
          <span>Powered by SecureDevOps AI</span>
        </div>
      </div>
    </div>
  );
};

/**
 * Enhanced Notification Panel with Real Data
 */
const NotificationPanel = ({
  notifications,
  isOpen,
  onClear,
  onDismiss,
  onMarkAllRead,
}) => {
  if (!isOpen) return null;

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getNotificationIcon = (type) => {
    switch (type) {
      case "scan_started":
        return <BoltIcon className="h-4 w-4 text-blue-400" />;
      case "scan_completed":
        return <CheckCircleIcon className="h-4 w-4 text-green-400" />;
      case "scan_error":
        return <XCircleIcon className="h-4 w-4 text-red-400" />;
      case "scan_update":
        return <ArrowPathIcon className="h-4 w-4 text-yellow-400" />;
      default:
        return <BellIcon className="h-4 w-4 text-purple-400" />;
    }
  };

  const getNotificationBg = (type) => {
    switch (type) {
      case "scan_started":
        return "bg-blue-500/10";
      case "scan_completed":
        return "bg-green-500/10";
      case "scan_error":
        return "bg-red-500/10";
      case "scan_update":
        return "bg-yellow-500/10";
      default:
        return "bg-purple-500/10";
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-[420px] bg-gray-900/98 backdrop-blur-2xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-800/50 bg-gradient-to-r from-blue-500/5 to-purple-500/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
              <BellIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                Notifications
              </h3>
              <p className="text-xs text-gray-400">
                {unreadCount > 0
                  ? `${unreadCount} unread notification${
                      unreadCount > 1 ? "s" : ""
                    }`
                  : "All caught up!"}
              </p>
            </div>
          </div>
          {notifications.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                onClick={onMarkAllRead}
                className="px-3 py-1.5 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-all"
              >
                Mark all read
              </button>
              <button
                onClick={onClear}
                className="px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all"
              >
                Clear all
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Notification List */}
      <div className="max-h-[400px] overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="py-12 text-center">
            <div className="p-4 rounded-2xl bg-gray-800/30 inline-block mb-4">
              <BellIcon className="h-12 w-12 text-gray-600" />
            </div>
            <p className="text-gray-400 font-medium">No notifications yet</p>
            <p className="text-sm text-gray-500 mt-1">
              Activity from your scans will appear here
            </p>
          </div>
        ) : (
          <div>
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 border-b border-gray-800/30 hover:bg-white/[0.02] transition-all ${
                  !notification.read ? "bg-blue-500/[0.03]" : ""
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-xl ${getNotificationBg(
                      notification.type
                    )}`}
                  >
                    {getNotificationIcon(notification.type)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-medium text-white truncate">
                        {notification.data?.project_name || "System"}
                      </p>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-sm text-gray-400 line-clamp-2">
                      {notification.message}
                    </p>
                    <p className="text-xs text-gray-500 mt-1.5">
                      {formatTime(notification.timestamp)}
                    </p>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDismiss(notification.id);
                    }}
                    className="p-1.5 text-gray-500 hover:text-white hover:bg-white/5 rounded-lg transition-all"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="p-3 border-t border-gray-800/50 bg-gray-900/50">
          <Link
            to="/notifications"
            className="block text-center text-sm text-blue-400 hover:text-blue-300 transition-colors py-1"
          >
            View all activity →
          </Link>
        </div>
      )}
    </div>
  );
};

/**
 * Enhanced User Menu
 */
const UserMenu = ({ user, isOpen, onToggle, onLogout, onProfileClick }) => {
  const navigate = useNavigate();

  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center gap-2 lg:gap-3 p-1.5 lg:p-2 rounded-xl lg:rounded-2xl text-gray-300 hover:text-white hover:bg-white/5 transition-all group"
      >
        <div className="relative">
          <div className="w-9 h-9 lg:w-10 lg:h-10 rounded-xl lg:rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm lg:text-base shadow-lg ring-2 ring-white/10 group-hover:ring-white/20 transition-all">
            {user?.full_name?.[0]?.toUpperCase() ||
              user?.email?.[0]?.toUpperCase() ||
              "U"}
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-gray-900 shadow-lg" />
        </div>
        <div className="hidden lg:block text-left">
          <p className="text-sm font-medium text-white truncate max-w-[120px]">
            {user?.full_name || "User"}
          </p>
          <p className="text-xs text-gray-400 truncate max-w-[120px] capitalize">
            {user?.role || "Member"}
          </p>
        </div>
        <ChevronDownIcon
          className={`hidden lg:block h-4 w-4 text-gray-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-gray-900/98 backdrop-blur-2xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden">
          {/* User Info Header */}
          <div className="p-5 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 border-b border-gray-800/50">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl shadow-xl ring-2 ring-white/20">
                {user?.full_name?.[0]?.toUpperCase() ||
                  user?.email?.[0]?.toUpperCase() ||
                  "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-white truncate text-lg">
                  {user?.full_name || "User"}
                </p>
                <p className="text-sm text-gray-400 truncate">{user?.email}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="px-2.5 py-1 bg-blue-500/20 text-blue-400 text-xs font-medium rounded-lg capitalize">
                    {user?.role || "Member"}
                  </span>
                  {user?.is_email_verified && (
                    <span className="px-2.5 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-lg flex items-center gap-1">
                      <CheckCircleIcon className="h-3 w-3" />
                      Verified
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="p-2">
            <button
              onClick={() => {
                onToggle();
                onProfileClick?.();
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-white/5 rounded-xl transition-all"
            >
              <UserCircleIcon className="h-5 w-5" />
              <span>Profile Settings</span>
            </button>
            <button
              onClick={() => {
                onToggle();
                navigate("/settings");
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-white/5 rounded-xl transition-all"
            >
              <Cog6ToothIcon className="h-5 w-5" />
              <span>Preferences</span>
            </button>
            <button
              onClick={() => {
                onToggle();
                window.open("/docs", "_blank");
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-white/5 rounded-xl transition-all"
            >
              <BookOpenIcon className="h-5 w-5" />
              <span>Documentation</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-white/5 rounded-xl transition-all">
              <QuestionMarkCircleIcon className="h-5 w-5" />
              <span>Help & Support</span>
            </button>
          </div>

          {/* Logout */}
          <div className="p-2 border-t border-gray-800/50">
            <button
              onClick={onLogout}
              className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-all"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Main Header Component
 */
export const Header = ({
  onMenuClick,
  notifications = [],
  onClearNotifications,
  onDismissNotification,
  onProfileClick,
}) => {
  const { user, logout, resendVerificationEmail } = useAuth();
  const [notificationPanelOpen, setNotificationPanelOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const searchRef = useRef(null);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd/Ctrl + K to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchRef.current?.focus();
        setSearchFocused(true);
      }
      // Escape to close panels
      if (e.key === "Escape") {
        setSearchFocused(false);
        setNotificationPanelOpen(false);
        setUserMenuOpen(false);
        searchRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Close panels on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        notificationPanelOpen &&
        !event.target.closest(".notification-panel")
      ) {
        setNotificationPanelOpen(false);
      }
      if (userMenuOpen && !event.target.closest(".user-menu")) {
        setUserMenuOpen(false);
      }
      if (searchFocused && !event.target.closest(".search-container")) {
        setSearchFocused(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [notificationPanelOpen, userMenuOpen, searchFocused]);

  return (
    <header className="sticky top-0 z-30">
      {/* Email Verification Banner */}
      {user && !user.is_email_verified && (
        <div className="relative overflow-hidden bg-gradient-to-r from-amber-500 via-orange-500 to-red-500">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0yMCAyMGw0LTRoLThsNCA0em0wIDBoNC00bC00IDR6bTAgMGgtNGw0LTRtMCA0aDRsLTQgNHoiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIi8+PC9nPjwvc3ZnPg==')] opacity-50" />
          <div className="relative px-4 py-2.5 flex items-center justify-center gap-3">
            <SparklesIcon className="h-4 w-4 text-white animate-pulse" />
            <p className="text-white text-sm font-medium">
              Please verify your email to unlock all features
            </p>
            <button
              onClick={async () => {
                try {
                  await resendVerificationEmail();
                } catch (error) {
                  // Error handled
                }
              }}
              className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm font-semibold transition-all shadow-lg hover:shadow-xl"
            >
              Resend Email
            </button>
          </div>
        </div>
      )}

      {/* Main Header */}
      <div className="bg-gray-900/80 backdrop-blur-2xl border-b border-gray-800/50 shadow-xl">
        <div className="flex h-16 lg:h-[72px] items-center justify-between px-4 lg:px-6">
          {/* Left Section */}
          <div className="flex items-center gap-4">
            <button
              type="button"
              className="lg:hidden p-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all active:scale-95"
              onClick={onMenuClick}
            >
              <MenuIcon className="h-6 w-6" />
            </button>

            {/* Breadcrumb */}
            <div className="hidden lg:block">
              <Breadcrumb />
            </div>
          </div>

          {/* Center - Search */}
          <div className="flex-1 max-w-2xl mx-4 hidden sm:block search-container">
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <MagnifyingGlassIcon
                  className={`h-5 w-5 transition-colors ${
                    searchFocused ? "text-blue-400" : "text-gray-400"
                  }`}
                />
              </div>
              <input
                ref={searchRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                placeholder="Search projects, scans, vulnerabilities..."
                className="w-full pl-12 pr-24 py-3 bg-white/5 border border-gray-700/50 rounded-2xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-white/[0.08] transition-all text-sm"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="p-1 text-gray-500 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                )}
                <kbd className="hidden lg:inline-flex items-center gap-1 px-2 py-1 bg-gray-800/50 rounded-lg text-xs text-gray-400 border border-gray-700/50">
                  <span className="text-[10px]">⌘</span>K
                </kbd>
              </div>

              <SearchDropdown
                query={searchQuery}
                isOpen={searchFocused}
                onClose={() => {
                  setSearchFocused(false);
                  setSearchQuery("");
                }}
              />
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2 lg:gap-3">
            {/* Mobile Search */}
            <button
              onClick={() => {
                setSearchFocused(true);
                setTimeout(() => searchRef.current?.focus(), 100);
              }}
              className="sm:hidden p-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all"
            >
              <MagnifyingGlassIcon className="h-5 w-5" />
            </button>

            {/* Notifications */}
            <div className="relative notification-panel">
              <button
                onClick={() => setNotificationPanelOpen(!notificationPanelOpen)}
                className="relative p-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all"
              >
                <BellIcon className="h-5 w-5" />
                {notifications.length > 0 && (
                  <span className="absolute -top-1 -right-1 h-5 w-5 bg-gradient-to-r from-red-500 to-pink-500 rounded-full text-xs text-white flex items-center justify-center font-bold shadow-lg ring-2 ring-gray-900 animate-pulse">
                    {notifications.length > 9 ? "9+" : notifications.length}
                  </span>
                )}
              </button>

              <NotificationPanel
                notifications={notifications}
                isOpen={notificationPanelOpen}
                onClear={onClearNotifications}
                onDismiss={onDismissNotification}
                onMarkAllRead={() => {}}
              />
            </div>

            {/* Divider */}
            <div className="hidden lg:block w-px h-8 bg-gray-700/50" />

            {/* User Menu */}
            <div className="user-menu">
              <UserMenu
                user={user}
                isOpen={userMenuOpen}
                onToggle={() => setUserMenuOpen(!userMenuOpen)}
                onLogout={logout}
                onProfileClick={() => {
                  setUserMenuOpen(false);
                  onProfileClick?.();
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
