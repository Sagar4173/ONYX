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
});
