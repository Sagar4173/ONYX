import { useMemo } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheckIcon, BoltIcon, PlusIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { reportsAPI } from "../services/api";
import { dashboardAPI } from "../services/dashboardService";
import { PageContainer, PageHeader, GlassCard, SectionHeader, EmptyState } from "../layouts";
import ParticleBackground from "../components/projects/ParticleBackground";
import MetricCard from "../components/projects/MetricCard";
import DashboardHero from "../components/dashboard/DashboardHero";
import ScoreTrendChart from "../components/dashboard/ScoreTrendChart";
import QuickActions from "../components/dashboard/QuickActions";
import RecentScans from "../components/dashboard/RecentScans";

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
    queryFn: () => reportsAPI.getReports({ limit: 10, sort_by: "created_at", sort_order: "desc" }),
    staleTime: 30000,
  });

  const { recentReports, severityDistribution } = useMemo(() => {
    const reports = reportsData?.reports || reportsData?.data || [];
    const dist = reports.reduce(
      (acc, r) => {
        const sev = r.findings_by_severity || {};
        acc.critical += sev.critical || 0;
        acc.high += sev.high || 0;
        acc.medium += sev.medium || 0;
        acc.low += sev.low || 0;
        return acc;
      },
      { critical: 0, high: 0, medium: 0, low: 0 }
    );
    return { recentReports: reports, severityDistribution: dist };
  }, [reportsData]);

  const score = stats?.avgSecurityScore != null ? Math.round(stats.avgSecurityScore) : null;
  const scoreTrend = stats?.scoreTrend ?? null;

  const refresh = () => {
    refetchStats();
    refetchReports();
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        visible: { transition: { staggerChildren: 0.08 } },
      }}
      className="relative min-h-screen"
    >
      <ParticleBackground />
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
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl bg-gray-800/30 border border-gray-700/50 text-gray-300 hover:text-white hover:border-gray-600 hover:bg-gray-800/50 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
              >
                <ArrowPathIcon className={`w-4 h-4 ${statsFetching ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
              <Link
                to="/projects?action=new"
                className="inline-flex items-center justify-center gap-2 px-8 py-3 text-base font-semibold rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transform hover:scale-[1.03] active:scale-[0.98] transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                <PlusIcon className="h-5 w-5" />
                <span>New Project</span>
              </Link>
            </div>
          }
        />

        <DashboardHero securityScore={score} scoreTrend={scoreTrend} />

        {statsLoading ? (
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 15 },
              visible: { opacity: 1, y: 0 },
            }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
          >
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-[120px] bg-gray-800/30 rounded-xl animate-pulse p-4 flex flex-col justify-between"
              >
                <div className="h-3 w-24 bg-gray-700/50 rounded-full" />
                <div className="h-8 w-16 bg-gray-700/50 rounded-lg" />
                <div className="h-2.5 w-full bg-gray-700/40 rounded-full" />
              </div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 15 },
              visible: { opacity: 1, y: 0 },
            }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
          >
            <MetricCard
              title="Projects"
              value={stats?.totalProjects ?? 0}
              trend={stats?.projectsTrend}
              icon={ShieldCheckIcon}
            />
            <MetricCard
              title="Total Scans"
              value={stats?.totalScans ?? 0}
              trend={stats?.scansTrend}
              icon={ArrowPathIcon}
            />
            <MetricCard
              title="Open Issues"
              value={stats?.openIssues ?? 0}
              trend={stats?.issuesTrend}
              icon={BoltIcon}
              colorClass={
                stats?.openIssues > 0 ? "from-red-500 to-orange-500" : "from-cyan-400 to-violet-500"
              }
            />
            <MetricCard
              title="Avg Score"
              value={score != null ? score : "—"}
              trend={scoreTrend}
              icon={ShieldCheckIcon}
              colorClass={
                score >= 80
                  ? "from-emerald-400 to-cyan-500"
                  : score >= 60
                    ? "from-yellow-400 to-orange-500"
                    : "from-red-400 to-rose-500"
              }
            />
          </motion.div>
        )}

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 15 },
            visible: { opacity: 1, y: 0 },
          }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"
        >
          <GlassCard>
            <SectionHeader title="Security Overview" description="Score trend over time" />
            <ScoreTrendChart reports={recentReports} />
            <div className="mt-4 pt-4 border-t border-gray-800/50">
              <h4 className="text-sm font-medium text-white mb-3">Vulnerability Distribution</h4>
              {[
                {
                  label: "Critical",
                  count: severityDistribution.critical || 0,
                  color: "from-red-500 to-rose-500",
                },
                {
                  label: "High",
                  count: severityDistribution.high || 0,
                  color: "from-orange-500 to-amber-500",
                },
                {
                  label: "Medium",
                  count: severityDistribution.medium || 0,
                  color: "from-yellow-500 to-lime-500",
                },
                {
                  label: "Low",
                  count: severityDistribution.low || 0,
                  color: "from-blue-500 to-cyan-500",
                },
              ].map(({ label, count, color }) => (
                <div key={label} className="flex items-center justify-between text-sm py-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${color}`} />
                    <span className="text-gray-400">{label}</span>
                  </div>
                  <span className="text-white font-medium">{count}</span>
                </div>
              ))}
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
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 15 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <GlassCard>
            <SectionHeader
              title="Live Activity"
              description="Real-time notifications and updates"
            />
            <div className="max-h-[200px] overflow-y-auto space-y-2">
              {notifications.length === 0 ? (
                <EmptyState
                  icon={BoltIcon}
                  title="No recent activity"
                  description="Updates will appear here in real-time"
                />
              ) : (
                notifications.slice(0, 6).map((notif) => {
                  const typeStyle =
                    notif.type === "scan_completed"
                      ? "text-emerald-400 bg-emerald-500/10"
                      : notif.type === "scan_error"
                        ? "text-red-400 bg-red-500/10"
                        : notif.type === "scan_started"
                          ? "text-blue-400 bg-blue-500/10"
                          : "text-cyan-400 bg-cyan-500/10";
                  const IconComponent =
                    notif.type === "scan_completed"
                      ? ShieldCheckIcon
                      : notif.type === "scan_error"
                        ? ArrowPathIcon
                        : BoltIcon;

                  return (
                    <motion.div
                      key={notif.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2 }}
                      className="flex items-center gap-3 p-3 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
                    >
                      <div className={`p-2 rounded-lg ${typeStyle} flex-shrink-0`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{notif.message}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(notif.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </GlassCard>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
};

export default Dashboard;
