# ReportDetails Remaster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster the `/report/:id` page with ParticleBackground, animated tab navigation with count badges, pill severity filters, stagger-animated findings, enhanced scanner cards, and extracted compliance utility.

**Architecture:** Single-page orchestrator (`ReportDetails.jsx`) with particles ambient layer, glassmorphism info bar, animated tab nav, pill-based severity filter, and stagger-animated finding cards. Inline compliance logic extracted to pure utility.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, Canvas API, react-router-dom, @tanstack/react-query

## Global Constraints
- Zero new npm dependencies
- Follow ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- Lint: `npx eslint src/` must pass with 0 errors, 0 warnings

---
### File Structure

```
frontend/src/
├── utils/
│   └── complianceMapping.js     (NEW — extracted pure utility)
├── components/reports/
│   ├── ReportDetails.jsx        (REWRITE — orchestrator with particles, animated tabs, pill filters)
│   └── ScannerResultCard.jsx    (ENHANCE — severity breakdown, framer-motion entry)
```

---
### Task 1: complianceMapping.js — Extract Utility

**Files:**
- Create: `frontend/src/utils/complianceMapping.js`

**Interfaces:**
- Exports: `mapFindingToCompliance(finding, standard)` → array of category codes
- Pure function, same logic as current inline version in ReportDetails.jsx

- [ ] **Step 1: Create complianceMapping.js**

```js
export const COMPLIANCE_STANDARDS = {
  OWASP: {
    name: "OWASP Top 10",
    description: "Web Application Security",
    color: "#f43f5e",
    categories: [
      { id: "A01", name: "Broken Access Control", description: "Failure to enforce user permissions" },
      { id: "A02", name: "Cryptographic Failures", description: "Weak or missing encryption" },
      { id: "A03", name: "Injection", description: "SQL, XSS, and command injection" },
      { id: "A04", name: "Insecure Design", description: "Architecture-level flaws" },
      { id: "A05", name: "Security Misconfiguration", description: "Default or insecure configs" },
      { id: "A06", name: "Vulnerable Components", description: "Outdated dependencies" },
      { id: "A07", name: "Auth Failures", description: "Broken authentication" },
      { id: "A08", name: "Data Integrity", description: "Software supply chain" },
      { id: "A09", name: "Logging Failures", description: "Insufficient monitoring" },
      { id: "A10", name: "SSRF", description: "Server-side request forgery" },
    ],
  },
  NIST: {
    name: "NIST CSF",
    description: "Cybersecurity Framework",
    color: "#3b82f6",
    categories: [
      { id: "ID", name: "Identify", description: "Asset management and risk assessment" },
      { id: "PR", name: "Protect", description: "Safeguards and access control" },
      { id: "DE", name: "Detect", description: "Monitoring and anomaly detection" },
      { id: "RS", name: "Respond", description: "Incident response planning" },
      { id: "RC", name: "Recover", description: "Resilience and restoration" },
    ],
  },
  ISO27001: {
    name: "ISO 27001",
    description: "Information Security Standard",
    color: "#8b5cf6",
    categories: [
      { id: "A.5", name: "Security Policies", description: "Management direction" },
      { id: "A.6", name: "Organization", description: "Internal security roles" },
      { id: "A.7", name: "HR Security", description: "Personnel vetting" },
      { id: "A.8", name: "Asset Management", description: "Asset inventory" },
      { id: "A.9", name: "Access Control", description: "Authentication and authorization" },
      { id: "A.10", name: "Cryptography", description: "Encryption key management" },
      { id: "A.11", name: "Physical Security", description: "Facility protection" },
      { id: "A.12", name: "Operations", description: "Change and capacity management" },
      { id: "A.13", name: "Communications", description: "Network security" },
      { id: "A.14", name: "Development", description: "Secure development lifecycle" },
      { id: "A.15", name: "Supplier", description: "Third-party security" },
      { id: "A.16", name: "Incident", description: "Incident management" },
    ],
  },
};

export const mapFindingToCompliance = (finding, standard) => {
  const description = (finding.description || finding.title || "").toLowerCase();
  const categories = [];

  switch (standard) {
    case "OWASP":
      if (description.includes("access") || description.includes("authorization") || description.includes("permission")) categories.push("A01");
      if (description.includes("crypto") || description.includes("encryption") || description.includes("hash") || description.includes("password")) categories.push("A02");
      if (description.includes("injection") || description.includes("sql") || description.includes("xss") || description.includes("command")) categories.push("A03");
      if (description.includes("misconfiguration") || description.includes("default") || description.includes("config")) categories.push("A05");
      if (description.includes("component") || description.includes("dependency") || description.includes("outdated") || description.includes("vulnerable")) categories.push("A06");
      if (description.includes("auth") || description.includes("session") || description.includes("token")) categories.push("A07");
      if (categories.length === 0) categories.push("A05");
      break;
    case "NIST":
      categories.push("ID");
      if (description.includes("protect") || description.includes("secure") || description.includes("encrypt")) categories.push("PR");
      if (description.includes("detect") || description.includes("monitor") || description.includes("log")) categories.push("DE");
      break;
    case "ISO27001":
      if (description.includes("access") || description.includes("authentication")) categories.push("A.9");
      if (description.includes("crypto") || description.includes("encryption")) categories.push("A.10");
      if (description.includes("development") || description.includes("code")) categories.push("A.14");
      if (categories.length === 0) categories.push("A.12");
      break;
  }
  return categories;
};
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/utils/complianceMapping.js`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/utils/complianceMapping.js
git commit -m "feat: Task 1 — extract complianceMapping utility"
```

---
### Task 2: ScannerResultCard.jsx — Enhanced

**Files:**
- Modify: `frontend/src/components/reports/ScannerResultCard.jsx`

**Interfaces:**
- Consumes: same `scanResult` + `index` props (unchanged)
- Produces: enhanced card with framer-motion entry, severity breakdown bar, findings stats

- [ ] **Step 1: Rewrite ScannerResultCard.jsx**

Replace the file:

```jsx
import { motion } from "framer-motion";
import { CpuChipIcon } from "@heroicons/react/24/outline";
import { StatusBadge } from "./ReportBadges";

