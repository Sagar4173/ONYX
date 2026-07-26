import { CpuChipIcon } from "@heroicons/react/24/outline";
import { StatusBadge } from "./ReportBadges";

const ScannerResultCard = ({ scanResult, index }) => {
  return (
    <div key={index} className="glass-container rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <CpuChipIcon className="h-5 w-5 mr-2" />
          {scanResult.scanner}
        </h3>
        <StatusBadge status={scanResult.status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Findings</p>
          <p className="text-xl font-bold text-white">{scanResult.findings_count || 0}</p>
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

      {scanResult.summary && (
        <div className="mb-4">
          <h4 className="text-md font-medium text-white mb-2">Summary</h4>
          {typeof scanResult.summary === "object" ? (
            <div className="flex flex-wrap gap-2">
              {Object.entries(scanResult.summary).map(([severity, count]) => {
                const severityColors = {
                  critical: "bg-red-500/20 text-red-400 border-red-500/30",
                  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
                  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                  low: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                  info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
                };
                const colorClass = severityColors[severity.toLowerCase()] || severityColors.info;
                return (
                  <span key={severity} className={`px-2 py-1 rounded text-sm border ${colorClass}`}>
                    {severity}: {count}
                  </span>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-300">{scanResult.summary}</p>
          )}
        </div>
      )}

      {scanResult.error_message && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
          <h4 className="text-md font-medium text-red-400 mb-2">Error</h4>
          <p className="text-red-300">{scanResult.error_message}</p>
        </div>
      )}
    </div>
  );
};

export default ScannerResultCard;
