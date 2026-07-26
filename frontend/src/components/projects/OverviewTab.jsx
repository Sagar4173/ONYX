import { GlobeAltIcon } from "@heroicons/react/24/outline";
import { getPriorityColor, getStatusColor } from "./projectHelpers";
import SecurityRadar from "./SecurityRadar";
import VulnerabilityMatrix from "./VulnerabilityMatrix";
import ActivityTimeline from "./ActivityTimeline";

const OverviewTab = ({ project, vulnCounts, events = [] }) => {
  const radarData = [
    { label: "SAST", value: project.stats?.sast_coverage || 0 },
    { label: "Secrets", value: project.stats?.secrets_coverage || 0 },
    { label: "Dependencies", value: project.stats?.deps_coverage || 0 },
    { label: "Container", value: project.stats?.container_coverage || 0 },
    { label: "IaC", value: project.stats?.iac_coverage || 0 },
    { label: "DAST", value: project.stats?.dast_coverage || 0 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50 flex items-center justify-center">
          <SecurityRadar data={radarData} />
        </div>
        <VulnerabilityMatrix vulnCounts={vulnCounts} />
      </div>

      <div className="space-y-6">
        <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Project Info</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Status</span>
              <span
                className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getStatusColor(project.status)}`}
              >
                {project.status}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Priority</span>
              <span
                className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getPriorityColor(project.priority)}`}
              >
                {project.priority}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Category</span>
              <span className="text-white text-sm">{project.category}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Created</span>
              <span className="text-white text-sm">
                {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>
            {project.repository?.url && (
              <div className="pt-3 border-t border-gray-700/50">
                <div className="flex items-start space-x-2">
                  <GlobeAltIcon className="w-4 h-4 text-gray-400 mt-0.5" />
                  <a
                    href={project.repository.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-400 hover:text-cyan-300 text-sm break-all"
                  >
                    {project.repository.url}
                  </a>
                </div>
                <p className="text-gray-500 text-xs mt-1 font-mono">
                  Branch: {project.repository.branch || "main"}
                </p>
              </div>
            )}
          </div>
        </div>

        <ActivityTimeline events={events} />

        {project.stats?.vulnerable_deps > 0 && (
          <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-3">Dependencies</h3>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400 text-sm">Vulnerable</span>
              <span className="text-red-400 font-bold">{project.stats.vulnerable_deps}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Total packages</span>
              <span className="text-white font-mono">{project.stats.total_deps || "-"}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OverviewTab;
