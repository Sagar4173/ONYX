/**
 * Enhanced Report Details Component - Comprehensive security report viewer
 * Unified Security Analysis & Compliance Report
 */
import { useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { COMPLIANCE_STANDARDS, generateViewPDF } from "../../utils/pdfReportGenerator";
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ClockIcon,
  CodeBracketIcon as CodeIcon,
  ArrowPathIcon as RefreshIcon,
  CheckCircleIcon,
  ChartBarIcon,
  CpuChipIcon,
  DocumentTextIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI, utils } from "../../services/api";
import toast from "react-hot-toast";
import { PageContainer, PageHeader } from "../../layouts";

import { VulnerabilityList } from "./VulnerabilityList";
import { ComplianceMapping } from "./ComplianceMapping";
import { ReportCharts } from "./ReportCharts";
import { ExportDropdown } from "./ReportExport";
import { AISection } from "./AISection";
import { StatusBadge } from "./ReportBadges";
import RemediationRoadmap from "./RemediationRoadmap";
import SecretDetectionSummary from "./SecretDetectionSummary";
import FindingCard from "./FindingCard";
import ScannerResultCard from "./ScannerResultCard";

const EnhancedReportDetails = () => {
  const { reportId } = useParams();
  const reportRef = useRef();
  const [_selectedFinding, _setSelectedFinding] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [_expandedFindings, _setExpandedFindings] = useState(new Set());
  const [_showCodeContext, _setShowCodeContext] = useState(new Set());
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedStandards, setSelectedStandards] = useState(["OWASP", "NIST"]);

  // Map findings to compliance categories
  const mapFindingToCompliance = (finding, standard) => {
    const description = (finding.description || finding.title || "").toLowerCase();
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
        if (description.includes("access") || description.includes("authentication")) {
          categories.push("A.9");
        }
        if (description.includes("crypto") || description.includes("encryption")) {
          categories.push("A.10");
        }
        if (description.includes("development") || description.includes("code")) {
          categories.push("A.14");
        }
        if (categories.length === 0) categories.push("A.12");
        break;
    }
    return categories;
  };

  // Check if reportId is valid
  const isValidReportId = reportId && reportId !== "undefined" && reportId !== "null";

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
            <h2 className="text-2xl font-bold text-white mb-2">Invalid Report ID</h2>
            <p className="text-gray-400 mb-6">
              The report ID is missing or invalid. Please select a valid report.
            </p>
            <Link
              to="/"
              className="inline-flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
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
            <RefreshIcon className="h-8 w-8 text-cyan-400 animate-spin mr-3" />
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
            <h2 className="text-2xl font-bold text-white mb-2">Report Not Found</h2>
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
                className="inline-flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
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
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium disabled:opacity-50 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
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
        <div className="hidden print:block print:mb-8 print:pb-4 print:border-b-2 print:border-cyan-600">
          <div className="print:text-center">
            <h1 className="print:text-2xl print:font-bold print:text-cyan-800 print:mb-2">
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
                      className={`flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                        activeTab === tab.id
                          ? "bg-gradient-to-r from-cyan-500 to-violet-500 text-white shadow-lg"
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
                      <p className="text-gray-300">{aiAnalysis.executive_summary}</p>
                      {aiAnalysis.risk_assessment && (
                        <div className="mt-4 p-4 bg-purple-900/20 border border-purple-500/30 rounded-lg">
                          <p className="text-purple-300">{aiAnalysis.risk_assessment}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Scanner Summary */}
                {report.scan_results && (
                  <div className="glass-container rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Scanner Results</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {report.scan_results.map((scanResult, index) => (
                        <div
                          key={index}
                          className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-white">{scanResult.scanner}</span>
                            <StatusBadge status={scanResult.status} />
                          </div>
                          <div className="text-sm text-gray-400">
                            <div>Findings: {scanResult.findings_count || 0}</div>
                            {scanResult.duration_seconds && (
                              <div>Duration: {Math.round(scanResult.duration_seconds)}s</div>
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
                <SecretDetectionSummary filteredFindings={filteredFindings} />

                {/* Filters */}
                <div className="glass-container rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">Security Findings</h3>
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
                      <FindingCard key={index} finding={finding} index={index} />
                    ))
                  ) : (
                    <div className="glass-container rounded-xl p-8 text-center">
                      <CheckCircleIcon className="h-12 w-12 text-green-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-white mb-2">No Findings</h3>
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
              <RemediationRoadmap
                aiAnalysis={aiAnalysis}
                getFilteredFindings={getFilteredFindings}
              />
            )}
            {activeTab === "scanners" && (
              <div className="space-y-6">
                {report.scan_results && report.scan_results.length > 0 ? (
                  report.scan_results.map((scanResult, index) => (
                    <ScannerResultCard key={index} scanResult={scanResult} index={index} />
                  ))
                ) : (
                  <div className="glass-container rounded-xl p-8 text-center">
                    <CpuChipIcon className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">No Scanner Results</h3>
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
