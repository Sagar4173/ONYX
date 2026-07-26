import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ArrowRightIcon,
  DocumentChartBarIcon,
} from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const statusConfig = {
  completed: {
    icon: CheckCircleIcon,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    label: "Completed",
  },
  in_progress: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  running: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  failed: { icon: XCircleIcon, color: "text-red-400", bg: "bg-red-500/10", label: "Failed" },
  cancelled: {
    icon: XCircleIcon,
    color: "text-gray-400",
    bg: "bg-gray-500/10",
    label: "Cancelled",
  },
  pending: { icon: ClockIcon, color: "text-amber-400", bg: "bg-amber-500/10", label: "Pending" },
};

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};
const itemAnim = { hidden: { opacity: 0, x: -10 }, show: { opacity: 1, x: 0 } };

const RecentScanItem = ({ report, onClick }) => {
  const status = statusConfig[report.status] || statusConfig.pending;
  const StatusIcon = status.icon;
  const sev = report.findings_by_severity || {};
  const critical = sev.critical || 0;
  const high = sev.high || 0;
  const medium = sev.medium || 0;
  const low = sev.low || 0;
  const total = critical + high + medium + low;

  return (
    <motion.div
      variants={itemAnim}
      onClick={onClick}
      className="group relative flex items-center gap-4 p-4 rounded-xl bg-gray-800/20 hover:bg-gray-800/40 border border-transparent hover:border-gray-700/50 transition-all cursor-pointer overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
    >
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 ${critical > 0 ? "bg-red-500" : high > 0 ? "bg-orange-500" : medium > 0 ? "bg-yellow-500" : "bg-transparent"}`}
      />
      <div className={`p-2.5 rounded-xl ${status.bg} flex-shrink-0`}>
        <StatusIcon className={`h-5 w-5 ${status.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-medium text-white truncate">
            {report.project_name || "Unknown Project"}
          </h4>
          {critical > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-red-500/20 text-red-400">
              {critical} CRIT
            </span>
          )}
          {high > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-orange-500/20 text-orange-400">
              {high} HIGH
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{report.scan_type || "Security"} Scan</span>
          <span>{total} findings</span>
          <span>{new Date(report.created_at).toLocaleDateString()}</span>
        </div>
      </div>
      <ArrowRightIcon className="w-4 h-4 text-gray-500 group-hover:text-white group-hover:translate-x-1 transition-all flex-shrink-0" />
    </motion.div>
  );
};

const RecentScans = ({ scans = [], isLoading, error, onRetry }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-[72px] bg-gray-800/20 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <p className="text-red-400 text-sm mb-3">Failed to load recent scans</p>
        <button
          onClick={onRetry}
          className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors underline underline-offset-2"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!scans || scans.length === 0) {
    return (
      <EmptyState
        icon={DocumentChartBarIcon}
        title="No scans yet"
        description="Create a project to start scanning"
      />
    );
  }

  return (
    <motion.div className="space-y-2" variants={container} initial="hidden" animate="show">
      {scans.slice(0, 4).map((report) => (
        <RecentScanItem
          key={report.id || report._id}
          report={report}
          onClick={() => navigate(`/report/${report.id || report._id}`)}
        />
      ))}
    </motion.div>
  );
};

export default RecentScans;
