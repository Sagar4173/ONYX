/**
 * Scan Comparison Component
 * Compare two security scans to show fixed, new, and unchanged vulnerabilities
 * Features: delta analysis, remediation tracking, regression detection
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  ArrowsUpDownIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ArrowRightLeftIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  FunnelIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";

// API Configuration - Production ready with environment variable support
const API_BASE_URL = import.meta.env.DEV
  ? "http://127.0.0.1:8000"
  : import.meta.env.VITE_API_URL || "/api";

// Severity badge component
const SeverityBadge = ({ severity }) => {
  const colors = {
    critical: "bg-red-900/30 text-red-400 border-red-700/50",
    high: "bg-orange-900/30 text-orange-400 border-orange-700/50",
    medium: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
    low: "bg-blue-900/30 text-blue-400 border-blue-700/50",
    info: "bg-gray-700/30 text-gray-300 border-gray-700/50",
  };

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded-full border ${
        colors[severity] || colors.info
      }`}
    >
      {severity?.toUpperCase()}
    </span>
  );
};

// Change type badge
const ChangeTypeBadge = ({ type }) => {
  const config = {
    fixed: {
      color: "bg-green-900/30 text-green-400",
      icon: CheckCircleIcon,
      label: "Fixed",
    },
    new: { color: "bg-red-900/30 text-red-400", icon: XCircleIcon, label: "New" },
    reintroduced: {
      color: "bg-purple-900/30 text-purple-400",
      icon: ArrowPathIcon,
      label: "Reintroduced",
    },
    modified: {
      color: "bg-yellow-900/30 text-yellow-400",
      icon: ArrowsUpDownIcon,
      label: "Modified",
    },
    unchanged: {
      color: "bg-gray-700/30 text-gray-400",
      icon: MinusIcon,
      label: "Unchanged",
    },
  };

  const { color, icon: Icon, label } = config[type] || config.unchanged;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color}`}
    >
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
};

// Finding row component
const FindingRow = ({ finding, changeType, severityChange }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-b border-gray-700/50 last:border-0">
      <div
        className="flex items-center justify-between p-3 hover:bg-gray-800/30 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {expanded ? (
            <ChevronDownIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
          )}
          <ChangeTypeBadge type={changeType} />
          <SeverityBadge severity={finding.severity} />
          <span className="font-medium text-white truncate">
            {finding.title}
          </span>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <span className="hidden md:inline">{finding.scanner}</span>
          <span className="hidden lg:inline truncate max-w-[200px]">
            {finding.file_path}
          </span>
          {severityChange && (
            <span className="text-xs text-yellow-400 bg-yellow-900/30 px-2 py-0.5 rounded">
              {severityChange.from} → {severityChange.to}
            </span>
          )}
        </div>
      </div>

      {expanded && (
        <div className="px-10 pb-3 space-y-2 bg-gray-800/30">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Rule ID:</span>
              <span className="ml-2 font-mono text-gray-200">
                {finding.rule_id}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Line:</span>
              <span className="ml-2">{finding.line}</span>
            </div>
          </div>
          <div className="text-sm">
            <span className="text-gray-400">File:</span>
            <span className="ml-2 font-mono text-gray-200">
              {finding.file_path}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// Summary card component
const SummaryCard = ({ label, value, icon: Icon, color, description }) => {
  const colorClasses = {
    green: "bg-green-900/30 text-green-400 border-green-700/50",
    red: "bg-red-900/30 text-red-400 border-red-700/50",
    purple: "bg-purple-900/30 text-purple-400 border-purple-700/50",
    yellow: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
    gray: "bg-gray-800/30 text-gray-400 border-gray-700/50",
    blue: "bg-blue-900/30 text-blue-400 border-blue-700/50",
  };

  return (
    <div className={`p-4 rounded-xl border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm opacity-80">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
          {description && (
            <p className="text-xs opacity-60 mt-1">{description}</p>
          )}
        </div>
        <Icon className="w-8 h-8 opacity-50" />
      </div>
    </div>
  );
};

// Main component
const ScanComparison = ({
  baseScanId = null,
  compareScanId = null,
  projectId = null,
}) => {
  const [selectedBaseScan, setSelectedBaseScan] = useState(baseScanId);
  const [selectedCompareScan, setSelectedCompareScan] = useState(compareScanId);
  const [activeTab, setActiveTab] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");

  // Fetch comparison data
  const {
    data: comparisonData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["scan-comparison", selectedBaseScan, selectedCompareScan],
    queryFn: async () => {
      if (!selectedBaseScan || !selectedCompareScan) return null;

      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `${API_BASE_URL}/api/enterprise/scans/compare`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
          body: JSON.stringify({
            base_scan_id: selectedBaseScan,
            compare_scan_id: selectedCompareScan,
            include_unchanged: false,
          }),
        }
      );
      if (!response.ok) throw new Error("Failed to compare scans");
      return response.json();
    },
    enabled: !!selectedBaseScan && !!selectedCompareScan,
  });

  // Fetch available scans for selection from real API
  const { data: scansData } = useQuery({
    queryKey: ["available-scans", projectId],
    queryFn: async () => {
      const token = localStorage.getItem("access_token");
      // Fetch real scan history from reports API
      const response = await fetch(
        `${API_BASE_URL}/api/reports?project_id=${
          projectId || ""
        }&limit=50&sort_by=created_at&sort_order=desc`,
        {
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );
      if (!response.ok) {
        throw new Error("Failed to fetch scans");
      }
      const data = await response.json();
      // Transform reports to scan format
      const scans = (data.reports || []).map((report) => ({
        id: report.id || report._id,
        timestamp: report.created_at,
        branch: report.branch || report.repository_branch || "main",
        findings:
          report.total_findings ||
          Object.values(report.findings_by_severity || {}).reduce(
            (a, b) => a + b,
            0
          ) ||
          0,
        status: report.status,
        scan_type: report.scan_type,
      }));
      return { scans };
    },
    enabled: true, // Always try to fetch
  });

  const data = comparisonData?.data || {};
  const summary = data.summary || {};
  const details = data.details || {};

  // Filter findings based on active tab and severity
  const getFilteredFindings = () => {
    let findings = [];

    if (activeTab === "all" || activeTab === "fixed") {
      findings = [
        ...findings,
        ...(details.fixed || []).map((f) => ({ ...f, _changeType: "fixed" })),
      ];
    }
    if (activeTab === "all" || activeTab === "new") {
      findings = [
        ...findings,
        ...(details.new || []).map((f) => ({ ...f, _changeType: "new" })),
      ];
    }
    if (activeTab === "all" || activeTab === "reintroduced") {
      findings = [
        ...findings,
        ...(details.reintroduced || []).map((f) => ({
          ...f,
          _changeType: "reintroduced",
        })),
      ];
    }
    if (activeTab === "modified") {
      findings = [
        ...findings,
        ...(details.modified || []).map((f) => ({
          ...f,
          _changeType: "modified",
        })),
      ];
    }

    if (severityFilter !== "all") {
      findings = findings.filter((f) => f.finding?.severity === severityFilter);
    }

    return findings;
  };

  const filteredFindings = getFilteredFindings();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Scan Comparison</h2>
          <p className="text-gray-400">
            Compare security scans to track remediation progress
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={!selectedBaseScan || !selectedCompareScan}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
            <ArrowPathIcon className="w-4 h-4" />
          Compare
        </button>
      </div>

      {/* Scan Selector */}
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-200 mb-2">
              Base Scan (Older)
            </label>
            <select
              value={selectedBaseScan || ""}
              onChange={(e) => setSelectedBaseScan(e.target.value)}
              className="w-full px-3 py-2 border border-gray-700/50 rounded-lg focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white"
            >
              <option value="">Select base scan...</option>
              {scansData?.scans?.map((scan) => (
                <option key={scan.id} value={scan.id}>
                  {new Date(scan.timestamp).toLocaleDateString()} -{" "}
                  {scan.branch} ({scan.findings} findings)
                </option>
              ))}
            </select>
          </div>

          <ArrowRightIcon className="w-6 h-6 text-gray-400 flex-shrink-0 mt-6" />

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-200 mb-2">
              Compare Scan (Newer)
            </label>
            <select
              value={selectedCompareScan || ""}
              onChange={(e) => setSelectedCompareScan(e.target.value)}
              className="w-full px-3 py-2 border border-gray-700/50 rounded-lg focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white"
            >
              <option value="">Select compare scan...</option>
              {scansData?.scans?.map((scan) => (
                <option key={scan.id} value={scan.id}>
                  {new Date(scan.timestamp).toLocaleDateString()} -{" "}
                  {scan.branch} ({scan.findings} findings)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <ArrowPathIcon className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-4 text-red-400">
          <ExclamationTriangleIcon className="w-5 h-5 inline mr-2" />
          Error comparing scans: {error.message}
        </div>
      )}

      {data.summary && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <SummaryCard
              label="Fixed"
              value={summary.fixed || 0}
              icon={CheckCircleIcon}
              color="green"
              description="Vulnerabilities remediated"
            />
            <SummaryCard
              label="New"
              value={summary.new || 0}
              icon={XCircleIcon}
              color="red"
              description="Newly introduced"
            />
            <SummaryCard
              label="Reintroduced"
              value={summary.reintroduced || 0}
              icon={ArrowPathIcon}
              color="purple"
              description="Previously fixed, now back"
            />
            <SummaryCard
              label="Modified"
              value={summary.modified || 0}
              icon={ArrowsUpDownIcon}
              color="yellow"
              description="Severity changed"
            />
            <SummaryCard
              label="Net Change"
              value={
                summary.net_change > 0
                  ? `+${summary.net_change}`
                  : summary.net_change
              }
              icon={summary.net_change <= 0 ? ArrowTrendingDownIcon : ArrowTrendingUpIcon}
              color={summary.net_change <= 0 ? "green" : "red"}
              description="New - Fixed"
            />
            <SummaryCard
              label="Improvement"
              value={summary.improvement_score?.toFixed(1) || 0}
              icon={summary.improvement_score >= 0 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon}
              color={summary.improvement_score >= 0 ? "blue" : "red"}
              description="Weighted score"
            />
          </div>

          {/* Scan Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
              <h4 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
                <DocumentTextIcon className="w-4 h-4" />
                Base Scan
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Date:</span>
                  <span>
                    {data.base_scan?.timestamp
                      ? new Date(data.base_scan.timestamp).toLocaleString()
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Branch:</span>
                  <span className="flex items-center gap-1">
                    <ArrowRightLeftIcon className="w-3 h-3" />
                    {data.base_scan?.branch || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Findings:</span>
                  <span className="font-medium">
                    {data.base_scan?.total_findings || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
              <h4 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
                <DocumentTextIcon className="w-4 h-4" />
                Compare Scan
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Date:</span>
                  <span>
                    {data.compare_scan?.timestamp
                      ? new Date(data.compare_scan.timestamp).toLocaleString()
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Branch:</span>
                  <span className="flex items-center gap-1">
                    <ArrowRightLeftIcon className="w-3 h-3" />
                    {data.compare_scan?.branch || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Findings:</span>
                  <span className="font-medium">
                    {data.compare_scan?.total_findings || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Analysis Insights */}
          {data.analysis && (
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-xl p-4">
              <h4 className="font-medium text-blue-300 mb-2">
                {data.analysis.summary}
              </h4>

              {data.analysis.highlights?.length > 0 && (
                <div className="mb-3">
                  <p className="text-sm text-blue-300 font-medium mb-1">
                    Highlights:
                  </p>
                  <ul className="text-sm text-blue-300 space-y-1">
                    {data.analysis.highlights.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
              )}

              {data.analysis.recommendations?.length > 0 && (
                <div>
                  <p className="text-sm text-blue-300 font-medium mb-1">
                    Recommendations:
                  </p>
                  <ul className="text-sm text-blue-300 space-y-1">
                    {data.analysis.recommendations.map((r, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <ArrowRightIcon className="w-3 h-3 mt-1 flex-shrink-0" />
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Findings List */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl">
            {/* Tabs */}
            <div className="flex items-center gap-2 p-4 border-b border-gray-700/50 overflow-x-auto">
              {[
                {
                  key: "all",
                  label: "All Changes",
                  count:
                    (summary.fixed || 0) +
                    (summary.new || 0) +
                    (summary.reintroduced || 0),
                },
                { key: "fixed", label: "Fixed", count: summary.fixed || 0 },
                { key: "new", label: "New", count: summary.new || 0 },
                {
                  key: "reintroduced",
                  label: "Reintroduced",
                  count: summary.reintroduced || 0,
                },
                {
                  key: "modified",
                  label: "Modified",
                  count: summary.modified || 0,
                },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap ${
                    activeTab === tab.key
                      ? "bg-blue-900/30 text-blue-400"
                      : "text-gray-400 hover:bg-gray-800/30"
                  }`}
                >
                  {tab.label}
                  <span className="ml-2 px-2 py-0.5 text-xs bg-gray-700/50 rounded-full">
                    {tab.count}
                  </span>
                </button>
              ))}

              <div className="ml-auto flex items-center gap-2">
                <FunnelIcon className="w-4 h-4 text-gray-400" />
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="text-sm border border-gray-700/50 rounded-lg px-2 py-1 bg-gray-800 text-white"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            {/* Findings */}
            <div className="max-h-[500px] overflow-y-auto">
              {filteredFindings.length === 0 ? (
                <div className="text-center text-gray-400 py-12">
                  No findings match the current filters
                </div>
              ) : (
                filteredFindings.map((item, index) => (
                  <FindingRow
                    key={index}
                    finding={item.finding}
                    changeType={item._changeType || item.change_type}
                    severityChange={item.severity_change}
                  />
                ))
              )}
            </div>
          </div>

          {/* Export Button */}
          <div className="flex justify-end">
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-700/50 rounded-lg hover:bg-gray-800/30">
              <ArrowDownTrayIcon className="w-4 h-4" />
              Export Comparison Report
            </button>
          </div>
        </>
      )}

      {!data.summary && !isLoading && !error && (
        <div className="text-center py-12 bg-gray-800/30 rounded-xl">
          <ArrowsUpDownIcon className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Select two scans to compare</p>
        </div>
      )}
    </div>
  );
};

export default ScanComparison;
