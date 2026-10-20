import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../../services/aiClient", () => ({
  autoFixPropose: vi.fn(),
  autoFixApprove: vi.fn(),
  autoFixGetState: vi.fn(),
  autoFixDiscard: vi.fn(),
  getAIFeatures: vi.fn(),
}));
vi.mock("react-hot-toast", () => ({ default: { success: vi.fn(), error: vi.fn() } }));
vi.mock("react-diff-viewer-continued", () => ({
  default: ({ oldValue, newValue }) => (
    <div data-testid="rdv">
      <pre>{oldValue}</pre>
      <pre>{newValue}</pre>
    </div>
  ),
}));

import {
  autoFixPropose,
  autoFixApprove,
  autoFixGetState,
  autoFixDiscard,
  getAIFeatures,
} from "../../services/aiClient";
import { useFixRun } from "../../hooks/useFixRun";
import { FixTriggerCard } from "./FixTriggerCard";
import { FixReviewSection } from "./FixReviewSection";

const AWAITING = {
  status: "awaiting_approval",
  finding_id: "f-1",
  file_path: "src/app.py",
  diff: "@@ -1,1 +1,1 @@\n-old line\n+new line",
  gate_failures: [],
  model_used: "groq/openai/gpt-oss-120b",
};

function Harness({ findingId = "f-1" }) {
  const fix = useFixRun({ scanId: "s1", findingId });
  return (
    <>
      <FixTriggerCard fix={fix} scanId="s1" findingId={findingId} />
      <FixReviewSection fix={fix} scanId="s1" findingId={findingId} filePath="src/app.py" />
    </>
  );
}

function renderHarness(props) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <Harness {...props} />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  getAIFeatures.mockResolvedValue({ auto_fix_requires_approval: true });
  autoFixGetState.mockResolvedValue({ status: "none", finding_id: "f-1" });
});

