import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { InvestigateReport } from "./InvestigateReport";

const DATA = {
  report: {
    finding_id: "f-1",
    summary: "The vulnerable path is reachable from the public HTTP handler.",
    exploitability: "Requires an authenticated session but no admin role.",
    evidence: [
      "src/api/orders.py:87 - user input reaches the raw query",
      "Sibling finding f-2 shares src/api/orders.py",
      "No upstream validation found",
    ],
    likely_false_positive: true,
    false_positive_reasons: ["Values are allow-listed upstream"],
    fix_guidance: "Switch to parameterized queries.",
    confidence: "high",
  },
  provider: "groq",
  model: "llama-3.3-70b",
  usage: { prompt_tokens: 10, completion_tokens: 20, requests: 1 },
};

function renderReport(overrides = {}) {
  const props = {
    data: DATA,
    reportId: "r1",
    findingIds: ["f-1", "f-2"],
    currentLabel: null,
    onAgreeFp: vi.fn(),
    isLabelPending: false,
    ...overrides,
  };
  render(
    <MemoryRouter>
      <InvestigateReport {...props} />
    </MemoryRouter>
  );
  return props;
}

describe("InvestigateReport", () => {
  it("renders badges, prose cards, evidence chips, and the model footer", () => {
    renderReport();

    expect(screen.getByText("Confidence: high")).toBeInTheDocument();
    expect(screen.getByText("Likely false positive")).toBeInTheDocument();
    expect(screen.getByText(/reachable from the public HTTP handler/)).toBeInTheDocument();
    expect(screen.getByText(/Requires an authenticated session/)).toBeInTheDocument();
    expect(screen.getByText("src/api/orders.py:87")).toBeInTheDocument();
    expect(screen.getByText(/Switch to parameterized queries/)).toBeInTheDocument();
    expect(screen.getByText(/groq\/llama-3.3-70b/)).toBeInTheDocument();
    expect(screen.getByText(/· 30 tokens/)).toBeInTheDocument();
  });

  it("deep-links sibling finding ids in evidence", () => {
    renderReport();

    const link = screen.getByRole("link", { name: "f-2" });
    expect(link).toHaveAttribute("href", "/report/r1/finding/f-2");
  });

  it("calls onAgreeFp when agreeing with a false-positive reason", async () => {
    const user = userEvent.setup();
    const props = renderReport();

    await user.click(screen.getByRole("button", { name: /Agree — mark false positive/ }));
    expect(props.onAgreeFp).toHaveBeenCalledTimes(1);
  });

  it("shows the agreed badge instead of the button once labelled false positive", () => {
    renderReport({ currentLabel: "false_positive" });

    expect(screen.getByText("Agreed")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Agree — mark false positive/ })).toBeNull();
  });

  it("renders empty states for absent evidence and reasons", () => {
    renderReport({
      data: {
        ...DATA,
        report: { ...DATA.report, evidence: [], false_positive_reasons: [] },
      },
    });

    expect(screen.getByText("No evidence collected.")).toBeInTheDocument();
    expect(screen.getByText("No false-positive indicators identified.")).toBeInTheDocument();
  });

  it("disables the agree button while a label write is pending", () => {
    renderReport({ isLabelPending: true });

    expect(screen.getByRole("button", { name: /Agree — mark false positive/ })).toBeDisabled();
  });
});
