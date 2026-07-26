/**
 * PDF Generator Utility
 * Provides professional PDF generation with proper styling for dark-themed web apps
 */
import html2pdf from "html2pdf.js";

/**
 * Apply PDF-friendly styles to an element for proper rendering
 * Converts dark theme to professional light theme for PDF output
 */
export const applyPDFStyles = (element) => {
  // Main container styles
  element.style.backgroundColor = "#ffffff";
  element.style.color = "#1f2937";
  element.style.padding = "24px";
  element.style.fontFamily = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif";
  element.style.fontSize = "12px";
  element.style.lineHeight = "1.6";

  const allElements = element.querySelectorAll("*");

  allElements.forEach((el) => {
    // Remove any dark mode classes that might interfere
    el.classList.remove("dark");

    // ===== TEXT COLORS =====
    // White text -> Dark gray
    if (el.classList.contains("text-white")) {
      el.style.color = "#111827";
      el.style.fontWeight = "600";
    }

    // Gray text variations
    if (el.classList.contains("text-gray-100")) el.style.color = "#1f2937";
    if (el.classList.contains("text-gray-200")) el.style.color = "#374151";
    if (el.classList.contains("text-gray-300")) el.style.color = "#4b5563";
    if (el.classList.contains("text-gray-400")) el.style.color = "#6b7280";
    if (el.classList.contains("text-gray-500")) el.style.color = "#6b7280";
    if (el.classList.contains("text-gray-600")) el.style.color = "#4b5563";

    // Severity colors - make vibrant for PDF
    if (
      el.classList.contains("text-red-400") ||
      el.classList.contains("text-red-500") ||
      el.classList.contains("text-red-600")
    ) {
      el.style.color = "#dc2626";
      el.style.fontWeight = "600";
    }
    if (el.classList.contains("text-orange-400") || el.classList.contains("text-orange-500")) {
      el.style.color = "#ea580c";
      el.style.fontWeight = "600";
    }
    if (
      el.classList.contains("text-yellow-400") ||
      el.classList.contains("text-yellow-500") ||
      el.classList.contains("text-amber-400") ||
      el.classList.contains("text-amber-500")
    ) {
      el.style.color = "#d97706";
      el.style.fontWeight = "600";
    }
    if (
      el.classList.contains("text-green-400") ||
      el.classList.contains("text-green-500") ||
      el.classList.contains("text-emerald-400") ||
      el.classList.contains("text-emerald-500")
    ) {
      el.style.color = "#059669";
      el.style.fontWeight = "600";
    }
    if (el.classList.contains("text-cyan-400") || el.classList.contains("text-cyan-500")) {
      el.style.color = "#06b6d4";
      el.style.fontWeight = "600";
    }
    if (el.classList.contains("text-blue-400") || el.classList.contains("text-blue-500")) {
      el.style.color = "#2563eb";
      el.style.fontWeight = "600";
    }
    if (
      el.classList.contains("text-purple-400") ||
      el.classList.contains("text-purple-500") ||
      el.classList.contains("text-violet-400") ||
      el.classList.contains("text-violet-500")
    ) {
      el.style.color = "#7c3aed";
      el.style.fontWeight = "600";
    }
    if (el.classList.contains("text-pink-400") || el.classList.contains("text-pink-500")) {
      el.style.color = "#db2777";
      el.style.fontWeight = "600";
    }

    // ===== BACKGROUNDS =====
    // Dark backgrounds -> Light backgrounds
    if (
      el.classList.contains("bg-gray-800") ||
      el.classList.contains("bg-gray-900") ||
      el.classList.contains("bg-gray-950") ||
      el.classList.contains("bg-black") ||
      el.classList.contains("glass-container") ||
      el.classList.contains("bg-gray-800/50") ||
      el.classList.contains("bg-gray-800/30") ||
      el.classList.contains("bg-gray-700") ||
      el.classList.contains("bg-gray-700/50") ||
      el.classList.contains("bg-gray-900/50") ||
      el.classList.contains("bg-gray-900/30")
    ) {
      el.style.backgroundColor = "#f9fafb";
      el.style.border = "1px solid #e5e7eb";
      el.style.borderRadius = "8px";
    }

    // Gray severity backgrounds (info level)
    if (el.classList.contains("bg-gray-500/10") || el.classList.contains("bg-gray-500/20")) {
      el.style.backgroundColor = "#f3f4f6";
      el.style.border = "1px solid #d1d5db";
    }

    // Gradient backgrounds -> Solid light backgrounds
    if (
      el.classList.contains("bg-gradient-to-br") ||
      el.classList.contains("bg-gradient-to-r") ||
      el.classList.contains("bg-gradient-to-b") ||
      el.classList.contains("bg-gradient-to-l") ||
      el.classList.contains("bg-gradient-to-t")
    ) {
      el.style.background = "#ffffff";
    }

    // Severity background colors - lighter versions for PDF
    if (
      el.classList.contains("bg-red-500/10") ||
      el.classList.contains("bg-red-500/20") ||
      el.classList.contains("bg-red-600/20")
    ) {
      el.style.backgroundColor = "#fef2f2";
      el.style.border = "1px solid #fecaca";
    }
    if (el.classList.contains("bg-orange-500/10") || el.classList.contains("bg-orange-500/20")) {
      el.style.backgroundColor = "#fff7ed";
      el.style.border = "1px solid #fed7aa";
    }
    if (
      el.classList.contains("bg-yellow-500/10") ||
      el.classList.contains("bg-yellow-500/20") ||
      el.classList.contains("bg-amber-500/10")
    ) {
      el.style.backgroundColor = "#fffbeb";
      el.style.border = "1px solid #fde68a";
    }
    if (
      el.classList.contains("bg-green-500/10") ||
      el.classList.contains("bg-green-500/20") ||
      el.classList.contains("bg-emerald-500/10")
    ) {
      el.style.backgroundColor = "#ecfdf5";
      el.style.border = "1px solid #a7f3d0";
    }
    if (el.classList.contains("bg-cyan-500/10")) {
      el.style.backgroundColor = "#ecfeff";
      el.style.border = "1px solid #67e8f9";
    }
    if (el.classList.contains("bg-blue-500/10") || el.classList.contains("bg-blue-500/20")) {
      el.style.backgroundColor = "#eff6ff";
      el.style.border = "1px solid #bfdbfe";
    }
    if (
      el.classList.contains("bg-purple-500/10") ||
      el.classList.contains("bg-purple-500/20") ||
      el.classList.contains("bg-violet-500/10")
    ) {
      el.style.backgroundColor = "#f5f3ff";
      el.style.border = "1px solid #ddd6fe";
    }

    // ===== BORDERS =====
    if (
      el.classList.contains("border-gray-700") ||
      el.classList.contains("border-gray-800") ||
      el.classList.contains("border-gray-700/50") ||
      el.classList.contains("border-gray-600") ||
      el.classList.contains("border-gray-500/30")
    ) {
      el.style.borderColor = "#e5e7eb";
    }
    if (el.classList.contains("border-red-500/30") || el.classList.contains("border-red-500")) {
      el.style.borderColor = "#fca5a5";
    }
    if (
      el.classList.contains("border-orange-500/30") ||
      el.classList.contains("border-orange-500")
    ) {
      el.style.borderColor = "#fdba74";
    }
    if (
      el.classList.contains("border-yellow-500/30") ||
      el.classList.contains("border-yellow-500")
    ) {
      el.style.borderColor = "#fcd34d";
    }
    if (el.classList.contains("border-green-500/30") || el.classList.contains("border-green-500")) {
      el.style.borderColor = "#6ee7b7";
    }
    if (el.classList.contains("border-cyan-500/30") || el.classList.contains("border-cyan-500")) {
      el.style.borderColor = "#67e8f9";
    }
    if (el.classList.contains("border-blue-500/30") || el.classList.contains("border-blue-500")) {
      el.style.borderColor = "#93c5fd";
    }

    // ===== SPECIAL ELEMENTS =====
    // Code blocks
    if (el.tagName === "CODE" || el.tagName === "PRE" || el.classList.contains("code-block")) {
      el.style.backgroundColor = "#f3f4f6";
      el.style.color = "#1f2937";
      el.style.padding = "8px 12px";
      el.style.borderRadius = "6px";
      el.style.fontFamily = "'Fira Code', 'Consolas', monospace";
      el.style.fontSize = "11px";
      el.style.border = "1px solid #e5e7eb";
    }

    // Tables
    if (el.tagName === "TABLE") {
      el.style.borderCollapse = "collapse";
      el.style.width = "100%";
      el.style.marginTop = "12px";
      el.style.marginBottom = "12px";
    }
    if (el.tagName === "TH") {
      el.style.backgroundColor = "#f3f4f6";
      el.style.color = "#111827";
      el.style.fontWeight = "600";
      el.style.padding = "10px 12px";
      el.style.borderBottom = "2px solid #e5e7eb";
      el.style.textAlign = "left";
    }
    if (el.tagName === "TD") {
      el.style.padding = "10px 12px";
      el.style.borderBottom = "1px solid #e5e7eb";
      el.style.color = "#374151";
    }

    // Headings
    if (el.tagName === "H1") {
      el.style.color = "#111827";
      el.style.fontSize = "24px";
      el.style.fontWeight = "700";
      el.style.marginBottom = "16px";
      el.style.borderBottom = "2px solid #3b82f6";
      el.style.paddingBottom = "8px";
    }
    if (el.tagName === "H2") {
      el.style.color = "#1f2937";
      el.style.fontSize = "20px";
      el.style.fontWeight = "600";
      el.style.marginTop = "24px";
      el.style.marginBottom = "12px";
    }
    if (el.tagName === "H3") {
      el.style.color = "#374151";
      el.style.fontSize = "16px";
      el.style.fontWeight = "600";
      el.style.marginTop = "16px";
      el.style.marginBottom = "8px";
    }

    // Lists
    if (el.tagName === "UL" || el.tagName === "OL") {
      el.style.marginLeft = "20px";
      el.style.color = "#374151";
    }
    if (el.tagName === "LI") {
      el.style.marginBottom = "4px";
    }

    // Links
    if (el.tagName === "A") {
      el.style.color = "#2563eb";
      el.style.textDecoration = "underline";
    }

    // Fix truncated text for PDF - allow full text to wrap
    if (el.classList.contains("truncate")) {
      el.style.overflow = "visible";
      el.style.textOverflow = "clip";
      el.style.whiteSpace = "normal";
      el.style.wordBreak = "break-word";
    }

    // Fix text that might have line-through or be cut off
    if (el.classList.contains("line-through")) {
      el.style.textDecoration = "line-through";
    } else {
      // Ensure no unwanted strikethrough
      if (el.style.textDecoration === "line-through") {
        el.style.textDecoration = "none";
      }
    }

    // Ensure min-w-0 elements can expand in PDF
    if (el.classList.contains("min-w-0")) {
      el.style.minWidth = "auto";
      el.style.width = "auto";
    }

    // ===== FLEXBOX ALIGNMENT =====
    // Preserve flex container alignment for proper icon/text alignment in PDF
    if (el.classList.contains("flex")) {
      el.style.display = "flex";
    }
    if (el.classList.contains("inline-flex")) {
      el.style.display = "inline-flex";
    }
    if (el.classList.contains("items-center")) {
      el.style.alignItems = "center";
    }
    if (el.classList.contains("items-start")) {
      el.style.alignItems = "flex-start";
    }
    if (el.classList.contains("items-end")) {
      el.style.alignItems = "flex-end";
    }
    if (el.classList.contains("justify-center")) {
      el.style.justifyContent = "center";
    }
    if (el.classList.contains("justify-between")) {
      el.style.justifyContent = "space-between";
    }
    if (el.classList.contains("gap-1")) {
      el.style.gap = "4px";
    }
    if (el.classList.contains("gap-2")) {
      el.style.gap = "8px";
    }
    if (el.classList.contains("gap-3")) {
      el.style.gap = "12px";
    }
    if (el.classList.contains("gap-4")) {
      el.style.gap = "16px";
    }

    // Badges/Pills (severity badges like Medium, High, etc.)
    if (
      el.classList.contains("rounded-full") &&
      (el.classList.contains("px-2") || el.classList.contains("px-3"))
    ) {
      el.style.display = "inline-block";
      el.style.padding = "5px 12px";
      el.style.borderRadius = "9999px";
      el.style.fontSize = "11px";
      el.style.fontWeight = "500";
      el.style.lineHeight = "1.2";
      el.style.verticalAlign = "middle";
      el.style.textAlign = "center";
      el.style.boxSizing = "border-box";
    }

    // Compliance status badges with rounded-lg (Non-Compliant, Compliant)
    if (
      el.classList.contains("rounded-lg") &&
      el.classList.contains("border") &&
      (el.classList.contains("px-3") || el.classList.contains("py-1.5"))
    ) {
      el.style.display = "inline-flex";
      el.style.alignItems = "center";
      el.style.padding = "6px 12px";
      el.style.borderRadius = "8px";
      el.style.fontSize = "12px";
      el.style.fontWeight = "500";
      el.style.lineHeight = "1";
    }

    // Icons - ensure proper sizing and alignment
    if (
      el.tagName === "svg" ||
      el.classList.contains("h-4") ||
      el.classList.contains("h-5") ||
      el.classList.contains("h-6")
    ) {
      // Keep icons but ensure they're visible and properly sized
      el.style.color = "inherit";
      el.style.flexShrink = "0";
      el.style.display = "inline-block";
      el.style.verticalAlign = "middle";
      if (el.classList.contains("h-4")) {
        el.style.width = "16px";
        el.style.height = "16px";
      }
      if (el.classList.contains("h-5")) {
        el.style.width = "20px";
        el.style.height = "20px";
      }
      if (el.classList.contains("h-6")) {
        el.style.width = "24px";
        el.style.height = "24px";
      }
    }

    // Handle margin classes for icon spacing
    if (el.classList.contains("mr-1")) {
      el.style.marginRight = "4px";
    }
    if (el.classList.contains("mr-1.5")) {
      el.style.marginRight = "6px";
    }
    if (el.classList.contains("mr-2")) {
      el.style.marginRight = "8px";
    }

    // Handle padding classes for badges - override with equal padding for centering
    if (el.classList.contains("py-1") && el.classList.contains("rounded-full")) {
      el.style.paddingTop = "5px";
      el.style.paddingBottom = "5px";
    }
    if (el.classList.contains("py-0.5")) {
      el.style.paddingTop = "2px";
      el.style.paddingBottom = "2px";
    }

    // Ensure text inside severity badges is vertically centered
    if (
      el.classList.contains("text-xs") &&
      el.classList.contains("font-medium") &&
      el.classList.contains("rounded-full")
    ) {
      el.style.lineHeight = "1.2";
      el.style.display = "inline-block";
      el.style.textAlign = "center";
      el.style.verticalAlign = "middle";
    }

    // Ensure SVG icons inside flex containers align properly
    if (el.tagName === "svg") {
      el.style.display = "inline-block";
      el.style.verticalAlign = "middle";
      el.style.flexShrink = "0";
      // Ensure the SVG maintains its aspect ratio and size
      if (!el.style.width) {
        el.style.width = "1em";
        el.style.height = "1em";
      }
    }

    // Remove animations
    el.style.animation = "none";
    el.style.transition = "none";

    // Ensure visibility
    el.style.opacity = "1";
    el.style.visibility = "visible";
  });

  // Hide elements marked as no-print
  const noPrintElements = element.querySelectorAll(".no-print, .print\\:hidden");
  noPrintElements.forEach((el) => {
    el.style.display = "none";
  });

  return element;
};

