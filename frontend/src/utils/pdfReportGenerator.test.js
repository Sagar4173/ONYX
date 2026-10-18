import { describe, it, expect, vi, beforeEach } from "vitest";
import { generatePDF } from "./pdfGenerator";
import { generateViewPDF } from "./pdfReportGenerator";

vi.mock("./pdfGenerator", () => ({
  generatePDF: vi.fn().mockResolvedValue(undefined),
}));

const baseReport = {
  project_name: "ONYX QA",
  findings_by_severity: { critical: 1, high: 2, medium: 3, low: 0, info: 0 },
  findings: [],
};

describe("generateViewPDF", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("builds the report and hands off to generatePDF without errors (regression: gradeColor TDZ)", async () => {
    const toast = { success: vi.fn(), error: vi.fn() };
    const setIsGenerating = vi.fn();

    await generateViewPDF({
      report: baseReport,
      aiAnalysis: { risk_score: 60, security_score: 72 },
      reportId: "qa-live-check-001",
      setIsGenerating,
      toast,
    });

    expect(toast.error).not.toHaveBeenCalled();
    expect(generatePDF).toHaveBeenCalledTimes(1);

    const [content, options] = generatePDF.mock.calls[0];
    // security_score 72 -> gradeColor #10b981 must be interpolated into the cover page
    expect(content.innerHTML).toContain("#10b981");
    expect(options.filename).toContain("ONYX QA");
    expect(setIsGenerating).toHaveBeenCalledWith(true);
    expect(setIsGenerating).toHaveBeenLastCalledWith(false);
  });

  it("uses the low-grade color for weak security scores", async () => {
    const toast = { success: vi.fn(), error: vi.fn() };

    await generateViewPDF({
      report: baseReport,
      aiAnalysis: { risk_score: 80, security_score: 40 },
      reportId: "qa-live-check-002",
      setIsGenerating: vi.fn(),
      toast,
    });

    expect(toast.error).not.toHaveBeenCalled();
    const [content] = generatePDF.mock.calls[0];
    expect(content.innerHTML).toContain("#ef4444");
  });
});
