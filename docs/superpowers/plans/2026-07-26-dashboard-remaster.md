# Dashboard Remaster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster the landing `/dashboard` page into a security command center with hero section, animated metric cards, Canvas trend chart, enhanced quick actions, animated scan list, and live activity feed.

**Architecture:** Page-level orchestrator (`Dashboard.jsx`) composes new and enhanced sub-components from `components/dashboard/`. Reuses `ParticleBackground`, `SecurityScoreGlobe`, and `MetricCard` from `components/projects/`.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, Canvas API, react-router-dom, @tanstack/react-query

## Global Constraints
- Zero new npm dependencies — Canvas API and framer-motion already available
- Follow ONYX design language: cyan-400/violet-500/cyan-400 gradients, glassmorphism (`backdrop-blur-sm`/`backdrop-blur-xl`), dark theme (gray-900 through gray-950), Inter font
- All new components go in `frontend/src/components/dashboard/`
- Reuse existing components from `components/projects/` where possible
- Lint: `npx eslint src/` must pass with 0 errors, 0 warnings

---
### File Structure

```
frontend/src/components/dashboard/
├── DashboardHero.jsx       (NEW)
├── ScoreTrendChart.jsx     (NEW)
├── QuickActions.jsx        (MODIFY — visual upgrade)
├── RecentScans.jsx         (MODIFY — visual upgrade)
├── DashboardStatsBar.jsx   (DELETE)
├── SecurityScoreChart.jsx  (DELETE — replaced by ScoreTrendChart)

frontend/src/pages/
└── Dashboard.jsx           (MODIFY — orchestrator)
```

---
### Task 1: DashboardHero.jsx

**Files:**
- Create: `frontend/src/components/dashboard/DashboardHero.jsx`

**Interfaces:**
- Consumes: `securityScore` (number | null), `scoreTrend` (number | null — percentage change)
- Produces: rendered hero section with SecurityScoreGlobe + animated score

- [ ] **Step 1: Create DashboardHero.jsx**

```jsx
import SecurityScoreGlobe from "../projects/SecurityScoreGlobe";
import { AnimatedCounter } from "../../styles/components";

const DashboardHero = ({ securityScore, scoreTrend }) => {
  const trendColor = scoreTrend > 0 ? "text-emerald-400" : scoreTrend < 0 ? "text-red-400" : "text-gray-400";
  const trendArrow = scoreTrend > 0 ? "↑" : scoreTrend < 0 ? "↓" : "→";

  return (
    <div className="bg-gray-800/40 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 mb-6">
      <div className="flex items-center gap-8">
        <div className="flex-shrink-0">
          <SecurityScoreGlobe score={securityScore || 0} isScanActive={false} />
        </div>
        <div className="flex-1">
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1 font-medium">Organization Security Posture</p>
          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-bold text-white">
              {securityScore != null ? <AnimatedCounter value={securityScore} /> : "—"}
            </span>
            {scoreTrend != null && securityScore != null && (
              <span className={`text-lg font-medium ${trendColor}`}>
                {trendArrow} {Math.abs(scoreTrend)}%
              </span>
            )}
          </div>
          <p className="text-gray-500 text-xs mt-1">Last updated: {new Date().toLocaleTimeString()}</p>
        </div>
      </div>
    </div>
  );
};

export default DashboardHero;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/dashboard/DashboardHero.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/DashboardHero.jsx
git commit -m "feat: Task 1 — DashboardHero with globe + animated score"
```

---
### Task 2: ScoreTrendChart.jsx

**Files:**
- Create: `frontend/src/components/dashboard/ScoreTrendChart.jsx`

**Interfaces:**
- Consumes: `reports` (array — each has `security_score` and `created_at`)
- Produces: Canvas-based line chart rendered in a glass card

- [ ] **Step 1: Create ScoreTrendChart.jsx**

