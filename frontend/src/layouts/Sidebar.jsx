/**
 * Sidebar Component
 * Modern sidebar with glassmorphism design
 */
import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  ShieldCheckIcon,
  PlusIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  XMarkIcon as XIcon,
} from "@heroicons/react/24/outline";
import { ShieldCheckIcon as ShieldCheckSolid } from "@heroicons/react/24/solid";
import { navigation, getNavigationByCategory } from "../config/navigation";

/**
 * Navigation Link Component
 */
const NavLink = ({ item, isActive, onClick }) => (
  <Link
    to={item.href}
    onClick={onClick}
    className={`flex items-center px-3 py-3 rounded-xl transition-all group ${
      isActive
        ? "bg-gray-800/50 text-white shadow-lg border border-gray-700/30"
        : "text-gray-400 hover:text-white hover:bg-gray-800/30"
    }`}
  >
    <div
      className={`p-2 rounded-xl bg-gradient-to-r ${item.gradient} ${
        isActive ? "shadow-lg" : "opacity-60 group-hover:opacity-100"
      }`}
    >
      <item.icon className="h-4 w-4 text-white" />
    </div>
    <span className="ml-3 font-medium text-sm">{item.name}</span>
    {isActive && (
      <div className="ml-auto w-1.5 h-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-600" />
    )}
  </Link>
);

/**
 * Navigation Section Component
 */
const NavSection = ({ title, items, onLinkClick }) => {
  const location = useLocation();

  return (
    <div className="mb-6">
      {title && (
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
          {title}
        </p>
      )}
      <div className="space-y-1">
        {items.map((item) => {
          const isActive =
            location.pathname === item.href ||
            (item.href === "/dashboard" &&
              location.pathname === "/dashboard") ||
            (item.href !== "/dashboard" &&
              item.href !== "/" &&
              location.pathname.startsWith(item.href));
          return (
            <NavLink
              key={item.name}
              item={item}
              isActive={isActive}
              onClick={onLinkClick}
            />
          );
        })}
      </div>
    </div>
  );
};

/**
 * Connection Status Component
 */
const ConnectionStatus = ({ isConnected }) => (
  <div className="p-6 border-t border-gray-800/50">
    <div
      className={`relative flex items-center p-4 rounded-2xl transition-all duration-500 ${
        isConnected
          ? "bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30"
          : "bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30"
      }`}
    >
      {/* Animated background glow */}
      <div
        className={`absolute inset-0 rounded-2xl blur-xl transition-all ${
          isConnected ? "bg-green-500/20 animate-glow" : "bg-red-500/20"
        }`}
      />

      <div className="relative flex items-center">
        <div className="relative mr-3">
          <div
            className={`h-3 w-3 rounded-full ${
              isConnected ? "bg-green-400" : "bg-red-400"
            } animate-pulse`}
          />
          {isConnected && (
            <div className="absolute inset-0 h-3 w-3 rounded-full bg-green-400 animate-ping" />
          )}
        </div>
        <div>
          <p className="text-sm font-medium text-white flex items-center">
            {isConnected ? (
              <>
                <span>Real-time Active</span>
                <CheckCircleIcon className="h-4 w-4 text-green-400 ml-1" />
              </>
            ) : (
              <>
                <span>Disconnected</span>
                <ArrowPathIcon className="h-4 w-4 text-red-400 ml-1 animate-spin" />
              </>
            )}
          </p>
          <p className="text-xs text-gray-400">
            {isConnected
              ? "Live monitoring & notifications"
              : "Attempting to reconnect..."}
          </p>
        </div>
      </div>
    </div>
  </div>
);

/**
 * Desktop Sidebar Component
 */
export const DesktopSidebar = ({ isConnected }) => {
  return (
    <div className="fixed inset-y-0 left-0 z-40 w-72 transform bg-gray-900/95 backdrop-blur-xl border-r border-gray-800/50 translate-x-0">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-purple-500/5 to-pink-500/5" />

      <div className="relative flex flex-col h-full">
        {/* Brand Header */}
        <div className="flex items-center px-6 py-8">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
              <ShieldCheckSolid className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                SecureDevOps AI
              </h1>
              <p className="text-xs text-gray-400">
                Advanced Security Platform
              </p>
            </div>
          </div>
        </div>

        {/* Quick Action - Navigate to Projects */}
        <div className="px-6 mb-8">
          <Link
            to="/projects?action=new"
            className="relative w-full p-4 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-2xl flex items-center justify-center space-x-2 group overflow-hidden transform hover:scale-105"
          >
            {/* Animated background */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-700 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Shimmer effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />

            <div className="relative flex items-center space-x-2">
              <PlusIcon className="h-5 w-5 group-hover:rotate-90 transition-all duration-300" />
              <span className="font-semibold">New Project</span>
              <ShieldCheckIcon className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-all" />
            </div>
          </Link>
        </div>

        {/* Navigation - Grouped */}
        <nav className="flex-1 px-6 overflow-y-auto">
          <NavSection title="Main" items={getNavigationByCategory("main")} />
          <NavSection
            title="Enterprise"
            items={getNavigationByCategory("enterprise")}
          />
          <NavSection items={getNavigationByCategory("settings")} />
        </nav>

        {/* Connection Status */}
        <ConnectionStatus isConnected={isConnected} />
      </div>
    </div>
  );
};

/**
 * Mobile Sidebar Component
 */
export const MobileSidebar = ({ isOpen, onClose, isConnected }) => {
  if (!isOpen) return null;

  return (
    <div
      className="lg:hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="fixed inset-y-0 left-0 w-80 max-w-[85vw] bg-gray-900/95 backdrop-blur-xl border-r border-gray-800/50 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600">
              <ShieldCheckSolid className="h-5 w-5 text-white" />
            </div>
            <span className="text-base font-bold text-white">
              SecureDevOps AI
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Quick Action */}
        <div className="p-4 border-b border-gray-800/50">
          <Link
            to="/projects?action=new"
            onClick={onClose}
            className="w-full p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg flex items-center justify-center space-x-2"
          >
            <PlusIcon className="h-4 w-4" />
            <span className="text-sm">New Project</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="px-4 py-4">
          <NavSection
            title="Main"
            items={getNavigationByCategory("main")}
            onLinkClick={onClose}
          />
          <NavSection
            title="Enterprise"
            items={getNavigationByCategory("enterprise")}
            onLinkClick={onClose}
          />
          <NavSection
            items={getNavigationByCategory("settings")}
            onLinkClick={onClose}
          />
        </nav>

        {/* Connection Status */}
        <ConnectionStatus isConnected={isConnected} />
      </div>
    </div>
  );
};

export default { DesktopSidebar, MobileSidebar };
