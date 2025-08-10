import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  MagnifyingGlassIcon as SearchIcon,
  FunnelIcon as FilterIcon,
  DocumentIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  ArrowDownTrayIcon as DownloadIcon,
  ArrowPathIcon as RefreshIcon,
} from "@heroicons/react/24/outline";
import { ChevronRightIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { reportsAPI, utils } from "../services/api";

// Additional utility functions specific to ProjectList
const projectUtils = {
  calculateSecurityScore: (findings) => {
    if (!findings) return 100;
    const { critical = 0, high = 0, medium = 0, low = 0 } = findings;
    const total = critical + high + medium + low;
    if (total === 0) return 100;

    const weightedScore = critical * 25 + high * 10 + medium * 5 + low * 1;
    return Math.max(0, Math.min(100, 100 - Math.min(weightedScore, 100)));
  },

  getScoreColor: (score) => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    if (score >= 40) return "text-orange-400";
    return "text-red-400";
  },

  getStatusColor: (status) => {
    const colors = {
      completed: "text-green-400 bg-green-400/10 border-green-400/30",
      running: "text-blue-400 bg-blue-400/10 border-blue-400/30",
      pending: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
      failed: "text-red-400 bg-red-400/10 border-red-400/30",
    };
    return colors[status] || colors.pending;
  },

  getSeverityColor: (severity) => {
    const colors = {
      critical: "text-red-400 bg-red-400/10 border-red-400/30",
      high: "text-orange-400 bg-orange-400/10 border-orange-400/30",
      medium: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
      low: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    };
    return colors[severity] || colors.low;
  },

  formatRelativeDate: (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  },
};

