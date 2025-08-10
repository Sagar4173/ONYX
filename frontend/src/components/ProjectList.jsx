/**
 * ProjectList Component - Lists projects with security scores and reports
 */
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
import { reportsAPI, utils } from "../services/api";
import toast from "react-hot-toast";

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
    const score = utils.calculateSecurityScore(findingsBySeverity);
    const colorClass = utils.getScoreColor(score);

    return (
      <div
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass} bg-opacity-10 border`}
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
    const colorClass = utils.getStatusColor(status);
    const statusIcons = {
      completed: CheckCircleIcon,
      running: RefreshIcon,
      pending: ClockIcon,
      failed: XCircleIcon,
    };

    const Icon = statusIcons[status] || ClockIcon;

    return (
      <div
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass} border`}
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
        <div className="flex items-center text-green-600">
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

          const colorClass = utils.getSeverityColor(severity);
          return (
            <span
              key={severity}
              className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${colorClass} border`}
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
      <div className="flex items-center justify-between px-6 py-3 bg-white border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-700">
          Showing {(currentPage - 1) * itemsPerPage + 1} to{" "}
          {Math.min(currentPage * itemsPerPage, totalReports)} of {totalReports}{" "}
          results
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {pages.map((page) => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              className={`px-3 py-1 text-sm font-medium rounded-md ${
                page === currentPage
                  ? "text-blue-600 bg-blue-50 border border-blue-300"
                  : "text-gray-500 bg-white border border-gray-300 hover:bg-gray-50"
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
            className="px-3 py-1 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  if (isError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error loading reports
              </h3>
              <p className="mt-2 text-sm text-red-700">
                {error?.message || "Failed to fetch reports"}
              </p>
              <button
                onClick={() => refetch()}
                className="mt-3 text-sm text-red-800 underline hover:text-red-900"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Security Reports</h1>
        <p className="mt-2 text-gray-600">
          Monitor and analyze security scan results across all projects
        </p>
      </div>

      {/* Quick Stats */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <DocumentIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.scan_summary?.total_scans || 0}
                </p>
                <p className="text-sm text-gray-600">Total Scans</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.vulnerability_summary?.critical || 0}
                </p>
                <p className="text-sm text-gray-600">Critical Issues</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.scan_summary?.success_rate?.toFixed(1) || 0}%
                </p>
                <p className="text-sm text-gray-600">Success Rate</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.top_projects?.length || 0}
                </p>
                <p className="text-sm text-gray-600">Active Projects</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            {/* Search */}
            <div className="relative max-w-md">
              <SearchIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search projects..."
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>

            <div className="flex items-center space-x-4">
              {/* Filters */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              >
                {severityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
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
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              >
                {sortOptions.map((option) => (
                  <React.Fragment key={option.value}>
                    <option value={`${option.value}:desc`}>
                      {option.label} (Newest)
                    </option>
                    <option value={`${option.value}:asc`}>
                      {option.label} (Oldest)
                    </option>
                  </React.Fragment>
                ))}
              </select>

              <button
                onClick={() => refetch()}
                className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                title="Refresh"
              >
                <RefreshIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Reports List */}
        <div className="divide-y divide-gray-200">
          {isLoading ? (
            <div className="p-8 text-center">
              <RefreshIcon className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-500">Loading reports...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="p-8 text-center">
              <DocumentIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No reports found</p>
              <p className="text-sm text-gray-400">
                Try adjusting your search criteria
              </p>
            </div>
          ) : (
            reports.map((report) => (
              <div
                key={report.id}
                className="p-6 hover:bg-gray-50 transition-colors duration-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {report.project_name}
                      </h3>
                      <StatusBadge status={report.status} />
                      <SecurityScoreBadge
                        findingsBySeverity={report.findings_by_severity}
                      />
                    </div>

                    <div className="mt-2 flex items-center text-sm text-gray-500 space-x-4">
                      <span>Branch: {report.branch || "main"}</span>
                      <span>
                        Commit: {report.commit_hash?.substring(0, 8) || "N/A"}
                      </span>
                      <span>{utils.formatDate(report.created_at)}</span>
                      {report.duration_seconds && (
                        <span>
                          Duration:{" "}
                          {utils.formatDuration(report.duration_seconds)}
                        </span>
                      )}
                    </div>

                    <div className="mt-3">
                      <FindingsSummary
                        findingsBySeverity={report.findings_by_severity}
                      />
                    </div>

                    {report.has_ai_analysis && (
                      <div className="mt-2 flex items-center text-sm text-blue-600">
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        AI Analysis Available
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <Link
                      to={`/report/${report.id}`}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <EyeIcon className="h-4 w-4 mr-1.5" />
                      View Details
                    </Link>

                    <Link
                      to={`/compliance/${report.id}`}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <DownloadIcon className="h-4 w-4 mr-1.5" />
                      Export PDF
                    </Link>

                    <button className="p-2 text-gray-400 hover:text-gray-500">
                      <ChevronRightIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        <Pagination />
      </div>
    </div>
  );
};

export default ProjectList;
