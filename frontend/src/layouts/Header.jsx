/**
 * Header Component
 * Modern header with glassmorphism, notifications, and user profile
 */
import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  BellIcon,
  MagnifyingGlassIcon,
  Bars3Icon as MenuIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "../components/auth";

/**
 * Notification Panel Component
 */
const NotificationPanel = ({ notifications, isOpen, onClear, onDismiss }) => {
  if (!isOpen) return null;

  return (
    <div className="absolute right-0 top-full mt-2 w-80 bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Notifications</h3>
          {notifications.length > 0 && (
            <button
              onClick={onClear}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Clear All
            </button>
          )}
        </div>

        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="text-center py-8">
              <BellIcon className="h-12 w-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No notifications</p>
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className="p-3 rounded-xl bg-gray-700/50 border border-gray-600/30 hover:bg-gray-700/70 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {notification.type === "scan_started" && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        )}
                        {notification.type === "scan_update" && (
                          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        )}
                        {notification.type === "scan_error" && (
                          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        )}
                        {notification.type === "scan_completed" && (
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        )}
                        {notification.type === "system" && (
                          <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                        )}
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
                      </div>
                      <p className="text-sm text-gray-300">
                        {notification.message || "Notification"}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
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
                      className="text-gray-500 hover:text-gray-300 transition-colors"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M6 18L18 6M6 6l12 12"
                        ></path>
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * User Menu Component
 */
const UserMenu = ({ user, isOpen, onToggle, onLogout, onProfileClick }) => {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center space-x-2 lg:space-x-3 p-2 lg:p-3 rounded-xl lg:rounded-2xl text-gray-300 hover:text-white hover:bg-gray-800/50 transition-all"
      >
        <div className="w-8 h-8 lg:w-10 lg:h-10 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-sm lg:text-base">
          {user?.full_name?.[0]?.toUpperCase() ||
            user?.email?.[0]?.toUpperCase() ||
            "U"}
        </div>
        <div className="hidden lg:block text-left">
          <p className="text-sm font-medium text-white truncate max-w-[120px]">
            {user?.full_name || "User"}
          </p>
          <p className="text-xs text-gray-400 truncate max-w-[120px]">
            {user?.email}
          </p>
        </div>
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-56 bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50">
          <div className="p-2">
            <button
              onClick={onProfileClick}
              className="w-full flex items-center px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-colors"
            >
              <UserCircleIcon className="h-5 w-5 mr-3" />
              <span>Profile Settings</span>
            </button>
            <button
              onClick={onLogout}
              className="w-full flex items-center px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-colors"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5 mr-3" />
              <span>Logout</span>
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
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [notificationPanelOpen, userMenuOpen]);

  return (
    <div className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50">
      {/* Email Verification Banner */}
      {user && !user.is_email_verified && (
        <div className="bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 text-center">
          <p className="text-white text-sm font-medium">
            Please verify your email address to access all features.{" "}
            <button
              onClick={async () => {
                try {
                  await resendVerificationEmail();
                } catch (error) {
                  // Error already handled in the function
                }
              }}
              className="underline hover:no-underline font-semibold"
            >
              Resend verification email
            </button>
          </p>
        </div>
      )}

      <div className="flex h-16 lg:h-20 items-center justify-between px-4 lg:px-8">
        {/* Mobile menu button */}
        <button
          type="button"
          className="lg:hidden p-3 rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
          onClick={onMenuClick}
        >
          <MenuIcon className="h-6 w-6" />
        </button>

        {/* Enhanced Search Bar */}
        <div className="flex-1 max-w-lg mx-4 lg:mx-8 hidden sm:block">
          <div className="relative group">
            <MagnifyingGlassIcon className="absolute left-3 lg:left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 lg:h-5 lg:w-5 text-gray-400 group-focus-within:text-blue-400 transition-colors" />
            <input
              type="text"
              placeholder="Search repositories, scans, vulnerabilities..."
              className="w-full pl-10 lg:pl-12 pr-3 lg:pr-4 py-2 lg:py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl lg:rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-gray-800/70 transition-all hover:bg-gray-800/60 text-sm lg:text-base"
            />
            <div className="absolute inset-0 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500/0 via-purple-500/0 to-pink-500/0 group-focus-within:from-blue-500/10 group-focus-within:via-purple-500/5 group-focus-within:to-pink-500/10 transition-all pointer-events-none" />
          </div>
        </div>

        {/* Right side actions */}
        <div className="flex items-center space-x-2 lg:space-x-4">
          {/* Mobile search button */}
          <button className="sm:hidden p-2 lg:p-3 rounded-xl lg:rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all">
            <MagnifyingGlassIcon className="h-5 w-5 lg:h-6 lg:w-6" />
          </button>

          {/* Notifications */}
          <div className="relative notification-panel">
            <button
              onClick={() => setNotificationPanelOpen(!notificationPanelOpen)}
              className="relative p-2 lg:p-3 rounded-xl lg:rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all hover:scale-105"
            >
              <BellIcon className="h-5 w-5 lg:h-6 lg:w-6" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 h-4 w-4 lg:h-5 lg:w-5 bg-gradient-to-r from-red-500 to-pink-500 rounded-full text-xs text-white flex items-center justify-center animate-pulse shadow-lg">
                  {notifications.length > 9 ? "9+" : notifications.length}
                </span>
              )}
            </button>

            <NotificationPanel
              notifications={notifications}
              isOpen={notificationPanelOpen}
              onClear={onClearNotifications}
              onDismiss={onDismissNotification}
            />
          </div>

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
  );
};

export default Header;
