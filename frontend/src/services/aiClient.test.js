import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  streamChat,
  getAIFeatures,
  runInvestigate,
  autoFixPropose,
  autoFixApprove,
  AIStreamError,
} from "./aiClient";
import { api } from "./api";

const encoder = new TextEncoder();

function fakeResponse({
  status = 200,
  headers = {},
  frames = [],
  splitAt = null,
  failAfter = null,
  failError = null,
}) {
  const chunks = frames.map((f) => encoder.encode(`data: ${JSON.stringify(f)}\n\n`));
  if (splitAt !== null && chunks.length > 0) {
    const whole = chunks[0];
    chunks.splice(0, 1, whole.slice(0, splitAt), whole.slice(splitAt));
  }
  let i = 0;
  let reads = 0;
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (name) => headers[name] ?? null },
    json: async () => ({ detail: headers.detail || "" }),
    body: {
      getReader: () => ({
        read: async () => {
          if (failAfter !== null && reads >= failAfter) throw failError;
          reads++;
          return i < chunks.length
            ? { done: false, value: chunks[i++] }
            : { done: true, value: undefined };
        },
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

  it("keeps a legitimate Retry-After: 0 as 0 (immediate retry)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(fakeResponse({ status: 429, headers: { "Retry-After": "0" } }))
    );
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err.kind).toBe("rate_limited");
    expect(err.retryAfter).toBe(0);
  });

  it("maps a missing Retry-After header to null (indeterminate quota)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(fakeResponse({ status: 429 })));
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err.kind).toBe("rate_limited");
    expect(err.retryAfter).toBeNull();
  });

  it("clamps a negative Retry-After to 0", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(fakeResponse({ status: 429, headers: { "Retry-After": "-5" } }))
    );
    const err = await streamChat({ scanId: "s", message: "x", onEvent: () => {} }).catch((e) => e);
    expect(err.kind).toBe("rate_limited");
    expect(err.retryAfter).toBe(0);
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

  it("types mid-stream reader.read() failure as AIStreamError network", async () => {
    const readError = new TypeError("network stream closed");
    const response = fakeResponse({
      frames: [{ type: "delta", text: "partial" }],
      failAfter: 1,
      failError: readError,
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
    expect(err.name).toBe("AIStreamError");
    expect(err.kind).toBe("network");
    expect(err.status).toBe(0);
  });

  it("passes mid-read AbortError through untouched", async () => {
    const abortError = new Error("aborted mid-read");
    abortError.name = "AbortError";
    const response = fakeResponse({
      frames: [{ type: "delta", text: "partial" }],
      failAfter: 1,
      failError: abortError,
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    const events = [];
    const err = await streamChat({
      scanId: "s",
      message: "x",
      onEvent: (e) => events.push(e),
    }).catch((e) => e);
    expect(events).toEqual([{ type: "delta", text: "partial" }]);
    expect(err).toBe(abortError);
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

describe("runInvestigate", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts the investigate payload and returns the envelope", async () => {
    const envelope = {
      report: { finding_id: "f-1", summary: "blast", evidence: [] },
      provider: "groq",
      model: "llama-3.3-70b",
      usage: { prompt_tokens: 10, completion_tokens: 20, requests: 1 },
    };
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: envelope });

    await expect(
      runInvestigate({ scanId: "s1", findingId: "f-1", question: "  is this exploitable?  " })
    ).resolves.toEqual(envelope);
    expect(postSpy).toHaveBeenCalledWith("/ai/investigate", {
      scan_id: "s1",
      finding_id: "f-1",
      question: "is this exploitable?",
    });
  });

  it("omits a blank question", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} });

    await runInvestigate({ scanId: "s1", findingId: "f-1", question: "   " });

    expect(postSpy).toHaveBeenCalledWith("/ai/investigate", {
      scan_id: "s1",
      finding_id: "f-1",
    });
  });
});

describe("autoFixPropose", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts with finding_id as a query param and returns the run", async () => {
    const run = {
      status: "awaiting_approval",
      finding_id: "f-1",
      file_path: "src/app.py",
      diff: "@@ -1,1 +1,1 @@\n-a\n+b",
    };
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: run });

    await expect(autoFixPropose({ scanId: "s1", findingId: "f-1" })).resolves.toEqual(run);
    expect(postSpy).toHaveBeenCalledWith("/reports/s1/auto-fix", null, {
      params: { finding_id: "f-1" },
      timeout: 120000,
    });
  });
});

describe("autoFixApprove", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts to the approve endpoint and returns the run", async () => {
    const run = { status: "verified", finding_id: "f-1", pr_url: "https://x/pull/1" };
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: run });

    await expect(autoFixApprove({ scanId: "s1", findingId: "f-1" })).resolves.toEqual(run);
    expect(postSpy).toHaveBeenCalledWith("/reports/s1/auto-fix/f-1/approve", undefined, {
      timeout: 600000,
    });
  });
});
