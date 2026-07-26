import { useState } from "react";
import { EllipsisVerticalIcon, PencilIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Badge, StatusDot } from "../../styles/components";

const priorityBadgeMap = { critical: "danger", high: "warning", medium: "warning", low: "info" };
const statusDotMap = { active: "success", inactive: "warning", archived: "neutral" };

const getScoreColor = (score) => {
  if (score >= 80) return "text-green-400";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
};

const severityDotMap = [
  { key: "critical", color: "bg-red-500" },
  { key: "high", color: "bg-orange-500" },
  { key: "medium", color: "bg-yellow-500" },
  { key: "low", color: "bg-cyan-500" },
];

const ProjectRow = ({ project, selected, onSelect, onView, onEdit, onDelete }) => {
  const [showActions, setShowActions] = useState(false);
  const issues = project.vulnerability_count || {};

  return (
    <div
      className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer
        hover:bg-gray-800/50 border border-transparent hover:border-gray-700/50
        ${selected ? "bg-gray-800/50 border-gray-700/50" : ""}`}
      onClick={() => onView?.(project)}
    >
      {onSelect && (
        <div onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onSelect(project.id)}
            className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
          />
        </div>
      )}

      <StatusDot status={statusDotMap[project.status] || "neutral"} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium truncate">{project.name}</span>
          <Badge variant={priorityBadgeMap[project.priority] || "default"} size="xs">
            {project.priority}
          </Badge>
        </div>
        {project.description && (
          <p className="text-gray-500 text-sm truncate">{project.description}</p>
        )}
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className={`font-mono font-bold ${getScoreColor(project.security_score)}`}>
          {project.security_score ?? "—"}
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        {severityDotMap.map(({ key, color }) => (
          <span
            key={key}
            className={`w-2 h-2 rounded-full ${color} ${(issues[key] || 0) > 0 ? "" : "opacity-20"}`}
            title={`${key}: ${issues[key] || 0}`}
          />
        ))}
      </div>

      <span className="text-sm text-gray-500 w-24 text-right">
        {project.last_scan ? new Date(project.last_scan).toLocaleDateString() : "—"}
      </span>

      <div className="relative" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={() => setShowActions(!showActions)}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-all"
        >
          <EllipsisVerticalIcon className="w-5 h-5" />
        </button>
        {showActions && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowActions(false)} />
            <div className="absolute right-0 top-full mt-1 w-40 z-20 bg-gray-800 border border-gray-700 rounded-xl shadow-xl py-1">
              <button
                onClick={() => {
                  setShowActions(false);
                  onEdit?.(project);
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50"
              >
                <PencilIcon className="w-4 h-4" /> Edit
              </button>
              <button
                onClick={() => {
                  setShowActions(false);
                  onDelete?.(project);
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-700/50"
              >
                <TrashIcon className="w-4 h-4" /> Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProjectRow;
