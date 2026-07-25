/**
 * Enhanced Report Details Component - Comprehensive security report viewer
 * Unified Security Analysis & Compliance Report
 */
import { useState, useEffect, useRef, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { COMPLIANCE_STANDARDS, getAllFindings, generateViewPDF } from "../../utils/pdfReportGenerator";
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
  ChevronRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  FireIcon,
  ChartBarIcon,
  CpuChipIcon,
  BoltIcon,
  EyeIcon,
  DocumentTextIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  ShieldExclamationIcon,
  RocketLaunchIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI, utils } from "../../services/api";
import toast from "react-hot-toast";
import { PageContainer, PageHeader } from "../../layouts";
import { ReportSummary } from "./ReportSummary";
import { VulnerabilityList } from "./VulnerabilityList";
import { ComplianceMapping } from "./ComplianceMapping";
import { ReportCharts } from "./ReportCharts";
import { ExportDropdown, downloadReport, printReport } from "./ReportExport";
import { AISection } from "./AISection";


const EnhancedReportDetails = () => {
  const { reportId } = useParams();
  const reportRef = useRef();
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [expandedFindings, setExpandedFindings] = useState(new Set());
  const [showCodeContext, setShowCodeContext] = useState(new Set());
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedStandards, setSelectedStandards] = useState(["OWASP", "NIST"]);

  // Map findings to compliance categories
  const mapFindingToCompliance = (finding, standard) => {
    const description = (
      finding.description ||
      finding.title ||
      ""
    ).toLowerCase();
    const categories = [];

    switch (standard) {
      case "OWASP":
        if (
          description.includes("access") ||
          description.includes("authorization") ||
          description.includes("permission")
        ) {
          categories.push("A01");
        }
        if (
          description.includes("crypto") ||
          description.includes("encryption") ||
          description.includes("hash") ||
          description.includes("password")
        ) {
          categories.push("A02");
        }
        if (
          description.includes("injection") ||
          description.includes("sql") ||
          description.includes("xss") ||
          description.includes("command")
        ) {
          categories.push("A03");
        }
        if (
          description.includes("misconfiguration") ||
          description.includes("default") ||
          description.includes("config")
        ) {
          categories.push("A05");
        }
        if (
          description.includes("component") ||
          description.includes("dependency") ||
          description.includes("outdated") ||
          description.includes("vulnerable")
        ) {
          categories.push("A06");
        }
        if (
          description.includes("auth") ||
          description.includes("session") ||
          description.includes("token")
        ) {
          categories.push("A07");
        }
        if (categories.length === 0) categories.push("A05");
        break;
      case "NIST":
        categories.push("ID");
        if (
          description.includes("protect") ||
          description.includes("secure") ||
          description.includes("encrypt")
        ) {
          categories.push("PR");
        }
        if (
          description.includes("detect") ||
          description.includes("monitor") ||
          description.includes("log")
        ) {
          categories.push("DE");
        }
        break;
      case "ISO27001":
        if (
          description.includes("access") ||
          description.includes("authentication")
        ) {
          categories.push("A.9");
        }
        if (
          description.includes("crypto") ||
          description.includes("encryption")
        ) {
          categories.push("A.10");
        }
        if (
          description.includes("development") ||
          description.includes("code")
        ) {
          categories.push("A.14");
        }
        if (categories.length === 0) categories.push("A.12");
        break;
    }
    return categories;
  };

  // Check if reportId is valid
  const isValidReportId =
    reportId && reportId !== "undefined" && reportId !== "null";

  // Fetch report details - hooks must be called unconditionally
  const {
    data: report,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => reportsAPI.getReport(reportId),
    enabled: isValidReportId,
    retry: false,
  });

  // Fetch AI analysis - always try to fetch regardless of has_ai_analysis flag
  const {
    data: aiAnalysis,
    isLoading: aiLoading,
    error: aiError,
  } = useQuery({
    queryKey: ["ai-analysis", reportId],
    queryFn: () => reportsAPI.getAIAnalysis(reportId),
    enabled: isValidReportId && !!report, // Only need reportId and report to exist
    retry: false, // Don't retry if AI analysis isn't available
  });

  // Early return if reportId is invalid - after all hooks
  if (!isValidReportId) {
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

  // Generate comprehensive PDF using extracted utility
  const handleGenerateViewPDF = async () => {
    await generateViewPDF({ report, aiAnalysis, reportId, setIsGenerating, toast });
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
    {
      id: "overview",
      name: "Overview",
      icon: ChartBarIcon,
      desc: "Summary & AI Assessment",
    },
    {
      id: "findings",
      name: "Findings",
      icon: ShieldCheckIcon,
      desc: "Security Issues & Fixes",
    },
    {
      id: "ai-analysis",
      name: "AI Analysis",
      icon: SparklesIcon,
      desc: "Intelligent Insights",
    },
    {
      id: "compliance",
      name: "Compliance",
      icon: DocumentTextIcon,
      desc: "OWASP, NIST, ISO",
    },
    {
      id: "scanners",
      name: "Scanners",
      icon: CpuChipIcon,
      desc: "Tool Results",
    },
  ];

  // Unified SeverityBadge component - consolidated from ComplianceReport
  const SeverityBadge = ({ severity }) => {
    const severityColors = {
      critical: "bg-red-500/20 text-red-400 border-red-500/30",
      high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    };
    const severityIcons = {
      critical: "🔴",
      high: "🟠",
      medium: "🟡",
      low: "🔵",
      info: "⚪",
    };
    const colorClass =
      severityColors[severity?.toLowerCase()] || severityColors.info;
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${colorClass} border shadow-sm`}
      >
        <span>{severityIcons[severity?.toLowerCase()] || "⚪"}</span>
        {severity?.charAt(0).toUpperCase() + severity?.slice(1)}
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
      <div className="max-w-7xl mx-auto print:max-w-none">
        {/* Header - Hidden in print */}
        <div className="no-print">
          <PageHeader
            title="Security Scan Report"
            description={report.project_name}
            icon={DocumentTextIcon}
            breadcrumb={["Reports", report.project_name]}
            actions={
              <div className="flex items-center space-x-2">
                <ExportDropdown reportId={reportId} />

                {/* Primary PDF Download Button */}
                <button
                  onClick={handleGenerateViewPDF}
                  disabled={isGenerating}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 shadow-lg shadow-blue-500/25"
                  title="Download complete PDF report"
                >
                  {isGenerating ? (
                    <RefreshIcon className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <DocumentTextIcon className="h-4 w-4 mr-2" />
                  )}
                  {isGenerating ? "Generating..." : "Download PDF"}
                </button>
              </div>
            }
          />
        </div>
        {/* Print-only Header - Hidden on screen, shown in print */}
        <div className="hidden print:block print:mb-8 print:pb-4 print:border-b-2 print:border-blue-600">
          <div className="print:text-center">
            <h1 className="print:text-2xl print:font-bold print:text-blue-800 print:mb-2">
              🛡️ ONYX Security Report
            </h1>
            <p className="print:text-gray-600 print:text-sm">
              Security Analysis Report for {report.project_name}
            </p>
            <p className="print:text-gray-500 print:text-xs print:mt-1">
              Generated:{" "}
              {new Date().toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}{" "}
              | Report ID: {reportId}
            </p>
          </div>
        </div>
        {/* Main Report Content - Add ref for PDF generation */}
        <div ref={reportRef} className="print:bg-white">
          <div className="glass-container rounded-2xl p-6 mb-8 print:bg-white print:shadow-none print:border print:border-gray-200">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-6 text-sm text-gray-400 print:text-gray-600">
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {utils.formatDate(report.created_at)}
                  </div>
                  <div className="flex items-center">
                    <CodeIcon className="h-4 w-4 mr-1" />
                    {report.git_metadata?.repository_url}
                  </div>
                  <div className="flex items-center">
                    <span className="text-xs bg-gray-700 print:bg-gray-200 px-2 py-1 rounded print:text-gray-700">
                      {report.git_metadata?.branch || "main"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <StatusBadge status={report.status} />
                <div className="mt-2 text-sm text-gray-400 print:text-gray-600">
                  Scan ID: {report.scan_id}
                </div>
                {report.duration_seconds && (
                  <div className="text-sm text-gray-400 print:text-gray-600">
                    Duration: {Math.round(report.duration_seconds)}s
                  </div>
                )}
              </div>
            </div>
          </div>
          {/* Tabs - Hidden in print */}
          <div className="mb-8 no-print">
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
          <div className="space-y-8">
            {activeTab === "overview" && (
              <div className="space-y-6">
                <ReportCharts report={report} />

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
                            <div>
                              Findings: {scanResult.findings_count || 0}
                            </div>
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
                {/* Secret Detection Summary */}
                {(() => {
                  const secretFindings = filteredFindings.filter(
                    (f) =>
                      f.scanner?.toLowerCase() === "gitleaks" ||
                      f.title?.toLowerCase().includes("secret") ||
                      f.title?.toLowerCase().includes("credential")
                  );
                  const placeholderCount = secretFindings.filter(
                    (f) => f.metadata?.is_placeholder
                  ).length;
                  const exampleFileCount = secretFindings.filter(
                    (f) =>
                      f.metadata?.is_example_file && !f.metadata?.is_placeholder
                  ).length;
                  const realSecretCount = secretFindings.filter(
                    (f) => f.metadata?.is_likely_real !== false
                  ).length;

                  if (secretFindings.length > 0) {
                    return (
                      <div className="glass-container rounded-xl p-4 border border-gray-700">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-semibold text-white flex items-center">
                            <ShieldCheckIcon className="h-4 w-4 mr-2 text-purple-400" />
                            Secret Detection Summary
                          </h4>
                          <span className="text-xs text-gray-400">
                            {secretFindings.length} secret-related finding
                            {secretFindings.length !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                          {realSecretCount > 0 && (
                            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold text-red-400">
                                {realSecretCount}
                              </div>
                              <div className="text-xs text-red-300">
                                Likely Real
                              </div>
                              <div className="text-xs text-gray-400 mt-1">
                                Requires Action
                              </div>
                            </div>
                          )}
                          {placeholderCount > 0 && (
                            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold text-blue-400">
                                {placeholderCount}
                              </div>
                              <div className="text-xs text-blue-300">
                                Placeholders
                              </div>
                              <div className="text-xs text-gray-400 mt-1">
                                Example Values
                              </div>
                            </div>
                          )}
                          {exampleFileCount > 0 && (
                            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold text-yellow-400">
                                {exampleFileCount}
                              </div>
                              <div className="text-xs text-yellow-300">
                                In Example Files
                              </div>
                              <div className="text-xs text-gray-400 mt-1">
                                Verify If Real
                              </div>
                            </div>
                          )}
                        </div>
                        {placeholderCount > 0 || exampleFileCount > 0 ? (
                          <p className="text-xs text-gray-400 mt-3 flex items-start">
                            <InformationCircleIcon className="h-4 w-4 mr-1 flex-shrink-0 mt-0.5" />
                            <span>
                              Placeholder credentials in .env.example,
                              README.md, or documentation files are flagged for
                              awareness but typically don't require immediate
                              action. Always verify secrets in example files
                              aren't accidentally real.
                            </span>
                          </p>
                        ) : null}
                      </div>
                    );
                  }
                  return null;
                })()}

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
                      <option
                        value="critical"
                        className="bg-gray-800 text-white"
                      >
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
                    filteredFindings.map((finding, index) => {
                      // Check if this is a placeholder/example credential
                      const isPlaceholder = finding.metadata?.is_placeholder;
                      const isExampleFile = finding.metadata?.is_example_file;
                      const isLikelyReal =
                        finding.metadata?.is_likely_real !== false; // Default to true if not specified
                      const isSecretFinding =
                        finding.scanner?.toLowerCase() === "gitleaks" ||
                        finding.title?.toLowerCase().includes("secret") ||
                        finding.title?.toLowerCase().includes("credential");

                      return (
                        <div
                          key={index}
                          className={`glass-container rounded-xl p-6 ${
                            isSecretFinding && !isLikelyReal
                              ? "border-l-4 border-l-blue-500 bg-blue-900/10"
                              : isSecretFinding && isExampleFile && isLikelyReal
                              ? "border-l-4 border-l-orange-500 bg-orange-900/10"
                              : ""
                          }`}
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2 flex-wrap gap-2">
                                <SeverityBadge severity={finding.severity} />
                                <span className="text-sm text-gray-400">
                                  {finding.scanner}
                                </span>

                                {/* Placeholder/Example Credential Indicator */}
                                {isSecretFinding && !isLikelyReal && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                    <InformationCircleIcon className="h-3 w-3 mr-1" />
                                    {isPlaceholder
                                      ? "Placeholder Credential"
                                      : "Example File"}
                                  </span>
                                )}

                                {/* Warning for real-looking secrets in example files */}
                                {isSecretFinding &&
                                  isLikelyReal &&
                                  isExampleFile && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">
                                      <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                                      Verify - May Be Real
                                    </span>
                                  )}
                              </div>

                              <h4 className="text-lg font-semibold text-white mb-2">
                                {finding.title}
                              </h4>

                              {/* Entropy indicator for secrets */}
                              {isSecretFinding &&
                                finding.metadata?.calculated_entropy && (
                                  <div className="flex items-center text-xs text-gray-400 mb-2">
                                    <span className="mr-2">Entropy:</span>
                                    <div className="flex items-center">
                                      <div className="w-24 h-1.5 bg-gray-700 rounded-full overflow-hidden mr-2">
                                        <div
                                          className={`h-full ${
                                            finding.metadata
                                              .calculated_entropy > 4
                                              ? "bg-red-500"
                                              : finding.metadata
                                                  .calculated_entropy > 3
                                              ? "bg-yellow-500"
                                              : "bg-green-500"
                                          }`}
                                          style={{
                                            width: `${Math.min(
                                              finding.metadata
                                                .calculated_entropy * 15,
                                              100
                                            )}%`,
                                          }}
                                        />
                                      </div>
                                      <span
                                        className={
                                          finding.metadata.calculated_entropy >
                                          4
                                            ? "text-red-400"
                                            : finding.metadata
                                                .calculated_entropy > 3
                                            ? "text-yellow-400"
                                            : "text-green-400"
                                        }
                                      >
                                        {finding.metadata.calculated_entropy.toFixed(
                                          2
                                        )}
                                        {finding.metadata.calculated_entropy > 4
                                          ? " (High - Likely Real)"
                                          : finding.metadata
                                              .calculated_entropy > 3
                                          ? " (Medium)"
                                          : " (Low - Likely Fake)"}
                                      </span>
                                    </div>
                                  </div>
                                )}

                              <p className="text-gray-300 mb-3">
                                {finding.description}
                              </p>

                              {finding.file_path && (
                                <div className="flex items-center text-sm text-gray-400 mb-2">
                                  <DocumentIcon className="h-4 w-4 mr-1" />
                                  {finding.file_path}
                                  {finding.line_number &&
                                    `:${finding.line_number}`}
                                </div>
                              )}

                              {finding.remediation && (
                                <div
                                  className={`mt-4 p-4 rounded-lg ${
                                    isSecretFinding && !isLikelyReal
                                      ? "bg-blue-900/20 border border-blue-500/30"
                                      : "bg-green-900/20 border border-green-500/30"
                                  }`}
                                >
                                  <h5
                                    className={`text-sm font-medium mb-2 flex items-center ${
                                      isSecretFinding && !isLikelyReal
                                        ? "text-blue-400"
                                        : "text-green-400"
                                    }`}
                                  >
                                    <LightBulbIcon className="h-4 w-4 mr-1" />
                                    {isSecretFinding && !isLikelyReal
                                      ? "Context"
                                      : "Remediation"}
                                  </h5>
                                  <p
                                    className={`text-sm whitespace-pre-line ${
                                      isSecretFinding && !isLikelyReal
                                        ? "text-blue-300"
                                        : "text-green-300"
                                    }`}
                                  >
                                    {finding.remediation}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })
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
              <AISection aiAnalysis={aiAnalysis} aiLoading={aiLoading} aiError={aiError} />
            )}

            {activeTab === "remediation" && (
              <div className="space-y-6">
                {/* Remediation Header */}
                <div className="glass-container rounded-xl p-6 bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/30">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                      <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <RocketLaunchIcon className="h-6 w-6 text-green-400" />
                        Remediation Roadmap
                      </h3>
                      <p className="text-gray-400 mt-1">
                        Prioritized action plan to resolve security
                        vulnerabilities
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-400">
                          {
                            getFilteredFindings().filter(
                              (f) =>
                                f.severity === "critical" ||
                                f.severity === "high"
                            ).length
                          }
                        </div>
                        <div className="text-xs text-gray-400">
                          Critical/High
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-400">
                          {
                            getFilteredFindings().filter(
                              (f) => f.severity === "medium"
                            ).length
                          }
                        </div>
                        <div className="text-xs text-gray-400">Medium</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          {
                            getFilteredFindings().filter(
                              (f) =>
                                f.severity === "low" || f.severity === "info"
                            ).length
                          }
                        </div>
                        <div className="text-xs text-gray-400">Low/Info</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Remediation Roadmap */}
                {aiAnalysis?.remediation_roadmap &&
                aiAnalysis.remediation_roadmap.length > 0 ? (
                  <div className="glass-container rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                      <SparklesIcon className="h-5 w-5 text-purple-400" />
                      AI-Generated Remediation Plan
                    </h4>
                    <div className="relative">
                      {/* Timeline line */}
                      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-green-500 via-yellow-500 to-blue-500" />

                      <div className="space-y-6">
                        {aiAnalysis.remediation_roadmap.map((item, idx) => {
                          const priorityColors = {
                            immediate: {
                              bg: "bg-red-500",
                              border: "border-red-500",
                              text: "text-red-400",
                              label: "Immediate",
                            },
                            short_term: {
                              bg: "bg-orange-500",
                              border: "border-orange-500",
                              text: "text-orange-400",
                              label: "Short-term",
                            },
                            medium_term: {
                              bg: "bg-yellow-500",
                              border: "border-yellow-500",
                              text: "text-yellow-400",
                              label: "Medium-term",
                            },
                            long_term: {
                              bg: "bg-blue-500",
                              border: "border-blue-500",
                              text: "text-blue-400",
                              label: "Long-term",
                            },
                          };
                          const priority =
                            priorityColors[item.priority] ||
                            priorityColors.medium_term;

                          return (
                            <div key={idx} className="relative pl-16">
                              {/* Timeline dot */}
                              <div
                                className={`absolute left-4 w-5 h-5 rounded-full ${priority.bg} border-4 border-gray-800`}
                              />

                              <div
                                className={`glass-container rounded-xl p-5 border-l-4 ${priority.border}`}
                              >
                                <div className="flex flex-wrap items-center gap-3 mb-3">
                                  <span
                                    className={`px-2.5 py-1 rounded-full text-xs font-semibold ${priority.bg}/20 ${priority.text}`}
                                  >
                                    {priority.label}
                                  </span>
                                  {item.category && (
                                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400">
                                      {item.category}
                                    </span>
                                  )}
                                  {item.effort && (
                                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400">
                                      ⏱️ {item.effort}
                                    </span>
                                  )}
                                </div>
                                <h5 className="text-white font-semibold mb-2">
                                  {item.action || item.title}
                                </h5>
                                <p className="text-gray-400 text-sm mb-3">
                                  {item.description}
                                </p>
                                {item.impact && (
                                  <div className="flex items-start gap-2 text-sm">
                                    <span className="text-green-400 font-medium">
                                      Impact:
                                    </span>
                                    <span className="text-gray-300">
                                      {item.impact}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="glass-container rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                      <ClockIcon className="h-5 w-5 text-blue-400" />
                      Prioritized Remediation Timeline
                    </h4>
                    <div className="relative">
                      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-red-500 via-yellow-500 to-green-500" />

                      {/* Immediate Priority - Critical/High */}
                      <div className="relative pl-16 pb-8">
                        <div className="absolute left-4 w-5 h-5 rounded-full bg-red-500 border-4 border-gray-800" />
                        <div className="glass-container rounded-xl p-5 border-l-4 border-red-500">
                          <div className="flex items-center gap-3 mb-3">
                            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400">
                              Immediate (0-48 hours)
                            </span>
                            <span className="text-xs text-gray-500">
                              Phase 1
                            </span>
                          </div>
                          <h5 className="text-white font-semibold mb-3">
                            Critical & High Severity Issues
                          </h5>
                          <div className="space-y-2">
                            {getFilteredFindings()
                              .filter(
                                (f) =>
                                  f.severity === "critical" ||
                                  f.severity === "high"
                              )
                              .slice(0, 5)
                              .map((finding, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-start gap-2 text-sm"
                                >
                                  <ExclamationCircleIcon
                                    className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                                      finding.severity === "critical"
                                        ? "text-red-400"
                                        : "text-orange-400"
                                    }`}
                                  />
                                  <span className="text-gray-300">
                                    {finding.title || finding.message}
                                  </span>
                                </div>
                              ))}
                            {getFilteredFindings().filter(
                              (f) =>
                                f.severity === "critical" ||
                                f.severity === "high"
                            ).length > 5 && (
                              <p className="text-xs text-gray-500 pl-6">
                                +
                                {getFilteredFindings().filter(
                                  (f) =>
                                    f.severity === "critical" ||
                                    f.severity === "high"
                                ).length - 5}{" "}
                                more issues
                              </p>
                            )}
                            {getFilteredFindings().filter(
                              (f) =>
                                f.severity === "critical" ||
                                f.severity === "high"
                            ).length === 0 && (
                              <div className="flex items-center gap-2 text-sm text-green-400">
                                <CheckCircleIcon className="h-4 w-4" />
                                No critical or high severity issues found
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Short-term - Medium */}
                      <div className="relative pl-16 pb-8">
                        <div className="absolute left-4 w-5 h-5 rounded-full bg-yellow-500 border-4 border-gray-800" />
                        <div className="glass-container rounded-xl p-5 border-l-4 border-yellow-500">
                          <div className="flex items-center gap-3 mb-3">
                            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-400">
                              Short-term (1-2 weeks)
                            </span>
                            <span className="text-xs text-gray-500">
                              Phase 2
                            </span>
                          </div>
                          <h5 className="text-white font-semibold mb-3">
                            Medium Severity Issues
                          </h5>
                          <div className="space-y-2">
                            {getFilteredFindings()
                              .filter((f) => f.severity === "medium")
                              .slice(0, 5)
                              .map((finding, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-start gap-2 text-sm"
                                >
                                  <ExclamationCircleIcon className="h-4 w-4 mt-0.5 flex-shrink-0 text-yellow-400" />
                                  <span className="text-gray-300">
                                    {finding.title || finding.message}
                                  </span>
                                </div>
                              ))}
                            {getFilteredFindings().filter(
                              (f) => f.severity === "medium"
                            ).length > 5 && (
                              <p className="text-xs text-gray-500 pl-6">
                                +
                                {getFilteredFindings().filter(
                                  (f) => f.severity === "medium"
                                ).length - 5}{" "}
                                more issues
                              </p>
                            )}
                            {getFilteredFindings().filter(
                              (f) => f.severity === "medium"
                            ).length === 0 && (
                              <div className="flex items-center gap-2 text-sm text-green-400">
                                <CheckCircleIcon className="h-4 w-4" />
                                No medium severity issues found
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Long-term - Low/Info */}
                      <div className="relative pl-16">
                        <div className="absolute left-4 w-5 h-5 rounded-full bg-green-500 border-4 border-gray-800" />
                        <div className="glass-container rounded-xl p-5 border-l-4 border-green-500">
                          <div className="flex items-center gap-3 mb-3">
                            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400">
                              Long-term (1+ month)
                            </span>
                            <span className="text-xs text-gray-500">
                              Phase 3
                            </span>
                          </div>
                          <h5 className="text-white font-semibold mb-3">
                            Low Severity & Improvements
                          </h5>
                          <div className="space-y-2">
                            {getFilteredFindings()
                              .filter(
                                (f) =>
                                  f.severity === "low" || f.severity === "info"
                              )
                              .slice(0, 5)
                              .map((finding, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-start gap-2 text-sm"
                                >
                                  <InformationCircleIcon className="h-4 w-4 mt-0.5 flex-shrink-0 text-blue-400" />
                                  <span className="text-gray-300">
                                    {finding.title || finding.message}
                                  </span>
                                </div>
                              ))}
                            {getFilteredFindings().filter(
                              (f) =>
                                f.severity === "low" || f.severity === "info"
                            ).length > 5 && (
                              <p className="text-xs text-gray-500 pl-6">
                                +
                                {getFilteredFindings().filter(
                                  (f) =>
                                    f.severity === "low" ||
                                    f.severity === "info"
                                ).length - 5}{" "}
                                more issues
                              </p>
                            )}
                            {getFilteredFindings().filter(
                              (f) =>
                                f.severity === "low" || f.severity === "info"
                            ).length === 0 && (
                              <div className="flex items-center gap-2 text-sm text-green-400">
                                <CheckCircleIcon className="h-4 w-4" />
                                No low severity issues found
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Best Practices & Quick Wins */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="glass-container rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <SparklesIcon className="h-5 w-5 text-yellow-400" />
                      Quick Wins
                    </h4>
                    <div className="space-y-3">
                      {[
                        "Enable dependency vulnerability scanning in CI/CD",
                        "Add security linting to pre-commit hooks",
                        "Configure SAST tools for automated code review",
                        "Implement secret scanning in repositories",
                      ].map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg"
                        >
                          <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-300 text-sm">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="glass-container rounded-xl p-6">
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <ShieldCheckIcon className="h-5 w-5 text-blue-400" />
                      Security Best Practices
                    </h4>
                    <div className="space-y-3">
                      {[
                        "Implement least privilege access controls",
                        "Enable multi-factor authentication (MFA)",
                        "Conduct regular security training for developers",
                        "Establish incident response procedures",
                      ].map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg"
                        >
                          <LightBulbIcon className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-300 text-sm">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
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
                            <p className="text-gray-300">
                              {scanResult.summary}
                            </p>
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
              <ComplianceMapping
                COMPLIANCE_STANDARDS={COMPLIANCE_STANDARDS}
                selectedStandards={selectedStandards}
                onToggleStandard={(std) => {
                  if (selectedStandards.includes(std)) {
                    setSelectedStandards(selectedStandards.filter((s) => s !== std));
                  } else {
                    setSelectedStandards([...selectedStandards, std]);
                  }
                }}
                getFilteredFindings={getFilteredFindings}
                mapFindingToCompliance={mapFindingToCompliance}
              />
            )}
          </div>{" "}
          {/* End of main content space-y-8 div */}
        </div>{" "}
        {/* End of reportRef div */}
      </div>{" "}
      {/* End of max-w-7xl div */}
    </PageContainer>
  );
};

export default EnhancedReportDetails;
