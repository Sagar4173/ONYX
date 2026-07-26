import { utils } from "../../services/api";

export const SeverityBadge = ({ severity }) => {
  const severityColors = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  };
  const severityIcons = {
    critical: "🔴",
    high: "🟠",
    medium: "🟡",
    low: "🔵",
    info: "⚪",
  };
  const colorClass = severityColors[severity?.toLowerCase()] || severityColors.info;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${colorClass} border shadow-sm`}
    >
      <span>{severityIcons[severity?.toLowerCase()] || "⚪"}</span>
      {severity?.charAt(0).toUpperCase() + severity?.slice(1)}
    </span>
  );
};

export const StatusBadge = ({ status }) => {
  const colorClass = utils.getStatusColor(status);
  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} border`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};
