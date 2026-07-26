import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  FolderIcon,
  CalendarDaysIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { StatCard } from "../styles/components";
import { PageContainer, PageHeader, GlassCard, SectionHeader, LoadingState } from "../layouts";
import { reportsAPI, projectsAPI } from "../services/api";
import SeverityDistribution from "../components/analytics/SeverityDistribution";
import ScanTypeDistribution from "../components/analytics/ScanTypeDistribution";
import RecentScansTimeline from "../components/analytics/RecentScansTimeline";
import TopProjects from "../components/analytics/TopProjects";
import ScannerPerformance from "../components/analytics/ScannerPerformance";
import TimePeriodSelector from "../components/analytics/TimePeriodSelector";

const Analytics = () => {
  const [daysBack, setDaysBack] = useState(30);

  const {
    data: analytics,
    isLoading: analyticsLoading,
    isError: analyticsError,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ["analytics", daysBack],
    queryFn: () => reportsAPI.getAnalyticsOverview(daysBack),
    staleTime: 30000,
  });

  const {
    data: projectAnalytics,
    isLoading: projectLoading,
    isError: projectError,
  } = useQuery({
    queryKey: ["projectAnalytics"],
    queryFn: () => projectsAPI.getAnalyticsOverview(),
    staleTime: 30000,
  });

  const {
    data: reportsData,
    isLoading: reportsLoading,
    isError: reportsError,
  } = useQuery({
    queryKey: ["reports", { limit: 50 }],
    queryFn: () => reportsAPI.getReports({ limit: 50 }),
    staleTime: 30000,
  });

  const isLoading = analyticsLoading || reportsLoading || projectLoading;
  const hasError = analyticsError || projectError || reportsError;

  const {
    vulnSummary,
    totalVulnerabilities,
    totalScans,
    successRate,
    avgSecurityScore,
    totalProjects,
    calculatedTopProjects,
    calculatedScannerPerformance,
  } = useMemo(() => {
    const scanSum = analytics?.scan_summary || {};
    const vulnSum = analytics?.vulnerability_summary || {};
    const topProj = analytics?.top_projects || [];
    const scannerPerf = analytics?.scanner_performance || {};
    const reports = reportsData?.reports || [];
    const projAnalytics = projectAnalytics || {};

    let vulnSummary = { ...vulnSum };
    let calculatedTotalFindings = 0;

    if (reports.length > 0) {
      const aggregated = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
      reports.forEach((report) => {
        if (report.findings_by_severity) {
          aggregated.critical += report.findings_by_severity.critical || 0;
          aggregated.high += report.findings_by_severity.high || 0;
          aggregated.medium += report.findings_by_severity.medium || 0;
          aggregated.low += report.findings_by_severity.low || 0;
          aggregated.info += report.findings_by_severity.info || 0;
        }
        calculatedTotalFindings += report.total_findings || 0;
      });
      const analyticsTotal =
        (vulnSum.critical || 0) +
        (vulnSum.high || 0) +
        (vulnSum.medium || 0) +
        (vulnSum.low || 0) +
        (vulnSum.info || 0);
      const aggregatedTotal =
        aggregated.critical +
        aggregated.high +
        aggregated.medium +
        aggregated.low +
        aggregated.info;
      if (analyticsTotal === 0 && (calculatedTotalFindings > 0 || aggregatedTotal > 0)) {
        vulnSummary = aggregated;
        if (aggregatedTotal === 0 && calculatedTotalFindings > 0) {
          vulnSummary.info = calculatedTotalFindings;
        }
      }
    }

    const totalVulns =
      calculatedTotalFindings > 0
        ? calculatedTotalFindings
        : (vulnSummary.critical || 0) +
          (vulnSummary.high || 0) +
          (vulnSummary.medium || 0) +
          (vulnSummary.low || 0) +
          (vulnSummary.info || 0);

    let ctp = topProj;
    if (topProj.length === 0 && reports.length > 0) {
      const pmap = {};
      reports.forEach((report) => {
        const name = report.project_name || "Unknown";
        if (!pmap[name]) {
          pmap[name] = {
            project_name: name,
            total_findings: 0,
            scans_count: 0,
            critical_findings: 0,
            high_findings: 0,
          };
        }
        pmap[name].scans_count += 1;
        pmap[name].total_findings += report.total_findings || 0;
        pmap[name].critical_findings += report.findings_by_severity?.critical || 0;
        pmap[name].high_findings += report.findings_by_severity?.high || 0;
      });
      ctp = Object.values(pmap)
        .sort((a, b) => b.total_findings - a.total_findings)
        .slice(0, 10);
    }

    let csp = scannerPerf;
    if (Object.keys(scannerPerf).length === 0 && reports.length > 0) {
      const smap = {};
      reports.forEach((report) => {
        if (report.scan_results) {
          report.scan_results.forEach((result) => {
            const scanner = result.scanner || "unknown";
            if (!smap[scanner]) {
              smap[scanner] = {
                total_runs: 0,
                successful_runs: 0,
                total_findings: 0,
                avg_duration: 0,
                total_duration: 0,
              };
            }
            smap[scanner].total_runs += 1;
            if (result.status === "completed") {
              smap[scanner].successful_runs += 1;
              smap[scanner].total_findings += result.findings?.length || 0;
              if (result.duration_seconds) {
                smap[scanner].total_duration += result.duration_seconds;
              }
            }
          });
        }
      });
      Object.values(smap).forEach((stats) => {
        if (stats.successful_runs > 0)
          stats.avg_duration = stats.total_duration / stats.successful_runs;
      });
      csp = smap;
    }

    const avgScore = projAnalytics.average_security_score || 0;
    const totalProj = projAnalytics.total_projects || 0;
    const completed = reports.filter((r) => r.status === "completed").length;
    const total = scanSum.total_scans || reports.length || 0;
    const rate = total > 0 ? Math.round((completed / total) * 100) : scanSum.success_rate || 0;

    return {
      scanSummary: scanSum,
      vulnSummary,
      topProjects: topProj,
      scannerPerformance: scannerPerf,
      totalVulnerabilities: totalVulns,
      completedScans: completed,
      totalScans: total,
      successRate: rate,
      avgSecurityScore: avgScore,
      totalProjects: totalProj,
      calculatedTopProjects: ctp,
      calculatedScannerPerformance: csp,
    };
  }, [analytics, reportsData, projectAnalytics]);

  const stats = [
    {
      title: "Total Scans",
      value: isLoading ? "—" : totalScans.toString(),
      change: totalScans > 0 ? `${successRate}% success` : null,
      changeType: successRate >= 80 ? "positive" : successRate >= 50 ? "neutral" : "negative",
      icon: DocumentTextIcon,
      gradient: "from-blue-500 to-cyan-500",
      bgGradient: "from-blue-500/10 to-cyan-500/10",
    },
    {
      title: "Total Vulnerabilities",
      value: isLoading ? "—" : totalVulnerabilities.toString(),
      change:
        vulnSummary.critical > 0
          ? `${vulnSummary.critical} critical`
          : vulnSummary.high > 0
            ? `${vulnSummary.high} high`
            : null,
      changeType: vulnSummary.critical > 0 || vulnSummary.high > 0 ? "negative" : "positive",
      icon: ExclamationTriangleIcon,
      gradient: "from-red-500 to-pink-500",
      bgGradient: "from-red-500/10 to-pink-500/10",
    },
    {
      title: "Avg Security Score",
      value: isLoading ? "—" : `${Math.round(avgSecurityScore)}/100`,
      change:
        avgSecurityScore >= 80 ? "Healthy" : avgSecurityScore >= 50 ? "Needs Work" : "At Risk",
      changeType:
        avgSecurityScore >= 80 ? "positive" : avgSecurityScore >= 50 ? "neutral" : "negative",
      icon: ShieldCheckIcon,
      gradient: "from-green-500 to-emerald-500",
      bgGradient: "from-green-500/10 to-emerald-500/10",
    },
    {
      title: "Active Projects",
      value: isLoading ? "—" : totalProjects.toString(),
      change: projectAnalytics?.active_projects
        ? `${projectAnalytics.active_projects} active`
        : null,
      changeType: "positive",
      icon: FolderIcon,
      gradient: "from-purple-500 to-violet-500",
      bgGradient: "from-purple-500/10 to-violet-500/10",
    },
  ];

  if (hasError) {
    return (
      <PageContainer>
        <PageHeader
          title="Analytics"
          description="Failed to load analytics data"
          icon={ChartBarIcon}
          breadcrumb={["Analytics"]}
        />
        <div className="text-center py-16">
          <div className="inline-flex p-5 rounded-2xl bg-red-500/10 border border-red-500/20 mb-5">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Failed to Load Analytics</h3>
          <p className="text-gray-400 max-w-sm mx-auto mb-6">
            Unable to fetch analytics data. Please try again.
          </p>
          <button
            type="button"
            onClick={() => refetchAnalytics()}
            className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold
              hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20
              transition-all duration-200"
          >
            Try Again
          </button>
        </div>
      </PageContainer>
    );
  }

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
            aria-label="Refresh analytics data"
            className="p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 text-gray-400 hover:text-white transition-all"
          >
            <ArrowPathIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {analytics?.period && (
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
          <CalendarDaysIcon className="h-4 w-4" />
          <span>
            Showing data from {new Date(analytics.period.start_date).toLocaleDateString()} to{" "}
            {new Date(analytics.period.end_date).toLocaleDateString()}
          </span>
        </div>
      )}

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <GlassCard>
          <SectionHeader
            title="Vulnerability Severity"
            description="Distribution across severity levels"
          />
          {isLoading ? (
            <LoadingState message="Loading severity data..." />
          ) : totalVulnerabilities === 0 ? (
            <div className="py-8 text-center">
              <ExclamationTriangleIcon className="h-12 w-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No vulnerabilities found</p>
              <p className="text-gray-600 text-xs mt-1">Run a scan to see results</p>
            </div>
          ) : (
            <SeverityDistribution data={vulnSummary} />
          )}
        </GlassCard>

        <GlassCard>
          <SectionHeader title="Scanner Activity" description="Breakdown by scanner type" />
          {isLoading ? (
            <LoadingState message="Loading scan data..." />
          ) : Object.keys(calculatedScannerPerformance).length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-gray-500 text-sm">No scanner activity</p>
              <p className="text-gray-600 text-xs mt-1">Scanners will appear once scans are run</p>
            </div>
          ) : (
            <ScanTypeDistribution data={calculatedScannerPerformance} />
          )}
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
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
