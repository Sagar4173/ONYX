/**
 * Sidebar Component - Enterprise Glass Design
 * Matches the project's glass morphism and gradient design language
 */
import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  HomeIcon,
  FolderIcon,
  DocumentChartBarIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  UsersIcon,
  Cog6ToothIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../components/common";

// Navigation Configuration
const navigation = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: HomeIcon,
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    name: "Projects",
    path: "/projects",
    icon: FolderIcon,
    gradient: "from-violet-500 to-purple-500",
  },
  {
    name: "Reports",
    path: "/reports",
    icon: DocumentChartBarIcon,
    gradient: "from-emerald-500 to-green-500",
  },
  {
    name: "Analytics",
    path: "/analytics",
    icon: ChartBarIcon,
    gradient: "from-orange-500 to-amber-500",
  },
  {
    name: "Compliance",
    path: "/compliance",
    icon: ShieldCheckIcon,
    gradient: "from-pink-500 to-rose-500",
  },
  {
    name: "Users",
    path: "/users",
    icon: UsersIcon,
    gradient: "from-indigo-500 to-blue-500",
  },
  {
    name: "Audit Logs",
    path: "/audit-logs",
    icon: ClipboardDocumentListIcon,
    gradient: "from-teal-500 to-cyan-500",
  },
  {
    name: "Data Retention",
    path: "/retention-policies",
    icon: ClockIcon,
    gradient: "from-slate-500 to-gray-500",
  },
  {
    name: "Settings",
    path: "/settings",
    icon: Cog6ToothIcon,
    gradient: "from-gray-500 to-slate-500",
  },
];

/**
 * Navigation Item Component
 */
const NavItem = ({ item, collapsed, onClick }) => {
  const location = useLocation();
  const isActive =
    location.pathname === item.path ||
    (item.path !== "/dashboard" && location.pathname.startsWith(item.path));
  const Icon = item.icon;

  return (
    <NavLink
      to={item.path}
      onClick={onClick}
      className="group relative block"
      title={collapsed ? item.name : undefined}
    >
      {/* Active indicator */}
      {isActive && (
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full 
                       bg-gradient-to-b from-blue-500 to-purple-600 shadow-lg shadow-blue-500/50"
        />
      )}

      <div
        className={`
          flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-all duration-300
          ${
            isActive
              ? "bg-gradient-to-r from-gray-800/80 to-gray-800/40 text-white shadow-lg"
              : "text-gray-400 hover:text-white hover:bg-gray-800/50"
          }
          ${collapsed ? "justify-center mx-2 px-3" : ""}
        `}
      >
        {/* Icon with gradient background when active */}
        <div
          className={`
          relative p-2 rounded-xl transition-all duration-300
          ${
            isActive
              ? `bg-gradient-to-r ${item.gradient} shadow-lg`
              : "bg-gray-800/50 group-hover:bg-gray-700/50"
          }
        `}
        >
          <Icon className={`w-5 h-5 ${isActive ? "text-white" : ""}`} />
        </div>

        {!collapsed && (
          <span
            className={`text-sm font-medium transition-colors ${
              isActive ? "text-white" : ""
            }`}
          >
            {item.name}
          </span>
        )}

        {/* Hover glow effect */}
        {isActive && (
          <div
            className={`absolute inset-0 rounded-xl bg-gradient-to-r ${item.gradient} opacity-10 blur-xl`}
          />
        )}
      </div>
    </NavLink>
  );
};

/**
 * Logo Component
 */
const Logo = ({ collapsed }) => (
  <div className="flex items-center gap-3 px-4">
    <div className="relative">
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-xl blur-lg opacity-40" />
      <div
        className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-gray-900 to-gray-800 
                    flex items-center justify-center shadow-xl border border-cyan-500/30"
      >
        <OnyxLogo className="w-7 h-7" />
      </div>
    </div>
    {!collapsed && (
      <div>
        <h1 className="text-white font-bold text-lg tracking-wide">ONYX</h1>
        <p className="text-cyan-400/70 text-[10px] uppercase tracking-[0.2em]">
          Security Intelligence
        </p>
      </div>
    )}
  </div>
);

/**
 * Desktop Sidebar
 */
const DesktopSidebar = ({ collapsed, onToggle }) => {
  return (
    <aside
      className={`
        hidden lg:flex flex-col fixed left-0 top-0 h-screen z-40
        transition-all duration-300 ease-out
        ${collapsed ? "w-[80px]" : "w-[280px]"}
      `}
    >
      {/* Glass background */}
      <div className="absolute inset-0 bg-gray-900/90 backdrop-blur-xl border-r border-gray-800/50" />

      {/* Content */}
      <div className="relative flex flex-col h-full">
        {/* Logo */}
        <div className="h-16 lg:h-18 flex items-center border-b border-gray-800/50">
          <Logo collapsed={collapsed} />
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-6 space-y-1">
          {navigation.map((item) => (
            <NavItem key={item.path} item={item} collapsed={collapsed} />
          ))}
        </nav>

        {/* Collapse Toggle */}
        <div className="p-4 border-t border-gray-800/50">
          <button
            onClick={onToggle}
            className={`
              w-full flex items-center gap-3 px-4 py-3 rounded-xl
              text-gray-400 hover:text-white bg-gray-800/30 hover:bg-gray-800/50
              border border-gray-700/30 hover:border-gray-600/50
              transition-all duration-300
              ${collapsed ? "justify-center" : ""}
            `}
          >
            {collapsed ? (
              <ChevronRightIcon className="w-5 h-5" />
            ) : (
              <>
                <ChevronLeftIcon className="w-5 h-5" />
                <span className="text-sm font-medium">Collapse</span>
              </>
            )}
          </button>
        </div>
      </div>
    </aside>
  );
};

/**
 * Mobile Sidebar
 */
const MobileSidebar = ({ isOpen, onClose }) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="lg:hidden fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-[280px]">
        {/* Glass background */}
        <div className="absolute inset-0 bg-gray-900/95 backdrop-blur-xl border-r border-gray-800/50 shadow-2xl" />

        {/* Content */}
        <div className="relative flex flex-col h-full">
          {/* Header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800/50">
            <Logo collapsed={false} />
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white bg-gray-800/50 
                       hover:bg-gray-700/50 rounded-xl transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto py-6 space-y-1">
            {navigation.map((item) => (
              <NavItem
                key={item.path}
                item={item}
                collapsed={false}
                onClick={onClose}
              />
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-800/50">
            <div
              className="px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500/5 to-violet-500/5 
                          border border-cyan-500/20"
            >
              <p className="text-xs text-gray-400">
                <span className="text-cyan-400 font-semibold tracking-wide">
                  ONYX
                </span>
                <span className="text-gray-500"> • </span>
                <span className="text-gray-500">v1.0</span>
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
};

/**
 * Mobile Menu Button Export
 */
export const MobileMenuButton = ({ onClick }) => (
  <button
    onClick={onClick}
    className="lg:hidden p-2.5 text-gray-400 hover:text-white bg-gray-800/50 
             hover:bg-gray-700/50 border border-gray-700/50 rounded-xl transition-all"
  >
    <svg
      className="w-5 h-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  </button>
);

/**
 * Main Sidebar Export
 */
export default function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}) {
  return (
    <>
      <DesktopSidebar collapsed={collapsed} onToggle={onToggle} />
      <MobileSidebar isOpen={mobileOpen} onClose={onMobileClose} />
    </>
  );
}
