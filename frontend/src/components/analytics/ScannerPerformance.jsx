import { motion } from "framer-motion";
import { CpuChipIcon, ClockIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return "N/A";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
};

const ScannerPerformance = ({ scanners = {} }) => {
  const scannerList = Object.entries(scanners).map(([name, stats]) => ({
    name,
    ...stats,
  }));

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
    <motion.div
      className="space-y-3"
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
    >
      {scannerList.slice(0, 6).map((scanner) => {
        const successRate =
          scanner.total_runs > 0
            ? Math.round((scanner.successful_runs / scanner.total_runs) * 100)
            : 0;
        return (
          <motion.div
            key={scanner.name}
            variants={{
              hidden: { opacity: 0, y: 10 },
              show: { opacity: 1, y: 0 },
            }}
            className="p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white capitalize flex items-center gap-2">
                <CpuChipIcon className="h-4 w-4 text-cyan-400" /> {scanner.name}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
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
            <div className="h-1.5 bg-gray-700/50 rounded-full overflow-hidden mb-2">
              <motion.div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${successRate}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
              <div>
                <span className="text-gray-500">Runs:</span> {scanner.total_runs}
              </div>
              <div>
                <span className="text-gray-500">Findings:</span> {scanner.total_findings}
              </div>
              <div className="flex items-center gap-1">
                <ClockIcon className="h-3 w-3 text-gray-500" />{" "}
                {formatDuration(scanner.avg_duration)}
              </div>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default ScannerPerformance;
