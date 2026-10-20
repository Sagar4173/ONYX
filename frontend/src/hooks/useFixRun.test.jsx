import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../services/aiClient", () => ({
  autoFixPropose: vi.fn(),
  autoFixApprove: vi.fn(),
  autoFixGetState: vi.fn(),
  autoFixDiscard: vi.fn(),
}));
vi.mock("react-hot-toast", () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

import {
  autoFixPropose,
  autoFixApprove,
  autoFixGetState,
  autoFixDiscard,
} from "../services/aiClient";
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
  autoFixGetState.mockResolvedValue({ status: "none", finding_id: "f-1" });
});

describe("classifyFixError", () => {
  it("maps network, 404, race, and generic 400s", () => {
    expect(classifyFixError(new Error("boom")).kind).toBe("network");
    expect(classifyFixError(axiosError(404, "Report not found")).kind).toBe("not_found");
    expect(classifyFixError(axiosError(400, "No pending fix for finding f-1")).kind).toBe("race");
    expect(classifyFixError(axiosError(409, "Already approved")).kind).toBe("race");
    expect(
      classifyFixError(
        axiosError(409, "Approval already in progress for this fix — try again shortly")
      ).kind
    ).toBe("race");
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
  it("hydrates a no-state finding from the server on mount", async () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    await waitFor(() =>
      expect(autoFixGetState).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1" })
    );
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

  it("preserves the reviewed diff when the approve response omits it", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixApprove.mockResolvedValue({
      status: "verified",
      finding_id: "f-1",
      file_path: "src/app.py",
      pr_url: "https://x/pull/1",
      pr_number: 1,
      verification: { verified: true, remaining: [], total_findings: 1 },
    });
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.approve({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run?.status).toBe("verified"));
    expect(result.current.run.diff).toBe(AWAITING.diff);
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

  it("keys the state read by filePath", async () => {
    const { wrapper } = makeWrapper();
    const first = renderHook(
      ({ filePath }) => useFixRun({ scanId: "s1", findingId: "f-1", filePath }),
      { wrapper, initialProps: { filePath: "app/run.py" } }
    );

    await waitFor(() =>
      expect(autoFixGetState).toHaveBeenCalledWith({
        scanId: "s1",
        findingId: "f-1",
        filePath: "app/run.py",
      })
    );
    await waitFor(() => expect(first.result.current.run).toBeNull());
    first.unmount();
    autoFixGetState.mockClear();

    const second = renderHook(
      ({ filePath }) => useFixRun({ scanId: "s1", findingId: "f-1", filePath }),
      { wrapper, initialProps: { filePath: "app/run.py" } }
    );
    expect(autoFixGetState).not.toHaveBeenCalled();

    second.rerender({ filePath: "app/other.py" });
    await waitFor(() =>
      expect(autoFixGetState).toHaveBeenCalledWith({
        scanId: "s1",
        findingId: "f-1",
        filePath: "app/other.py",
      })
    );
    expect(autoFixGetState).toHaveBeenCalledTimes(1);
  });

  it("writes mutation results to the key pinned at mutation start", async () => {
    let resolvePropose;
    autoFixPropose.mockImplementation(
      () =>
        new Promise((r) => {
          resolvePropose = r;
        })
    );
    const { client, wrapper } = makeWrapper();
    const { result, rerender } = renderHook(
      ({ findingId, filePath }) => useFixRun({ scanId: "s1", findingId, filePath }),
      { wrapper, initialProps: { findingId: "f-1", filePath: "app/run.py" } }
    );

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.isProposing).toBe(true));

    rerender({ findingId: "f-2", filePath: "app/other.py" });
    await waitFor(() =>
      expect(client.getQueryState(["fix-run", "s1", "f-2", "app/other.py"])?.status).toBe("success")
    );

    await act(async () => resolvePropose({ ...AWAITING, finding_id: "f-1" }));
    await waitFor(() =>
      expect(client.getQueryData(["fix-run", "s1", "f-1", "app/run.py"])?.run?.status).toBe(
        "awaiting_approval"
      )
    );
    expect(client.getQueryData(["fix-run", "s1", "f-2", "app/other.py"])?.run ?? null).toBeNull();
  });

  it("writes mutation results to the filePath-scoped cache key", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    const { client, wrapper } = makeWrapper();
    const { result } = renderHook(
      () => useFixRun({ scanId: "s1", findingId: "f-1", filePath: "app/run.py" }),
      { wrapper }
    );

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());

    expect(client.getQueryData(["fix-run", "s1", "f-1", "app/run.py"])?.run?.status).toBe(
      "awaiting_approval"
    );
    expect(client.getQueryData(["fix-run", "s1", "f-1", null])).toBeUndefined();
  });

  it("discards a pending proposal server-side on reject", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixDiscard.mockResolvedValue({ status: "discarded" });
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.reject());
    await waitFor(() => expect(result.current.run).toBeNull());
    expect(autoFixDiscard).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1" });
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
    autoFixGetState.mockClear();
    autoFixPropose.mockClear();

    const second = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });
    expect(second.result.current.run?.status).toBe("awaiting_approval");
    expect(autoFixPropose).not.toHaveBeenCalled();
    expect(autoFixGetState).not.toHaveBeenCalled();
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

  it("hydrates a pending proposal from the server on mount", async () => {
    autoFixGetState.mockResolvedValue({
      status: "awaiting_approval",
      finding_id: "f-1",
      file_path: "src/app.py",
      diff: "@@ -1,1 +1,1 @@\n-a\n+b",
      model_used: "groq/openai/gpt-oss-120b",
      created_at: "2026-10-19T00:00:00Z",
    });
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    await waitFor(() => expect(result.current.run?.status).toBe("awaiting_approval"));
    expect(result.current.run.diff).toContain("+b");
    expect(result.current.run.model_used).toBe("groq/openai/gpt-oss-120b");
    expect(result.current.history).toEqual([]);
    expect(autoFixPropose).not.toHaveBeenCalled();
    expect(autoFixApprove).not.toHaveBeenCalled();
  });

  it("hydrates an opened PR without diff or session history", async () => {
    autoFixGetState.mockResolvedValue({
      status: "verified",
      finding_id: "f-1",
      file_path: "src/app.py",
      pr_url: "https://x/pull/1",
    });
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    await waitFor(() => expect(result.current.run?.status).toBe("verified"));
    expect(result.current.run.pr_url).toBe("https://x/pull/1");
    expect(result.current.run.diff).toBe("");
    expect(result.current.history).toEqual([]);
  });

  it("fails soft when the state read fails", async () => {
    autoFixGetState.mockRejectedValue(axiosError(502, "Auto-fix failed"));
    const { client, wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    await waitFor(() =>
      expect(client.getQueryState(["fix-run", "s1", "f-1", null])?.status).toBe("success")
    );
    expect(result.current.run).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("distinguishes a discard conflict and preserves the run", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixDiscard.mockRejectedValue(
      axiosError(409, "Approval already in progress for this fix — try again shortly")
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.reject());
    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Approval already in progress — try again shortly")
    );
    expect(result.current.run?.status).toBe("awaiting_approval");
  });

  it("keeps the run and warns when discard fails", async () => {
    autoFixPropose.mockResolvedValue(AWAITING);
    autoFixDiscard.mockRejectedValue(axiosError(502, "boom"));
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFixRun({ scanId: "s1", findingId: "f-1" }), { wrapper });

    act(() => result.current.propose({ scanId: "s1", findingId: "f-1" }));
    await waitFor(() => expect(result.current.run).not.toBeNull());
    act(() => result.current.reject());
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Could not discard the proposal"));
    expect(result.current.run?.status).toBe("awaiting_approval");
    expect(result.current.error).toBeNull();
  });
});