const ProjectList = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Fetch reports with current filters
  const {
    data: reportsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: [
      "reports",
      {
        page: currentPage,
        limit: itemsPerPage,
        search: searchTerm,
        status: statusFilter !== "all" ? statusFilter : undefined,
        severity: severityFilter !== "all" ? severityFilter : undefined,
        sort: `${sortOrder === "desc" ? "-" : ""}${sortBy}`,
      },
    ],
    queryFn: () =>
      reportsAPI.getReports({
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        project_name: searchTerm || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        severity_filter: severityFilter !== "all" ? severityFilter : undefined,
      }),
    keepPreviousData: true,
  });

  // Fetch analytics for dashboard stats
  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => reportsAPI.getAnalyticsOverview(30),
  });

  const reports = reportsData?.reports || [];
  const totalReports = reportsData?.pagination?.total || 0;
  const totalPages = Math.ceil(totalReports / itemsPerPage);

  // Handle search with debouncing
  const handleSearch = utils.debounce((value) => {
    setSearchTerm(value);
    setCurrentPage(1);
  }, 300);

  // Handle report download
  const handleDownloadReport = async (reportId, format = "pdf") => {
    try {
      toast.loading("Preparing download...", { id: "download" });
      const API_BASE_URL =
        import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${API_BASE_URL}/api/reports/${reportId}/download?format=${format}`,
        {
          method: "GET",
          headers: {
            Accept:
              format === "pdf"
                ? "application/pdf"
                : format === "csv"
                ? "text/csv"
                : "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Download failed: ${errorText}`);
      }

      const blob = await response.blob();

      // Verify blob type for PDF
      if (format === "pdf" && !blob.type.includes("pdf")) {
        console.warn("Downloaded blob type:", blob.type);
        // Force PDF MIME type
        const pdfBlob = new Blob([blob], { type: "application/pdf" });
        utils.downloadFile(pdfBlob, `security-report-${reportId}.pdf`);
      } else {
        const extension =
          format === "csv" ? "csv" : format === "json" ? "json" : "pdf";
        utils.downloadFile(blob, `security-report-${reportId}.${extension}`);
      }

      toast.success("Download started successfully!", { id: "download" });
    } catch (error) {
      toast.error("Failed to download report. Please try again.", {
        id: "download",
      });
      console.error("Download error:", error);
    }
  };

  // Filter options
  const statusOptions = [
    { value: "all", label: "All Status" },
    { value: "completed", label: "Completed" },
    { value: "running", label: "Running" },
    { value: "pending", label: "Pending" },
    { value: "failed", label: "Failed" },
  ];

  const severityOptions = [
    { value: "all", label: "All Severity" },
    { value: "critical", label: "Critical+" },
    { value: "high", label: "High+" },
    { value: "medium", label: "Medium+" },
    { value: "low", label: "Low+" },
  ];

  const sortOptions = [
    { value: "created_at", label: "Date Created" },
    { value: "project_name", label: "Project Name" },
    { value: "total_findings", label: "Total Findings" },
    { value: "status", label: "Status" },
  ];

  const SecurityScoreBadge = ({ findingsBySeverity }) => {
    const score = projectUtils.calculateSecurityScore(findingsBySeverity);
    const colorClass = projectUtils.getScoreColor(score);

    return (
      <div
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass} bg-opacity-10 border border-current`}
      >
        <span
          className={`h-2 w-2 rounded-full ${colorClass.replace(
            "text-",
            "bg-"
          )} mr-1`}
        />
        {score}/100
      </div>
    );
  };

  const StatusBadge = ({ status }) => {
    const colorClass = projectUtils.getStatusColor(status);
    const statusIcons = {
      completed: CheckCircleIcon,
      running: RefreshIcon,
      pending: ClockIcon,
      failed: XCircleIcon,
    };

    const Icon = statusIcons[status] || ClockIcon;

    return (
      <div
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
      >
        <Icon className="h-3 w-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </div>
    );
  };

  const FindingsSummary = ({ findingsBySeverity }) => {
    const severities = ["critical", "high", "medium", "low"];
    const hasFindings = Object.values(findingsBySeverity || {}).some(
      (count) => count > 0
    );

    if (!hasFindings) {
      return (
        <div className="flex items-center text-green-400">
          <CheckCircleIcon className="h-4 w-4 mr-1" />
          <span className="text-sm">No issues</span>
        </div>
      );
    }

    return (
      <div className="flex items-center space-x-2">
        {severities.map((severity) => {
          const count = findingsBySeverity?.[severity] || 0;
          if (count === 0) return null;

          const colorClass = projectUtils.getSeverityColor(severity);
          return (
            <span
              key={severity}
              className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${colorClass}`}
              title={`${count} ${severity} issue${count !== 1 ? "s" : ""}`}
            >
              {count}
            </span>
          );
        })}
      </div>
    );
  };

  const Pagination = () => {
    if (totalPages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return (
      <div className="flex items-center justify-between px-6 py-3 bg-gray-900 border-t border-gray-700 rounded-b-2xl">
        <div className="flex items-center text-sm text-gray-400">
          Showing {(currentPage - 1) * itemsPerPage + 1} to{" "}
          {Math.min(currentPage * itemsPerPage, totalReports)} of {totalReports}{" "}
          results
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 text-sm font-medium text-gray-400 bg-gray-800 border border-gray-600 rounded-md hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Previous
          </button>

          {pages.map((page) => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                page === currentPage
                  ? "text-blue-400 bg-blue-500/20 border border-blue-500/30"
                  : "text-gray-400 bg-gray-800 border border-gray-600 hover:bg-gray-700 hover:text-white"
              }`}
            >
              {page}
            </button>
          ))}

          <button
            onClick={() =>
              setCurrentPage(Math.min(totalPages, currentPage + 1))
            }
            disabled={currentPage === totalPages}
            className="px-3 py-1 text-sm font-medium text-gray-400 bg-gray-800 border border-gray-600 rounded-md hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-500/30 rounded-2xl p-6">
            <div className="flex">
              <XCircleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-400">
                  Error loading reports
                </h3>
                <p className="mt-2 text-sm text-red-300">
                  {error?.message || "Failed to fetch reports"}
                </p>
                <button
                  onClick={() => refetch()}
                  className="mt-3 text-sm text-red-400 underline hover:text-red-300 transition-colors"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Security Dashboard
          </h1>
          <p className="mt-2 text-gray-400">
            Monitor and analyze security scan results across all projects
          </p>
        </div>

        {/* Quick Stats */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-gray-800/70 transition-all duration-300">
              <div className="flex items-center">
                <div className="p-3 rounded-xl bg-blue-500/20 border border-blue-500/30">
                  <DocumentIcon className="h-8 w-8 text-blue-400" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-white">
                    {analytics.scan_summary?.total_scans || 0}
                  </p>
                  <p className="text-sm text-gray-400">Total Scans</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-gray-800/70 transition-all duration-300">
              <div className="flex items-center">
                <div className="p-3 rounded-xl bg-red-500/20 border border-red-500/30">
                  <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-white">
                    {analytics.vulnerability_summary?.critical || 0}
                  </p>
                  <p className="text-sm text-gray-400">Critical Issues</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-gray-800/70 transition-all duration-300">
              <div className="flex items-center">
                <div className="p-3 rounded-xl bg-green-500/20 border border-green-500/30">
                  <CheckCircleIcon className="h-8 w-8 text-green-400" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-white">
                    {analytics.scan_summary?.success_rate?.toFixed(1) || 0}%
                  </p>
                  <p className="text-sm text-gray-400">Success Rate</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-gray-800/70 transition-all duration-300">
              <div className="flex items-center">
                <div className="p-3 rounded-xl bg-purple-500/20 border border-purple-500/30">
                  <ClockIcon className="h-8 w-8 text-purple-400" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-white">
                    {analytics.top_projects?.length || 0}
                  </p>
                  <p className="text-sm text-gray-400">Active Projects</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters and Search */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            {/* Search */}
            <div className="relative max-w-md">
              <SearchIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search projects..."
                className="pl-10 pr-4 py-3 w-full bg-gray-900/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>

            <div className="flex flex-wrap items-center gap-4">
              {/* Filters */}
              <div className="flex items-center space-x-2">
                <FilterIcon className="h-5 w-5 text-gray-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 bg-gray-900/50 border border-gray-600/50 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                >
                  {statusOptions.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                      className="bg-gray-800 text-white"
                    >
                      {option.label}
                    </option>
                  ))}
                </select>

                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="px-4 py-2 bg-gray-900/50 border border-gray-600/50 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                >
                  {severityOptions.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                      className="bg-gray-800 text-white"
                    >
                      {option.label}
                    </option>
                  ))}
                </select>

                <select
                  value={`${sortBy}:${sortOrder}`}
                  onChange={(e) => {
                    const [field, order] = e.target.value.split(":");
                    setSortBy(field);
                    setSortOrder(order);
                  }}
                  className="px-4 py-2 bg-gray-900/50 border border-gray-600/50 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                >
                  {sortOptions.map((option) => (
                    <React.Fragment key={option.value}>
                      <option
                        value={`${option.value}:desc`}
                        className="bg-gray-800 text-white"
                      >
                        {option.label} (Newest)
                      </option>
                      <option
                        value={`${option.value}:asc`}
                        className="bg-gray-800 text-white"
                      >
                        {option.label} (Oldest)
                      </option>
                    </React.Fragment>
                  ))}
                </select>
              </div>

              <button
                onClick={() => refetch()}
                className="p-2 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-400 hover:bg-blue-500/30 hover:border-blue-500/50 transition-all duration-300"
                title="Refresh"
              >
                <RefreshIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Reports List */}
        <div className="space-y-4">
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, index) => (
                <div
                  key={index}
                  className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 animate-pulse"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="h-6 bg-gray-700 rounded-lg w-1/2 mb-3"></div>
                      <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-700 rounded w-1/2"></div>
                    </div>
                    <div className="ml-4">
                      <div className="h-8 bg-gray-700 rounded-lg w-20"></div>
                    </div>
                  </div>
                  <div className="mt-4 flex space-x-2">
                    <div className="h-6 bg-gray-700 rounded w-16"></div>
                    <div className="h-6 bg-gray-700 rounded w-16"></div>
                    <div className="h-6 bg-gray-700 rounded w-16"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : reports.length === 0 ? (
            <div className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-12 text-center">
              <div className="max-w-sm mx-auto">
                <div className="mx-auto h-20 w-20 text-gray-600 mb-6">
                  <DocumentIcon className="h-full w-full" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  No security scans found
                </h3>
                <p className="text-gray-400 mb-6">
                  {searchTerm ||
                  statusFilter !== "all" ||
                  severityFilter !== "all"
                    ? "No scans match your current filters. Try adjusting your search criteria."
                    : "Get started by running your first security scan on a repository."}
                </p>
              </div>
            </div>
          ) : (
            reports.map((report, index) => (
              <div
                key={report.id}
                className="group bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-gray-800/70 hover:border-gray-600/50 transition-all duration-300 hover:scale-[1.01]"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-3">
                      <h3 className="text-lg font-semibold text-white truncate group-hover:text-blue-300 transition-colors">
                        {report.project_name}
                      </h3>
                      <StatusBadge status={report.status} />
                      <SecurityScoreBadge
                        findingsBySeverity={report.findings_by_severity}
                      />
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-400 mb-3">
                      <div className="flex items-center">
                        <ClockIcon className="h-4 w-4 mr-1" />
                        {projectUtils.formatRelativeDate(report.created_at)}
                      </div>
                      <span>Branch: {report.branch || "main"}</span>
                      <span>
                        Commit: {report.commit_hash?.substring(0, 8) || "N/A"}
                      </span>
                      {report.duration_seconds && (
                        <span>
                          Duration:{" "}
                          {utils.formatDuration(report.duration_seconds)}
                        </span>
                      )}
                    </div>

                    <div className="mb-4">
                      <FindingsSummary
                        findingsBySeverity={report.findings_by_severity}
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 ml-6">
                    <Link
                      to={`/report/${report.id}`}
                      className="inline-flex items-center px-4 py-2 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-400 hover:bg-blue-500/30 hover:border-blue-500/50 transition-all duration-300 group/btn"
                    >
                      <EyeIcon className="h-4 w-4 mr-2 group-hover/btn:scale-110 transition-transform" />
                      View Report
                      <ChevronRightIcon className="h-4 w-4 ml-1 group-hover/btn:translate-x-1 transition-transform" />
                    </Link>

                    {report.status === "completed" && (
                      <button
                        onClick={() => handleDownloadReport(report.id)}
                        className="inline-flex items-center px-4 py-2 rounded-xl bg-gray-700/50 border border-gray-600/50 text-gray-300 hover:bg-gray-600/50 hover:border-gray-500/50 hover:text-white transition-all duration-300 group/btn"
                      >
                        <DownloadIcon className="h-4 w-4 mr-2 group-hover/btn:scale-110 transition-transform" />
                        Download
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {reports.length > 0 && <Pagination />}
      </div>
    </div>
  );
};

export default ProjectList;