describe("fix-PR flow", () => {
  it("is hidden until activity, then proposes and renders the diff", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    renderHarness();

    expect(screen.queryByText("Fix-PR review")).toBeNull();
    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));

    expect(autoFixPropose).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1" });
    await screen.findByText("Fix-PR review");
    expect(screen.getByTestId("rdv").textContent).toContain("new line");
    expect(screen.getByRole("button", { name: /Approve & open PR/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.getByText(/groq\/openai\/gpt-oss-120b/)).toBeInTheDocument();
  });

  it("requires typing APPROVE before approving, then shows the verified badge", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockResolvedValue({
      ...AWAITING,
      status: "verified",
      pr_url: "https://x/pull/9",
      pr_number: 9,
      branch: "onyx-fix/app-py-1",
      verification: { verified: true, remaining: [], total_findings: 1 },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: /Approve & open PR/ }));

    const confirm = await screen.findByRole("button", { name: "Open pull request" });
    expect(confirm).toBeDisabled();
    await user.type(screen.getByRole("textbox"), "APPROVE");
    expect(confirm).toBeEnabled();
    await user.click(confirm);

    expect(autoFixApprove).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1" });
    await screen.findByText(/Verified — re-scan no longer detects/);
    expect(screen.getByRole("link", { name: /PR #9/ })).toHaveAttribute("href", "https://x/pull/9");
  });

  it("renders a race notice with no retry when approve loses the pending claim", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockRejectedValue({
      response: { status: 400, data: { detail: "No pending fix for finding f-1" } },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: /Approve & open PR/ }));
    await user.type(screen.getByRole("textbox"), "APPROVE");
    await user.click(screen.getByRole("button", { name: "Open pull request" }));

    await screen.findByText("Already handled elsewhere");
    expect(screen.queryByRole("button", { name: /Propose again/ })).toBeNull();
  });

  it("shows gate/agent 400s inline with a propose-again retry", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockRejectedValue({
      response: {
        status: 400,
        data: { detail: "Fix agent produced a patch over the 50-line cap" },
      },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await screen.findByText("Auto-fix could not run");
    expect(screen.getByText(/50-line cap/)).toBeInTheDocument();

    autoFixPropose.mockResolvedValue(AWAITING);
    await user.click(screen.getByRole("button", { name: /Propose again/ }));
    await screen.findByText("Fix-PR review");
  });

  it("explains dry-run mode and disables apply", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue({ ...AWAITING, status: "dry_run" });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await screen.findByText(/Dry-run mode/);
    expect(screen.getByRole("button", { name: "Apply fix" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Propose again/ })).toBeEnabled();
  });

  it("not-verified re-scan shows a warning with remaining findings", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockResolvedValue({
      ...AWAITING,
      status: "pr_created",
      pr_url: "https://x/pull/7",
      pr_number: 7,
      verification: { verified: false, remaining: ["B608 at src/app.py"], total_findings: 4 },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: /Approve & open PR/ }));
    await user.type(screen.getByRole("textbox"), "APPROVE");
    await user.click(screen.getByRole("button", { name: "Open pull request" }));

    await screen.findByText("Not verified by re-scan");
    expect(screen.getByText(/B608 at src\/app\.py/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /PR #7/ })).toBeInTheDocument();
  });

  it("keeps the reviewed diff when the approve response omits it", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockResolvedValue({
      status: "pr_created",
      finding_id: "f-1",
      file_path: "src/app.py",
      pr_url: "https://x/pull/8",
      pr_number: 8,
      verification: { verified: true, remaining: [], total_findings: 1 },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: /Approve & open PR/ }));
    await user.type(screen.getByRole("textbox"), "APPROVE");
    await user.click(screen.getByRole("button", { name: "Open pull request" }));

    await screen.findByRole("link", { name: /PR #8/ });
    expect(screen.queryByText("No changes")).toBeNull();
    expect(screen.getByTestId("rdv").textContent).toContain("new line");
  });

  it("omits the diff area entirely when a run carries no diff", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue({
      status: "pr_created",
      finding_id: "f-1",
      file_path: "src/app.py",
      pr_url: "https://x/pull/3",
      pr_number: 3,
      gate_failures: [],
      verification: { verified: true, remaining: [], total_findings: 1 },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));

    await screen.findByRole("link", { name: /PR #3/ });
    expect(screen.queryByText("No changes")).toBeNull();
    expect(screen.queryByTestId("rdv")).toBeNull();
  });

  it("discards server-side after confirmation", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: "Reject" }));
    await user.click(screen.getByRole("button", { name: "Reject proposal" }));

    await waitFor(() => expect(screen.queryByText("Fix-PR review")).toBeNull());
    expect(autoFixDiscard).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1" });
    expect(autoFixApprove).not.toHaveBeenCalled();
  });

  it("disables review actions while approval is in flight", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    let resolveApprove;
    autoFixApprove.mockReturnValue(new Promise((resolve) => (resolveApprove = resolve)));
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: /Approve & open PR/ }));
    await user.type(screen.getByRole("textbox"), "APPROVE");
    await user.click(screen.getByRole("button", { name: "Open pull request" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Reject" })).toBeDisabled();
      expect(screen.getByRole("button", { name: "Approving…" })).toBeDisabled();
      expect(screen.getByRole("button", { name: /Propose again/ })).toBeDisabled();
    });
    expect(screen.queryByRole("button", { name: /Approve & open PR/ })).toBeNull();

    resolveApprove({
      ...AWAITING,
      status: "pr_created",
      pr_url: "https://x/pull/11",
      pr_number: 11,
    });
    await screen.findByRole("link", { name: /PR #11/ });
  });

  it("goes explain-mode when the approval flow is disabled", async () => {
    getAIFeatures.mockResolvedValue({ auto_fix_requires_approval: false });
    renderHarness();
    const button = await screen.findByRole("button", { name: /Propose fix/ });
    await waitFor(() => expect(button).toBeDisabled());
    expect(screen.getByText(/Approval flow disabled/)).toBeInTheDocument();
  });

  it("keeps the diff and shows the stale-base 400 inline with a propose-again path", async () => {
    const user = userEvent.setup();
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockRejectedValue({
      response: {
        status: 400,
        data: { detail: "Base branch advanced since the fix was proposed — re-run auto-fix" },
      },
    });
    renderHarness();

    await user.click(await screen.findByRole("button", { name: /Propose fix/ }));
    await user.click(await screen.findByRole("button", { name: /Approve & open PR/ }));
    await user.type(screen.getByRole("textbox"), "APPROVE");
    await user.click(screen.getByRole("button", { name: "Open pull request" }));

    await screen.findByText("Auto-fix could not run");
    expect(screen.getByRole("alert")).toHaveTextContent("Auto-fix could not run");
    expect(screen.getByText(/re-run auto-fix/)).toBeInTheDocument();
    expect(screen.getByTestId("rdv")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Propose again/ })).toBeInTheDocument();
  });

  it("renders a hydrated pending proposal with review actions and no propose call", async () => {
    autoFixGetState.mockResolvedValue({
      status: "awaiting_approval",
      finding_id: "f-1",
      file_path: "src/app.py",
      diff: "@@ -1,1 +1,1 @@\n-old line\n+new line",
      model_used: "groq/openai/gpt-oss-120b",
      created_at: "2026-10-19T00:00:00Z",
    });
    renderHarness();

    await screen.findByText("Fix-PR review");
    expect(screen.getByTestId("rdv").textContent).toContain("new line");
    expect(screen.getByRole("button", { name: /Approve & open PR/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(autoFixPropose).not.toHaveBeenCalled();
  });

  it("renders a hydrated opened PR without verification details", async () => {
    autoFixGetState.mockResolvedValue({
      status: "verified",
      finding_id: "f-1",
      file_path: "src/app.py",
      pr_url: "https://x/pull/7",
    });
    renderHarness();

    await screen.findByText("Fix-PR review");
    expect(screen.getByRole("link", { name: "View PR" })).toHaveAttribute(
      "href",
      "https://x/pull/7"
    );
    expect(screen.getByText(/re-scan no longer detects/)).toBeInTheDocument();
    expect(screen.queryByText("Verification could not run")).toBeNull();
    expect(autoFixPropose).not.toHaveBeenCalled();
  });
});