/**
 * Generate executive summary section for PDF
 * @param {Object} reportData - Report data containing findings
 * @returns {HTMLElement}
 */
const createExecutiveSummarySection = (reportData) => {
  const summary = document.createElement("div");
  summary.style.cssText = `
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  `;

  const totalFindings = reportData?.totalFindings || 0;
  const criticalCount = reportData?.critical || 0;
  const highCount = reportData?.high || 0;
  const mediumCount = reportData?.medium || 0;
  const lowCount = reportData?.low || 0;
  const riskScore = reportData?.riskScore || 0;
  const securityScore = reportData?.securityScore || 100;

  summary.innerHTML = `
    <div style="margin-bottom: 16px;">
      <h3 style="font-size: 16px; font-weight: 700; color: #0369a1; margin: 0 0 8px 0; display: flex; align-items: center; gap: 8px;">
        📊 Executive Summary
      </h3>
      <p style="font-size: 12px; color: #475569; margin: 0; line-height: 1.5;">
        This security assessment identified <strong style="color: #1e40af;">${totalFindings}</strong> total findings 
        with a security score of <strong style="color: ${
          securityScore >= 80 ? "#059669" : securityScore >= 60 ? "#d97706" : "#dc2626"
        };">${securityScore}/100</strong>.
      </p>
    </div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 100px; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #dc2626;">${criticalCount}</div>
        <div style="font-size: 10px; font-weight: 600; color: #991b1b; text-transform: uppercase;">Critical</div>
      </div>
      <div style="flex: 1; min-width: 100px; background: #ffedd5; border: 1px solid #fdba74; border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #ea580c;">${highCount}</div>
        <div style="font-size: 10px; font-weight: 600; color: #9a3412; text-transform: uppercase;">High</div>
      </div>
      <div style="flex: 1; min-width: 100px; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #d97706;">${mediumCount}</div>
        <div style="font-size: 10px; font-weight: 600; color: #92400e; text-transform: uppercase;">Medium</div>
      </div>
      <div style="flex: 1; min-width: 100px; background: #dbeafe; border: 1px solid #93c5fd; border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #2563eb;">${lowCount}</div>
        <div style="font-size: 10px; font-weight: 600; color: #1e40af; text-transform: uppercase;">Low</div>
      </div>
    </div>
    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #bae6fd;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 11px; color: #64748b;">
          <strong>Risk Level:</strong> 
          <span style="color: ${
            riskScore <= 25
              ? "#059669"
              : riskScore <= 50
                ? "#d97706"
                : riskScore <= 75
                  ? "#ea580c"
                  : "#dc2626"
          }; font-weight: 600;">
            ${
              riskScore <= 25
                ? "Low"
                : riskScore <= 50
                  ? "Medium"
                  : riskScore <= 75
                    ? "High"
                    : "Critical"
            } (${riskScore}%)
          </span>
        </div>
        <div style="font-size: 11px; color: #64748b;">
          <strong>Security Score:</strong> 
          <span style="color: ${
            securityScore >= 80 ? "#059669" : securityScore >= 60 ? "#d97706" : "#dc2626"
          }; font-weight: 600;">
            ${securityScore}/100
          </span>
        </div>
      </div>
    </div>
  `;

  return summary;
};

