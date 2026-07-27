import { motion } from "framer-motion";
import { SeverityBadge } from "./ReportBadges";
import {
  ClockIcon,
  CodeBracketIcon as CodeIcon,
  ShieldCheckIcon,
  FireIcon,
} from "@heroicons/react/24/outline";

const StatusBadgeInline = ({ status, utils }) => {
  const colorClass = utils.getStatusColor(status);
  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} border`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

export const ReportSummary = ({ report, utils }) => {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        visible: { transition: { staggerChildren: 0.08 } },
      }}
    >
      <motion.div
        variants={{
          hidden: { opacity: 0, y: 15 },
          visible: { opacity: 1, y: 0 },
        }}
        className="glass-container rounded-2xl p-6 mb-8 print:bg-white print:shadow-none print:border print:border-gray-200"
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-6 text-sm text-gray-400 print:text-gray-600">
              <div className="flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                {utils.formatDate(report.created_at)}
              </div>
              <div className="flex items-center">
                <CodeIcon className="h-4 w-4 mr-1" />
                {report.git_metadata?.repository_url}
              </div>
              <div className="flex items-center">
                <span className="text-xs bg-gray-700 print:bg-gray-200 px-2 py-1 rounded print:text-gray-700">
                  {report.git_metadata?.branch || "main"}
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <StatusBadgeInline status={report.status} utils={utils} />
            <div className="mt-2 text-sm text-gray-400 print:text-gray-600">
              Scan ID: {report.scan_id}
            </div>
            {report.duration_seconds && (
              <div className="text-sm text-gray-400 print:text-gray-600">
                Duration: {Math.round(report.duration_seconds)}s
              </div>
            )}
          </div>
        </div>
      </motion.div>

      <motion.div
        variants={{
          hidden: { opacity: 0, y: 15 },
          visible: { opacity: 1, y: 0 },
        }}
        className="space-y-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="glass-container rounded-xl p-6">
            <div className="flex items-center">
              <div className="p-2 rounded-lg bg-cyan-500/20">
                <ShieldCheckIcon className="h-6 w-6 text-cyan-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-400">Total Findings</p>
                <p className="text-2xl font-bold text-white">{report.total_findings || 0}</p>
              </div>
            </div>
          </div>
          {Object.entries(report.findings_by_severity || {}).map(([severity, count]) => (
            <div key={severity} className="glass-container rounded-xl p-6">
              <div className="flex items-center">
                <div className={`p-2 rounded-lg ${utils.getSeverityBgColor(severity)}`}>
                  <FireIcon className={`h-6 w-6 ${utils.getSeverityTextColor(severity)}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-400 capitalize">{severity}</p>
                  <p className="text-2xl font-bold text-white">{count}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Severity Summary */}
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 15 },
            visible: { opacity: 1, y: 0 },
          }}
          className="glass-container rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Severity Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {["critical", "high", "medium", "low", "info"].map((severity) => {
              const count = report.findings_by_severity?.[severity] || 0;
              const total =
                Object.values(report.findings_by_severity || {}).reduce((a, b) => a + b, 0) || 1;
              const percentage = Math.round((count / total) * 100);
              return (
                <div key={severity} className="text-center p-3 bg-gray-800/50 rounded-lg">
                  <SeverityBadge severity={severity} />
                  <div className="mt-2 text-xl font-bold text-white">{count}</div>
                  <div className="text-xs text-gray-500">{percentage}%</div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
};
