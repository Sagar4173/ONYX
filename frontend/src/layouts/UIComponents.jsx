/**
 * UIComponents - Shared UI Components Library
 * Reusable components used across all pages:
 * - PageContainer: Full-page wrapper with gradient background
 * - PageHeader: Page title, description, breadcrumb, and actions
 * - GlassCard: Glass morphism card container
 * - SectionHeader: Section title with optional action button
 * - EmptyState, LoadingState, ErrorState: State indicators
 */
import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  HomeIcon,
  FolderIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  CogIcon,
  UsersIcon,
  ClockIcon,
  ArchiveBoxIcon,
  BuildingOfficeIcon,
  ChevronRightIcon,
} from "@heroicons/react/24/outline";

// eslint-disable-next-line react-refresh/only-export-components
export const pageConfig = {
  "/": {
    title: "Dashboard",
    description: "Security overview and system status",
    icon: HomeIcon,
    breadcrumb: ["Dashboard"],
  },
  "/projects": {
    title: "Projects",
    description: "Manage your security scanning projects",
    icon: FolderIcon,
    breadcrumb: ["Projects"],
  },
  "/reports": {
    title: "Scan Reports",
    description: "View detailed security scan results",
    icon: DocumentTextIcon,
    breadcrumb: ["Reports"],
  },
  "/analytics": {
    title: "Analytics",
    description: "Security trends and insights",
    icon: ChartBarIcon,
    breadcrumb: ["Analytics"],
  },
  "/users": {
    title: "User Management",
    description: "Manage team members and permissions",
    icon: UsersIcon,
    breadcrumb: ["Users"],
  },
  "/audit-logs": {
    title: "Audit Logs",
    description: "Track all system activities and changes",
    icon: ClockIcon,
    breadcrumb: ["Audit Logs"],
  },
  "/retention-policies": {
    title: "Data Retention",
    description: "Configure data lifecycle and retention policies",
    icon: ArchiveBoxIcon,
    breadcrumb: ["Data Retention"],
  },
  "/compliance": {
    title: "Compliance Center",
    description: "Compliance frameworks and assessments",
    icon: BuildingOfficeIcon,
    breadcrumb: ["Compliance"],
  },
  "/settings": {
    title: "Settings",
    description: "Platform configuration and preferences",
    icon: CogIcon,
    breadcrumb: ["Settings"],
  },
};

// Breadcrumb Component
export const Breadcrumb = ({ items = [] }) => {
  if (items.length === 0) return null;

  return (
    <nav className="flex items-center space-x-2 text-sm mb-4" aria-label="Breadcrumb">
      <Link
        to="/"
        className="text-gray-400 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
        aria-label="Home"
      >
        <HomeIcon className="h-4 w-4" />
      </Link>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRightIcon className="h-4 w-4 text-gray-600" />
          <span
            className={index === items.length - 1 ? "text-white font-medium" : "text-gray-400"}
            aria-current={index === items.length - 1 ? "page" : undefined}
          >
            {item}
          </span>
        </React.Fragment>
      ))}
    </nav>
  );
};

// Page Header Component
export const PageHeader = ({ title, description, icon: Icon, actions, breadcrumb = [] }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="mb-6 lg:mb-8"
    >
      <Breadcrumb items={breadcrumb} />
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.08 } },
          }}
          className="flex items-center space-x-4"
        >
          {Icon && (
            <motion.div
              variants={{
                hidden: { opacity: 0, scale: 0.8 },
                visible: { opacity: 1, scale: 1 },
              }}
              className="p-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600 shadow-lg"
            >
              <Icon className="h-6 w-6 text-white" />
            </motion.div>
          )}
          <motion.div
            variants={{
              hidden: { opacity: 0, x: -10 },
              visible: { opacity: 1, x: 0 },
            }}
          >
            <h1 className="text-2xl sm:text-3xl font-bold text-white">{title}</h1>
            {description && (
              <p className="text-gray-400 mt-1 text-sm sm:text-base">{description}</p>
            )}
          </motion.div>
        </motion.div>
        {actions && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.15 }}
            className="flex items-center gap-3"
          >
            {actions}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

