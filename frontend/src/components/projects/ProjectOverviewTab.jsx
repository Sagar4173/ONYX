import { GlobeAltIcon } from "@heroicons/react/24/outline";
import { getPriorityColor, getStatusColor } from "./projectHelpers";

const VulnBreakdown = ({ vulnCounts }) => {
  const items = [
    { severity: "critical", count: vulnCounts.critical, color: "text-red-400" },
    { severity: "high", count: vulnCounts.high, color: "text-orange-400" },
    { severity: "medium", count: vulnCounts.medium, color: "text-yellow-400" },
    { severity: "low", count: vulnCounts.low, color: "text-cyan-400" },
  ];

  return (
    <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
      <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Breakdown</h3>
      <div className="space-y-4">
        {items.map(({ severity, count, color }) => (
          <div key={severity} className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${color.replace("text-", "bg-")}`} />
              <span className="text-gray-400 capitalize">{severity}</span>
            </div>
            <span className={`font-medium ${color}`}>{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const ProjectOverviewTab = ({ project, vulnCounts }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-6">
        <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Project Information</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Status</span>
              <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(project.status)}`}>{project.status}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Priority</span>
              <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getPriorityColor(project.priority)}`}>{project.priority}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Category</span>
              <span className="text-white">{project.category}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Created</span>
              <span className="text-white">{new Date(project.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Repository</h3>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <GlobeAltIcon className="h-5 w-5 text-gray-400 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-gray-400 text-sm">Repository URL</p>
                <a href={project.repository?.url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors break-all">
                  {project.repository?.url || "Not configured"}
                </a>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Branch</span>
              <span className="text-white font-mono">{project.repository?.branch || "main"}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <VulnBreakdown vulnCounts={vulnCounts} />

        <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Enabled Scanners</h3>
          <div className="flex flex-wrap gap-2">
            {project.scan_config.enabled_scanners.map((scanner) => (
              <span key={scanner} className="px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm font-medium">{scanner.toUpperCase()}</span>
            ))}
          </div>
        </div>

        {project.tags?.length > 0 && (
          <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {project.tags.map((tag) => (
                <span key={tag} className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-lg text-sm">{tag}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  </div>
);

export default ProjectOverviewTab;
