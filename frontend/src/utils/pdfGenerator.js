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
  element.style.fontFamily =
    "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif";
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
    if (
      el.classList.contains("text-orange-400") ||
      el.classList.contains("text-orange-500")
    ) {
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
    if (
      el.classList.contains("text-blue-400") ||
      el.classList.contains("text-blue-500") ||
      el.classList.contains("text-cyan-400") ||
      el.classList.contains("text-cyan-500")
    ) {
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
    if (
      el.classList.contains("text-pink-400") ||
      el.classList.contains("text-pink-500")
    ) {
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
    if (
      el.classList.contains("bg-gray-500/10") ||
      el.classList.contains("bg-gray-500/20")
    ) {
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
    if (
      el.classList.contains("bg-orange-500/10") ||
      el.classList.contains("bg-orange-500/20")
    ) {
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
    if (
      el.classList.contains("bg-blue-500/10") ||
      el.classList.contains("bg-blue-500/20") ||
      el.classList.contains("bg-cyan-500/10")
    ) {
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
    if (
      el.classList.contains("border-red-500/30") ||
      el.classList.contains("border-red-500")
    ) {
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
    if (
      el.classList.contains("border-green-500/30") ||
      el.classList.contains("border-green-500")
    ) {
      el.style.borderColor = "#6ee7b7";
    }
    if (
      el.classList.contains("border-blue-500/30") ||
      el.classList.contains("border-blue-500")
    ) {
      el.style.borderColor = "#93c5fd";
    }

    // ===== SPECIAL ELEMENTS =====
    // Code blocks
    if (
      el.tagName === "CODE" ||
      el.tagName === "PRE" ||
      el.classList.contains("code-block")
    ) {
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
    if (
      el.classList.contains("py-1") &&
      el.classList.contains("rounded-full")
    ) {
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
  const noPrintElements = element.querySelectorAll(
    ".no-print, .print\\:hidden"
  );
  noPrintElements.forEach((el) => {
    el.style.display = "none";
  });

  return element;
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
    title = "SecureDevOps AI",
    subtitle = "Security Compliance Report",
    format = "letter",
    orientation = "portrait",
    margin = 0.5,
    quality = 0.98,
    scale = 2,
    showHeader = true,
    showFooter = true,
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

    // Add PDF header with branding
    if (showHeader) {
      const header = document.createElement("div");
      header.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        margin-bottom: 24px;
        border-bottom: 2px solid #3b82f6;
      `;
      header.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
            <span style="color: white; font-weight: bold; font-size: 18px;">S</span>
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #111827;">${title}</div>
            <div style="font-size: 11px; color: #6b7280;">${subtitle}</div>
          </div>
        </div>
        <div style="text-align: right; font-size: 11px; color: #6b7280;">
          <div>Generated: ${new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}</div>
          <div>${new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          })}</div>
        </div>
      `;
      clonedElement.insertBefore(header, clonedElement.firstChild);
    }

    // Add PDF footer
    if (showFooter) {
      const footer = document.createElement("div");
      footer.style.cssText = `
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid #e5e7eb;
        text-align: center;
        font-size: 10px;
        color: #9ca3af;
      `;
      footer.innerHTML = `
        <div>This report was automatically generated by SecureDevOps AI Platform</div>
        <div style="margin-top: 4px;">© ${new Date().getFullYear()} SecureDevOps AI - Confidential</div>
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
    `;
    tempContainer.appendChild(clonedElement);
    document.body.appendChild(tempContainer);

    // PDF options
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
      },
      jsPDF: {
        unit: "in",
        format,
        orientation,
      },
      pagebreak: { mode: ["avoid-all", "css", "legacy"] },
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

export default { generatePDF, applyPDFStyles };
