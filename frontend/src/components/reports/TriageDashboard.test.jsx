import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { triageAPI, labelsAPI } from "../../services/api";
import TriageDashboard from "./TriageDashboard";

vi.mock("../../services/api", () => ({
  triageAPI: { getTriage: vi.fn(), rescoreTriage: vi.fn() },
  labelsAPI: { setFindingLabel: vi.fn() },
}));

vi.mock("react-hot-toast", () => {
  const toastMock = Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  });
  return { default: toastMock };
});

const TRIAGE = {
  total_findings: 3,
  priority_counts: { immediate: 1, high: 1, medium: 1, low: 0, informational: 0 },
  executive_summary: "Top risks focus on auth.",
  ranked_findings: [
    {
      finding_id: "f-1",
      title: "SQL Injection",
      file_path: "app.py",
      composite_score: 91.2,
      priority: "immediate",
      sla_deadline: "2026-10-20",
      triage_label: null,
      score_breakdown: {
        severity: 9,
        cvss: 8,
        exploitability: 7,
        business_impact: 6,
        compliance_risk: 5,
        epss: 4,
        false_positive_adjustment: 0,
      },
      ai_triage_summary: "Internet-facing sink.",
    },
    {
      finding_id: "f-2",
      title: "Hardcoded key",
      file_path: "config.py",
      composite_score: 74.5,
      priority: "high",
      triage_label: null,
      score_breakdown: {
        severity: 7,
        cvss: 6,
        exploitability: 5,
        business_impact: 5,
        compliance_risk: 4,
        epss: 3,
        false_positive_adjustment: 0,
      },
    },
    {
      finding_id: "f-3",
      title: "Weak hash",
      file_path: "util.py",
      composite_score: 52.1,
      priority: "medium",
      triage_label: null,
      score_breakdown: {
        severity: 5,
        cvss: 4,
        exploitability: 4,
        business_impact: 3,
        compliance_risk: 3,
        epss: 2,
        false_positive_adjustment: 0,
      },
    },
  ],
};

function renderDashboard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TriageDashboard scanId="s1" reportId="r1" />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  triageAPI.getTriage.mockResolvedValue(TRIAGE);
  labelsAPI.setFindingLabel.mockResolvedValue({ triage_label: "accepted" });
});

describe("TriageDashboard", () => {
  it("renders ranked rows with deep links and labels from the expanded rail", async () => {
    const user = userEvent.setup();
    renderDashboard();
    await waitFor(() => expect(screen.getByText("SQL Injection")).toBeInTheDocument());

    expect(screen.getByRole("link", { name: "SQL Injection" })).toHaveAttribute(
      "href",
      "/report/r1/finding/f-1"
    );

    await user.click(screen.getByRole("button", { name: "Expand details for SQL Injection" }));
    await user.click(await screen.findByRole("button", { name: "Label as Accept" }));
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f-1", "accepted");
  });

  it("labels the keyboard cursor and warns when nothing is focused", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("SQL Injection")).toBeInTheDocument());

    fireEvent.keyDown(document, { key: "a" });
    expect(toast.error).toHaveBeenCalledWith("No row focused — press J first");
    expect(labelsAPI.setFindingLabel).not.toHaveBeenCalled();

    fireEvent.keyDown(document, { key: "j" });
    fireEvent.keyDown(document, { key: "a" });
    await waitFor(() =>
      expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f-1", "accepted")
    );
  });

  it("opens the shortcut overlay on ?", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("SQL Injection")).toBeInTheDocument());
    fireEvent.keyDown(document, { key: "?" });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Triage shortcuts")).toBeInTheDocument();
  });

  it("bulk-labels selected rows from the toolbar", async () => {
    const user = userEvent.setup();
    renderDashboard();
    await waitFor(() => expect(screen.getByText("SQL Injection")).toBeInTheDocument());

    await user.click(screen.getByRole("checkbox", { name: "Select SQL Injection" }));
    await user.click(screen.getByRole("checkbox", { name: "Select Hardcoded key" }));
    expect(screen.getByText("2 selected")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "False positive" }));
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledTimes(2);
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f-1", "false_positive");
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f-2", "false_positive");
    await waitFor(() => expect(screen.queryByText("2 selected")).toBeNull());
  });
});
