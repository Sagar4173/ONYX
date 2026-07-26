import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const statusConfig = {
  completed: { icon: CheckCircleIcon, bg: "bg-green-500/20", color: "text-green-400" },
  failed: { icon: XCircleIcon, bg: "bg-red-500/20", color: "text-red-400" },
  pending: { icon: ArrowPathIcon, bg: "bg-cyan-500/20", color: "text-cyan-400" },
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
    <motion.div
      className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar"
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}
    >
      {scans.map((scan) => {
        const cfg = statusConfig[scan.status] || statusConfig.pending;
        const Icon = cfg.icon;
        return (
          <motion.div
            key={scan.id}
            variants={{
              hidden: { opacity: 0, x: -20 },
              show: { opacity: 1, x: 0 },
            }}
          >
            <Link
              to={`/report/${scan.id}`}
              className="flex items-start space-x-4 p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 hover:bg-gray-800/60 transition-all group"
            >
              <div className="relative flex items-start pt-1">
                <div className={`p-2 rounded-lg ${cfg.bg}`}>
                  <Icon className={`h-5 w-5 ${cfg.color}`} />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate group-hover:text-cyan-400 transition-colors">
                  {scan.project_name || scan.repository_url || "Unknown Project"}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color}`}>
                    {scan.status}
                  </span>
                  <span className="text-xs text-gray-500">
                    {scan.total_findings || scan.findings_count || 0} findings
                  </span>
                </div>
              </div>
              <div className="text-right flex-shrink-0">
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
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default RecentScansTimeline;
