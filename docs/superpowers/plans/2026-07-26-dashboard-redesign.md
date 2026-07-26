# Dashboard Redesign Implementation Plan

**Goal:** Split 556-line Dashboard.jsx into focused components, fix error handling, add staleTime, add refresh button.

**Architecture:** Extract 5 inline components into `components/dashboard/`, rewrite orchestrator.

---
### Task 1: SecurityScoreChart Component

**Create:** `src/components/dashboard/SecurityScoreChart.jsx`

```jsx
const SecurityScoreChart = ({ score, severitySummary }) => {
  const scoreValue = score ?? 0;
  const scoreColor = scoreValue >= 80 ? "#22c55e" : scoreValue >= 60 ? "#eab308" : "#ef4444";
  const scoreText = scoreValue >= 80 ? "text-green-400" : scoreValue >= 60 ? "text-yellow-400" : "text-red-400";
  const healthMessage = scoreValue >= 80 ? "Good" : scoreValue >= 60 ? "Fair" : "Needs Attention";
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (scoreValue / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-48">
        <svg className="w-48 h-48 -rotate-90" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={radius} fill="none" stroke="#1f2937" strokeWidth="12" />
          <circle cx="80" cy="80" r={radius} fill="none" stroke={scoreColor} strokeWidth="12"
            strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
            className="transition-all duration-1000 ease-out" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${scoreText}`}>{scoreValue}</span>
          <span className="text-gray-500 text-sm">Security Score</span>
        </div>
      </div>
      <p className={`mt-3 text-sm font-medium ${scoreText}`}>{healthMessage}</p>
      {severitySummary && (
        <div className="w-full mt-4 space-y-1.5">
          {[
            { label: "Critical", count: severitySummary.critical || 0, color: "bg-red-500" },
            { label: "High", count: severitySummary.high || 0, color: "bg-orange-500" },
            { label: "Medium", count: severitySummary.medium || 0, color: "bg-yellow-500" },
            { label: "Low", count: severitySummary.low || 0, color: "bg-cyan-500" },
          ].map(({ label, count, color }) => (
            <div key={label} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
                <span className="text-gray-400">{label}</span>
              </div>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SecurityScoreChart;
```

---
### Task 2: SeverityBar Component

**Create:** `src/components/dashboard/SeverityBar.jsx`

```jsx
const SeverityBar = ({ critical = 0, high = 0, medium = 0, low = 0 }) => {
  const total = critical + high + medium + low;
  if (total === 0) return null;
  const segments = [
    { value: critical, color: "bg-red-500", label: "Critical" },
    { value: high, color: "bg-orange-500", label: "High" },
    { value: medium, color: "bg-yellow-500", label: "Medium" },
    { value: low, color: "bg-cyan-500", label: "Low" },
  ];

  return (
    <div className="space-y-3">
      <div className="flex h-3 rounded-full overflow-hidden bg-gray-800">
        {segments.map((s) =>
          s.value > 0 ? <div key={s.label} className={s.color} style={{ width: `${(s.value / total) * 100}%` }} /> : null
        )}
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        {segments.map((s) => (
          <span key={s.label}>{s.label}: {s.value}</span>
        ))}
      </div>
    </div>
  );
};

export default SeverityBar;
```

---
### Task 3: QuickActions Component

**Create:** `src/components/dashboard/QuickActions.jsx`

```jsx
import { Link } from "react-router-dom";
import { PlusIcon, PlayIcon, DocumentChartBarIcon, ChartBarIcon } from "@heroicons/react/24/outline";

const actions = [
  { name: "New Project", description: "Create a security scan", path: "/projects", icon: PlusIcon, gradient: "from-cyan-500 to-violet-600" },
  { name: "Run Scan", description: "Start a new scan", path: "/projects", icon: PlayIcon, gradient: "from-violet-500 to-purple-600" },
  { name: "View Reports", description: "Review scan results", path: "/reports", icon: DocumentChartBarIcon, gradient: "from-emerald-500 to-green-600" },
  { name: "Analytics", description: "Security trends", path: "/analytics", icon: ChartBarIcon, gradient: "from-orange-500 to-amber-600" },
];

const QuickActions = () => (
  <div className="grid grid-cols-2 gap-3">
    {actions.map(({ name, description, path, icon: Icon, gradient }) => (
      <Link key={name} to={path}
        className="group p-4 rounded-xl bg-gray-800/30 border border-gray-700/50 hover:border-gray-600/50
          hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200">
        <div className={`p-2.5 rounded-xl bg-gradient-to-r ${gradient} shadow-lg w-fit mb-3`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <h4 className="text-white font-medium text-sm group-hover:text-cyan-400 transition-colors">{name}</h4>
        <p className="text-gray-500 text-xs mt-0.5">{description}</p>
      </Link>
    ))}
  </div>
);

export default QuickActions;
```

---
### Task 4: RecentScans Component

**Create:** `src/components/dashboard/RecentScans.jsx`

```jsx
import { Link } from "react-router-dom";
import { ClockIcon, ShieldCheckIcon } from "@heroicons/react/24/outline";
import { Badge } from "../../styles/components";

const statusConfig = {
  completed: { badge: "success", label: "Completed" },
  in_progress: { badge: "warning", label: "In Progress" },
  running: { badge: "warning", label: "Running" },
  failed: { badge: "danger", label: "Failed" },
  pending: { badge: "info", label: "Pending" },
};

const RecentScans = ({ scans }) => {
  if (!scans || scans.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <ShieldCheckIcon className="w-10 h-10 text-gray-600 mb-3" />
        <p className="text-gray-500 text-sm">No scans yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {scans.slice(0, 4).map((scan) => {
        const status = statusConfig[scan.status] || statusConfig.pending;
        const severity = scan.findings_by_severity || {};
        return (
          <Link key={scan.id || scan._id} to={`/report/${scan.id}`}
            className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-800/50 transition-colors group">
            <div className={`p-2 rounded-lg ${scan.status === "completed" ? "bg-green-500/10" : scan.status === "failed" ? "bg-red-500/10" : "bg-gray-800"}`}>
              <ShieldCheckIcon className={`w-5 h-5 ${scan.status === "completed" ? "text-green-400" : scan.status === "failed" ? "text-red-400" : "text-gray-400"}`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate group-hover:text-cyan-400 transition-colors">
                {scan.project_name || "Untitled"}
              </p>
              <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                <span>{scan.scan_type?.toUpperCase()}</span>
                <span>•</span>
                <span>{new Date(scan.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              {severity.critical > 0 && <Badge variant="critical" size="xs">{severity.critical}</Badge>}
              {severity.high > 0 && <Badge variant="high" size="xs">{severity.high}</Badge>}
              <Badge variant={status.badge} size="xs">{status.label}</Badge>
            </div>
          </Link>
        );
      })}
    </div>
  );
};

export default RecentScans;
```

---
### Task 5: DashboardStatsBar Component

**Create:** `src/components/dashboard/DashboardStatsBar.jsx`

```jsx
import { FolderIcon, ShieldCheckIcon, ExclamationTriangleIcon, PlayIcon } from "@heroicons/react/24/outline";
import { StatCard } from "../../styles/components";

const DashboardStatsBar = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 bg-gray-800/30 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }
  if (!stats) return null;

  const score = stats.avgSecurityScore ?? stats.average_score ?? 0;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard title="Total Projects" value={stats.totalProjects ?? stats.total_projects ?? 0}
        icon={<FolderIcon className="w-6 h-6 text-white" />} gradient="from-blue-500 to-cyan-500" />
      <StatCard title="Total Scans" value={stats.totalScans ?? stats.total_scans ?? 0}
        icon={<PlayIcon className="w-6 h-6 text-white" />} gradient="from-violet-500 to-purple-500" />
      <StatCard title="Open Issues" value={stats.openIssues ?? stats.open_issues ?? 0}
        icon={<ExclamationTriangleIcon className="w-6 h-6 text-white" />} gradient="from-red-500 to-orange-500" />
      <StatCard title="Security Score" value={`${score}%`}
        icon={<ShieldCheckIcon className="w-6 h-6 text-white" />} gradient="from-emerald-500 to-green-500" />
    </div>
  );
};

export default DashboardStatsBar;
```

---
### Task 6: Rewrite Dashboard.jsx Orchestrator

**Modify:** `src/pages/Dashboard.jsx`

```jsx
import { useQuery } from "@tanstack/react-query";
import { ArrowPathIcon, BoltIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { Button } from "../styles/components";
import { PageContainer, PageHeader, GlassCard, SectionHeader, EmptyState } from "../layouts";
import { reportsAPI } from "../services/api";
import { dashboardAPI } from "../services/dashboardService";
import SecurityScoreChart from "../components/dashboard/SecurityScoreChart";
import SeverityBar from "../components/dashboard/SeverityBar";
import QuickActions from "../components/dashboard/QuickActions";
import RecentScans from "../components/dashboard/RecentScans";
import DashboardStatsBar from "../components/dashboard/DashboardStatsBar";

const Dashboard = ({ notifications }) => {
  const { data: stats, isLoading: statsLoading, refetch: refetchStats, isFetching: statsFetching } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardAPI.getQuickStats(),
    refetchInterval: 30000,
    staleTime: 30000,
  });

  const { data: reportsData, isLoading: reportsLoading, error: reportsError, refetch: refetchReports } = useQuery({
    queryKey: ["recent-reports"],
    queryFn: () => reportsAPI.getReports({ limit: 10, sort_by: "created_at", sort_order: "desc" })
      .then((res) => res.data || res),
    staleTime: 30000,
  });

  const recentReports = reportsData?.reports ?? reportsData ?? [];
  const severitySummary = recentReports.reduce(
    (acc, r) => {
      const s = r.findings_by_severity || {};
      acc.critical += s.critical || 0;
      acc.high += s.high || 0;
      acc.medium += s.medium || 0;
      acc.low += s.low || 0;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 }
  );
  const totalFindings = severitySummary.critical + severitySummary.high + severitySummary.medium + severitySummary.low;

  const score =
    stats?.avgSecurityScore ??
    stats?.average_score ??
    (recentReports.length > 0
      ? Math.round(recentReports.reduce((sum, r) => sum + (r.security_score || 0), 0) / recentReports.length)
      : 0);

  const refresh = () => { refetchStats(); refetchReports(); };

  return (
    <PageContainer>
      <PageHeader
        title="Security Dashboard"
        description="Real-time security overview and system status"
        icon={SparklesIcon}
        breadcrumb={["Dashboard"]}
        actions={
          <Button variant="ghost" leftIcon={<ArrowPathIcon className="w-4 h-4" />}
            onClick={refresh} isLoading={statsFetching}>Refresh</Button>
        }
      />

      <DashboardStatsBar stats={stats} isLoading={statsLoading} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <GlassCard>
          <SectionHeader title="Security Overview" />
          <SecurityScoreChart score={score} severitySummary={severitySummary} />
          {totalFindings > 0 && (
            <div className="mt-6 pt-4 border-t border-gray-800/50">
              <SeverityBar {...severitySummary} />
            </div>
          )}
        </GlassCard>

        <GlassCard>
          <SectionHeader title="Quick Actions" />
          <QuickActions />
        </GlassCard>

        <GlassCard>
          <SectionHeader
            title="Recent Scans"
            action={reportsError ? null : <Button variant="ghost" size="sm" onClick={refetchReports}>Refresh</Button>}
          />
          {reportsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-800/30 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : reportsError ? (
            <div className="text-center py-6">
              <p className="text-red-400 text-sm mb-2">Failed to load scans</p>
              <Button variant="ghost" size="sm" onClick={refetchReports}>Try Again</Button>
            </div>
          ) : (
            <RecentScans scans={recentReports} />
          )}
        </GlassCard>
      </div>

      <GlassCard>
        <SectionHeader title="Live Activity" />
        {notifications?.length > 0 ? (
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {notifications.slice(0, 6).map((n) => (
              <div key={n.id} className="flex items-start gap-3 p-3 rounded-xl bg-gray-800/30">
                <BoltIcon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${n.type === "security_alert" ? "text-red-400" : "text-cyan-400"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300">{n.message}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{n.timestamp instanceof Date ? n.timestamp.toLocaleTimeString() : ""}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={BoltIcon} title="No recent activity" description="Real-time events will appear here" />
        )}
      </GlassCard>
    </PageContainer>
  );
};

export default Dashboard;
```

---
### Task 7: Verify

- [ ] Run `npx eslint src/components/dashboard/ --ext jsx` — 0 errors
- [ ] Run `npx eslint src/pages/Dashboard.jsx` — 0 errors
- [ ] Run `npm run build` — passes
- [ ] Run `npm run lint` — still 0 errors, 0 warnings
