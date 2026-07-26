import { useState } from "react";
import { motion } from "framer-motion";
import {
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  FolderIcon,
  CalendarDaysIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import {
  PageContainer,
  PageHeader,
  GlassCard,
  SectionHeader,
  ErrorState,
} from "../layouts";
import ParticleBackground from "../components/projects/ParticleBackground";
import MetricCard from "../components/projects/MetricCard";
import useAnalyticsData from "../hooks/useAnalyticsData";
import SeverityDistribution from "../components/analytics/SeverityDistribution";
import ScanTypeDistribution from "../components/analytics/ScanTypeDistribution";
import RecentScansTimeline from "../components/analytics/RecentScansTimeline";
import TopProjects from "../components/analytics/TopProjects";
import ScannerPerformance from "../components/analytics/ScannerPerformance";
import TimePeriodSelector from "../components/analytics/TimePeriodSelector";

const containerAnim = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};
const itemAnim = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0 },
};

const cardColors = {
  scans: "#06b6d4",
  vulns: "#ef4444",
  score: "#10b981",
  projects: "#8b5cf6",
};

const Analytics = () => {
  const [daysBack, setDaysBack] = useState(30);
  const {
    vulnSummary,
    totalVulnerabilities,
    totalScans,
    successRate,
    avgSecurityScore,
    totalProjects,
    topProjects,
    scannerPerformance,
    analytics,
    reports,
    isLoading,
    hasError,
    refetch,
  } = useAnalyticsData(daysBack);

  if (hasError) {
    return (
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <ErrorState
            title="Failed to Load Analytics"
            message="Unable to fetch analytics data. Please try again."
            onRetry={refetch}
          />
        </div>
      </PageContainer>
    );
  }

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
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
                onClick={() => refetch()}
                aria-label="Refresh analytics data"
                className="p-2 rounded-lg bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 text-gray-400 hover:text-white transition-all hover:bg-gray-700/50"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {analytics?.period && (
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-6 bg-gray-800/20 backdrop-blur-sm border border-gray-700/30 rounded-lg px-4 py-2">
              <CalendarDaysIcon className="h-4 w-4" />
              <span>
                Showing data from{" "}
                {new Date(analytics.period.start_date).toLocaleDateString()} to{" "}
                {new Date(analytics.period.end_date).toLocaleDateString()}
              </span>
            </div>
          )}

          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
            variants={containerAnim}
            initial="hidden"
            animate="show"
          >
            <motion.div variants={itemAnim}>
              <MetricCard
                icon={DocumentTextIcon}
                label="Total Scans"
                value={isLoading ? 0 : totalScans}
                color={cardColors.scans}
              />
            </motion.div>
            <motion.div variants={itemAnim}>
              <MetricCard
                icon={ExclamationTriangleIcon}
                label="Total Vulnerabilities"
                value={isLoading ? 0 : totalVulnerabilities}
                color={cardColors.vulns}
              />
            </motion.div>
            <motion.div variants={itemAnim}>
              <MetricCard
                icon={ShieldCheckIcon}
                label="Avg Security Score"
                value={isLoading ? 0 : Math.round(avgSecurityScore)}
                color={cardColors.score}
                formatter={(v) => `${v}/100`}
              />
            </motion.div>
            <motion.div variants={itemAnim}>
              <MetricCard
                icon={FolderIcon}
                label="Active Projects"
                value={isLoading ? 0 : totalProjects}
                color={cardColors.projects}
              />
            </motion.div>
          </motion.div>

          <motion.div
            className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
            variants={containerAnim}
            initial="hidden"
            animate="show"
          >
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader
                  title="Vulnerability Severity"
                  description="Distribution across severity levels"
                />
                {isLoading ? (
                  <div className="h-[200px] bg-gray-800/30 rounded-xl animate-pulse" />
                ) : (
                  <SeverityDistribution data={vulnSummary} />
                )}
              </GlassCard>
            </motion.div>
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader
                  title="Scanner Activity"
                  description="Breakdown by scanner type"
                />
                {isLoading ? (
                  <div className="h-[200px] bg-gray-800/30 rounded-xl animate-pulse" />
                ) : (
                  <ScanTypeDistribution data={scannerPerformance} />
                )}
              </GlassCard>
            </motion.div>
          </motion.div>

          <motion.div
            className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
            variants={containerAnim}
            initial="hidden"
            animate="show"
          >
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader
                  title="Top Projects by Findings"
                  description="Projects with the most security findings"
                />
                {isLoading ? (
                  <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="h-16 bg-gray-800/30 rounded-xl animate-pulse"
                      />
                    ))}
                  </div>
                ) : (
                  <TopProjects projects={topProjects} />
                )}
              </GlassCard>
            </motion.div>
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader
                  title="Scanner Performance"
                  description="Success rates and average durations"
                />
                {isLoading ? (
                  <div className="space-y-3">
                    {[...Array(4)].map((_, i) => (
                      <div
                        key={i}
                        className="h-16 bg-gray-800/30 rounded-xl animate-pulse"
                      />
                    ))}
                  </div>
                ) : (
                  <ScannerPerformance scanners={scannerPerformance} />
                )}
              </GlassCard>
            </motion.div>
          </motion.div>

          <motion.div variants={itemAnim} initial="hidden" animate="show">
            <GlassCard>
              <SectionHeader
                title="Recent Scan Activity"
                description="Latest security scans and their results"
              />
              <RecentScansTimeline scans={reports || []} />
            </GlassCard>
          </motion.div>
        </div>
      </PageContainer>
    </div>
  );
};

export default Analytics;
