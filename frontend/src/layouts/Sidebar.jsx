/**
 * Enhanced Sidebar Component
 * Modern sidebar with collapsible sections, badges, and improved UX
 */
import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  XMarkIcon,
  PlusIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ShieldCheckIcon,
  WifiIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
} from "@heroicons/react/24/outline";
import { navigation, getNavigationByCategory } from "../config/navigation";

/**
 * Connection Status Component
 */
const ConnectionStatus = ({ isConnected = true }) => {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-all ${
        isConnected
          ? "bg-green-500/10 text-green-400"
          : "bg-red-500/10 text-red-400"
      }`}
    >
      <div className="relative">
        <WifiIcon className="h-4 w-4" />
        {isConnected && (
          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        )}
      </div>
      <span className="text-xs font-medium">
        {isConnected ? "Live Sync" : "Offline"}
      </span>
    </div>
  );
};

/**
 * Badge Component for navigation items
 */
const NavBadge = ({ count, type = "default" }) => {
  if (!count) return null;

  const colors = {
    default: "bg-gray-700 text-gray-300",
    primary: "bg-blue-500 text-white",
    warning: "bg-yellow-500 text-black",
    danger: "bg-red-500 text-white",
    success: "bg-green-500 text-white",
  };

  return (
    <span
      className={`ml-auto px-2 py-0.5 text-xs font-medium rounded-full ${colors[type]}`}
    >
      {count > 99 ? "99+" : count}
    </span>
  );
};

/**
 * Navigation Link Component
 */
const NavLink = ({ item, isCollapsed, isActive }) => {
  const Icon = item.icon;
  const path = item.path || item.href;

  if (isCollapsed) {
    return (
      <Link
        to={path}
        className={`group relative flex items-center justify-center p-3 rounded-xl transition-all ${
          isActive
            ? "bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white"
            : "text-gray-400 hover:text-white hover:bg-gray-800/50"
        }`}
        title={item.name}
      >
        <Icon className={`h-5 w-5 ${isActive ? "text-blue-400" : ""}`} />
        {item.badge && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-medium rounded-full flex items-center justify-center">
            {item.badge > 9 ? "9+" : item.badge}
          </span>
        )}
        {/* Tooltip */}
        <div className="absolute left-full ml-3 px-3 py-2 bg-gray-800 text-white text-sm rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50 shadow-xl">
          {item.name}
          {item.badge && (
            <span className="ml-2 px-1.5 py-0.5 bg-red-500 text-xs rounded-full">
              {item.badge}
            </span>
          )}
        </div>
      </Link>
    );
  }

  return (
    <Link
      to={path}
      className={`group flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
        isActive
          ? "bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-l-4 border-blue-500"
          : "text-gray-400 hover:text-white hover:bg-gray-800/50"
      }`}
    >
      <Icon
        className={`h-5 w-5 flex-shrink-0 ${
          isActive ? "text-blue-400" : "group-hover:text-blue-400"
        }`}
      />
      <span className="text-sm font-medium flex-1">{item.name}</span>
      <NavBadge count={item.badge} type={item.badgeType} />
    </Link>
  );
};

/**
 * Navigation Section Component
 */
const NavSection = ({ title, items, isCollapsed }) => {
  const [isOpen, setIsOpen] = useState(true);
  const location = useLocation();

  if (isCollapsed) {
    return (
      <div className="space-y-1">
        {items.map((item) => {
          const path = item.path || item.href;
          return (
            <NavLink
              key={path}
              item={item}
              isCollapsed={isCollapsed}
              isActive={location.pathname === path}
            />
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {title && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors"
        >
          <span>{title}</span>
          <ChevronDownIcon
            className={`h-3 w-3 transition-transform ${
              isOpen ? "rotate-0" : "-rotate-90"
            }`}
          />
        </button>
      )}
      {isOpen && (
        <div className="space-y-1">
          {items.map((item) => {
            const path = item.path || item.href;
            return (
              <NavLink
                key={path}
                item={item}
                isCollapsed={isCollapsed}
                isActive={location.pathname === path}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

/**
 * Quick Stats Component (Sidebar Footer)
 */
const QuickStats = ({ isCollapsed }) => {
  const stats = [
    { label: "Projects", value: 12, trend: "+3" },
    { label: "Scans Today", value: 47, trend: "+12" },
    { label: "Issues Fixed", value: 89, trend: "+24" },
  ];

  if (isCollapsed) {
    return (
      <div className="p-2">
        <div className="flex flex-col items-center gap-2 p-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl">
          <ArrowTrendingUpIcon className="h-5 w-5 text-green-400" />
          <span className="text-xs text-gray-400">+24</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 border-t border-gray-800/50">
      <div className="p-4 bg-gradient-to-r from-gray-800/50 to-gray-800/30 rounded-2xl border border-gray-700/30">
        <div className="flex items-center gap-2 mb-3">
          <ArrowTrendingUpIcon className="h-4 w-4 text-green-400" />
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Quick Stats
          </span>
        </div>
        <div className="space-y-3">
          {stats.map((stat) => (
            <div key={stat.label} className="flex items-center justify-between">
              <span className="text-sm text-gray-400">{stat.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">
                  {stat.value}
                </span>
                <span className="text-xs text-green-400">{stat.trend}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * User Profile Section (Bottom of Sidebar)
 */
const UserSection = ({ user, isCollapsed }) => {
  const navigate = useNavigate();

  if (isCollapsed) {
    return (
      <div className="p-2">
        <button
          onClick={() => navigate("/settings")}
          className="w-full flex items-center justify-center p-3 rounded-xl hover:bg-gray-800/50 transition-all group"
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm shadow-lg">
              {user?.full_name?.[0]?.toUpperCase() ||
                user?.email?.[0]?.toUpperCase() ||
                "U"}
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-gray-900" />
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 border-t border-gray-800/50">
      <button
        onClick={() => navigate("/settings")}
        className="w-full flex items-center gap-3 p-3 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all group"
      >
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm shadow-lg">
            {user?.full_name?.[0]?.toUpperCase() ||
              user?.email?.[0]?.toUpperCase() ||
              "U"}
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-gray-900" />
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-sm font-medium text-white truncate">
            {user?.full_name || "User"}
          </p>
          <p className="text-xs text-gray-400 truncate">{user?.email}</p>
        </div>
        <ChevronRightIcon className="h-4 w-4 text-gray-500 group-hover:text-gray-300 transition-colors" />
      </button>
    </div>
  );
};

/**
 * Desktop Sidebar Component
 */
export const DesktopSidebar = ({ user, isCollapsed, onToggleCollapse }) => {
  const navigate = useNavigate();

  return (
    <aside
      className={`hidden lg:flex flex-col bg-gray-900/95 backdrop-blur-xl border-r border-gray-800/50 transition-all duration-300 ${
        isCollapsed ? "w-20" : "w-72"
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-800/50">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <Link to="/" className="flex items-center gap-3 group">
              <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg group-hover:shadow-xl transition-shadow">
                <ShieldCheckIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">SecureDevOps</h1>
                <p className="text-xs text-gray-400">AI Security Platform</p>
              </div>
            </Link>
          )}
          {isCollapsed && (
            <Link
              to="/"
              className="mx-auto p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg"
            >
              <ShieldCheckIcon className="h-6 w-6 text-white" />
            </Link>
          )}
          <button
            onClick={onToggleCollapse}
            className={`p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all ${
              isCollapsed ? "hidden" : ""
            }`}
          >
            <ChevronLeftIcon className="h-4 w-4" />
          </button>
        </div>

        {/* Expand button when collapsed */}
        {isCollapsed && (
          <button
            onClick={onToggleCollapse}
            className="w-full mt-3 p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all flex items-center justify-center"
          >
            <ChevronRightIcon className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* New Project Button */}
      <div className="p-4">
        {isCollapsed ? (
          <button
            onClick={() => navigate("/projects?action=new")}
            className="w-full flex items-center justify-center p-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg hover:shadow-xl transition-all"
            title="New Project"
          >
            <PlusIcon className="h-5 w-5" />
          </button>
        ) : (
          <button
            onClick={() => navigate("/projects?action=new")}
            className="w-full flex items-center justify-center gap-2 p-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all"
          >
            <PlusIcon className="h-5 w-5" />
            <span>New Project</span>
            <SparklesIcon className="h-4 w-4 opacity-60" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
        {/* Main Navigation */}
        <NavSection
          items={getNavigationByCategory("main")}
          isCollapsed={isCollapsed}
        />

        {/* Enterprise Navigation */}
        <NavSection
          title="Enterprise"
          items={getNavigationByCategory("enterprise")}
          isCollapsed={isCollapsed}
        />

        {/* Settings Navigation */}
        <NavSection
          title="Settings"
          items={getNavigationByCategory("settings")}
          isCollapsed={isCollapsed}
        />
      </nav>

      {/* Quick Stats */}
      <QuickStats isCollapsed={isCollapsed} />

      {/* Connection Status */}
      <div className={`px-4 pb-2 ${isCollapsed ? "px-2" : ""}`}>
        {isCollapsed ? (
          <div className="flex justify-center">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
          </div>
        ) : (
          <ConnectionStatus isConnected={true} />
        )}
      </div>

      {/* User Section */}
      <UserSection user={user} isCollapsed={isCollapsed} />
    </aside>
  );
};

/**
 * Mobile Sidebar Component
 */
export const MobileSidebar = ({ isOpen, onClose, user }) => {
  const navigate = useNavigate();

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
        onClick={onClose}
      />

      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-80 max-w-[85vw] bg-gray-900/98 backdrop-blur-xl border-r border-gray-800/50 z-50 lg:hidden flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-800/50">
          <div className="flex items-center justify-between">
            <Link to="/" onClick={onClose} className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
                <ShieldCheckIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">SecureDevOps</h1>
                <p className="text-xs text-gray-400">AI Security Platform</p>
              </div>
            </Link>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* New Project Button */}
        <div className="p-4">
          <button
            onClick={() => {
              onClose();
              navigate("/projects?action=new");
            }}
            className="w-full flex items-center justify-center gap-2 p-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium shadow-lg"
          >
            <PlusIcon className="h-5 w-5" />
            <span>New Project</span>
            <SparklesIcon className="h-4 w-4 opacity-60" />
          </button>
        </div>

        {/* Navigation */}
        <nav
          className="flex-1 overflow-y-auto px-3 py-2 space-y-4"
          onClick={onClose}
        >
          <NavSection
            items={getNavigationByCategory("main")}
            isCollapsed={false}
          />
          <NavSection
            title="Enterprise"
            items={getNavigationByCategory("enterprise")}
            isCollapsed={false}
          />
          <NavSection
            title="Settings"
            items={getNavigationByCategory("settings")}
            isCollapsed={false}
          />
        </nav>

        {/* Quick Stats */}
        <QuickStats isCollapsed={false} />

        {/* Connection Status */}
        <div className="px-4 pb-2">
          <ConnectionStatus isConnected={true} />
        </div>

        {/* User Section */}
        <UserSection user={user} isCollapsed={false} />
      </aside>
    </>
  );
};

export default { DesktopSidebar, MobileSidebar };
