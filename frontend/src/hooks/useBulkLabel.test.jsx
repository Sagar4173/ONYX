import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { labelsAPI } from "../services/api";
import { useBulkLabel } from "./useBulkLabel";

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

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  queryClient.setQueryData(["report", "r1"], REPORT);
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const hook = renderHook(() => useBulkLabel({ reportId: "r1", scanId: "s1" }), {
    wrapper,
  });
  return { queryClient, hook };
}

beforeEach(() => {
  vi.clearAllMocks();
  labelsAPI.setFindingLabel.mockResolvedValue({ triage_label: "dismissed" });
});

describe("useBulkLabel", () => {
  it("applies sequentially and shows a 5s undo toast that restores prior labels", async () => {
    const { hook } = setup();

    await act(async () => {
      await hook.result.current.applyLabels(["f1", "f2"], "dismissed");
    });

    expect(labelsAPI.setFindingLabel.mock.calls).toEqual([
      ["s1", "f1", "dismissed"],
      ["s1", "f2", "dismissed"],
    ]);
    expect(toast).toHaveBeenCalledWith(expect.any(Function), { duration: 5000 });

    const undoToast = toast.mock.calls[0][0];
    const view = undoToast({ id: "t1" });
    await act(async () => {
      await view.props.children[1].props.onClick();
    });

    expect(toast.dismiss).toHaveBeenCalledWith("t1");
    const restoreCalls = labelsAPI.setFindingLabel.mock.calls.slice(2);
    expect(restoreCalls).toEqual([
      ["s1", "f1", null],
      ["s1", "f2", "accepted"],
    ]);
    expect(toast.success).toHaveBeenCalledWith("Change undone");
  });

  it("reports partial apply and still offers undo", async () => {
    const { hook } = setup();
    labelsAPI.setFindingLabel
      .mockResolvedValueOnce({ triage_label: "dismissed" })
      .mockRejectedValueOnce(new Error("500"));

    await act(async () => {
      await hook.result.current.applyLabels(["f1", "f2"], "dismissed");
    });

    expect(toast.error).toHaveBeenCalledWith("1/2 labels saved");
    expect(toast).toHaveBeenCalledWith(expect.any(Function), { duration: 5000 });
  });

  it("reports N/M restored when an undo write fails", async () => {
    const { hook } = setup();
    labelsAPI.setFindingLabel.mockResolvedValueOnce({ triage_label: "dismissed" });

    await act(async () => {
      await hook.result.current.applyLabels(["f1", "f2"], "dismissed");
    });
    const undoToast = toast.mock.calls[0][0];
    labelsAPI.setFindingLabel
      .mockRejectedValueOnce(new Error("500"))
      .mockResolvedValueOnce({ triage_label: "accepted" });

    await act(async () => {
      await undoToast({ id: "t1" }).props.children[1].props.onClick();
    });

    expect(toast.error).toHaveBeenCalledWith("1/2 restored");
  });

  it("errors without an undo toast when everything fails", async () => {
    const { hook } = setup();
    labelsAPI.setFindingLabel.mockRejectedValue(new Error("500"));

    await act(async () => {
      await hook.result.current.applyLabels(["f1", "f2"], "accepted");
    });

    expect(toast.error).toHaveBeenCalledWith("Couldn't label 2 findings");
    expect(toast).not.toHaveBeenCalled();
  });
});
