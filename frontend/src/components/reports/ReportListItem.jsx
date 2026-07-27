import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { CheckCircleIcon, ClockIcon, XCircleIcon } from "@heroicons/react/24/outline";
import { Badge } from "../ui/StyleComponents";

const statusConfig = {
  completed: {
    icon: CheckCircleIcon,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    label: "Completed",
  },
  running: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  in_progress: { icon: ClockIcon, color: "text-blue-400", bg: "bg-blue-500/10", label: "Running" },
  pending: { icon: ClockIcon, color: "text-amber-400", bg: "bg-amber-500/10", label: "Pending" },
  failed: { icon: XCircleIcon, color: "text-red-400", bg: "bg-red-500/10", label: "Failed" },
  cancelled: {
    icon: XCircleIcon,
    color: "text-gray-400",
    bg: "bg-gray-500/10",
    label: "Cancelled",
  },
};

const scanTypeColors = {
  sast: "from-cyan-500 to-blue-600",
  secrets: "from-purple-500 to-pink-600",
  dependency: "from-amber-500 to-orange-600",
  container: "from-teal-500 to-emerald-600",
  iac: "from-violet-500 to-indigo-600",
  dast: "from-rose-500 to-red-600",
};

const itemAnim = { hidden: { opacity: 0, x: -10 }, show: { opacity: 1, x: 0 } };

const ScanTypeBadge = ({ type }) => {
  const color = scanTypeColors[type] || "from-gray-500 to-gray-600";
  const label = (type || "sast").toUpperCase();
  return (
    <span
      className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[10px] font-bold text-white bg-gradient-to-r ${color}`}
    >
      {label}
    </span>
  );
};

const ReportListItem = ({ report }) => {
  const navigate = useNavigate();
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
      onClick={() => navigate(`/report/${report.id}`)}
      className="group relative flex items-center gap-4 p-4 rounded-xl bg-gray-800/20 hover:bg-gray-800/40 border border-transparent hover:border-gray-700/50 transition-all cursor-pointer overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter") navigate(`/report/${report.id}`);
      }}
    >
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 ${critical > 0 ? "bg-red-500" : high > 0 ? "bg-orange-500" : medium > 0 ? "bg-yellow-500" : "bg-transparent"}`}
      />
      <div className={`p-2.5 rounded-xl ${status.bg} flex-shrink-0`}>
        <StatusIcon
          className={`h-5 w-5 ${status.color} ${status.label === "Running" || status.label === "Pending" ? "animate-pulse" : ""}`}
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-sm font-semibold text-white truncate">
            {report.project_name ||
              report.repository_url?.replace(/^https?:\/\//, "") ||
              "Untitled"}
          </h3>
          <ScanTypeBadge type={report.scan_type || report.type} />
          {report.security_score != null && (
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${report.security_score >= 80 ? "bg-emerald-500/20 text-emerald-400" : report.security_score >= 60 ? "bg-amber-500/20 text-amber-400" : "bg-red-500/20 text-red-400"}`}
            >
              {report.security_score}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <StatusIcon className={`w-3 h-3 ${status.color}`} />
            {status.label}
          </span>
          {report.created_at && <span>{new Date(report.created_at).toLocaleDateString()}</span>}
          {total > 0 && <span>{total} findings</span>}
        </div>
      </div>
      <div className="flex items-center gap-1 flex-shrink-0">
        {critical > 0 && (
          <Badge variant="critical" size="xs">
            {critical}
          </Badge>
        )}
        {high > 0 && (
          <Badge variant="high" size="xs">
            {high}
          </Badge>
        )}
        {medium > 0 && (
          <Badge variant="medium" size="xs">
            {medium}
          </Badge>
        )}
        {low > 0 && (
          <Badge variant="low" size="xs">
            {low}
          </Badge>
        )}
        {total === 0 && (
          <Badge variant="success" size="xs">
            Clean
          </Badge>
        )}
      </div>
    </motion.div>
  );
};

export default ReportListItem;
