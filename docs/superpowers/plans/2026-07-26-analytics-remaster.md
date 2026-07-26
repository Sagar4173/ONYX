# Analytics Page Remaster — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster the Analytics page with ParticleBackground, framer-motion staggered animations, Canvas mini donut charts, animated severity bars, glassmorphism elevation, and extracted data hook.

**Architecture:** Single-page orchestrator (`Analytics.jsx`) + 6 sub-components + 1 custom hook. Data aggregation extracted from inline `useMemo` into `useAnalyticsData`. ParticleBackground as ambient backdrop. MetricCard reused from projects for stat row.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, Canvas API, @tanstack/react-query

## Global Constraints
- Zero new npm dependencies
- All visualizations use Canvas, SVG, CSS, or framer-motion only
- ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- `npx eslint src/` must pass with 0 errors, 0 warnings

---

### File Structure

```
frontend/src/
├── hooks/
│   └── useAnalyticsData.js          (NEW — extract data aggregation)
└── components/analytics/
    ├── SeverityDistribution.jsx      (ENHANCE — animated bars, glassmorphism)
    ├── ScanTypeDistribution.jsx      (ENHANCE — Canvas donut charts, stagger)
    ├── RecentScansTimeline.jsx       (ENHANCE — framer-motion slide-in, timeline dots)
    ├── TopProjects.jsx               (ENHANCE — stagger, rank badges, mini severity bars)
    ├── ScannerPerformance.jsx        (ENHANCE — mini success bars, stagger)
    ├── TimePeriodSelector.jsx        (ENHANCE — glassmorphism polish)
    └── pages/
        └── Analytics.jsx             (REWRITE — ParticleBackground, hook, MetricCard, staggering)
```

---

### Task 1: useAnalyticsData — Custom Hook

**Files:**
- Create: `frontend/src/hooks/useAnalyticsData.js`

**Interfaces:**
- Produces: `useAnalyticsData(daysBack)` → `{ vulnSummary, totalVulnerabilities, totalScans, successRate, avgSecurityScore, totalProjects, topProjects, scannerPerformance, isLoading, hasError, refetch }`

- [ ] **Step 1: Create useAnalyticsData.js**

