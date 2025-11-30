/**
 * Enhanced Header Component
 * Modern header with glassmorphism, notifications, search, and user profile
 */
import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  BellIcon,
  MagnifyingGlassIcon,
  Bars3Icon as MenuIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  BookOpenIcon,
  CommandLineIcon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
  ChevronDownIcon,
  XMarkIcon,
  ShieldCheckIcon,
  BoltIcon,
  SparklesIcon,
  ChevronRightIcon,
  HomeIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "../components/auth";

/**
 * Breadcrumb Component
 */
const Breadcrumb = () => {
  const location = useLocation();
  const pathSegments = location.pathname.split("/").filter(Boolean);

  const breadcrumbMap = {
    dashboard: { label: "Dashboard", icon: HomeIcon },
    projects: { label: "Projects" },
    scans: { label: "Scans" },
    reports: { label: "Reports" },
    analytics: { label: "Analytics" },
    settings: { label: "Settings" },
    compliance: { label: "Compliance" },
    users: { label: "Users" },
    admin: { label: "Admin" },
  };

  if (pathSegments.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <HomeIcon className="h-4 w-4 text-gray-400" />
        <span className="text-white font-medium">Dashboard</span>
      </div>
    );
  }

  return (
    <nav className="flex items-center gap-1.5 text-sm">
      <Link to="/" className="text-gray-400 hover:text-white transition-colors">
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
              <span className="text-white font-medium capitalize">
                {config.label}
              </span>
            ) : (
              <Link
                to={path}
                className="text-gray-400 hover:text-white transition-colors capitalize"
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
 * Search Results Dropdown
 */
const SearchResults = ({ query, isOpen, onClose }) => {
  if (!isOpen || !query) return null;

  const mockResults = {
    projects: [
      { id: 1, name: "frontend-app", type: "project", status: "active" },
      { id: 2, name: "backend-api", type: "project", status: "scanning" },
    ],
    scans: [
      { id: 1, name: "SAST Scan #1234", type: "scan", severity: "high" },
      { id: 2, name: "Secret Scan #1235", type: "scan", severity: "medium" },
    ],
    vulnerabilities: [
      { id: 1, name: "SQL Injection", type: "vuln", severity: "critical" },
      { id: 2, name: "XSS Attack", type: "vuln", severity: "high" },
    ],
  };

  return (
    <div className="absolute top-full left-0 right-0 mt-2 bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden">
      <div className="p-4">
        {/* Quick Actions */}
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Quick Actions
          </p>
          <div className="flex gap-2">
            <Link
              to="/projects?action=new"
              onClick={onClose}
              className="flex items-center gap-2 px-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg text-sm hover:bg-blue-500/30 transition-colors"
            >
              <SparklesIcon className="h-4 w-4" />
              New Scan
            </Link>
            <Link
              to="/reports"
              onClick={onClose}
              className="flex items-center gap-2 px-3 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm hover:bg-purple-500/30 transition-colors"
            >
              <ShieldCheckIcon className="h-4 w-4" />
              View Reports
            </Link>
          </div>
        </div>

        {/* Search Results Sections */}
        {Object.entries(mockResults).map(([category, items]) => (
          <div key={category} className="mb-4 last:mb-0">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              {category}
            </p>
            <div className="space-y-1">
              {items
                .filter((item) =>
                  item.name.toLowerCase().includes(query.toLowerCase())
                )
                .slice(0, 3)
                .map((item) => (
                  <button
                    key={item.id}
                    onClick={onClose}
                    className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/50 transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          item.severity === "critical"
                            ? "bg-red-500"
                            : item.severity === "high"
                            ? "bg-orange-500"
                            : item.severity === "medium"
                            ? "bg-yellow-500"
                            : item.status === "scanning"
                            ? "bg-blue-500 animate-pulse"
                            : "bg-green-500"
                        }`}
                      />
                      <span className="text-sm text-white">{item.name}</span>
                    </div>
                    <span className="text-xs text-gray-500 capitalize">
                      {item.type}
                    </span>
                  </button>
                ))}
            </div>
          </div>
        ))}

        {/* Search Tip */}
        <div className="pt-3 border-t border-gray-700/50">
          <p className="text-xs text-gray-500 flex items-center gap-2">
            <CommandLineIcon className="h-3 w-3" />
            Press{" "}
            <kbd className="px-1.5 py-0.5 bg-gray-700 rounded text-gray-300">
              ⌘K
            </kbd>{" "}
            to search anywhere
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * Enhanced Notification Panel Component
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

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-700/50 bg-gradient-to-r from-blue-500/10 to-purple-500/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600">
              <BellIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                Notifications
              </h3>
              <p className="text-xs text-gray-400">
                {unreadCount > 0 ? `${unreadCount} unread` : "All caught up!"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {notifications.length > 0 && (
              <>
                <button
                  onClick={onMarkAllRead}
                  className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Mark all read
                </button>
                <span className="text-gray-600">|</span>
                <button
                  onClick={onClear}
                  className="text-xs text-gray-400 hover:text-white transition-colors"
                >
                  Clear all
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Notification List */}
      <div className="max-h-[400px] overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="text-center py-12">
            <div className="p-4 rounded-2xl bg-gray-700/30 inline-block mb-4">
              <BellIcon className="h-12 w-12 text-gray-500" />
            </div>
            <p className="text-gray-400 font-medium">No notifications</p>
            <p className="text-sm text-gray-500 mt-1">
              You're all caught up! 🎉
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700/30">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-gray-700/30 transition-colors ${
                  !notification.read ? "bg-blue-500/5" : ""
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-xl ${
                      notification.type === "scan_started"
                        ? "bg-blue-500/20"
                        : notification.type === "scan_completed"
                        ? "bg-green-500/20"
                        : notification.type === "scan_error"
                        ? "bg-red-500/20"
                        : notification.type === "scan_update"
                        ? "bg-yellow-500/20"
                        : "bg-purple-500/20"
                    }`}
                  >
                    {notification.type === "scan_started" && (
                      <BoltIcon className="h-4 w-4 text-blue-400" />
                    )}
                    {notification.type === "scan_completed" && (
                      <ShieldCheckIcon className="h-4 w-4 text-green-400" />
                    )}
                    {notification.type === "scan_error" && (
                      <XMarkIcon className="h-4 w-4 text-red-400" />
                    )}
                    {notification.type === "scan_update" && (
                      <SparklesIcon className="h-4 w-4 text-yellow-400" />
                    )}
                    {notification.type === "system" && (
                      <BellIcon className="h-4 w-4 text-purple-400" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-medium text-white truncate">
                        {notification.data?.project_name ||
                          notification.data?.projectName ||
                          (notification.type === "scan_update"
                            ? "Scan Update"
                            : notification.type === "scan_started"
                            ? "Scan Started"
                            : notification.type === "scan_completed"
                            ? "Scan Completed"
                            : notification.type === "scan_error"
                            ? "Scan Error"
                            : "System Notification")}
                      </p>
                      {!notification.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full" />
                      )}
                    </div>
                    <p className="text-sm text-gray-400 line-clamp-2">
                      {notification.message || "Notification"}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      {notification.timestamp instanceof Date
                        ? notification.timestamp.toLocaleString()
                        : new Date(notification.timestamp).toLocaleString()}
                    </p>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDismiss(notification.id);
                    }}
                    className="p-1 text-gray-500 hover:text-gray-300 transition-colors rounded-lg hover:bg-gray-700/50"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {notifications.length > 0 && (
        <div className="p-3 border-t border-gray-700/50 bg-gray-800/50">
          <Link
            to="/notifications"
            className="block text-center text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            View all notifications →
          </Link>
        </div>
      )}
    </div>
  );
};

/**
 * Enhanced User Menu Component
 */
const UserMenu = ({ user, isOpen, onToggle, onLogout, onProfileClick }) => {
  const navigate = useNavigate();

  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center space-x-2 lg:space-x-3 p-1.5 lg:p-2 rounded-xl lg:rounded-2xl text-gray-300 hover:text-white hover:bg-gray-800/50 transition-all group"
      >
        <div className="relative">
          <div className="w-9 h-9 lg:w-10 lg:h-10 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm lg:text-base shadow-lg group-hover:shadow-xl transition-shadow">
            {user?.full_name?.[0]?.toUpperCase() ||
              user?.email?.[0]?.toUpperCase() ||
              "U"}
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-gray-900" />
        </div>
        <div className="hidden lg:block text-left">
          <p className="text-sm font-medium text-white truncate max-w-[120px]">
            {user?.full_name || "User"}
          </p>
          <p className="text-xs text-gray-400 truncate max-w-[120px]">
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
        <div className="absolute right-0 top-full mt-2 w-72 bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden">
          <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-b border-gray-700/50">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                {user?.full_name?.[0]?.toUpperCase() ||
                  user?.email?.[0]?.toUpperCase() ||
                  "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-white truncate">
                  {user?.full_name || "User"}
                </p>
                <p className="text-sm text-gray-400 truncate">{user?.email}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full">
                    {user?.role || "Member"}
                  </span>
                  {user?.is_email_verified && (
                    <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full flex items-center gap-1">
                      <ShieldCheckIcon className="h-3 w-3" />
                      Verified
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="p-2">
            <button
              onClick={() => {
                onToggle();
                onProfileClick();
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-colors"
            >
              <UserCircleIcon className="h-5 w-5" />
              <span>Profile Settings</span>
            </button>
            <button
              onClick={() => {
                onToggle();
                navigate("/settings");
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-colors"
            >
              <Cog6ToothIcon className="h-5 w-5" />
              <span>Preferences</span>
            </button>
            <button
              onClick={() => {
                onToggle();
                window.open("/docs", "_blank");
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-colors"
            >
              <BookOpenIcon className="h-5 w-5" />
              <span>Documentation</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-colors">
              <QuestionMarkCircleIcon className="h-5 w-5" />
              <span>Help & Support</span>
            </button>
          </div>

          <div className="p-2 border-t border-gray-700/50">
            <button
              onClick={onLogout}
              className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-colors"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
              <span>Sign out</span>
            </button>
          </div>

          <div className="px-4 py-3 bg-gray-900/50 border-t border-gray-700/50">
            <p className="text-xs text-gray-500 text-center">
              SecureDevOps AI v2.0 • © 2025
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Theme Switcher Component
 */
const ThemeSwitcher = () => {
  const [theme, setTheme] = useState("dark");

  const themes = [
    { id: "light", icon: SunIcon, label: "Light" },
    { id: "dark", icon: MoonIcon, label: "Dark" },
    { id: "system", icon: ComputerDesktopIcon, label: "System" },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-800/50 rounded-xl border border-gray-700/50">
      {themes.map(({ id, icon: Icon }) => (
        <button
          key={id}
          onClick={() => setTheme(id)}
          className={`p-2 rounded-lg transition-all ${
            theme === id
              ? "bg-gray-700 text-white"
              : "text-gray-400 hover:text-white"
          }`}
          title={id}
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
};

/**
 * Main Enhanced Header Component
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

  // Keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchRef.current?.focus();
      }
      if (e.key === "Escape") {
        setSearchFocused(false);
        searchRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Close panels when clicking outside
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
        <div className="bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 px-4 py-2.5">
          <div className="flex items-center justify-center gap-2">
            <SparklesIcon className="h-4 w-4 text-white" />
            <p className="text-white text-sm font-medium">
              Please verify your email address to access all features.
            </p>
            <button
              onClick={async () => {
                try {
                  await resendVerificationEmail();
                } catch (error) {
                  // Error handled
                }
              }}
              className="ml-2 px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm font-semibold transition-colors"
            >
              Resend Email
            </button>
          </div>
        </div>
      )}

      {/* Main Header */}
      <div className="bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50">
        <div className="flex h-16 lg:h-18 items-center justify-between px-4 lg:px-6">
          {/* Left Section */}
          <div className="flex items-center gap-4">
            {/* Mobile menu button */}
            <button
              type="button"
              className="lg:hidden p-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
              onClick={onMenuClick}
            >
              <MenuIcon className="h-6 w-6" />
            </button>

            {/* Breadcrumb - Desktop */}
            <div className="hidden lg:block">
              <Breadcrumb />
            </div>
          </div>

          {/* Center - Search Bar */}
          <div className="flex-1 max-w-xl mx-4 hidden sm:block search-container">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                ref={searchRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                placeholder="Search projects, scans, vulnerabilities..."
                className="w-full pl-12 pr-20 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-gray-800/70 transition-all text-sm"
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                <kbd className="hidden lg:inline-flex items-center gap-1 px-2 py-1 bg-gray-700/50 rounded-md text-xs text-gray-400 border border-gray-600/50">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </div>

              <SearchResults
                query={searchQuery}
                isOpen={searchFocused && searchQuery.length > 0}
                onClose={() => {
                  setSearchFocused(false);
                  setSearchQuery("");
                }}
              />
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2 lg:gap-3">
            {/* Mobile search button */}
            <button className="sm:hidden p-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all">
              <MagnifyingGlassIcon className="h-5 w-5" />
            </button>

            {/* Theme Switcher - Desktop only */}
            <div className="hidden xl:block">
              <ThemeSwitcher />
            </div>

            {/* Notifications */}
            <div className="relative notification-panel">
              <button
                onClick={() => setNotificationPanelOpen(!notificationPanelOpen)}
                className="relative p-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
              >
                <BellIcon className="h-5 w-5" />
                {notifications.length > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-5 w-5 bg-gradient-to-r from-red-500 to-pink-500 rounded-full text-xs text-white flex items-center justify-center font-medium shadow-lg animate-pulse">
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
