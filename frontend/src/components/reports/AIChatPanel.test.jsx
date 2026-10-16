import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("@services/aiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, streamChat: vi.fn() };
});

const { streamChat, AIStreamError } = await import("@services/aiClient");
import { AIChatPanel } from "./AIChatPanel";

function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("AIChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
    localStorage.setItem("access_token", "t");
  });
  afterEach(() => vi.restoreAllMocks());

  it("streams a reply: user bubble, caret during stream, final answer with model label", async () => {
    const d = deferred();
    streamChat.mockImplementation(async ({ onEvent }) => {
      onEvent({ type: "delta", text: "The crit" });
      await d.promise;
      onEvent({ type: "delta", text: "ical finding" });
      onEvent({
        type: "done",
        reply: "The critical finding",
        citations: [],
        model_used: "groq/llama",
      });
    });

    render(<AIChatPanel scanId="scan-1" />);
    expect(screen.getByText(/ask anything about this security scan/i)).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/ask about vulnerabilities/i), {
      target: { value: "what is critical?" },
    });
    fireEvent.keyDown(screen.getByPlaceholderText(/ask about vulnerabilities/i), { key: "Enter" });

    expect(await screen.findByText("what is critical?")).toBeInTheDocument();
    expect(await screen.findByText("The crit")).toBeInTheDocument();
    // Stop button replaces Send while streaming
    expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();

    d.resolve();
    expect(await screen.findByText("The critical finding")).toBeInTheDocument();
    expect(screen.getByText("groq/llama")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /stop/i })).toBeNull();
  });

  it("keeps partial text on mid-stream error and offers retry", async () => {
    streamChat.mockImplementation(async ({ onEvent }) => {
      onEvent({ type: "delta", text: "partial answer" });
      throw new AIStreamError("Connection lost mid-stream.", { kind: "stream" });
    });
    render(<AIChatPanel scanId="scan-2" />);
    fireEvent.change(screen.getByPlaceholderText(/ask about vulnerabilities/i), {
      target: { value: "q" },
    });
    fireEvent.keyDown(screen.getByPlaceholderText(/ask about vulnerabilities/i), { key: "Enter" });

    expect(await screen.findByText("partial answer")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/connection lost mid-stream/i)).toBeInTheDocument();
  });

  it("renders AIStateBlock error (no retry) when zero deltas arrived", async () => {
    streamChat.mockRejectedValue(
      new AIStreamError("Scan not found or access denied.", { status: 404, kind: "not_found" })
    );
    render(<AIChatPanel scanId="scan-3" />);
    fireEvent.change(screen.getByPlaceholderText(/ask about vulnerabilities/i), {
      target: { value: "q" },
    });
    fireEvent.keyDown(screen.getByPlaceholderText(/ask about vulnerabilities/i), { key: "Enter" });

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Scan not found or access denied.")).toBeInTheDocument();
    expect(screen.queryByText("partial answer")).toBeNull();
  });

  it("shows QuotaNotice with countdown on 429", async () => {
    streamChat.mockRejectedValue(
      new AIStreamError("Rate limit exceeded.", {
        status: 429,
        kind: "rate_limited",
        retryAfter: 42,
      })
    );
    render(<AIChatPanel scanId="scan-4" />);
    fireEvent.change(screen.getByPlaceholderText(/ask about vulnerabilities/i), {
      target: { value: "q" },
    });
    fireEvent.keyDown(screen.getByPlaceholderText(/ask about vulnerabilities/i), { key: "Enter" });

    expect(await screen.findByText(/rate limit reached/i)).toBeInTheDocument();
    expect(screen.getByText(/retry in 42s/i)).toBeInTheDocument();
  });
});