```jsx
import { useRef, useEffect } from "react";
import { SectionHeader, EmptyState } from "../../layouts";
import { ChartBarIcon } from "@heroicons/react/24/outline";

const ScoreTrendChart = ({ reports = [] }) => {
  const canvasRef = useRef(null);

  const dataPoints = reports
    .filter((r) => r.security_score != null)
    .map((r) => ({ score: r.security_score, date: new Date(r.created_at) }))
    .sort((a, b) => a.date - b.date);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || dataPoints.length < 2) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = rect.height;
    const pad = { top: 20, right: 20, bottom: 30, left: 40 };
    const plotW = w - pad.left - pad.right;
    const plotH = h - pad.top - pad.bottom;

    const xMin = dataPoints[0].date.getTime();
    const xMax = dataPoints[dataPoints.length - 1].date.getTime();
    const yMin = 0;
    const yMax = 100;

    const x = (d) => pad.left + ((d.getTime() - xMin) / (xMax - xMin)) * plotW;
    const y = (s) => pad.top + plotH - ((s - yMin) / (yMax - yMin)) * plotH;

    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = "rgba(75, 85, 99, 0.3)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gy = pad.top + (plotH / 4) * i;
      ctx.beginPath(); ctx.moveTo(pad.left, gy); ctx.lineTo(w - pad.right, gy); ctx.stroke();
      ctx.fillStyle = "#6b7280"; ctx.font = "10px Inter, sans-serif"; ctx.textAlign = "right";
      ctx.fillText(Math.round(yMax - (yMax / 4) * i).toString(), pad.left - 8, gy + 4);
    }

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, pad.top, 0, h - pad.bottom);
    if (dataPoints[dataPoints.length - 1].score >= 60) {
      gradient.addColorStop(0, "rgba(34, 211, 238, 0.3)");
      gradient.addColorStop(1, "rgba(34, 211, 238, 0.02)");
    } else {
      gradient.addColorStop(0, "rgba(239, 68, 68, 0.3)");
      gradient.addColorStop(1, "rgba(239, 68, 68, 0.02)");
    }

    ctx.beginPath();
    ctx.moveTo(x(dataPoints[0].date), pad.top + plotH);
    dataPoints.forEach((p) => ctx.lineTo(x(p.date), y(p.score)));
    ctx.lineTo(x(dataPoints[dataPoints.length - 1].date), pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    dataPoints.forEach((p, i) => {
      const px = x(p.date);
      const py = y(p.score);
      if (i === 0) ctx.moveTo(px, py);
      else {
        const cp1x = x(dataPoints[i - 1].date) + (px - x(dataPoints[i - 1].date)) / 2;
        ctx.bezierCurveTo(cp1x, y(dataPoints[i - 1].score), cp1x, py, px, py);
      }
    });
    ctx.strokeStyle = dataPoints[dataPoints.length - 1].score >= 60 ? "#22d3ee" : "#ef4444";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Dots
    dataPoints.forEach((p) => {
      ctx.beginPath();
      ctx.arc(x(p.date), y(p.score), 3, 0, Math.PI * 2);
      ctx.fillStyle = dataPoints[dataPoints.length - 1].score >= 60 ? "#22d3ee" : "#ef4444";
      ctx.fill();
    });
  }, [dataPoints]);

  if (dataPoints.length < 2) {
    return (
      <div className="flex items-center justify-center h-full">
        <EmptyState icon={ChartBarIcon} title="No trend data" description="Run scans to see your security score trend over time" />
      </div>
    );
  }

  return (
    <div>
      <canvas ref={canvasRef} className="w-full h-[220px]" />
    </div>
  );
};

export default ScoreTrendChart;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/dashboard/ScoreTrendChart.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/ScoreTrendChart.jsx
git commit -m "feat: Task 2 — ScoreTrendChart Canvas line chart"
```

---
### Task 3: QuickActions.jsx — Visual Upgrade

**Files:**
- Modify: `frontend/src/components/dashboard/QuickActions.jsx`

**Interfaces:**
- Consumes: none (same as current)
- Produces: same 4-action grid with enhanced animations and keyboard shortcut hints

- [ ] **Step 1: Rewrite QuickActions.jsx**

Replace the entire file with:

