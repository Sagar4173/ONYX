import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { reportsAPI, labelsAPI } from "../../services/api";
import ReportDetails from "./ReportDetails";

vi.mock("../../services/api", () => ({
  reportsAPI: { getReport: vi.fn() },
  labelsAPI: { setFindingLabel: vi.fn() },
  triageAPI: { getTriage: vi.fn(), rescoreTriage: vi.fn() },
  enterpriseAPI: {},
  utils: { formatDate: (d) => String(d ?? ""), getStatusColor: () => "text-gray-400" },
  API_BASE_URL: "",
  websocketService: { connect: vi.fn(), disconnect: vi.fn() },
}));

vi.mock("react-hot-toast", () => {
  const toastMock = Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  });
  return { default: toastMock };
});

vi.mock("../../layouts", () => ({
  PageContainer: ({ children }) => <div>{children}</div>,
  PageHeader: ({ children }) => <div>{children}</div>,
  LoadingState: () => <div>loading</div>,
  ErrorState: ({ message }) => <div>{message}</div>,
}));

vi.mock("../../components/projects/ParticleBackground", () => ({ default: () => null }));
vi.mock("../../components/reports/ComplianceMapping", () => ({ ComplianceMapping: () => null }));
vi.mock("../../components/reports/ReportCharts", () => ({ ReportCharts: () => null }));
vi.mock("../../components/reports/ReportExport", () => ({ ExportDropdown: () => null }));
vi.mock("../../components/reports/ReportBadges", () => ({
  SeverityBadge: ({ severity }) => <span>{severity}</span>,
  StatusBadge: ({ status }) => <span>{status}</span>,
}));
vi.mock("../../components/reports/SecretDetectionSummary", () => ({ default: () => null }));
vi.mock("../../components/reports/ScannerResultCard", () => ({ default: () => null }));
vi.mock("../../components/security/ScanComparison", () => ({ default: () => null }));
vi.mock("../../components/reports/TriageDashboard", () => ({ default: () => null }));
vi.mock("../../components/reports/AISection", () => ({ default: () => null }));
vi.mock("../../components/reports/AIChatPanel", () => ({ default: () => null }));
vi.mock("../../utils/pdfReportGenerator", () => ({
  generateViewPDF: vi.fn(),
  generatePdfReport: vi.fn(),
}));

const FINDING = (id, title) => ({
  id,
  severity: "high",
  scanner: "semgrep",
  title,
  description: "desc",
  file_path: `${title}.py`,
  line_number: 1,
  remediation: "fix it",
  triage_label: null,
});

const REPORT = {
  scan_id: "s1",
  status: "completed",
  project_name: "demo",
  created_at: "2026-10-17T00:00:00Z",
  scan_results: [
    {
      scanner: "semgrep",
      status: "completed",
      findings: [FINDING("f-1", "SQL Injection"), FINDING("f-2", "Weak hash")],
    },
  ],
};

function renderReport() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/report/r1"]}>
        <Routes>
          <Route path="/report/:reportId" element={<ReportDetails />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  reportsAPI.getReport.mockResolvedValue(REPORT);
  labelsAPI.setFindingLabel.mockResolvedValue({ triage_label: "accepted" });
});

async function openFindingsTab(user) {
  renderReport();
  await waitFor(() => expect(reportsAPI.getReport).toHaveBeenCalled());
  await user.click(screen.getByRole("button", { name: /findings/i }));
  await waitFor(() => expect(screen.getByText("SQL Injection")).toBeInTheDocument());
}

describe("ReportDetails findings keyboard", () => {
  it("deep-links titles and shows the hint strip", async () => {
    const user = userEvent.setup();
    await openFindingsTab(user);
    expect(screen.getByRole("link", { name: "SQL Injection" })).toHaveAttribute(
      "href",
      "/report/r1/finding/f-1"
    );
    expect(
      screen.getByText(
        /J\/K move · A accept · F false positive · D dismiss · U untriage · \? shortcuts/i
      )
    ).toBeInTheDocument();
  });

  it("refuses to label with no focus, then labels after J", async () => {
    const user = userEvent.setup();
    await openFindingsTab(user);

    fireEvent.keyDown(document, { key: "a" });
    expect(toast.error).toHaveBeenCalledWith("No finding focused — press J first");
    expect(labelsAPI.setFindingLabel).not.toHaveBeenCalled();

    fireEvent.keyDown(document, { key: "j" });
    fireEvent.keyDown(document, { key: "a" });
    await waitFor(() =>
      expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f-1", "accepted")
    );
  });

  it("opens the shortcut overlay on ?", async () => {
    const user = userEvent.setup();
    await openFindingsTab(user);
    fireEvent.keyDown(document, { key: "?" });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Triage shortcuts")).toBeInTheDocument();
  });
});
