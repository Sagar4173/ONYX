import { Link } from "react-router-dom";
import { ChevronRightIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import { Badge } from "../../styles/components";

const statusConfig = {
  completed: { badge: "success", label: "Completed" },
  running: { badge: "warning", label: "Running" },
  pending: { badge: "info", label: "Pending" },
  failed: { badge: "danger", label: "Failed" },
};

const scanTypeIcons = {
  sast: "🔍",
  secrets: "🔑",
  dependency: "📦",
  container: "🐳",
  iac: "🏗️",
};

const ReportCard = ({ report }) => {
  const status = statusConfig[report.status] || statusConfig.pending;
  const scanType = report.scan_type || report.type || "sast";

  return (
    <Link
      to={`/report/${report.id}`}
      className="group flex items-center gap-4 p-4 bg-gray-900/50 border border-gray-800/50 rounded-xl
        hover:border-gray-700/50 hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200"
    >
      <div className="p-3 rounded-2xl bg-gradient-to-r from-violet-500 to-purple-600 shadow-lg flex-shrink-0">
        <DocumentTextIcon className="w-6 h-6 text-white" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-white font-semibold truncate">
            {report.project_name ||
              report.repository_url?.replace(/^https?:\/\//, "") ||
              "Untitled"}
          </h3>
          <Badge variant={status.badge} size="xs">
            {status.label}
          </Badge>
        </div>
        {report.repository_url && (
          <p className="text-gray-500 text-xs truncate font-mono mb-1">
            {report.repository_url.replace(/^https?:\/\//, "")}
          </p>
        )}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>
            {scanTypeIcons[scanType] || "🔍"} {scanType.toUpperCase()}
          </span>
          {report.created_at && <span>{new Date(report.created_at).toLocaleDateString()}</span>}
        </div>
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0">
        {report.critical_count > 0 && (
          <Badge variant="critical" size="xs">
            {report.critical_count}
          </Badge>
        )}
        {report.high_count > 0 && (
          <Badge variant="high" size="xs">
            {report.high_count}
          </Badge>
        )}
        {report.medium_count > 0 && (
          <Badge variant="medium" size="xs">
            {report.medium_count}
          </Badge>
        )}
        {!report.critical_count && !report.high_count && !report.medium_count && (
          <Badge variant="success" size="xs">
            Clean
          </Badge>
        )}
      </div>

      <ChevronRightIcon className="w-5 h-5 text-gray-600 group-hover:text-gray-400 transition-colors flex-shrink-0" />
    </Link>
  );
};

export default ReportCard;
