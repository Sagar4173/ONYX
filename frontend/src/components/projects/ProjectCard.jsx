import { useState } from "react";
import { EllipsisVerticalIcon, PencilIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Badge } from "../ui/StyleComponents";
import { motion } from "framer-motion";

const priorityConfig = {
  critical: { color: "from-red-500 to-orange-500", badge: "danger" },
  high: { color: "from-orange-500 to-amber-500", badge: "warning" },
  medium: { color: "from-yellow-500 to-amber-500", badge: "warning" },
  low: { color: "from-cyan-500 to-blue-500", badge: "info" },
};

const statusConfig = {
  active: { border: "border-l-green-500", dot: "success" },
  inactive: { border: "border-l-yellow-500", dot: "warning" },
  archived: { border: "border-l-gray-500", dot: "neutral" },
};

const getScoreColor = (score) => {
  if (score >= 80) return { stroke: "#22c55e", text: "text-green-400" };
  if (score >= 50) return { stroke: "#eab308", text: "text-yellow-400" };
  return { stroke: "#ef4444", text: "text-red-400" };
};

const severityDots = [
  { key: "critical", color: "bg-red-500", label: "Critical" },
  { key: "high", color: "bg-orange-500", label: "High" },
  { key: "medium", color: "bg-yellow-500", label: "Medium" },
  { key: "low", color: "bg-cyan-500", label: "Low" },
];

const ProjectCard = ({ project, selected, onSelect, onView, onEdit, onDelete }) => {
  const [showActions, setShowActions] = useState(false);
  const status = statusConfig[project.status] || statusConfig.active;
  const priority = priorityConfig[project.priority] || priorityConfig.low;
  const score = project.security_score ?? 0;
  const scoreColor = getScoreColor(score);
  const issues = project.vulnerability_count || {};
  const displayTags = (project.tags || []).slice(0, 3);
  const extraTags = (project.tags || []).length - 3;

  const repoDisplay = project.repository_url
    ? project.repository_url.replace(/^https?:\/\//, "").replace(/\/$/, "")
    : "";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`group relative bg-gray-900/50 border border-gray-800/50 rounded-xl
        hover:border-gray-700/50 hover:-translate-y-0.5 hover:shadow-lg
        transition-all duration-200 cursor-pointer border-l-[3px] ${status.border}
        ${selected ? "ring-2 ring-cyan-500/50 border-cyan-500/50" : ""}`}
      onClick={() => onView?.(project)}
    >
      <div className="p-4">
        {/* Top row: checkbox + icon + name + actions */}
        <div className="flex items-start gap-3">
          {onSelect && (
            <div className="pt-1" onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={selected}
                onChange={() => onSelect(project.id)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500
                  focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
              />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-white font-semibold truncate">{project.name}</h3>
              <Badge variant={priority.badge} size="xs">
                {project.priority}
              </Badge>
              <Badge
                variant={
                  status.dot === "success"
                    ? "success"
                    : status.dot === "warning"
                      ? "warning"
                      : "default"
                }
                size="xs"
              >
                {project.status}
              </Badge>
            </div>
            {project.description && (
              <p className="text-gray-400 text-sm line-clamp-2 mb-2">{project.description}</p>
            )}
            {repoDisplay && (
              <p className="text-gray-500 text-xs truncate mb-3 font-mono">{repoDisplay}</p>
            )}
          </div>

          {/* Actions dropdown */}
          <div
            className="relative opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => e.stopPropagation()}
          >
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
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 transition-colors"
                  >
                    <PencilIcon className="w-4 h-4" /> Edit
                  </button>
                  <button
                    onClick={() => {
                      setShowActions(false);
                      onDelete?.(project);
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-700/50 transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" /> Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Bottom row: score + severity + tags */}
        <div className="flex items-end justify-between mt-3 pt-3 border-t border-gray-800/50">
          {/* Score ring */}
          <div className="flex items-center gap-3">
            <div className="relative w-12 h-12 flex-shrink-0">
              <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#374151" strokeWidth="3" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  stroke={scoreColor.stroke}
                  strokeWidth="3"
                  strokeDasharray={`${(score / 100) * 97.4} 97.4`}
                  strokeLinecap="round"
                />
              </svg>
              <span
                className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${scoreColor.text}`}
              >
                {score}
              </span>
            </div>

            {/* Severity dots */}
            <div className="flex items-center gap-1.5">
              {severityDots.map(({ key, color, label }) => (
                <div
                  key={key}
                  className="flex items-center gap-1"
                  title={`${label}: ${issues[key] || 0}`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${color} ${(issues[key] || 0) > 0 ? "opacity-100" : "opacity-20"}`}
                  />
                  <span className="text-xs text-gray-500">{issues[key] || 0}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tags + last scan */}
          <div className="text-right">
            {displayTags.length > 0 && (
              <div className="flex items-center gap-1 mb-1 justify-end flex-wrap">
                {displayTags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-1.5 py-0.5 rounded-md bg-gray-800/80 text-gray-400 border border-gray-700/50"
                  >
                    {tag}
                  </span>
                ))}
                {extraTags > 0 && <span className="text-xs text-gray-500">+{extraTags}</span>}
              </div>
            )}
            {project.last_scan && (
              <p className="text-xs text-gray-500">
                Scanned {new Date(project.last_scan).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ProjectCard;
