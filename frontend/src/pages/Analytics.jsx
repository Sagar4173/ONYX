/**
 * Analytics Page - Security Analytics Dashboard
 * Displays security trends, vulnerability metrics, and scan insights
 */
import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  DocumentTextIcon,
  BoltIcon,
  EyeIcon,
  CodeBracketIcon,
  ServerIcon,
  CubeIcon,
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

// Stat Card Component
const StatCard = ({
  title,
  value,
  change,
  changeType,
  icon: Icon,
  gradient,
  bgGradient,
}) => {
  const isPositive = changeType === "positive" || change?.startsWith("+");
  const isNegative = changeType === "negative" || change?.startsWith("-");

  return (
    <div className="relative group">
      <div className="absolute inset-0 bg-gradient-to-r from-gray-800/30 to-gray-700/30 rounded-2xl blur-xl group-hover:blur-2xl transition-all" />
      <div
        className={`relative p-5 rounded-2xl border border-gray-800/50 bg-gradient-to-br ${bgGradient} backdrop-blur-xl hover:border-gray-700/50 transition-all`}
      >
        <div className="flex items-center justify-between mb-3">
          <div
            className={`p-2.5 rounded-xl bg-gradient-to-r ${gradient} shadow-lg`}
          >
            <Icon className="h-5 w-5 text-white" />
          </div>
          {change && (
            <span
              className={`text-sm font-medium flex items-center gap-1 ${
                isPositive
                  ? "text-green-400"
                  : isNegative
                  ? "text-red-400"
                  : "text-gray-400"
              }`}
            >
              {isPositive ? (
                <ArrowTrendingUpIcon className="h-4 w-4" />
              ) : isNegative ? (
                <ArrowTrendingDownIcon className="h-4 w-4" />
              ) : null}
              {change}
            </span>
          )}
        </div>
        <h3 className="text-2xl font-bold text-white mb-1">{value}</h3>
        <p className="text-gray-400 text-sm">{title}</p>
      </div>
    </div>
  );
};

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

  return (
    <div className="grid grid-cols-2 gap-4">
      {scanTypes.map((type) => {
        const count = data?.[type.key] || 0;
        return (
          <div
            key={type.key}
            className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50 transition-all"
          >
            <div
              className={`inline-flex p-2 rounded-xl bg-gradient-to-r ${type.color} mb-3`}
            >
              <type.icon className="h-5 w-5 text-white" />
            </div>
            <p className="text-xl font-bold text-white">{count}</p>
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
    <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
      {scans.map((scan, index) => (
        <div
          key={scan.id || index}
          className="flex items-start space-x-4 p-4 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all"
        >
          <div
            className={`p-2 rounded-lg ${
              scan.status === "completed"
                ? "bg-green-500/20"
                : scan.status === "failed"
                ? "bg-red-500/20"
                : "bg-blue-500/20"
            }`}
          >
            <DocumentTextIcon
              className={`h-5 w-5 ${
                scan.status === "completed"
                  ? "text-green-400"
                  : scan.status === "failed"
                  ? "text-red-400"
                  : "text-blue-400"
              }`}
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {scan.project_name || scan.repository_url || "Unknown Project"}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {scan.findings_count || 0} findings •{" "}
              {scan.scan_type || "security"} scan
            </p>
          </div>
          <span className="text-xs text-gray-500">
            {new Date(scan.created_at).toLocaleDateString()}
          </span>
        </div>
      ))}
    </div>
  );
};

// Main Analytics Component
const Analytics = () => {
  // Fetch analytics data
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["analytics", 30],
    queryFn: () => reportsAPI.getAnalyticsOverview(30),
  });

  // Fetch recent reports
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ["reports", { limit: 10 }],
    queryFn: () => reportsAPI.getReports({ limit: 10 }),
  });

  const isLoading = analyticsLoading || reportsLoading;

  // Calculate stats
  const stats = [
    {
      title: "Total Scans",
      value: isLoading
        ? "..."
        : (
            analytics?.total_scans ||
            reportsData?.pagination?.total ||
            0
          ).toString(),
      change: analytics?.scans_change || "+12%",
      changeType: "positive",
      icon: DocumentTextIcon,
      gradient: "from-blue-500 to-cyan-500",
      bgGradient: "from-blue-500/10 to-cyan-500/10",
    },
    {
      title: "Vulnerabilities Found",
      value: isLoading
        ? "..."
        : (analytics?.total_vulnerabilities || 0).toString(),
      change: analytics?.vuln_change || "-5%",
      changeType: "negative",
      icon: ExclamationTriangleIcon,
      gradient: "from-red-500 to-pink-500",
      bgGradient: "from-red-500/10 to-pink-500/10",
    },
    {
      title: "Avg Security Score",
      value: isLoading
        ? "..."
        : `${Math.round(analytics?.average_security_score || 85)}/100`,
      change: analytics?.score_change || "+8%",
      changeType: "positive",
      icon: ShieldCheckIcon,
      gradient: "from-green-500 to-emerald-500",
      bgGradient: "from-green-500/10 to-emerald-500/10",
    },
    {
      title: "Scans This Week",
      value: isLoading
        ? "..."
        : (
            analytics?.scans_this_week ||
            analytics?.scans_last_24h ||
            0
          ).toString(),
      change: analytics?.weekly_change || "+15%",
      changeType: "positive",
      icon: BoltIcon,
      gradient: "from-purple-500 to-violet-500",
      bgGradient: "from-purple-500/10 to-violet-500/10",
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Analytics"
        description="Security insights, vulnerability trends, and scan metrics"
        icon={ChartBarIcon}
        breadcrumb={["Analytics"]}
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        {stats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
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
          ) : (
            <SeverityDistribution data={analytics?.severity_distribution} />
          )}
        </GlassCard>

        {/* Scan Type Distribution */}
        <GlassCard>
          <SectionHeader
            title="Scan Types"
            description="Breakdown by scan category"
          />
          {isLoading ? (
            <LoadingState message="Loading scan data..." />
          ) : (
            <ScanTypeDistribution data={analytics?.scan_types} />
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
          <RecentScansTimeline scans={reportsData?.reports || []} />
        )}
      </GlassCard>
    </PageContainer>
  );
};

export default Analytics;
