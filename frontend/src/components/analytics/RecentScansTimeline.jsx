import { Link } from "react-router-dom";
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const ScanStatusIcon = ({ status }) => {
  if (status === "completed") return <CheckCircleIcon className="h-5 w-5 text-green-400" />;
  if (status === "failed") return <XCircleIcon className="h-5 w-5 text-red-400" />;
  return <ArrowPathIcon className="h-5 w-5 text-cyan-400 animate-spin" />;
};

const RecentScansTimeline = ({ scans = [] }) => {
  if (scans.length === 0) {
    return (
      <EmptyState
        icon={ClockIcon}
        title="No Recent Scans"
        description="Start a security scan to see activity here"
      />
    );
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
      {scans.map((scan) => (
        <Link
          key={scan.id}
          to={`/report/${scan.id}`}
          className="flex items-start space-x-4 p-4 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-all border border-transparent hover:border-gray-700/50 group"
        >
          <div
            className={`p-2.5 rounded-lg ${
              scan.status === "completed"
                ? "bg-green-500/20"
                : scan.status === "failed"
                  ? "bg-red-500/20"
                  : "bg-cyan-500/20"
            }`}
          >
            <ScanStatusIcon status={scan.status} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate group-hover:text-cyan-400 transition-colors">
              {scan.project_name || scan.repository_url || "Unknown Project"}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  scan.status === "completed"
                    ? "bg-green-500/20 text-green-400"
                    : scan.status === "failed"
                      ? "bg-red-500/20 text-red-400"
                      : "bg-cyan-500/20 text-cyan-400"
                }`}
              >
                {scan.status}
              </span>
              <span className="text-xs text-gray-500">
                {scan.total_findings || scan.findings_count || 0} findings
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-gray-500">
              {new Date(scan.created_at).toLocaleDateString()}
            </span>
            <p className="text-xs text-gray-600 mt-1">
              {new Date(scan.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
};

export default RecentScansTimeline;
