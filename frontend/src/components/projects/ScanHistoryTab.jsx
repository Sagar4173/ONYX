import { Link } from "react-router-dom";
import { ArrowPathIcon, ClockIcon, EyeIcon, ChartBarIcon } from "@heroicons/react/24/outline";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import { Button, EmptyState } from "../../styles/components";
import { utils } from "../../services/api";

const ScanStatusBadge = ({ status }) => {
  const config = {
    completed: "bg-green-500/20 text-green-400 border border-green-500/30",
    running: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30",
    pending: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    failed: "bg-red-500/20 text-red-400 border border-red-500/30",
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${config[status] || config.failed}`}>
      {status === "running" && <ArrowPathIcon className="h-3 w-3 animate-spin" />}
      <span className="capitalize">{status}</span>
    </span>
  );
};

const FindingsBadge = ({ count, color, label }) => {
  if (!count) return null;
  return <span className={`px-2 py-1 ${color} text-xs rounded-lg border font-medium`}>{count} {label}</span>;
};

const ScanHistoryTab = ({ scanHistory, scanHistoryLoading, onStartScan, isStarting }) => {
  if (scanHistoryLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-1/4 mb-2" />
            <div className="h-3 bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!scanHistory?.reports?.length) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Scan History</h3>
          <button onClick={onStartScan} disabled={isStarting} className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
            {isStarting ? "Starting..." : "New Scan"}
          </button>
        </div>
        <EmptyState
          icon={<ChartBarIcon className="h-12 w-12" />}
          title="No Scans Yet"
          description="Start your first security scan to see results here."
          action={<Button variant="primary" onClick={onStartScan} disabled={isStarting} isLoading={isStarting}>Start First Scan</Button>}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Scan History</h3>
        <button onClick={onStartScan} disabled={isStarting} className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
          {isStarting ? "Starting..." : "New Scan"}
        </button>
      </div>

      <div className="space-y-4">
        {scanHistory.reports.map((scan, index) => (
          <div key={scan.id} className={`bg-gray-900/50 rounded-xl p-6 border transition-all ${index === 0 && scan.status === "completed" ? "border-green-500/50 ring-1 ring-green-500/20" : "border-gray-700/50 hover:border-gray-600/50"}`}>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="text-white font-medium">Scan #{scan.id.slice(-8)}</h4>
                  <ScanStatusBadge status={scan.status} />
                  {index === 0 && scan.status === "completed" && (
                    <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full border border-cyan-500/30">Latest</span>
                  )}
                </div>
                <div className="flex items-center flex-wrap gap-4 text-sm text-gray-400 mb-3">
                  <span className="flex items-center space-x-1">
                    <ClockIcon className="h-4 w-4" />
                    <span>{utils.formatRelativeDate(scan.created_at)}</span>
                  </span>
                  <span>Branch: {scan.branch || "main"}</span>
                  {scan.duration_seconds && <span>Duration: {utils.formatDuration(scan.duration_seconds)}</span>}
                </div>

                {scan.status === "completed" && (
                  <div className="flex items-center space-x-3">
                    <span className="text-gray-500 text-sm">Findings:</span>
                    <FindingsBadge count={scan.findings_by_severity?.critical} color="bg-red-500/20 text-red-400 border-red-500/30" label="Critical" />
                    <FindingsBadge count={scan.findings_by_severity?.high} color="bg-orange-500/20 text-orange-400 border-orange-500/30" label="High" />
                    <FindingsBadge count={scan.findings_by_severity?.medium} color="bg-yellow-500/20 text-yellow-400 border-yellow-500/30" label="Medium" />
                    <FindingsBadge count={scan.findings_by_severity?.low} color="bg-cyan-500/20 text-cyan-400 border-cyan-500/30" label="Low" />
                    {(scan.total_findings === 0 || (!scan.findings_by_severity?.critical && !scan.findings_by_severity?.high && !scan.findings_by_severity?.medium && !scan.findings_by_severity?.low)) && (
                      <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-lg border border-green-500/30 font-medium flex items-center space-x-1">
                        <CheckCircleIcon className="h-3 w-3" />
                        <span>No Issues Found</span>
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-3">
                {scan.status === "completed" && (
                  <Link to={`/report/${scan.id}`} className="px-4 py-2.5 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 flex items-center space-x-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                    <EyeIcon className="h-4 w-4" />
                    <span>View Report</span>
                  </Link>
                )}
                {scan.status === "running" && (
                  <div className="px-4 py-2.5 bg-cyan-500/20 text-cyan-400 rounded-xl flex items-center space-x-2">
                    <ArrowPathIcon className="h-4 w-4 animate-spin" />
                    <span>In Progress...</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScanHistoryTab;
