/**
 * ComplianceReport Component - Generate compliance-ready PDF reports
 */
import React, { useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import html2pdf from "html2pdf.js";
import {
  ArrowLeftIcon,
  ArrowDownTrayIcon as DownloadIcon,
  PrinterIcon,
  DocumentDuplicateIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  CalendarIcon,
  TagIcon,
  UserIcon,
  BuildingOfficeIcon as OfficeBuildingIcon,
  ArrowPathIcon as RefreshIcon,
  ChartBarIcon,
  LightBulbIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI, utils } from "../../services/api";
import toast from "react-hot-toast";

const ComplianceReport = () => {
  const { reportId } = useParams();
  const reportRef = useRef();
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedStandards, setSelectedStandards] = useState([
    "OWASP",
    "NIST",
    "ISO27001",
  ]);
  const [includeAIAnalysis, setIncludeAIAnalysis] = useState(true);
  const [includeCodeSnippets, setIncludeCodeSnippets] = useState(false);
  const [reportFormat, setReportFormat] = useState("detailed");

  // Debug logging
  console.log(
    "ComplianceReport - reportId:",
    reportId,
    "type:",
    typeof reportId
  );

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
  const { data: aiAnalysis } = useQuery({
    queryKey: ["ai-analysis", reportId],
    queryFn: () => reportsAPI.getAIAnalysis(reportId),
    enabled: !!reportId && report?.has_ai_analysis && includeAIAnalysis,
  });

  // Compliance standards mapping
  const complianceStandards = {
    OWASP: {
      name: "OWASP Top 10",
      version: "2021",
      description:
        "Open Web Application Security Project Top 10 Most Critical Security Risks",
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
        "A.17":
          "Information Security Aspects of Business Continuity Management",
        "A.18": "Compliance",
      },
    },
    PCI_DSS: {
      name: "PCI DSS",
      version: "4.0",
      description: "Payment Card Industry Data Security Standard",
      categories: {
        "REQ.1": "Install and Maintain Network Security Controls",
        "REQ.2": "Apply Secure Configurations to All System Components",
        "REQ.3": "Protect Stored Account Data",
        "REQ.4":
          "Protect Account Data with Strong Cryptography During Transmission",
        "REQ.5": "Protect All Systems and Networks from Malicious Software",
        "REQ.6": "Develop and Maintain Secure Systems and Software",
        "REQ.7": "Restrict Access by Business Need to Know",
        "REQ.8": "Identify Users and Authenticate Access to System Components",
        "REQ.9": "Restrict Physical Access to Account Data",
        "REQ.10":
          "Log and Monitor All Access to System Components and Account Data",
        "REQ.11": "Test Security of Systems and Networks Regularly",
        "REQ.12":
          "Support Information Security with Organizational Policies and Programs",
      },
    },
  };

  // Map findings to compliance standards
  const mapFindingsToCompliance = (findings, standards) => {
    const mapping = {};

    standards.forEach((standard) => {
      mapping[standard] = {
        ...complianceStandards[standard],
        findings: [],
        coverage: {},
      };

      // Initialize coverage
      Object.keys(complianceStandards[standard].categories).forEach(
        (category) => {
          mapping[standard].coverage[category] = {
            compliant: true,
            findings: [],
            risk_level: "low",
          };
        }
      );
    });

    // Map each finding to relevant standards
    findings.forEach((finding) => {
      standards.forEach((standard) => {
        const relevantCategories = getRelevantCategories(finding, standard);
        relevantCategories.forEach((category) => {
          mapping[standard].coverage[category].findings.push(finding);
          mapping[standard].coverage[category].compliant = false;

          // Determine risk level based on severity
          const currentRisk = mapping[standard].coverage[category].risk_level;
          const findingRisk =
            finding.severity === "critical"
              ? "critical"
              : finding.severity === "high"
              ? "high"
              : finding.severity === "medium"
              ? "medium"
              : "low";

          if (getRiskPriority(findingRisk) > getRiskPriority(currentRisk)) {
            mapping[standard].coverage[category].risk_level = findingRisk;
          }
        });

        mapping[standard].findings.push(finding);
      });
    });

    return mapping;
  };

  // Get relevant compliance categories for a finding
  const getRelevantCategories = (finding, standard) => {
    const categories = [];
    const cweId = finding.cwe_id;
    const description = finding.description?.toLowerCase() || "";
    const title = finding.title?.toLowerCase() || "";

    switch (standard) {
      case "OWASP":
        if (
          cweId &&
          [
            22, 23, 36, 59, 98, 99, 117, 209, 284, 285, 352, 642, 862, 863,
          ].includes(parseInt(cweId))
        ) {
          categories.push("A01"); // Broken Access Control
        }
        if (
          cweId &&
          [259, 261, 311, 321, 322, 325, 326, 327, 328, 329, 330].includes(
            parseInt(cweId)
          )
        ) {
          categories.push("A02"); // Cryptographic Failures
        }
        if (
          description.includes("injection") ||
          description.includes("sql") ||
          description.includes("xss")
        ) {
          categories.push("A03"); // Injection
        }
        if (
          description.includes("misconfiguration") ||
          description.includes("default")
        ) {
          categories.push("A05"); // Security Misconfiguration
        }
        if (
          description.includes("component") ||
          description.includes("dependency") ||
          description.includes("outdated")
        ) {
          categories.push("A06"); // Vulnerable Components
        }
        break;

      case "NIST":
        categories.push("ID"); // All findings relate to identification
        if (description.includes("protect") || description.includes("secure")) {
          categories.push("PR");
        }
        if (description.includes("detect") || description.includes("monitor")) {
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
        break;

      case "PCI_DSS":
        if (
          description.includes("network") ||
          description.includes("firewall")
        ) {
          categories.push("REQ.1");
        }
        if (
          description.includes("configuration") ||
          description.includes("default")
        ) {
          categories.push("REQ.2");
        }
        if (
          description.includes("crypto") ||
          description.includes("encryption")
        ) {
          categories.push("REQ.4");
        }
        if (
          description.includes("development") ||
          description.includes("secure code")
        ) {
          categories.push("REQ.6");
        }
        break;
    }

    // Default mapping if no specific categories found
    if (categories.length === 0) {
      switch (standard) {
        case "OWASP":
          categories.push("A05"); // Security Misconfiguration as default
          break;
        case "NIST":
          categories.push("PR"); // Protect as default
          break;
        case "ISO27001":
          categories.push("A.12"); // Operations Security as default
          break;
        case "PCI_DSS":
          categories.push("REQ.6"); // Secure Development as default
          break;
      }
    }

    return categories;
  };

  const getRiskPriority = (risk) => {
    const priorities = { low: 1, medium: 2, high: 3, critical: 4 };
    return priorities[risk] || 1;
  };

  // Generate PDF
  const generatePDF = async () => {
    if (!reportRef.current || !report) return;

    setIsGenerating(true);
    try {
      const element = reportRef.current;
      const opt = {
        margin: [0.5, 0.5],
        filename: `compliance-report-${report.project_name}-${
          new Date().toISOString().split("T")[0]
        }.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          letterRendering: true,
          logging: false,
        },
        jsPDF: {
          unit: "in",
          format: "letter",
          orientation: "portrait",
        },
      };

      await html2pdf().set(opt).from(element).save();
      toast.success("PDF report generated successfully");
    } catch (error) {
      console.error("PDF generation error:", error);
      toast.error("Failed to generate PDF report");
    } finally {
      setIsGenerating(false);
    }
  };

  // Print report
  const printReport = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <RefreshIcon className="h-8 w-8 text-blue-400 animate-spin mr-3" />
            <span className="text-gray-400 text-lg">
              Loading compliance report...
            </span>
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
                  {availableReports.reports
                    .slice(0, 3)
                    .map((availableReport) => (
                      <Link
                        key={availableReport.id}
                        to={`/compliance/${availableReport.id}`}
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
              <Link
                to="/reports"
                className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
              >
                <DocumentTextIcon className="h-4 w-4 mr-2" />
                View All Reports
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Extract all findings from the report
  const getAllFindings = (report) => {
    let allFindings = [];

    // Try different data structures
    if (report.findings) {
      allFindings = report.findings;
    } else if (report.scan_results) {
      // Extract findings from scan_results
      report.scan_results.forEach((scanResult) => {
        if (scanResult.findings) {
          allFindings = allFindings.concat(scanResult.findings);
        }
      });
    }

    return allFindings;
  };

  const allFindings = getAllFindings(report || {});
  const complianceMapping = mapFindingsToCompliance(
    allFindings,
    selectedStandards
  );

  const SeverityBadge = ({ severity }) => {
    const severityColors = {
      critical: "bg-red-500/20 text-red-400 border-red-500/30",
      high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    };
    const colorClass =
      severityColors[severity?.toLowerCase()] || severityColors.info;
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} border`}
      >
        {severity?.charAt(0).toUpperCase() + severity?.slice(1)}
      </span>
    );
  };

  const ComplianceStatus = ({ isCompliant, riskLevel }) => {
    if (isCompliant) {
      return (
        <div className="flex items-center text-green-400 bg-green-500/10 px-3 py-1.5 rounded-lg border border-green-500/30">
          <CheckCircleIcon className="h-4 w-4 mr-1.5" />
          <span className="text-sm font-medium">Compliant</span>
        </div>
      );
    }

    const riskColors = {
      low: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
      medium: "text-orange-400 bg-orange-500/10 border-orange-500/30",
      high: "text-red-400 bg-red-500/10 border-red-500/30",
      critical: "text-red-400 bg-red-600/20 border-red-500/30",
    };

    const riskIcons = {
      low: InformationCircleIcon,
      medium: ExclamationTriangleIcon,
      high: ExclamationTriangleIcon,
      critical: XCircleIcon,
    };

    const Icon = riskIcons[riskLevel] || ExclamationTriangleIcon;
    const colorClass = riskColors[riskLevel] || riskColors.medium;

    return (
      <div
        className={`flex items-center px-3 py-1.5 rounded-lg border ${colorClass}`}
      >
        <Icon className="h-4 w-4 mr-1.5" />
        <span className="text-sm font-medium">Non-Compliant ({riskLevel})</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 no-print">
          <div className="flex items-center mb-4">
            <Link
              to={`/report/${reportId}`}
              className="inline-flex items-center text-sm text-gray-400 hover:text-white transition-colors duration-200"
            >
              <ArrowLeftIcon className="h-4 w-4 mr-1" />
              Back to Report Details
            </Link>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <DocumentTextIcon className="h-8 w-8 text-blue-400" />
                Compliance Report
              </h1>
              <p className="mt-2 text-gray-400">{report.project_name}</p>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={printReport}
                className="inline-flex items-center px-4 py-2 border border-gray-600 text-sm font-medium rounded-lg text-gray-300 bg-gray-800/50 hover:bg-gray-700/50 hover:text-white transition-all duration-200"
              >
                <PrinterIcon className="h-4 w-4 mr-2" />
                Print
              </button>

              <button
                onClick={generatePDF}
                disabled={isGenerating}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 disabled:opacity-50 transition-all duration-200 shadow-lg shadow-blue-500/25"
              >
                {isGenerating ? (
                  <RefreshIcon className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <DownloadIcon className="h-4 w-4 mr-2" />
                )}
                {isGenerating ? "Generating..." : "Download PDF"}
              </button>
            </div>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="glass-container rounded-2xl p-6 mb-8 no-print border border-gray-700/50">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <ShieldCheckIcon className="h-5 w-5 text-blue-400" />
            Report Configuration
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Compliance Standards
              </label>
              <div className="space-y-2">
                {Object.keys(complianceStandards).map((standard) => (
                  <label
                    key={standard}
                    className="flex items-center cursor-pointer group"
                  >
                    <input
                      type="checkbox"
                      checked={selectedStandards.includes(standard)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedStandards([
                            ...selectedStandards,
                            standard,
                          ]);
                        } else {
                          setSelectedStandards(
                            selectedStandards.filter((s) => s !== standard)
                          );
                        }
                      }}
                      className="h-4 w-4 text-blue-500 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-offset-gray-900"
                    />
                    <span className="ml-2 text-sm text-gray-400 group-hover:text-gray-200 transition-colors">
                      {complianceStandards[standard].name}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Report Format
              </label>
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value)}
                className="block w-full px-3 py-2 bg-gray-800/80 border border-gray-600 rounded-lg text-gray-200 shadow-sm focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="detailed">Detailed Report</option>
                <option value="summary">Executive Summary</option>
                <option value="technical">Technical Report</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Additional Options
              </label>
              <div className="space-y-2">
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={includeAIAnalysis}
                    onChange={(e) => setIncludeAIAnalysis(e.target.checked)}
                    className="h-4 w-4 text-blue-500 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-offset-gray-900"
                  />
                  <span className="ml-2 text-sm text-gray-400 group-hover:text-gray-200 transition-colors">
                    Include AI Analysis
                  </span>
                </label>
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={includeCodeSnippets}
                    onChange={(e) => setIncludeCodeSnippets(e.target.checked)}
                    className="h-4 w-4 text-blue-500 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-offset-gray-900"
                  />
                  <span className="ml-2 text-sm text-gray-400 group-hover:text-gray-200 transition-colors">
                    Include Code Snippets
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* PDF Content */}
        <div
          ref={reportRef}
          className="glass-container rounded-2xl p-8 border border-gray-700/50"
        >
          {/* Report Header */}
          <div className="border-b border-gray-700/50 pb-8 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">
                  Security Compliance Report
                </h1>
                <h2 className="text-xl text-gray-400 mt-2">
                  {report.project_name}
                </h2>
              </div>
              <div className="text-right text-sm text-gray-400">
                <div>Generated: {new Date().toLocaleDateString()}</div>
                <div className="text-gray-500">Report ID: {report.id}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-8">
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/30">
                <div className="text-sm font-medium text-gray-400">Project</div>
                <div className="text-white mt-1">{report.project_name}</div>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/30">
                <div className="text-sm font-medium text-gray-400">Branch</div>
                <div className="text-white mt-1">{report.branch}</div>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/30">
                <div className="text-sm font-medium text-gray-400">
                  Scan Date
                </div>
                <div className="text-white mt-1">
                  {utils.formatDate(report.created_at)}
                </div>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/30">
                <div className="text-sm font-medium text-gray-400">Status</div>
                <div className="text-white mt-1 capitalize">
                  {report.status}
                </div>
              </div>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <ChartBarIcon className="h-6 w-6 text-blue-400" />
              Executive Summary
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {Object.entries(report.findings_by_severity || {}).map(
                ([severity, count]) => {
                  const severityColors = {
                    critical:
                      "from-red-500/20 to-red-600/10 border-red-500/30 text-red-400",
                    high: "from-orange-500/20 to-orange-600/10 border-orange-500/30 text-orange-400",
                    medium:
                      "from-yellow-500/20 to-yellow-600/10 border-yellow-500/30 text-yellow-400",
                    low: "from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400",
                    info: "from-gray-500/20 to-gray-600/10 border-gray-500/30 text-gray-400",
                  };
                  const colorClass =
                    severityColors[severity] || severityColors.info;
                  return (
                    <div
                      key={severity}
                      className={`bg-gradient-to-br ${colorClass} p-4 rounded-xl border`}
                    >
                      <div className="text-sm font-medium capitalize">
                        {severity} Issues
                      </div>
                      <div className="text-3xl font-bold text-white mt-1">
                        {count}
                      </div>
                    </div>
                  );
                }
              )}
            </div>

            <div className="prose prose-invert max-w-none">
              <p className="text-gray-300">
                This security compliance report provides an assessment of{" "}
                <span className="text-white font-medium">
                  {report.project_name}
                </span>{" "}
                against industry-standard security frameworks. The analysis
                identified{" "}
                <span className="text-blue-400 font-medium">
                  {allFindings.length}
                </span>{" "}
                security findings across {selectedStandards.join(", ")}{" "}
                compliance frameworks.
              </p>

              {aiAnalysis?.overall_risk_assessment && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mt-4">
                  <h3 className="text-lg font-medium text-blue-400 mb-2 flex items-center gap-2">
                    <SparklesIcon className="h-5 w-5" />
                    AI Risk Assessment
                  </h3>
                  <p className="text-blue-200">
                    {aiAnalysis.overall_risk_assessment}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Compliance Analysis */}
          {selectedStandards.map((standardKey) => {
            const standard = complianceMapping[standardKey];
            const totalCategories = Object.keys(standard.categories).length;
            const compliantCategories = Object.values(standard.coverage).filter(
              (c) => c.compliant
            ).length;
            const complianceRate = (
              (compliantCategories / totalCategories) *
              100
            ).toFixed(1);

            return (
              <div key={standardKey} className="mb-8 page-break-before">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                  <ShieldCheckIcon className="h-6 w-6 text-green-400" />
                  {standard.name} Compliance Analysis
                </h2>

                <div className="bg-gray-800/50 p-6 rounded-xl mb-6 border border-gray-700/30">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                    <div>
                      <div className="text-sm font-medium text-gray-400">
                        Compliance Rate
                      </div>
                      <div className="text-3xl font-bold text-white mt-1">
                        <span
                          className={
                            complianceRate >= 80
                              ? "text-green-400"
                              : complianceRate >= 50
                              ? "text-yellow-400"
                              : "text-red-400"
                          }
                        >
                          {complianceRate}%
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-400">
                        Compliant Controls
                      </div>
                      <div className="text-3xl font-bold text-white mt-1">
                        <span className="text-green-400">
                          {compliantCategories}
                        </span>
                        <span className="text-gray-500">
                          /{totalCategories}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-400">
                        Total Findings
                      </div>
                      <div className="text-3xl font-bold text-white mt-1">
                        {standard.findings.length}
                      </div>
                    </div>
                  </div>

                  {/* Compliance Progress Bar */}
                  <div className="mt-4">
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-500 ${
                          complianceRate >= 80
                            ? "bg-green-500"
                            : complianceRate >= 50
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${complianceRate}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {Object.entries(standard.coverage).map(
                    ([categoryKey, coverage]) => (
                      <div
                        key={categoryKey}
                        className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-5 hover:bg-gray-800/50 transition-colors duration-200"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h3 className="text-lg font-medium text-white">
                              {categoryKey}: {standard.categories[categoryKey]}
                            </h3>
                          </div>
                          <ComplianceStatus
                            isCompliant={coverage.compliant}
                            riskLevel={coverage.risk_level}
                          />
                        </div>

                        {!coverage.compliant &&
                          coverage.findings.length > 0 && (
                            <div className="mt-4 pt-4 border-t border-gray-700/50">
                              <h4 className="text-sm font-medium text-gray-300 mb-3">
                                Non-Compliance Issues (
                                {coverage.findings.length})
                              </h4>
                              <div className="space-y-3">
                                {coverage.findings
                                  .slice(0, reportFormat === "summary" ? 3 : 10)
                                  .map((finding, index) => (
                                    <div
                                      key={index}
                                      className="flex items-start space-x-3 text-sm bg-gray-900/50 rounded-lg p-3"
                                    >
                                      <SeverityBadge
                                        severity={finding.severity}
                                      />
                                      <div className="flex-1 min-w-0">
                                        <div className="font-medium text-white">
                                          {finding.title}
                                        </div>
                                        <div className="text-gray-400 truncate">
                                          {finding.file_path}:
                                          {finding.line_number}
                                        </div>
                                        {reportFormat === "detailed" && (
                                          <div className="text-gray-500 mt-1">
                                            {finding.description}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                {coverage.findings.length >
                                  (reportFormat === "summary" ? 3 : 10) && (
                                  <div className="text-sm text-gray-500 pl-3">
                                    ... and{" "}
                                    {coverage.findings.length -
                                      (reportFormat === "summary"
                                        ? 3
                                        : 10)}{" "}
                                    more findings
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                      </div>
                    )
                  )}
                </div>
              </div>
            );
          })}

          {/* Detailed Findings */}
          {reportFormat === "detailed" && (
            <div className="mb-8 page-break-before">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <ExclamationTriangleIcon className="h-6 w-6 text-amber-400" />
                Detailed Findings
              </h2>
              <div className="space-y-4">
                {allFindings.map((finding, index) => (
                  <div
                    key={index}
                    className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-6 hover:bg-gray-800/50 transition-colors duration-200"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-medium text-white">
                          {finding.title}
                        </h3>
                        <div className="flex items-center flex-wrap gap-3 mt-2 text-sm text-gray-400">
                          <SeverityBadge severity={finding.severity} />
                          <span className="bg-gray-700/50 px-2 py-0.5 rounded">
                            CWE-{finding.cwe_id || "N/A"}
                          </span>
                          <span className="truncate max-w-xs">
                            {finding.file_path}:{finding.line_number}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-300 mb-1">
                          Description
                        </h4>
                        <p className="text-sm text-gray-400">
                          {finding.description}
                        </p>
                      </div>

                      {includeCodeSnippets && finding.code_snippet && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-300 mb-2">
                            Code Snippet
                          </h4>
                          <pre className="bg-gray-900 text-gray-300 p-4 rounded-lg text-xs overflow-x-auto border border-gray-700/50">
                            <code>{finding.code_snippet}</code>
                          </pre>
                        </div>
                      )}

                      {includeAIAnalysis &&
                        aiAnalysis?.findings_analysis?.[finding.id] && (
                          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                            <h4 className="text-sm font-medium text-blue-400 mb-2 flex items-center gap-2">
                              <SparklesIcon className="h-4 w-4" />
                              AI Analysis
                            </h4>
                            <div className="space-y-2 text-sm text-blue-200">
                              <div>
                                <strong className="text-blue-300">
                                  Impact:
                                </strong>{" "}
                                {
                                  aiAnalysis.findings_analysis[finding.id]
                                    .impact_assessment
                                }
                              </div>
                              <div>
                                <strong className="text-blue-300">
                                  Remediation:
                                </strong>
                                <ul className="list-disc list-inside mt-1 text-blue-200/80">
                                  {aiAnalysis.findings_analysis[
                                    finding.id
                                  ].remediation_steps?.map((step, i) => (
                                    <li key={i}>{step}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <LightBulbIcon className="h-6 w-6 text-yellow-400" />
              Recommendations
            </h2>
            <div className="bg-gray-800/30 rounded-xl p-6 border border-gray-700/50">
              <div className="space-y-4">
                {aiAnalysis?.priority_recommendations ? (
                  aiAnalysis.priority_recommendations.map(
                    (recommendation, index) => (
                      <div
                        key={index}
                        className="flex items-start space-x-4 p-3 bg-gray-900/50 rounded-lg"
                      >
                        <span className="flex-shrink-0 w-7 h-7 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </span>
                        <span className="text-gray-300">{recommendation}</span>
                      </div>
                    )
                  )
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-start space-x-4 p-3 bg-gray-900/50 rounded-lg">
                      <span className="flex-shrink-0 w-7 h-7 bg-red-500/20 text-red-400 rounded-full flex items-center justify-center text-sm font-medium">
                        1
                      </span>
                      <span className="text-gray-300">
                        Address all critical and high severity findings as a
                        priority
                      </span>
                    </div>
                    <div className="flex items-start space-x-4 p-3 bg-gray-900/50 rounded-lg">
                      <span className="flex-shrink-0 w-7 h-7 bg-orange-500/20 text-orange-400 rounded-full flex items-center justify-center text-sm font-medium">
                        2
                      </span>
                      <span className="text-gray-300">
                        Implement secure coding practices and regular security
                        reviews
                      </span>
                    </div>
                    <div className="flex items-start space-x-4 p-3 bg-gray-900/50 rounded-lg">
                      <span className="flex-shrink-0 w-7 h-7 bg-yellow-500/20 text-yellow-400 rounded-full flex items-center justify-center text-sm font-medium">
                        3
                      </span>
                      <span className="text-gray-300">
                        Establish automated security testing in the CI/CD
                        pipeline
                      </span>
                    </div>
                    <div className="flex items-start space-x-4 p-3 bg-gray-900/50 rounded-lg">
                      <span className="flex-shrink-0 w-7 h-7 bg-green-500/20 text-green-400 rounded-full flex items-center justify-center text-sm font-medium">
                        4
                      </span>
                      <span className="text-gray-300">
                        Conduct regular security assessments and penetration
                        testing
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-700/50 pt-8 text-center text-sm text-gray-500">
            <p>
              This report was generated by{" "}
              <span className="text-blue-400">SecureDevOps AI Platform</span> on{" "}
              {new Date().toLocaleDateString()}
            </p>
            <p className="mt-1">
              Report ID: <span className="text-gray-400">{report.id}</span> |
              Project:{" "}
              <span className="text-gray-400">{report.project_name}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceReport;
