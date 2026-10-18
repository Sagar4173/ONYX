import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { reportsAPI, labelsAPI } from "../services/api";
import { getAIFeatures, runInvestigate } from "@services/aiClient";
import FindingDetail from "./FindingDetail";

vi.mock("../services/api", () => ({
  reportsAPI: { getReport: vi.fn() },
  labelsAPI: { setFindingLabel: vi.fn() },
  api: { post: vi.fn() },
  API_BASE_URL: "http://api.test",
  utils: { getStatusColor: () => "text-gray-400" },
}));

vi.mock("@services/aiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, getAIFeatures: vi.fn(), runInvestigate: vi.fn() };
});

vi.mock("react-hot-toast", () => {
  const toastMock = Object.assign(vi.fn(), { success: vi.fn(), error: vi.fn() });
  return { default: toastMock };
});

const REPORT = {
  scan_id: "scan-1",
  status: "completed",
  project_name: "demo",
  created_at: "2026-10-17T00:00:00Z",
  scan_results: [
    {
      scanner: "semgrep",
      status: "completed",
      findings: [
        {
          id: "f-1",
          severity: "high",
          scanner: "semgrep",
          title: "SQL Injection",
          description: "User input flows into query",
          file_path: "app.py",
          line_number: 42,
          code_snippet: 'query = f"SELECT * FROM t WHERE id={uid}"',
          remediation: "Use parameterized queries",
          cwe_id: "89",
          cve_id: null,
          triage_label: null,
          cvss_score: {
            version: "3.1",
            base_score: 9.8,
            vector_string: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
          },
        },
      ],
    },
  ],
};

const INVESTIGATE_ENVELOPE = {
  report: {
    finding_id: "f-1",
    summary: "Vulnerable path is reachable from the public handler.",
    exploitability: "No admin role required.",
    evidence: [],
    likely_false_positive: false,
    false_positive_reasons: [],
    fix_guidance: "Use parameterized queries.",
    confidence: "medium",
  },
  provider: "groq",
  model: "llama-3.3-70b",
  usage: { prompt_tokens: 1, completion_tokens: 2, requests: 1 },
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/report/r1/finding/f-1"]}>
        <Routes>
          <Route path="/report/:reportId/finding/:findingId" element={<FindingDetail />} />
          <Route path="/report/:reportId" element={<div>report page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  reportsAPI.getReport.mockResolvedValue(REPORT);
  labelsAPI.setFindingLabel.mockResolvedValue({ triage_label: "accepted" });
  getAIFeatures.mockResolvedValue({ investigate_agent_enabled: true });
  runInvestigate.mockResolvedValue(INVESTIGATE_ENVELOPE);
});

describe("FindingDetail", () => {
  it("renders the header block, body sections, and action rail", async () => {
    renderPage();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "SQL Injection" })).toBeInTheDocument()
    );

    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("CWE-89")).toBeInTheDocument();
    expect(screen.getByText(/CVSS 9\.8/)).toBeInTheDocument();
    expect(screen.getByText("app.py:42")).toBeInTheDocument();
    expect(screen.getByText("User input flows into query")).toBeInTheDocument();
    expect(screen.getByText('query = f"SELECT * FROM t WHERE id={uid}"')).toBeInTheDocument();
    expect(screen.getByText("Use parameterized queries")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Triage label" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to report/ })).toBeInTheDocument();
  });

  it("labels the finding from the action rail", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "SQL Injection" })).toBeInTheDocument()
    );

    await user.click(screen.getByRole("button", { name: "Label as Accept" }));
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("scan-1", "f-1", "accepted");
  });

  it("shows the 404 empty state when the finding is absent", async () => {
    const user = userEvent.setup();
    reportsAPI.getReport.mockResolvedValue({
      ...REPORT,
      scan_results: [{ scanner: "semgrep", status: "completed", findings: [] }],
    });
    renderPage();

    await waitFor(() => expect(screen.getByText("Finding not found")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Back to report" }));
    expect(screen.getByText("report page")).toBeInTheDocument();
  });

  it("mounts the investigate panel on the action rail", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "Investigate" })).toBeInTheDocument();
    expect(screen.getByLabelText("Investigation question")).toBeInTheDocument();
  });

  it("shows the disabled explanation when the investigate flag is off", async () => {
    getAIFeatures.mockResolvedValue({ investigate_agent_enabled: false });
    renderPage();

    expect(await screen.findByText("Investigate agent disabled")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Investigate" })).toBeDisabled();
  });

  it("resets the investigate panel when navigating to another finding", async () => {
    const user = userEvent.setup();
    reportsAPI.getReport.mockResolvedValue({
      ...REPORT,
      scan_results: [
        {
          scanner: "semgrep",
          status: "completed",
          findings: [
            REPORT.scan_results[0].findings[0],
            {
              ...REPORT.scan_results[0].findings[0],
              id: "f-2",
              title: "Reflected XSS",
              severity: "medium",
            },
          ],
        },
      ],
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/report/r1/finding/f-1"]}>
          <Link to="/report/r1/finding/f-2">next finding</Link>
          <Routes>
            <Route path="/report/:reportId/finding/:findingId" element={<FindingDetail />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "SQL Injection" })).toBeInTheDocument()
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "Investigate" })).toBeEnabled());

    await user.type(screen.getByLabelText("Investigation question"), "why?");
    await user.click(screen.getByRole("button", { name: "Investigate" }));
    expect(await screen.findByText("Blast radius")).toBeInTheDocument();
    expect(runInvestigate).toHaveBeenCalledTimes(1);
    expect(runInvestigate).toHaveBeenCalledWith({
      scanId: "scan-1",
      findingId: "f-1",
      question: "why?",
    });

    await user.click(screen.getByRole("link", { name: "next finding" }));

    expect(await screen.findByRole("heading", { name: "Reflected XSS" })).toBeInTheDocument();
    expect(runInvestigate).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText("Investigation question")).toHaveValue("");
    expect(screen.queryByText("Blast radius")).toBeNull();
  });
});
