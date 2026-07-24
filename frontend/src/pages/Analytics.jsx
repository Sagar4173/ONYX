/**
 * Analytics Page - Security Analytics Dashboard
 * Displays security trends, vulnerability metrics, and scan insights
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  DocumentTextIcon,
  EyeIcon,
  CodeBracketIcon,
  ServerIcon,
  CubeIcon,
  CheckCircleIcon,
  XCircleIcon,
  FolderIcon,
  CalendarDaysIcon,
  CpuChipIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { StatCard, EmptyState } from "../styles/components";
import {
  PageContainer,
  PageHeader,
  GlassCard,
  SectionHeader,
  LoadingState,
} from "../layouts";
import { reportsAPI, projectsAPI } from "../services/api";
import { Link } from "react-router-dom";

// Severity Distribution Chart (simplified bar chart)
const SeverityDistribution = ({ data }) => {
  const severities = [
    {
      key: "critical",
      label: "Critical",
      color: "bg-red-500",
      textColor: "text-red-400",
    },
    {
      key: "high",
      label: "High",
      color: "bg-orange-500",
      textColor: "text-orange-400",
    },
    {
      key: "medium",
      label: "Medium",
      color: "bg-yellow-500",
      textColor: "text-yellow-400",
    },
    {
      key: "low",
      label: "Low",
      color: "bg-blue-500",
      textColor: "text-blue-400",
    },
    {
      key: "info",
      label: "Info",
      color: "bg-gray-500",
      textColor: "text-gray-400",
    },
  ];

  const total =
    severities.reduce((sum, s) => sum + (data?.[s.key] || 0), 0) || 1;

  return (
    <div className="space-y-4">
      {severities.map((severity) => {
        const count = data?.[severity.key] || 0;
        const percentage = Math.round((count / total) * 100);
        return (
          <div key={severity.key}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${severity.textColor}`}>
                {severity.label}
              </span>
              <span className="text-sm text-gray-400">
                {count} ({percentage}%)
              </span>
            </div>
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${severity.color} rounded-full transition-all duration-500`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Scan Type Distribution
const ScanTypeDistribution = ({ data }) => {
  const scanTypes = [
    {
      key: "sast",
      label: "Static Analysis",
      icon: CodeBracketIcon,
      color: "from-blue-500 to-cyan-500",
    },
    {
      key: "secrets",
      label: "Secret Detection",
      icon: EyeIcon,
      color: "from-purple-500 to-pink-500",
    },
    {
      key: "container",
      label: "Container Scan",
      icon: CubeIcon,
      color: "from-green-500 to-emerald-500",
    },
    {
      key: "infrastructure",
      label: "Infrastructure",
      icon: ServerIcon,
      color: "from-orange-500 to-red-500",
    },
  ];

  // Handle both direct scan type counts and scanner_performance format
  const getCount = (key) => {
    if (!data) return 0;
    // Direct count
    if (typeof data[key] === "number") return data[key];
    // Scanner performance format
    if (data[key]?.total_runs) return data[key].total_runs;
    // Try common scanner names
    const scannerNames = {
      sast: ["semgrep", "bandit", "eslint"],
      secrets: ["gitleaks", "trufflehog"],
      container: ["trivy", "grype"],
      infrastructure: ["checkov", "tfsec"],
    };
    let count = 0;
    scannerNames[key]?.forEach((scanner) => {
      if (data[scanner]?.total_runs) count += data[scanner].total_runs;
    });
    return count;
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      {scanTypes.map((type) => {
        const count = getCount(type.key);
        return (
          <div
            key={type.key}
            className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50 transition-all group"
          >
            <div
              className={`inline-flex p-2.5 rounded-xl bg-gradient-to-r ${type.color} mb-3 group-hover:scale-110 transition-transform`}
            >
              <type.icon className="h-5 w-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-white">{count}</p>
            <p className="text-sm text-gray-400">{type.label}</p>
          </div>
        );
      })}
    </div>
  );
};

// Recent Scans Timeline
const RecentScansTimeline = ({ scans = [] }) => {
  if (scans.length === 0) {
    return (
      <EmptyState
        icon={ClockIcon}
        title="No Recent Scans"
        description="Start a security scan to see activity here"
      />
    );
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
      {scans.map((scan, index) => (
        <Link
          to={`/report/${scan.id}`}
          key={scan.id || index}
          className="flex items-start space-x-4 p-4 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all border border-transparent hover:border-gray-700/50 group"
        >
          <div
            className={`p-2.5 rounded-lg ${
              scan.status === "completed"
                ? "bg-green-500/20"
                : scan.status === "failed"
                ? "bg-red-500/20"
                : "bg-blue-500/20"
            }`}
          >
            {scan.status === "completed" ? (
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
            ) : scan.status === "failed" ? (
              <XCircleIcon className="h-5 w-5 text-red-400" />
            ) : (
              <ArrowPathIcon className="h-5 w-5 text-blue-400 animate-spin" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate group-hover:text-blue-400 transition-colors">
              {scan.project_name || scan.repository_url || "Unknown Project"}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  scan.status === "completed"
                    ? "bg-green-500/20 text-green-400"
                    : scan.status === "failed"
                    ? "bg-red-500/20 text-red-400"
                    : "bg-blue-500/20 text-blue-400"
                }`}
              >
                {scan.status}
              </span>
              <span className="text-xs text-gray-500">
                {scan.total_findings || scan.findings_count || 0} findings
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-gray-500">
              {new Date(scan.created_at).toLocaleDateString()}
            </span>
            <p className="text-xs text-gray-600 mt-1">
              {new Date(scan.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
};

// Top Projects Component
const TopProjects = ({ projects = [] }) => {
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FolderIcon}
        title="No Project Data"
        description="Scan some projects to see analytics"
      />
    );
  }

  return (
    <div className="space-y-3">
      {projects.slice(0, 5).map((project, index) => (
        <div
          key={project.project_name || index}
          className="flex items-center justify-between p-4 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all border border-gray-700/30"
        >
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
              {index + 1}
            </div>
            <div>
              <p className="text-sm font-medium text-white">
                {project.project_name}
              </p>
              <p className="text-xs text-gray-500">
                {project.scans_count} scans
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              {project.critical_findings > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400">
                  {project.critical_findings} critical
                </span>
              )}
              {project.high_findings > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-orange-500/20 text-orange-400">
                  {project.high_findings} high
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {project.total_findings} total findings
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

// Scanner Performance Component
const ScannerPerformance = ({ scanners = {} }) => {
  const scannerList = Object.entries(scanners).map(([name, stats]) => ({
    name,
    ...stats,
  }));

  if (scannerList.length === 0) {
    return (
      <EmptyState
        icon={CpuChipIcon}
        title="No Scanner Data"
        description="Run scans to see scanner performance"
      />
    );
  }

  const formatDuration = (seconds) => {
    if (!seconds || seconds === 0) return "N/A";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  };

  return (
    <div className="space-y-3">
      {scannerList.slice(0, 6).map((scanner) => {
        const successRate =
          scanner.total_runs > 0
            ? Math.round((scanner.successful_runs / scanner.total_runs) * 100)
            : 0;
        return (
          <div
            key={scanner.name}
            className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/30"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white capitalize">
                {scanner.name}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  successRate >= 90
                    ? "bg-green-500/20 text-green-400"
                    : successRate >= 70
                    ? "bg-yellow-500/20 text-yellow-400"
                    : "bg-red-500/20 text-red-400"
                }`}
              >
                {successRate}% success
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
              <div>
                <span className="text-gray-500">Runs:</span>{" "}
                {scanner.total_runs}
              </div>
              <div>
                <span className="text-gray-500">Findings:</span>{" "}
                {scanner.total_findings}
              </div>
              <div>
                <span className="text-gray-500">Avg:</span>{" "}
                {formatDuration(scanner.avg_duration)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Time Period Selector
const TimePeriodSelector = ({ value, onChange }) => {
  const periods = [
    { value: 7, label: "7 Days" },
    { value: 30, label: "30 Days" },
    { value: 90, label: "90 Days" },
  ];

  return (
    <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg p-1">
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onChange(period.value)}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
            value === period.value
              ? "bg-blue-500 text-white"
              : "text-gray-400 hover:text-white hover:bg-gray-700/50"
          }`}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
};

// Main Analytics Component
const Analytics = () => {
  const [daysBack, setDaysBack] = useState(30);

  // Fetch analytics data from reports API
  const {
    data: analytics,
    isLoading: analyticsLoading,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ["analytics", daysBack],
    queryFn: () => reportsAPI.getAnalyticsOverview(daysBack),
  });

  // Fetch project analytics
  const { data: projectAnalytics, isLoading: projectLoading } = useQuery({
    queryKey: ["projectAnalytics"],
    queryFn: () => projectsAPI.getAnalyticsOverview(),
  });

  // Fetch recent reports
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ["reports", { limit: 50 }],
    queryFn: () => reportsAPI.getReports({ limit: 50 }),
  });

  const isLoading = analyticsLoading || reportsLoading || projectLoading;

  // Extract data from API response (handle both formats)
  const scanSummary = analytics?.scan_summary || {};
  const vulnSummary = analytics?.vulnerability_summary || {};
  const topProjects = analytics?.top_projects || [];
  const scannerPerformance = analytics?.scanner_performance || {};

  // If analytics endpoint doesn't return data, calculate from reports
  const reports = reportsData?.reports || [];

  // Calculate vulnerabilities from reports if not in analytics
  let calculatedVulnSummary = { ...vulnSummary };
  let calculatedTotalFindings = 0;

  if (reports.length > 0) {
    // Aggregate findings from reports
    const aggregatedFindings = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      info: 0,
    };

    reports.forEach((report) => {
      if (report.findings_by_severity) {
        aggregatedFindings.critical +=
          report.findings_by_severity.critical || 0;
        aggregatedFindings.high += report.findings_by_severity.high || 0;
        aggregatedFindings.medium += report.findings_by_severity.medium || 0;
        aggregatedFindings.low += report.findings_by_severity.low || 0;
        aggregatedFindings.info += report.findings_by_severity.info || 0;
      }
      calculatedTotalFindings += report.total_findings || 0;
    });

    // Use aggregated if analytics is empty
    const analyticsTotal =
      (vulnSummary.critical || 0) +
      (vulnSummary.high || 0) +
      (vulnSummary.medium || 0) +
      (vulnSummary.low || 0) +
      (vulnSummary.info || 0);

    const aggregatedTotal =
      aggregatedFindings.critical +
      aggregatedFindings.high +
      aggregatedFindings.medium +
      aggregatedFindings.low +
      aggregatedFindings.info;

    if (
      analyticsTotal === 0 &&
      (calculatedTotalFindings > 0 || aggregatedTotal > 0)
    ) {
      calculatedVulnSummary = aggregatedFindings;
      // If we have total_findings but no severity breakdown, classify as "info"
      if (aggregatedTotal === 0 && calculatedTotalFindings > 0) {
        calculatedVulnSummary.info = calculatedTotalFindings;
      }
    }
  }

  // Calculate total vulnerabilities - use calculated total if available
  const totalVulnerabilities =
    calculatedTotalFindings > 0
      ? calculatedTotalFindings
      : (calculatedVulnSummary.critical || 0) +
        (calculatedVulnSummary.high || 0) +
        (calculatedVulnSummary.medium || 0) +
        (calculatedVulnSummary.low || 0) +
        (calculatedVulnSummary.info || 0);

  // Calculate top projects from reports if not in analytics
  let calculatedTopProjects = topProjects;
  if (topProjects.length === 0 && reports.length > 0) {
    const projectMap = {};
    reports.forEach((report) => {
      const name = report.project_name || "Unknown";
      if (!projectMap[name]) {
        projectMap[name] = {
          project_name: name,
          total_findings: 0,
          scans_count: 0,
          critical_findings: 0,
          high_findings: 0,
        };
      }
      projectMap[name].scans_count += 1;
      projectMap[name].total_findings += report.total_findings || 0;
      projectMap[name].critical_findings +=
        report.findings_by_severity?.critical || 0;
      projectMap[name].high_findings += report.findings_by_severity?.high || 0;
    });
    calculatedTopProjects = Object.values(projectMap)
      .sort((a, b) => b.total_findings - a.total_findings)
      .slice(0, 10);
  }

  // Calculate scanner performance from reports if not in analytics
  let calculatedScannerPerformance = scannerPerformance;
  if (Object.keys(scannerPerformance).length === 0 && reports.length > 0) {
    const scannerMap = {};
    reports.forEach((report) => {
      if (report.scan_results) {
        report.scan_results.forEach((result) => {
          const scanner = result.scanner || "unknown";
          if (!scannerMap[scanner]) {
            scannerMap[scanner] = {
              total_runs: 0,
              successful_runs: 0,
              total_findings: 0,
              avg_duration: 0,
              total_duration: 0,
            };
          }
          scannerMap[scanner].total_runs += 1;
          if (result.status === "completed") {
            scannerMap[scanner].successful_runs += 1;
            scannerMap[scanner].total_findings += result.findings?.length || 0;
            if (result.duration_seconds) {
              scannerMap[scanner].total_duration += result.duration_seconds;
            }
          }
        });
      }
    });
    // Calculate averages
    Object.values(scannerMap).forEach((stats) => {
      if (stats.successful_runs > 0) {
        stats.avg_duration = stats.total_duration / stats.successful_runs;
      }
    });
    calculatedScannerPerformance = scannerMap;
  }

  // Use project analytics for additional data
  const avgSecurityScore = projectAnalytics?.average_security_score || 0;
  const totalProjects = projectAnalytics?.total_projects || 0;

  // Calculate scan summary from reports if needed
  const completedScans = reports.filter((r) => r.status === "completed").length;
  const failedScans = reports.filter((r) => r.status === "failed").length;
  const totalScans = scanSummary.total_scans || reports.length || 0;
  const successRate =
    totalScans > 0
      ? Math.round((completedScans / totalScans) * 100)
      : scanSummary.success_rate || 0;

  // Calculate stats
  const stats = [
    {
      title: "Total Scans",
      value: isLoading ? "..." : totalScans.toString(),
      change: totalScans > 0 ? `${successRate}% success` : null,
      changeType:
        successRate >= 80
          ? "positive"
          : successRate >= 50
          ? "neutral"
          : "negative",
      icon: DocumentTextIcon,
      gradient: "from-blue-500 to-cyan-500",
      bgGradient: "from-blue-500/10 to-cyan-500/10",
    },
    {
      title: "Total Vulnerabilities",
      value: isLoading ? "..." : totalVulnerabilities.toString(),
      change:
        calculatedVulnSummary.critical > 0
          ? `${calculatedVulnSummary.critical} critical`
          : calculatedVulnSummary.high > 0
          ? `${calculatedVulnSummary.high} high`
          : null,
      changeType:
        calculatedVulnSummary.critical > 0
          ? "negative"
          : calculatedVulnSummary.high > 0
          ? "negative"
          : "positive",
      icon: ExclamationTriangleIcon,
      gradient: "from-red-500 to-pink-500",
      bgGradient: "from-red-500/10 to-pink-500/10",
    },
    {
      title: "Avg Security Score",
      value: isLoading ? "..." : `${Math.round(avgSecurityScore)}/100`,
      change:
        avgSecurityScore >= 80
          ? "Healthy"
          : avgSecurityScore >= 50
          ? "Needs Work"
          : "At Risk",
      changeType:
        avgSecurityScore >= 80
          ? "positive"
          : avgSecurityScore >= 50
          ? "neutral"
          : "negative",
      icon: ShieldCheckIcon,
      gradient: "from-green-500 to-emerald-500",
      bgGradient: "from-green-500/10 to-emerald-500/10",
    },
    {
      title: "Active Projects",
      value: isLoading ? "..." : totalProjects.toString(),
      change: projectAnalytics?.active_projects
        ? `${projectAnalytics.active_projects} active`
        : null,
      changeType: "positive",
      icon: FolderIcon,
      gradient: "from-purple-500 to-violet-500",
      bgGradient: "from-purple-500/10 to-violet-500/10",
    },
  ];

  return (
    <PageContainer>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <PageHeader
          title="Analytics"
          description="Security insights, vulnerability trends, and scan metrics"
          icon={ChartBarIcon}
          breadcrumb={["Analytics"]}
        />
        <div className="flex items-center gap-3">
          <TimePeriodSelector value={daysBack} onChange={setDaysBack} />
          <button
            onClick={() => refetchAnalytics()}
            className="p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 text-gray-400 hover:text-white transition-all"
            title="Refresh data"
          >
            <ArrowPathIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Period Info */}
      {analytics?.period && (
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
          <CalendarDaysIcon className="h-4 w-4" />
          <span>
            Showing data from{" "}
            {new Date(analytics.period.start_date).toLocaleDateString()} to{" "}
            {new Date(analytics.period.end_date).toLocaleDateString()}
          </span>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        {stats.map((stat) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            icon={<stat.icon className="h-5 w-5 text-white" />}
            gradient={stat.gradient}
            bgGradient={stat.bgGradient}
          />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Severity Distribution */}
        <GlassCard>
          <SectionHeader
            title="Vulnerability Severity"
            description="Distribution across severity levels"
          />
          {isLoading ? (
            <LoadingState message="Loading severity data..." />
          ) : totalVulnerabilities === 0 ? (
            <EmptyState
              icon={<ExclamationTriangleIcon className="h-12 w-12" />}
              title="No vulnerabilities found"
              description="No security findings have been detected yet. Run a scan to see results."
            />
          ) : (
            <SeverityDistribution data={calculatedVulnSummary} />
          )}
        </GlassCard>

        {/* Scan Type Distribution */}
        <GlassCard>
          <SectionHeader
            title="Scanner Activity"
            description="Breakdown by scanner type"
          />
          {isLoading ? (
            <LoadingState message="Loading scan data..." />
          ) : Object.keys(calculatedScannerPerformance).length === 0 ? (
            <EmptyState
              icon={<ClockIcon className="h-12 w-12" />}
              title="No scanner activity"
              description="No scanner data available yet. Scanners will appear once scans are run."
            />
          ) : (
            <ScanTypeDistribution data={calculatedScannerPerformance} />
          )}
        </GlassCard>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Top Projects */}
        <GlassCard>
          <SectionHeader
            title="Top Projects by Findings"
            description="Projects with the most security findings"
          />
          {isLoading ? (
            <LoadingState message="Loading project data..." />
          ) : (
            <TopProjects projects={calculatedTopProjects} />
          )}
        </GlassCard>

        {/* Scanner Performance */}
        <GlassCard>
          <SectionHeader
            title="Scanner Performance"
            description="Success rates and average durations"
          />
          {isLoading ? (
            <LoadingState message="Loading scanner data..." />
          ) : (
            <ScannerPerformance scanners={calculatedScannerPerformance} />
          )}
        </GlassCard>
      </div>

      {/* Recent Activity */}
      <GlassCard>
        <SectionHeader
          title="Recent Scan Activity"
          description="Latest security scans and their results"
        />
        {reportsLoading ? (
          <LoadingState message="Loading recent scans..." />
        ) : (
          <RecentScansTimeline scans={reports} />
        )}
      </GlassCard>
    </PageContainer>
  );
};

export default Analytics;
