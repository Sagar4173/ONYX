import { useCallback, useRef, useState } from "react";
import { streamChat, AIStreamError } from "../services/aiClient";

export function useSSEStream() {
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const controllerRef = useRef(null);

  const send = useCallback(async ({ scanId, message, history, onEvent }) => {
    const controller = new AbortController();
    controllerRef.current = controller;
    setError(null);
    setStatus("connecting");
    let sawFrame = false;
    try {
      await streamChat({
        scanId,
        message,
        conversationHistory: history,
        signal: controller.signal,
        onEvent: (event) => {
          if (!sawFrame) {
            sawFrame = true;
            setStatus("streaming");
          }
          onEvent(event);
        },
      });
      setStatus("done");
      return { status: "done", error: null };
    } catch (err) {
      if (err.name === "AbortError") {
        setStatus("done");
        return { status: "aborted", error: null };
      }
      setError(err);
      if (err instanceof AIStreamError && err.kind === "rate_limited") {
        setStatus("rate_limited");
        return { status: "rate_limited", error: err };
      }
      setStatus("error");
      return { status: "error", error: err };
    } finally {
      controllerRef.current = null;
    }
  }, []);

  const abort = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  return { status, error, send, abort };
}
