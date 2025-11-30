/**
 * Header Component - Clean Production UI
 * Professional header with search, notifications, and user profile
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
      <div className="flex items-center text-sm text-white font-medium">
        <HomeIcon className="w-4 h-4 mr-2 text-blue-400" />
        Dashboard
      </div>
    );
  }

  return (
    <nav className="flex items-center text-sm">
      <Link
        to="/dashboard"
        className="text-slate-400 hover:text-white transition-colors"
      >
        <HomeIcon className="w-4 h-4" />
      </Link>
      {segments.map((segment, i) => (
        <React.Fragment key={segment}>
          <ChevronRightIcon className="w-3 h-3 mx-2 text-slate-600" />
          {i === segments.length - 1 ? (
            <span className="text-white font-medium">
              {labels[segment] ||
                segment.charAt(0).toUpperCase() + segment.slice(1)}
            </span>
          ) : (
            <Link
              to={`/${segments.slice(0, i + 1).join("/")}`}
              className="text-slate-400 hover:text-white transition-colors"
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
 * Search Component
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
    <div className="relative">
      <button
        onClick={() => {
          setIsOpen(true);
          setTimeout(() => inputRef.current?.focus(), 100);
        }}
        className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 border border-slate-700/50 
                   rounded-lg text-slate-400 hover:text-white hover:border-slate-600 
                   transition-all duration-200 min-w-[200px]"
      >
        <MagnifyingGlassIcon className="w-4 h-4" />
        <span className="text-sm">Search...</span>
        <kbd className="ml-auto text-[10px] px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">
          ⌘K
        </kbd>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4">
          <div
            className="fixed inset-0 bg-black/60"
            onClick={() => setIsOpen(false)}
          />
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-700 rounded-xl shadow-2xl">
            <div className="flex items-center px-4 border-b border-slate-700">
              <MagnifyingGlassIcon className="w-5 h-5 text-slate-400" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search projects, reports, settings..."
                className="flex-1 px-3 py-4 bg-transparent text-white placeholder-slate-500 
                         outline-none text-sm"
              />
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-slate-400 hover:text-white"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 text-center text-slate-500 text-sm">
              {query
                ? `No results for "${query}"`
                : "Start typing to search..."}
            </div>
          </div>
        </div>
      )}
    </div>
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
        className="relative p-2 text-slate-400 hover:text-white hover:bg-slate-800 
                   rounded-lg transition-colors"
      >
        <BellIcon className="w-5 h-5" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full 
                         text-[10px] font-bold text-white flex items-center justify-center"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-700 
                       rounded-xl shadow-xl z-50 overflow-hidden"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
            <h3 className="text-sm font-semibold text-white">Notifications</h3>
            {notifications.length > 0 && (
              <button
                onClick={onClear}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Clear all
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-slate-500 text-sm">
                No notifications
              </div>
            ) : (
              notifications.slice(0, 5).map((notif) => (
                <div
                  key={notif.id}
                  className="px-4 py-3 hover:bg-slate-800/50 border-b border-slate-800 last:border-0"
                >
                  <p className="text-sm text-white">{notif.message}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {new Date(notif.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * User Menu Dropdown
 */
const UserMenu = () => {
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
        className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
      >
        <div
          className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 
                       flex items-center justify-center text-white text-sm font-semibold"
        >
          {getInitials()}
        </div>
        <div className="hidden md:block text-left">
          <p className="text-sm font-medium text-white leading-tight">
            {user?.full_name || user?.name || "User"}
          </p>
          <p className="text-xs text-slate-400 leading-tight">
            {user?.role || "Member"}
          </p>
        </div>
        <ChevronDownIcon
          className={`w-4 h-4 text-slate-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700 
                       rounded-xl shadow-xl z-50 overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-slate-700">
            <p className="text-sm font-medium text-white">
              {user?.full_name || user?.name}
            </p>
            <p className="text-xs text-slate-400">{user?.email}</p>
          </div>
          <div className="py-1">
            <Link
              to="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 text-sm text-slate-300 
                       hover:bg-slate-800 hover:text-white transition-colors"
            >
              <Cog6ToothIcon className="w-4 h-4" />
              Settings
            </Link>
            <Link
              to="/profile"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 text-sm text-slate-300 
                       hover:bg-slate-800 hover:text-white transition-colors"
            >
              <UserIcon className="w-4 h-4" />
              Profile
            </Link>
          </div>
          <div className="border-t border-slate-700 py-1">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-400 
                       hover:bg-red-500/10 transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-4 h-4" />
              Sign out
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
export default function Header({
  onMenuClick,
  notifications = [],
  onClearNotifications,
}) {
  return (
    <header className="sticky top-0 z-30 h-16 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800">
      <div className="h-full px-4 lg:px-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
          >
            <Bars3Icon className="w-5 h-5" />
          </button>
          <Breadcrumb />
        </div>
        <div className="flex items-center gap-2">
          <div className="hidden sm:block">
            <SearchBar />
          </div>
          <NotificationsDropdown
            notifications={notifications}
            onClear={onClearNotifications}
          />
          <div className="w-px h-6 bg-slate-700 mx-1" />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
