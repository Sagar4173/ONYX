import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { labelsAPI } from "../services/api";
import { useLabelFinding } from "./useLabelFinding";

vi.mock("../services/api", () => ({
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

const REPORT = {
  scan_id: "s1",
  scan_results: [
    {
      findings: [
        { id: "f1", triage_label: null },
        { id: "f2", triage_label: "accepted" },
      ],
    },
  ],
};

const TRIAGE_KEY = ["triage", "s1", { asset_criticality: "medium" }];

const TRIAGE = {
  ranked_findings: [{ finding_id: "f1", triage_label: null, composite_score: 70 }],
};

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  queryClient.setQueryData(["report", "r1"], REPORT);
  queryClient.setQueryData(TRIAGE_KEY, TRIAGE);
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const hook = renderHook(() => useLabelFinding({ reportId: "r1", scanId: "s1" }), {
    wrapper,
  });
  return { queryClient, hook };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("useLabelFinding", () => {
  it("applies the label optimistically to both caches, then settles", async () => {
    let resolveMutation;
    labelsAPI.setFindingLabel.mockReturnValue(
      new Promise((resolve) => {
        resolveMutation = resolve;
      })
    );
    const { queryClient, hook } = setup();

    hook.result.current.labelFinding({ findingId: "f1", label: "accepted" });

    await waitFor(() =>
      expect(
        queryClient.getQueryData(["report", "r1"]).scan_results[0].findings[0].triage_label
      ).toBe("accepted")
    );
    expect(queryClient.getQueryData(TRIAGE_KEY).ranked_findings[0].triage_label).toBe("accepted");
    expect(hook.result.current.isPending).toBe(true);

    resolveMutation({ scan_id: "s1", finding_id: "f1", triage_label: "accepted" });
    await waitFor(() => expect(hook.result.current.isPending).toBe(false));
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f1", "accepted");
    expect(toast.success).toHaveBeenCalledWith("Your label: Accepted");
  });

  it("rolls both caches back and toasts on failure", async () => {
    labelsAPI.setFindingLabel.mockRejectedValue(new Error("500"));
    const { queryClient, hook } = setup();

    hook.result.current.labelFinding({ findingId: "f1", label: "dismissed" });

    await waitFor(() => expect(toast.error).toHaveBeenCalled());
    const reportNow = queryClient.getQueryData(["report", "r1"]);
    expect(reportNow.scan_results[0].findings[0].triage_label).toBeNull();
    expect(queryClient.getQueryData(TRIAGE_KEY).ranked_findings[0].triage_label).toBeNull();
    expect(toast.error).toHaveBeenCalledWith("Couldn't save your label — change reverted");
  });

  it("clears optimistically with untriaged and invalidates both keys", async () => {
    let resolveMutation;
    labelsAPI.setFindingLabel.mockReturnValue(
      new Promise((resolve) => {
        resolveMutation = resolve;
      })
    );
    const { queryClient, hook } = setup();

    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    hook.result.current.labelFinding({ findingId: "f2", label: "untriaged" });

    await waitFor(() =>
      expect(
        queryClient.getQueryData(["report", "r1"]).scan_results[0].findings[1].triage_label
      ).toBeNull()
    );
    expect(hook.result.current.isPending).toBe(true);

    resolveMutation({ scan_id: "s1", finding_id: "f2", triage_label: null });
    await waitFor(() => expect(hook.result.current.isPending).toBe(false));
    expect(labelsAPI.setFindingLabel).toHaveBeenCalledWith("s1", "f2", "untriaged");
    expect(toast.success).toHaveBeenCalledWith("Label cleared (untriaged)");
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["report", "r1"] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["triage", "s1"] });
  });
});
