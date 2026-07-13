/**
 * Reports Page - View all security scan reports
 * Shows a comprehensive list of all completed scans with filtering and sorting
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChevronRightIcon,
} from "@heroicons/react/24/outline";
import {
  PageContainer,
  PageHeader,
  GlassCard,
  SectionHeader,
  LoadingState,
  EmptyState,
} from "../layouts";
import { reportsAPI } from "../services/api";

// Status Badge Component
const StatusBadge = ({ status }) => {
  const styles = {
    completed: "bg-green-500/20 text-green-400 border-green-500/30",
    running: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
  };

  const icons = {
    completed: CheckCircleIcon,
    running: ArrowPathIcon,
    pending: ClockIcon,
    failed: XCircleIcon,
  };

  const Icon = icons[status] || ClockIcon;
  const style = styles[status] || styles.pending;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${style}`}
    >
      <Icon
        className={`h-3.5 w-3.5 ${status === "running" ? "animate-spin" : ""}`}
      />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

// Severity Badge Component
const SeverityBadge = ({ severity, count }) => {
  const styles = {
    critical: "bg-red-500/20 text-red-400",
    high: "bg-orange-500/20 text-orange-400",
    medium: "bg-yellow-500/20 text-yellow-400",
    low: "bg-blue-500/20 text-blue-400",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        styles[severity] || styles.low
      }`}
    >
      {count}
    </span>
  );
};

// Report Card Component
const ReportCard = ({ report }) => {
  const vulnerabilities =
    report.vulnerability_count || report.findings_summary || {};
  const totalVulns = Object.values(vulnerabilities).reduce(
    (sum, val) => sum + (val || 0),
    0
  );

  return (
    <Link
      to={`/report/${report.id}`}
      className="block p-4 sm:p-5 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50 hover:border-gray-600/50 transition-all group"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Left: Project Info */}
        <div className="flex items-start sm:items-center gap-4 min-w-0">
          <div className="p-2.5 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 flex-shrink-0">
            <DocumentTextIcon className="h-5 w-5 text-purple-400" />
          </div>
          <div className="min-w-0">
            <h3 className="text-white font-medium truncate group-hover:text-blue-400 transition-colors">
              {report.project_name ||
                report.repository_url?.split("/").pop() ||
                "Unknown Project"}
            </h3>
            <p className="text-sm text-gray-400 truncate mt-0.5">
              {report.repository_url || "No repository URL"}
            </p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span>{report.scan_type || "security"} scan</span>
              <span>•</span>
              <span>{new Date(report.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Right: Stats & Status */}
        <div className="flex items-center gap-4 sm:gap-6">
          {/* Vulnerability Summary */}
          <div className="flex items-center gap-2">
            {vulnerabilities.critical > 0 && (
              <SeverityBadge
                severity="critical"
                count={vulnerabilities.critical}
              />
            )}
            {vulnerabilities.high > 0 && (
              <SeverityBadge severity="high" count={vulnerabilities.high} />
            )}
            {vulnerabilities.medium > 0 && (
              <SeverityBadge severity="medium" count={vulnerabilities.medium} />
            )}
            {totalVulns === 0 && (
              <span className="text-sm text-green-400 flex items-center gap-1">
                <ShieldCheckIcon className="h-4 w-4" />
                Clean
              </span>
            )}
          </div>

          {/* Status */}
          <StatusBadge status={report.status || "completed"} />

          {/* Arrow */}
          <ChevronRightIcon className="h-5 w-5 text-gray-600 group-hover:text-gray-400 transition-colors" />
        </div>
      </div>
    </Link>
  );
};

// Main Reports Component
const Reports = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("newest");

  // Fetch reports
  const {
    data: reportsData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["reports", { limit: 50 }],
    queryFn: () => reportsAPI.getReports({ limit: 50 }),
  });

  const reports = reportsData?.reports || [];

  // Filter and sort reports
  const filteredReports = reports
    .filter((report) => {
      const matchesSearch =
        searchQuery === "" ||
        report.project_name
          ?.toLowerCase()
          .includes(searchQuery.toLowerCase()) ||
        report.repository_url
          ?.toLowerCase()
          .includes(searchQuery.toLowerCase());

      const matchesStatus =
        statusFilter === "all" || report.status === statusFilter;

      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === "newest") {
        return new Date(b.created_at) - new Date(a.created_at);
      } else if (sortBy === "oldest") {
        return new Date(a.created_at) - new Date(b.created_at);
      }
      return 0;
    });

  return (
    <PageContainer>
      <PageHeader
        title="Scan Reports"
        description="View and analyze security scan results across all projects"
        icon={DocumentTextIcon}
        breadcrumb={["Reports"]}
        actions={
          <button
            onClick={() => refetch()}
            className="px-4 py-2 rounded-xl bg-gray-800/50 border border-gray-700/50 text-gray-300 hover:text-white hover:bg-gray-800 transition-all flex items-center gap-2"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        }
      />

      <GlassCard>
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search reports..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all [&>option]:bg-gray-800 [&>option]:text-white"
          >
            <option value="all" className="bg-gray-800 text-white">
              All Status
            </option>
            <option value="completed" className="bg-gray-800 text-white">
              Completed
            </option>
            <option value="running" className="bg-gray-800 text-white">
              Running
            </option>
            <option value="pending" className="bg-gray-800 text-white">
              Pending
            </option>
            <option value="failed" className="bg-gray-800 text-white">
              Failed
            </option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all [&>option]:bg-gray-800 [&>option]:text-white"
          >
            <option value="newest" className="bg-gray-800 text-white">
              Newest First
            </option>
            <option value="oldest" className="bg-gray-800 text-white">
              Oldest First
            </option>
          </select>
        </div>

        {/* Reports List */}
        {isLoading ? (
          <LoadingState message="Loading reports..." />
        ) : filteredReports.length === 0 ? (
          <EmptyState
            icon={DocumentTextIcon}
            title="No Reports Found"
            description={
              searchQuery || statusFilter !== "all"
                ? "Try adjusting your filters or search query"
                : "Start a security scan to generate your first report"
            }
          />
        ) : (
          <div className="space-y-3">
            {filteredReports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </div>
        )}

        {/* Pagination Info */}
        {reportsData?.pagination && (
          <div className="mt-6 pt-4 border-t border-gray-800/50 flex items-center justify-between text-sm text-gray-400">
            <span>
              Showing {filteredReports.length} of {reportsData.pagination.total}{" "}
              reports
            </span>
          </div>
        )}
      </GlassCard>
    </PageContainer>
  );
};

export default Reports;
