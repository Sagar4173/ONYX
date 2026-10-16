import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

vi.mock("@services/aiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, streamChat: vi.fn() };
});

const { streamChat, AIStreamError } = await import("@services/aiClient");
import { useSSEStream } from "./useSSEStream";

describe("useSSEStream", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("walks idle → connecting → streaming → done and forwards events", async () => {
    const statuses = [];
    streamChat.mockImplementation(async ({ onEvent }) => {
      statuses.push("during-send");
      onEvent({ type: "delta", text: "a" });
      onEvent({ type: "done", reply: "a", citations: [], model_used: "m" });
    });
    const { result } = renderHook(() => useSSEStream());
    expect(result.current.status).toBe("idle");

    const seen = [];
    let outcome;
    await act(async () => {
      outcome = await result.current.send({
        scanId: "s",
        message: "x",
        history: [],
        onEvent: (e) => seen.push(e.type),
      });
    });

    expect(result.current.status).toBe("done");
    expect(outcome).toEqual({ status: "done", error: null });
    expect(seen).toEqual(["delta", "done"]);
  });

  it("sets rate_limited with retryAfter on 429", async () => {
    const err = new AIStreamError("Rate limit exceeded.", {
      status: 429,
      kind: "rate_limited",
      retryAfter: 30,
    });
    streamChat.mockRejectedValue(err);
    const { result } = renderHook(() => useSSEStream());
    let outcome;
    await act(async () => {
      outcome = await result.current.send({
        scanId: "s",
        message: "x",
        history: [],
        onEvent: () => {},
      });
    });
    expect(outcome.status).toBe("rate_limited");
    expect(outcome.error.retryAfter).toBe(30);
    expect(result.current.status).toBe("rate_limited");
  });

  it("sets error state on other failures", async () => {
    streamChat.mockRejectedValue(new AIStreamError("boom", { kind: "server" }));
    const { result } = renderHook(() => useSSEStream());
    let outcome;
    await act(async () => {
      outcome = await result.current.send({
        scanId: "s",
        message: "x",
        history: [],
        onEvent: () => {},
      });
    });
    expect(outcome.status).toBe("error");
    expect(result.current.status).toBe("error");
    expect(result.current.error.message).toBe("boom");
  });

  it("abort() resolves outcome aborted and lands on done", async () => {
    let rejectStream;
    streamChat.mockImplementation(
      ({ signal }) =>
        new Promise((resolve, reject) => {
          rejectStream = reject;
          signal.addEventListener("abort", () => {
            const e = new Error("aborted");
            e.name = "AbortError";
            reject(e);
          });
        })
    );
    const { result } = renderHook(() => useSSEStream());
    let outcome;
    await act(async () => {
      const p = result.current.send({ scanId: "s", message: "x", history: [], onEvent: () => {} });
      result.current.abort();
      outcome = await p;
    });
    expect(outcome).toEqual({ status: "aborted", error: null });
    expect(result.current.status).toBe("done");
    expect(rejectStream).toBeDefined();
  });

  it("overlapping send aborts the first stream and a stale settle cannot overwrite the second's state", async () => {
    const first = { signal: null, reject: null };
    let resolveSecond;
    let calls = 0;
    streamChat.mockImplementation(({ signal }) => {
      calls += 1;
      if (calls === 1) {
        first.signal = signal;
        return new Promise((_, reject) => {
          first.reject = reject;
        });
      }
      return new Promise((resolve) => {
        resolveSecond = resolve;
      });
    });
    const { result } = renderHook(() => useSSEStream());

    let firstOutcome;
    await act(async () => {
      firstOutcome = result.current.send({
        scanId: "s",
        message: "a",
        history: [],
        onEvent: () => {},
      });
    });
    expect(first.signal.aborted).toBe(false);

    let secondOutcome;
    await act(async () => {
      secondOutcome = result.current.send({
        scanId: "s",
        message: "b",
        history: [],
        onEvent: () => {},
      });
    });
    expect(first.signal.aborted).toBe(true);

    await act(async () => {
      resolveSecond();
      secondOutcome = await secondOutcome;
    });
    expect(secondOutcome).toEqual({ status: "done", error: null });
    expect(result.current.status).toBe("done");

    await act(async () => {
      first.reject(new AIStreamError("late failure", { kind: "server" }));
      firstOutcome = await firstOutcome;
    });
    expect(firstOutcome).toEqual({ status: "error", error: expect.any(Error) });
    expect(result.current.status).toBe("done");
    expect(result.current.error).toBeNull();
  });

  it("aborts the in-flight request when the hook unmounts", async () => {
    let capturedSignal;
    streamChat.mockImplementation(
      ({ signal }) =>
        new Promise((_, reject) => {
          capturedSignal = signal;
          signal.addEventListener("abort", () => {
            const e = new Error("aborted");
            e.name = "AbortError";
            reject(e);
          });
        })
    );
    const { result, unmount } = renderHook(() => useSSEStream());
    await act(async () => {
      result.current.send({ scanId: "s", message: "x", history: [], onEvent: () => {} });
    });
    expect(capturedSignal).toBeDefined();
    expect(capturedSignal.aborted).toBe(false);

    unmount();
    expect(capturedSignal.aborted).toBe(true);
    await act(async () => {});
  });
});
