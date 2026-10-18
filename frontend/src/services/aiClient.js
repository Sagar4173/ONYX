/**
 * AI client (UX Track Phase 0).
 * Non-streaming AI calls stay on the axios instance in ./api (auth refresh, toasts).
 * SSE chat uses fetch directly — EventSource cannot send an Authorization header.
 */
import { API_BASE_URL, api } from "./api";

export class AIStreamError extends Error {
  constructor(message, { status = 0, kind = "stream", retryAfter = null } = {}) {
    super(message);
    this.name = "AIStreamError";
    this.status = status;
    this.kind = kind;
    this.retryAfter = retryAfter;
  }
}

const authHeaders = () => {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export async function streamChat({ scanId, message, conversationHistory = [], onEvent, signal }) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/ai/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        scan_id: scanId,
        message,
        conversation_history: conversationHistory.slice(-20),
      }),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new AIStreamError("Network error. Please check your connection.", { kind: "network" });
  }

  if (!response.ok) {
    let detail = "";
    try {
      detail = ((await response.json()) || {}).detail || "";
    } catch {
      detail = "";
    }
    if (response.status === 429) {
      const header = response.headers.get("Retry-After");
      const parsed = header == null ? NaN : parseInt(header, 10);
      throw new AIStreamError("Rate limit exceeded.", {
        status: 429,
        kind: "rate_limited",
        retryAfter: Number.isNaN(parsed) ? null : Math.max(0, parsed),
      });
    }
    if (response.status === 401) {
      throw new AIStreamError("Session expired. Please log in again.", {
        status: 401,
        kind: "auth",
      });
    }
    if (response.status === 404) {
      throw new AIStreamError(detail || "Scan not found or access denied.", {
        status: 404,
        kind: "not_found",
      });
    }
    if (response.status === 400 || response.status === 403) {
      throw new AIStreamError(detail || "Message blocked by safety screening.", {
        status: response.status,
        kind: "blocked",
      });
    }
    throw new AIStreamError(detail || `AI chat service error (${response.status}).`, {
      status: response.status,
      kind: "server",
    });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let sawDone = false;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop();
      for (const frame of frames) {
        const dataLine = frame.split("\n").find((line) => line.startsWith("data:"));
        if (!dataLine) continue;
        let event;
        try {
          event = JSON.parse(dataLine.slice(5).trim());
        } catch {
          continue;
        }
        if (event.type === "error") {
          throw new AIStreamError(event.detail || "AI provider error mid-stream.", {
            kind: "server",
          });
        }
        if (event.type === "done") sawDone = true;
        onEvent(event);
      }
    }
  } catch (err) {
    if (err.name === "AbortError" || err instanceof AIStreamError) throw err;
    throw new AIStreamError("Network error. Please check your connection.", {
      status: 0,
      kind: "network",
    });
  } finally {
    reader.releaseLock?.();
  }
  if (!sawDone) {
    throw new AIStreamError("Connection lost mid-stream.", { kind: "stream" });
  }
}

export async function getAIFeatures() {
  const response = await fetch(`${API_BASE_URL}/ai/features`, { headers: authHeaders() });
  if (!response.ok) throw new Error(`AI features request failed (${response.status})`);
  return response.json();
}

export async function runInvestigate({ scanId, findingId, question }) {
  const payload = { scan_id: scanId, finding_id: findingId };
  const trimmed = (question || "").trim();
  if (trimmed) payload.question = trimmed;
  const response = await api.post("/ai/investigate", payload);
  return response.data;
}
