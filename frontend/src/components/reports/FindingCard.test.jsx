import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { labelsAPI } from "../../services/api";
import FindingCard from "./FindingCard";

vi.mock("../../services/api", () => ({
  labelsAPI: { setFindingLabel: vi.fn() },
}));

vi.mock("react-hot-toast", () => {
  const toastMock = Object.assign(vi.fn(), { success: vi.fn(), error: vi.fn() });
  return { default: toastMock };
});

const FINDING = {
  id: "f-1",
  severity: "high",
  scanner: "semgrep",
  title: "SQL Injection",
  description: "User input flows into query",
  file_path: "app.py",
  line_number: 12,
  remediation: "Use parameterized queries",
  triage_label: null,
};

function renderCard(props = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <FindingCard finding={FINDING} index={0} reportId="r1" scanId="s1" {...props} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  labelsAPI.setFindingLabel.mockResolvedValue({ triage_label: "accepted" });
});

describe("FindingCard", () => {
  it("deep-links the title to the finding route", () => {
    renderCard();
    expect(screen.getByRole("link", { name: "SQL Injection" })).toHaveAttribute(
      "href",
      "/report/r1/finding/f-1"
    );
    expect(screen.getByText("app.py")).toBeInTheDocument();
  });

  it("labels compactly via the inline controls", async () => {
    const user = userEvent.setup();
    renderCard();
    await user.click(screen.getByRole("button", { name: "Label as Accept" }));
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f-1", "accepted");
  });

  it("renders secret heuristic chips from the shared component", () => {
    renderCard({
      finding: {
        ...FINDING,
        scanner: "gitleaks",
        title: "Secret key leaked",
        metadata: { is_likely_real: false, is_placeholder: true },
      },
    });
    expect(screen.getByText("Placeholder Credential")).toBeInTheDocument();
  });

  it("marks the focused card and reports selection", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const { container } = renderCard({ focused: true, onSelect });
    expect(container.querySelector("[data-finding-card]")).toHaveClass("ring-1");
    await user.click(screen.getByRole("heading", { name: /SQL Injection/ }));
    expect(onSelect).toHaveBeenCalled();
  });
});