```jsx
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { PlusIcon, PlayIcon, DocumentChartBarIcon, ChartBarIcon } from "@heroicons/react/24/outline";

const actions = [
  { name: "New Project", description: "Add repository", icon: PlusIcon, gradient: "from-blue-500 to-purple-600", to: "/projects?action=new", shortcut: "N" },
  { name: "Run Scan", description: "Start security scan", icon: PlayIcon, gradient: "from-emerald-500 to-green-500", to: "/projects", shortcut: "S" },
  { name: "View Reports", description: "See all findings", icon: DocumentChartBarIcon, gradient: "from-orange-500 to-amber-500", to: "/reports", shortcut: "R" },
  { name: "Analytics", description: "Explore trends", icon: ChartBarIcon, gradient: "from-pink-500 to-rose-500", to: "/analytics", shortcut: "A" },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const itemAnim = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const QuickActions = () => (
  <motion.div className="grid grid-cols-2 gap-4" variants={container} initial="hidden" animate="show">
    {actions.map((action) => (
      <motion.div key={action.name} variants={itemAnim}>
        <Link to={action.to}
          className="group relative flex flex-col items-center justify-center p-5 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:border-cyan-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-cyan-500/10 text-center min-h-[120px] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
        >
          <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity`} />
          <div className={`p-3 rounded-xl bg-gradient-to-br ${action.gradient} shadow-lg mb-3 group-hover:scale-110 transition-transform`}>
            <action.icon className="h-5 w-5 text-white" />
          </div>
          <span className="text-sm font-medium text-white">{action.name}</span>
          <span className="text-xs text-gray-500 mt-1">{action.description}</span>
          <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-gray-700/50 text-gray-500 rounded text-[10px] font-mono">{action.shortcut}</span>
        </Link>
      </motion.div>
    ))}
  </motion.div>
);

