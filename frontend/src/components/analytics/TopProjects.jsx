import { FolderIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const TopProjects = ({ projects = [] }) => {
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FolderIcon}
        title="No Project Data"
        description="Scan some projects to see analytics"
      />
    );
  }

  return (
    <div className="space-y-3">
      {projects.slice(0, 5).map((project, index) => (
        <div
          key={project.project_name}
          className="flex items-center justify-between p-4 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all border border-gray-700/30"
        >
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-500 flex items-center justify-center text-white font-bold text-sm">
              {index + 1}
            </div>
            <div>
              <p className="text-sm font-medium text-white">{project.project_name}</p>
              <p className="text-xs text-gray-500">{project.scans_count} scans</p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              {project.critical_findings > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400">
                  {project.critical_findings} critical
                </span>
              )}
              {project.high_findings > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-orange-500/20 text-orange-400">
                  {project.high_findings} high
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">{project.total_findings} total findings</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TopProjects;
