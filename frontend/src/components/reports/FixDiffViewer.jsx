import { useEffect, useMemo, useState } from "react";
import ReactDiffViewer from "react-diff-viewer-continued";
import { Button, EmptyState } from "../ui/StyleComponents";
import { buildViewerTexts, parseUnifiedDiff } from "../../utils/fixDiff";

const DARK_STYLES = {
  variables: {
    dark: {
      diffViewerBackground: "#111827",
      diffViewerColor: "#c4b5fd",
      addedBackground: "rgba(6, 182, 212, 0.12)",
      addedColor: "#a5f3fc",
      removedBackground: "rgba(239, 68, 68, 0.14)",
      removedColor: "#fecaca",
      wordAddedBackground: "rgba(6, 182, 212, 0.3)",
      wordRemovedBackground: "rgba(239, 68, 68, 0.3)",
      addedGutterBackground: "rgba(6, 182, 212, 0.18)",
      removedGutterBackground: "rgba(239, 68, 68, 0.2)",
      gutterBackground: "#0f172a",
      gutterBackgroundDark: "#0b1220",
      gutterColor: "#64748b",
      codeFoldBackground: "#0f172a",
      codeFoldGutterBackground: "#0b1220",
      codeFoldContentColor: "#94a3b8",
      emptyLineBackground: "#0b1220",
      diffViewerTitleBackground: "#0f172a",
      diffViewerTitleColor: "#94a3b8",
      diffViewerTitleBorderColor: "#334155",
    },
  },
};

export function FixDiffViewer({ diff, maxHunks = 12 }) {
  const [split, setSplit] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const mql = window.matchMedia("(max-width: 767px)");
    const sync = () => setSplit(!mql.matches);
    sync();
    mql.addEventListener?.("change", sync);
    return () => mql.removeEventListener?.("change", sync);
  }, []);

  const parsed = useMemo(() => parseUnifiedDiff(diff), [diff]);
  const view = useMemo(
    () => buildViewerTexts(parsed, { maxHunks: expanded ? Infinity : maxHunks }),
    [parsed, expanded, maxHunks]
  );

  if (!parsed.hunks.length) {
    return <EmptyState title="No changes" description="The fix agent proposed no code changes." />;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-gray-500">
          {parsed.hunks.length} hunk{parsed.hunks.length === 1 ? "" : "s"} · +{parsed.addedLines} −
          {parsed.removedLines}
        </p>
        <div className="flex gap-1" role="group" aria-label="Diff layout">
          <Button
            size="sm"
            variant={split ? "primary" : "outline"}
            aria-pressed={split}
            onClick={() => setSplit(true)}
          >
            Split
          </Button>
          <Button
            size="sm"
            variant={!split ? "primary" : "outline"}
            aria-pressed={!split}
            onClick={() => setSplit(false)}
          >
            Unified
          </Button>
        </div>
      </div>

      <div
        role="region"
        aria-label="Proposed fix diff"
        tabIndex={0}
        className="max-h-[32rem] overflow-auto rounded-lg border border-gray-700/60 bg-gray-900/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <ReactDiffViewer
          oldValue={view.oldText}
          newValue={view.newText}
          splitView={split}
          useDarkTheme
          hideLineNumbers
          styles={DARK_STYLES}
        />
      </div>

      {view.truncated && (
        <Button variant="outline" size="sm" onClick={() => setExpanded(true)}>
          Show full diff ({view.totalHunks - view.shownHunks} more hunks)
        </Button>
      )}
    </div>
  );
}
