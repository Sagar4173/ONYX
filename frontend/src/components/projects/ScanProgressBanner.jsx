import { Link } from "react-router-dom";
import { ArrowPathIcon, EyeIcon, PlayIcon, StopIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { CheckCircleIcon, ExclamationCircleIcon } from "@heroicons/react/24/solid";
import { ShieldCheckIcon } from "@heroicons/react/24/outline";

const STAGES = [
  { label: "Initialize", min: 0, max: 10 },
  { label: "Clone", min: 10, max: 20 },
  { label: "SAST", min: 20, max: 35 },
  { label: "Secrets", min: 35, max: 50 },
  { label: "Dependencies", min: 50, max: 70 },
  { label: "Process", min: 70, max: 90 },
  { label: "AI Analysis", min: 90, max: 100 },
];

const ScanFindingsSummary = ({ findings }) => {
  if (!findings) return null;
  const severityConfig = [
    { key: "critical", color: "text-red-400", bgClass: "bg-red-500/20 border-red-500/40" },
    { key: "high", color: "text-orange-400", bgClass: "bg-orange-500/20 border-orange-500/40" },
    { key: "medium", color: "text-yellow-400", bgClass: "bg-yellow-500/20 border-yellow-500/40" },
    { key: "low", color: "text-cyan-400", bgClass: "bg-cyan-500/20 border-cyan-500/40" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4 pt-4 border-t border-gray-700/50">
      <div className="bg-gray-800/50 rounded-xl p-3 text-center border border-gray-700/50">
        <p className="text-2xl font-bold text-white mb-0.5">{findings.total_findings || 0}</p>
        <p className="text-gray-400 text-xs">Total</p>
      </div>
      {severityConfig.map(({ key, color, bgClass }) => (
        <div key={key} className={`rounded-xl p-3 text-center border ${(findings[key] || 0) > 0 ? bgClass : "bg-gray-800/50 border-gray-700/50"}`}>
          <p className={`text-2xl font-bold mb-0.5 ${(findings[key] || 0) > 0 ? color : "text-gray-500"}`}>{findings[key] || 0}</p>
          <p className="text-gray-400 text-xs capitalize">{key}</p>
        </div>
      ))}
    </div>
  );
};

const ScanProgressBanner = ({ activeScan, scanCompleted, scanProgress, projectName, onStopScan, onDismiss, onRunNewScan, isStopping, isStarting }) => {
  if (!activeScan) return null;

  const isCompleted = activeScan.status === "completed";
  const isCancelled = activeScan.status === "cancelled";
  const isFailed = activeScan.status === "failed";
  const done = scanCompleted;

  return (
    <div className={`mb-6 rounded-2xl overflow-hidden shadow-xl transition-all duration-500 ${
      done
        ? isCompleted
          ? "bg-gradient-to-r from-gray-900 via-green-900/30 to-gray-900 border border-green-500/40 shadow-green-500/10"
          : isCancelled
            ? "bg-gradient-to-r from-gray-900 via-yellow-900/30 to-gray-900 border border-yellow-500/40 shadow-yellow-500/10"
            : "bg-gradient-to-r from-gray-900 via-red-900/30 to-gray-900 border border-red-500/40 shadow-red-500/10"
        : "bg-gradient-to-r from-gray-900 via-blue-900/30 to-gray-900 border border-cyan-500/40 shadow-cyan-500/10"
    }`}>
      <div className={`px-6 py-4 border-b ${
        done
          ? isCompleted
            ? "bg-gradient-to-r from-green-600/20 to-emerald-600/20 border-green-500/30"
            : isCancelled
              ? "bg-gradient-to-r from-yellow-600/20 to-amber-600/20 border-yellow-500/30"
              : "bg-gradient-to-r from-red-600/20 to-rose-600/20 border-red-500/30"
          : "bg-gradient-to-r from-cyan-600/20 to-violet-600/20 border-cyan-500/30"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className={`p-3 rounded-xl ${done ? (isCompleted ? "bg-green-500/30" : isCancelled ? "bg-yellow-500/30" : "bg-red-500/30") : "bg-cyan-500/30"}`}>
                {done ? (isCompleted ? <CheckCircleIcon className="h-7 w-7 text-green-400" /> : <ExclamationCircleIcon className="h-7 w-7 text-yellow-400" />) : <ShieldCheckIcon className="h-7 w-7 text-cyan-400" />}
              </div>
              {!done && <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse border-2 border-gray-900" />}
            </div>
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                {done ? (isCompleted ? "Scan Completed Successfully" : isCancelled ? "Scan Cancelled" : "Scan Failed") : "Security Scan in Progress"}
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
                  done
                    ? isCompleted ? "bg-green-500/20 text-green-400 border-green-500/30" : isCancelled ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" : "bg-red-500/20 text-red-400 border-red-500/30"
                    : "bg-green-500/20 text-green-400 border-green-500/30"
                }`}>
                  {done ? activeScan.status?.toUpperCase() : "LIVE"}
                </span>
              </h3>
              <p className={`text-sm mt-0.5 ${done ? "text-gray-300" : "text-cyan-300"}`}>
                {projectName || "Repository"} • {done ? `Completed at ${new Date(activeScan.completed_at).toLocaleTimeString()}` : activeScan?.project_name || "Scanning..."}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {done ? (
              <>
                {isCompleted && activeScan.report_id && (
                  <Link to={`/report/${activeScan.report_id}`} className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 flex items-center space-x-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                    <EyeIcon className="h-5 w-5" />
                    <span className="font-medium">View Report</span>
                  </Link>
                )}
                <button onClick={onDismiss} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900" title="Dismiss">
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </>
            ) : (
              <button onClick={onStopScan} disabled={isStopping} className="px-4 py-2 bg-red-500/20 text-red-400 rounded-xl hover:bg-red-500/30 border border-red-500/30 transition-all flex items-center space-x-2 group focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                <StopIcon className="h-5 w-5 group-hover:scale-110 transition-transform" />
                <span className="font-medium">Stop Scan</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 py-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            {done ? (isCompleted ? <CheckCircleIcon className="h-5 w-5 text-green-400" /> : <ExclamationCircleIcon className="h-5 w-5 text-yellow-400" />) : <ArrowPathIcon className="h-5 w-5 text-cyan-400 animate-spin" />}
            <span className="text-white font-medium">
              {done ? (isCompleted ? `Found ${activeScan.total_findings || 0} security findings` : isCancelled ? "Scan was cancelled by user" : activeScan.error_message || "Scan encountered an error") : activeScan?.current_scanner || "Initializing scan..."}
            </span>
          </div>
          <span className={`text-2xl font-bold ${done ? (isCompleted ? "text-green-400" : "text-yellow-400") : "text-cyan-400"}`}>{scanProgress}%</span>
        </div>

        <div className="relative w-full h-4 bg-gray-800/80 rounded-full overflow-hidden mb-4">
          <div
            className={`absolute inset-0 h-full rounded-full transition-all duration-700 ease-out ${
              done
                ? isCompleted ? "bg-gradient-to-r from-green-600 via-emerald-500 to-green-400" : "bg-gradient-to-r from-yellow-600 via-amber-500 to-yellow-400"
                : "bg-gradient-to-r from-cyan-600 via-violet-500 to-purple-500"
            }`}
            style={{ width: `${Math.max(scanProgress, 2)}%` }}
          />
          {!done && (
            <div className="absolute inset-0 h-full bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full animate-shimmer" style={{ width: `${Math.max(scanProgress, 2)}%` }} />
          )}
        </div>

        <div className="grid grid-cols-7 gap-2 mb-4">
          {STAGES.map((stage, idx) => {
            const isActive = scanProgress >= stage.min && scanProgress < stage.max;
            const isComplete = scanProgress >= stage.max;
            return (
              <div key={idx} className="text-center">
                <div className={`h-1.5 rounded-full mb-2 transition-all duration-300 ${isComplete ? "bg-green-500" : isActive && !done ? "bg-cyan-500 animate-pulse" : "bg-gray-700"}`} />
                <span className={`text-xs font-medium transition-colors ${isComplete ? "text-green-400" : isActive && !done ? "text-cyan-400" : "text-gray-500"}`}>
                  {isComplete ? "✓ " : ""}{stage.label}
                </span>
              </div>
            );
          })}
        </div>

        {done && isCompleted && <ScanFindingsSummary findings={activeScan} />}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-800/50">
          <div className="bg-gray-800/30 rounded-xl p-3">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Scan ID</p>
            <p className="text-gray-300 font-mono text-sm">{activeScan?.scan_id?.slice(0, 12) || "..."}</p>
          </div>
          <div className="bg-gray-800/30 rounded-xl p-3">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Started</p>
            <p className="text-gray-300 text-sm">{activeScan?.started_at ? new Date(activeScan.started_at).toLocaleTimeString() : "Just now"}</p>
          </div>
          <div className="bg-gray-800/30 rounded-xl p-3">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">{done ? "Completed" : "Status"}</p>
            <p className={`text-sm font-medium capitalize ${done ? (isCompleted ? "text-green-400" : "text-yellow-400") : "text-cyan-400"}`}>
              {done && activeScan.completed_at ? new Date(activeScan.completed_at).toLocaleTimeString() : activeScan?.status || "pending"}
            </p>
          </div>
          <div className="bg-gray-800/30 rounded-xl p-3">
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">{done ? "Duration" : "Findings"}</p>
            <p className="text-gray-300 text-sm">
              {done
                ? activeScan.started_at && activeScan.completed_at
                  ? (() => {
                      const duration = Math.round((new Date(activeScan.completed_at).getTime() - new Date(activeScan.started_at).getTime()) / 1000);
                      const absDuration = Math.abs(duration);
                      if (absDuration < 60) return `${absDuration}s`;
                      if (absDuration < 3600) return `${Math.round(absDuration / 60)}m ${absDuration % 60}s`;
                      return `${Math.floor(absDuration / 3600)}h ${Math.round((absDuration % 3600) / 60)}m`;
                    })()
                  : "N/A"
                : activeScan?.total_findings !== undefined ? activeScan.total_findings : "Scanning..."}
            </p>
          </div>
        </div>

        {done && (
          <div className="flex items-center justify-center space-x-4 mt-5 pt-4 border-t border-gray-700/50">
            <button onClick={onRunNewScan} disabled={isStarting} className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50 flex items-center space-x-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
              <PlayIcon className="h-5 w-5" />
              <span>Run New Scan</span>
            </button>
            {isCompleted && activeScan.report_id && (
              <Link to={`/report/${activeScan.report_id}`} className="px-5 py-2.5 bg-gray-700 text-white rounded-xl hover:bg-gray-600 transition-all flex items-center space-x-2">
                <EyeIcon className="h-5 w-5" />
                <span>View Detailed Report</span>
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanProgressBanner;
