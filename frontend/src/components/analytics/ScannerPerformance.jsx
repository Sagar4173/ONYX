import { CpuChipIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return "N/A";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
};

const ScannerPerformance = ({ scanners = {} }) => {
  const scannerList = Object.entries(scanners).map(([name, stats]) => ({ name, ...stats }));

  if (scannerList.length === 0) {
    return (
      <EmptyState
        icon={CpuChipIcon}
        title="No Scanner Data"
        description="Run scans to see scanner performance"
      />
    );
  }

  return (
    <div className="space-y-3">
      {scannerList.slice(0, 6).map((scanner) => {
        const successRate =
          scanner.total_runs > 0
            ? Math.round((scanner.successful_runs / scanner.total_runs) * 100)
            : 0;
        return (
          <div
            key={scanner.name}
            className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/30"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white capitalize">{scanner.name}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  successRate >= 90
                    ? "bg-green-500/20 text-green-400"
                    : successRate >= 70
                      ? "bg-yellow-500/20 text-yellow-400"
                      : "bg-red-500/20 text-red-400"
                }`}
              >
                {successRate}% success
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
              <div>
                <span className="text-gray-500">Runs:</span> {scanner.total_runs}
              </div>
              <div>
                <span className="text-gray-500">Findings:</span> {scanner.total_findings}
              </div>
              <div>
                <span className="text-gray-500">Avg:</span> {formatDuration(scanner.avg_duration)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ScannerPerformance;
