import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import ScanComparison from "./ScanComparison";

vi.mock("@services/api", () => ({
  enterpriseAPI: {
    compareScans: vi.fn(),
  },
  reportsAPI: {
    getReports: vi.fn(),
    getProjectReports: vi.fn(),
  },
}));

const { enterpriseAPI, reportsAPI } = await import("@services/api");

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithClient(ui) {
  const queryClient = createQueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const mockComparisonData = {
  data: {
    summary: {
      fixed: 3,
      new: 2,
      reintroduced: 1,
      modified: 1,
      net_change: -1,
      improvement_score: 15.5,
    },
    base_scan: {
      timestamp: "2025-01-01T00:00:00Z",
      branch: "main",
      total_findings: 10,
    },
    compare_scan: {
      timestamp: "2025-01-15T00:00:00Z",
      branch: "main",
      total_findings: 7,
    },
    analysis: {
      summary: "Overall security improved",
      highlights: ["3 critical issues fixed"],
      recommendations: ["Continue monitoring"],
    },
    details: {
      fixed: [
        {
          finding: {
            id: "f-1",
            title: "SQL Injection",
            severity: "critical",
            scanner: "semgrep",
            file_path: "app.py",
            rule_id: "sql.001",
            line: 42,
          },
        },
        {
          finding: {
            id: "f-2",
            title: "Hardcoded Secret",
            severity: "high",
            scanner: "gitleaks",
            file_path: "config.py",
            rule_id: "secret.001",
            line: 10,
          },
        },
        {
          finding: {
            id: "f-3",
            title: "XSS Vulnerability",
            severity: "medium",
            scanner: "semgrep",
            file_path: "templates/index.html",
            rule_id: "xss.001",
            line: 25,
          },
        },
      ],
      new: [
        {
          finding: {
            id: "f-4",
            title: "CSRF Token Missing",
            severity: "high",
            scanner: "bandit",
            file_path: "views.py",
            rule_id: "csrf.001",
            line: 15,
          },
        },
        {
          finding: {
            id: "f-5",
            title: "Unvalidated Redirect",
            severity: "low",
            scanner: "semgrep",
            file_path: "utils.py",
            rule_id: "redirect.001",
            line: 88,
          },
        },
      ],
      reintroduced: [
        {
          finding: {
            id: "f-6",
            title: "Command Injection",
            severity: "critical",
            scanner: "semgrep",
            file_path: "cli.py",
            rule_id: "cmd.001",
            line: 33,
          },
        },
      ],
      modified: [
        {
          finding: {
            id: "f-7",
            title: "Deprecated API Usage",
            severity: "medium",
            scanner: "bandit",
            file_path: "api.py",
            rule_id: "dep.001",
            line: 55,
            severity_change: { from: "low", to: "medium" },
          },
        },
      ],
    },
  },
};

const mockScansData = {
  reports: [
    {
      id: "scan-001",
      created_at: "2025-01-01T00:00:00Z",
      branch: "main",
      total_findings: 10,
      status: "completed",
      scan_type: "full",
    },
    {
      id: "scan-002",
      created_at: "2025-01-15T00:00:00Z",
      branch: "main",
      total_findings: 7,
      status: "completed",
      scan_type: "full",
    },
  ],
};

const emptyComparisonData = {
  data: {
    summary: { fixed: 0, new: 0, reintroduced: 0, modified: 0, net_change: 0, improvement_score: 0 },
    base_scan: { timestamp: "2025-01-01T00:00:00Z", branch: "main", total_findings: 0 },
    compare_scan: { timestamp: "2025-01-15T00:00:00Z", branch: "main", total_findings: 0 },
    details: { fixed: [], new: [], reintroduced: [], modified: [] },
  },
};

describe("ScanComparison", () => {
  beforeEach(() => {
    enterpriseAPI.compareScans.mockReset();
    reportsAPI.getReports.mockReset();
    reportsAPI.getProjectReports.mockReset();
  });

  it("renders initial state with scan selectors", async () => {
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison />);

    expect(screen.getByText("Scan Comparison")).toBeInTheDocument();
    expect(screen.getByText("Compare security scans to track remediation progress")).toBeInTheDocument();
    expect(screen.getByText("Base Scan (Older)")).toBeInTheDocument();
    expect(screen.getByText("Compare Scan (Newer)")).toBeInTheDocument();
    expect(screen.getByText("Select two scans to compare")).toBeInTheDocument();
  });

  it("renders loading state when comparison is in progress", async () => {
    enterpriseAPI.compareScans.mockImplementation(() => new Promise(() => {}));
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    expect(await screen.findByText("Scan Comparison")).toBeInTheDocument();
    const compareBtn = screen.getByText("Compare");
    expect(compareBtn).not.toBeDisabled();
  });

  it("renders error state when comparison fails", async () => {
    const errorMessage = "Failed to fetch comparison";
    enterpriseAPI.compareScans.mockRejectedValue(new Error(errorMessage));
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    expect(await screen.findByText(`Error comparing scans: ${errorMessage}`)).toBeInTheDocument();
  });

  it("renders comparison data with summary cards and findings", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    await waitFor(() => {
      expect(screen.getByText("Vulnerabilities remediated")).toBeInTheDocument();
    });

    const fixedCards = screen.getAllByText("Fixed");
    expect(fixedCards.length).toBeGreaterThanOrEqual(1);

    const threeValues = screen.getAllByText("3");
    expect(threeValues.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("-1")).toBeInTheDocument();
    expect(screen.getByText("15.5")).toBeInTheDocument();
  });

  it("renders analysis insights when provided", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    expect(await screen.findByText("Overall security improved")).toBeInTheDocument();
    expect(screen.getByText("3 critical issues fixed")).toBeInTheDocument();
    expect(screen.getByText("Continue monitoring")).toBeInTheDocument();
  });

  it("renders finding rows for fixed, new, and reintroduced change types", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    expect(await screen.findByText("SQL Injection")).toBeInTheDocument();
    expect(screen.getByText("Hardcoded Secret")).toBeInTheDocument();
    expect(screen.getByText("XSS Vulnerability")).toBeInTheDocument();
    expect(screen.getByText("CSRF Token Missing")).toBeInTheDocument();
    expect(screen.getByText("Unvalidated Redirect")).toBeInTheDocument();
    expect(screen.getByText("Command Injection")).toBeInTheDocument();
    expect(screen.queryByText("Deprecated API Usage")).not.toBeInTheDocument();
  });

  it("renders modified findings when Modified tab is active", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    expect(await screen.findByText("SQL Injection"));

    const modifiedButtons = screen.getAllByText("Modified");
    const modifiedTab = modifiedButtons.find(
      (el) => el.tagName === "BUTTON",
    ) || modifiedButtons[1];
    await userEvent.click(modifiedTab);

    expect(screen.getByText("Deprecated API Usage")).toBeInTheDocument();
    expect(screen.queryByText("SQL Injection")).not.toBeInTheDocument();
  });

  it("filters findings by tab", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    await screen.findByText("SQL Injection");

    const fixedTabButtons = screen.getAllByText("Fixed");
    const fixedTabButton = fixedTabButtons.find(
      (el) => el.tagName === "BUTTON",
    ) || fixedTabButtons[1];
    await userEvent.click(fixedTabButton);

    expect(screen.getByText("SQL Injection")).toBeInTheDocument();
    expect(screen.queryByText("CSRF Token Missing")).not.toBeInTheDocument();
    expect(screen.queryByText("Command Injection")).not.toBeInTheDocument();

    const newTabButtons = screen.getAllByText("New");
    const newTabButton = newTabButtons.find(
      (el) => el.tagName === "BUTTON",
    ) || newTabButtons[1];
    await userEvent.click(newTabButton);

    expect(screen.getByText("CSRF Token Missing")).toBeInTheDocument();
    expect(screen.queryByText("SQL Injection")).not.toBeInTheDocument();
  });

  it("filters findings by severity", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    await screen.findByText("SQL Injection");

    const severitySelect = screen.getByRole("option", { name: "All Severities" }).closest("select");
    await userEvent.selectOptions(severitySelect, "critical");

    expect(screen.getByText("SQL Injection")).toBeInTheDocument();
    expect(screen.getByText("Command Injection")).toBeInTheDocument();
    expect(screen.queryByText("Hardcoded Secret")).not.toBeInTheDocument();
    expect(screen.queryByText("CSRF Token Missing")).not.toBeInTheDocument();
  });

  it("shows empty state when no findings match filters", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(emptyComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    expect(await screen.findByText("No findings match the current filters")).toBeInTheDocument();
  });

  it("renders scan info cards with correct data", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    await screen.findByText("Base Scan");
    expect(screen.getByText("Compare Scan")).toBeInTheDocument();
  });

  it("calls getProjectReports when projectName is provided", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getProjectReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" projectName="test-project" />);

    await screen.findByText("Scan Comparison");

    expect(reportsAPI.getProjectReports).toHaveBeenCalledWith("test-project", {
      limit: 50,
      sort_by: "created_at",
      sort_order: "desc",
    });
  });

  it("calls getReports when projectName is not provided", async () => {
    enterpriseAPI.compareScans.mockResolvedValue(mockComparisonData);
    reportsAPI.getReports.mockResolvedValue(mockScansData);

    renderWithClient(<ScanComparison baseScanId="scan-001" compareScanId="scan-002" />);

    await screen.findByText("Scan Comparison");

    expect(reportsAPI.getReports).toHaveBeenCalledWith({
      limit: 50,
      sort_by: "created_at",
      sort_order: "desc",
    });
  });
});