const severityColors = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-cyan-500",
  info: "bg-gray-500",
};

const itemAnim = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const ScannerResultCard = ({ scanResult, index }) => {
  const summary = scanResult.summary || {};
  const totalSeverity = Object.values(summary).reduce((a, b) => a + (typeof b === "number" ? b : 0), 0);
  const findingsCount = scanResult.findings_count || totalSeverity || 0;

  return (
    <motion.div variants={itemAnim} className="glass-container rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <CpuChipIcon className="h-5 w-5 mr-2 text-cyan-400" />
          {scanResult.scanner}
        </h3>
        <StatusBadge status={scanResult.status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Findings</p>
          <p className="text-xl font-bold text-white">{findingsCount}</p>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Duration</p>
          <p className="text-xl font-bold text-white">{scanResult.duration_seconds ? `${Math.round(scanResult.duration_seconds)}s` : "N/A"}</p>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-sm text-gray-400">Status</p>
          <p className="text-xl font-bold text-white capitalize">{scanResult.status}</p>
        </div>
      </div>

      {totalSeverity > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Severity Breakdown</h4>
          <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden flex">
            {Object.entries(summary).map(([severity, count]) => {
              if (typeof count !== "number" || count === 0) return null;
              const pct = (count / totalSeverity) * 100;
              return <div key={severity} className={`${severityColors[severity.toLowerCase()] || "bg-gray-500"} h-full transition-all`} style={{ width: `${pct}%` }} title={`${severity}: ${count}`} />;
            })}
          </div>
          <div className="flex flex-wrap gap-3 mt-2">
            {Object.entries(summary).map(([severity, count]) => {
              if (typeof count !== "number" || count === 0) return null;
              const color = severityColors[severity.toLowerCase()] || "bg-gray-500";
              return (
                <span key={severity} className="flex items-center gap-1.5 text-xs">
                  <span className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-gray-400 capitalize">{severity}</span>
                  <span className="text-white font-medium">{count}</span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {scanResult.summary && typeof scanResult.summary === "object" && Object.keys(scanResult.summary).length > 0 && Object.values(scanResult.summary).every((v) => typeof v !== "number") && (
        <div className="mb-4">
          <h4 className="text-md font-medium text-white mb-2">Summary</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(scanResult.summary).map(([severity, count]) => {
              const color = severityColors[severity.toLowerCase()] || "bg-gray-500/20";
              return (
                <span key={severity} className={`px-2 py-1 rounded text-sm border ${color.replace("bg-", "bg-").replace("500", "500/20")} text-${color.includes("red") ? "red" : color.includes("orange") ? "orange" : color.includes("yellow") ? "yellow" : "cyan"}-400 border-${color.includes("red") ? "red" : color.includes("orange") ? "orange" : color.includes("yellow") ? "yellow" : "cyan"}-500/30`}>
                  {severity}: {count}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {scanResult.error_message && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
          <h4 className="text-md font-medium text-red-400 mb-2">Error</h4>
          <p className="text-red-300">{scanResult.error_message}</p>
        </div>
      )}
    </motion.div>
  );
};

export default ScannerResultCard;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/reports/ScannerResultCard.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/reports/ScannerResultCard.jsx
git commit -m "feat: Task 2 — ScannerResultCard with severity bar + framer-motion entry"
```

---
### Task 3: ReportDetails.jsx — Full Orchestrator Rewrite

**Files:**
- Rewrite: `frontend/src/components/reports/ReportDetails.jsx`

**Interfaces:**
- Consumes: none (reads reportId from useParams, fetches report + AI analysis internally)
- Produces: fully remastered report detail page

- [ ] **Step 1: Rewrite ReportDetails.jsx**

```jsx
import { useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { generateViewPDF } from "../../utils/pdfReportGenerator";
import { reportsAPI, utils } from "../../services/api";
import toast from "react-hot-toast";
import { motion } from "framer-motion";
import {
  ArrowLeftIcon, ExclamationTriangleIcon, ShieldCheckIcon, ClockIcon, CodeBracketIcon,
  ArrowPathIcon, CheckCircleIcon, ChartBarIcon, CpuChipIcon, DocumentTextIcon, SparklesIcon,
} from "@heroicons/react/24/outline";
import { PageContainer, PageHeader, LoadingState, ErrorState } from "../../layouts";
import ParticleBackground from "../projects/ParticleBackground";
import { ComplianceMapping } from "./ComplianceMapping";
import { ReportCharts } from "./ReportCharts";
import { ExportDropdown } from "./ReportExport";
import { AISection } from "./AISection";
import { StatusBadge } from "./ReportBadges";
import SecretDetectionSummary from "./SecretDetectionSummary";
import FindingCard from "./FindingCard";
import ScannerResultCard from "./ScannerResultCard";
import { COMPLIANCE_STANDARDS, mapFindingToCompliance } from "../../utils/complianceMapping";

const TABS = [
  { id: "overview", name: "Overview", icon: ChartBarIcon },
  { id: "findings", name: "Findings", icon: ShieldCheckIcon },
  { id: "ai-analysis", name: "AI Analysis", icon: SparklesIcon },
  { id: "compliance", name: "Compliance", icon: DocumentTextIcon },
  { id: "scanners", name: "Scanners", icon: CpuChipIcon },
];

const SEVERITY_PILLS = [
  { value: "all", label: "All", color: "" },
  { value: "critical", label: "Critical", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  { value: "high", label: "High", color: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
  { value: "medium", label: "Medium", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
  { value: "low", label: "Low", color: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
];

const ReportDetails = () => {
  const { reportId } = useParams();
  const reportRef = useRef();
  const [activeTab, setActiveTab] = useState("overview");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedStandards, setSelectedStandards] = useState(["OWASP", "NIST"]);

  const isValidReportId = reportId && reportId !== "undefined" && reportId !== "null";

  const { data: report, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => reportsAPI.getReport(reportId),
    enabled: isValidReportId,
    retry: false,
  });

  const { data: aiAnalysis, isLoading: aiLoading, error: aiError } = useQuery({
    queryKey: ["ai-analysis", reportId],
    queryFn: () => reportsAPI.getAIAnalysis(reportId),
    enabled: isValidReportId && !!report,
    retry: false,
  });

  const handleGenerateViewPDF = async () => {
    await generateViewPDF({ report, aiAnalysis, reportId, setIsGenerating, toast });
  };

  if (!isValidReportId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="glass-container rounded-2xl p-8 text-center">
            <ExclamationTriangleIcon className="h-16 w-16 text-amber-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Invalid Report ID</h2>
            <p className="text-gray-400 mb-6">The report ID is missing or invalid. Please select a valid report.</p>
            <Link to="/" className="inline-flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
              <ArrowLeftIcon className="h-4 w-4 mr-2" /> Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) return <LoadingState message="Loading report..." cards={3} />;

  if (isError || !report) {
    return <ErrorState title="Report Not Found" message={error?.message || "The requested report could not be found."} onRetry={refetch} />;
  }

  const getFilteredFindings = () => {
    let allFindings = [];
    if (report.findings) allFindings = allFindings.concat(report.findings);
    else if (report.scan_results) report.scan_results.forEach((sr) => { if (sr.findings) allFindings = allFindings.concat(sr.findings); });
    return severityFilter === "all" ? allFindings : allFindings.filter((f) => f.severity === severityFilter);
  };

  const filteredFindings = getFilteredFindings();
  const totalFindings = report.findings?.length || report.scan_results?.reduce((a, sr) => a + (sr.findings?.length || 0), 0) || 0;
  const hasAiAnalysis = !!aiAnalysis;

  const tabAnim = { hidden: { opacity: 0, y: -5 }, show: { opacity: 1, y: 0 } };

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto print:max-w-none relative z-10">
          <div className="no-print">
            <PageHeader title="Security Scan Report" description={report.project_name} icon={DocumentTextIcon}
              breadcrumb={["Reports", report.project_name]}
              actions={
                <div className="flex items-center space-x-2">
                  <ExportDropdown reportId={reportId} onGeneratePDF={handleGenerateViewPDF} isGenerating={isGenerating} />
                  <button onClick={handleGenerateViewPDF} disabled={isGenerating}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium disabled:opacity-50 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                    {isGenerating ? <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" /> : <DocumentTextIcon className="h-4 w-4 mr-2" />}
                    {isGenerating ? "Generating..." : "Download PDF"}
                  </button>
                </div>
              }
            />
          </div>

          <div className="hidden print:block print:mb-8 print:pb-4 print:border-b-2 print:border-cyan-600">
            <div className="print:text-center">
              <h1 className="print:text-2xl print:font-bold print:text-cyan-800 print:mb-2">ONYX Security Report</h1>
              <p className="print:text-gray-600 print:text-sm">Security Analysis Report for {report.project_name}</p>
              <p className="print:text-gray-500 print:text-xs print:mt-1">Generated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })} | Report ID: {reportId}</p>
            </div>
          </div>

          <div ref={reportRef} className="print:bg-white">
            <div className="bg-gray-800/40 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 mb-8 print:bg-white print:shadow-none print:border print:border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-6 text-sm text-gray-400 print:text-gray-600">
                    <div className="flex items-center"><ClockIcon className="h-4 w-4 mr-1" /> {utils.formatDate(report.created_at)}</div>
                    <div className="flex items-center"><CodeBracketIcon className="h-4 w-4 mr-1" /> {report.git_metadata?.repository_url}</div>
                    <div className="flex items-center"><span className="text-xs bg-gray-700 print:bg-gray-200 px-2 py-1 rounded print:text-gray-700">{report.git_metadata?.branch || "main"}</span></div>
                  </div>
                </div>
                <div className="text-right">
                  <StatusBadge status={report.status} />
                  <div className="mt-2 text-sm text-gray-400 print:text-gray-600">Scan ID: {report.scan_id}</div>
                  {report.duration_seconds && <div className="text-sm text-gray-400 print:text-gray-600">Duration: {Math.round(report.duration_seconds)}s</div>}
                </div>
              </div>
            </div>

            <div className="mb-8 no-print">
              <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-1">
                <nav className="flex space-x-1">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    const count = tab.id === "findings" ? totalFindings : tab.id === "ai-analysis" && hasAiAnalysis ? 1 : null;
                    return (
                      <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                        className={`relative flex items-center px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                          activeTab === tab.id ? "text-white" : "text-gray-400 hover:text-gray-300 hover:bg-gray-800/50"
                        }`}>
                        {activeTab === tab.id && (
                          <motion.div layoutId="tab-indicator" className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-xl" initial={false} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
                        )}
                        <span className="relative z-10 flex items-center">
                          <Icon className="h-4 w-4 mr-2" /> {tab.name}
                          {count != null && <span className={`ml-1.5 px-1.5 py-0.5 rounded text-[10px] font-bold ${activeTab === tab.id ? "bg-white/20 text-white" : "bg-gray-700/50 text-gray-400"}`}>{count}</span>}
                        </span>
                      </button>
                    );
                  })}
                </nav>
              </div>
            </div>

            <div className="space-y-8">
              {activeTab === "overview" && (
                <motion.div variants={tabAnim} initial="hidden" animate="show" className="space-y-6">
                  <ReportCharts report={report} />
                  {aiAnalysis && (
                    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center"><SparklesIcon className="h-5 w-5 mr-2 text-purple-400" /> AI Risk Assessment</h3>
                      <div className="prose prose-invert max-w-none">
                        <p className="text-gray-300">{aiAnalysis.executive_summary}</p>
                        {aiAnalysis.risk_assessment && <div className="mt-4 p-4 bg-purple-900/20 border border-purple-500/30 rounded-lg"><p className="text-purple-300">{aiAnalysis.risk_assessment}</p></div>}
                      </div>
                    </div>
                  )}
                  {report.scan_results && (
                    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Scanner Results</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {report.scan_results.map((sr, i) => (
                          <div key={sr.scanner || i} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-white">{sr.scanner}</span>
                              <StatusBadge status={sr.status} />
                            </div>
                            <div className="text-sm text-gray-400">
                              <div>Findings: {sr.findings_count || 0}</div>
                              {sr.duration_seconds && <div>Duration: {Math.round(sr.duration_seconds)}s</div>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "findings" && (
                <motion.div variants={tabAnim} initial="hidden" animate="show" className="space-y-6">
                  <SecretDetectionSummary filteredFindings={filteredFindings} />
                  <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white">Security Findings</h3>
                      <div className="flex items-center gap-2">
                        {SEVERITY_PILLS.map((pill) => (
                          <button key={pill.value} onClick={() => setSeverityFilter(pill.value)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                              severityFilter === pill.value
                                ? pill.color || "bg-gray-700/70 text-white"
                                : "text-gray-400 hover:text-white hover:bg-gray-700/30"
                            }`}>
                            {pill.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <motion.div className="space-y-4" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}>
                    {filteredFindings.length > 0 ? (
                      filteredFindings.map((finding, i) => (
                        <motion.div key={finding.id || i} variants={{ hidden: { opacity: 0, x: -10 }, show: { opacity: 1, x: 0 } }}>
                          <FindingCard finding={finding} index={i} />
                        </motion.div>
                      ))
                    ) : (
                      <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 text-center">
                        <CheckCircleIcon className="h-12 w-12 text-green-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-white mb-2">No Findings</h3>
                        <p className="text-gray-400">{severityFilter === "all" ? "No security findings were detected in this scan." : `No ${severityFilter} severity findings found.`}</p>
                      </div>
                    )}
                  </motion.div>
                </motion.div>
              )}

              {activeTab === "ai-analysis" && <AISection aiAnalysis={aiAnalysis} aiLoading={aiLoading} aiError={aiError} />}

              {activeTab === "scanners" && (
                <motion.div className="space-y-6" initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}>
                  {report.scan_results && report.scan_results.length > 0 ? (
                    report.scan_results.map((sr, i) => <ScannerResultCard key={sr.scanner || i} scanResult={sr} index={i} />)
                  ) : (
                    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 text-center">
                      <CpuChipIcon className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-white mb-2">No Scanner Results</h3>
                      <p className="text-gray-400">No detailed scanner results are available for this report.</p>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "compliance" && (
                <ComplianceMapping
                  COMPLIANCE_STANDARDS={COMPLIANCE_STANDARDS}
                  selectedStandards={selectedStandards}
                  onToggleStandard={(std) => {
                    setSelectedStandards((prev) => prev.includes(std) ? prev.filter((s) => s !== std) : [...prev, std]);
                  }}
                  getFilteredFindings={getFilteredFindings}
                  mapFindingToCompliance={mapFindingToCompliance}
                />
              )}
            </div>
          </div>
        </div>
      </PageContainer>
    </div>
  );
};

export default ReportDetails;
```

- [ ] **Step 2: Full lint**

Run: `npx eslint src/`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: Task 3 — ReportDetails orchestrator with particles, animated tabs, pill filters, stagger animations"
```

---

## Execution

After plan is saved, will execute inline.
