import { useEffect } from "react";

const LABEL_KEYS = {
  a: "accepted",
  f: "false_positive",
  d: "dismissed",
  u: "untriaged",
};

const NON_TEXT_INPUT_TYPES = new Set(["checkbox", "radio", "button", "submit"]);

export function useTriageShortcuts({ enabled, onLabel, onMove, onToggleHelp }) {
  useEffect(() => {
    if (!enabled) return undefined;

    const handler = (event) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target;
      const tag = target?.tagName?.toLowerCase();
      const suppressForInput = tag === "input" && !NON_TEXT_INPUT_TYPES.has(target.type);
      if (suppressForInput || tag === "textarea" || tag === "select" || target?.isContentEditable) {
        return;
      }

      const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;

      if (key === "?") {
        event.preventDefault();
        onToggleHelp?.();
        return;
      }
      if (LABEL_KEYS[key]) {
        event.preventDefault();
        onLabel?.(LABEL_KEYS[key]);
        return;
      }
      if (key === "j") {
        event.preventDefault();
        onMove?.(1);
        return;
      }
      if (key === "k") {
        event.preventDefault();
        onMove?.(-1);
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [enabled, onLabel, onMove, onToggleHelp]);
}
