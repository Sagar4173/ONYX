import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheckIcon, BoltIcon, PlusIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { reportsAPI } from "../services/api";
import { dashboardAPI } from "../services/dashboardService";
import { PageContainer, PageHeader, GlassCard, SectionHeader, EmptyState } from "../layouts";
import SecurityScoreChart from "../components/dashboard/SecurityScoreChart";
import SeverityBar from "../components/dashboard/SeverityBar";
import QuickActions from "../components/dashboard/QuickActions";
import RecentScans from "../components/dashboard/RecentScans";
import DashboardStatsBar from "../components/dashboard/DashboardStatsBar";

const Dashboard = ({ notifications = [] }) => {
  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
    isFetching: statsFetching,
  } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardAPI.getQuickStats(),
    refetchInterval: 30000,
    staleTime: 30000,
  });

  const {
    data: reportsData,
    isLoading: reportsLoading,
    error: reportsError,
    refetch: refetchReports,
  } = useQuery({
    queryKey: ["recent-reports"],
    queryFn: () =>
      reportsAPI.getReports({
        limit: 10,
        sort_by: "created_at",
        sort_order: "desc",
      }),
    staleTime: 30000,
  });

  const { recentReports, severityDistribution } = useMemo(() => {
    const reports = reportsData?.reports || reportsData?.data || [];
    const dist = reports.reduce(
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
    return { recentReports: reports, severityDistribution: dist };
  }, [reportsData]);

  const score = stats?.avgSecurityScore != null ? Math.round(stats.avgSecurityScore) : null;

  const refresh = () => {
    refetchStats();
    refetchReports();
  };

  return (
    <PageContainer>
      <PageHeader
        title="Security Dashboard"
        description="Real-time overview of your security posture"
        icon={ShieldCheckIcon}
        breadcrumb={["Dashboard"]}
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={refresh}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl
                bg-gray-800/30 border border-gray-700/50 text-gray-300 hover:text-white hover:border-gray-600
                hover:bg-gray-800/50 transition-all duration-200"
            >
              <ArrowPathIcon className={`w-4 h-4 ${statsFetching ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
            <Link
              to="/projects?action=new"
              className="inline-flex items-center justify-center gap-2 px-8 py-3 text-base font-semibold rounded-full
                bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white
                hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300
                shadow-lg hover:shadow-xl hover:shadow-cyan-500/20
                transform hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
            >
              <PlusIcon className="h-5 w-5" />
              <span>New Project</span>
            </Link>
          </div>
        }
      />

      <DashboardStatsBar stats={stats} isLoading={statsLoading} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <GlassCard>
          <SectionHeader title="Security Overview" description="Current security status" />
          <SecurityScoreChart score={score} severitySummary={severityDistribution} />
          <div className="mt-6 pt-6 border-t border-gray-800/50">
            <h4 className="text-sm font-medium text-white mb-4">Vulnerability Distribution</h4>
            <SeverityBar data={severityDistribution} />
          </div>
        </GlassCard>

        <GlassCard>
          <SectionHeader title="Quick Actions" description="Common security operations" />
          <QuickActions />
        </GlassCard>

        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <SectionHeader title="Recent Scans" description="Latest security scans" />
            <Link
              to="/reports"
              className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              View all →
            </Link>
          </div>
          <RecentScans
            scans={recentReports}
            isLoading={reportsLoading}
            error={reportsError}
            onRetry={refetchReports}
          />
        </GlassCard>
      </div>

      <GlassCard>
        <SectionHeader title="Live Activity" description="Real-time notifications and updates" />
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
                <div className="p-2 rounded-lg bg-cyan-500/10 flex-shrink-0">
                  <BoltIcon className="w-4 h-4 text-cyan-400" />
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
