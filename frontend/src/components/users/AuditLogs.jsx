/**
 * AuditLogs Component - Enterprise Audit Trail Viewer
 * Displays comprehensive audit logs with filtering, search, and export
 */
import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ClockIcon,
  UserIcon,
  ShieldCheckIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  CalendarIcon,
  ComputerDesktopIcon,
  GlobeAltIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI, utils } from "../../services/api";
import { Button, Card, EmptyState } from "../../styles/components";
import { PageContainer, PageHeader, GlassCard } from "../../layouts";

const AuditLogs = () => {
  const [filters, setFilters] = useState({
    event_types: [],
    users: [],
    start_date: "",
    end_date: "",
    search: "",
    severity: "",
  });
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedLog, setExpandedLog] = useState(null);

  // Event type categories
  const eventTypes = [
    { value: "user.login", label: "User Login", category: "User Management" },
    { value: "user.logout", label: "User Logout", category: "User Management" },
    {
      value: "user.created",
      label: "User Created",
      category: "User Management",
    },
    {
      value: "user.updated",
      label: "User Updated",
      category: "User Management",
    },
    {
      value: "user.deleted",
      label: "User Deleted",
      category: "User Management",
    },
    { value: "scan.started", label: "Scan Started", category: "Security" },
    { value: "scan.completed", label: "Scan Completed", category: "Security" },
    { value: "scan.failed", label: "Scan Failed", category: "Security" },
    {
      value: "vulnerability.detected",
      label: "Vulnerability Detected",
      category: "Security",
    },
    {
      value: "vulnerability.fixed",
      label: "Vulnerability Fixed",
      category: "Security",
    },
    {
      value: "compliance.assessment",
      label: "Compliance Assessment",
      category: "Compliance",
    },
    { value: "policy.created", label: "Policy Created", category: "Policy" },
    { value: "policy.updated", label: "Policy Updated", category: "Policy" },
    { value: "policy.deleted", label: "Policy Deleted", category: "Policy" },
    {
      value: "settings.changed",
      label: "Settings Changed",
      category: "Configuration",
    },
    {
      value: "api.key.created",
      label: "API Key Created",
      category: "Security",
    },
    {
      value: "api.key.revoked",
      label: "API Key Revoked",
      category: "Security",
    },
    { value: "auth.failed", label: "Auth Failed", category: "Security" },
    {
      value: "suspicious.activity",
      label: "Suspicious Activity",
      category: "Security",
    },
  ];

  const severityLevels = ["info", "warning", "error", "critical"];

  // Fetch audit logs with filters
  const {
    data: auditData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["auditLogs", filters, page, limit],
    queryFn: () =>
      enterpriseAPI.getAuditLogs({
        ...filters,
        skip: (page - 1) * limit,
        limit,
      }),
    keepPreviousData: true,
  });

  // Fetch users for filter dropdown
  const { data: usersData } = useQuery({
    queryKey: ["auditUsers"],
    queryFn: () => enterpriseAPI.getAuditUsers(),
  });

  // Export audit logs
  const handleExport = async (format = "json") => {
    try {
      toast.loading("Exporting audit logs...");
      const data = await enterpriseAPI.exportAuditLogs({
        ...filters,
        format,
      });

      // Create download link
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: format === "json" ? "application/json" : "text/csv",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString()}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.dismiss();
      toast.success(`Audit logs exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.dismiss();
      toast.error("Failed to export audit logs");
    }
  };

  // Get severity badge color
  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case "critical":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      case "error":
        return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      case "warning":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "info":
      default:
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    }
  };

  // Get severity icon
  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case "critical":
      case "error":
        return <XCircleIcon className="w-4 h-4" />;
      case "warning":
        return <ExclamationTriangleIcon className="w-4 h-4" />;
      case "info":
      default:
        return <InformationCircleIcon className="w-4 h-4" />;
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="Audit Logs"
          description="Comprehensive audit trail for compliance and security monitoring"
          icon={ClockIcon}
          breadcrumb={["Audit Logs"]}
          actions={
            <button
              onClick={() => handleExport("json")}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-xl text-white text-sm lg:text-base font-semibold shadow-lg transition-all"
            >
              <ArrowDownTrayIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>Export</span>
            </button>
          }
        />

        {/* Search and Filter Bar */}
        <GlassCard className="mb-6">
          <div className="flex flex-col lg:flex-row gap-3 lg:gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 lg:left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 lg:w-5 lg:h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={filters.search}
                onChange={(e) =>
                  setFilters({ ...filters, search: e.target.value })
                }
                className="w-full pl-10 lg:pl-12 pr-4 py-2.5 lg:py-3 bg-gray-900/50 border border-gray-600/50 rounded-xl text-sm lg:text-base text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center justify-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/30 rounded-xl text-purple-300 transition-all text-sm lg:text-base"
            >
              <FunnelIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>Filters</span>
              {showFilters ? (
                <ChevronUpIcon className="w-3.5 h-3.5 lg:w-4 lg:h-4" />
              ) : (
                <ChevronDownIcon className="w-3.5 h-3.5 lg:w-4 lg:h-4" />
              )}
            </button>

            {/* Export */}
            <div className="flex gap-2">
              <button
                onClick={() => handleExport("json")}
                className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-xl text-blue-300 transition-all text-sm lg:text-base"
              >
                <ArrowDownTrayIcon className="w-4 h-4 lg:w-5 lg:h-5" />
                <span className="hidden sm:inline">Export</span> JSON
              </button>
            </div>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-700/50 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Event Types */}
              <div>
                <label className="block text-xs lg:text-sm font-medium text-gray-300 mb-2">
                  Event Types
                </label>
                <select
                  multiple
                  value={filters.event_types}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      event_types: Array.from(
                        e.target.selectedOptions,
                        (option) => option.value
                      ),
                    })
                  }
                  className="w-full px-3 lg:px-4 py-2 bg-gray-800 border border-gray-600/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-gray-800 [&>option]:text-white"
                  size="5"
                >
                  {eventTypes.map((type) => (
                    <option
                      key={type.value}
                      value={type.value}
                      className="bg-gray-800 text-white"
                    >
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Users */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Users
                </label>
                <select
                  multiple
                  value={filters.users}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      users: Array.from(
                        e.target.selectedOptions,
                        (option) => option.value
                      ),
                    })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-gray-800 [&>option]:text-white"
                  size="5"
                >
                  {usersData?.users?.map((user) => (
                    <option
                      key={user}
                      value={user}
                      className="bg-gray-800 text-white"
                    >
                      {user}
                    </option>
                  ))}
                </select>
              </div>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Start Date
                </label>
                <input
                  type="datetime-local"
                  value={filters.start_date}
                  onChange={(e) =>
                    setFilters({ ...filters, start_date: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <label className="block text-sm font-medium text-gray-300 mb-2 mt-2">
                  End Date
                </label>
                <input
                  type="datetime-local"
                  value={filters.end_date}
                  onChange={(e) =>
                    setFilters({ ...filters, end_date: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Severity */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Severity
                </label>
                <select
                  value={filters.severity}
                  onChange={(e) =>
                    setFilters({ ...filters, severity: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-gray-800 [&>option]:text-white"
                >
                  <option value="" className="bg-gray-800 text-white">
                    All Severities
                  </option>
                  {severityLevels.map((level) => (
                    <option
                      key={level}
                      value={level}
                      className="bg-gray-800 text-white"
                    >
                      {level.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </GlassCard>

        {/* Audit Logs Table */}
        <Card padding="none" className="shadow-xl overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading audit logs...</p>
            </div>
          ) : auditData?.logs?.length === 0 ? (
            <EmptyState
              icon={<ShieldCheckIcon className="h-12 w-12" />}
              title="No audit logs found"
              description="Try adjusting your filters"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700/50">
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      Timestamp
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      Event Type
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      User
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      Description
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      Severity
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      IP Address
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {auditData?.logs?.map((log) => (
                    <React.Fragment key={log.id}>
                      <tr className="border-b border-gray-700/30 hover:bg-gray-800/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm text-gray-300">
                            <ClockIcon className="w-4 h-4 text-gray-500" />
                            {formatTimestamp(log.timestamp)}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-sm font-medium">
                            {log.event_type}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm text-gray-300">
                            <UserIcon className="w-4 h-4 text-gray-500" />
                            {log.user_id || "System"}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-300 max-w-xs truncate">
                          {log.description}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center gap-1 px-3 py-1 border rounded-lg text-xs font-medium ${getSeverityColor(
                              log.severity
                            )}`}
                          >
                            {getSeverityIcon(log.severity)}
                            {log.severity?.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm text-gray-400">
                            <GlobeAltIcon className="w-4 h-4" />
                            {log.ip_address || "N/A"}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <button
                            onClick={() =>
                              setExpandedLog(
                                expandedLog === log.id ? null : log.id
                              )
                            }
                            className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                          >
                            {expandedLog === log.id ? "Hide" : "Details"}
                          </button>
                        </td>
                      </tr>
                      {expandedLog === log.id && (
                        <tr className="bg-gray-800/30">
                          <td colSpan="7" className="px-6 py-4">
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm font-medium text-gray-400 mb-1">
                                    Event ID
                                  </p>
                                  <p className="text-sm text-white font-mono">
                                    {log.id}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-400 mb-1">
                                    User Agent
                                  </p>
                                  <p className="text-sm text-white truncate">
                                    {log.user_agent || "N/A"}
                                  </p>
                                </div>
                                {log.metadata && (
                                  <div className="col-span-2">
                                    <p className="text-sm font-medium text-gray-400 mb-1">
                                      Metadata
                                    </p>
                                    <pre className="text-xs text-gray-300 bg-black/30 p-3 rounded-lg overflow-x-auto">
                                      {JSON.stringify(log.metadata, null, 2)}
                                    </pre>
                                  </div>
                                )}
                                {log.integrity_hash && (
                                  <div className="col-span-2">
                                    <p className="text-sm font-medium text-gray-400 mb-1">
                                      Integrity Hash (SHA-256)
                                    </p>
                                    <p className="text-xs text-gray-300 font-mono break-all">
                                      {log.integrity_hash}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {auditData?.total > limit && (
            <div className="px-6 py-4 border-t border-gray-700/50 flex items-center justify-between">
              <p className="text-sm text-gray-400">
                Showing {(page - 1) * limit + 1} to{" "}
                {Math.min(page * limit, auditData.total)} of {auditData.total}{" "}
                logs
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-4 py-2 bg-gray-800/30 hover:bg-gray-700/50 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700/50 rounded-lg text-white transition-all"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page * limit >= auditData.total}
                  className="px-4 py-2 bg-gray-800/30 hover:bg-gray-700/50 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700/50 rounded-lg text-white transition-all"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </PageContainer>
  );
};

export default AuditLogs;
