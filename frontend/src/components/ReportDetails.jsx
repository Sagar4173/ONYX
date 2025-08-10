/**
 * ReportDetails Component - Shows vulnerability details with AI explanations & code fixes
 */
import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ClockIcon,
  CodeBracketIcon as CodeIcon,
  DocumentIcon,
  LightBulbIcon,
  ClipboardDocumentIcon as ClipboardCopyIcon,
  ArrowTopRightOnSquareIcon as ExternalLinkIcon,
  ArrowPathIcon as RefreshIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  FireIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI, utils } from "../services/api";
import toast from "react-hot-toast";
import Prism from "prismjs";
import "prismjs/themes/prism-tomorrow.css";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-python";
import "prismjs/components/prism-java";
import "prismjs/components/prism-go";
import "prismjs/components/prism-rust";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-json";

const ReportDetails = () => {
  const { reportId } = useParams();
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [expandedFindings, setExpandedFindings] = useState(new Set());
  const [showCodeContext, setShowCodeContext] = useState(new Set());

  // Debug logging
  console.log("ReportDetails - reportId:", reportId, "type:", typeof reportId);

  // Early return if reportId is invalid
  if (!reportId || reportId === "undefined" || reportId === "null") {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="glass-container rounded-2xl p-8 text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">
            Invalid Report ID
          </h2>
          <p className="text-gray-400 mb-6">
            The report ID is missing or invalid. Please select a valid report.
          </p>
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // Fetch report details
  const {
    data: report,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => reportsAPI.getReport(reportId),
    enabled: !!reportId,
    retry: false, // Don't retry on 404 errors
  });

  // Fetch available reports if the main report is not found
  const { data: availableReports } = useQuery({
    queryKey: ["available-reports"],
    queryFn: () => reportsAPI.getReports({ limit: 5 }),
    enabled: isError, // Only fetch when there's an error
  });

  // Fetch AI analysis if available
  const { data: aiAnalysis, isLoading: aiLoading } = useQuery({
    queryKey: ["ai-analysis", reportId],
    queryFn: () => reportsAPI.getAIAnalysis(reportId),
    enabled: !!reportId && report?.has_ai_analysis,
  });

  // Syntax highlighting effect
  useEffect(() => {
    Prism.highlightAll();
  }, [selectedFinding, showCodeContext]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <RefreshIcon className="h-8 w-8 text-gray-400 animate-spin mr-3" />
          <span className="text-gray-500">Loading report details...</span>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="glass-container rounded-2xl p-8 text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">
            Report Not Found
          </h2>
          <p className="text-gray-400 mb-2">
            {error?.message ||
              "The requested report could not be found or is no longer available."}
          </p>
          <p className="text-gray-500 text-sm mb-6">Report ID: {reportId}</p>

          {/* Show available reports if any */}
          {availableReports?.reports?.length > 0 && (
            <div className="mt-8 text-left">
              <h3 className="text-lg font-semibold text-white mb-4">
                Recent Reports Available:
              </h3>
              <div className="space-y-3">
                {availableReports.reports.slice(0, 3).map((availableReport) => (
                  <Link
                    key={availableReport.id}
                    to={`/report/${availableReport.id}`}
                    className="block p-4 bg-gray-800/50 hover:bg-gray-700/50 rounded-lg border border-gray-700/50 transition-colors duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">
                          {availableReport.project_name}
                        </p>
                        <p className="text-gray-400 text-sm">
                          {availableReport.repository_url}
                        </p>
                      </div>
                      <div className="text-right">
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs ${
                            availableReport.status === "completed"
                              ? "bg-green-500/20 text-green-400"
                              : availableReport.status === "running"
                              ? "bg-blue-500/20 text-blue-400"
                              : "bg-gray-500/20 text-gray-400"
                          }`}
                        >
                          {availableReport.status}
                        </span>
                        <p className="text-gray-500 text-xs mt-1">
                          {availableReport.findings_count} findings
                        </p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-center space-x-4 mt-8">
            <Link
              to="/"
              className="inline-flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200"
            >
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Link>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
            >
              <RefreshIcon className="h-4 w-4 mr-2" />
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <DocumentIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">
            Report not found
          </h3>
          <p className="text-gray-500">
            The requested report could not be found.
          </p>
        </div>
      </div>
    );
  }

  // Filter findings by severity
  const filteredFindings = (report.findings || []).filter((finding) => {
    if (severityFilter === "all") return true;
    return finding.severity === severityFilter;
  });

  // Group findings by file
  const findingsByFile = filteredFindings.reduce((acc, finding) => {
    const file = finding.file_path || "Unknown";
    if (!acc[file]) acc[file] = [];
    acc[file].push(finding);
    return acc;
  }, {});

  // Toggle finding expansion
  const toggleFinding = (findingId) => {
    const newExpanded = new Set(expandedFindings);
    if (newExpanded.has(findingId)) {
      newExpanded.delete(findingId);
    } else {
      newExpanded.add(findingId);
    }
    setExpandedFindings(newExpanded);
  };

  // Toggle code context
  const toggleCodeContext = (findingId) => {
    const newShowCode = new Set(showCodeContext);
    if (newShowCode.has(findingId)) {
      newShowCode.delete(findingId);
    } else {
      newShowCode.add(findingId);
    }
    setShowCodeContext(newShowCode);
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        toast.success("Copied to clipboard");
      })
      .catch(() => {
        toast.error("Failed to copy");
      });
  };

  const SeverityBadge = ({ severity, count }) => {
    const colorClass = utils.getSeverityColor(severity);
    const icons = {
      critical: FireIcon,
      high: ExclamationTriangleIcon,
      medium: InformationCircleIcon,
      low: CheckCircleIcon,
    };
    const Icon = icons[severity] || InformationCircleIcon;

    return (
      <div
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass} border`}
      >
        <Icon className="h-4 w-4 mr-1" />
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
        {count && <span className="ml-1">({count})</span>}
      </div>
    );
  };

  const StatusBadge = ({ status }) => {
    const colorClass = utils.getStatusColor(status);
    const icons = {
      completed: CheckCircleIcon,
      running: RefreshIcon,
      pending: ClockIcon,
      failed: XCircleIcon,
    };
    const Icon = icons[status] || ClockIcon;

    return (
      <div
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass} border`}
      >
        <Icon className="h-4 w-4 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </div>
    );
  };

  const CodeBlock = ({ code, language = "javascript", title }) => (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      {title && (
        <div className="px-4 py-2 bg-gray-800 text-gray-200 text-sm font-medium border-b border-gray-700">
          {title}
        </div>
      )}
      <div className="relative">
        <pre className="p-4 overflow-x-auto text-sm">
          <code className={`language-${language}`}>{code}</code>
        </pre>
        <button
          onClick={() => copyToClipboard(code)}
          className="absolute top-2 right-2 p-2 text-gray-400 hover:text-gray-200 bg-gray-800 rounded"
          title="Copy code"
        >
          <ClipboardCopyIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  );

  const FindingCard = ({ finding }) => {
    const isExpanded = expandedFindings.has(finding.id);
    const showCode = showCodeContext.has(finding.id);

    return (
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div
          className="p-6 cursor-pointer hover:bg-gray-50"
          onClick={() => toggleFinding(finding.id)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <SeverityBadge severity={finding.severity} />
                <span className="text-sm text-gray-500">
                  {finding.scanner_type || "Security Scanner"}
                </span>
              </div>

              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {finding.title || finding.rule_id}
              </h3>

              <div className="flex items-center text-sm text-gray-500 space-x-4">
                <span>Line {finding.line_number || "N/A"}</span>
                <span>CWE-{finding.cwe_id || "N/A"}</span>
                {finding.confidence && (
                  <span>Confidence: {finding.confidence}</span>
                )}
              </div>
            </div>

            <ChevronDownIcon
              className={`h-5 w-5 text-gray-400 transform transition-transform ${
                isExpanded ? "rotate-180" : ""
              }`}
            />
          </div>
        </div>

        {isExpanded && (
          <div className="border-t border-gray-200 p-6 bg-gray-50">
            <div className="space-y-6">
              {/* Description */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  Description
                </h4>
                <p className="text-sm text-gray-700">{finding.description}</p>
              </div>

              {/* Code snippet */}
              {finding.code_snippet && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900">
                      Vulnerable Code
                    </h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleCodeContext(finding.id);
                      }}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      {showCode ? "Hide" : "Show"} Context
                    </button>
                  </div>

                  {showCode && (
                    <CodeBlock
                      code={finding.code_snippet}
                      language={utils.getLanguageFromFile(finding.file_path)}
                      title={`${finding.file_path}:${finding.line_number}`}
                    />
                  )}
                </div>
              )}

              {/* AI Analysis */}
              {aiAnalysis?.findings_analysis?.[finding.id] && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <LightBulbIcon className="h-5 w-5 text-blue-500 mr-2" />
                    <h4 className="text-sm font-medium text-blue-900">
                      AI Analysis
                    </h4>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h5 className="text-sm font-medium text-blue-900 mb-1">
                        Impact Assessment
                      </h5>
                      <p className="text-sm text-blue-800">
                        {
                          aiAnalysis.findings_analysis[finding.id]
                            .impact_assessment
                        }
                      </p>
                    </div>

                    <div>
                      <h5 className="text-sm font-medium text-blue-900 mb-1">
                        Remediation Steps
                      </h5>
                      <div className="text-sm text-blue-800">
                        {aiAnalysis.findings_analysis[
                          finding.id
                        ].remediation_steps.map((step, index) => (
                          <div key={index} className="flex items-start mb-1">
                            <span className="text-blue-600 mr-2">
                              {index + 1}.
                            </span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {aiAnalysis.findings_analysis[finding.id].code_fix && (
                      <div>
                        <h5 className="text-sm font-medium text-blue-900 mb-2">
                          Suggested Fix
                        </h5>
                        <CodeBlock
                          code={
                            aiAnalysis.findings_analysis[finding.id].code_fix
                          }
                          language={utils.getLanguageFromFile(
                            finding.file_path
                          )}
                          title="Suggested fix"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* References */}
              {finding.references && finding.references.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">
                    References
                  </h4>
                  <div className="space-y-1">
                    {finding.references.map((ref, index) => (
                      <a
                        key={index}
                        href={ref}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700"
                      >
                        <ExternalLinkIcon className="h-4 w-4 mr-1" />
                        {ref}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Object.entries(report.findings_by_severity || {}).map(
          ([severity, count]) => (
            <div
              key={severity}
              className="bg-white p-6 rounded-lg shadow border"
            >
              <div className="flex items-center">
                <div
                  className={`p-2 rounded-lg ${utils.getSeverityColor(
                    severity
                  )} bg-opacity-10`}
                >
                  <ExclamationTriangleIcon
                    className={`h-6 w-6 ${utils
                      .getSeverityColor(severity)
                      .replace("text-", "text-")}`}
                  />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-600 capitalize">
                    {severity} Issues
                  </p>
                </div>
              </div>
            </div>
          )
        )}
      </div>

      {/* Scan Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Scan Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">Project</dt>
                <dd className="text-sm text-gray-900">{report.project_name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Branch</dt>
                <dd className="text-sm text-gray-900">{report.branch}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Commit</dt>
                <dd className="text-sm text-gray-900 font-mono">
                  {report.commit_hash}
                </dd>
              </div>
            </dl>
          </div>
          <div>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd>
                  <StatusBadge status={report.status} />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Scan Date</dt>
                <dd className="text-sm text-gray-900">
                  {utils.formatDate(report.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Duration</dt>
                <dd className="text-sm text-gray-900">
                  {report.duration_seconds
                    ? utils.formatDuration(report.duration_seconds)
                    : "N/A"}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* AI Analysis Summary */}
      {aiAnalysis && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <LightBulbIcon className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">
              AI Analysis Summary
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Overall Risk Assessment
              </h4>
              <p className="text-sm text-gray-700">
                {aiAnalysis.overall_risk_assessment}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Priority Recommendations
              </h4>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {aiAnalysis.priority_recommendations?.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const FindingsTab = () => (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-700">
              Filter by severity:
            </span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="text-sm text-gray-500">
            Showing {filteredFindings.length} of {report.findings?.length || 0}{" "}
            findings
          </div>
        </div>
      </div>

      {/* Findings by File */}
      <div className="space-y-6">
        {Object.entries(findingsByFile).map(([filePath, findings]) => (
          <div
            key={filePath}
            className="bg-white shadow rounded-lg overflow-hidden"
          >
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  {filePath}
                </h3>
                <span className="text-sm text-gray-500">
                  {findings.length} issue{findings.length !== 1 ? "s" : ""}
                </span>
              </div>
            </div>

            <div className="divide-y divide-gray-200">
              {findings.map((finding) => (
                <FindingCard key={finding.id} finding={finding} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Link
            to="/reports"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back to Reports
          </Link>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {report.project_name}
            </h1>
            <div className="flex items-center space-x-4 mt-2">
              <StatusBadge status={report.status} />
              <span className="text-sm text-gray-500">
                Security Score:{" "}
                {utils.calculateSecurityScore(report.findings_by_severity)}/100
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to={`/compliance/${report.id}`}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <DocumentIcon className="h-4 w-4 mr-2" />
              Generate Compliance Report
            </Link>

            <button
              onClick={() => refetch()}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <RefreshIcon className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "overview"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            Overview
          </button>

          <button
            onClick={() => setActiveTab("findings")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "findings"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            Findings ({report.findings?.length || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && <OverviewTab />}
      {activeTab === "findings" && <FindingsTab />}
    </div>
  );
};

export default ReportDetails;