/**
 * Create a table of contents for the PDF
 * @returns {HTMLElement}
 */
const createTableOfContents = () => {
  const toc = document.createElement("div");
  toc.style.cssText = `
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 24px;
  `;

  toc.innerHTML = `
    <h3 style="font-size: 14px; font-weight: 700; color: #1e293b; margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px;">
      📑 Table of Contents
    </h3>
    <div style="font-size: 11px; color: #475569; line-height: 1.8;">
      <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #cbd5e1;">
        <span>1. Executive Summary</span>
        <span style="color: #94a3b8;">Page 1</span>
      </div>
      <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #cbd5e1;">
        <span>2. Security Overview</span>
        <span style="color: #94a3b8;">Page 1</span>
      </div>
      <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #cbd5e1;">
        <span>3. Compliance Analysis</span>
        <span style="color: #94a3b8;">Page 2</span>
      </div>
      <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #cbd5e1;">
        <span>4. Detailed Findings</span>
        <span style="color: #94a3b8;">Page 3</span>
      </div>
      <div style="display: flex; justify-content: space-between; padding: 4px 0;">
        <span>5. Recommendations</span>
        <span style="color: #94a3b8;">Page 4</span>
      </div>
    </div>
  `;

  return toc;
};

/**
 * Generate a professional PDF from an HTML element
 * @param {HTMLElement} element - The element to convert to PDF
 * @param {Object} options - PDF generation options
 * @returns {Promise<void>}
 */
