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
import { Link, useLocation } from "react-router-dom";
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

// Page configuration with metadata
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
    <nav
      className="flex items-center space-x-2 text-sm mb-4"
      aria-label="Breadcrumb"
    >
      <Link to="/" className="text-gray-400 hover:text-white transition-colors">
        <HomeIcon className="h-4 w-4" />
      </Link>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRightIcon className="h-4 w-4 text-gray-600" />
          <span
            className={
              index === items.length - 1
                ? "text-white font-medium"
                : "text-gray-400"
            }
          >
            {item}
          </span>
        </React.Fragment>
      ))}
    </nav>
  );
};

// Page Header Component
export const PageHeader = ({
  title,
  description,
  icon: Icon,
  actions,
  breadcrumb = [],
}) => {
  return (
    <div className="mb-6 lg:mb-8">
      <Breadcrumb items={breadcrumb} />
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          {Icon && (
            <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
              <Icon className="h-6 w-6 text-white" />
            </div>
          )}
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">
              {title}
            </h1>
            {description && (
              <p className="text-gray-400 mt-1 text-sm sm:text-base">
                {description}
              </p>
            )}
          </div>
        </div>
        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>
    </div>
  );
};

// Page Container Component - Wraps page content with consistent styling
export const PageContainer = ({ children, className = "" }) => {
  return (
    <div
      className={`min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8 ${className}`}
    >
      {children}
    </div>
  );
};

// Glass Card Component - Consistent card styling
export const GlassCard = ({ children, className = "", noPadding = false }) => {
  return (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-r from-gray-800/30 to-gray-700/30 rounded-2xl lg:rounded-3xl blur-xl" />
      <div
        className={`relative ${
          noPadding ? "" : "p-4 sm:p-6 lg:p-8"
        } rounded-2xl lg:rounded-3xl border border-gray-800/50 bg-gray-900/50 backdrop-blur-xl ${className}`}
      >
        {children}
      </div>
    </div>
  );
};

// Section Header Component
export const SectionHeader = ({ title, description, action }) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h2 className="text-lg lg:text-xl font-bold text-white">{title}</h2>
        {description && (
          <p className="text-sm text-gray-400 mt-1">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
};

// Empty State Component
export const EmptyState = ({ icon: Icon, title, description, action }) => {
  return (
    <div className="text-center py-12 lg:py-16">
      {Icon && (
        <div className="inline-flex p-4 rounded-2xl bg-gray-800/50 mb-4">
          <Icon className="h-12 w-12 text-gray-400" />
        </div>
      )}
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-gray-400 max-w-sm mx-auto mb-6">{description}</p>
      {action}
    </div>
  );
};

// Loading State Component
export const LoadingState = ({ message = "Loading..." }) => {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
        <p className="text-gray-400">{message}</p>
      </div>
    </div>
  );
};

// Error State Component
export const ErrorState = ({ title = "Error", message, onRetry }) => {
  return (
    <div className="text-center py-12">
      <div className="inline-flex p-4 rounded-2xl bg-red-500/10 mb-4">
        <ShieldCheckIcon className="h-12 w-12 text-red-400" />
      </div>
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-gray-400 max-w-sm mx-auto mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default {
  PageContainer,
  PageHeader,
  Breadcrumb,
  GlassCard,
  SectionHeader,
  EmptyState,
  LoadingState,
  ErrorState,
  pageConfig,
};
