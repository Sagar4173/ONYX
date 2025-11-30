/**
 * ComplianceReport Component - Generate compliance-ready PDF reports
 * Enhanced UI/UX with professional styling and interactive elements
 */
import React, { useState, useRef, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { generatePDF as generateProfessionalPDF } from "../../utils/pdfGenerator";
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
  ShieldExclamationIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BoltIcon,
  CubeTransparentIcon,
  AcademicCapIcon,
  FireIcon,
  StarIcon,
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
  const [activeTab, setActiveTab] = useState("overview");
  const [expandedStandard, setExpandedStandard] = useState(null);

  // Debug logging
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

  // Generate PDF with enhanced options
  const generatePDF = async () => {
    if (!reportRef.current || !report) return;

    setIsGenerating(true);
    try {
      // Prepare report data for PDF executive summary
      const reportData = {
        totalFindings: allFindings.length,
        critical: report.findings_by_severity?.critical || 0,
        high: report.findings_by_severity?.high || 0,
        medium: report.findings_by_severity?.medium || 0,
        low: report.findings_by_severity?.low || 0,
        info: report.findings_by_severity?.info || 0,
        riskScore:
          aiAnalysis?.risk_score ||
          Math.min(
            100,
            (report.findings_by_severity?.critical || 0) * 25 +
              (report.findings_by_severity?.high || 0) * 15 +
              (report.findings_by_severity?.medium || 0) * 5 +
              (report.findings_by_severity?.low || 0) * 1
          ),
        securityScore:
          aiAnalysis?.security_score ||
          Math.max(
            0,
            100 -
              ((report.findings_by_severity?.critical || 0) * 20 +
                (report.findings_by_severity?.high || 0) * 10 +
                (report.findings_by_severity?.medium || 0) * 3)
          ),
      };

      await generateProfessionalPDF(reportRef.current, {
        filename: `compliance-report-${report.project_name}-${
          new Date().toISOString().split("T")[0]
        }.pdf`,
        title: "ONYX Security",
        subtitle: `Compliance Report - ${report.project_name}`,
        showExecutiveSummary: true,
        showTableOfContents: true,
        reportData: reportData,
        companyName: report.project_name,
        confidential: true,
      });
      toast.success("🎉 PDF report generated successfully!", {
        icon: "📄",
        duration: 3000,
      });
    } catch (error) {
      console.error("PDF generation error:", error);
      toast.error("Failed to generate PDF report. Please try again.");
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

  // Circular Progress Component for Compliance Score
  const CircularProgress = ({
    percentage,
    size = 120,
    strokeWidth = 8,
    color = "blue",
  }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percentage / 100) * circumference;

    const colorClasses = {
      green: {
        stroke: "#10b981",
        bg: "text-green-400",
        glow: "shadow-green-500/50",
      },
      yellow: {
        stroke: "#f59e0b",
        bg: "text-yellow-400",
        glow: "shadow-yellow-500/50",
      },
      red: { stroke: "#ef4444", bg: "text-red-400", glow: "shadow-red-500/50" },
      blue: {
        stroke: "#3b82f6",
        bg: "text-blue-400",
        glow: "shadow-blue-500/50",
      },
    };

    const scoreColor =
      percentage >= 80 ? "green" : percentage >= 60 ? "yellow" : "red";
    const colors = colorClasses[scoreColor];

    return (
      <div className="relative inline-flex items-center justify-center">
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-gray-700/50"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={colors.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 6px ${colors.stroke}40)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${colors.bg}`}>
            {percentage.toFixed(0)}%
          </span>
          <span className="text-xs text-gray-400 mt-1">Compliance</span>
        </div>
      </div>
    );
  };

  // Overall Compliance Score Card
  const OverallComplianceScore = ({ complianceMapping }) => {
    const overallScore = useMemo(() => {
      let totalCompliant = 0;
      let totalCategories = 0;

      Object.values(complianceMapping).forEach((standard) => {
        Object.values(standard.coverage).forEach((coverage) => {
          totalCategories++;
          if (coverage.compliant) totalCompliant++;
        });
      });

      return totalCategories > 0 ? (totalCompliant / totalCategories) * 100 : 0;
    }, [complianceMapping]);

    const getGrade = (score) => {
      if (score >= 90)
        return { grade: "A+", color: "text-green-400", bg: "bg-green-500/20" };
      if (score >= 80)
        return { grade: "A", color: "text-green-400", bg: "bg-green-500/20" };
      if (score >= 70)
        return { grade: "B", color: "text-blue-400", bg: "bg-blue-500/20" };
      if (score >= 60)
        return { grade: "C", color: "text-yellow-400", bg: "bg-yellow-500/20" };
      if (score >= 50)
        return { grade: "D", color: "text-orange-400", bg: "bg-orange-500/20" };
      return { grade: "F", color: "text-red-400", bg: "bg-red-500/20" };
    };

    const gradeInfo = getGrade(overallScore);

    return (
      <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-2xl p-6 border border-gray-700/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <ShieldCheckIcon className="h-5 w-5 text-blue-400" />
            Overall Compliance Score
          </h3>
          <div
            className={`px-3 py-1.5 rounded-lg ${gradeInfo.bg} ${gradeInfo.color} font-bold text-lg`}
          >
            Grade: {gradeInfo.grade}
          </div>
        </div>
        <div className="flex items-center justify-center py-4">
          <CircularProgress
            percentage={overallScore}
            size={160}
            strokeWidth={12}
          />
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3">
          {Object.entries(complianceMapping).map(([key, standard]) => {
            const compliant = Object.values(standard.coverage).filter(
              (c) => c.compliant
            ).length;
            const total = Object.values(standard.coverage).length;
            const pct = (compliant / total) * 100;
            return (
              <div
                key={key}
                className="text-center p-3 bg-gray-800/50 rounded-lg border border-gray-700/30"
              >
                <div
                  className={`text-sm font-medium ${
                    pct >= 80
                      ? "text-green-400"
                      : pct >= 60
                      ? "text-yellow-400"
                      : "text-red-400"
                  }`}
                >
                  {pct.toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">{key}</div>
              </div>
            );
          })}
        </div>
      </div>
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
        {/* Enhanced Header with Gradient Background */}
        <div className="mb-8 no-print">
          <div className="flex items-center mb-4">
            <Link
              to={`/report/${reportId}`}
              className="inline-flex items-center text-sm text-gray-400 hover:text-white transition-colors duration-200 group"
            >
              <ArrowLeftIcon className="h-4 w-4 mr-1 group-hover:-translate-x-1 transition-transform" />
              Back to Report Details
            </Link>
          </div>

          <div className="bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-cyan-600/20 rounded-2xl p-6 border border-gray-700/50 backdrop-blur-sm">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg shadow-blue-500/25">
                  <ShieldCheckIcon className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                    Compliance Report
                    <span className="px-2 py-1 text-xs font-medium bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">
                      v2.0
                    </span>
                  </h1>
                  <p className="mt-1 text-gray-400 flex items-center gap-2">
                    <CubeTransparentIcon className="h-4 w-4" />
                    {report.project_name}
                    <span className="text-gray-600">•</span>
                    <CalendarIcon className="h-4 w-4" />
                    {utils.formatDate(report.created_at)}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={printReport}
                  className="inline-flex items-center px-4 py-2.5 border border-gray-600 text-sm font-medium rounded-xl text-gray-300 bg-gray-800/50 hover:bg-gray-700/50 hover:text-white hover:border-gray-500 transition-all duration-200 gap-2"
                >
                  <PrinterIcon className="h-4 w-4" />
                  Print
                </button>

                <button
                  onClick={generatePDF}
                  disabled={isGenerating}
                  className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 gap-2"
                >
                  {isGenerating ? (
                    <>
                      <RefreshIcon className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <DownloadIcon className="h-4 w-4" />
                      Download PDF
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Quick Stats Bar */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-xl border border-gray-700/30">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <DocumentTextIcon className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Total Findings</p>
                  <p className="text-lg font-semibold text-white">
                    {allFindings.length}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-xl border border-gray-700/30">
                <div className="p-2 bg-red-500/20 rounded-lg">
                  <FireIcon className="h-5 w-5 text-red-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Critical/High</p>
                  <p className="text-lg font-semibold text-white">
                    {(report.findings_by_severity?.critical || 0) +
                      (report.findings_by_severity?.high || 0)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-xl border border-gray-700/30">
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <CheckCircleIcon className="h-5 w-5 text-green-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Standards</p>
                  <p className="text-lg font-semibold text-white">
                    {selectedStandards.length}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-xl border border-gray-700/30">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <SparklesIcon className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">AI Analysis</p>
                  <p className="text-lg font-semibold text-white">
                    {aiAnalysis ? "Available" : "Pending"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6 no-print">
          <div className="flex gap-2 p-1 bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-x-auto">
            {[
              { id: "overview", label: "Overview", icon: ChartBarIcon },
              {
                id: "compliance",
                label: "Compliance Analysis",
                icon: ShieldCheckIcon,
              },
              {
                id: "findings",
                label: "Detailed Findings",
                icon: ExclamationTriangleIcon,
              },
              {
                id: "recommendations",
                label: "Recommendations",
                icon: LightBulbIcon,
              },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                  activeTab === tab.id
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                    : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Configuration Panel - Enhanced Design */}
        <div className="glass-container rounded-2xl p-6 mb-8 no-print border border-gray-700/50 bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <CubeTransparentIcon className="h-5 w-5 text-blue-400" />
            Report Configuration
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Compliance Standards Selection */}
            <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
              <label className="flex items-center gap-2 text-sm font-semibold text-white mb-4">
                <ShieldCheckIcon className="h-4 w-4 text-green-400" />
                Compliance Standards
              </label>
              <div className="space-y-3">
                {Object.keys(complianceStandards).map((standard) => (
                  <label
                    key={standard}
                    className={`flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                      selectedStandards.includes(standard)
                        ? "bg-blue-500/20 border-blue-500/50"
                        : "bg-gray-800/50 border-gray-700/30 hover:border-gray-600"
                    }`}
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
                    <div className="ml-3">
                      <span className="text-sm font-medium text-white">
                        {standard}
                      </span>
                      <p className="text-xs text-gray-500">
                        {complianceStandards[standard].version}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Report Format Selection */}
            <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
              <label className="flex items-center gap-2 text-sm font-semibold text-white mb-4">
                <DocumentTextIcon className="h-4 w-4 text-purple-400" />
                Report Format
              </label>
              <div className="space-y-2">
                {[
                  {
                    value: "detailed",
                    label: "Detailed Report",
                    desc: "Full findings & code",
                  },
                  {
                    value: "summary",
                    label: "Executive Summary",
                    desc: "High-level overview",
                  },
                  {
                    value: "technical",
                    label: "Technical Report",
                    desc: "Technical details only",
                  },
                ].map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-start p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                      reportFormat === option.value
                        ? "bg-purple-500/20 border-purple-500/50"
                        : "bg-gray-800/50 border-gray-700/30 hover:border-gray-600"
                    }`}
                  >
                    <input
                      type="radio"
                      name="reportFormat"
                      value={option.value}
                      checked={reportFormat === option.value}
                      onChange={(e) => setReportFormat(e.target.value)}
                      className="h-4 w-4 mt-0.5 text-purple-500 bg-gray-700 border-gray-600 focus:ring-purple-500 focus:ring-offset-gray-900"
                    />
                    <div className="ml-3">
                      <span className="text-sm font-medium text-white">
                        {option.label}
                      </span>
                      <p className="text-xs text-gray-500">{option.desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Additional Options */}
            <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
              <label className="flex items-center gap-2 text-sm font-semibold text-white mb-4">
                <SparklesIcon className="h-4 w-4 text-yellow-400" />
                Additional Options
              </label>
              <div className="space-y-3">
                <label
                  className={`flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                    includeAIAnalysis
                      ? "bg-yellow-500/20 border-yellow-500/50"
                      : "bg-gray-800/50 border-gray-700/30 hover:border-gray-600"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={includeAIAnalysis}
                    onChange={(e) => setIncludeAIAnalysis(e.target.checked)}
                    className="h-4 w-4 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500 focus:ring-offset-gray-900"
                  />
                  <div className="ml-3">
                    <span className="text-sm font-medium text-white flex items-center gap-1">
                      AI Analysis
                      <SparklesIcon className="h-3 w-3 text-yellow-400" />
                    </span>
                    <p className="text-xs text-gray-500">Include AI insights</p>
                  </div>
                </label>
                <label
                  className={`flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                    includeCodeSnippets
                      ? "bg-cyan-500/20 border-cyan-500/50"
                      : "bg-gray-800/50 border-gray-700/30 hover:border-gray-600"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={includeCodeSnippets}
                    onChange={(e) => setIncludeCodeSnippets(e.target.checked)}
                    className="h-4 w-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500 focus:ring-offset-gray-900"
                  />
                  <div className="ml-3">
                    <span className="text-sm font-medium text-white">
                      Code Snippets
                    </span>
                    <p className="text-xs text-gray-500">
                      Show vulnerable code
                    </p>
                  </div>
                </label>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
              <label className="flex items-center gap-2 text-sm font-semibold text-white mb-4">
                <BoltIcon className="h-4 w-4 text-orange-400" />
                Quick Actions
              </label>
              <div className="space-y-2">
                <button
                  onClick={() =>
                    setSelectedStandards(Object.keys(complianceStandards))
                  }
                  className="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-600/50 hover:text-white transition-all duration-200 text-left"
                >
                  Select All Standards
                </button>
                <button
                  onClick={() => setSelectedStandards(["OWASP"])}
                  className="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-600/50 hover:text-white transition-all duration-200 text-left"
                >
                  OWASP Only
                </button>
                <button
                  onClick={() => {
                    setIncludeAIAnalysis(true);
                    setIncludeCodeSnippets(true);
                    setReportFormat("detailed");
                  }}
                  className="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-gradient-to-r from-blue-600/30 to-purple-600/30 text-white hover:from-blue-600/50 hover:to-purple-600/50 transition-all duration-200 text-left border border-blue-500/30"
                >
                  ✨ Full Report Mode
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* PDF Content */}
        <div
          ref={reportRef}
          className="glass-container rounded-2xl p-8 border border-gray-700/50"
        >
          {/* Report Header - Enhanced */}
          <div className="border-b border-gray-700/50 pb-8 mb-8">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-white">
                      Security Compliance Report
                    </h1>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-2 py-0.5 text-xs font-medium bg-blue-500/20 text-blue-400 rounded border border-blue-500/30">
                        Automated Assessment
                      </span>
                      <span className="px-2 py-0.5 text-xs font-medium bg-green-500/20 text-green-400 rounded border border-green-500/30">
                        {report.status === "completed"
                          ? "✓ Complete"
                          : report.status}
                      </span>
                    </div>
                  </div>
                </div>
                <h2 className="text-xl text-gray-400 mt-3 flex items-center gap-2">
                  <CubeTransparentIcon className="h-5 w-5" />
                  {report.project_name}
                </h2>
              </div>
              <div className="text-right">
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/30">
                  <div className="text-xs text-gray-500 mb-1">
                    Report Generated
                  </div>
                  <div className="text-sm font-medium text-white">
                    {new Date().toLocaleDateString()}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">Report ID</div>
                  <div className="text-xs font-mono text-gray-400">
                    {report.id?.substring(0, 12)}...
                  </div>
                </div>
              </div>
            </div>

            {/* Info Grid with Icons */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 rounded-xl p-4 border border-blue-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <CubeTransparentIcon className="h-4 w-4 text-blue-400" />
                  <div className="text-xs font-medium text-blue-400">
                    Project
                  </div>
                </div>
                <div className="text-white font-semibold truncate">
                  {report.project_name}
                </div>
              </div>
              <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 rounded-xl p-4 border border-purple-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <TagIcon className="h-4 w-4 text-purple-400" />
                  <div className="text-xs font-medium text-purple-400">
                    Branch
                  </div>
                </div>
                <div className="text-white font-semibold">
                  {report.branch || report.git_metadata?.branch || "main"}
                </div>
              </div>
              <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 rounded-xl p-4 border border-cyan-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <CalendarIcon className="h-4 w-4 text-cyan-400" />
                  <div className="text-xs font-medium text-cyan-400">
                    Scan Date
                  </div>
                </div>
                <div className="text-white font-semibold">
                  {utils.formatDate(report.created_at)}
                </div>
              </div>
              <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 rounded-xl p-4 border border-green-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-400" />
                  <div className="text-xs font-medium text-green-400">
                    Status
                  </div>
                </div>
                <div className="text-white font-semibold capitalize flex items-center gap-1">
                  {report.status === "completed" && (
                    <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                  )}
                  {report.status}
                </div>
              </div>
            </div>
          </div>

          {/* Executive Summary - Enhanced with AI Integration */}
          {(activeTab === "overview" || true) && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <ChartBarIcon className="h-6 w-6 text-blue-400" />
                </div>
                Executive Summary
              </h2>

              {/* Score Dashboard */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Overall Compliance Score */}
                <OverallComplianceScore complianceMapping={complianceMapping} />

                {/* Findings by Severity */}
                <div className="lg:col-span-2 bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-2xl p-6 border border-gray-700/50">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <ExclamationTriangleIcon className="h-5 w-5 text-amber-400" />
                    Findings Distribution
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {[
                      {
                        key: "critical",
                        color: "red",
                        icon: "🔴",
                        label: "Critical",
                      },
                      {
                        key: "high",
                        color: "orange",
                        icon: "🟠",
                        label: "High",
                      },
                      {
                        key: "medium",
                        color: "yellow",
                        icon: "🟡",
                        label: "Medium",
                      },
                      { key: "low", color: "blue", icon: "🔵", label: "Low" },
                      { key: "info", color: "gray", icon: "⚪", label: "Info" },
                    ].map((item) => {
                      const count =
                        report.findings_by_severity?.[item.key] || 0;
                      const bgColors = {
                        red: "from-red-500/20 to-red-600/10 border-red-500/30",
                        orange:
                          "from-orange-500/20 to-orange-600/10 border-orange-500/30",
                        yellow:
                          "from-yellow-500/20 to-yellow-600/10 border-yellow-500/30",
                        blue: "from-blue-500/20 to-blue-600/10 border-blue-500/30",
                        gray: "from-gray-500/20 to-gray-600/10 border-gray-500/30",
                      };
                      const textColors = {
                        red: "text-red-400",
                        orange: "text-orange-400",
                        yellow: "text-yellow-400",
                        blue: "text-blue-400",
                        gray: "text-gray-400",
                      };
                      return (
                        <div
                          key={item.key}
                          className={`bg-gradient-to-br ${
                            bgColors[item.color]
                          } p-4 rounded-xl border text-center transition-transform hover:scale-105`}
                        >
                          <div className="text-xl mb-1">{item.icon}</div>
                          <div
                            className={`text-3xl font-bold ${
                              textColors[item.color]
                            }`}
                          >
                            {count}
                          </div>
                          <div className="text-xs font-medium text-gray-400 mt-1 uppercase tracking-wide">
                            {item.label}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Progress bar showing distribution */}
                  <div className="mt-6">
                    <div className="flex rounded-full overflow-hidden h-3">
                      {[
                        { key: "critical", color: "bg-red-500" },
                        { key: "high", color: "bg-orange-500" },
                        { key: "medium", color: "bg-yellow-500" },
                        { key: "low", color: "bg-blue-500" },
                        { key: "info", color: "bg-gray-500" },
                      ].map((item) => {
                        const count =
                          report.findings_by_severity?.[item.key] || 0;
                        const total = allFindings.length || 1;
                        const width = (count / total) * 100;
                        return width > 0 ? (
                          <div
                            key={item.key}
                            className={`${item.color} transition-all duration-500`}
                            style={{ width: `${width}%` }}
                            title={`${item.key}: ${count}`}
                          />
                        ) : null;
                      })}
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-gray-500">
                      <span>Total: {allFindings.length} findings</span>
                      <span>
                        Across {selectedStandards.length} compliance standards
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Summary Text */}
              <div className="prose prose-invert max-w-none bg-gray-800/30 rounded-xl p-6 border border-gray-700/30">
                <p className="text-gray-300 leading-relaxed m-0">
                  This security compliance report provides a comprehensive
                  assessment of{" "}
                  <span className="text-white font-semibold">
                    {report.project_name}
                  </span>{" "}
                  against industry-standard security frameworks. The automated
                  analysis identified{" "}
                  <span className="text-blue-400 font-semibold">
                    {allFindings.length} security findings
                  </span>{" "}
                  across the selected compliance frameworks:{" "}
                  {selectedStandards.map((s, i) => (
                    <span key={s}>
                      <span className="text-white font-medium">{s}</span>
                      {i < selectedStandards.length - 1
                        ? i === selectedStandards.length - 2
                          ? " and "
                          : ", "
                        : ""}
                    </span>
                  ))}
                  .
                </p>
              </div>

              {aiAnalysis?.overall_risk_assessment && (
                <div className="mt-6 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-blue-400 mb-3 flex items-center gap-2">
                    <SparklesIcon className="h-5 w-5" />
                    AI Risk Assessment
                    <span className="ml-2 px-2 py-0.5 text-xs bg-blue-500/20 rounded-full border border-blue-500/30">
                      Powered by AI
                    </span>
                  </h3>
                  <p className="text-blue-200 leading-relaxed">
                    {aiAnalysis.overall_risk_assessment}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Compliance Analysis - Enhanced with Interactive Elements */}
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
            const isExpanded = expandedStandard === standardKey;

            const standardIcons = {
              OWASP: "🔐",
              NIST: "🏛️",
              ISO27001: "📋",
              PCI_DSS: "💳",
            };

            const standardColors = {
              OWASP: {
                bg: "from-orange-500/20 to-red-500/20",
                border: "border-orange-500/30",
                text: "text-orange-400",
              },
              NIST: {
                bg: "from-blue-500/20 to-cyan-500/20",
                border: "border-blue-500/30",
                text: "text-blue-400",
              },
              ISO27001: {
                bg: "from-purple-500/20 to-pink-500/20",
                border: "border-purple-500/30",
                text: "text-purple-400",
              },
              PCI_DSS: {
                bg: "from-green-500/20 to-emerald-500/20",
                border: "border-green-500/30",
                text: "text-green-400",
              },
            };

            const colors = standardColors[standardKey] || standardColors.OWASP;

            return (
              <div key={standardKey} className="mb-8 page-break-before">
                {/* Standard Header Card */}
                <div
                  className={`bg-gradient-to-r ${colors.bg} rounded-2xl p-6 border ${colors.border} mb-6 cursor-pointer transition-all duration-300 hover:shadow-lg`}
                  onClick={() =>
                    setExpandedStandard(isExpanded ? null : standardKey)
                  }
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-4xl">
                        {standardIcons[standardKey] || "🛡️"}
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                          {standard.name}
                          <span
                            className={`text-sm font-normal ${colors.text}`}
                          >
                            v{complianceStandards[standardKey]?.version}
                          </span>
                        </h2>
                        <p className="text-gray-400 text-sm mt-1">
                          {complianceStandards[standardKey]?.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      {/* Circular Progress for this standard */}
                      <div className="relative">
                        <CircularProgress
                          percentage={parseFloat(complianceRate)}
                          size={80}
                          strokeWidth={6}
                        />
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">
                          Controls Compliant
                        </div>
                        <div className="text-2xl font-bold text-white">
                          <span className="text-green-400">
                            {compliantCategories}
                          </span>
                          <span className="text-gray-500">
                            /{totalCategories}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="bg-gray-800/50 p-6 rounded-xl mb-6 border border-gray-700/30">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div className="text-center p-4 bg-gray-900/50 rounded-lg">
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
                      <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                        Compliance Rate
                      </div>
                    </div>
                    <div className="text-center p-4 bg-gray-900/50 rounded-lg">
                      <div className="text-3xl font-bold text-green-400">
                        {compliantCategories}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                        Compliant
                      </div>
                    </div>
                    <div className="text-center p-4 bg-gray-900/50 rounded-lg">
                      <div className="text-3xl font-bold text-red-400">
                        {totalCategories - compliantCategories}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                        Non-Compliant
                      </div>
                    </div>
                    <div className="text-center p-4 bg-gray-900/50 rounded-lg">
                      <div className="text-3xl font-bold text-blue-400">
                        {standard.findings.length}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                        Total Findings
                      </div>
                    </div>
                  </div>

                  {/* Enhanced Compliance Progress Bar */}
                  <div className="mt-6">
                    <div className="flex justify-between text-xs text-gray-500 mb-2">
                      <span>0%</span>
                      <span>Compliance Progress</span>
                      <span>100%</span>
                    </div>
                    <div className="relative w-full bg-gray-700 rounded-full h-4 overflow-hidden">
                      <div
                        className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${
                          complianceRate >= 80
                            ? "bg-gradient-to-r from-green-500 to-emerald-400"
                            : complianceRate >= 50
                            ? "bg-gradient-to-r from-yellow-500 to-orange-400"
                            : "bg-gradient-to-r from-red-500 to-pink-400"
                        }`}
                        style={{ width: `${complianceRate}%` }}
                      >
                        <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                      </div>
                      {/* Milestone markers */}
                      <div className="absolute top-0 left-1/4 w-0.5 h-full bg-gray-600"></div>
                      <div className="absolute top-0 left-1/2 w-0.5 h-full bg-gray-600"></div>
                      <div className="absolute top-0 left-3/4 w-0.5 h-full bg-gray-600"></div>
                    </div>
                  </div>
                </div>

                {/* Control Categories Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(standard.coverage).map(
                    ([categoryKey, coverage]) => (
                      <div
                        key={categoryKey}
                        className={`bg-gray-800/30 border rounded-xl p-5 transition-all duration-300 hover:bg-gray-800/50 ${
                          coverage.compliant
                            ? "border-green-500/30 hover:border-green-500/50"
                            : "border-red-500/30 hover:border-red-500/50"
                        }`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-lg ${
                                  coverage.compliant
                                    ? "text-green-400"
                                    : "text-red-400"
                                }`}
                              >
                                {coverage.compliant ? "✓" : "✗"}
                              </span>
                              <h3 className="text-base font-semibold text-white">
                                {categoryKey}
                              </h3>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">
                              {standard.categories[categoryKey]}
                            </p>
                          </div>
                          <ComplianceStatus
                            isCompliant={coverage.compliant}
                            riskLevel={coverage.risk_level}
                          />
                        </div>

                        {!coverage.compliant &&
                          coverage.findings.length > 0 && (
                            <div className="mt-4 pt-4 border-t border-gray-700/50">
                              <h4 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wide flex items-center gap-2">
                                <ExclamationTriangleIcon className="h-3 w-3" />
                                Issues Found ({coverage.findings.length})
                              </h4>
                              <div className="space-y-2">
                                {coverage.findings
                                  .slice(0, reportFormat === "summary" ? 2 : 5)
                                  .map((finding, index) => (
                                    <div
                                      key={index}
                                      className="flex items-start gap-3 text-sm bg-gray-900/50 rounded-lg p-3 border border-gray-700/30"
                                    >
                                      <SeverityBadge
                                        severity={finding.severity}
                                      />
                                      <div className="flex-1 min-w-0">
                                        <div className="font-medium text-white truncate">
                                          {finding.title}
                                        </div>
                                        <div className="text-gray-500 text-xs truncate mt-0.5">
                                          📁 {finding.file_path}:
                                          {finding.line_number}
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                {coverage.findings.length >
                                  (reportFormat === "summary" ? 2 : 5) && (
                                  <div className="text-xs text-gray-500 text-center py-2 bg-gray-900/30 rounded-lg">
                                    +{" "}
                                    {coverage.findings.length -
                                      (reportFormat === "summary" ? 2 : 5)}{" "}
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

          {/* Detailed Findings - Enhanced with Better Visualization */}
          {reportFormat === "detailed" && (
            <div className="mb-8 page-break-before">
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                <div className="p-2 bg-amber-500/20 rounded-lg">
                  <ExclamationTriangleIcon className="h-6 w-6 text-amber-400" />
                </div>
                Detailed Findings
                <span className="ml-2 px-3 py-1 text-sm font-medium bg-gray-700 text-gray-300 rounded-full">
                  {allFindings.length} total
                </span>
              </h2>

              {/* Findings Filter Chips */}
              <div className="flex flex-wrap gap-2 mb-6">
                {["all", "critical", "high", "medium", "low"].map((filter) => (
                  <button
                    key={filter}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      filter === "all"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50 hover:text-white border border-gray-700/50"
                    }`}
                  >
                    {filter.charAt(0).toUpperCase() + filter.slice(1)}
                    {filter !== "all" && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-gray-700 rounded">
                        {report.findings_by_severity?.[filter] || 0}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              <div className="space-y-4">
                {allFindings.map((finding, index) => (
                  <div
                    key={index}
                    className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 rounded-xl overflow-hidden hover:border-gray-600/50 transition-all duration-300 group"
                  >
                    {/* Finding Header */}
                    <div className="p-5 border-b border-gray-700/30">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-sm font-mono text-gray-500">
                              #{index + 1}
                            </span>
                            <SeverityBadge severity={finding.severity} />
                            {finding.cwe_id && (
                              <span className="px-2 py-1 text-xs font-mono bg-purple-500/20 text-purple-400 rounded border border-purple-500/30">
                                CWE-{finding.cwe_id}
                              </span>
                            )}
                          </div>
                          <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                            {finding.title}
                          </h3>
                        </div>
                        <div className="flex-shrink-0 text-right">
                          <div className="text-xs text-gray-500 mb-1">
                            Location
                          </div>
                          <div className="text-sm font-mono text-gray-400 bg-gray-800 px-2 py-1 rounded truncate max-w-xs">
                            📁 {finding.file_path?.split("/").pop()}:
                            {finding.line_number}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Finding Content */}
                    <div className="p-5 space-y-4">
                      {/* Description */}
                      <div>
                        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-2">
                          <InformationCircleIcon className="h-3.5 w-3.5" />
                          Description
                        </h4>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {finding.description}
                        </p>
                      </div>

                      {/* File Path */}
                      <div>
                        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                          File Location
                        </h4>
                        <code className="block text-xs text-cyan-400 bg-gray-900/70 p-3 rounded-lg border border-gray-700/50 overflow-x-auto">
                          {finding.file_path}:{finding.line_number}
                        </code>
                      </div>

                      {/* Code Snippet */}
                      {includeCodeSnippets && finding.code_snippet && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-2">
                            💻 Vulnerable Code
                          </h4>
                          <pre className="bg-gray-900 text-gray-300 p-4 rounded-lg text-xs overflow-x-auto border border-gray-700/50 max-h-48">
                            <code className="language-javascript">
                              {finding.code_snippet}
                            </code>
                          </pre>
                        </div>
                      )}

                      {/* AI Analysis Section */}
                      {includeAIAnalysis &&
                        aiAnalysis?.findings_analysis?.[finding.id] && (
                          <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-5 mt-4">
                            <h4 className="text-sm font-semibold text-blue-400 mb-4 flex items-center gap-2">
                              <SparklesIcon className="h-4 w-4" />
                              AI-Powered Analysis
                              <span className="ml-auto text-xs text-blue-400/60 font-normal">
                                Powered by AI
                              </span>
                            </h4>
                            <div className="grid md:grid-cols-2 gap-4">
                              <div>
                                <h5 className="text-xs font-medium text-blue-300 mb-2">
                                  🎯 Impact Assessment
                                </h5>
                                <p className="text-sm text-blue-200/80">
                                  {
                                    aiAnalysis.findings_analysis[finding.id]
                                      .impact_assessment
                                  }
                                </p>
                              </div>
                              <div>
                                <h5 className="text-xs font-medium text-blue-300 mb-2">
                                  🔧 Remediation Steps
                                </h5>
                                <ul className="space-y-1">
                                  {aiAnalysis.findings_analysis[
                                    finding.id
                                  ].remediation_steps
                                    ?.slice(0, 3)
                                    .map((step, i) => (
                                      <li
                                        key={i}
                                        className="text-sm text-blue-200/80 flex items-start gap-2"
                                      >
                                        <span className="text-blue-400 mt-0.5">
                                          {i + 1}.
                                        </span>
                                        {step}
                                      </li>
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

          {/* Recommendations - Enhanced with Priority Indicators */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <div className="p-2 bg-yellow-500/20 rounded-lg">
                <LightBulbIcon className="h-6 w-6 text-yellow-400" />
              </div>
              Security Recommendations
              <span className="ml-auto text-sm font-normal text-gray-400">
                Prioritized Action Items
              </span>
            </h2>

            <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-2xl p-6 border border-gray-700/50">
              <div className="space-y-4">
                {aiAnalysis?.priority_recommendations ? (
                  aiAnalysis.priority_recommendations.map(
                    (recommendation, index) => {
                      const priorityColors = [
                        {
                          bg: "bg-red-500/20",
                          border: "border-red-500/30",
                          text: "text-red-400",
                          label: "Critical",
                        },
                        {
                          bg: "bg-orange-500/20",
                          border: "border-orange-500/30",
                          text: "text-orange-400",
                          label: "High",
                        },
                        {
                          bg: "bg-yellow-500/20",
                          border: "border-yellow-500/30",
                          text: "text-yellow-400",
                          label: "Medium",
                        },
                        {
                          bg: "bg-blue-500/20",
                          border: "border-blue-500/30",
                          text: "text-blue-400",
                          label: "Normal",
                        },
                        {
                          bg: "bg-green-500/20",
                          border: "border-green-500/30",
                          text: "text-green-400",
                          label: "Low",
                        },
                      ];
                      const priority =
                        priorityColors[
                          Math.min(index, priorityColors.length - 1)
                        ];

                      return (
                        <div
                          key={index}
                          className={`flex items-start gap-4 p-4 ${priority.bg} rounded-xl border ${priority.border} hover:scale-[1.01] transition-transform duration-200`}
                        >
                          <div
                            className={`flex-shrink-0 w-10 h-10 ${priority.bg} ${priority.text} rounded-xl flex items-center justify-center text-lg font-bold border ${priority.border}`}
                          >
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span
                                className={`text-xs font-semibold ${priority.text} uppercase tracking-wide`}
                              >
                                {priority.label} Priority
                              </span>
                            </div>
                            <p className="text-gray-200">{recommendation}</p>
                          </div>
                          <div className={`flex-shrink-0 ${priority.text}`}>
                            <ArrowTrendingUpIcon className="h-5 w-5" />
                          </div>
                        </div>
                      );
                    }
                  )
                ) : (
                  <div className="space-y-4">
                    {[
                      {
                        icon: "🚨",
                        priority: "Critical",
                        color: "red",
                        text: "Address all critical and high severity findings as an immediate priority to prevent potential security breaches.",
                      },
                      {
                        icon: "🔒",
                        priority: "High",
                        color: "orange",
                        text: "Implement secure coding practices and establish regular security code reviews for all new development.",
                      },
                      {
                        icon: "🔄",
                        priority: "Medium",
                        color: "yellow",
                        text: "Integrate automated security testing (SAST/DAST) into your CI/CD pipeline for continuous monitoring.",
                      },
                      {
                        icon: "📊",
                        priority: "Normal",
                        color: "blue",
                        text: "Conduct regular security assessments, penetration testing, and vulnerability scanning.",
                      },
                      {
                        icon: "📚",
                        priority: "Ongoing",
                        color: "green",
                        text: "Provide security awareness training and maintain up-to-date documentation of security policies.",
                      },
                    ].map((item, index) => {
                      const colorClasses = {
                        red: {
                          bg: "bg-red-500/20",
                          border: "border-red-500/30",
                          text: "text-red-400",
                        },
                        orange: {
                          bg: "bg-orange-500/20",
                          border: "border-orange-500/30",
                          text: "text-orange-400",
                        },
                        yellow: {
                          bg: "bg-yellow-500/20",
                          border: "border-yellow-500/30",
                          text: "text-yellow-400",
                        },
                        blue: {
                          bg: "bg-blue-500/20",
                          border: "border-blue-500/30",
                          text: "text-blue-400",
                        },
                        green: {
                          bg: "bg-green-500/20",
                          border: "border-green-500/30",
                          text: "text-green-400",
                        },
                      };
                      const colors = colorClasses[item.color];

                      return (
                        <div
                          key={index}
                          className={`flex items-start gap-4 p-4 ${colors.bg} rounded-xl border ${colors.border} hover:scale-[1.01] transition-transform duration-200`}
                        >
                          <div
                            className={`flex-shrink-0 w-10 h-10 ${colors.bg} rounded-xl flex items-center justify-center text-xl border ${colors.border}`}
                          >
                            {item.icon}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span
                                className={`text-xs font-semibold ${colors.text} uppercase tracking-wide`}
                              >
                                {item.priority} Priority
                              </span>
                            </div>
                            <p className="text-gray-200">{item.text}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enhanced Footer */}
          <div className="border-t border-gray-700/50 pt-8 mt-8">
            <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-2xl p-6 border border-gray-700/30">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">
                      ONYX Security Intelligence
                    </div>
                    <div className="text-xs text-gray-500">
                      Automated Security Assessment & Compliance
                    </div>
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">
                    Report Generated
                  </div>
                  <div className="text-sm text-gray-300">
                    {new Date().toLocaleDateString("en-US", {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-gray-500 mb-1">
                    Report Details
                  </div>
                  <div className="text-xs font-mono text-gray-400">
                    ID: {report.id?.substring(0, 8)}...
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {report.project_name}
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-gray-700/30 flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
                <span>© {new Date().getFullYear()} ONYX Security</span>
                <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                <span className="flex items-center gap-1">
                  🔒 Confidential Document
                </span>
                <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                <span>Version 2.0</span>
                <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                <span className="flex items-center gap-1">
                  <SparklesIcon className="h-3 w-3 text-blue-400" />
                  AI-Enhanced Analysis
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceReport;