```js
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { reportsAPI, projectsAPI } from "../services/api";

const useAnalyticsData = (daysBack) => {
  const { data: analytics, isLoading: analyticsLoading, isError: analyticsError, refetch } = useQuery({
    queryKey: ["analytics", daysBack],
    queryFn: () => reportsAPI.getAnalyticsOverview(daysBack),
    staleTime: 30000,
  });

  const { data: projectAnalytics, isLoading: projectLoading, isError: projectError } = useQuery({
    queryKey: ["projectAnalytics"],
    queryFn: () => projectsAPI.getAnalyticsOverview(),
    staleTime: 30000,
  });

  const { data: reportsData, isLoading: reportsLoading, isError: reportsError } = useQuery({
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
      const analyticsTotal = (vulnSum.critical || 0) + (vulnSum.high || 0) + (vulnSum.medium || 0) + (vulnSum.low || 0) + (vulnSum.info || 0);
      const aggregatedTotal = aggregated.critical + aggregated.high + aggregated.medium + aggregated.low + aggregated.info;
      if (analyticsTotal === 0 && (calculatedTotalFindings > 0 || aggregatedTotal > 0)) {
        vulnSummary = aggregated;
        if (aggregatedTotal === 0 && calculatedTotalFindings > 0) vulnSummary.info = calculatedTotalFindings;
      }
    }

    const totalVulnerabilities = calculatedTotalFindings > 0
      ? calculatedTotalFindings
      : (vulnSummary.critical || 0) + (vulnSummary.high || 0) + (vulnSummary.medium || 0) + (vulnSummary.low || 0) + (vulnSummary.info || 0);

    let topProjects = topProj;
    if (topProj.length === 0 && reports.length > 0) {
      const pmap = {};
      reports.forEach((report) => {
        const name = report.project_name || "Unknown";
        if (!pmap[name]) pmap[name] = { project_name: name, total_findings: 0, scans_count: 0, critical_findings: 0, high_findings: 0 };
        pmap[name].scans_count += 1;
        pmap[name].total_findings += report.total_findings || 0;
        pmap[name].critical_findings += report.findings_by_severity?.critical || 0;
        pmap[name].high_findings += report.findings_by_severity?.high || 0;
      });
      topProjects = Object.values(pmap).sort((a, b) => b.total_findings - a.total_findings).slice(0, 10);
    }

    let scannerPerformance = scannerPerf;
    if (Object.keys(scannerPerf).length === 0 && reports.length > 0) {
      const smap = {};
      reports.forEach((report) => {
        if (report.scan_results) {
          report.scan_results.forEach((result) => {
            const scanner = result.scanner || "unknown";
            if (!smap[scanner]) smap[scanner] = { total_runs: 0, successful_runs: 0, total_findings: 0, avg_duration: 0, total_duration: 0 };
            smap[scanner].total_runs += 1;
            if (result.status === "completed") {
              smap[scanner].successful_runs += 1;
              smap[scanner].total_findings += result.findings?.length || 0;
              if (result.duration_seconds) smap[scanner].total_duration += result.duration_seconds;
            }
          });
        }
      });
      Object.values(smap).forEach((stats) => { if (stats.successful_runs > 0) stats.avg_duration = stats.total_duration / stats.successful_runs; });
      scannerPerformance = smap;
    }

    const avgSecurityScore = projAnalytics.average_security_score || 0;
    const totalProjects = projAnalytics.total_projects || 0;
    const completed = reports.filter((r) => r.status === "completed").length;
    const totalScans = scanSum.total_scans || reports.length || 0;
    const successRate = totalScans > 0 ? Math.round((completed / totalScans) * 100) : scanSum.success_rate || 0;

    return { vulnSummary, totalVulnerabilities, totalScans, successRate, avgSecurityScore, totalProjects, topProjects, scannerPerformance, analytics, reports, isLoading, hasError, refetch };
  }, [analytics, reportsData, projectAnalytics, isLoading, hasError, refetch]);
};

export default useAnalyticsData;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/hooks/useAnalyticsData.js`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useAnalyticsData.js
git commit -m "feat: Task 1 — create useAnalyticsData hook"
```

---

### Task 2: SeverityDistribution — Animated Bars

**Files:**
- Rewrite: `frontend/src/components/analytics/SeverityDistribution.jsx`

**Interfaces:**
- Consumes: `{ data }` — same prop shape as before
- Produces: animated severity bars with glassmorphism container

- [ ] **Step 1: Rewrite SeverityDistribution.jsx**

```jsx
import { motion } from "framer-motion";

const severities = [
  { key: "critical", label: "Critical", bar: "bg-gradient-to-r from-red-500 to-red-400", text: "text-red-400", dot: "bg-red-500" },
  { key: "high", label: "High", bar: "bg-gradient-to-r from-orange-500 to-orange-400", text: "text-orange-400", dot: "bg-orange-500" },
  { key: "medium", label: "Medium", bar: "bg-gradient-to-r from-yellow-500 to-yellow-400", text: "text-yellow-400", dot: "bg-yellow-500" },
  { key: "low", label: "Low", bar: "bg-gradient-to-r from-cyan-500 to-cyan-400", text: "text-cyan-400", dot: "bg-cyan-500" },
  { key: "info", label: "Info", bar: "bg-gradient-to-r from-gray-500 to-gray-400", text: "text-gray-400", dot: "bg-gray-500" },
];

