import {
  FolderIcon,
  PlayIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { StatCard } from "../../styles/components";

const ProjectStatsBar = ({ analytics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 bg-gray-800/30 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        title="Total Projects"
        value={analytics.total_projects ?? analytics.totalProjects ?? 0}
        icon={<FolderIcon className="w-6 h-6 text-white" />}
        gradient="from-blue-500 to-cyan-500"
      />
      <StatCard
        title="Active Scans"
        value={analytics.active_scans ?? analytics.activeScans ?? 0}
        icon={<PlayIcon className="w-6 h-6 text-white" />}
        gradient="from-violet-500 to-purple-500"
      />
      <StatCard
        title="Avg Security Score"
        value={(analytics.average_score ?? analytics.averageScore ?? 0) + "%"}
        icon={<ShieldCheckIcon className="w-6 h-6 text-white" />}
        gradient="from-emerald-500 to-green-500"
      />
      <StatCard
        title="Open Issues"
        value={analytics.total_issues ?? analytics.totalIssues ?? 0}
        icon={<ExclamationTriangleIcon className="w-6 h-6 text-white" />}
        gradient="from-red-500 to-orange-500"
      />
    </div>
  );
};

export default ProjectStatsBar;
