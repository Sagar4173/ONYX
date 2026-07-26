import { motion } from "framer-motion";
import { PencilIcon, TrashIcon, GlobeAltIcon } from "@heroicons/react/24/outline";
import { getPriorityColor, getStatusColor } from "./projectHelpers";
import SecurityScoreGlobe from "./SecurityScoreGlobe";

const ProjectSidebar = ({ project, vulnCounts, securityScore, isScanActive, onEdit, onDelete }) => {
  return (
    <motion.aside
      className="w-[300px] flex-shrink-0 bg-gray-800/40 backdrop-blur-xl border-r border-gray-700/50 p-6 space-y-6 overflow-y-auto"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", damping: 20 }}
    >
      <div>
        <h2 className="text-lg font-bold text-white mb-3">{project.name}</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          <span
            className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getStatusColor(project.status)}`}
          >
            {project.status}
          </span>
          <span
            className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getPriorityColor(project.priority)}`}
          >
            {project.priority}
          </span>
          {project.category && (
            <span className="px-2.5 py-0.5 bg-gray-700/50 text-gray-300 rounded-lg text-xs">
              {project.category}
            </span>
          )}
        </div>
        {project.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {project.tags.slice(0, 5).map((tag) => (
              <span key={tag} className="px-2 py-0.5 bg-gray-700/30 text-gray-400 rounded text-xs">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex justify-center">
        <SecurityScoreGlobe score={securityScore} isScanActive={isScanActive} />
      </div>
      <div className="text-center -mt-2">
        <p className="text-xs text-gray-500">Security Score</p>
        <p className="text-xs text-gray-400">
          Last scan:{" "}
          {project.stats?.last_scan_date
            ? new Date(project.stats.last_scan_date).toLocaleDateString()
            : "Never"}
        </p>
      </div>

      <div className="border-t border-gray-700/50" />

      {project.repository?.url && (
        <div>
          <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2 font-medium">
            Repository
          </h4>
          <div className="flex items-start space-x-2">
            <GlobeAltIcon className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <a
              href={project.repository.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 text-xs break-all"
            >
              {project.repository.url}
            </a>
          </div>
          <p className="text-gray-500 text-xs mt-1 font-mono ml-6">
            {project.repository.branch || "main"}
          </p>
        </div>
      )}

      {project.scan_config?.enabled_scanners?.length > 0 && (
        <div>
          <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2 font-medium">
            Scanners
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {project.scan_config.enabled_scanners.map((s) => (
              <span
                key={s}
                className="px-2 py-1 bg-cyan-500/15 text-cyan-400 rounded text-xs font-medium"
              >
                {s.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2 font-medium">
          Vulnerabilities
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-red-500/10 rounded-lg p-2.5 text-center border border-red-500/20">
            <p className="text-lg font-bold text-red-400">{vulnCounts.critical}</p>
            <p className="text-xs text-gray-500">Critical</p>
          </div>
          <div className="bg-orange-500/10 rounded-lg p-2.5 text-center border border-orange-500/20">
            <p className="text-lg font-bold text-orange-400">{vulnCounts.high}</p>
            <p className="text-xs text-gray-500">High</p>
          </div>
          <div className="bg-yellow-500/10 rounded-lg p-2.5 text-center border border-yellow-500/20">
            <p className="text-lg font-bold text-yellow-400">{vulnCounts.medium}</p>
            <p className="text-xs text-gray-500">Medium</p>
          </div>
          <div className="bg-cyan-500/10 rounded-lg p-2.5 text-center border border-cyan-500/20">
            <p className="text-lg font-bold text-cyan-400">{vulnCounts.low}</p>
            <p className="text-xs text-gray-500">Low</p>
          </div>
        </div>
      </div>

      <div className="space-y-2 pt-2">
        <button
          onClick={onEdit}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-gray-700/50 hover:bg-gray-700/70 text-gray-300 rounded-xl transition-all text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
        >
          <PencilIcon className="w-4 h-4" />
          <span>Edit Project</span>
        </button>
        <button
          onClick={onDelete}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl transition-all text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          <TrashIcon className="w-4 h-4" />
          <span>Delete Project</span>
        </button>
      </div>
    </motion.aside>
  );
};

export default ProjectSidebar;