export const generatePDF = async (element, options = {}) => {
  const {
    filename = `report-${new Date().toISOString().split("T")[0]}.pdf`,
    title = "ONYX Security",
    subtitle = "Security Compliance Report",
    format = "letter",
    orientation = "portrait",
    margin = 0.5,
    quality = 0.98,
    scale = 2,
    showHeader = true,
    showFooter = true,
    showExecutiveSummary = true,
    showTableOfContents = false,
    reportData = null,
    companyName = "",
    confidential = true,
    onStart = () => {},
    onSuccess = () => {},
    onError = () => {},
  } = options;

  onStart();

  try {
    // Clone the element
    const clonedElement = element.cloneNode(true);

    // Apply PDF-friendly styles
    applyPDFStyles(clonedElement);

    // Add PDF header with enhanced branding
    if (showHeader) {
      const header = document.createElement("div");
      header.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        margin-bottom: 24px;
        background: linear-gradient(135deg, #1e40af, #7c3aed);
        border-radius: 12px;
        color: white;
      `;
      header.innerHTML = `
        <div style="display: flex; align-items: center; gap: 16px;">
          <div style="width: 50px; height: 50px; background: rgba(255,255,255,0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
            <span style="font-size: 24px;">🛡️</span>
          </div>
          <div>
            <div style="font-size: 20px; font-weight: 800; letter-spacing: -0.5px;">${title}</div>
            <div style="font-size: 12px; opacity: 0.9; margin-top: 2px;">${subtitle}</div>
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 12px; font-weight: 600; margin-bottom: 4px;">
            ${companyName || "Security Assessment Report"}
          </div>
          <div style="font-size: 11px; opacity: 0.8;">
            ${new Date().toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
          ${
            confidential
              ? `<div style="font-size: 9px; margin-top: 4px; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; display: inline-block;">🔒 CONFIDENTIAL</div>`
              : ""
          }
        </div>
      `;
      clonedElement.insertBefore(header, clonedElement.firstChild);
    }

    // Add Table of Contents after header
    if (showTableOfContents) {
      const toc = createTableOfContents();
      const firstChild = clonedElement.firstChild;
      if (firstChild && firstChild.nextSibling) {
        clonedElement.insertBefore(toc, firstChild.nextSibling);
      } else {
        clonedElement.appendChild(toc);
      }
    }

    // Add Executive Summary after TOC or header
    if (showExecutiveSummary && reportData) {
      const summary = createExecutiveSummarySection(reportData);
      const headerElement = clonedElement.firstChild;
      if (headerElement) {
        const insertAfter =
          showTableOfContents && headerElement.nextSibling
            ? headerElement.nextSibling
            : headerElement;
        if (insertAfter.nextSibling) {
          clonedElement.insertBefore(summary, insertAfter.nextSibling);
        } else {
          clonedElement.appendChild(summary);
        }
      }
    }

    // Add PDF footer with enhanced styling
    if (showFooter) {
      const footer = document.createElement("div");
      footer.style.cssText = `
        margin-top: 40px;
        padding: 20px;
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        text-align: center;
      `;
      footer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div style="font-size: 10px; color: #64748b;">
            <strong>Generated by:</strong> ONYX Security Intelligence Platform
          </div>
          <div style="font-size: 10px; color: #64748b;">
            <strong>Date:</strong> ${new Date().toLocaleString()}
          </div>
        </div>
        <div style="border-top: 1px solid #e2e8f0; padding-top: 12px; display: flex; justify-content: center; gap: 20px; font-size: 10px; color: #94a3b8;">
          <span>© ${new Date().getFullYear()} ONYX Security</span>
          <span>|</span>
          <span>${confidential ? "🔒 Confidential Document" : "Security Report"}</span>
          <span>|</span>
          <span>v1.0</span>
        </div>
      `;
      clonedElement.appendChild(footer);
    }

    // Create temporary container
    const tempContainer = document.createElement("div");
    tempContainer.style.cssText = `
      position: absolute;
      left: -9999px;
      top: 0;
      width: ${element.offsetWidth || 800}px;
      background: white;
      font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    `;
    tempContainer.appendChild(clonedElement);
    document.body.appendChild(tempContainer);

    // PDF options with enhanced settings
    const pdfOptions = {
      margin: Array.isArray(margin) ? margin : [margin, margin],
      filename,
      image: { type: "jpeg", quality },
      html2canvas: {
        scale,
        useCORS: true,
        letterRendering: true,
        logging: false,
        backgroundColor: "#ffffff",
        windowWidth: element.offsetWidth || 800,
        allowTaint: true,
      },
      jsPDF: {
        unit: "in",
        format,
        orientation,
        compress: true,
      },
      pagebreak: {
        mode: ["avoid-all", "css", "legacy"],
        before: ".page-break-before",
        after: ".page-break-after",
      },
    };

    await html2pdf().set(pdfOptions).from(clonedElement).save();

    // Cleanup
    document.body.removeChild(tempContainer);

    onSuccess();
  } catch (error) {
    console.error("PDF generation error:", error);
    onError(error);
    throw error;
  }
};

/**
 * Generate a compliance-specific PDF with enhanced styling
 * @param {HTMLElement} element - The element to convert to PDF
 * @param {Object} options - PDF generation options
 * @returns {Promise<void>}
 */
export const generateCompliancePDF = async (element, options = {}) => {
  const enhancedOptions = {
    ...options,
    showTableOfContents: true,
    showExecutiveSummary: true,
    subtitle: options.subtitle || "Compliance Assessment Report",
    confidential: true,
  };

  return generatePDF(element, enhancedOptions);
};

export default { generatePDF, generateCompliancePDF, applyPDFStyles };