const SeverityDistribution = ({ data }) => {
  const total = severities.reduce((sum, s) => sum + (data?.[s.key] || 0), 0) || 1;

  return (
    <div className="space-y-4">
      {severities.map((severity) => {
        const count = data?.[severity.key] || 0;
        const pct = Math.round((count / total) * 100);
        return (
          <div key={severity.key}>
            <div className="flex items-center justify-between mb-2">
              <span className={`flex items-center gap-2 text-sm font-medium ${severity.text}`}>
                <span className={`w-2 h-2 rounded-full ${severity.dot}`} />
                {severity.label}
              </span>
              <span className="text-sm text-gray-400">
                {count} ({pct}%)
              </span>
            </div>
            <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${severity.bar} rounded-full`}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SeverityDistribution;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/analytics/SeverityDistribution.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analytics/SeverityDistribution.jsx
git commit -m "feat: Task 2 — SeverityDistribution with animated bars"
```

---

### Task 3: ScanTypeDistribution — Canvas Donut Charts

**Files:**
- Rewrite: `frontend/src/components/analytics/ScanTypeDistribution.jsx`

**Interfaces:**
- Consumes: `{ data }` — same prop shape (scanner performance object)
- Produces: 2×2 grid with Canvas mini donut, stagger, hover-lift

- [ ] **Step 1: Write ScanTypeDistribution.jsx**

```jsx
import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { CodeBracketIcon, EyeIcon, CubeIcon, ServerIcon } from "@heroicons/react/24/outline";

const scanTypes = [
  { key: "sast", label: "Static Analysis", icon: CodeBracketIcon, color: "#06b6d4", gradient: "from-blue-500 to-cyan-500" },
  { key: "secrets", label: "Secret Detection", icon: EyeIcon, color: "#a855f7", gradient: "from-purple-500 to-pink-500" },
  { key: "container", label: "Container Scan", icon: CubeIcon, color: "#10b981", gradient: "from-green-500 to-emerald-500" },
  { key: "infrastructure", label: "Infrastructure", icon: ServerIcon, color: "#f97316", gradient: "from-orange-500 to-red-500" },
];

const getCount = (data, key) => {
  if (!data) return 0;
  if (typeof data[key] === "number") return data[key];
  if (data[key]?.total_runs) return data[key].total_runs;
  const map = { sast: ["semgrep", "bandit", "eslint"], secrets: ["gitleaks", "trufflehog"], container: ["trivy", "grype"], infrastructure: ["checkov", "tfsec"] };
  return (map[key] || []).reduce((a, s) => a + (data[s]?.total_runs || 0), 0);
};

const getTotal = (data) => {
  if (!data) return 0;
  return scanTypes.reduce((a, t) => a + getCount(data, t.key), 0);
};

const Donut = ({ value, total, color }) => {
  const ref = useRef();
  useEffect(() => {
    const cvs = ref.current;
    if (!cvs) return;
    const ctx = cvs.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const s = 75;
    cvs.width = s * dpr;
    cvs.height = s * dpr;
    cvs.style.width = `${s}px`;
    cvs.style.height = `${s}px`;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, s, s);
    const cx = s / 2, cy = s / 2, r = 28, lw = 5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    ctx.lineWidth = lw;
    ctx.stroke();
    if (total > 0 && value > 0) {
      const pct = value / total;
      ctx.beginPath();
      ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * pct);
      ctx.strokeStyle = color;
      ctx.lineWidth = lw;
      ctx.lineCap = "round";
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.font = `600 ${Math.round(12 * (dpr))}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`${Math.round(pct * 100)}%`, cx, cy);
    }
  }, [value, total, color]);
  return <canvas ref={ref} className="flex-shrink-0" />;
};

const ScanTypeDistribution = ({ data }) => {
  const total = getTotal(data);
  return (
    <motion.div className="grid grid-cols-2 gap-4" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.08 } } }}>
      {scanTypes.map((type) => {
        const count = getCount(data, type.key);
        return (
          <motion.div key={type.key} variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } }}
            className="p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 hover:-translate-y-1 hover:shadow-xl transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`inline-flex p-2.5 rounded-xl bg-gradient-to-r ${type.gradient}`}>
                <type.icon className="h-5 w-5 text-white" />
              </div>
              {total > 0 && <Donut value={count} total={total} color={type.color} />}
            </div>
            <p className="text-2xl font-bold text-white">{count}</p>
            <p className="text-sm text-gray-400">{type.label}</p>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default ScanTypeDistribution;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/analytics/ScanTypeDistribution.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analytics/ScanTypeDistribution.jsx
git commit -m "feat: Task 3 — ScanTypeDistribution with Canvas donuts and stagger"
```

---

### Task 4: RecentScansTimeline — Slide-In Stagger

**Files:**
- Rewrite: `frontend/src/components/analytics/RecentScansTimeline.jsx`

**Interfaces:**
- Consumes: `{ scans }` — same prop shape
- Produces: timeline with framer-motion slide-in, timeline dots

- [ ] **Step 1: Write RecentScansTimeline.jsx**

```jsx
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon, ClockIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const statusConfig = {
  completed: { icon: CheckCircleIcon, bg: "bg-green-500/20", color: "text-green-400" },
  failed: { icon: XCircleIcon, bg: "bg-red-500/20", color: "text-red-400" },
  pending: { icon: ArrowPathIcon, bg: "bg-cyan-500/20", color: "text-cyan-400" },
};

const RecentScansTimeline = ({ scans = [] }) => {
  if (scans.length === 0) {
    return <EmptyState icon={ClockIcon} title="No Recent Scans" description="Start a security scan to see activity here" />;
  }

  return (
    <motion.div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}>
      {scans.map((scan) => {
        const cfg = statusConfig[scan.status] || statusConfig.pending;
        const Icon = cfg.icon;
        return (
          <motion.div key={scan.id} variants={{ hidden: { opacity: 0, x: -20 }, show: { opacity: 1, x: 0 } }}>
            <Link to={`/report/${scan.id}`}
              className="flex items-start space-x-4 p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 hover:bg-gray-800/60 transition-all group"
            >
              <div className="relative flex items-start pt-1">
                <div className={`p-2 rounded-lg ${cfg.bg}`}>
                  <Icon className={`h-5 w-5 ${cfg.color}`} />
                </div>
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-px h-full bg-gray-700/30 -z-10" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate group-hover:text-cyan-400 transition-colors">
                  {scan.project_name || scan.repository_url || "Unknown Project"}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color}`}>{scan.status}</span>
                  <span className="text-xs text-gray-500">{scan.total_findings || scan.findings_count || 0} findings</span>
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <span className="text-xs text-gray-500">{new Date(scan.created_at).toLocaleDateString()}</span>
                <p className="text-xs text-gray-600 mt-1">{new Date(scan.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</p>
              </div>
            </Link>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default RecentScansTimeline;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/analytics/RecentScansTimeline.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analytics/RecentScansTimeline.jsx
git commit -m "feat: Task 4 — RecentScansTimeline with slide-in stagger"
```

---

### Task 5: TopProjects — Stagger, Rank Badges, Mini Severity Bars

**Files:**
- Rewrite: `frontend/src/components/analytics/TopProjects.jsx`

**Interfaces:**
- Consumes: `{ projects }` — same prop shape
- Produces: ranked list with stagger, animated rank badges, inline mini severity bars

- [ ] **Step 1: Write TopProjects.jsx**

```jsx
import { motion } from "framer-motion";
import { FolderIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const rankGradients = [
  "from-yellow-400 to-yellow-600",
  "from-gray-300 to-gray-500",
  "from-amber-600 to-amber-800",
];

const TopProjects = ({ projects = [] }) => {
  if (!projects || projects.length === 0) {
    return <EmptyState icon={FolderIcon} title="No Project Data" description="Scan some projects to see analytics" />;
  }

  return (
    <motion.div className="space-y-3" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.05 } } }}>
      {projects.slice(0, 5).map((project, index) => {
        const totalCritHigh = (project.critical_findings || 0) + (project.high_findings || 0);
        const totalMed = project.medium_findings || 0;
        const totalLow = project.low_findings || 0;
        const total = totalCritHigh + totalMed + totalLow || 1;
        return (
          <motion.div key={project.project_name} variants={{ hidden: { opacity: 0, x: -15 }, show: { opacity: 1, x: 0 } }}
            className="flex items-center justify-between p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 hover:bg-gray-800/60 transition-all"
          >
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <div className={`flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r ${rankGradients[index] || "from-cyan-500 to-violet-500"} flex items-center justify-center text-white font-bold text-sm`}>
                {index + 1}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{project.project_name}</p>
                <p className="text-xs text-gray-500">{project.scans_count} scans</p>
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-4">
              <div className="flex items-center gap-2 justify-end">
                {project.critical_findings > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400">{project.critical_findings} critical</span>
                )}
                {project.high_findings > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-xs bg-orange-500/20 text-orange-400">{project.high_findings} high</span>
                )}
              </div>
              <div className="mt-1.5 h-1.5 bg-gray-700/50 rounded-full overflow-hidden flex max-w-[120px] ml-auto">
                <motion.div className="h-full bg-red-500 rounded-full" initial={{ width: 0 }} animate={{ width: `${(totalCritHigh / total) * 100}%` }} transition={{ duration: 0.6, delay: 0.2 }} />
                <motion.div className="h-full bg-yellow-500" initial={{ width: 0 }} animate={{ width: `${(totalMed / total) * 100}%` }} transition={{ duration: 0.6, delay: 0.3 }} />
                <motion.div className="h-full bg-cyan-500" initial={{ width: 0 }} animate={{ width: `${(totalLow / total) * 100}%` }} transition={{ duration: 0.6, delay: 0.4 }} />
              </div>
              <p className="text-xs text-gray-500 mt-1">{project.total_findings} total findings</p>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default TopProjects;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/analytics/TopProjects.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analytics/TopProjects.jsx
git commit -m "feat: Task 5 — TopProjects with stagger, rank badges, mini severity bars"
```

---

### Task 6: ScannerPerformance — Mini Success Bars

**Files:**
- Rewrite: `frontend/src/components/analytics/ScannerPerformance.jsx`

**Interfaces:**
- Consumes: `{ scanners }` — same prop shape
- Produces: scanner list with mini success bars, stagger

- [ ] **Step 1: Write ScannerPerformance.jsx**

```jsx
import { motion } from "framer-motion";
import { CpuChipIcon, ClockIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return "N/A";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
};

const ScannerPerformance = ({ scanners = {} }) => {
  const scannerList = Object.entries(scanners).map(([name, stats]) => ({ name, ...stats }));

  if (scannerList.length === 0) {
    return <EmptyState icon={CpuChipIcon} title="No Scanner Data" description="Run scans to see scanner performance" />;
  }

  return (
    <motion.div className="space-y-3" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}>
      {scannerList.slice(0, 6).map((scanner) => {
        const successRate = scanner.total_runs > 0 ? Math.round((scanner.successful_runs / scanner.total_runs) * 100) : 0;
        return (
          <motion.div key={scanner.name} variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
            className="p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white capitalize flex items-center gap-2">
                <CpuChipIcon className="h-4 w-4 text-cyan-400" /> {scanner.name}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                successRate >= 90 ? "bg-green-500/20 text-green-400" : successRate >= 70 ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-400"
              }`}>
                {successRate}% success
              </span>
            </div>
            <div className="h-1.5 bg-gray-700/50 rounded-full overflow-hidden mb-2">
              <motion.div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full"
                initial={{ width: 0 }} animate={{ width: `${successRate}%` }} transition={{ duration: 0.6, ease: "easeOut" }} />
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
              <div><span className="text-gray-500">Runs:</span> {scanner.total_runs}</div>
              <div><span className="text-gray-500">Findings:</span> {scanner.total_findings}</div>
              <div className="flex items-center gap-1"><ClockIcon className="h-3 w-3 text-gray-500" /> {formatDuration(scanner.avg_duration)}</div>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default ScannerPerformance;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/analytics/ScannerPerformance.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analytics/ScannerPerformance.jsx
git commit -m "feat: Task 6 — ScannerPerformance with mini success bars and stagger"
```

---

### Task 7: TimePeriodSelector — Glassmorphism Polish

**Files:**
- Rewrite: `frontend/src/components/analytics/TimePeriodSelector.jsx`

**Interfaces:**
- Consumes: `{ value, onChange }` — same prop shape
- Produces: glassmorphism pill group with gradient active

- [ ] **Step 1: Write TimePeriodSelector.jsx**

```jsx
import { motion } from "framer-motion";

const periods = [
  { value: 7, label: "7 Days" },
  { value: 30, label: "30 Days" },
  { value: 90, label: "90 Days" },
];

const TimePeriodSelector = ({ value, onChange }) => (
  <div className="flex items-center gap-1 bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-lg p-1">
    {periods.map((period) => (
      <button
        key={period.value}
        onClick={() => onChange(period.value)}
        className={`relative px-3 py-1.5 rounded-md text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
          value === period.value ? "text-white" : "text-gray-400 hover:text-white"
        }`}
      >
        {value === period.value && (
          <motion.div layoutId="period-indicator" className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-md" initial={false} transition={{ type: "spring", stiffness: 400, damping: 30 }} />
        )}
        <span className="relative z-10">{period.label}</span>
      </button>
    ))}
  </div>
);

export default TimePeriodSelector;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/analytics/TimePeriodSelector.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analytics/TimePeriodSelector.jsx
git commit -m "feat: Task 7 — TimePeriodSelector with glassmorphism and animated indicator"
```

---

### Task 8: Analytics.jsx — Full Orchestrator Rewrite

**Files:**
- Rewrite: `frontend/src/pages/Analytics.jsx`

**Interfaces:**
- Produces: fully remastered Analytics page
- Consumes: all sub-components (unchanged interfaces) + useAnalyticsData hook + MetricCard

- [ ] **Step 1: Rewrite Analytics.jsx**

```jsx
import { useState } from "react";
import { motion } from "framer-motion";
import { ChartBarIcon, ShieldCheckIcon, ExclamationTriangleIcon, DocumentTextIcon, FolderIcon, CalendarDaysIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { PageContainer, PageHeader, GlassCard, SectionHeader, ErrorState } from "../layouts";
import ParticleBackground from "../components/projects/ParticleBackground";
import MetricCard from "../components/projects/MetricCard";
import useAnalyticsData from "../hooks/useAnalyticsData";
import SeverityDistribution from "../components/analytics/SeverityDistribution";
import ScanTypeDistribution from "../components/analytics/ScanTypeDistribution";
import RecentScansTimeline from "../components/analytics/RecentScansTimeline";
import TopProjects from "../components/analytics/TopProjects";
import ScannerPerformance from "../components/analytics/ScannerPerformance";
import TimePeriodSelector from "../components/analytics/TimePeriodSelector";

const containerAnim = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const itemAnim = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } };

const cardColors = {
  scans: "#06b6d4",
  vulns: "#ef4444",
  score: "#10b981",
  projects: "#8b5cf6",
};

const Analytics = () => {
  const [daysBack, setDaysBack] = useState(30);
  const { vulnSummary, totalVulnerabilities, totalScans, successRate, avgSecurityScore, totalProjects, topProjects, scannerPerformance, analytics, reports, isLoading, hasError, refetch } = useAnalyticsData(daysBack);

  if (hasError) {
    return (
      <ErrorState
        title="Failed to Load Analytics"
        message="Unable to fetch analytics data. Please try again."
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <PageHeader title="Analytics" description="Security insights, vulnerability trends, and scan metrics" icon={ChartBarIcon} breadcrumb={["Analytics"]} />
            <div className="flex items-center gap-3">
              <TimePeriodSelector value={daysBack} onChange={setDaysBack} />
              <button onClick={() => refetch()} aria-label="Refresh analytics data"
                className="p-2 rounded-lg bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 text-gray-400 hover:text-white transition-all hover:bg-gray-700/50">
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {analytics?.period && (
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-6 bg-gray-800/20 backdrop-blur-sm border border-gray-700/30 rounded-lg px-4 py-2">
              <CalendarDaysIcon className="h-4 w-4" />
              <span>Showing data from {new Date(analytics.period.start_date).toLocaleDateString()} to {new Date(analytics.period.end_date).toLocaleDateString()}</span>
            </div>
          )}

          <motion.div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8" variants={containerAnim} initial="hidden" animate="show">
            <motion.div variants={itemAnim}>
              <MetricCard icon={DocumentTextIcon} label="Total Scans" value={isLoading ? 0 : totalScans} color={cardColors.scans} />
            </motion.div>
            <motion.div variants={itemAnim}>
              <MetricCard icon={ExclamationTriangleIcon} label="Total Vulnerabilities" value={isLoading ? 0 : totalVulnerabilities} color={cardColors.vulns} />
            </motion.div>
            <motion.div variants={itemAnim}>
              <MetricCard icon={ShieldCheckIcon} label="Avg Security Score" value={isLoading ? 0 : Math.round(avgSecurityScore)} color={cardColors.score} formatter={(v) => `${v}/100`} />
            </motion.div>
            <motion.div variants={itemAnim}>
              <MetricCard icon={FolderIcon} label="Active Projects" value={isLoading ? 0 : totalProjects} color={cardColors.projects} />
            </motion.div>
          </motion.div>

          <motion.div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8" variants={containerAnim} initial="hidden" animate="show">
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader title="Vulnerability Severity" description="Distribution across severity levels" />
                {isLoading ? (
                  <div className="h-[200px] bg-gray-800/30 rounded-xl animate-pulse" />
                ) : (
                  <SeverityDistribution data={vulnSummary} />
                )}
              </GlassCard>
            </motion.div>
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader title="Scanner Activity" description="Breakdown by scanner type" />
                {isLoading ? (
                  <div className="h-[200px] bg-gray-800/30 rounded-xl animate-pulse" />
                ) : (
                  <ScanTypeDistribution data={scannerPerformance} />
                )}
              </GlassCard>
            </motion.div>
          </motion.div>

          <motion.div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8" variants={containerAnim} initial="hidden" animate="show">
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader title="Top Projects by Findings" description="Projects with the most security findings" />
                {isLoading ? (
                  <div className="space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-gray-800/30 rounded-xl animate-pulse" />)}</div>
                ) : (
                  <TopProjects projects={topProjects} />
                )}
              </GlassCard>
            </motion.div>
            <motion.div variants={itemAnim}>
              <GlassCard>
                <SectionHeader title="Scanner Performance" description="Success rates and average durations" />
                {isLoading ? (
                  <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-800/30 rounded-xl animate-pulse" />)}</div>
                ) : (
                  <ScannerPerformance scanners={scannerPerformance} />
                )}
              </GlassCard>
            </motion.div>
          </motion.div>

          <motion.div variants={itemAnim} initial="hidden" animate="show">
            <GlassCard>
              <SectionHeader title="Recent Scan Activity" description="Latest security scans and their results" />
              <RecentScansTimeline scans={reports || []} />
            </GlassCard>
          </motion.div>
        </div>
      </PageContainer>
    </div>
  );
};

export default Analytics;
```

- [ ] **Step 2: Full lint**

Run: `npx eslint src/`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: Task 8 — Analytics orchestrator with particles, MetricCard, stagger, hook integration"
```

---

### Verification After All Tasks

- [ ] **Final lint**

Run: `npx eslint src/`
Expected: 0 errors, 0 warnings

- [ ] **Final status**

```bash
git status
git log --oneline -6
```
