import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowPathIcon,
  ClockIcon,
  EyeIcon,
  ChartBarIcon,
  ArrowsRightLeftIcon,
} from "@heroicons/react/24/outline";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import { Button, EmptyState } from "../ui/StyleComponents";
import { utils } from "../../services/api";

const ScanStatusBadge = ({ status }) => {
  const config = {
    completed: "bg-green-500/20 text-green-400 border border-green-500/30",
    running: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse",
    pending: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    failed: "bg-red-500/20 text-red-400 border border-red-500/30",
  };
  return (
    <span
      className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${config[status] || config.failed}`}
    >
      {status === "running" && <ArrowPathIcon className="h-3 w-3 animate-spin" />}
      <span className="capitalize">{status}</span>
    </span>
  );
};

const MiniSeverityBar = ({ findings }) => {
  if (!findings) return null;
  const total =
    (findings.critical || 0) +
      (findings.high || 0) +
      (findings.medium || 0) +
      (findings.low || 0) || 1;
  return (
    <div className="flex h-1.5 rounded-full overflow-hidden w-24">
      <div
        style={{
          width: `${((findings.critical || 0) / total) * 100}%`,
          backgroundColor: "#ef4444",
        }}
      />
      <div
        style={{ width: `${((findings.high || 0) / total) * 100}%`, backgroundColor: "#f97316" }}
      />
      <div
        style={{ width: `${((findings.medium || 0) / total) * 100}%`, backgroundColor: "#eab308" }}
      />
      <div
        style={{ width: `${((findings.low || 0) / total) * 100}%`, backgroundColor: "#22d3ee" }}
      />
    </div>
  );
};

const CompareOverlay = ({ scanA, scanB, onClose }) => {
  if (!scanA || !scanB) return null;
  const getFindings = (s) => s.findings_by_severity || {};
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      className="overflow-hidden mb-6"
    >
      <div className="bg-gray-900/80 rounded-xl p-6 border border-cyan-500/30">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <ArrowsRightLeftIcon className="w-5 h-5 text-cyan-400" />
            <span>Scan Comparison</span>
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-sm">
            Close
          </button>
        </div>
        <div className="grid grid-cols-2 gap-6">
          {[scanA, scanB].map((scan, i) => (
            <div key={i} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
              <p className="text-sm text-gray-400 mb-2">Scan #{scan.id?.slice(-8)}</p>
              <div className="space-y-2">
                {["critical", "high", "medium", "low"].map((sev) => {
                  const countA = getFindings(scanA)[sev] || 0;
                  const countB = getFindings(scanB)[sev] || 0;
                  const diff = countB - countA;
                  return (
                    <div key={sev} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-gray-400">{sev}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-white font-mono">
                          {scan === scanA ? countA : countB}
                        </span>
                        {i === 1 && diff !== 0 && (
                          <span
                            className={`text-xs ${diff > 0 ? "text-red-400" : "text-green-400"}`}
                          >
                            {diff > 0 ? `+${diff}` : diff}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

const ScanHistoryTab = ({ scanHistory, scanHistoryLoading, onStartScan, isStarting }) => {
  const [viewMode, setViewMode] = useState("list");
  const [compareIds, setCompareIds] = useState([]);
  const [showCompare, setShowCompare] = useState(false);

  const reports = scanHistory?.reports || [];

  const handleToggleCompare = (id) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  if (scanHistoryLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50 animate-pulse"
          >
            <div className="h-4 bg-gray-700 rounded w-1/4 mb-2" />
            <div className="h-3 bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!reports.length) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Scan History</h3>
          <button
            onClick={onStartScan}
            disabled={isStarting}
            className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg transition-all disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            {isStarting ? "Starting..." : "New Scan"}
          </button>
        </div>
        <EmptyState
          icon={<ChartBarIcon className="h-12 w-12" />}
          title="No Scans Yet"
          description="Start your first security scan to see results here."
          action={
            <Button
              variant="primary"
              onClick={onStartScan}
              disabled={isStarting}
              isLoading={isStarting}
            >
              Start First Scan
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-white">Scan History</h3>
          <div className="flex bg-gray-800/50 rounded-lg p-0.5 border border-gray-700/50">
            <button
              onClick={() => setViewMode("list")}
              className={`px-3 py-1 text-xs rounded-md transition-all ${viewMode === "list" ? "bg-cyan-500/20 text-cyan-400" : "text-gray-400"}`}
            >
              List
            </button>
            <button
              onClick={() => setViewMode("timeline")}
              className={`px-3 py-1 text-xs rounded-md transition-all ${viewMode === "timeline" ? "bg-cyan-500/20 text-cyan-400" : "text-gray-400"}`}
            >
              Timeline
            </button>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {compareIds.length === 2 && (
            <button
              onClick={() => setShowCompare(!showCompare)}
              className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium border border-cyan-500/30 hover:bg-cyan-500/30 transition-all"
            >
              {showCompare ? "Hide Compare" : "Compare Scans"}
            </button>
          )}
          <button
            onClick={onStartScan}
            disabled={isStarting}
            className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg transition-all disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            {isStarting ? "Starting..." : "New Scan"}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {showCompare && compareIds.length === 2 && (
          <CompareOverlay
            scanA={reports.find((r) => r.id === compareIds[0])}
            scanB={reports.find((r) => r.id === compareIds[1])}
            onClose={() => {
              setShowCompare(false);
              setCompareIds([]);
            }}
          />
        )}
      </AnimatePresence>

      <div className={viewMode === "timeline" ? "relative" : "space-y-4"}>
        {viewMode === "timeline" && (
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/30 to-violet-500/30" />
        )}
        {reports.map((scan, index) => (
          <motion.div
            key={scan.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05, type: "spring", damping: 20 }}
            className={viewMode === "timeline" ? "relative flex items-start ml-4" : ""}
          >
            {viewMode === "timeline" && (
              <div
                className={`absolute left-0 w-4 h-4 rounded-full border-2 mt-5 -translate-x-1/2 z-10 ${
                  scan.status === "completed"
                    ? "bg-green-500 border-green-400"
                    : scan.status === "failed"
                      ? "bg-red-500 border-red-400"
                      : "bg-gray-700 border-gray-500"
                }`}
              />
            )}
            <div
              className={`bg-gray-900/50 rounded-xl p-5 border transition-all flex-1 ${
                viewMode === "timeline" ? "ml-10" : ""
              } ${index === 0 && scan.status === "completed" ? "border-green-500/50 ring-1 ring-green-500/20" : "border-gray-700/50 hover:border-gray-600/50"}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="text-white font-medium">Scan #{scan.id?.slice(-8)}</h4>
                    <ScanStatusBadge status={scan.status} />
                    {index === 0 && scan.status === "completed" && (
                      <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full border border-cyan-500/30">
                        Latest
                      </span>
                    )}
                  </div>
                  <div className="flex items-center flex-wrap gap-4 text-sm text-gray-400 mb-2">
                    <span className="flex items-center space-x-1">
                      <ClockIcon className="h-4 w-4" />
                      <span>{utils.formatRelativeDate(scan.created_at)}</span>
                    </span>
                    <span>Branch: {scan.branch || "main"}</span>
                    {scan.duration_seconds && (
                      <span>{utils.formatDuration(scan.duration_seconds)}</span>
                    )}
                  </div>
                  {scan.status === "completed" && (
                    <div className="flex items-center space-x-3">
                      <MiniSeverityBar findings={scan.findings_by_severity} />
                      {(scan.total_findings === 0 ||
                        (!scan.findings_by_severity?.critical &&
                          !scan.findings_by_severity?.high &&
                          !scan.findings_by_severity?.medium &&
                          !scan.findings_by_severity?.low)) && (
                        <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-lg border border-green-500/30 font-medium flex items-center space-x-1">
                          <CheckCircleIcon className="h-3 w-3" />
                          <span>No Issues Found</span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <label
                    className={`p-2 rounded-lg cursor-pointer transition-all ${compareIds.includes(scan.id) ? "bg-cyan-500/20 text-cyan-400" : "text-gray-500 hover:text-gray-300"}`}
                  >
                    <input
                      type="checkbox"
                      checked={compareIds.includes(scan.id)}
                      onChange={() => handleToggleCompare(scan.id)}
                      className="sr-only"
                    />
                    <ArrowsRightLeftIcon className="w-4 h-4" />
                  </label>
                  {scan.status === "completed" && (
                    <Link
                      to={`/report/${scan.id}`}
                      className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default ScanHistoryTab;
