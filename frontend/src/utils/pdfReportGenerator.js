import { generatePDF } from "./pdfGenerator";

export const COMPLIANCE_STANDARDS = {
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
    description: "National Institute of Standards and Technology Cybersecurity Framework",
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

export const getAllFindings = (report) => {
  let allFindings = [];
  if (report?.findings && Array.isArray(report.findings)) {
    allFindings = report.findings;
  } else if (report?.scan_results) {
    report.scan_results.forEach((scanResult) => {
      if (scanResult.findings && Array.isArray(scanResult.findings)) {
        allFindings = [...allFindings, ...scanResult.findings];
      }
    });
  }
  return allFindings;
};

export const generateViewPDF = async ({ report, aiAnalysis, reportId, setIsGenerating, toast }) => {
  setIsGenerating(true);
  try {
    const allFindings = getAllFindings(report);
    const totalFindings = allFindings.length;

    // Prepare report data
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

    // Calculate page estimates for TOC
    const criticalCount = reportData.critical;
    const highCount = reportData.high;
    const mediumCount = reportData.medium;
    const lowCount = reportData.low;
    const infoCount = reportData.info;

    // Estimate pages: Cover=1, TOC=1, Summary=1, Findings=variable, Compliance=2, Remediation=1, AI=1
    const findingsPages = Math.ceil(totalFindings / 4) || 1; // ~4 findings per page
    const pageEstimates = {
      cover: 1,
      toc: 2,
      summary: 3,
      findings: 4,
      compliance: 4 + findingsPages,
      remediation: 4 + findingsPages + 2,
      ai: 4 + findingsPages + 3,
    };

    // Build comprehensive PDF content
    const pdfContent = document.createElement("div");
    pdfContent.style.fontFamily = "'Inter', 'Segoe UI', Arial, sans-serif";
    pdfContent.style.color = "#1f2937";
    pdfContent.style.backgroundColor = "#ffffff";
    pdfContent.style.padding = "0";
    pdfContent.style.width = "100%";

    // ============ COVER PAGE ============
    const coverPage = `
        <div style="page-break-after: always; background: #1e1b4b; color: white; padding: 50px 40px; min-height: 800px;">
          <!-- Header -->
          <table style="width: 100%; margin-bottom: 60px;">
            <tr>
              <td style="vertical-align: middle;">
                <span style="font-size: 36px;">🛡️</span>
                <span style="font-size: 24px; font-weight: 700; letter-spacing: 2px; margin-left: 12px;">ONYX</span>
              </td>
              <td style="text-align: right; font-size: 12px; color: #a5b4fc;">
                <div>Security Intelligence Platform</div>
                <div style="margin-top: 4px;">Enterprise Edition</div>
              </td>
            </tr>
          </table>
          
          <!-- Main Title Section -->
          <div style="text-align: center; margin-bottom: 50px;">
            <div style="background: rgba(255,255,255,0.15); padding: 10px 24px; border-radius: 8px; font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 30px;">
              🔒 CONFIDENTIAL SECURITY REPORT
            </div>
            
            <h1 style="font-size: 48px; font-weight: 900; margin: 0 0 10px 0; letter-spacing: -1px;">
              Comprehensive
            </h1>
            <h1 style="font-size: 48px; font-weight: 900; margin: 0; color: #a5b4fc; letter-spacing: -1px;">
              Security Analysis
            </h1>
            
            <p style="font-size: 16px; color: #c7d2fe; margin: 24px auto 0 auto; max-width: 450px; line-height: 1.6;">
              Complete vulnerability assessment with AI-powered insights and compliance mapping
            </p>
          </div>
          
          <!-- Project Info Box -->
          <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 16px; padding: 30px; max-width: 550px; margin: 0 auto 50px auto;">
            <h2 style="font-size: 22px; font-weight: 700; margin: 0 0 8px 0; text-align: center;">${
              report?.project_name || "Security Assessment"
            }</h2>
            <p style="font-size: 12px; color: #a5b4fc; margin: 0 0 24px 0; text-align: center; word-break: break-all;">${
              report?.git_metadata?.repository_url || "Repository Analysis"
            }</p>
            
            <table style="width: 100%; border-collapse: separate; border-spacing: 12px 0;">
              <tr>
                <td style="width: 25%; text-align: center; background: rgba(239,68,68,0.25); padding: 16px 8px; border-radius: 10px;">
                  <div style="font-size: 32px; font-weight: 800; color: #fca5a5;">${totalFindings}</div>
                  <div style="font-size: 10px; color: #fecaca; margin-top: 4px;">Total Issues</div>
                </td>
                <td style="width: 25%; text-align: center; background: rgba(239,68,68,0.25); padding: 16px 8px; border-radius: 10px;">
                  <div style="font-size: 32px; font-weight: 800; color: #fca5a5;">${criticalCount}</div>
                  <div style="font-size: 10px; color: #fecaca; margin-top: 4px;">Critical</div>
                </td>
                <td style="width: 25%; text-align: center; background: rgba(251,146,60,0.25); padding: 16px 8px; border-radius: 10px;">
                  <div style="font-size: 32px; font-weight: 800; color: #fdba74;">${highCount}</div>
                  <div style="font-size: 10px; color: #fed7aa; margin-top: 4px;">High</div>
                </td>
                <td style="width: 25%; text-align: center; background: rgba(34,197,94,0.25); padding: 16px 8px; border-radius: 10px;">
                  <div style="font-size: 32px; font-weight: 800; color: #86efac;">${
                    reportData.securityScore
                  }</div>
                  <div style="font-size: 10px; color: #bbf7d0; margin-top: 4px;">Score</div>
                </td>
              </tr>
            </table>
          </div>
          
          <!-- Footer Info -->
          <table style="width: 100%; font-size: 12px; color: #a5b4fc; margin-top: 40px;">
            <tr>
              <td>
                <div>Branch: <strong style="color: white;">${
                  report?.git_metadata?.branch || "main"
                }</strong></div>
                <div style="margin-top: 4px;">Scan ID: ${report?.scan_id || reportId}</div>
              </td>
              <td style="text-align: right;">
                <div>Generated: <strong style="color: white;">${new Date().toLocaleDateString(
                  "en-US",
                  { year: "numeric", month: "long", day: "numeric" }
                )}</strong></div>
                <div style="margin-top: 4px;">${new Date().toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}</div>
              </td>
            </tr>
          </table>
        </div>
      `;

    // ============ TABLE OF CONTENTS ============
    const tocPage = `
        <div style="page-break-after: always; padding: 40px;">
          <h2 style="font-size: 24px; font-weight: 700; color: #1e40af; border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">📑 Table of Contents</h2>
          <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr style="border-bottom: 1px dotted #cbd5e1;">
              <td style="padding: 10px 0; font-weight: 600;">1. Executive Summary</td>
              <td style="padding: 10px 0; text-align: right; color: #64748b; font-weight: 500;">Page ${
                pageEstimates.summary
              }</td>
            </tr>
            <tr style="border-bottom: 1px dotted #cbd5e1;">
              <td style="padding: 10px 0; font-weight: 600;">2. Detailed Vulnerability Analysis</td>
              <td style="padding: 10px 0; text-align: right; color: #64748b; font-weight: 500;">Page ${
                pageEstimates.findings
              }</td>
            </tr>
            <tr>
              <td colspan="2" style="padding: 4px 0 8px 24px; font-size: 13px; color: #64748b;">
                ${
                  criticalCount > 0
                    ? `• Critical Vulnerabilities (${criticalCount} issues)<br/>`
                    : ""
                }
                ${highCount > 0 ? `• High Severity Issues (${highCount} issues)<br/>` : ""}
                ${mediumCount > 0 ? `• Medium Severity Issues (${mediumCount} issues)<br/>` : ""}
                ${lowCount > 0 ? `• Low Severity Issues (${lowCount} issues)<br/>` : ""}
                ${infoCount > 0 ? `• Informational Findings (${infoCount} issues)` : ""}
              </td>
            </tr>
            <tr style="border-bottom: 1px dotted #cbd5e1;">
              <td style="padding: 10px 0; font-weight: 600;">3. Compliance Assessment</td>
              <td style="padding: 10px 0; text-align: right; color: #64748b; font-weight: 500;">Page ${
                pageEstimates.compliance
              }</td>
            </tr>
            <tr>
              <td colspan="2" style="padding: 4px 0 8px 24px; font-size: 13px; color: #64748b;">
                • OWASP Top 10 (2021)<br/>
                • NIST Cybersecurity Framework<br/>
                • ISO/IEC 27001<br/>
                • PCI DSS 4.0
              </td>
            </tr>
            <tr style="border-bottom: 1px dotted #cbd5e1;">
              <td style="padding: 10px 0; font-weight: 600;">4. Remediation Roadmap</td>
              <td style="padding: 10px 0; text-align: right; color: #64748b; font-weight: 500;">Page ${
                pageEstimates.remediation
              }</td>
            </tr>
            ${
              aiAnalysis
                ? `
            <tr style="border-bottom: 1px dotted #cbd5e1;">
              <td style="padding: 10px 0; font-weight: 600;">5. AI-Powered Security Analysis</td>
              <td style="padding: 10px 0; text-align: right; color: #64748b; font-weight: 500;">Page ${pageEstimates.ai}</td>
            </tr>
            `
                : ""
            }
          </table>
          
          <div style="margin-top: 40px; padding: 20px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h4 style="margin: 0 0 12px 0; font-size: 14px; color: #1e293b;">📊 Report Summary</h4>
            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px 0; color: #64748b;">Total Vulnerabilities:</td>
                <td style="padding: 8px 0; font-weight: 600; color: #1e293b;">${totalFindings}</td>
                <td style="padding: 8px 0; color: #64748b;">Security Score:</td>
                <td style="padding: 8px 0; font-weight: 600; color: ${
                  reportData.securityScore >= 70
                    ? "#059669"
                    : reportData.securityScore >= 40
                      ? "#d97706"
                      : "#dc2626"
                };">${reportData.securityScore}/100</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #64748b;">Critical/High Issues:</td>
                <td style="padding: 8px 0; font-weight: 600; color: #dc2626;">${
                  criticalCount + highCount
                }</td>
                <td style="padding: 8px 0; color: #64748b;">Scanners Used:</td>
                <td style="padding: 8px 0; font-weight: 600; color: #1e293b;">${
                  report?.scan_results?.length || 1
                }</td>
              </tr>
            </table>
          </div>
        </div>
      `;

    // ============ EXECUTIVE SUMMARY ============
    const riskLevel =
      reportData.riskScore <= 25
        ? "Low"
        : reportData.riskScore <= 50
          ? "Medium"
          : reportData.riskScore <= 75
            ? "High"
            : "Critical";
    const riskColor =
      reportData.riskScore <= 25
        ? "#059669"
        : reportData.riskScore <= 50
          ? "#d97706"
          : reportData.riskScore <= 75
            ? "#ea580c"
            : "#dc2626";
    const securityGrade =
      reportData.securityScore >= 90
        ? "A+"
        : reportData.securityScore >= 80
          ? "A"
          : reportData.securityScore >= 70
            ? "B"
            : reportData.securityScore >= 60
              ? "C"
              : reportData.securityScore >= 50
                ? "D"
                : "F";
    const gradeColor =
      reportData.securityScore >= 70
        ? "#10b981"
        : reportData.securityScore >= 50
          ? "#f59e0b"
          : "#ef4444";

    const executiveSummary = `
        <div style="page-break-after: always; padding: 40px;">
          <h2 style="font-size: 26px; font-weight: 800; color: #1e40af; border-bottom: 4px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">
            📊 Executive Summary
          </h2>
          
          <!-- Key Metrics - Using Table for PDF compatibility -->
          <table style="width: 100%; margin-bottom: 24px;">
            <tr>
              <!-- Security Score Card -->
              <td style="width: 48%; vertical-align: top; background: #ecfdf5; border: 2px solid #10b981; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 12px; color: #047857; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 12px;">🛡️ Security Score</div>
                <div style="font-size: 48px; font-weight: 900; color: ${gradeColor}; margin-bottom: 8px;">${
                  reportData.securityScore
                }</div>
                <div style="font-size: 32px; font-weight: 800; color: ${gradeColor};">Grade: ${securityGrade}</div>
              </td>
              <td style="width: 4%;"></td>
              <!-- Risk Level Card -->
              <td style="width: 48%; vertical-align: top; background: #fef2f2; border: 2px solid ${riskColor}; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 12px; color: ${riskColor}; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 12px;">⚠️ Risk Assessment</div>
                <div style="font-size: 40px; font-weight: 900; color: ${riskColor}; margin-bottom: 8px;">${riskLevel}</div>
                <div style="font-size: 13px; color: ${riskColor};">Risk Score: <strong>${Math.round(
                  reportData.riskScore
                )}/100</strong></div>
              </td>
            </tr>
          </table>

          <!-- Assessment Overview -->
          <div style="background: #f0f9ff; border: 2px solid #0284c7; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <h3 style="font-size: 15px; color: #0369a1; margin: 0 0 12px 0;">📋 Assessment Overview</h3>
            <p style="font-size: 13px; color: #1e293b; line-height: 1.8; margin: 0;">
              This comprehensive security assessment of <strong>${
                report?.project_name || "the target repository"
              }</strong> has identified 
              <strong style="color: ${
                totalFindings > 0 ? "#dc2626" : "#059669"
              };">${totalFindings} security vulnerabilities</strong> across the codebase, 
              including <strong style="color: #dc2626;">${criticalCount} critical</strong> and <strong style="color: #ea580c;">${highCount} high-severity</strong> issues 
              that require immediate attention. The overall security posture is rated as <strong style="color: ${riskColor};">${riskLevel} Risk</strong> 
              with a security score of <strong style="color: ${gradeColor};">${
                reportData.securityScore
              }/100 (Grade: ${securityGrade})</strong>.
              ${
                criticalCount > 0
                  ? ' <span style="color: #dc2626; font-weight: 600;">⚠️ Immediate action required.</span>'
                  : ""
              }
            </p>
          </div>

          <h3 style="font-size: 16px; font-weight: 700; color: #1e293b; margin: 24px 0 16px 0;">📈 Vulnerability Distribution</h3>
          
          <!-- Severity Cards - Using Table -->
          <table style="width: 100%; margin-bottom: 24px;">
            <tr>
              <td style="width: 20%; text-align: center; padding: 16px 8px; background: #fef2f2; border-radius: 10px; border: 2px solid #dc2626;">
                <div style="font-size: 10px; color: #dc2626; margin-bottom: 4px;">🔴</div>
                <div style="font-size: 36px; font-weight: 900; color: #dc2626; line-height: 1;">${
                  reportData.critical
                }</div>
                <div style="font-size: 10px; color: #991b1b; font-weight: 700; text-transform: uppercase; margin-top: 6px;">Critical</div>
                <div style="font-size: 9px; color: #b91c1c; margin-top: 2px;">Fix Now</div>
              </td>
              <td style="width: 20%; text-align: center; padding: 16px 8px; background: #fff7ed; border-radius: 10px; border: 2px solid #ea580c;">
                <div style="font-size: 10px; color: #ea580c; margin-bottom: 4px;">🟠</div>
                <div style="font-size: 36px; font-weight: 900; color: #ea580c; line-height: 1;">${
                  reportData.high
                }</div>
                <div style="font-size: 10px; color: #9a3412; font-weight: 700; text-transform: uppercase; margin-top: 6px;">High</div>
                <div style="font-size: 9px; color: #c2410c; margin-top: 2px;">This Sprint</div>
              </td>
              <td style="width: 20%; text-align: center; padding: 16px 8px; background: #fffbeb; border-radius: 10px; border: 2px solid #d97706;">
                <div style="font-size: 10px; color: #d97706; margin-bottom: 4px;">🟡</div>
                <div style="font-size: 36px; font-weight: 900; color: #d97706; line-height: 1;">${
                  reportData.medium
                }</div>
                <div style="font-size: 10px; color: #92400e; font-weight: 700; text-transform: uppercase; margin-top: 6px;">Medium</div>
                <div style="font-size: 9px; color: #a16207; margin-top: 2px;">Plan Fix</div>
              </td>
              <td style="width: 20%; text-align: center; padding: 16px 8px; background: #eff6ff; border-radius: 10px; border: 2px solid #2563eb;">
                <div style="font-size: 10px; color: #2563eb; margin-bottom: 4px;">🔵</div>
                <div style="font-size: 36px; font-weight: 900; color: #2563eb; line-height: 1;">${
                  reportData.low
                }</div>
                <div style="font-size: 10px; color: #1e40af; font-weight: 700; text-transform: uppercase; margin-top: 6px;">Low</div>
                <div style="font-size: 9px; color: #1d4ed8; margin-top: 2px;">Monitor</div>
              </td>
              <td style="width: 20%; text-align: center; padding: 16px 8px; background: #f9fafb; border-radius: 10px; border: 2px solid #6b7280;">
                <div style="font-size: 10px; color: #6b7280; margin-bottom: 4px;">⚪</div>
                <div style="font-size: 36px; font-weight: 900; color: #6b7280; line-height: 1;">${
                  reportData.info
                }</div>
                <div style="font-size: 10px; color: #374151; font-weight: 700; text-transform: uppercase; margin-top: 6px;">Info</div>
                <div style="font-size: 9px; color: #4b5563; margin-top: 2px;">Review</div>
              </td>
            </tr>
          </table>

          <h3 style="font-size: 16px; font-weight: 700; color: #1e293b; margin: 24px 0 12px 0;">📋 Scan Details</h3>
          <table style="width: 100%; border-collapse: collapse; font-size: 12px; border: 2px solid #e2e8f0; border-radius: 8px;">
            <tr style="background: #1e40af; color: white;">
              <td style="padding: 12px 14px; font-weight: 600;" colspan="4">Repository & Scan Information</td>
            </tr>
            <tr style="background: #f8fafc;">
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #64748b; width: 18%;">Project</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #1e293b; width: 32%;">${
                report?.project_name || "N/A"
              }</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #64748b; width: 18%;">Score</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: ${gradeColor}; font-weight: 700; width: 32%;">${
                reportData.securityScore
              }/100 (${securityGrade})</td>
            </tr>
            <tr>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #64748b;">Risk</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: ${riskColor}; font-weight: 700;">${riskLevel}</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #64748b;">Duration</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #1e293b;">${
                report?.duration_seconds ? Math.round(report.duration_seconds) + "s" : "N/A"
              }</td>
            </tr>
            <tr style="background: #f8fafc;">
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #64748b;">Repository</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #1e293b; word-break: break-all; font-size: 11px;" colspan="3">${
                report?.git_metadata?.repository_url || "N/A"
              }</td>
            </tr>
            <tr>
              <td style="padding: 10px 14px; font-weight: 600; color: #64748b;">Branch</td>
              <td style="padding: 10px 14px; color: #1e293b;">${
                report?.git_metadata?.branch || "main"
              }</td>
              <td style="padding: 10px 14px; font-weight: 600; color: #64748b;">Scan Date</td>
              <td style="padding: 10px 14px; color: #1e293b;">${
                report?.created_at
                  ? new Date(report.created_at).toLocaleString()
                  : new Date().toLocaleString()
              }</td>
            </tr>
          </table>
          
          <!-- Action Items -->
          ${
            criticalCount > 0 || highCount > 0
              ? `
          <div style="margin-top: 20px; background: #fef2f2; border: 2px solid #dc2626; border-radius: 10px; padding: 16px;">
            <h4 style="color: #dc2626; margin: 0 0 10px 0; font-size: 13px;">🚨 Immediate Actions Required</h4>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; line-height: 1.7; color: #1e293b;">
              ${
                criticalCount > 0
                  ? `<li><strong style="color: #dc2626;">${criticalCount} Critical vulnerabilities</strong> - fix within 24 hours</li>`
                  : ""
              }
              ${
                highCount > 0
                  ? `<li><strong style="color: #ea580c;">${highCount} High-severity issues</strong> - address this sprint</li>`
                  : ""
              }
              <li>Review detailed findings for specific remediation steps</li>
            </ul>
          </div>
          `
              : `
          <div style="margin-top: 20px; background: #ecfdf5; border: 2px solid #10b981; border-radius: 10px; padding: 16px;">
            <h4 style="color: #047857; margin: 0 0 6px 0; font-size: 13px;">✅ Security Status</h4>
            <p style="margin: 0; font-size: 12px; color: #1e293b;">No critical or high-severity vulnerabilities detected. Continue monitoring and maintaining security best practices.</p>
          </div>
          `
          }
        </div>
      `;

    // ============ DETAILED FINDINGS ============
    const severityOrder = ["critical", "high", "medium", "low", "info"];
    const findingsBySeverity = {};
    severityOrder.forEach((sev) => {
      findingsBySeverity[sev] = [];
    });
    allFindings.forEach((f) => {
      const sev = (f.severity || "info").toLowerCase();
      if (findingsBySeverity[sev]) {
        findingsBySeverity[sev].push(f);
      } else {
        findingsBySeverity["info"].push(f);
      }
    });

    const severityColors = {
      critical: {
        bg: "#fef2f2",
        border: "#dc2626",
        text: "#dc2626",
        headerBg: "#dc2626",
      },
      high: {
        bg: "#fff7ed",
        border: "#ea580c",
        text: "#ea580c",
        headerBg: "#ea580c",
      },
      medium: {
        bg: "#fffbeb",
        border: "#d97706",
        text: "#d97706",
        headerBg: "#d97706",
      },
      low: {
        bg: "#eff6ff",
        border: "#2563eb",
        text: "#2563eb",
        headerBg: "#2563eb",
      },
      info: {
        bg: "#f3f4f6",
        border: "#6b7280",
        text: "#6b7280",
        headerBg: "#6b7280",
      },
    };

    let findingsHtml = `<div style="padding: 40px; page-break-before: always;">
        <h2 style="font-size: 24px; font-weight: 700; color: #1e40af; border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">🔍 Detailed Vulnerability Analysis</h2>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 20px;">Complete list of security vulnerabilities identified during the scan, organized by severity level with file locations, line numbers, and recommended fixes.</p>`;

    // Generate default remediation based on finding type
    const getDefaultRemediation = (finding) => {
      const title = (finding.title || finding.message || "").toLowerCase();
      const desc = (finding.description || "").toLowerCase();

      if (title.includes("sql") || desc.includes("sql injection")) {
        return "Use parameterized queries or prepared statements instead of string concatenation. Implement input validation and use ORM frameworks.";
      } else if (title.includes("xss") || desc.includes("cross-site scripting")) {
        return "Encode all user-supplied data before rendering. Use Content Security Policy (CSP) headers and sanitize HTML input.";
      } else if (
        title.includes("hardcoded") ||
        desc.includes("secret") ||
        desc.includes("password")
      ) {
        return "Remove hardcoded credentials. Use environment variables or secure secret management solutions like HashiCorp Vault.";
      } else if (title.includes("auth") || desc.includes("authentication")) {
        return "Implement proper authentication mechanisms. Use secure session management and multi-factor authentication where possible.";
      } else if (title.includes("crypto") || desc.includes("encryption")) {
        return "Use strong, modern encryption algorithms (AES-256, RSA-2048+). Avoid deprecated algorithms like MD5, SHA1, or DES.";
      } else if (title.includes("injection") || desc.includes("command injection")) {
        return "Validate and sanitize all user inputs. Avoid executing shell commands with user-supplied data. Use safe APIs.";
      } else if (title.includes("path") || desc.includes("traversal")) {
        return "Validate file paths and use allowlists for permitted directories. Never use user input directly in file operations.";
      } else if (title.includes("ssrf") || desc.includes("server-side request")) {
        return "Validate and sanitize URLs. Use allowlists for permitted domains. Disable unnecessary URL schemes.";
      } else if (title.includes("insecure") || desc.includes("http://")) {
        return "Use HTTPS instead of HTTP. Implement HSTS headers and ensure all connections are encrypted.";
      } else if (title.includes("log") || desc.includes("sensitive data")) {
        return "Avoid logging sensitive information. Implement data masking and secure log storage practices.";
      }
      return "Review the code and apply security best practices. Consult OWASP guidelines for specific remediation steps.";
    };

    severityOrder.forEach((severity) => {
      const findings = findingsBySeverity[severity];
      if (findings.length > 0) {
        const colors = severityColors[severity];
        findingsHtml += `
            <div style="margin-bottom: 32px;">
              <table style="width: 100%; background: ${
                colors.headerBg
              }; color: white; border-radius: 8px 8px 0 0;">
                <tr>
                  <td style="padding: 14px 18px;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600; text-transform: uppercase;">${severity.toUpperCase()} SEVERITY</h3>
                  </td>
                  <td style="padding: 14px 18px; text-align: right;">
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 12px; font-size: 12px;">${
                      findings.length
                    } ${findings.length === 1 ? "issue" : "issues"}</span>
                  </td>
                </tr>
              </table>
              <div style="border: 2px solid ${
                colors.border
              }; border-top: none; border-radius: 0 0 8px 8px; padding: 16px;">
          `;

        // Show ALL findings with complete details
        findings.forEach((finding, idx) => {
          const title = finding.title || finding.message || finding.rule_id || `Finding ${idx + 1}`;
          const filePath =
            finding.file_path || finding.path || finding.location?.path || "Unknown file";
          const lineNum = finding.line_number || finding.line || finding.location?.line || "";
          const endLine = finding.end_line || finding.location?.end_line || "";
          const colNum = finding.column || finding.col || finding.location?.column || "";
          const description = finding.description || finding.message || "";
          const recommendation =
            finding.recommendation ||
            finding.fix ||
            finding.remediation ||
            getDefaultRemediation(finding);
          const ruleId = finding.rule_id || finding.check_id || finding.id || "";
          const scanner = finding.scanner || finding.tool || finding.source || "";
          const cwe = finding.cwe || finding.cwe_id || "";
          const owasp = finding.owasp || finding.owasp_category || "";
          const codeSnippet =
            finding.code_snippet ||
            finding.snippet ||
            finding.vulnerable_code ||
            finding.extra?.lines ||
            "";
          const confidence = finding.confidence || finding.certainty || "";
          const category = finding.category || finding.vulnerability_class || "";

          findingsHtml += `
              <div style="margin-bottom: 20px; padding: 18px; background: ${
                colors.bg
              }; border-radius: 10px; border-left: 5px solid ${colors.border};">
                <table style="width: 100%; margin-bottom: 12px;">
                  <tr>
                    <td style="vertical-align: top;">
                      <h4 style="margin: 0; font-size: 15px; font-weight: 700; color: #0f172a;">${
                        idx + 1
                      }. ${title}</h4>
                    </td>
                    <td style="text-align: right; vertical-align: top; white-space: nowrap;">
                      ${
                        ruleId
                          ? `<span style="font-size: 10px; background: ${colors.border}; color: white; padding: 3px 10px; border-radius: 4px; font-weight: 600; margin-left: 4px;">${ruleId}</span>`
                          : ""
                      }
                      ${
                        cwe
                          ? `<span style="font-size: 10px; background: #7c3aed; color: white; padding: 3px 10px; border-radius: 4px; margin-left: 4px;">CWE-${cwe}</span>`
                          : ""
                      }
                      ${
                        owasp
                          ? `<span style="font-size: 10px; background: #0891b2; color: white; padding: 3px 10px; border-radius: 4px; margin-left: 4px;">${owasp}</span>`
                          : ""
                      }
                    </td>
                  </tr>
                </table>
                <div style="background: #1e293b; color: #e2e8f0; padding: 12px 16px; border-radius: 6px; margin-bottom: 14px; font-family: Consolas, Monaco, monospace;">
                  <div style="font-size: 12px;">
                    <span style="color: #60a5fa;">📁</span>
                    <span style="color: #94a3b8;"> File:</span>
                    <span style="color: #fbbf24; font-weight: 600;"> ${filePath}</span>
                    ${
                      lineNum
                        ? `
                      <span style="margin-left: 16px; color: #60a5fa;">📍</span>
                      <span style="color: #94a3b8;"> Line:</span>
                      <span style="color: #4ade80; font-weight: 600;"> ${lineNum}${
                        endLine && endLine !== lineNum ? ` - ${endLine}` : ""
                      }${colNum ? `, Col: ${colNum}` : ""}</span>
                    `
                        : ""
                    }
                    ${
                      scanner
                        ? `
                      <span style="margin-left: 16px; color: #60a5fa;">🔧</span>
                      <span style="color: #94a3b8;"> Scanner:</span>
                      <span style="color: #a78bfa;"> ${scanner}</span>
                    `
                        : ""
                    }
                  </div>
                </div>
                ${
                  category || confidence
                    ? `
                  <div style="margin-bottom: 12px; font-size: 12px;">
                    ${
                      category
                        ? `<span><strong style="color: #64748b;">Category:</strong> <span style="color: #1e293b;">${category}</span></span>`
                        : ""
                    }
                    ${
                      confidence
                        ? `<span style="margin-left: 16px;"><strong style="color: #64748b;">Confidence:</strong> <span style="color: #1e293b;">${confidence}</span></span>`
                        : ""
                    }
                  </div>
                `
                    : ""
                }
                ${
                  description
                    ? `
                  <div style="margin-bottom: 14px;">
                    <div style="font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 6px;">
                      📋 VULNERABILITY DESCRIPTION
                    </div>
                    <div style="font-size: 13px; color: #334155; line-height: 1.7; background: white; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                      ${description}
                    </div>
                  </div>
                `
                    : ""
                }
                ${
                  codeSnippet
                    ? `
                  <div style="margin-bottom: 14px;">
                    <div style="font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 6px;">
                      💻 VULNERABLE CODE
                    </div>
                    <pre style="background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 6px; font-size: 11px; overflow-x: auto; margin: 0; font-family: Consolas, Monaco, monospace; line-height: 1.5;">${
                      typeof codeSnippet === "string"
                        ? codeSnippet
                        : JSON.stringify(codeSnippet, null, 2)
                    }</pre>
                  </div>
                `
                    : ""
                }
                <div style="background: #d1fae5; padding: 14px; border-radius: 8px; border: 1px solid #10b981;">
                  <div style="font-size: 12px; font-weight: 700; color: #065f46; margin-bottom: 8px;">
                    💡 HOW TO FIX
                  </div>
                  <div style="font-size: 13px; color: #064e3b; line-height: 1.7;">
                    ${recommendation}
                  </div>
                </div>
              </div>
            `;
        });
        findingsHtml += `</div></div>`;
      }
    });

    if (totalFindings === 0) {
      findingsHtml += `
          <div style="text-align: center; padding: 40px; background: #ecfdf5; border-radius: 12px; border: 2px solid #059669;">
            <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
            <h3 style="color: #059669; margin: 0 0 8px 0;">No Vulnerabilities Found</h3>
            <p style="color: #047857; margin: 0;">The security scan did not detect any vulnerabilities in the codebase.</p>
          </div>
        `;
    }
    findingsHtml += `</div>`;

    // ============ COMPLIANCE SECTION ============
    let complianceHtml = `<div style="padding: 40px; page-break-before: always;">
        <h2 style="font-size: 24px; font-weight: 700; color: #1e40af; border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">📋 Compliance Assessment</h2>
        <p style="font-size: 14px; color: #64748b; margin-bottom: 24px;">Assessment of security findings against major compliance frameworks and security standards.</p>`;

    Object.entries(COMPLIANCE_STANDARDS).forEach(([key, standard]) => {
      const categories = Object.entries(standard.categories);
      const affectedCategories = categories.filter(([code, name]) => {
        return allFindings.some((f) => {
          const desc = ((f.description || "") + (f.title || "") + (f.message || "")).toLowerCase();
          return (
            desc.includes(code.toLowerCase()) || desc.includes(name.toLowerCase().split(" ")[0])
          );
        });
      });
      const complianceScore =
        categories.length > 0
          ? Math.round(((categories.length - affectedCategories.length) / categories.length) * 100)
          : 100;
      const scoreColor =
        complianceScore >= 80 ? "#059669" : complianceScore >= 50 ? "#d97706" : "#dc2626";

      complianceHtml += `
          <div style="margin-bottom: 24px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
            <table style="width: 100%; background: #1e40af; color: white;">
              <tr>
                <td style="padding: 16px;">
                  <span style="font-size: 24px; margin-right: 12px;">${standard.icon}</span>
                  <span style="font-size: 18px; font-weight: 600;">${standard.name}</span>
                  <span style="font-size: 12px; color: #c7d2fe; margin-left: 8px;">v${
                    standard.version
                  }</span>
                </td>
                <td style="padding: 16px; text-align: right;">
                  <div style="font-size: 28px; font-weight: 800;">${complianceScore}%</div>
                  <div style="font-size: 11px; color: #c7d2fe;">Compliance Score</div>
                </td>
              </tr>
            </table>
            <div style="padding: 16px; background: #f8fafc;">
              <p style="font-size: 12px; color: #64748b; margin: 0 0 12px 0;">${
                standard.description
              }</p>
              <table style="width: 100%; font-size: 11px;">
                ${categories
                  .map(([code, name], idx) => {
                    const isAffected = affectedCategories.some(([c]) => c === code);
                    return `${idx % 3 === 0 ? "<tr>" : ""}<td style="padding: 6px; background: ${
                      isAffected ? "#fef2f2" : "#ecfdf5"
                    }; border-radius: 4px; border-left: 3px solid ${
                      isAffected ? "#dc2626" : "#059669"
                    }; width: 33%;"><strong>${code}:</strong> ${name} <span style="float: right;">${
                      isAffected ? "⚠️" : "✅"
                    }</span></td>${idx % 3 === 2 || idx === categories.length - 1 ? "</tr>" : ""}`;
                  })
                  .join("")}
              </table>
            </div>
          </div>
        `;
    });
    complianceHtml += `</div>`;

    // ============ REMEDIATION RECOMMENDATIONS ============
    let remediationHtml = `<div style="padding: 40px; page-break-before: always;">
        <h2 style="font-size: 24px; font-weight: 700; color: #1e40af; border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">💡 Remediation Recommendations</h2>`;

    const priorityActions = [
      {
        priority: "Immediate",
        color: "#dc2626",
        items: findingsBySeverity.critical
          .slice(0, 5)
          .map((f) => f.title || f.message || "Critical vulnerability"),
      },
      {
        priority: "High Priority",
        color: "#ea580c",
        items: findingsBySeverity.high
          .slice(0, 5)
          .map((f) => f.title || f.message || "High severity issue"),
      },
      {
        priority: "Medium Priority",
        color: "#d97706",
        items: findingsBySeverity.medium
          .slice(0, 5)
          .map((f) => f.title || f.message || "Medium severity issue"),
      },
    ];

    priorityActions.forEach(({ priority, color, items }) => {
      if (items.length > 0) {
        remediationHtml += `
            <div style="margin-bottom: 24px;">
              <h3 style="font-size: 16px; font-weight: 600; color: ${color}; margin-bottom: 12px;">${priority} Actions</h3>
              <ul style="margin: 0; padding-left: 24px; font-size: 13px; line-height: 2;">
                ${items.map((item) => `<li style="color: #1e293b;">${item}</li>`).join("")}
              </ul>
            </div>
          `;
      }
    });

    remediationHtml += `
        <div style="background: #f0f9ff; border: 1px solid #0284c7; border-radius: 8px; padding: 20px; margin-top: 24px;">
          <h4 style="color: #0369a1; margin: 0 0 12px 0;">📚 General Security Best Practices</h4>
          <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8; color: #1e293b;">
            <li>Implement secure coding guidelines and conduct regular code reviews</li>
            <li>Keep all dependencies and frameworks updated to latest secure versions</li>
            <li>Enable security scanning in CI/CD pipelines for continuous monitoring</li>
            <li>Conduct regular penetration testing and security assessments</li>
            <li>Implement proper input validation and output encoding</li>
            <li>Use parameterized queries to prevent SQL injection attacks</li>
            <li>Implement proper authentication and session management</li>
            <li>Enable comprehensive logging and monitoring for security events</li>
          </ul>
        </div>
      </div>`;

    // ============ AI ANALYSIS (if available) ============
    let aiHtml = "";
    if (aiAnalysis && aiAnalysis.has_analysis !== false) {
      // Parse AI analysis data properly - map to backend response fields
      const aiSummary =
        aiAnalysis.executive_summary || aiAnalysis.summary || aiAnalysis.analysis_summary || "";
      const aiRecs =
        aiAnalysis.priority_recommendations ||
        aiAnalysis.recommendations ||
        aiAnalysis.suggested_fixes ||
        [];
      const aiRiskAssessment =
        aiAnalysis.overall_risk_assessment ||
        aiAnalysis.risk_assessment ||
        aiAnalysis.threat_analysis ||
        "";
      const aiScore =
        aiAnalysis.security_score || aiAnalysis.risk_score || reportData.securityScore;
      const aiRiskLevel =
        aiAnalysis.risk_level ||
        aiAnalysis.severity ||
        (aiScore >= 70 ? "Low" : aiScore >= 40 ? "Medium" : "High");
      const aiThreatVectors = aiAnalysis.attack_vectors || aiAnalysis.threat_vectors || [];
      const aiPriorityFindings = aiAnalysis.priority_findings || aiAnalysis.priority_fixes || [];
      const aiComplianceImpact = aiAnalysis.compliance_impact || {};
      const aiSecureCodeExamples = aiAnalysis.secure_code_examples || {};
      const aiRemediationRoadmap = aiAnalysis.remediation_roadmap || [];
      const aiThreatCategories = aiAnalysis.threat_categories || {};
      const aiEstimatedFixTime = aiAnalysis.estimated_fix_time || "";
      const aiModelUsed = aiAnalysis.model_used || "AI Analysis Engine";
      const aiGeneratedAt = aiAnalysis.generated_at || "";

      // Create visual risk meter
      const riskMeterColor = aiScore >= 70 ? "#10b981" : aiScore >= 40 ? "#f59e0b" : "#ef4444";
      const riskMeterWidth = Math.min(100, Math.max(0, aiScore));

      aiHtml = `<div style="padding: 40px; page-break-before: always;">
          <h2 style="font-size: 24px; font-weight: 800; color: #1e40af; border-bottom: 4px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">
            🤖 AI-Powered Security Analysis
          </h2>
          
          <!-- AI Analysis Header -->
          <div style="background: #1e1b4b; border-radius: 12px; padding: 24px; margin-bottom: 24px; color: white;">
            <table style="width: 100%;">
              <tr>
                <td style="vertical-align: top; padding-right: 20px;">
                  <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 700;">🧠 Automated Security Intelligence</h3>
                  <p style="margin: 0 0 8px 0; font-size: 12px; color: #c7d2fe;">Powered by ${aiModelUsed}</p>
                  ${
                    aiGeneratedAt
                      ? `<p style="margin: 0; font-size: 10px; color: #a5b4fc;">Generated: ${new Date(
                          aiGeneratedAt
                        ).toLocaleString()}</p>`
                      : ""
                  }
                </td>
                <td style="width: 120px; text-align: center; background: rgba(255,255,255,0.1); padding: 16px; border-radius: 10px;">
                  <div style="font-size: 32px; font-weight: 800; color: #fbbf24;">${aiScore}</div>
                  <div style="font-size: 10px; color: #c7d2fe; margin-top: 4px;">Security Score</div>
                </td>
                <td style="width: 120px; text-align: center; background: rgba(255,255,255,0.1); padding: 16px; border-radius: 10px;">
                  <div style="font-size: 18px; font-weight: 700; color: ${
                    aiRiskLevel === "Low"
                      ? "#4ade80"
                      : aiRiskLevel === "Medium"
                        ? "#fbbf24"
                        : "#f87171"
                  };">${aiRiskLevel}</div>
                  <div style="font-size: 10px; color: #c7d2fe; margin-top: 4px;">Risk Level</div>
                </td>
                ${
                  aiEstimatedFixTime
                    ? `
                <td style="width: 120px; text-align: center; background: rgba(255,255,255,0.1); padding: 16px; border-radius: 10px;">
                  <div style="font-size: 14px; font-weight: 700;">⏱️ ${aiEstimatedFixTime}</div>
                  <div style="font-size: 10px; color: #c7d2fe; margin-top: 4px;">Est. Fix Time</div>
                </td>
                `
                    : ""
                }
              </tr>
            </table>
            
            <!-- Security Health Bar -->
            <div style="margin-top: 20px; background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px;">
              <table style="width: 100%; margin-bottom: 6px;">
                <tr>
                  <td style="font-size: 11px; font-weight: 600;">Security Health</td>
                  <td style="text-align: right; font-size: 11px;">${riskMeterWidth}%</td>
                </tr>
              </table>
              <div style="background: rgba(255,255,255,0.2); border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #10b981; height: 100%; width: ${riskMeterWidth}%; border-radius: 6px;"></div>
              </div>
              <table style="width: 100%; margin-top: 4px;">
                <tr>
                  <td style="font-size: 9px; color: #a5b4fc;">Critical</td>
                  <td style="text-align: center; font-size: 9px; color: #a5b4fc;">Moderate</td>
                  <td style="text-align: right; font-size: 9px; color: #a5b4fc;">Secure</td>
                </tr>
              </table>
            </div>
          </div>

          ${
            aiSummary
              ? `
          <!-- AI Summary -->
          <div style="background: #eff6ff; border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #1e40af; margin: 0 0 12px 0; font-size: 15px; font-weight: 700;">📊 Executive Summary</h3>
            <p style="font-size: 13px; color: #1e293b; line-height: 1.8; margin: 0;">${aiSummary}</p>
          </div>
          `
              : ""
          }

          ${
            aiRiskAssessment
              ? `
          <!-- Risk Assessment -->
          <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #dc2626; margin: 0 0 12px 0; font-size: 15px; font-weight: 700;">⚠️ Risk Assessment</h3>
            <p style="font-size: 13px; color: #1e293b; line-height: 1.8; margin: 0;">${aiRiskAssessment}</p>
          </div>
          `
              : ""
          }

          ${
            Array.isArray(aiPriorityFindings) && aiPriorityFindings.length > 0
              ? `
          <!-- Priority Findings -->
          <div style="background: #fefce8; border: 2px solid #eab308; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #a16207; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">🎯 Priority Findings</h3>
            ${aiPriorityFindings
              .slice(0, 5)
              .map(
                (finding, idx) => `
              <div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid #eab308; margin-bottom: 10px;">
                <table style="width: 100%;">
                  <tr>
                    <td style="width: 35px; vertical-align: top;">
                      <div style="background: #fef3c7; color: #a16207; padding: 6px 10px; border-radius: 6px; font-weight: 700; font-size: 13px; text-align: center;">${
                        idx + 1
                      }</div>
                    </td>
                    <td style="vertical-align: top; padding-left: 10px;">
                      <div style="font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">${
                        typeof finding === "object"
                          ? finding.title || finding.name || finding.finding
                          : finding
                      }</div>
                      ${
                        typeof finding === "object" && finding.description
                          ? `<div style="font-size: 11px; color: #64748b; line-height: 1.5;">${finding.description}</div>`
                          : ""
                      }
                      ${
                        typeof finding === "object" && finding.severity
                          ? `<span style="font-size: 9px; background: ${
                              finding.severity === "critical"
                                ? "#dc2626"
                                : finding.severity === "high"
                                  ? "#ea580c"
                                  : "#d97706"
                            }; color: white; padding: 2px 6px; border-radius: 3px; margin-top: 4px; display: inline-block;">${finding.severity.toUpperCase()}</span>`
                          : ""
                      }
                    </td>
                  </tr>
                </table>
              </div>
            `
              )
              .join("")}
          </div>
          `
              : ""
          }

          ${
            Array.isArray(aiThreatVectors) && aiThreatVectors.length > 0
              ? `
          <!-- Attack Vectors -->
          <div style="background: #fff7ed; border: 2px solid #f97316; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #c2410c; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">🎯 Identified Attack Vectors</h3>
            <table style="width: 100%; border-collapse: separate; border-spacing: 8px;">
              <tr>
                ${aiThreatVectors
                  .slice(0, 6)
                  .map(
                    (vector, idx) => `
                  ${idx > 0 && idx % 2 === 0 ? "</tr><tr>" : ""}
                  <td style="width: 50%; background: white; padding: 12px; border-radius: 8px; border: 1px solid #fed7aa; vertical-align: top;">
                    <span style="color: #c2410c; margin-right: 8px;">🔴</span>
                    <span style="font-size: 12px; color: #1e293b; font-weight: 500;">${
                      typeof vector === "object"
                        ? vector.name || vector.vector || JSON.stringify(vector)
                        : vector
                    }</span>
                  </td>
                `
                  )
                  .join("")}
              </tr>
            </table>
          </div>
          `
              : ""
          }

          ${
            Object.keys(aiThreatCategories).length > 0
              ? `
          <!-- Threat Categories -->
          <div style="background: #fdf4ff; border: 2px solid #d946ef; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #a21caf; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">📂 Threat Categories</h3>
            <table style="width: 100%; border-collapse: separate; border-spacing: 8px;">
              <tr>
                ${Object.entries(aiThreatCategories)
                  .slice(0, 6)
                  .map(
                    ([category, count], idx) => `
                  ${idx > 0 && idx % 3 === 0 ? "</tr><tr>" : ""}
                  <td style="width: 33%; background: white; padding: 14px; border-radius: 8px; text-align: center; border: 1px solid #f5d0fe;">
                    <div style="font-size: 22px; font-weight: 800; color: #a21caf;">${count}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">${category}</div>
                  </td>
                `
                  )
                  .join("")}
              </tr>
            </table>
          </div>
          `
              : ""
          }
        </div>

        <!-- AI Recommendations Page -->
        ${
          (Array.isArray(aiRecs) && aiRecs.length > 0) ||
          Object.keys(aiSecureCodeExamples).length > 0 ||
          aiRemediationRoadmap.length > 0 ||
          Object.keys(aiComplianceImpact).length > 0
            ? `
        <div style="padding: 40px; page-break-before: always;">
          <h2 style="font-size: 22px; font-weight: 700; color: #1e40af; border-bottom: 3px solid #1e40af; padding-bottom: 10px; margin-bottom: 20px;">🤖 AI Recommendations & Remediation</h2>

          ${
            Array.isArray(aiRecs) && aiRecs.length > 0
              ? `
          <!-- AI Recommendations -->
          <div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #047857; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">💡 AI Security Recommendations</h3>
            ${aiRecs
              .slice(0, 8)
              .map(
                (rec, idx) => `
              <div style="background: white; padding: 12px 14px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 10px;">
                <table style="width: 100%;">
                  <tr>
                    <td style="width: 30px; vertical-align: top;">
                      <div style="background: #10b981; color: white; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; font-weight: 700; font-size: 12px;">${
                        idx + 1
                      }</div>
                    </td>
                    <td style="vertical-align: top; padding-left: 10px;">
                      <span style="font-size: 12px; color: #1e293b; line-height: 1.6;">${
                        typeof rec === "object"
                          ? rec.recommendation || rec.text || rec.description || JSON.stringify(rec)
                          : rec
                      }</span>
                    </td>
                  </tr>
                </table>
              </div>
            `
              )
              .join("")}
          </div>
          `
              : ""
          }

          ${
            aiRemediationRoadmap.length > 0
              ? `
          <!-- Remediation Roadmap -->
          <div style="background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #0369a1; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">🗺️ Remediation Roadmap</h3>
            ${aiRemediationRoadmap
              .slice(0, 6)
              .map(
                (step, idx) => `
              <table style="width: 100%; margin-bottom: 12px;">
                <tr>
                  <td style="width: 36px; vertical-align: top;">
                    <div style="background: ${idx === 0 ? "#0ea5e9" : "#bae6fd"}; color: ${
                      idx === 0 ? "white" : "#0369a1"
                    }; width: 28px; height: 28px; border-radius: 50%; text-align: center; line-height: 28px; font-weight: 700; font-size: 12px;">${
                      idx + 1
                    }</div>
                  </td>
                  <td style="vertical-align: top;">
                    <div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid #bae6fd;">
                      <div style="font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">${
                        typeof step === "object" ? step.title || step.step || step.action : step
                      }</div>
                      ${
                        typeof step === "object" && step.description
                          ? `<div style="font-size: 11px; color: #64748b; line-height: 1.5;">${step.description}</div>`
                          : ""
                      }
                    </div>
                  </td>
                </tr>
              </table>
            `
              )
              .join("")}
          </div>
          `
              : ""
          }

          ${
            Object.keys(aiSecureCodeExamples).length > 0
              ? `
          <!-- Secure Code Examples -->
          <div style="background: #f8fafc; border: 2px solid #64748b; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #334155; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">💻 Secure Code Examples</h3>
            ${Object.entries(aiSecureCodeExamples)
              .slice(0, 3)
              .map(
                ([title, code]) => `
              <div style="margin-bottom: 12px; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                <div style="background: #1e293b; color: #e2e8f0; padding: 10px 14px; font-size: 12px; font-weight: 600;">📝 ${title}</div>
                <pre style="background: #0f172a; color: #e2e8f0; padding: 14px; font-size: 10px; overflow-x: auto; margin: 0; font-family: Consolas, Monaco, monospace; line-height: 1.5; white-space: pre-wrap;">${
                  typeof code === "string"
                    ? code.replace(/</g, "&lt;").replace(/>/g, "&gt;")
                    : JSON.stringify(code, null, 2)
                }</pre>
              </div>
            `
              )
              .join("")}
          </div>
          `
              : ""
          }

          ${
            Object.keys(aiComplianceImpact).length > 0
              ? `
          <!-- Compliance Impact -->
          <div style="background: #faf5ff; border: 2px solid #8b5cf6; border-radius: 12px; padding: 20px;">
            <h3 style="color: #6d28d9; margin: 0 0 14px 0; font-size: 15px; font-weight: 700;">📋 Compliance Impact</h3>
            <table style="width: 100%; border-collapse: separate; border-spacing: 8px;">
              <tr>
                ${Object.entries(aiComplianceImpact)
                  .slice(0, 4)
                  .map(
                    ([framework, impact], idx) => `
                  ${idx > 0 && idx % 2 === 0 ? "</tr><tr>" : ""}
                  <td style="width: 50%; background: white; padding: 14px; border-radius: 8px; vertical-align: top; border: 1px solid #ede9fe;">
                    <div style="font-size: 13px; font-weight: 700; color: #6d28d9; margin-bottom: 6px;">📌 ${framework}</div>
                    <div style="font-size: 11px; color: #64748b; line-height: 1.5;">${
                      typeof impact === "object"
                        ? impact.description || impact.impact || JSON.stringify(impact)
                        : impact
                    }</div>
                  </td>
                `
                  )
                  .join("")}
              </tr>
            </table>
          </div>
        </div>
        `
              : ""
          }
        `
            : ""
        }`;
    } else {
      // No AI analysis available - show helpful message
      aiHtml = `<div style="padding: 40px; page-break-before: always;">
          <h2 style="font-size: 24px; font-weight: 700; color: #1e40af; border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px;">🤖 AI-Powered Security Analysis</h2>
          
          <div style="background: #e0f2fe; border: 2px solid #0284c7; border-radius: 16px; padding: 32px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">🧠</div>
            <h3 style="color: #0369a1; margin: 0 0 12px 0; font-size: 20px;">AI Analysis Insights</h3>
            <p style="font-size: 14px; color: #1e293b; line-height: 1.8; margin: 0 0 20px 0;">
              Based on the automated security scan, here are the key insights:
            </p>
            <table style="width: 100%; border-collapse: separate; border-spacing: 12px; margin-top: 24px;">
              <tr>
                ${
                  reportData.critical > 0
                    ? `
                <td style="background: #fef2f2; padding: 20px; border-radius: 12px; border: 2px solid #dc2626; text-align: center;">
                  <div style="font-size: 28px; font-weight: 800; color: #dc2626;">${reportData.critical}</div>
                  <div style="font-size: 12px; color: #991b1b; margin-top: 4px;">Critical Issues - Fix Immediately</div>
                </td>
                `
                    : ""
                }
                ${
                  reportData.high > 0
                    ? `
                <td style="background: #fff7ed; padding: 20px; border-radius: 12px; border: 2px solid #ea580c; text-align: center;">
                  <div style="font-size: 28px; font-weight: 800; color: #ea580c;">${reportData.high}</div>
                  <div style="font-size: 12px; color: #9a3412; margin-top: 4px;">High Severity - Prioritize</div>
                </td>
                `
                    : ""
                }
                <td style="background: #ecfdf5; padding: 20px; border-radius: 12px; border: 2px solid #10b981; text-align: center;">
                  <div style="font-size: 28px; font-weight: 800; color: #10b981;">${
                    reportData.securityScore
                  }</div>
                  <div style="font-size: 12px; color: #047857; margin-top: 4px;">Security Score</div>
                </td>
              </tr>
            </table>
            <div style="margin-top: 28px; padding-top: 24px; border-top: 1px solid #bfdbfe;">
              <h4 style="color: #0369a1; margin: 0 0 16px 0; font-size: 16px;">💡 Recommended Actions</h4>
              <ul style="text-align: left; margin: 0 auto; padding-left: 20px; font-size: 13px; line-height: 2; color: #1e293b; max-width: 500px;">
                ${
                  reportData.critical > 0
                    ? `<li>🔴 Address ${reportData.critical} critical vulnerabilities immediately</li>`
                    : ""
                }
                ${
                  reportData.high > 0
                    ? `<li>🟠 Remediate ${reportData.high} high-severity issues this sprint</li>`
                    : ""
                }
                ${
                  reportData.medium > 0
                    ? `<li>🟡 Plan fixes for ${reportData.medium} medium-severity findings</li>`
                    : ""
                }
                <li>📊 Enable continuous security monitoring in CI/CD pipeline</li>
                <li>🔄 Schedule regular vulnerability assessments</li>
                <li>📚 Review and update security policies based on findings</li>
              </ul>
            </div>
          </div>
        </div>`;
    }

    // ============ FOOTER ============
    const footer = `
        <div style="padding: 40px; background: #0f172a; color: white;">
          <!-- Main Footer Content -->
          <table style="width: 100%; margin-bottom: 24px;">
            <tr>
              <td style="vertical-align: middle;">
                <table>
                  <tr>
                    <td style="vertical-align: middle; padding-right: 16px;">
                      <div style="font-size: 36px;">🛡️</div>
                    </td>
                    <td style="vertical-align: middle;">
                      <div style="font-size: 20px; font-weight: 700; letter-spacing: 1px; color: white;">ONYX</div>
                      <div style="font-size: 11px; color: #94a3b8;">Security Intelligence Platform</div>
                    </td>
                  </tr>
                </table>
              </td>
              <td style="text-align: right; vertical-align: middle;">
                <div style="font-size: 12px; color: #94a3b8;">Report Generated</div>
                <div style="font-size: 14px; font-weight: 600; color: white;">${new Date().toLocaleString()}</div>
              </td>
            </tr>
          </table>
          
          <!-- Report Info -->
          <table style="width: 100%; background: #1e293b; border-radius: 12px; margin-bottom: 24px;">
            <tr>
              <td style="padding: 16px; text-align: center; border-right: 1px solid #334155;">
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Report ID</div>
                <div style="font-size: 12px; font-family: monospace; color: white;">${
                  report?.scan_id || reportId
                }</div>
              </td>
              <td style="padding: 16px; text-align: center; border-right: 1px solid #334155;">
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Project</div>
                <div style="font-size: 12px; color: white;">${
                  report?.project_name || "Security Assessment"
                }</div>
              </td>
              <td style="padding: 16px; text-align: center; border-right: 1px solid #334155;">
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Total Findings</div>
                <div style="font-size: 12px; font-weight: 600; color: ${
                  totalFindings > 0 ? "#fca5a5" : "#86efac"
                };">${totalFindings}</div>
              </td>
              <td style="padding: 16px; text-align: center;">
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Security Score</div>
                <div style="font-size: 12px; font-weight: 600; color: ${gradeColor};">${
                  reportData.securityScore
                }/100</div>
              </td>
            </tr>
          </table>
          
          <!-- Disclaimer -->
          <div style="border-top: 1px solid #334155; padding-top: 20px; text-align: center;">
            <div style="margin-bottom: 12px;">
              <span style="font-size: 16px;">🔒</span>
              <span style="font-size: 12px; font-weight: 600; letter-spacing: 1px; color: white; margin-left: 8px;">CONFIDENTIAL</span>
            </div>
            <p style="font-size: 11px; color: #94a3b8; max-width: 600px; margin: 0 auto; line-height: 1.6;">
              This document contains confidential security information. Distribution should be limited to authorized personnel only. 
              Unauthorized disclosure or distribution may result in legal action.
            </p>
            <div style="margin-top: 16px; font-size: 10px; color: #64748b;">
              © ${new Date().getFullYear()} ONYX Security Intelligence Platform. All rights reserved.
            </div>
          </div>
        </div>
      `;

    // Assemble the complete PDF
    pdfContent.innerHTML =
      coverPage +
      tocPage +
      executiveSummary +
      findingsHtml +
      complianceHtml +
      remediationHtml +
      aiHtml +
      footer;

    await generatePDF(pdfContent, {
      filename: `ONYX-Security-Report-${report?.project_name || reportId}-${
        new Date().toISOString().split("T")[0]
      }.pdf`,
      title: "ONYX Security Report",
      subtitle: `Complete Security Analysis - ${report?.project_name || "Security Assessment"}`,
      showExecutiveSummary: false,
      showTableOfContents: false,
      showHeader: false,
      showFooter: false,
      reportData: reportData,
      companyName: report?.project_name,
      confidential: true,
      format: "a4",
      orientation: "portrait",
      margin: 0,
    });

    toast.success("🎉 Complete security report generated!", {
      icon: "📄",
      duration: 4000,
    });
  } catch (error) {
    console.error("PDF generation error:", error);
    toast.error("Failed to generate PDF: " + (error.message || "Unknown error"));
  } finally {
    setIsGenerating(false);
  }
};
