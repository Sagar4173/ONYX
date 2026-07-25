import { SparklesIcon, ShieldCheckIcon, FireIcon, ChartBarIcon } from "@heroicons/react/24/outline";
import { utils } from "../../services/api";

export const ReportCharts = ({ report, aiAnalysis }) => {

  return (
    <div className="space-y-6">
      {report && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-container rounded-xl p-6">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <ShieldCheckIcon className="h-6 w-6 text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-400">Total Findings</p>
              <p className="text-2xl font-bold text-white">
                {report.total_findings || 0}
              </p>
            </div>
          </div>
        </div>

        {Object.entries(report.findings_by_severity || {}).map(
          ([severity, count]) => (
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
          )
        )}
      </div>
      )}

      {aiAnalysis && (
        <>
          {/* Security Score Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-container rounded-xl p-6 text-center">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Security Score</h4>
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-gray-700" />
                  <circle
                    cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent"
                    className={(aiAnalysis.security_score || 0) >= 80 ? "text-green-500" : (aiAnalysis.security_score || 0) >= 50 ? "text-yellow-500" : "text-red-500"}
                    strokeDasharray={`${(aiAnalysis.security_score || 0) * 2.51} 251`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute text-2xl font-bold text-white">{aiAnalysis.security_score || "N/A"}</span>
              </div>
              <p className="text-xs text-gray-500 mt-2">out of 100</p>
            </div>

            <div className="glass-container rounded-xl p-6 text-center">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Risk Level</h4>
              <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full border-4 ${
                aiAnalysis.risk_level === "critical" ? "border-red-500 text-red-400" :
                aiAnalysis.risk_level === "high" ? "border-orange-500 text-orange-400" :
                aiAnalysis.risk_level === "medium" ? "border-yellow-500 text-yellow-400" :
                "border-green-500 text-green-400"
              }`}>
                <span className="text-lg font-bold capitalize">{aiAnalysis.risk_level || "Unknown"}</span>
              </div>
              {aiAnalysis.risk_score && (
                <p className="text-xs text-gray-500 mt-2">Risk Score: {aiAnalysis.risk_score}</p>
              )}
            </div>
          </div>

          {/* Threat Categories */}
          {aiAnalysis.threat_categories && Object.keys(aiAnalysis.threat_categories).length > 0 && (
            <div className="glass-container rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-2 text-orange-400" />
                Threat Categories
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(aiAnalysis.threat_categories).map(([category, count]) => (
                  <div key={category} className="bg-gray-800/50 rounded-xl p-4 text-center border border-gray-700/30">
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-sm text-gray-400 capitalize mt-1">{category.replace(/_/g, " ")}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
