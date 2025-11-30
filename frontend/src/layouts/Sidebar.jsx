/**
 * Sidebar Component - Clean Production UI
 * Professional sidebar with navigation
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
} from "@heroicons/react/24/outline";

// Navigation items
const navigation = [
  { name: "Dashboard", path: "/dashboard", icon: HomeIcon },
  { name: "Projects", path: "/projects", icon: FolderIcon },
  { name: "Reports", path: "/reports", icon: DocumentChartBarIcon },
  { name: "Analytics", path: "/analytics", icon: ChartBarIcon },
  { name: "Compliance", path: "/compliance", icon: ShieldCheckIcon },
  { name: "Users", path: "/users", icon: UsersIcon },
  { name: "Audit Logs", path: "/audit-logs", icon: ClipboardDocumentListIcon },
  { name: "Data Retention", path: "/retention-policies", icon: ClockIcon },
  { name: "Settings", path: "/settings", icon: Cog6ToothIcon },
];

/**
 * Navigation Item
 */
const NavItem = ({ item, collapsed }) => {
  const location = useLocation();
  const isActive =
    location.pathname === item.path ||
    location.pathname.startsWith(item.path + "/");
  const Icon = item.icon;

  return (
    <NavLink
      to={item.path}
      className={`
        flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
        ${
          isActive
            ? "bg-blue-600 text-white shadow-lg shadow-blue-600/25"
            : "text-slate-400 hover:bg-slate-800 hover:text-white"
        }
        ${collapsed ? "justify-center" : ""}
      `}
      title={collapsed ? item.name : undefined}
    >
      <Icon
        className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-white" : ""}`}
      />
      {!collapsed && <span className="text-sm font-medium">{item.name}</span>}
    </NavLink>
  );
};

/**
 * Desktop Sidebar
 */
const DesktopSidebar = ({ collapsed, onToggle }) => {
  return (
    <aside
      className={`
        hidden lg:flex flex-col fixed left-0 top-0 h-screen z-40
        bg-slate-900 border-r border-slate-800
        transition-all duration-300 ease-in-out
        ${collapsed ? "w-[72px]" : "w-64"}
      `}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 
                          flex items-center justify-center shadow-lg"
            >
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <div>
              <h1 className="text-white font-bold text-sm">SecureDevOps</h1>
              <p className="text-slate-500 text-xs">AI Platform</p>
            </div>
          </div>
        )}
        {collapsed && (
          <div
            className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 
                        flex items-center justify-center shadow-lg mx-auto"
          >
            <span className="text-white font-bold text-lg">S</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navigation.map((item) => (
          <NavItem key={item.path} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-slate-800">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 
                   text-slate-400 hover:text-white hover:bg-slate-800 
                   rounded-lg transition-colors"
        >
          {collapsed ? (
            <ChevronRightIcon className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeftIcon className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
};

/**
 * Mobile Sidebar
 */
const MobileSidebar = ({ isOpen, onClose }) => {
  // Close on escape key
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
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-slate-900 border-r border-slate-800 shadow-xl">
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 
                          flex items-center justify-center"
            >
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <div>
              <h1 className="text-white font-bold text-sm">SecureDevOps</h1>
              <p className="text-slate-500 text-xs">AI Platform</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all
                ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }
              `}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.name}</span>
            </NavLink>
          ))}
        </nav>
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
    className="lg:hidden p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
  >
    <svg
      className="w-6 h-6"
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