export default QuickActions;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/dashboard/QuickActions.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/QuickActions.jsx
git commit -m "feat: Task 3 — QuickActions with stagger animation + shortcut badges"
```

---
### Task 4: RecentScans.jsx — Visual Upgrade

**Files:**
- Modify: `frontend/src/components/dashboard/RecentScans.jsx`

**Interfaces:**
- Consumes: `scans` (array), `isLoading` (bool), `error` (any), `onRetry` (fn) — same as current
- Produces: scan list with framer-motion staggered animation + left severity color bar

- [ ] **Step 1: Rewrite RecentScans.jsx**

Replace the entire file with:

```jsx
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { CheckCircleIcon, ClockIcon, XCircleIcon, ArrowRightIcon, DocumentChartBarIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const statusConfig = {
  completed: { icon: CheckCircleIcon, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Completed" },
  in_progress: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  running: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  failed: { icon: XCircleIcon, color: "text-red-400", bg: "bg-red-500/10", label: "Failed" },
  cancelled: { icon: XCircleIcon, color: "text-gray-400", bg: "bg-gray-500/10", label: "Cancelled" },
  pending: { icon: ClockIcon, color: "text-amber-400", bg: "bg-amber-500/10", label: "Pending" },
};

const getSeverityColor = (sev) => {
  if (sev > 0) return "bg-red-500";
  return "bg-transparent";
};

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const itemAnim = { hidden: { opacity: 0, x: -10 }, show: { opacity: 1, x: 0 } };

const RecentScanItem = ({ report, onClick, index }) => {
  const status = statusConfig[report.status] || statusConfig.pending;
  const StatusIcon = status.icon;
  const sev = report.findings_by_severity || {};
  const critical = sev.critical || 0;
  const high = sev.high || 0;
  const medium = sev.medium || 0;
  const low = sev.low || 0;
  const total = critical + high + medium + low;

  return (
    <motion.div variants={itemAnim} custom={index}
      onClick={onClick}
      className="group relative flex items-center gap-4 p-4 rounded-xl bg-gray-800/20 hover:bg-gray-800/40 border border-transparent hover:border-gray-700/50 transition-all cursor-pointer overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${critical > 0 ? "bg-red-500" : high > 0 ? "bg-orange-500" : medium > 0 ? "bg-yellow-500" : "bg-transparent"}`} />
      <div className={`p-2.5 rounded-xl ${status.bg} flex-shrink-0`}>
        <StatusIcon className={`h-5 w-5 ${status.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-medium text-white truncate">{report.project_name || "Unknown Project"}</h4>
          {critical > 0 && <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-red-500/20 text-red-400">{critical} CRIT</span>}
          {high > 0 && <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-orange-500/20 text-orange-400">{high} HIGH</span>}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{report.scan_type || "Security"} Scan</span>
          <span>{total} findings</span>
          <span>{new Date(report.created_at).toLocaleDateString()}</span>
        </div>
      </div>
      <ArrowRightIcon className="w-4 h-4 text-gray-500 group-hover:text-white group-hover:translate-x-1 transition-all flex-shrink-0" />
    </motion.div>
  );
};

const RecentScans = ({ scans = [], isLoading, error, onRetry }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-[72px] bg-gray-800/20 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <p className="text-red-400 text-sm mb-3">Failed to load recent scans</p>
        <button onClick={onRetry} className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors underline underline-offset-2">Try Again</button>
      </div>
    );
  }

  if (!scans || scans.length === 0) {
    return <EmptyState icon={DocumentChartBarIcon} title="No scans yet" description="Create a project to start scanning" />;
  }

  return (
    <motion.div className="space-y-2" variants={container} initial="hidden" animate="show">
      {scans.slice(0, 4).map((report, i) => (
        <RecentScanItem key={report.id || report._id} report={report} index={i} onClick={() => navigate(`/report/${report.id || report._id}`)} />
      ))}
    </motion.div>
  );
};

export default RecentScans;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/dashboard/RecentScans.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/RecentScans.jsx
git commit -m "feat: Task 4 — RecentScans with stagger animation + severity color bars"
```

---
### Task 5: Dashboard.jsx — Orchestrator + LiveActivity Extraction + Cleanup

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`
- Delete: `frontend/src/components/dashboard/DashboardStatsBar.jsx`
- Delete: `frontend/src/components/dashboard/SecurityScoreChart.jsx`

**Interfaces:**
- Consumes: `notifications` (array — same as current)
- Produces: fully remastered dashboard page

- [ ] **Step 1: Rewrite Dashboard.jsx**

Replace the file with the full orchestrator:

```jsx
import { useMemo } from "react";
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
  const { data: stats, isLoading: statsLoading, refetch: refetchStats, isFetching: statsFetching } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardAPI.getQuickStats(),
    refetchInterval: 30000,
    staleTime: 30000,
  });

  const { data: reportsData, isLoading: reportsLoading, error: reportsError, refetch: refetchReports } = useQuery({
    queryKey: ["recent-reports"],
    queryFn: () => reportsAPI.getReports({ limit: 10, sort_by: "created_at", sort_order: "desc" }),
    staleTime: 30000,
  });

  const { recentReports, severityDistribution } = useMemo(() => {
    const reports = reportsData?.reports || reportsData?.data || [];
    const dist = reports.reduce((acc, r) => {
      const sev = r.findings_by_severity || {};
      acc.critical += sev.critical || 0;
      acc.high += sev.high || 0;
      acc.medium += sev.medium || 0;
      acc.low += sev.low || 0;
      return acc;
    }, { critical: 0, high: 0, medium: 0, low: 0 });
    return { recentReports: reports, severityDistribution: dist };
  }, [reportsData]);

  const score = stats?.avgSecurityScore != null ? Math.round(stats.avgSecurityScore) : null;
  const scoreTrend = stats?.scoreTrend ?? null;

  const refresh = () => { refetchStats(); refetchReports(); };

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <PageHeader
          title="Security Dashboard"
          description="Real-time overview of your security posture"
          icon={ShieldCheckIcon}
          breadcrumb={["Dashboard"]}
          actions={
            <div className="flex items-center gap-3">
              <button onClick={refresh}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl bg-gray-800/30 border border-gray-700/50 text-gray-300 hover:text-white hover:border-gray-600 hover:bg-gray-800/50 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
                <ArrowPathIcon className={`w-4 h-4 ${statsFetching ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
              <Link to="/projects?action=new"
                className="inline-flex items-center justify-center gap-2 px-8 py-3 text-base font-semibold rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transform hover:scale-[1.03] active:scale-[0.98] transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                <PlusIcon className="h-5 w-5" />
                <span>New Project</span>
              </Link>
            </div>
          }
        />

        <DashboardHero securityScore={score} scoreTrend={scoreTrend} />

        {statsLoading ? (
          <div className="grid grid-cols-4 gap-4 mb-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-[120px] bg-gray-800/30 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <MetricCard title="Projects" value={stats?.totalProjects ?? 0} trend={stats?.projectsTrend} icon={ShieldCheckIcon} />
            <MetricCard title="Total Scans" value={stats?.totalScans ?? 0} trend={stats?.scansTrend} icon={ArrowPathIcon} />
            <MetricCard title="Open Issues" value={stats?.openIssues ?? 0} trend={stats?.issuesTrend} icon={BoltIcon} colorClass={stats?.openIssues > 0 ? "from-red-500 to-orange-500" : "from-cyan-400 to-violet-500"} />
            <MetricCard title="Avg Score" value={score != null ? score : "—"} trend={scoreTrend} icon={ShieldCheckIcon} colorClass={score >= 80 ? "from-emerald-400 to-cyan-500" : score >= 60 ? "from-yellow-400 to-orange-500" : "from-red-400 to-rose-500"} />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <GlassCard>
            <SectionHeader title="Security Overview" description="Score trend over time" />
            <ScoreTrendChart reports={recentReports} />
            <div className="mt-4 pt-4 border-t border-gray-800/50">
              <h4 className="text-sm font-medium text-white mb-3">Vulnerability Distribution</h4>
              {[
                { label: "Critical", count: severityDistribution.critical || 0, color: "from-red-500 to-rose-500" },
                { label: "High", count: severityDistribution.high || 0, color: "from-orange-500 to-amber-500" },
                { label: "Medium", count: severityDistribution.medium || 0, color: "from-yellow-500 to-lime-500" },
                { label: "Low", count: severityDistribution.low || 0, color: "from-blue-500 to-cyan-500" },
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
              <Link to="/reports" className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">View all →</Link>
            </div>
            <RecentScans scans={recentReports} isLoading={reportsLoading} error={reportsError} onRetry={refetchReports} />
          </GlassCard>
        </div>

        <GlassCard>
          <SectionHeader title="Live Activity" description="Real-time notifications and updates" />
          <div className="max-h-[200px] overflow-y-auto space-y-2">
            {notifications.length === 0 ? (
              <EmptyState icon={BoltIcon} title="No recent activity" description="Updates will appear here in real-time" />
            ) : (
              notifications.slice(0, 6).map((notif) => {
                const typeIcon = notif.type === "scan_completed" ? "text-emerald-400 bg-emerald-500/10"
                  : notif.type === "scan_error" ? "text-red-400 bg-red-500/10"
                  : notif.type === "scan_started" ? "text-blue-400 bg-blue-500/10"
                  : "text-cyan-400 bg-cyan-500/10";
                const IconComponent = notif.type === "scan_completed" ? ShieldCheckIcon
                  : notif.type === "scan_error" ? ArrowPathIcon
                  : BoltIcon;

                return (
                  <div key={notif.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
                  >
                    <div className={`p-2 rounded-lg ${typeIcon} flex-shrink-0`}>
                      <IconComponent className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate">{notif.message}</p>
                      <p className="text-xs text-gray-500">{new Date(notif.timestamp).toLocaleTimeString()}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </GlassCard>
      </PageContainer>
    </div>
  );
};

export default Dashboard;
```

- [ ] **Step 2: Delete old files**

```bash
git rm frontend/src/components/dashboard/DashboardStatsBar.jsx frontend/src/components/dashboard/SecurityScoreChart.jsx
```

- [ ] **Step 3: Lint entire src**

Run: `npx eslint src/`
Expected: 0 errors, 0 warnings

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: Task 5 — Dashboard orchestrator with hero, MetricCard row, ScoreTrendChart, cleanup"
```

---

## Execution Handoff

After this plan is saved, the user will choose execution approach.
