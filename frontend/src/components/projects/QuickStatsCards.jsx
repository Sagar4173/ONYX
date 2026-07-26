import { ChartBarIcon, ExclamationTriangleIcon, ShieldCheckIcon, ClockIcon } from "@heroicons/react/24/outline";
import { Card } from "../../styles/components";
import { utils } from "../../services/api";

const StatCard = ({ children, className = "" }) => (
  <Card padding="lg" className={`rounded-2xl ${className}`}>
    {children}
  </Card>
);

const QuickStatsCards = ({ stats, vulnCounts, totalVulns, liveSecurityScore, scanCompleted, onStartScan, hasActiveScan, isStarting }) => (
  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <StatCard className="hover:border-cyan-500/30 transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">Total Scans</p>
          <p className="text-2xl font-bold text-white">
            {(scanCompleted ? (stats.total_scans || 0) + 1 : stats.total_scans) || (scanCompleted ? 1 : 0)}
          </p>
        </div>
        <ChartBarIcon className="h-8 w-8 text-cyan-400" />
      </div>
    </StatCard>

    <StatCard className="hover:border-red-500/30 transition-all group">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">Vulnerabilities</p>
          <p className="text-2xl font-bold text-white">{totalVulns}</p>
          {totalVulns > 0 && (
            <div className="flex items-center space-x-2 mt-1">
              {vulnCounts.critical > 0 && (
                <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">{vulnCounts.critical} critical</span>
              )}
              {vulnCounts.high > 0 && (
                <span className="text-xs px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded">{vulnCounts.high} high</span>
              )}
            </div>
          )}
        </div>
        <ExclamationTriangleIcon className="h-8 w-8 text-red-400 group-hover:scale-110 transition-transform" />
      </div>
    </StatCard>

    <StatCard className="hover:border-green-500/30 transition-all group">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">Security Score</p>
          <p className={`text-2xl font-bold ${(liveSecurityScore ?? stats.security_score ?? 0) >= 80 ? "text-green-400" : (liveSecurityScore ?? stats.security_score ?? 0) >= 60 ? "text-yellow-400" : "text-red-400"}`}>
            {Math.round(liveSecurityScore ?? stats.security_score ?? 0)}
          </p>
          <div className="w-full bg-gray-700/50 rounded-full h-1.5 mt-2">
            <div
              className={`h-1.5 rounded-full transition-all ${(liveSecurityScore ?? stats.security_score ?? 0) >= 80 ? "bg-green-500" : (liveSecurityScore ?? stats.security_score ?? 0) >= 60 ? "bg-yellow-500" : "bg-red-500"}`}
              style={{ width: `${liveSecurityScore ?? stats.security_score ?? 0}%` }}
            />
          </div>
        </div>
        <ShieldCheckIcon className="h-8 w-8 text-green-400 group-hover:scale-110 transition-transform" />
      </div>
    </StatCard>

    <StatCard className="rounded-2xl hover:border-purple-500/30 transition-all group">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">Last Scan</p>
          <p className="text-sm font-medium text-white">
            {scanCompleted ? "Just now" : stats.last_scan_date ? utils.formatRelativeDate(stats.last_scan_date) : "Never"}
          </p>
          {!stats.last_scan_date && !scanCompleted && (
            <button
              onClick={onStartScan}
              disabled={hasActiveScan || isStarting}
              className="mt-2 text-xs text-cyan-400 hover:text-cyan-300 transition-colors disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-inset"
            >
              Run first scan →
            </button>
          )}
        </div>
        <ClockIcon className="h-8 w-8 text-purple-400 group-hover:scale-110 transition-transform" />
      </div>
    </StatCard>
  </div>
);

export default QuickStatsCards;