// Page Container Component - Wraps page content with consistent styling and entrance animation
export const PageContainer = ({ children, className = "" }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8 ${className}`}
    >
      {children}
    </motion.div>
  );
};

// Glass Card Component - Consistent card styling
export const GlassCard = ({ children, className = "", noPadding = false }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="relative"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-gray-800/30 to-gray-700/30 rounded-2xl lg:rounded-3xl blur-xl" />
      <div
        className={`relative ${
          noPadding ? "" : "p-4 sm:p-6 lg:p-8"
        } rounded-2xl lg:rounded-3xl border border-gray-800/50 bg-gray-900/50 backdrop-blur-xl ${className}`}
      >
        {children}
      </div>
    </motion.div>
  );
};

// Section Header Component
export const SectionHeader = ({ title, description, action }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6"
    >
      <div>
        <h2 className="text-lg lg:text-xl font-bold text-white">{title}</h2>
        {description && <p className="text-sm text-gray-400 mt-1">{description}</p>}
      </div>
      {action}
    </motion.div>
  );
};

// Empty State Component — Enhanced with gradient icon and entrance animation
export const EmptyState = ({ icon: Icon, title, description, action }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="text-center py-12 lg:py-16"
    >
      {Icon && (
        <div className="inline-flex p-5 rounded-2xl bg-gradient-to-br from-gray-800/80 to-gray-700/40 border border-gray-700/30 mb-5 shadow-lg shadow-black/20">
          <Icon className="h-12 w-12 text-gray-300" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 max-w-sm mx-auto mb-6 leading-relaxed">{description}</p>
      {action}
    </motion.div>
  );
};

// Skeleton Card Component — Shimmer loading placeholder
export const SkeletonCard = ({ className = "", lines = 3 }) => {
  return (
    <div className={`skeleton-card p-5 lg:p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="skeleton w-10 h-10 rounded-xl" />
        <div className="skeleton w-16 h-6 rounded-lg" />
      </div>
      <div className="skeleton w-24 h-8 rounded-lg mb-2" />
      <div className="skeleton w-32 h-4 rounded mb-1" />
      {lines > 2 && <div className="skeleton w-20 h-3 rounded mt-2" />}
    </div>
  );
};

// Loading State Component — Branded skeleton shimmer
export const LoadingState = ({ message = "Loading...", cards = 4 }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {Array.from({ length: cards }).map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: i * 0.08 }}
          >
            <SkeletonCard />
          </motion.div>
        ))}
      </div>
      <div className="flex items-center justify-center py-6 gap-3">
        <div className="relative">
          <div className="w-8 h-8 rounded-full border-2 border-gray-700 border-t-cyan-500 animate-spin" />
          <div
            className="absolute inset-0 w-8 h-8 rounded-full border-2 border-transparent border-b-purple-500 animate-spin"
            style={{ animationDirection: "reverse", animationDuration: "1.5s" }}
          />
        </div>
        <p className="text-gray-400 text-sm">{message}</p>
      </div>
    </motion.div>
  );
};

// Live Indicator Component — Real-time status display
export const LiveIndicator = ({ status = "connected", label }) => {
  const config = {
    connected: {
      color: "bg-emerald-500",
      shadow: "shadow-emerald-500/50",
      text: "text-emerald-400",
      label: label || "Live",
    },
    scanning: {
      color: "bg-amber-500",
      shadow: "shadow-amber-500/50",
      text: "text-amber-400",
      label: label || "Scanning",
    },
    disconnected: {
      color: "bg-red-500",
      shadow: "shadow-red-500/50",
      text: "text-red-400",
      label: label || "Offline",
    },
    idle: {
      color: "bg-gray-500",
      shadow: "shadow-gray-500/50",
      text: "text-gray-400",
      label: label || "Idle",
    },
  };
  const c = config[status] || config.idle;

  return (
    <div className="flex items-center gap-2">
      <span className={`relative flex h-2.5 w-2.5`}>
        {status === "connected" && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full ${c.color} opacity-75`}
          />
        )}
        <span
          className={`relative inline-flex rounded-full h-2.5 w-2.5 ${c.color} shadow-lg ${c.shadow}`}
        />
      </span>
      <span className={`text-xs font-medium ${c.text} uppercase tracking-wider`}>{c.label}</span>
    </div>
  );
};

// Error State Component — Enhanced with gradient background
export const ErrorState = ({ title = "Error", message, onRetry }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="text-center py-12"
    >
      <div className="inline-flex p-5 rounded-2xl bg-gradient-to-br from-red-500/20 to-red-900/10 border border-red-500/20 mb-5">
        <ShieldCheckIcon className="h-12 w-12 text-red-400" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 max-w-sm mx-auto mb-6 leading-relaxed">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
        >
          Try Again
        </button>
      )}
    </motion.div>
  );
};

export default {
  PageContainer,
  PageHeader,
  Breadcrumb,
  GlassCard,
  SectionHeader,
  EmptyState,
  SkeletonCard,
  LoadingState,
  LiveIndicator,
  ErrorState,
  pageConfig,
};
