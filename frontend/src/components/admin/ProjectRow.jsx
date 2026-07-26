import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { UsersIcon, EyeIcon, TrashIcon } from "@heroicons/react/24/outline";

const ProjectRow = ({ project, onDelete }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <motion.tr
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ backgroundColor: "rgba(255,255,255,0.03)" }}
      className="border-b border-gray-800/50 transition-colors"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <td className="px-4 py-3">
        <div>
          <Link
            to={`/project/${project.id}`}
            className="text-sm font-medium text-white hover:text-cyan-400 transition-colors"
          >
            {project.name}
          </Link>
          <p className="text-xs text-gray-500 truncate max-w-xs">{project.description}</p>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <UsersIcon className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-400">{project.owner?.username || "Unknown"}</span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400">{project.total_scans || 0} scans</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {project.critical_findings > 0 && (
            <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">
              {project.critical_findings} critical
            </span>
          )}
          <span className="text-sm text-gray-400">{project.total_findings || 0} total</span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {project.created_at ? new Date(project.created_at).toLocaleDateString() : "Unknown"}
      </td>
      <td className="px-4 py-3">
        <div
          className={`flex items-center gap-2 transition-opacity ${showActions ? "opacity-100" : "opacity-0"}`}
        >
          <Link
            to={`/project/${project.id}`}
            className="p-1.5 text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/20 rounded-lg transition-colors"
            title="View Project"
          >
            <EyeIcon className="h-4 w-4" />
          </Link>
          <button
            onClick={() => onDelete(project)}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
            title="Delete Project"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </td>
    </motion.tr>
  );
};

export default ProjectRow;
