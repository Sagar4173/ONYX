import { motion } from "framer-motion";
import { CpuChipIcon } from "@heroicons/react/24/outline";
import { StatusBadge } from "./ReportBadges";

const severityColors = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-cyan-500",
  info: "bg-gray-500",
};

const badgeColors = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const itemAnim = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const ScannerResultCard = ({ scanResult, index: _index }) => {
  const summary = scanResult.summary || {};
  const totalSeverity = Object.values(summary).reduce(
    (a, b) => a + (typeof b === "number" ? b : 0),
    0
  );
  const findingsCount = scanResult.findings_count || totalSeverity || 0;
  const isNonNumericSummary =
    typeof scanResult.summary === "object" &&
    Object.keys(scanResult.summary).length > 0 &&
    Object.values(scanResult.summary).every((v) => typeof v !== "number");

  return (
    <motion.div variants={itemAnim} className="glass-container rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <CpuChipIcon className="h-5 w-5 mr-2 text-cyan-400" />
          {scanResult.scanner}
        </h3>
        <StatusBadge status={scanResult.status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Findings</p>
          <p className="text-xl font-bold text-white">{findingsCount}</p>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Duration</p>
          <p className="text-xl font-bold text-white">
            {scanResult.duration_seconds ? `${Math.round(scanResult.duration_seconds)}s` : "N/A"}
          </p>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Status</p>
          <p className="text-xl font-bold text-white capitalize">{scanResult.status}</p>
        </div>
      </div>

      {totalSeverity > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Severity Breakdown</h4>
          <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden flex">
            {Object.entries(summary).map(([severity, count]) => {
              if (typeof count !== "number" || count === 0) return null;
              const pct = (count / totalSeverity) * 100;
              return (
                <div
                  key={severity}
                  className={`${
                    severityColors[severity.toLowerCase()] || "bg-gray-500"
                  } h-full transition-all`}
                  style={{ width: `${pct}%` }}
                  title={`${severity}: ${count}`}
                />
              );
            })}
          </div>
          <div className="flex flex-wrap gap-3 mt-2">
            {Object.entries(summary).map(([severity, count]) => {
              if (typeof count !== "number" || count === 0) return null;
              const color = severityColors[severity.toLowerCase()] || "bg-gray-500";
              return (
                <span key={severity} className="flex items-center gap-1.5 text-xs">
                  <span className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-gray-400 capitalize">{severity}</span>
                  <span className="text-white font-medium">{count}</span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {isNonNumericSummary && (
        <div className="mb-4">
          <h4 className="text-md font-medium text-white mb-2">Summary</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(scanResult.summary).map(([severity, count]) => (
              <span
                key={severity}
                className={`px-2 py-1 rounded text-sm border ${
                  badgeColors[severity.toLowerCase()] || badgeColors.info
                }`}
              >
                {severity}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {scanResult.error_message && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
          <h4 className="text-md font-medium text-red-400 mb-2">Error</h4>
          <p className="text-red-300">{scanResult.error_message}</p>
        </div>
      )}
    </motion.div>
  );
};

export default ScannerResultCard;
