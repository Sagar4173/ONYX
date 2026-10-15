import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { streamChat, getAIFeatures, AIStreamError } from "./aiClient";

const encoder = new TextEncoder();

function fakeResponse({ status = 200, headers = {}, frames = [], splitAt = null }) {
  const chunks = frames.map((f) => encoder.encode(`data: ${JSON.stringify(f)}\n\n`));
  if (splitAt !== null && chunks.length > 0) {
    const whole = chunks[0];
    chunks.splice(0, 1, whole.slice(0, splitAt), whole.slice(splitAt));
  }
  let i = 0;
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (name) => headers[name] ?? null },
    json: async () => ({ detail: headers.detail || "" }),
    body: {
      getReader: () => ({
        read: async () =>
          i < chunks.length
            ? { done: false, value: chunks[i++] }
            : { done: true, value: undefined },
        releaseLock: () => {},
      }),
    },
  };
}

describe("streamChat", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("emits delta events then done, in order", async () => {
    const response = fakeResponse({
      frames: [
        { type: "delta", text: "Hel" },
        { type: "delta", text: "lo" },
        { type: "done", reply: "Hello", citations: [], model_used: "m" },
      ],
    });
    const fetchMock = vi.fn().mockResolvedValue(response);
    vi.stubGlobal("fetch", fetchMock);
    const events = [];
    await streamChat({ scanId: "s1", message: "hi", onEvent: (e) => events.push(e) });
    expect(events.map((e) => e.type)).toEqual(["delta", "delta", "done"]);
    expect(events[2].model_used).toBe("m");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/ai/chat/stream");
    expect(JSON.parse(init.body)).toEqual({
      scan_id: "s1",
      message: "hi",
      conversation_history: [],
    });
  });

  it("parses a frame split across two reads", async () => {
    const response = fakeResponse({
      frames: [
        { type: "delta", text: "split-frame" },
        { type: "delta", text: "split-frame" },
        { type: "done", reply: "split-frame", citations: [], model_used: "m" },
      ],
      splitAt: 12,
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    const events = [];
    await streamChat({ scanId: "s", message: "x", onEvent: (e) => events.push(e) });
    expect(events).toHaveLength(3); // 2 deltas (chunk 1 split) + done
    expect(
      events
        .filter((e) => e.type === "delta")
        .map((e) => e.text)
        .join("")
    ).toBe("split-framesplit-frame");
  });

  it("throws AIStreamError rate_limited with retryAfter from Retry-After", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(fakeResponse({ status: 429, headers: { "Retry-After": "42" } }))
    );
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err).toBeInstanceOf(AIStreamError);
    expect(err.kind).toBe("rate_limited");
    expect(err.retryAfter).toBe(42);
  });

  it("throws AIStreamError not_found carrying detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(fakeResponse({ status: 404, headers: { detail: "Scan not found" } }))
    );
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err.kind).toBe("not_found");
    expect(err.message).toBe("Scan not found");
  });

  it("throws AIStreamError server on SSE error frame after emitting deltas", async () => {
    const response = fakeResponse({
      frames: [
        { type: "delta", text: "partial" },
        { type: "error", detail: "AI provider error mid-stream." },
      ],
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    const events = [];
    const err = await streamChat({
      scanId: "s",
      message: "x",
      onEvent: (e) => events.push(e),
    }).catch((e) => e);
    expect(events).toEqual([{ type: "delta", text: "partial" }]);
    expect(err).toBeInstanceOf(AIStreamError);
    expect(err.kind).toBe("server");
    expect(err.message).toBe("AI provider error mid-stream.");
  });

  it("throws AIStreamError stream when connection ends without done", async () => {
    const response = fakeResponse({ frames: [{ type: "delta", text: "lost" }] });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err.kind).toBe("stream");
  });

  it("passes AbortError through untouched", async () => {
    const abortError = new Error("aborted");
    abortError.name = "AbortError";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(abortError));
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err.name).toBe("AbortError");
  });

  it("slices conversation history to 20", async () => {
    const response = fakeResponse({
      frames: [{ type: "done", reply: "r", citations: [], model_used: "m" }],
    });
    const fetchMock = vi.fn().mockResolvedValue(response);
    vi.stubGlobal("fetch", fetchMock);
    const history = Array.from({ length: 30 }, (_, i) => ({ role: "user", content: `m${i}` }));
    await streamChat({
      scanId: "s",
      message: "x",
      conversationHistory: history,
      onEvent: () => {},
    });
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.conversation_history).toHaveLength(20);
    expect(body.conversation_history[0].content).toBe("m10");
  });
});

describe("getAIFeatures", () => {
  it("returns parsed JSON on ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: true, json: async () => ({ investigate_agent_enabled: true }) })
    );
    await expect(getAIFeatures()).resolves.toEqual({ investigate_agent_enabled: true });
  });

  it("throws on !ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));
    await expect(getAIFeatures()).rejects.toThrow("500");
  });
});
