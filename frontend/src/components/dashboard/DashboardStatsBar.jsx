import {
  FolderIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { StatCard } from "../../styles/components";

const DashboardStatsBar = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 bg-gray-800/30 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }
  if (!stats) return null;

  const statCards = [
    {
      title: "Total Projects",
      value: stats.totalProjects || 0,
      trend: stats.projectsTrend,
      trendPositive: true,
      subtitle: "Active repositories",
      gradient: "from-blue-500 to-cyan-500",
      icon: <FolderIcon className="w-5 h-5 text-white" />,
    },
    {
      title: "Security Scans",
      value: stats.totalScans || 0,
      trend: stats.scansTrend,
      trendPositive: true,
      subtitle: "Total scans performed",
      gradient: "from-violet-500 to-purple-500",
      icon: <ShieldCheckIcon className="w-5 h-5 text-white" />,
    },
    {
      title: "Open Issues",
      value: stats.openIssues || 0,
      trend: stats.issuesTrend,
      trendPositive: false,
      subtitle: "Critical & high severity",
      gradient: "from-orange-500 to-red-500",
      icon: <ExclamationTriangleIcon className="w-5 h-5 text-white" />,
    },
    {
      title: "Security Score",
      value: stats.avgSecurityScore != null ? `${Math.round(stats.avgSecurityScore)}%` : "N/A",
      trend: stats.scoreTrend,
      trendPositive: true,
      subtitle: stats.avgSecurityScore != null ? "Overall health" : "Run first scan",
      gradient: "from-emerald-500 to-green-500",
      icon: <SparklesIcon className="w-5 h-5 text-white" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
      {statCards.map((stat) => (
        <div key={stat.title}>
          <StatCard
            title={stat.title}
            value={stat.value}
            trend={stat.trend}
            trendPositive={stat.trendPositive}
            subtitle={stat.subtitle}
            gradient={stat.gradient}
            icon={stat.icon}
            animated
          />
        </div>
      ))}
    </div>
  );
};

export default DashboardStatsBar;
