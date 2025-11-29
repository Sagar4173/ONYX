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
    const colorClass = utils.getSeverityColor(severity);
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass} border`}
      >
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
    );
  };

  const ComplianceStatus = ({ isCompliant, riskLevel }) => {
    if (isCompliant) {
      return (
        <div className="flex items-center text-green-600">
          <CheckCircleIcon className="h-4 w-4 mr-1" />
          <span className="text-sm">Compliant</span>
        </div>
      );
    }

    const riskColors = {
      low: "text-yellow-600",
      medium: "text-orange-600",
      high: "text-red-600",
      critical: "text-red-700",
    };

    const riskIcons = {
      low: InformationCircleIcon,
      medium: ExclamationTriangleIcon,
      high: ExclamationTriangleIcon,
      critical: XCircleIcon,
    };

    const Icon = riskIcons[riskLevel] || ExclamationTriangleIcon;

    return (
      <div className={`flex items-center ${riskColors[riskLevel]}`}>
        <Icon className="h-4 w-4 mr-1" />
        <span className="text-sm">Non-Compliant ({riskLevel})</span>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 no-print">
        <div className="flex items-center mb-4">
          <Link
            to={`/report/${reportId}`}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back to Report Details
          </Link>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Compliance Report
            </h1>
            <p className="mt-2 text-gray-600">{report.project_name}</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={printReport}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <PrinterIcon className="h-4 w-4 mr-2" />
              Print
            </button>

            <button
              onClick={generatePDF}
              disabled={isGenerating}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
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
      <div className="bg-white shadow rounded-lg p-6 mb-8 no-print">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Report Configuration
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Compliance Standards
            </label>
            <div className="space-y-2">
              {Object.keys(complianceStandards).map((standard) => (
                <label key={standard} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedStandards.includes(standard)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedStandards([...selectedStandards, standard]);
                      } else {
                        setSelectedStandards(
                          selectedStandards.filter((s) => s !== standard)
                        );
                      }
                    }}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {complianceStandards[standard].name}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Format
            </label>
            <select
              value={reportFormat}
              onChange={(e) => setReportFormat(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="detailed">Detailed Report</option>
              <option value="summary">Executive Summary</option>
              <option value="technical">Technical Report</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Options
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeAIAnalysis}
                  onChange={(e) => setIncludeAIAnalysis(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Include AI Analysis
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeCodeSnippets}
                  onChange={(e) => setIncludeCodeSnippets(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Include Code Snippets
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* PDF Content */}
      <div ref={reportRef} className="bg-white">
        {/* Report Header */}
        <div className="border-b border-gray-200 pb-8 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Security Compliance Report
              </h1>
              <h2 className="text-xl text-gray-600 mt-2">
                {report.project_name}
              </h2>
            </div>
            <div className="text-right text-sm text-gray-500">
              <div>Generated: {new Date().toLocaleDateString()}</div>
              <div>Report ID: {report.id}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-8">
            <div>
              <div className="text-sm font-medium text-gray-500">Project</div>
              <div className="text-gray-900">{report.project_name}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Branch</div>
              <div className="text-gray-900">{report.branch}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Scan Date</div>
              <div className="text-gray-900">
                {utils.formatDate(report.created_at)}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Status</div>
              <div className="text-gray-900 capitalize">{report.status}</div>
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Executive Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
            {Object.entries(report.findings_by_severity || {}).map(
              ([severity, count]) => (
                <div key={severity} className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-gray-500 capitalize">
                    {severity} Issues
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {count}
                  </div>
                </div>
              )
            )}
          </div>

          <div className="prose max-w-none">
            <p className="text-gray-700">
              This security compliance report provides an assessment of{" "}
              {report.project_name} against industry-standard security
              frameworks. The analysis identified {allFindings.length}
              security findings across {selectedStandards.join(", ")} compliance
              frameworks.
            </p>

            {aiAnalysis?.overall_risk_assessment && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                <h3 className="text-lg font-medium text-blue-900 mb-2">
                  AI Risk Assessment
                </h3>
                <p className="text-blue-800">
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
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                {standard.name} Compliance Analysis
              </h2>

              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-500">
                      Compliance Rate
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {complianceRate}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-500">
                      Compliant Controls
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {compliantCategories}/{totalCategories}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-500">
                      Total Findings
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {standard.findings.length}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {Object.entries(standard.coverage).map(
                  ([categoryKey, coverage]) => (
                    <div
                      key={categoryKey}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {categoryKey}: {standard.categories[categoryKey]}
                          </h3>
                        </div>
                        <ComplianceStatus
                          isCompliant={coverage.compliant}
                          riskLevel={coverage.risk_level}
                        />
                      </div>

                      {!coverage.compliant && coverage.findings.length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">
                            Non-Compliance Issues ({coverage.findings.length})
                          </h4>
                          <div className="space-y-2">
                            {coverage.findings
                              .slice(0, reportFormat === "summary" ? 3 : 10)
                              .map((finding, index) => (
                                <div
                                  key={index}
                                  className="flex items-start space-x-3 text-sm"
                                >
                                  <SeverityBadge severity={finding.severity} />
                                  <div className="flex-1">
                                    <div className="font-medium text-gray-900">
                                      {finding.title}
                                    </div>
                                    <div className="text-gray-600">
                                      {finding.file_path}:{finding.line_number}
                                    </div>
                                    {reportFormat === "detailed" && (
                                      <div className="text-gray-700 mt-1">
                                        {finding.description}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            {coverage.findings.length >
                              (reportFormat === "summary" ? 3 : 10) && (
                              <div className="text-sm text-gray-500">
                                ... and{" "}
                                {coverage.findings.length -
                                  (reportFormat === "summary" ? 3 : 10)}{" "}
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
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Detailed Findings
            </h2>
            <div className="space-y-6">
              {allFindings.map((finding, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-6"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {finding.title}
                      </h3>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <SeverityBadge severity={finding.severity} />
                        <span>CWE-{finding.cwe_id || "N/A"}</span>
                        <span>
                          {finding.file_path}:{finding.line_number}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">
                        Description
                      </h4>
                      <p className="text-sm text-gray-600">
                        {finding.description}
                      </p>
                    </div>

                    {includeCodeSnippets && finding.code_snippet && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">
                          Code Snippet
                        </h4>
                        <pre className="bg-gray-900 text-white p-3 rounded text-xs overflow-x-auto">
                          <code>{finding.code_snippet}</code>
                        </pre>
                      </div>
                    )}

                    {includeAIAnalysis &&
                      aiAnalysis?.findings_analysis?.[finding.id] && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h4 className="text-sm font-medium text-blue-900 mb-2">
                            AI Analysis
                          </h4>
                          <div className="space-y-2 text-sm text-blue-800">
                            <div>
                              <strong>Impact:</strong>{" "}
                              {
                                aiAnalysis.findings_analysis[finding.id]
                                  .impact_assessment
                              }
                            </div>
                            <div>
                              <strong>Remediation:</strong>
                              <ul className="list-disc list-inside mt-1">
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
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Recommendations
          </h2>
          <div className="space-y-4">
            {aiAnalysis?.priority_recommendations ? (
              aiAnalysis.priority_recommendations.map(
                (recommendation, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <span className="text-blue-600 font-medium">
                      {index + 1}.
                    </span>
                    <span className="text-gray-700">{recommendation}</span>
                  </div>
                )
              )
            ) : (
              <div className="space-y-4 text-gray-700">
                <div className="flex items-start space-x-3">
                  <span className="text-blue-600 font-medium">1.</span>
                  <span>
                    Address all critical and high severity findings as a
                    priority
                  </span>
                </div>
                <div className="flex items-start space-x-3">
                  <span className="text-blue-600 font-medium">2.</span>
                  <span>
                    Implement secure coding practices and regular security
                    reviews
                  </span>
                </div>
                <div className="flex items-start space-x-3">
                  <span className="text-blue-600 font-medium">3.</span>
                  <span>
                    Establish automated security testing in the CI/CD pipeline
                  </span>
                </div>
                <div className="flex items-start space-x-3">
                  <span className="text-blue-600 font-medium">4.</span>
                  <span>
                    Conduct regular security assessments and penetration testing
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 pt-8 text-center text-sm text-gray-500">
          <p>
            This report was generated by SecureDevOps AI Platform on{" "}
            {new Date().toLocaleDateString()}
          </p>
          <p>
            Report ID: {report.id} | Project: {report.project_name}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ComplianceReport;
