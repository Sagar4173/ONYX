/**
 * Header Component - Enterprise Glass Design
 * Matches the project's glass morphism and gradient design language
 */
import React, { useState, useRef, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  ChevronDownIcon,
  ChevronRightIcon,
  HomeIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  UserIcon,
  XMarkIcon,
  CommandLineIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "../components/auth";

/**
 * Breadcrumb Navigation
 */
const Breadcrumb = () => {
  const location = useLocation();
  const segments = location.pathname.split("/").filter(Boolean);

  const labels = {
    dashboard: "Dashboard",
    projects: "Projects",
    project: "Project",
    reports: "Reports",
    report: "Report",
    analytics: "Analytics",
    settings: "Settings",
    compliance: "Compliance",
    users: "Users",
    "audit-logs": "Audit Logs",
    "retention-policies": "Data Retention",
  };

  if (segments.length === 0) {
    return (
      <div className="flex items-center gap-2">
        <div className="p-1.5 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600">
          <HomeIcon className="w-4 h-4 text-white" />
        </div>
        <span className="text-white font-medium">Dashboard</span>
      </div>
    );
  }

  return (
    <nav className="flex items-center gap-2 text-sm">
      <Link
        to="/dashboard"
        className="p-1.5 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
      >
        <HomeIcon className="w-4 h-4 text-gray-400" />
      </Link>
      {segments.map((segment, i) => (
        <React.Fragment key={segment + i}>
          <ChevronRightIcon className="w-4 h-4 text-gray-600" />
          {i === segments.length - 1 ? (
            <span className="px-3 py-1.5 rounded-lg bg-gray-800/50 text-white font-medium">
              {labels[segment] ||
                segment.charAt(0).toUpperCase() + segment.slice(1)}
            </span>
          ) : (
            <Link
              to={`/${segments.slice(0, i + 1).join("/")}`}
              className="px-3 py-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
            >
              {labels[segment] ||
                segment.charAt(0).toUpperCase() + segment.slice(1)}
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

/**
 * Search Component - Command Palette Style
 */
const SearchBar = () => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen(true);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
      if (e.key === "Escape") {
        setIsOpen(false);
        setQuery("");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <button
        onClick={() => {
          setIsOpen(true);
          setTimeout(() => inputRef.current?.focus(), 100);
        }}
        className="flex items-center gap-3 px-4 py-2.5 bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 
                   rounded-xl text-gray-400 hover:text-white hover:border-gray-600/50 hover:bg-gray-800/70
                   transition-all duration-300 group min-w-[240px]"
      >
        <MagnifyingGlassIcon className="w-4 h-4" />
        <span className="text-sm flex-1 text-left">Search anything...</span>
        <kbd className="hidden sm:flex items-center gap-1 text-[10px] px-2 py-1 bg-gray-700/50 rounded-md text-gray-500 group-hover:text-gray-400">
          <CommandLineIcon className="w-3 h-3" />
          <span>K</span>
        </kbd>
      </button>

      {/* Search Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          <div className="relative w-full max-w-2xl">
            {/* Glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl blur-xl" />

            <div className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden">
              <div className="flex items-center px-5 border-b border-gray-800/50">
                <MagnifyingGlassIcon className="w-5 h-5 text-gray-500" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search projects, reports, settings..."
                  className="flex-1 px-4 py-5 bg-transparent text-white placeholder-gray-500 
                           outline-none text-base"
                />
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-gray-500 hover:text-white hover:bg-gray-800/50 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6">
                {query ? (
                  <div className="text-center py-8">
                    <div className="inline-flex p-4 rounded-2xl bg-gray-800/50 mb-4">
                      <MagnifyingGlassIcon className="w-8 h-8 text-gray-500" />
                    </div>
                    <p className="text-gray-400">No results for "{query}"</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quick Actions
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: "New Project", icon: "📁", path: "/projects" },
                        { label: "View Reports", icon: "📊", path: "/reports" },
                        { label: "Analytics", icon: "📈", path: "/analytics" },
                        { label: "Settings", icon: "⚙️", path: "/settings" },
                      ].map((item) => (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => setIsOpen(false)}
                          className="flex items-center gap-3 p-3 rounded-xl bg-gray-800/50 hover:bg-gray-700/50 
                                   border border-gray-700/30 hover:border-gray-600/50 transition-all group"
                        >
                          <span className="text-xl">{item.icon}</span>
                          <span className="text-sm text-gray-300 group-hover:text-white">
                            {item.label}
                          </span>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

/**
 * Notifications Dropdown
 */
const NotificationsDropdown = ({ notifications = [], onClear }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2.5 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700/50 
                   border border-gray-700/50 hover:border-gray-600/50 rounded-xl transition-all duration-300"
      >
        <BellIcon className="w-5 h-5" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-r from-red-500 to-pink-500 
                         rounded-full text-[10px] font-bold text-white flex items-center justify-center
                         shadow-lg shadow-red-500/30"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-96">
          {/* Glow */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl blur-xl" />

          <div
            className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 
                         rounded-2xl shadow-2xl overflow-hidden"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800/50">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600">
                  <BellIcon className="w-4 h-4 text-white" />
                </div>
                <h3 className="font-semibold text-white">Notifications</h3>
              </div>
              {notifications.length > 0 && (
                <button
                  onClick={onClear}
                  className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded-lg hover:bg-gray-800/50 transition-colors"
                >
                  Clear all
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-5 py-12 text-center">
                  <div className="inline-flex p-4 rounded-2xl bg-gray-800/50 mb-4">
                    <BellIcon className="w-8 h-8 text-gray-500" />
                  </div>
                  <p className="text-gray-400">No notifications yet</p>
                </div>
              ) : (
                <div className="p-2">
                  {notifications.slice(0, 5).map((notif) => (
                    <div
                      key={notif.id}
                      className="p-4 rounded-xl hover:bg-gray-800/50 transition-colors cursor-pointer"
                    >
                      <p className="text-sm text-white">{notif.message}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(notif.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * User Menu Dropdown
 */
const UserMenu = ({ onProfileClick }) => {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const getInitials = () => {
    if (!user) return "U";
    const name = user.full_name || user.name || user.email || "";
    const parts = name.split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase() || "U";
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 p-2 rounded-xl bg-gray-800/50 hover:bg-gray-700/50 
                   border border-gray-700/50 hover:border-gray-600/50 transition-all duration-300"
      >
        {/* Avatar */}
        {user?.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user?.full_name || "User"}
            className="w-8 h-8 rounded-lg object-cover"
            onError={(e) => {
              e.target.style.display = "none";
              e.target.nextSibling.style.display = "flex";
            }}
          />
        ) : null}
        <div
          className={`w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 
                     flex items-center justify-center text-white text-sm font-semibold
                     shadow-lg shadow-blue-500/25 ${
                       user?.avatar_url ? "hidden" : ""
                     }`}
        >
          {getInitials()}
        </div>

        <div className="hidden lg:block text-left">
          <p className="text-sm font-medium text-white leading-tight">
            {user?.full_name || user?.name || "User"}
          </p>
          <p className="text-xs text-gray-500 leading-tight">
            {user?.role || "Member"}
          </p>
        </div>

        <ChevronDownIcon
          className={`w-4 h-4 text-gray-500 transition-transform duration-300 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-72">
          {/* Glow */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl blur-xl" />

          <div
            className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 
                         rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* User Info Header */}
            <div className="p-5 border-b border-gray-800/50">
              <div className="flex items-center gap-4">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="w-12 h-12 rounded-xl object-cover"
                  />
                ) : (
                  <div
                    className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 
                                flex items-center justify-center text-white font-semibold shadow-lg"
                  >
                    {getInitials()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate">
                    {user?.full_name || user?.name}
                  </p>
                  <p className="text-sm text-gray-400 truncate">
                    {user?.email}
                  </p>
                </div>
              </div>
            </div>

            {/* Menu Items */}
            <div className="p-2">
              <button
                onClick={() => {
                  setIsOpen(false);
                  onProfileClick?.();
                }}
                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 
                         hover:text-white hover:bg-gray-800/50 rounded-xl transition-all"
              >
                <div className="p-2 rounded-lg bg-gray-800/50">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <p className="font-medium">Profile</p>
                  <p className="text-xs text-gray-500">View and edit profile</p>
                </div>
              </button>

              <Link
                to="/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 
                         hover:text-white hover:bg-gray-800/50 rounded-xl transition-all"
              >
                <div className="p-2 rounded-lg bg-gray-800/50">
                  <Cog6ToothIcon className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <p className="font-medium">Settings</p>
                  <p className="text-xs text-gray-500">
                    Preferences & security
                  </p>
                </div>
              </Link>
            </div>

            {/* Logout */}
            <div className="p-2 border-t border-gray-800/50">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 
                         hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-all"
              >
                <div className="p-2 rounded-lg bg-red-500/10">
                  <ArrowRightOnRectangleIcon className="w-4 h-4" />
                </div>
                <span className="font-medium">Sign out</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Main Header Component
 */
export default function Header({
  onMenuClick,
  notifications = [],
  onClearNotifications,
  onProfileClick,
}) {
  return (
    <header className="sticky top-0 z-30">
      {/* Glass background */}
      <div className="absolute inset-0 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50" />

      <div className="relative h-16 lg:h-18 px-4 lg:px-6 flex items-center justify-between gap-4">
        {/* Left: Mobile menu + Breadcrumb */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50 
                     hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all"
          >
            <Bars3Icon className="w-5 h-5" />
          </button>
          <Breadcrumb />
        </div>

        {/* Right: Search + Notifications + User */}
        <div className="flex items-center gap-3">
          <div className="hidden md:block">
            <SearchBar />
          </div>
          <NotificationsDropdown
            notifications={notifications}
            onClear={onClearNotifications}
          />
          <UserMenu onProfileClick={onProfileClick} />
        </div>
      </div>
    </header>
  );
}
