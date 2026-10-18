import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../services/aiClient", () => ({
  autoFixPropose: vi.fn(),
  autoFixApprove: vi.fn(),
}));
vi.mock("react-hot-toast", () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

import { autoFixPropose, autoFixApprove } from "../services/aiClient";
import toast from "react-hot-toast";
import { useFixRun, classifyFixError } from "./useFixRun";

const AWAITING = {
  status: "awaiting_approval",
  finding_id: "f-1",
  file_path: "src/app.py",
  diff: "@@ -1,1 +1,1 @@\n-a\n+b",
};
const VERIFIED = { ...AWAITING, status: "verified", pr_url: "https://x/pull/1", pr_number: 1 };

const axiosError = (status, detail) => ({ response: { status, data: { detail } } });

function makeWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, wrapper };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("classifyFixError", () => {
  it("maps network, 404, race, and generic 400s", () => {
    expect(classifyFixError(new Error("boom")).kind).toBe("network");
    expect(classifyFixError(axiosError(404, "Report not found")).kind).toBe("not_found");
    expect(classifyFixError(axiosError(400, "No pending fix for finding f-1")).kind).toBe("race");
    expect(classifyFixError(axiosError(409, "Already approved")).kind).toBe("race");
    expect(classifyFixError(axiosError(400, "Daily AI quota exhausted")).kind).toBe("rejected");
    expect(classifyFixError(axiosError(502, "Auto-fix failed")).kind).toBe("server");
  });

  it("extracts only status and detail — never the raw error", () => {
    const classified = classifyFixError(axiosError(400, "gate: secret detected"));
    expect(classified).toEqual({ status: 400, detail: "gate: secret detected", kind: "rejected" });
    expect(classified).not.toHaveProperty("config");
  });
});

describe("useFixRun", () => {
  it("stays idle with no calls on mount", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });
    expect(result.current.run).toBeNull();
    expect(result.current.error).toBeNull();
    expect(autoFixPropose).not.toHaveBeenCalled();
  });

  it("proposes, exposes pending scoped to the finding, and toasts the transition", async () => {
    let resolvePropose;
    autoFixPropose.mockImplementation(
      () =>
        new Promise((r) => {
          resolvePropose = r;
        })
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.isProposing).toBe(true));
    expect(autoFixPropose).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1" });

    await act(async () => resolvePropose(AWAITING));
    await waitFor(() => expect(result.current.run?.status).toBe("awaiting_approval"));
    expect(result.current.isProposing).toBe(false);
    expect(result.current.history.at(-1)).toMatchObject({
      action: "propose",
      status: "awaiting_approval",
      ok: true,
    });
    expect(toast.success).toHaveBeenCalledWith("Fix proposed — awaiting your approval");
  });

  it("clears the run and classifies propose errors", async () => {
    autoFixPropose.mockRejectedValue(axiosError(400, "Fix agent failed gate: non-Python file"));
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.run).toBeNull();
    expect(result.current.error).toMatchObject({ status: 400, kind: "rejected" });
  });

  it("approves into verified and toasts", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockResolvedValue(VERIFIED);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.approve({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run?.status).toBe("verified"));
    expect(result.current.history.at(-1)).toMatchObject({ action: "approve", ok: true });
    expect(toast.success).toHaveBeenCalledWith("Fix verified by re-scan");
  });

  it("clears a stale run on an approve race", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockRejectedValue(axiosError(400, "No pending fix for finding f-1"));
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.approve({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.error?.kind).toBe("race"));
    expect(result.current.run).toBeNull();
  });

  it("keeps the run when approve fails transiently (502)", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockRejectedValue(axiosError(502, "Auto-fix failed"));
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.approve({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.error?.kind).toBe("server"));
    expect(result.current.run?.status).toBe("awaiting_approval");
  });

  it("rejects client-side with a toast", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.reject());
    await waitFor(() => expect(result.current.run).toBeNull());
    expect(result.current.history.at(-1)).toMatchObject({ action: "reject", status: "dismissed" });
    expect(toast.success).toHaveBeenCalledWith("Proposal rejected — nothing was applied");
  });

  it("restores cached state on remount without re-proposing", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    const { wrapper } = makeWrapper();
    const first = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });
    act(() => first.result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(first.result.current.run).not.toBeNull());
    first.unmount();
    autoFixPropose.mockClear();

    const second = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });
    expect(second.result.current.run?.status).toBe("awaiting_approval");
    expect(autoFixPropose).not.toHaveBeenCalled();
  });

  it("scopes isProposing to the current finding", async () => {
    let resolvePropose;
    autoFixPropose.mockImplementation(
      () =>
        new Promise((r) => {
          resolvePropose = r;
        })
    );
    const { wrapper } = makeWrapper();
    const { result, rerender } = renderHook(
      ({ findingId }) => useFixRun({ scanId: "s1", findingId }),
      {
        wrapper,
        initialProps: { findingId: "f-1" },
      }
    );

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.isProposing).toBe(true));

    rerender({ findingId: "f-2" });
    expect(result.current.isProposing).toBe(false);
    expect(result.current.run).toBeNull();

    await act(async () => resolvePropose(AWAITING));
  });
});
