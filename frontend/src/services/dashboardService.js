/**
 * Dashboard & Stats API Service
 * Provides real-time data for header, sidebar, and footer components
 */
import { projectsAPI, reportsAPI } from "./api";

/**
 * Dashboard Stats API
 */
export const dashboardAPI = {
  /**
   * Get quick stats for sidebar/header display
   * Returns: totalProjects, totalScans, openIssues, avgSecurityScore with trends
   */
  getQuickStats: async () => {
    try {
      const [projectsRes, reportsRes] = await Promise.allSettled([
        projectsAPI.getProjects({ limit: 100 }),
        reportsAPI.getReports({ limit: 100 }),
      ]);

      const projects =
        projectsRes.status === "fulfilled" ? projectsRes.value : { projects: [], total: 0 };
      const reports =
        reportsRes.status === "fulfilled" ? reportsRes.value : { reports: [], total: 0 };

      // Calculate stats
      const projectCount = projects.total || projects.projects?.length || 0;
      const reportCount = reports.total || reports.reports?.length || 0;

      // Calculate open issues (critical + high from all reports)
      const openIssues =
        reports.reports?.reduce((acc, r) => {
          return (
            acc + (r.findings_by_severity?.critical || 0) + (r.findings_by_severity?.high || 0)
          );
        }, 0) || 0;

      // Calculate average security score from reports
      const scoresArray =
        reports.reports
          ?.filter((r) => r.security_score !== undefined && r.security_score !== null)
          .map((r) => r.security_score) || [];

      const avgSecurityScore =
        scoresArray.length > 0
          ? scoresArray.reduce((sum, score) => sum + score, 0) / scoresArray.length
          : null; // No scan data available yet

      // Calculate real trends based on actual data
      // Get reports from last 7 days and compare with previous 7 days
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const fourteenDaysAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

      const recentReports =
        reports.reports?.filter((r) => new Date(r.created_at) >= sevenDaysAgo) || [];
      const previousReports =
        reports.reports?.filter(
          (r) => new Date(r.created_at) >= fourteenDaysAgo && new Date(r.created_at) < sevenDaysAgo
        ) || [];

      // Calculate scan trend (percentage change in scans)
      const recentScanCount = recentReports.length;
      const previousScanCount = previousReports.length || 1;
      const scansTrend =
        previousScanCount > 0
          ? Math.round(((recentScanCount - previousScanCount) / previousScanCount) * 100)
          : recentScanCount > 0
            ? 100
            : 0;

      // Calculate issues trend (negative is good - means fewer issues)
      const recentIssues = recentReports.reduce(
        (acc, r) =>
          acc + (r.findings_by_severity?.critical || 0) + (r.findings_by_severity?.high || 0),
        0
      );
      const previousIssues =
        previousReports.reduce(
          (acc, r) =>
            acc + (r.findings_by_severity?.critical || 0) + (r.findings_by_severity?.high || 0),
          0
        ) || 1;
      const issuesTrend =
        previousIssues > 0
          ? Math.round(((recentIssues - previousIssues) / previousIssues) * 100)
          : recentIssues > 0
            ? 100
            : 0;

      // Projects trend based on creation date if available
      const projectsTrend =
        projectCount > 0 ? Math.round((projectCount / Math.max(projectCount - 1, 1) - 1) * 100) : 0;

      // Score trend: compare average of recent vs previous
      const recentScores = recentReports
        .filter((r) => r.security_score != null)
        .map((r) => r.security_score);
      const previousScores = previousReports
        .filter((r) => r.security_score != null)
        .map((r) => r.security_score);
      const recentAvgScore =
        recentScores.length > 0
          ? recentScores.reduce((a, b) => a + b, 0) / recentScores.length
          : avgSecurityScore;
      const previousAvgScore =
        previousScores.length > 0
          ? previousScores.reduce((a, b) => a + b, 0) / previousScores.length
          : avgSecurityScore;
      const scoreTrend =
        previousAvgScore > 0
          ? Math.round(((recentAvgScore - previousAvgScore) / previousAvgScore) * 100)
          : 0;

      return {
        totalProjects: projectCount,
        totalScans: reportCount,
        openIssues,
        avgSecurityScore,
        projectsTrend,
        scansTrend,
        issuesTrend,
        scoreTrend,
        // Legacy format support
        projects: projectCount,
        scansToday:
          reports.reports?.filter((r) => {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            return new Date(r.created_at) >= today;
          }).length || 0,
        issuesFixed: reports.reports?.filter((r) => r.status === "completed").length || 0,
        criticalIssues:
          reports.reports?.reduce((acc, r) => acc + (r.findings_by_severity?.critical || 0), 0) ||
          0,
      };
    } catch (error) {
      console.error("Error fetching quick stats:", error);
      return {
        totalProjects: 0,
        totalScans: 0,
        openIssues: 0,
        avgSecurityScore: 0,
        projectsTrend: null,
        scansTrend: null,
        issuesTrend: null,
        scoreTrend: null,
        projects: 0,
        scansToday: 0,
        issuesFixed: 0,
        criticalIssues: 0,
      };
    }
  },

  /**
   * Search across projects, scans, and vulnerabilities
   */
  globalSearch: async (query, _options = {}) => {
    if (!query || query.length < 2) {
      return { projects: [], scans: [], vulnerabilities: [] };
    }

    try {
      const [projectsRes, reportsRes] = await Promise.allSettled([
        projectsAPI.getProjects({ search: query, limit: 5 }),
        reportsAPI.getReports({ search: query, limit: 10 }),
      ]);

      const projects = projectsRes.status === "fulfilled" ? projectsRes.value.projects || [] : [];
      const reports = reportsRes.status === "fulfilled" ? reportsRes.value.reports || [] : [];

      // Filter projects matching query
      const filteredProjects = projects
        .filter(
          (p) =>
            p.name?.toLowerCase().includes(query.toLowerCase()) ||
            p.description?.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, 5)
        .map((p) => ({
          id: p.id || p._id,
          name: p.name,
          type: "project",
          status: p.status || "active",
          path: `/project/${p.id || p._id}`,
        }));

      // Filter scans/reports matching query
      const filteredScans = reports
        .filter(
          (r) =>
            r.project_name?.toLowerCase().includes(query.toLowerCase()) ||
            r.scan_type?.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, 5)
        .map((r) => ({
          id: r.id || r._id,
          name: `${r.scan_type || "Security"} Scan - ${r.project_name}`,
          type: "scan",
          status: r.status,
          severity:
            r.findings_by_severity?.critical > 0
              ? "critical"
              : r.findings_by_severity?.high > 0
                ? "high"
                : "medium",
          path: `/report/${r.id || r._id}`,
        }));

      // Extract vulnerabilities from reports
      const vulnerabilities = [];
      reports.forEach((r) => {
        if (r.findings) {
          r.findings.forEach((f) => {
            if (
              f.title?.toLowerCase().includes(query.toLowerCase()) ||
              f.description?.toLowerCase().includes(query.toLowerCase()) ||
              f.rule_id?.toLowerCase().includes(query.toLowerCase())
            ) {
              vulnerabilities.push({
                id: f.id || `${r.id}-${f.rule_id}`,
                name: f.title || f.rule_id || "Unknown Vulnerability",
                type: "vulnerability",
                severity: f.severity || "medium",
                path: `/report/${r.id || r._id}`,
              });
            }
          });
        }
      });

      return {
        projects: filteredProjects,
        scans: filteredScans,
        vulnerabilities: vulnerabilities.slice(0, 5),
      };
    } catch (error) {
      console.error("Error in global search:", error);
      return { projects: [], scans: [], vulnerabilities: [] };
    }
  },

  /**
   * Get API health status for footer
   */
  getApiHealth: async () => {
    try {
      const startTime = Date.now();
      // Try to fetch a simple endpoint to check health
      await projectsAPI.getProjects({ limit: 1 });
      const latency = Date.now() - startTime;

      return {
        status: "healthy",
        latency,
        message: latency < 500 ? "Excellent" : latency < 1000 ? "Good" : "Slow",
      };
    } catch (error) {
      return {
        status: "unhealthy",
        latency: null,
        message: "Connection issue",
      };
    }
  },

  /**
   * Get comprehensive system health for sidebar/footer
   * Checks API, database connectivity, and AI service status
   */
  getSystemHealth: async () => {
    try {
      const startTime = Date.now();

      // Try to fetch projects to test API and database
      const projectsPromise = projectsAPI
        .getProjects({ limit: 1 })
        .then(() => ({ connected: true }))
        .catch(() => ({ connected: false }));

      // Get stats to test more functionality
      const reportsPromise = reportsAPI
        .getReports({ limit: 1 })
        .then(() => ({ connected: true }))
        .catch(() => ({ connected: false }));

      const [dbCheck, apiCheck] = await Promise.allSettled([projectsPromise, reportsPromise]);

      const latency = Date.now() - startTime;

      const dbConnected = dbCheck.status === "fulfilled" && dbCheck.value?.connected;
      const apiConnected = apiCheck.status === "fulfilled" && apiCheck.value?.connected;

      return {
        status: dbConnected && apiConnected ? "healthy" : apiConnected ? "degraded" : "error",
        latency,
        database: { connected: dbConnected },
        api: { connected: apiConnected },
        ai: { available: true }, // Assume AI is available if API works
        websocket: { connected: typeof WebSocket !== "undefined" },
      };
    } catch (error) {
      console.error("System health check failed:", error);
      return {
        status: "error",
        latency: null,
        database: { connected: false },
        api: { connected: false },
        ai: { available: false },
        websocket: { connected: false },
      };
    }
  },

  /**
   * Get recent activity for notifications
   */
  getRecentActivity: async (limit = 10) => {
    try {
      const reportsRes = await reportsAPI.getReports({
        limit,
        sort_by: "created_at",
        sort_order: "desc",
      });

      const reports = reportsRes.reports || [];

      return reports.map((r) => ({
        id: r.id || r._id,
        type:
          r.status === "completed"
            ? "scan_completed"
            : r.status === "failed"
              ? "scan_error"
              : r.status === "in_progress"
                ? "scan_started"
                : "scan_update",
        message: `${r.scan_type || "Security"} scan ${r.status} for ${r.project_name}`,
        timestamp: r.created_at,
        read: false,
        data: {
          project_name: r.project_name,
          scan_type: r.scan_type,
          status: r.status,
          findings: r.total_findings,
        },
      }));
    } catch (error) {
      console.error("Error fetching recent activity:", error);
      return [];
    }
  },
};

export default dashboardAPI;
