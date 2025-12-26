/**
 * Enhanced Report Details Component - Comprehensive security report viewer
 * Unified Security Analysis & Compliance Report
 */
import React, { useState, useEffect, useRef, useMemo } from "react";
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
  ArrowTrendingUpIcon,
  ShieldExclamationIcon,
  RocketLaunchIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI, utils } from "../../services/api";
import toast from "react-hot-toast";
import { PageContainer, PageHeader } from "../../layouts";

// Compliance Standards Configuration - Unified from ComplianceReport (now deprecated)
const COMPLIANCE_STANDARDS = {
  OWASP: {
    name: "OWASP Top 10",
    version: "2021",
    icon: "🔐",
    description: "Open Web Application Security Project Top 10 Security Risks",
    categories: {
      A01: "Broken Access Control",
      A02: "Cryptographic Failures",
      A03: "Injection",
      A04: "Insecure Design",
      A05: "Security Misconfiguration",
      A06: "Vulnerable and Outdated Components",
      A07: "Identification and Authentication Failures",
      A08: "Software and Data Integrity Failures",
      A09: "Security Logging and Monitoring Failures",
      A10: "Server-Side Request Forgery (SSRF)",
    },
  },
  NIST: {
    name: "NIST Cybersecurity Framework",
    version: "1.1",
    icon: "🏛️",
    description:
      "National Institute of Standards and Technology Cybersecurity Framework",
    categories: {
      ID: "Identify",
      PR: "Protect",
      DE: "Detect",
      RS: "Respond",
      RC: "Recover",
    },
  },
  ISO27001: {
    name: "ISO/IEC 27001",
    version: "2013",
    icon: "📋",
    description: "Information Security Management Systems Requirements",
    categories: {
      "A.8": "Asset Management",
      "A.9": "Access Control",
      "A.10": "Cryptography",
      "A.11": "Physical and Environmental Security",
      "A.12": "Operations Security",
      "A.13": "Communications Security",
      "A.14": "System Acquisition, Development and Maintenance",
      "A.15": "Supplier Relationships",
      "A.16": "Information Security Incident Management",
      "A.17": "Information Security Aspects of Business Continuity Management",
      "A.18": "Compliance",
    },
  },
  PCI_DSS: {
    name: "PCI DSS",
    version: "4.0",
    icon: "💳",
    description: "Payment Card Industry Data Security Standard",
    categories: {
      1: "Install and maintain network security controls",
      2: "Apply secure configurations to all system components",
      3: "Protect stored account data",
      4: "Protect cardholder data with strong cryptography",
      5: "Protect all systems against malware",
      6: "Develop and maintain secure systems and software",
      7: "Restrict access to system components and cardholder data",
      8: "Identify users and authenticate access",
      9: "Restrict physical access to cardholder data",
      10: "Log and monitor all access to system components",
      11: "Test security of systems and networks regularly",
      12: "Support information security with organizational policies",
    },
  },
};

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

  // Download report function
  const downloadReport = async (format = "pdf") => {
    try {
      toast.loading("Preparing download...", { id: "download" });

      // Get the auth token for authenticated download
      const token = localStorage.getItem("access_token");

      // Use the proper API base URL (same as axios config)
      const API_BASE_URL = import.meta.env.DEV
        ? "http://127.0.0.1:8000/api"
        : import.meta.env.VITE_API_URL ||
          import.meta.env.VITE_API_BASE_URL ||
          "/api";

      const response = await fetch(
        `${API_BASE_URL}/reports/${reportId}/download?format=${format}`,
        {
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication required. Please log in again.");
        } else if (response.status === 403) {
          throw new Error("Access denied to this report.");
        }
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
      toast.error(
        error.message || "Failed to download report. Please try again.",
        {
          id: "download",
        }
      );
      console.error("Download error:", error);
    }
  };

  // Generate PDF from current view with enhanced options
  const generateViewPDF = async () => {
    if (!reportRef.current) return;

    setIsGenerating(true);
    try {
      // Calculate total findings
      let totalFindings = 0;
      if (report?.findings) {
        totalFindings = report.findings.length;
      } else if (report?.scan_results) {
        report.scan_results.forEach((sr) => {
          if (sr.findings) totalFindings += sr.findings.length;
        });
      }

      // Prepare report data for PDF executive summary
      const reportData = {
        totalFindings: totalFindings,
        critical: report?.findings_by_severity?.critical || 0,
        high: report?.findings_by_severity?.high || 0,
        medium: report?.findings_by_severity?.medium || 0,
        low: report?.findings_by_severity?.low || 0,
        info: report?.findings_by_severity?.info || 0,
        riskScore:
          aiAnalysis?.risk_score ||
          Math.min(
            100,
            (report?.findings_by_severity?.critical || 0) * 25 +
              (report?.findings_by_severity?.high || 0) * 15 +
              (report?.findings_by_severity?.medium || 0) * 5 +
              (report?.findings_by_severity?.low || 0) * 1
          ),
        securityScore:
          aiAnalysis?.security_score ||
          Math.max(
            0,
            100 -
              ((report?.findings_by_severity?.critical || 0) * 20 +
                (report?.findings_by_severity?.high || 0) * 10 +
                (report?.findings_by_severity?.medium || 0) * 3)
          ),
      };

      await generatePDF(reportRef.current, {
        filename: `security-report-${report?.project_name || reportId}-${
          new Date().toISOString().split("T")[0]
        }.pdf`,
        title: "ONYX Security",
        subtitle: `Security Analysis Report - ${
          report?.project_name || "Vulnerability Scan"
        }`,
        showExecutiveSummary: true,
        showTableOfContents: false,
        reportData: reportData,
        companyName: report?.project_name,
        confidential: true,
      });
      toast.success("🎉 PDF report generated successfully!", {
        icon: "📄",
        duration: 3000,
      });
    } catch (error) {
      console.error("PDF generation error:", error);
      toast.error("Failed to generate PDF. Please try again.");
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
                to="#compliance-section"
                onClick={(e) => {
                  e.preventDefault();
                  document
                    .getElementById("compliance-section")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
                className="inline-flex items-center px-3 py-2 border border-green-600 text-sm font-medium rounded-md text-green-400 bg-green-900/20 hover:bg-green-900/30"
              >
                <DocumentTextIcon className="h-4 w-4 mr-2" />
                Jump to Compliance
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
                            Placeholder credentials in .env.example, README.md,
                            or documentation files are flagged for awareness but
                            typically don't require immediate action. Always
                            verify secrets in example files aren't accidentally
                            real.
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
                                          finding.metadata.calculated_entropy >
                                          4
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
                                        finding.metadata.calculated_entropy > 4
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
                                        : finding.metadata.calculated_entropy >
                                          3
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
            <div className="space-y-6">
              {aiLoading ? (
                <div className="glass-container rounded-xl p-8 text-center">
                  <RefreshIcon className="h-8 w-8 text-blue-400 animate-spin mx-auto mb-4" />
                  <p className="text-gray-400">Loading AI analysis...</p>
                </div>
              ) : aiAnalysis && aiAnalysis.has_analysis ? (
                <>
                  {/* Security Score Dashboard */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Security Score */}
                    <div className="glass-container rounded-xl p-6 text-center">
                      <h4 className="text-sm font-medium text-gray-400 mb-3">
                        Security Score
                      </h4>
                      <div className="relative inline-flex items-center justify-center">
                        <svg className="w-24 h-24 transform -rotate-90">
                          <circle
                            cx="48"
                            cy="48"
                            r="40"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            className="text-gray-700"
                          />
                          <circle
                            cx="48"
                            cy="48"
                            r="40"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            className={`${
                              (aiAnalysis.security_score || 0) >= 80
                                ? "text-green-500"
                                : (aiAnalysis.security_score || 0) >= 50
                                ? "text-yellow-500"
                                : "text-red-500"
                            }`}
                            strokeDasharray={`${
                              (aiAnalysis.security_score || 0) * 2.51
                            } 251`}
                            strokeLinecap="round"
                          />
                        </svg>
                        <span className="absolute text-2xl font-bold text-white">
                          {aiAnalysis.security_score || "N/A"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">out of 100</p>
                    </div>

                    {/* Risk Level */}
                    <div className="glass-container rounded-xl p-6 text-center">
                      <h4 className="text-sm font-medium text-gray-400 mb-3">
                        Risk Level
                      </h4>
                      <div
                        className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${
                          aiAnalysis.risk_level === "CRITICAL"
                            ? "bg-red-500/20 border-2 border-red-500"
                            : aiAnalysis.risk_level === "HIGH"
                            ? "bg-orange-500/20 border-2 border-orange-500"
                            : aiAnalysis.risk_level === "MEDIUM"
                            ? "bg-yellow-500/20 border-2 border-yellow-500"
                            : "bg-green-500/20 border-2 border-green-500"
                        }`}
                      >
                        <span
                          className={`text-lg font-bold ${
                            aiAnalysis.risk_level === "CRITICAL"
                              ? "text-red-400"
                              : aiAnalysis.risk_level === "HIGH"
                              ? "text-orange-400"
                              : aiAnalysis.risk_level === "MEDIUM"
                              ? "text-yellow-400"
                              : "text-green-400"
                          }`}
                        >
                          {aiAnalysis.risk_level || "N/A"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Risk Score: {aiAnalysis.risk_score || "N/A"}/100
                      </p>
                    </div>

                    {/* Fix Time Estimate */}
                    <div className="glass-container rounded-xl p-6 text-center">
                      <h4 className="text-sm font-medium text-gray-400 mb-3">
                        Estimated Fix Time
                      </h4>
                      <div className="flex items-center justify-center w-24 h-24 mx-auto bg-blue-500/20 rounded-full border-2 border-blue-500">
                        <ClockIcon className="h-10 w-10 text-blue-400" />
                      </div>
                      <p className="text-sm font-medium text-white mt-3">
                        {aiAnalysis.estimated_fix_time || "N/A"}
                      </p>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  {aiAnalysis.executive_summary && (
                    <div className="glass-container rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <SparklesIcon className="h-5 w-5 mr-2 text-blue-400" />
                        Executive Summary
                      </h3>
                      <p className="text-gray-300 leading-relaxed whitespace-pre-line">
                        {aiAnalysis.executive_summary}
                      </p>
                    </div>
                  )}

                  {aiAnalysis.overall_risk_assessment && (
                    <div className="glass-container rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-amber-400" />
                        Risk Assessment
                      </h3>
                      <p className="text-gray-300 leading-relaxed">
                        {aiAnalysis.overall_risk_assessment}
                      </p>
                    </div>
                  )}

                  {aiAnalysis.priority_findings &&
                    aiAnalysis.priority_findings.length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                          <FireIcon className="h-5 w-5 mr-2 text-red-400" />
                          Priority Findings
                        </h3>
                        <ul className="space-y-3">
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

                  {aiAnalysis.priority_recommendations &&
                    aiAnalysis.priority_recommendations.length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                          <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-400" />
                          Recommendations
                        </h3>
                        <ul className="space-y-3">
                          {aiAnalysis.priority_recommendations.map(
                            (recommendation, index) => (
                              <li key={index} className="flex items-start">
                                <CheckCircleIcon className="h-5 w-5 text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-300">
                                  {recommendation}
                                </span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {aiAnalysis.secure_code_examples &&
                    Object.keys(aiAnalysis.secure_code_examples).length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                          <CodeIcon className="h-5 w-5 mr-2 text-green-400" />
                          Secure Code Examples
                        </h3>
                        <div className="space-y-4">
                          {Object.entries(aiAnalysis.secure_code_examples).map(
                            ([key, example], index) => (
                              <div
                                key={index}
                                className="bg-gray-900/50 rounded-lg p-4"
                              >
                                <h4 className="text-sm font-medium text-gray-400 mb-2">
                                  {key}
                                </h4>
                                <pre className="text-sm text-green-300 overflow-x-auto">
                                  <code>{example}</code>
                                </pre>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                  {aiAnalysis.compliance_impact && (
                    <div className="glass-container rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <DocumentTextIcon className="h-5 w-5 mr-2 text-purple-400" />
                        Compliance Impact
                      </h3>
                      {typeof aiAnalysis.compliance_impact === "string" ? (
                        <p className="text-gray-300 leading-relaxed">
                          {aiAnalysis.compliance_impact}
                        </p>
                      ) : (
                        <div className="space-y-4">
                          {aiAnalysis.compliance_impact.overall_impact && (
                            <div className="flex items-center space-x-2">
                              <span className="text-gray-400 font-medium">
                                Overall Impact:
                              </span>
                              <span
                                className={`px-2 py-1 rounded text-sm font-medium ${
                                  aiAnalysis.compliance_impact.overall_impact
                                    .toLowerCase()
                                    .includes("high")
                                    ? "bg-red-500/20 text-red-400"
                                    : aiAnalysis.compliance_impact.overall_impact
                                        .toLowerCase()
                                        .includes("medium")
                                    ? "bg-yellow-500/20 text-yellow-400"
                                    : "bg-green-500/20 text-green-400"
                                }`}
                              >
                                {aiAnalysis.compliance_impact.overall_impact}
                              </span>
                            </div>
                          )}
                          {aiAnalysis.compliance_impact.frameworks_affected && (
                            <div>
                              <span className="text-gray-400 font-medium">
                                Frameworks Affected:
                              </span>
                              <p className="text-gray-300 mt-1">
                                {
                                  aiAnalysis.compliance_impact
                                    .frameworks_affected
                                }
                              </p>
                            </div>
                          )}
                          {aiAnalysis.compliance_impact.analysis && (
                            <div>
                              <span className="text-gray-400 font-medium">
                                Analysis:
                              </span>
                              <p className="text-gray-300 mt-1 leading-relaxed">
                                {aiAnalysis.compliance_impact.analysis}
                              </p>
                            </div>
                          )}
                          {aiAnalysis.compliance_impact.required_actions && (
                            <div>
                              <span className="text-gray-400 font-medium">
                                Required Actions:
                              </span>
                              <p className="text-gray-300 mt-1">
                                {aiAnalysis.compliance_impact.required_actions}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Threat Categories */}
                  {aiAnalysis.threat_categories &&
                    Object.keys(aiAnalysis.threat_categories).length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                          <ChartBarIcon className="h-5 w-5 mr-2 text-orange-400" />
                          Threat Categories Breakdown
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(aiAnalysis.threat_categories).map(
                            ([category, count]) => (
                              <div
                                key={category}
                                className="bg-gray-800/50 rounded-lg p-4 text-center"
                              >
                                <p className="text-2xl font-bold text-white">
                                  {count}
                                </p>
                                <p className="text-sm text-gray-400">
                                  {category}
                                </p>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                  {/* Attack Vectors */}
                  {aiAnalysis.attack_vectors &&
                    aiAnalysis.attack_vectors.length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                          <BoltIcon className="h-5 w-5 mr-2 text-red-400" />
                          Potential Attack Vectors
                        </h3>
                        <div className="space-y-3">
                          {aiAnalysis.attack_vectors.map((vector, index) => (
                            <div
                              key={index}
                              className="flex items-start bg-red-900/20 border border-red-500/30 rounded-lg p-3"
                            >
                              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-3 mt-0.5 flex-shrink-0" />
                              <span className="text-gray-300">{vector}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Remediation Roadmap */}
                  {aiAnalysis.remediation_roadmap &&
                    aiAnalysis.remediation_roadmap.length > 0 && (
                      <div className="glass-container rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                          <DocumentTextIcon className="h-5 w-5 mr-2 text-green-400" />
                          Remediation Roadmap
                        </h3>
                        <div className="space-y-4">
                          {aiAnalysis.remediation_roadmap.map(
                            (phase, index) => (
                              <div
                                key={index}
                                className="border border-gray-700 rounded-lg overflow-hidden"
                              >
                                <div
                                  className={`p-4 flex items-center justify-between ${
                                    phase.priority === "CRITICAL"
                                      ? "bg-red-900/30"
                                      : phase.priority === "HIGH"
                                      ? "bg-orange-900/30"
                                      : phase.priority === "MEDIUM"
                                      ? "bg-yellow-900/30"
                                      : "bg-green-900/30"
                                  }`}
                                >
                                  <div className="flex items-center space-x-3">
                                    <span
                                      className={`px-2 py-1 rounded text-xs font-bold ${
                                        phase.priority === "CRITICAL"
                                          ? "bg-red-500 text-white"
                                          : phase.priority === "HIGH"
                                          ? "bg-orange-500 text-white"
                                          : phase.priority === "MEDIUM"
                                          ? "bg-yellow-500 text-black"
                                          : "bg-green-500 text-white"
                                      }`}
                                    >
                                      Phase {phase.phase}
                                    </span>
                                    <span className="font-semibold text-white">
                                      {phase.title}
                                    </span>
                                  </div>
                                  <span className="text-sm text-gray-400">
                                    {phase.timeline}
                                  </span>
                                </div>
                                <div className="p-4 bg-gray-800/30">
                                  <ul className="space-y-2">
                                    {phase.tasks &&
                                      phase.tasks.map((task, taskIndex) => (
                                        <li
                                          key={taskIndex}
                                          className="flex items-start"
                                        >
                                          <CheckCircleIcon className="h-4 w-4 text-gray-500 mr-2 mt-0.5 flex-shrink-0" />
                                          <span className="text-gray-300 text-sm">
                                            {task}
                                          </span>
                                        </li>
                                      ))}
                                  </ul>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                  {aiAnalysis.model_used && (
                    <div className="glass-container rounded-xl p-4 bg-gray-800/30">
                      <p className="text-xs text-gray-500 text-center">
                        🤖 Analysis generated by{" "}
                        <span className="text-blue-400">
                          {aiAnalysis.model_used}
                        </span>
                        {aiAnalysis.generated_at &&
                          ` on ${new Date(
                            aiAnalysis.generated_at
                          ).toLocaleString()}`}
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="glass-container rounded-xl p-8 text-center">
                  <SparklesIcon className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    AI Analysis Not Available
                  </h3>
                  <p className="text-gray-400 mb-4">
                    {aiError
                      ? "Failed to load AI analysis. Please try again later."
                      : "AI analysis has not been generated for this report yet."}
                  </p>
                  <p className="text-sm text-gray-500">
                    AI analysis is automatically generated when a scan
                    completes. If you're seeing this message, the analysis may
                    still be processing or may not have been triggered.
                  </p>
                </div>
              )}
            </div>
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
                              f.severity === "critical" || f.severity === "high"
                          ).length
                        }
                      </div>
                      <div className="text-xs text-gray-400">Critical/High</div>
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
                            (f) => f.severity === "low" || f.severity === "info"
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
                          <span className="text-xs text-gray-500">Phase 1</span>
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
                              f.severity === "critical" || f.severity === "high"
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
                              f.severity === "critical" || f.severity === "high"
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
                          <span className="text-xs text-gray-500">Phase 2</span>
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
                          <span className="text-xs text-gray-500">Phase 3</span>
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
                            (f) => f.severity === "low" || f.severity === "info"
                          ).length > 5 && (
                            <p className="text-xs text-gray-500 pl-6">
                              +
                              {getFilteredFindings().filter(
                                (f) =>
                                  f.severity === "low" || f.severity === "info"
                              ).length - 5}{" "}
                              more issues
                            </p>
                          )}
                          {getFilteredFindings().filter(
                            (f) => f.severity === "low" || f.severity === "info"
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
            <div className="space-y-6">
              {/* Compliance Header */}
              <div className="glass-container rounded-xl p-6 bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                      <ShieldCheckIcon className="h-6 w-6 text-blue-400" />
                      Compliance Analysis
                    </h3>
                    <p className="text-gray-400 mt-1">
                      Map security findings against industry compliance
                      frameworks
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.keys(COMPLIANCE_STANDARDS).map((std) => (
                      <button
                        key={std}
                        onClick={() => {
                          if (selectedStandards.includes(std)) {
                            setSelectedStandards(
                              selectedStandards.filter((s) => s !== std)
                            );
                          } else {
                            setSelectedStandards([...selectedStandards, std]);
                          }
                        }}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                          selectedStandards.includes(std)
                            ? "bg-blue-600 text-white"
                            : "bg-gray-700/50 text-gray-400 hover:bg-gray-700 hover:text-white"
                        }`}
                      >
                        {COMPLIANCE_STANDARDS[std].icon} {std}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              {/* Compliance Standards Analysis */}
              <div id="compliance-section">
                {selectedStandards.map((standardKey) => {
                  const standard = COMPLIANCE_STANDARDS[standardKey];
                  const allFindings = getFilteredFindings();

                  // Calculate compliance for each category
                  const categoryCompliance = {};
                  Object.keys(standard.categories).forEach((cat) => {
                    categoryCompliance[cat] = {
                      findings: [],
                      compliant: true,
                      riskLevel: "low",
                    };
                  });

                  allFindings.forEach((finding) => {
                    const mappedCats = mapFindingToCompliance(
                      finding,
                      standardKey
                    );
                    mappedCats.forEach((cat) => {
                      if (categoryCompliance[cat]) {
                        categoryCompliance[cat].findings.push(finding);
                        categoryCompliance[cat].compliant = false;
                        if (
                          finding.severity === "critical" ||
                          finding.severity === "high"
                        ) {
                          categoryCompliance[cat].riskLevel = finding.severity;
                        } else if (
                          categoryCompliance[cat].riskLevel === "low" &&
                          finding.severity === "medium"
                        ) {
                          categoryCompliance[cat].riskLevel = "medium";
                        }
                      }
                    });
                  });

                  const totalCategories = Object.keys(
                    standard.categories
                  ).length;
                  const compliantCategories = Object.values(
                    categoryCompliance
                  ).filter((c) => c.compliant).length;
                  const complianceRate = (
                    (compliantCategories / totalCategories) *
                    100
                  ).toFixed(0);

                  return (
                    <div
                      key={standardKey}
                      className="glass-container rounded-xl overflow-hidden"
                    >
                      {/* Standard Header */}
                      <div
                        className={`p-6 border-b border-gray-700/50 bg-gradient-to-r ${
                          standardKey === "OWASP"
                            ? "from-orange-900/30 to-red-900/30"
                            : standardKey === "NIST"
                            ? "from-blue-900/30 to-cyan-900/30"
                            : "from-purple-900/30 to-pink-900/30"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <span className="text-4xl">{standard.icon}</span>
                            <div>
                              <h4 className="text-lg font-bold text-white">
                                {standard.name}
                              </h4>
                              <p className="text-sm text-gray-400">
                                {standard.description}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div
                              className={`text-3xl font-bold ${
                                complianceRate >= 80
                                  ? "text-green-400"
                                  : complianceRate >= 50
                                  ? "text-yellow-400"
                                  : "text-red-400"
                              }`}
                            >
                              {complianceRate}%
                            </div>
                            <div className="text-sm text-gray-400">
                              Compliance Rate
                            </div>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="mt-4">
                          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all duration-500 ${
                                complianceRate >= 80
                                  ? "bg-green-500"
                                  : complianceRate >= 50
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              }`}
                              style={{ width: `${complianceRate}%` }}
                            />
                          </div>
                          <div className="flex justify-between mt-2 text-xs text-gray-500">
                            <span>
                              {compliantCategories}/{totalCategories} Controls
                              Compliant
                            </span>
                            <span>{allFindings.length} Related Findings</span>
                          </div>
                        </div>
                      </div>

                      {/* Category Grid */}
                      <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {Object.entries(standard.categories).map(
                            ([catKey, catName]) => {
                              const catData = categoryCompliance[catKey];
                              const isCompliant = catData.compliant;
                              const findingCount = catData.findings.length;

                              return (
                                <div
                                  key={catKey}
                                  className={`p-4 rounded-lg border transition-all duration-200 ${
                                    isCompliant
                                      ? "bg-green-900/10 border-green-500/30 hover:border-green-500/50"
                                      : "bg-red-900/10 border-red-500/30 hover:border-red-500/50"
                                  }`}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3">
                                      <div
                                        className={`p-1.5 rounded-lg ${
                                          isCompliant
                                            ? "bg-green-500/20"
                                            : "bg-red-500/20"
                                        }`}
                                      >
                                        {isCompliant ? (
                                          <CheckCircleIcon className="h-5 w-5 text-green-400" />
                                        ) : (
                                          <XCircleIcon className="h-5 w-5 text-red-400" />
                                        )}
                                      </div>
                                      <div>
                                        <div className="font-medium text-white">
                                          {catKey}
                                        </div>
                                        <div className="text-sm text-gray-400">
                                          {catName}
                                        </div>
                                      </div>
                                    </div>
                                    {!isCompliant && (
                                      <span
                                        className={`px-2 py-1 rounded text-xs font-medium ${
                                          catData.riskLevel === "critical"
                                            ? "bg-red-500/20 text-red-400"
                                            : catData.riskLevel === "high"
                                            ? "bg-orange-500/20 text-orange-400"
                                            : "bg-yellow-500/20 text-yellow-400"
                                        }`}
                                      >
                                        {findingCount} issue
                                        {findingCount > 1 ? "s" : ""}
                                      </span>
                                    )}
                                  </div>

                                  {/* Show findings for non-compliant categories */}
                                  {!isCompliant &&
                                    catData.findings.length > 0 && (
                                      <div className="mt-3 pt-3 border-t border-gray-700/50">
                                        <div className="space-y-2">
                                          {catData.findings
                                            .slice(0, 3)
                                            .map((finding, idx) => (
                                              <div
                                                key={idx}
                                                className="flex items-start gap-2 text-sm"
                                              >
                                                <span
                                                  className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${
                                                    finding.severity ===
                                                    "critical"
                                                      ? "bg-red-500"
                                                      : finding.severity ===
                                                        "high"
                                                      ? "bg-orange-500"
                                                      : finding.severity ===
                                                        "medium"
                                                      ? "bg-yellow-500"
                                                      : "bg-blue-500"
                                                  }`}
                                                />
                                                <span className="text-gray-300 truncate">
                                                  {finding.title ||
                                                    finding.message}
                                                </span>
                                              </div>
                                            ))}
                                          {catData.findings.length > 3 && (
                                            <div className="text-xs text-gray-500 pl-4">
                                              +{catData.findings.length - 3}{" "}
                                              more findings
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    )}
                                </div>
                              );
                            }
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>{" "}
              {/* End of compliance-section */}
              {/* Recommendations based on compliance gaps */}
              <div className="glass-container rounded-xl p-6">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <LightBulbIcon className="h-5 w-5 text-yellow-400" />
                  Compliance Recommendations
                </h4>
                <div className="space-y-3">
                  {[
                    {
                      priority: "Critical",
                      color: "red",
                      text: "Address all critical and high severity findings to meet baseline compliance requirements.",
                    },
                    {
                      priority: "High",
                      color: "orange",
                      text: "Implement secure coding practices and code review processes to prevent injection vulnerabilities.",
                    },
                    {
                      priority: "Medium",
                      color: "yellow",
                      text: "Enable comprehensive security logging and monitoring for NIST DE (Detect) compliance.",
                    },
                    {
                      priority: "Low",
                      color: "blue",
                      text: "Document security procedures and conduct regular compliance assessments.",
                    },
                  ].map((rec, idx) => (
                    <div
                      key={idx}
                      className={`flex items-start gap-3 p-3 rounded-lg bg-${rec.color}-500/10 border border-${rec.color}-500/20`}
                    >
                      <span
                        className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-semibold bg-${rec.color}-500/20 text-${rec.color}-400`}
                      >
                        {rec.priority}
                      </span>
                      <span className="text-gray-300 text-sm">{rec.text}</span>
                    </div>
                  ))}
                </div>
              </div>
              {/* Export Options */}
              <div className="glass-container rounded-xl p-6">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <DownloadIcon className="h-5 w-5 text-green-400" />
                  Export Compliance Report
                </h4>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={generateViewPDF}
                    disabled={isGenerating}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors duration-200"
                  >
                    {isGenerating ? (
                      <RefreshIcon className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <DocumentTextIcon className="h-4 w-4 mr-2" />
                    )}
                    Download PDF Report
                  </button>
                  <Link
                    to="#top"
                    onClick={(e) => {
                      e.preventDefault();
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200"
                  >
                    <ExternalLinkIcon className="h-4 w-4 mr-2" />
                    Back to Top
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  );
};

export default EnhancedReportDetails;
