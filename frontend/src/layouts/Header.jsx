/**
 * Header Component - Enterprise Glass Design
 * Matches the project's glass morphism and gradient design language
 */
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import {
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  ChevronDownIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  UserIcon,
  XMarkIcon,
  CommandLineIcon,
  ShieldExclamationIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "../components/auth";

/**
 * Search Component - Command Palette Style
 */
const SearchBar = ({ onOpen }) => {
  const inputRef = useRef(null);

  return (
    <>
      <button
        onClick={onOpen}
        ref={inputRef}
        aria-label="Open search"
        className="flex items-center gap-3 px-4 py-2.5 bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 
                   rounded-full text-gray-400 hover:text-white hover:border-gray-600/50 hover:bg-gray-800/70
                   transition-all duration-300 group min-w-[240px]
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <MagnifyingGlassIcon className="w-5 h-5" />
        <span className="text-sm lg:text-base flex-1 text-left">Search anything...</span>
        <kbd className="hidden sm:flex items-center gap-1 text-[10px] px-2 py-1 bg-gray-700/50 rounded-md text-gray-500 group-hover:text-gray-400">
          <CommandLineIcon className="w-3 h-3" />
          <span>K</span>
        </kbd>
      </button>
    </>
  );
};

/**
 * Notifications Dropdown
 */
const NotificationsDropdown = ({ notifications = [], onClear, onDismiss }) => {
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

  // Mark all as read when dropdown opens
  useEffect(() => {
    if (isOpen && notifications.length > 0) {
      const hasUnread = notifications.some((n) => !n.read);
      if (!hasUnread) return;
      const markRead = setTimeout(() => {
        notifications.forEach((n) => {
          n.read = true;
        });
      }, 0);
      return () => clearTimeout(markRead);
    }
  }, [isOpen, notifications]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const relativeTime = (date) => {
    const diff = Date.now() - new Date(date).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `${days}d ago`;
    return new Date(date).toLocaleDateString();
  };

  const getNotificationIcon = (notif) => {
    if (notif.type === "security_alert") {
      const sev = notif.severity;
      if (sev === "critical" || sev === "high") {
        return { icon: ShieldExclamationIcon, bg: "bg-red-500/20", color: "text-red-400" };
      }
      return { icon: ExclamationTriangleIcon, bg: "bg-amber-500/20", color: "text-amber-400" };
    }
    if (notif.type === "scan_update") {
      const msg = notif.message || "";
      if (msg.includes("completed"))
        return { icon: CheckCircleIcon, bg: "bg-emerald-500/20", color: "text-emerald-400" };
      if (msg.includes("failed"))
        return { icon: XMarkIcon, bg: "bg-red-500/20", color: "text-red-400" };
      if (msg.includes("started"))
        return { icon: BoltIcon, bg: "bg-cyan-500/20", color: "text-cyan-400" };
      return { icon: InformationCircleIcon, bg: "bg-blue-500/20", color: "text-blue-400" };
    }
    return { icon: InformationCircleIcon, bg: "bg-gray-500/20", color: "text-gray-400" };
  };

  const handleNotificationClick = (notif) => {
    const { data } = notif;
    const projectId = data?.project_id || data?.projectId;
    const reportId = data?.report_id || data?.reportId;
    if (projectId) {
      window.location.href = `/project/${projectId}`;
    } else if (reportId) {
      window.location.href = `/report/${reportId}`;
    }
  };

  const displayedNotifications = notifications.slice(0, 10);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className="relative p-2.5 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700/50 
                   border border-gray-700/50 hover:border-gray-600/50 rounded-full transition-all duration-300
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <BellIcon className="w-5 h-5" aria-hidden="true" />
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

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 mt-3 w-96"
          >
            {/* Glow */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-violet-500/10 rounded-2xl blur-xl" />

            <div className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800/50">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-600">
                  <BellIcon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-white text-base lg:text-lg">Notifications</h3>
                {unreadCount > 0 && (
                  <span className="text-xs px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400">
                    {unreadCount}
                  </span>
                )}
              </div>
              {notifications.length > 0 && (
                <button
                  onClick={onClear}
                  className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded-lg hover:bg-gray-800/50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
                >
                  Clear all
                </button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-5 py-12 text-center">
                  <div className="inline-flex p-4 rounded-2xl bg-gray-800/50 mb-4">
                    <BellIcon className="w-8 h-8 text-gray-500" />
                  </div>
                  <p className="text-gray-400">No notifications yet</p>
                  <p className="text-xs text-gray-600 mt-1">Real-time updates appear here</p>
                </div>
              ) : (
                <div className="py-1">
                  {displayedNotifications.map((notif) => {
                    const { icon: Icon, bg, color } = getNotificationIcon(notif);
                    return (
                      <div
                        key={notif.id}
                        onClick={() => handleNotificationClick(notif)}
                        className={`flex items-start gap-3 px-4 py-3 mx-1 rounded-xl transition-colors cursor-pointer
                          ${notif.read ? "hover:bg-gray-800/30" : "bg-gray-800/20 hover:bg-gray-800/40"}
                          ${notif.type === "security_alert" && !notif.read ? "border-l-2 border-red-500/50" : ""}`}
                      >
                        <div className={`p-2 rounded-lg shrink-0 ${bg} ${color}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p
                            className={`text-sm leading-snug ${notif.read ? "text-gray-400" : "text-white"}`}
                          >
                            {notif.message}
                          </p>
                          <p className="text-xs text-gray-600 mt-1">
                            {relativeTime(notif.timestamp)}
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDismiss?.(notif.id);
                          }}
                          className="p-1 rounded-lg text-gray-600 hover:text-gray-300 hover:bg-gray-700/50 opacity-0 group-hover:opacity-100 transition-all shrink-0 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
                          aria-label="Dismiss notification"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {notifications.length > 10 && (
              <div className="px-5 py-3 border-t border-gray-800/50 text-center">
                <span className="text-xs text-gray-500">
                  +{notifications.length - 10} more notifications
                </span>
              </div>
            )}
          </div>
        </motion.div>
      )}
      </AnimatePresence>
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
        aria-label={isOpen ? "Close user menu" : "Open user menu"}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className="flex items-center gap-3 p-2 rounded-full bg-gray-800/50 hover:bg-gray-700/50 
                   border border-gray-700/50 hover:border-gray-600/50 transition-all duration-300
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
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
          className={`w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 
                     flex items-center justify-center text-white text-sm font-semibold
                     shadow-lg shadow-cyan-500/25 ${user?.avatar_url ? "hidden" : ""}`}
        >
          {getInitials()}
        </div>

        <div className="hidden lg:block text-left">
          <p className="text-sm font-medium text-white leading-tight">
            {user?.full_name || user?.name || "User"}
          </p>
          <p className="text-xs text-gray-500 leading-tight">{user?.role || "Member"}</p>
        </div>

        <ChevronDownIcon
          className={`w-4 h-4 text-gray-500 transition-transform duration-300 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 mt-3 w-72"
          >
            {/* Glow */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-violet-500/10 rounded-2xl blur-xl" />

            <div className="relative bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden">
            {/* User Info Header */}
            <div className="p-5 border-b border-gray-800/50">
              <div className="flex items-center gap-4">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="" className="w-12 h-12 rounded-xl object-cover" />
                ) : (
                  <div
                    className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 
                                flex items-center justify-center text-white font-semibold shadow-lg"
                  >
                    {getInitials()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate text-base lg:text-lg">
                    {user?.full_name || user?.name}
                  </p>
                  <p className="text-sm lg:text-base text-gray-400 truncate">{user?.email}</p>
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
                         hover:text-white hover:bg-gray-800/50 rounded-xl transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
              >
                <div className="p-2 rounded-lg bg-gray-800/50">
                  <UserIcon className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-sm lg:text-base">Profile</p>
                  <p className="text-xs lg:text-sm text-gray-500">View and edit profile</p>
                </div>
              </button>

              <Link
                to="/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 
                         hover:text-white hover:bg-gray-800/50 rounded-xl transition-all"
              >
                <div className="p-2 rounded-lg bg-gray-800/50">
                  <Cog6ToothIcon className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-sm lg:text-base">Settings</p>
                  <p className="text-xs lg:text-sm text-gray-500">Preferences & security</p>
                </div>
              </Link>
            </div>

            {/* Logout */}
            <div className="p-2 border-t border-gray-800/50">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400
                         hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
              >
                <div className="p-2 rounded-lg bg-red-500/10">
                  <ArrowRightOnRectangleIcon className="w-5 h-5" />
                </div>
                <span className="font-medium text-sm lg:text-base">Sign out</span>
              </button>
            </div>
          </div>
        </motion.div>
      )}
      </AnimatePresence>
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
  onDismissNotification = () => {},
  onProfileClick,
  onCommandPaletteOpen,
}) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="sticky top-0 z-30"
    >
      {/* Glass background */}
      <div className="absolute inset-0 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50" />

      <div className="relative h-16 lg:h-18 px-4 lg:px-6 flex items-center justify-between gap-4">
        {/* Left: Mobile menu */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            aria-label="Open navigation menu"
            className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50 
                     hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all
                     focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
          >
            <Bars3Icon className="w-5 h-5 lg:w-6 lg:h-6" />
          </button>
        </div>

        {/* Right: Search + Notifications + User */}
        <div className="flex items-center gap-3">
          <div className="hidden md:block">
            <SearchBar onOpen={onCommandPaletteOpen} />
          </div>
          <NotificationsDropdown
            notifications={notifications}
            onClear={onClearNotifications}
            onDismiss={onDismissNotification}
          />
          <UserMenu onProfileClick={onProfileClick} />
        </div>
      </div>
    </motion.header>
  );
}
