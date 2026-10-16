import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat, AIStreamError } from "../services/aiClient";

export function useSSEStream() {
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const controllerRef = useRef(null);

  const send = useCallback(async ({ scanId, message, history, onEvent }) => {
    controllerRef.current?.abort();
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
      if (controllerRef.current === controller) setStatus("done");
      return { status: "done", error: null };
    } catch (err) {
      const isCurrent = controllerRef.current === controller;
      if (err.name === "AbortError") {
        if (isCurrent) setStatus("done");
        return { status: "aborted", error: null };
      }
      if (isCurrent) setError(err);
      if (err instanceof AIStreamError && err.kind === "rate_limited") {
        if (isCurrent) setStatus("rate_limited");
        return { status: "rate_limited", error: err };
      }
      if (isCurrent) setStatus("error");
      return { status: "error", error: err };
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  }, []);

  const abort = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  useEffect(
    () => () => {
      controllerRef.current?.abort();
    },
    []
  );

  return { status, error, send, abort };
}
