/**
 * Dashboard Page - Enhanced Enterprise Version
 * Real-time security overview with live data, charts, and actionable insights
 */
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  SparklesIcon,
  PlusIcon,
  BoltIcon,
  FolderIcon,
  DocumentChartBarIcon,
  ClockIcon,
  PlayIcon,
  ArrowRightIcon,
  ChartBarIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { StatCard, AnimatedCounter } from "../styles/components";
import {
  PageContainer,
  PageHeader,
  GlassCard,
  SectionHeader,
  LoadingState,
  EmptyState,
} from "../layouts";
import { reportsAPI } from "../services/api";
import { dashboardAPI } from "../services/dashboardService";

/**
 * Security Score Ring Chart
 */
const SecurityScoreChart = ({ score = 0, size = 160 }) => {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getScoreColor = (s) => {
    if (s >= 80)
      return { stroke: "url(#scoreGreen)", text: "text-emerald-400" };
    if (s >= 60) return { stroke: "url(#scoreYellow)", text: "text-amber-400" };
    return { stroke: "url(#scoreRed)", text: "text-red-400" };
  };

  const colors = getScoreColor(score);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        <defs>
          <linearGradient id="scoreGreen" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#22c55e" />
          </linearGradient>
          <linearGradient id="scoreYellow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#eab308" />
          </linearGradient>
          <linearGradient id="scoreRed" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#f43f5e" />
          </linearGradient>
        </defs>

        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(75, 85, 99, 0.3)"
          strokeWidth="12"
        />

        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold ${colors.text}`}>
          <AnimatedCounter value={score} />
        </span>
        <span className="text-xs text-gray-400 uppercase tracking-wider mt-1">
          Score
        </span>
      </div>
    </div>
  );
};

/**
 * Severity Distribution Bar
 */
const SeverityBar = ({ data }) => {
  const total =
    (data?.critical || 0) +
    (data?.high || 0) +
    (data?.medium || 0) +
    (data?.low || 0);
  if (total === 0)
    return (
      <p className="text-sm text-gray-500 text-center py-4">
        No vulnerabilities found
      </p>
    );

  const getWidth = (count) => `${(count / total) * 100}%`;

  return (
    <div className="space-y-3">
      <div className="flex h-3 rounded-full overflow-hidden bg-gray-800/50">
        {data?.critical > 0 && (
          <div
            className="bg-gradient-to-r from-red-500 to-rose-500 transition-all duration-500"
            style={{ width: getWidth(data.critical) }}
          />
        )}
        {data?.high > 0 && (
          <div
            className="bg-gradient-to-r from-orange-500 to-amber-500 transition-all duration-500"
            style={{ width: getWidth(data.high) }}
          />
        )}
        {data?.medium > 0 && (
          <div
            className="bg-gradient-to-r from-yellow-500 to-lime-500 transition-all duration-500"
            style={{ width: getWidth(data.medium) }}
          />
        )}
        {data?.low > 0 && (
          <div
            className="bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
            style={{ width: getWidth(data.low) }}
          />
        )}
      </div>

      <div className="flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-red-500 to-rose-500" />
          <span className="text-gray-400">
            Critical:{" "}
            <span className="text-white font-medium">
              {data?.critical || 0}
            </span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-orange-500 to-amber-500" />
          <span className="text-gray-400">
            High:{" "}
            <span className="text-white font-medium">{data?.high || 0}</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-yellow-500 to-lime-500" />
          <span className="text-gray-400">
            Medium:{" "}
            <span className="text-white font-medium">{data?.medium || 0}</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500" />
          <span className="text-gray-400">
            Low:{" "}
            <span className="text-white font-medium">{data?.low || 0}</span>
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * Quick Action Button
 */
const QuickAction = ({ action, index }) => (
  <button
    onClick={action.onClick}
    className="group relative flex flex-col items-center justify-center p-5 rounded-xl bg-gray-800/30 
             border border-gray-700/30 hover:border-gray-600/50 transition-all duration-300 
             hover:scale-[1.03] text-center flex-1 min-h-[120px]"
    style={{ animationDelay: `${index * 0.05}s` }}
  >
    <div
      className={`absolute inset-0 rounded-xl bg-gradient-to-br ${action.gradient} 
                    opacity-0 group-hover:opacity-10 transition-opacity`}
    />
    <div
      className={`p-3 rounded-xl bg-gradient-to-br ${action.gradient} shadow-lg mb-3
                    group-hover:scale-110 transition-transform`}
    >
      <action.icon className="h-5 w-5 text-white" />
    </div>
    <span className="text-sm font-medium text-white">{action.name}</span>
    <span className="text-xs text-gray-500 mt-1">{action.description}</span>
  </button>
);

/**
 * Recent Scan Item
 */
const RecentScanItem = ({ report, onClick }) => {
  const statusConfig = {
    completed: {
      icon: CheckCircleIcon,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      label: "Completed",
    },
    in_progress: {
      icon: ClockIcon,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      label: "Running",
    },
    failed: {
      icon: XCircleIcon,
      color: "text-red-400",
      bg: "bg-red-500/10",
      label: "Failed",
    },
    pending: {
      icon: ClockIcon,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      label: "Pending",
    },
  };

  const status = statusConfig[report.status] || statusConfig.pending;
  const StatusIcon = status.icon;

  const severityCount = report.findings_by_severity || {};
  const hasCritical = (severityCount.critical || 0) > 0;
  const hasHigh = (severityCount.high || 0) > 0;

  return (
    <div
      onClick={onClick}
      className="group flex items-center gap-4 p-4 rounded-xl bg-gray-800/20 hover:bg-gray-800/40 
               border border-transparent hover:border-gray-700/50 transition-all cursor-pointer"
    >
      {/* Status Icon */}
      <div className={`p-2.5 rounded-xl ${status.bg} flex-shrink-0`}>
        <StatusIcon className={`h-5 w-5 ${status.color}`} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-medium text-white truncate">
            {report.project_name || "Unknown Project"}
          </h4>
          {hasCritical && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-red-500/20 text-red-400">
              CRITICAL
            </span>
          )}
          {!hasCritical && hasHigh && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-orange-500/20 text-orange-400">
              HIGH
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{report.scan_type || "Security"} Scan</span>
          <span>•</span>
          <span>{report.total_findings || 0} findings</span>
          <span>•</span>
          <span>{new Date(report.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Arrow */}
      <ArrowRightIcon
        className="w-4 h-4 text-gray-500 group-hover:text-white 
                                group-hover:translate-x-1 transition-all flex-shrink-0"
      />
    </div>
  );
};

/**
 * Main Dashboard Component
 */
const Dashboard = ({ notifications = [] }) => {
  const navigate = useNavigate();

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardAPI.getQuickStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch recent reports
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ["recent-reports"],
    queryFn: () =>
      reportsAPI.getReports({
        limit: 10,
        sort_by: "created_at",
        sort_order: "desc",
      }),
  });

  // Calculate severity distribution from all reports
  const severityDistribution = React.useMemo(() => {
    const reports = reportsData?.reports || reportsData?.data || [];
    return reports.reduce(
      (acc, report) => {
        const severity = report.findings_by_severity || {};
        acc.critical += severity.critical || 0;
        acc.high += severity.high || 0;
        acc.medium += severity.medium || 0;
        acc.low += severity.low || 0;
        return acc;
      },
      { critical: 0, high: 0, medium: 0, low: 0 }
    );
  }, [reportsData]);

  // Stats cards data
  const statsCards = [
    {
      label: "Total Projects",
      value: stats?.totalProjects || 0,
      trend: stats?.projectsTrend,
      trendPositive: true,
      icon: FolderIcon,
      gradient: "from-blue-500 to-cyan-500",
      subtitle: "Active repositories",
    },
    {
      label: "Security Scans",
      value: stats?.totalScans || 0,
      trend: stats?.scansTrend,
      trendPositive: true,
      icon: ShieldCheckIcon,
      gradient: "from-violet-500 to-purple-500",
      subtitle: "Total scans performed",
    },
    {
      label: "Open Issues",
      value: stats?.openIssues || 0,
      trend: stats?.issuesTrend,
      trendPositive: false, // Lower is better
      icon: ExclamationTriangleIcon,
      gradient: "from-orange-500 to-red-500",
      subtitle: "Critical & high severity",
    },
    {
      label: "Security Score",
      value: stats?.avgSecurityScore != null ? `${Math.round(stats.avgSecurityScore)}%` : "N/A",
      trend: stats?.scoreTrend,
      trendPositive: true,
      icon: SparklesIcon,
      gradient: "from-emerald-500 to-green-500",
      subtitle: stats?.avgSecurityScore != null ? "Overall health" : "Run first scan",
    },
  ];

  // Quick actions
  const quickActions = [
    {
      name: "New Project",
      description: "Add repository",
      icon: PlusIcon,
      gradient: "from-blue-500 to-purple-600",
      onClick: () => navigate("/projects?action=new"),
    },
    {
      name: "Run Scan",
      description: "Start security scan",
      icon: PlayIcon,
      gradient: "from-emerald-500 to-green-500",
      onClick: () => navigate("/projects"),
    },
    {
      name: "View Reports",
      description: "See all findings",
      icon: DocumentChartBarIcon,
      gradient: "from-orange-500 to-amber-500",
      onClick: () => navigate("/reports"),
    },
    {
      name: "Analytics",
      description: "Explore trends",
      icon: ChartBarIcon,
      gradient: "from-pink-500 to-rose-500",
      onClick: () => navigate("/analytics"),
    },
  ];

  const recentReports = reportsData?.reports || reportsData?.data || [];

  if (statsLoading) {
    return (
      <PageContainer>
        <LoadingState message="Loading dashboard..." />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* Header */}
      <PageHeader
        title="Security Dashboard"
        description="Real-time overview of your security posture"
        icon={ShieldCheckIcon}
        breadcrumb={["Dashboard"]}
        actions={
          <Link
            to="/projects?action=new"
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 
                     text-white font-medium hover:from-blue-600 hover:to-purple-700 
                     transition-all flex items-center gap-2 shadow-lg hover:shadow-xl
                     hover:scale-105"
          >
            <PlusIcon className="h-4 w-4" />
            <span>New Project</span>
          </Link>
        }
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        {statsCards.map((stat, index) => (
          <div key={stat.label} style={{ animationDelay: `${index * 0.1}s` }}>
            <StatCard
              title={stat.label}
              value={stat.value}
              trend={stat.trend}
              trendPositive={stat.trendPositive}
              subtitle={stat.subtitle}
              gradient={stat.gradient}
              icon={<stat.icon className="h-5 w-5 text-white" />}
              animated
            />
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Security Score & Severity - Left Column */}
        <GlassCard>
          <SectionHeader
            title="Security Overview"
            description="Current security status"
          />

          <div className="flex flex-col items-center py-4">
            <SecurityScoreChart
              score={stats?.avgSecurityScore != null ? Math.round(stats.avgSecurityScore) : 0}
            />
            <p className="text-sm text-gray-400 mt-4 text-center">
              {stats?.avgSecurityScore == null
                ? "Run your first scan to see your score"
                : stats.avgSecurityScore >= 80
                ? "Your security posture is healthy"
                : stats.avgSecurityScore >= 60
                ? "Some issues need attention"
                : "Critical issues detected"}
            </p>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-800/50">
            <h4 className="text-sm font-medium text-white mb-4">
              Vulnerability Distribution
            </h4>
            <SeverityBar data={severityDistribution} />
          </div>
        </GlassCard>

        {/* Quick Actions - Middle Column */}
        <GlassCard>
          <SectionHeader
            title="Quick Actions"
            description="Common security operations"
          />

          <div className="grid grid-cols-2 gap-4">
            {quickActions.map((action, index) => (
              <QuickAction key={action.name} action={action} index={index} />
            ))}
          </div>
        </GlassCard>

        {/* Recent Scans - Right Column */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <SectionHeader
              title="Recent Scans"
              description="Latest security scans"
            />
            <Link
              to="/reports"
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              View all →
            </Link>
          </div>

          <div className="space-y-2">
            {reportsLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto" />
              </div>
            ) : recentReports.length === 0 ? (
              <EmptyState
                icon={DocumentChartBarIcon}
                title="No scans yet"
                description="Create a project to start scanning"
              />
            ) : (
              recentReports
                .slice(0, 4)
                .map((report) => (
                  <RecentScanItem
                    key={report.id || report._id}
                    report={report}
                    onClick={() =>
                      navigate(`/report/${report.id || report._id}`)
                    }
                  />
                ))
            )}
          </div>
        </GlassCard>
      </div>

      {/* Bottom Row - Live Activity */}
      <GlassCard>
        <SectionHeader
          title="Live Activity"
          description="Real-time notifications and updates"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[200px] overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="col-span-full">
              <EmptyState
                icon={BoltIcon}
                title="No recent activity"
                description="Updates will appear here in real-time"
              />
            </div>
          ) : (
            notifications.slice(0, 6).map((notif) => (
              <div
                key={notif.id}
                className="flex items-center gap-3 p-3 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
              >
                <div className="p-2 rounded-lg bg-blue-500/10 flex-shrink-0">
                  <BoltIcon className="w-4 h-4 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{notif.message}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(notif.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </GlassCard>
    </PageContainer>
  );
};

export default Dashboard;
