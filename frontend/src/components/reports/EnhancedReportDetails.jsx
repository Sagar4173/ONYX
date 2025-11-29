/**
 * Enhanced Report Details Component - Comprehensive security report viewer
 */
import React, { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { generatePDF } from "../../utils/pdfGenerator";
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
  ArrowDownTrayIcon as DownloadIcon,
  ChartBarIcon,
  CpuChipIcon,
  BoltIcon,
  EyeIcon,
  PrinterIcon,
  DocumentTextIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI, utils } from "../../services/api";
import toast from "react-hot-toast";
import { PageContainer, PageHeader } from "../../layouts";

const EnhancedReportDetails = () => {
  const { reportId } = useParams();
  const reportRef = useRef();
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [expandedFindings, setExpandedFindings] = useState(new Set());
  const [showCodeContext, setShowCodeContext] = useState(new Set());
  const [isGenerating, setIsGenerating] = useState(false);

  // Early return if reportId is invalid
  if (!reportId || reportId === "undefined" || reportId === "null") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
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
    retry: false,
  });

  // Fetch AI analysis if available
  const { data: aiAnalysis, isLoading: aiLoading } = useQuery({
    queryKey: ["ai-analysis", reportId],
    queryFn: () => reportsAPI.getAIAnalysis(reportId),
    enabled: !!reportId && report?.has_ai_analysis,
  });

  // Download report function
  const downloadReport = async (format = "pdf") => {
    try {
      toast.loading("Preparing download...", { id: "download" });

      const response = await fetch(
        `/api/reports/${reportId}/download?format=${format}`
      );

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      const extension =
        format === "csv" ? "csv" : format === "json" ? "json" : "pdf";
      a.download = `security-report-${reportId}.${extension}`;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success("Download completed!", { id: "download" });
    } catch (error) {
      toast.error("Failed to download report. Please try again.", {
        id: "download",
      });
      console.error("Download error:", error);
    }
  };

  // Generate PDF from current view
  const generateViewPDF = async () => {
    if (!reportRef.current) return;

    setIsGenerating(true);
    try {
      await generatePDF(reportRef.current, {
        filename: `security-report-${reportId}.pdf`,
        title: "Security Analysis Report",
        subtitle: report?.scan_type || "Vulnerability Scan",
      });
      toast.success("PDF generated successfully");
    } catch (error) {
      console.error("PDF generation error:", error);
      toast.error("Failed to generate PDF");
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <RefreshIcon className="h-8 w-8 text-blue-400 animate-spin mr-3" />
            <span className="text-gray-400 text-lg">Loading report...</span>
          </div>
        </div>
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="glass-container rounded-2xl p-8 text-center">
            <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">
              Report Not Found
            </h2>
            <p className="text-gray-400 mb-6">
              {error?.message || "The requested report could not be found."}
            </p>
            <div className="flex justify-center space-x-4">
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
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", name: "Overview", icon: ChartBarIcon },
    { id: "findings", name: "Security Findings", icon: ShieldCheckIcon },
    { id: "ai-analysis", name: "AI Analysis", icon: SparklesIcon },
    { id: "scanners", name: "Scanner Results", icon: CpuChipIcon },
    { id: "compliance", name: "Compliance", icon: DocumentTextIcon },
  ];

  const SeverityBadge = ({ severity }) => {
    const colorClass = utils.getSeverityColor(severity);
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} border`}
      >
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
    );
  };

  const StatusBadge = ({ status }) => {
    const colorClass = utils.getStatusColor(status);
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} border`}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  // Filter findings by severity
  const getFilteredFindings = () => {
    let allFindings = [];

    // Try direct findings first
    if (report.findings) {
      allFindings = allFindings.concat(report.findings);
    }
    // Then try scan_results
    else if (report.scan_results) {
      report.scan_results.forEach((scanResult) => {
        if (scanResult.findings) {
          allFindings = allFindings.concat(scanResult.findings);
        }
      });
    }

    if (severityFilter === "all") {
      return allFindings;
    }

    return allFindings.filter((finding) => finding.severity === severityFilter);
  };

  const filteredFindings = getFilteredFindings();

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="Security Scan Report"
          description={report.project_name}
          icon={DocumentTextIcon}
          breadcrumb={["Reports", report.project_name]}
          actions={
            <div className="flex items-center space-x-3">
              <button
                onClick={() => downloadReport("json")}
                className="inline-flex items-center px-3 py-2 border border-gray-600 text-sm font-medium rounded-md text-gray-300 bg-gray-800 hover:bg-gray-700"
              >
                <DownloadIcon className="h-4 w-4 mr-2" />
                JSON
              </button>

              <button
                onClick={() => downloadReport("csv")}
                className="inline-flex items-center px-3 py-2 border border-gray-600 text-sm font-medium rounded-md text-gray-300 bg-gray-800 hover:bg-gray-700"
              >
                <DownloadIcon className="h-4 w-4 mr-2" />
                CSV
              </button>

              <button
                onClick={() => downloadReport("pdf")}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <DownloadIcon className="h-4 w-4 mr-2" />
                PDF Report
              </button>

              <button
                onClick={generateViewPDF}
                disabled={isGenerating}
                className="inline-flex items-center px-3 py-2 border border-gray-600 text-sm font-medium rounded-md text-gray-300 bg-gray-800 hover:bg-gray-700 disabled:opacity-50"
              >
                {isGenerating ? (
                  <RefreshIcon className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <PrinterIcon className="h-4 w-4 mr-2" />
                )}
                {isGenerating ? "Generating..." : "Print View"}
              </button>

              <Link
                to={`/compliance/${reportId}`}
                className="inline-flex items-center px-3 py-2 border border-green-600 text-sm font-medium rounded-md text-green-400 bg-green-900/20 hover:bg-green-900/30"
              >
                <DocumentTextIcon className="h-4 w-4 mr-2" />
                Compliance Report
              </Link>
            </div>
          }
        />

        <div className="glass-container rounded-2xl p-6 mb-8">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center space-x-6 text-sm text-gray-400">
                <div className="flex items-center">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  {utils.formatDate(report.created_at)}
                </div>
                <div className="flex items-center">
                  <CodeIcon className="h-4 w-4 mr-1" />
                  {report.git_metadata?.repository_url}
                </div>
                <div className="flex items-center">
                  <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                    {report.git_metadata?.branch || "main"}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-right">
              <StatusBadge status={report.status} />
              <div className="mt-2 text-sm text-gray-400">
                Scan ID: {report.scan_id}
              </div>
              {report.duration_seconds && (
                <div className="text-sm text-gray-400">
                  Duration: {Math.round(report.duration_seconds)}s
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="glass-container rounded-2xl p-1">
            <nav className="flex space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all duration-200 ${
                      activeTab === tab.id
                        ? "bg-blue-600 text-white shadow-lg"
                        : "text-gray-400 hover:text-gray-300 hover:bg-gray-800/50"
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div ref={reportRef} className="space-y-8">
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Summary Cards */}
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
                    <div
                      key={severity}
                      className="glass-container rounded-xl p-6"
                    >
                      <div className="flex items-center">
                        <div
                          className={`p-2 rounded-lg ${utils.getSeverityBgColor(
                            severity
                          )}`}
                        >
                          <FireIcon
                            className={`h-6 w-6 ${utils.getSeverityTextColor(
                              severity
                            )}`}
                          />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm text-gray-400 capitalize">
                            {severity}
                          </p>
                          <p className="text-2xl font-bold text-white">
                            {count}
                          </p>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>

              {/* AI Analysis Summary */}
              {aiAnalysis && (
                <div className="glass-container rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <SparklesIcon className="h-5 w-5 mr-2 text-purple-400" />
                    AI Risk Assessment
                  </h3>
                  <div className="prose prose-invert max-w-none">
                    <p className="text-gray-300">
                      {aiAnalysis.executive_summary}
                    </p>
                    {aiAnalysis.risk_assessment && (
                      <div className="mt-4 p-4 bg-purple-900/20 border border-purple-500/30 rounded-lg">
                        <p className="text-purple-300">
                          {aiAnalysis.risk_assessment}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Scanner Summary */}
              {report.scan_results && (
                <div className="glass-container rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    Scanner Results
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {report.scan_results.map((scanResult, index) => (
                      <div
                        key={index}
                        className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-white">
                            {scanResult.scanner}
                          </span>
                          <StatusBadge status={scanResult.status} />
                        </div>
                        <div className="text-sm text-gray-400">
                          <div>Findings: {scanResult.findings_count || 0}</div>
                          {scanResult.duration_seconds && (
                            <div>
                              Duration:{" "}
                              {Math.round(scanResult.duration_seconds)}s
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "findings" && (
            <div className="space-y-6">
              {/* Filters */}
              <div className="glass-container rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">
                    Security Findings
                  </h3>
                  <select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                    className="px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white text-sm [&>option]:bg-gray-800 [&>option]:text-white"
                  >
                    <option value="all" className="bg-gray-800 text-white">
                      All Severities
                    </option>
                    <option value="critical" className="bg-gray-800 text-white">
                      Critical
                    </option>
                    <option value="high" className="bg-gray-800 text-white">
                      High
                    </option>
                    <option value="medium" className="bg-gray-800 text-white">
                      Medium
                    </option>
                    <option value="low" className="bg-gray-800 text-white">
                      Low
                    </option>
                    <option value="info" className="bg-gray-800 text-white">
                      Info
                    </option>
                  </select>
                </div>
              </div>

              {/* Findings List */}
              <div className="space-y-4">
                {filteredFindings.length > 0 ? (
                  filteredFindings.map((finding, index) => (
                    <div key={index} className="glass-container rounded-xl p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <SeverityBadge severity={finding.severity} />
                            <span className="text-sm text-gray-400">
                              {finding.scanner}
                            </span>
                          </div>
                          <h4 className="text-lg font-semibold text-white mb-2">
                            {finding.title}
                          </h4>
                          <p className="text-gray-300 mb-3">
                            {finding.description}
                          </p>

                          {finding.file_path && (
                            <div className="flex items-center text-sm text-gray-400 mb-2">
                              <DocumentIcon className="h-4 w-4 mr-1" />
                              {finding.file_path}
                              {finding.line_number && `:${finding.line_number}`}
                            </div>
                          )}

                          {finding.remediation && (
                            <div className="mt-4 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
                              <h5 className="text-sm font-medium text-green-400 mb-2 flex items-center">
                                <LightBulbIcon className="h-4 w-4 mr-1" />
                                Remediation
                              </h5>
                              <p className="text-green-300 text-sm">
                                {finding.remediation}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="glass-container rounded-xl p-8 text-center">
                    <CheckCircleIcon className="h-12 w-12 text-green-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      No Findings
                    </h3>
                    <p className="text-gray-400">
                      {severityFilter === "all"
                        ? "No security findings were detected in this scan."
                        : `No ${severityFilter} severity findings found.`}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "ai-analysis" && (
            <div className="space-y-6">
              {aiLoading ? (
                <div className="glass-container rounded-xl p-8 text-center">
                  <RefreshIcon className="h-8 w-8 text-blue-400 animate-spin mx-auto mb-4" />
                  <p className="text-gray-400">Loading AI analysis...</p>
                </div>
              ) : aiAnalysis ? (
                <>
                  {aiAnalysis.executive_summary && (
                    <div className="glass-container rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Executive Summary
                      </h3>
                      <p className="text-gray-300">
                        {aiAnalysis.executive_summary}
                      </p>
                    </div>
                  )}

                  {aiAnalysis.risk_assessment && (
                    <div className="glass-container rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Risk Assessment
                      </h3>
                      <p className="text-gray-300">
                        {aiAnalysis.risk_assessment}
                      </p>
                    </div>
                  )}

                  {aiAnalysis.priority_findings &&
                    aiAnalysis.priority_findings.length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">
                          Priority Findings
                        </h3>
                        <ul className="space-y-2">
                          {aiAnalysis.priority_findings.map(
                            (finding, index) => (
                              <li key={index} className="flex items-start">
                                <span className="flex-shrink-0 w-6 h-6 bg-red-500 text-white text-xs rounded-full flex items-center justify-center mr-3 mt-0.5">
                                  {index + 1}
                                </span>
                                <span className="text-gray-300">{finding}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {aiAnalysis.recommendations &&
                    aiAnalysis.recommendations.length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">
                          Recommendations
                        </h3>
                        <ul className="space-y-2">
                          {aiAnalysis.recommendations.map(
                            (recommendation, index) => (
                              <li key={index} className="flex items-start">
                                <LightBulbIcon className="h-5 w-5 text-yellow-400 mr-3 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-300">
                                  {recommendation}
                                </span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {aiAnalysis.estimated_fix_time && (
                    <div className="glass-container rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Estimated Fix Time
                      </h3>
                      <p className="text-gray-300">
                        {aiAnalysis.estimated_fix_time}
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="glass-container rounded-xl p-8 text-center">
                  <InformationCircleIcon className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    AI Analysis Not Available
                  </h3>
                  <p className="text-gray-400">
                    AI analysis is not available for this report.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "scanners" && (
            <div className="space-y-6">
              {report.scan_results && report.scan_results.length > 0 ? (
                report.scan_results.map((scanResult, index) => (
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
                        <p className="text-xl font-bold text-white">
                          {scanResult.findings_count || 0}
                        </p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-sm text-gray-400">Duration</p>
                        <p className="text-xl font-bold text-white">
                          {scanResult.duration_seconds
                            ? `${Math.round(scanResult.duration_seconds)}s`
                            : "N/A"}
                        </p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-sm text-gray-400">Status</p>
                        <p className="text-xl font-bold text-white capitalize">
                          {scanResult.status}
                        </p>
                      </div>
                    </div>

                    {scanResult.summary && (
                      <div className="mb-4">
                        <h4 className="text-md font-medium text-white mb-2">
                          Summary
                        </h4>
                        {typeof scanResult.summary === "object" ? (
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(scanResult.summary).map(
                              ([severity, count]) => {
                                const severityColors = {
                                  critical:
                                    "bg-red-500/20 text-red-400 border-red-500/30",
                                  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
                                  medium:
                                    "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                                  low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                  info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
                                };
                                const colorClass =
                                  severityColors[severity.toLowerCase()] ||
                                  severityColors.info;
                                return (
                                  <span
                                    key={severity}
                                    className={`px-2 py-1 rounded text-sm border ${colorClass}`}
                                  >
                                    {severity}: {count}
                                  </span>
                                );
                              }
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-300">{scanResult.summary}</p>
                        )}
                      </div>
                    )}

                    {scanResult.error_message && (
                      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                        <h4 className="text-md font-medium text-red-400 mb-2">
                          Error
                        </h4>
                        <p className="text-red-300">
                          {scanResult.error_message}
                        </p>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="glass-container rounded-xl p-8 text-center">
                  <CpuChipIcon className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    No Scanner Results
                  </h3>
                  <p className="text-gray-400">
                    No detailed scanner results are available for this report.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "compliance" && (
            <div className="glass-container rounded-xl p-6">
              <div className="text-center">
                <DocumentTextIcon className="h-12 w-12 text-blue-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-4">
                  Compliance Analysis
                </h3>
                <p className="text-gray-400 mb-6">
                  For detailed compliance analysis against industry frameworks
                  (OWASP, NIST, ISO27001), use the dedicated compliance report.
                </p>
                <Link
                  to={`/compliance/${reportId}`}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
                >
                  <DocumentTextIcon className="h-4 w-4 mr-2" />
                  View Compliance Report
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  );
};

export default EnhancedReportDetails;
