import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { reportsAPI, projectsAPI } from "../services/api";

const useAnalyticsData = (daysBack) => {
  const {
    data: analytics,
    isLoading: analyticsLoading,
    isError: analyticsError,
    refetch,
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

  return useMemo(() => {
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
        if (aggregatedTotal === 0 && calculatedTotalFindings > 0)
          vulnSummary.info = calculatedTotalFindings;
      }
    }

    const totalVulnerabilities =
      calculatedTotalFindings > 0
        ? calculatedTotalFindings
        : (vulnSummary.critical || 0) +
          (vulnSummary.high || 0) +
          (vulnSummary.medium || 0) +
          (vulnSummary.low || 0) +
          (vulnSummary.info || 0);

    let topProjects = topProj;
    if (topProj.length === 0 && reports.length > 0) {
      const pmap = {};
      reports.forEach((report) => {
        const name = report.project_name || "Unknown";
        if (!pmap[name])
          pmap[name] = {
            project_name: name,
            total_findings: 0,
            scans_count: 0,
            critical_findings: 0,
            high_findings: 0,
          };
        pmap[name].scans_count += 1;
        pmap[name].total_findings += report.total_findings || 0;
        pmap[name].critical_findings += report.findings_by_severity?.critical || 0;
        pmap[name].high_findings += report.findings_by_severity?.high || 0;
      });
      topProjects = Object.values(pmap)
        .sort((a, b) => b.total_findings - a.total_findings)
        .slice(0, 10);
    }

    let scannerPerformance = scannerPerf;
    if (Object.keys(scannerPerf).length === 0 && reports.length > 0) {
      const smap = {};
      reports.forEach((report) => {
        if (report.scan_results) {
          report.scan_results.forEach((result) => {
            const scanner = result.scanner || "unknown";
            if (!smap[scanner])
              smap[scanner] = {
                total_runs: 0,
                successful_runs: 0,
                total_findings: 0,
                avg_duration: 0,
                total_duration: 0,
              };
            smap[scanner].total_runs += 1;
            if (result.status === "completed") {
              smap[scanner].successful_runs += 1;
              smap[scanner].total_findings += result.findings?.length || 0;
              if (result.duration_seconds) smap[scanner].total_duration += result.duration_seconds;
            }
          });
        }
      });
      Object.values(smap).forEach((stats) => {
        if (stats.successful_runs > 0)
          stats.avg_duration = stats.total_duration / stats.successful_runs;
      });
      scannerPerformance = smap;
    }

    const avgSecurityScore = projAnalytics.average_security_score || 0;
    const totalProjects = projAnalytics.total_projects || 0;
    const completed = reports.filter((r) => r.status === "completed").length;
    const totalScans = scanSum.total_scans || reports.length || 0;
    const successRate =
      totalScans > 0 ? Math.round((completed / totalScans) * 100) : scanSum.success_rate || 0;

    return {
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
    };
  }, [analytics, reportsData, projectAnalytics, isLoading, hasError, refetch]);
};

export default useAnalyticsData;
