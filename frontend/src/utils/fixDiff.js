const HUNK_RE = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/;
const GAP = "⋯";

export function parseUnifiedDiff(diff) {
  if (!diff || typeof diff !== "string") {
    return { hunks: [], addedLines: 0, removedLines: 0 };
  }
  const hunks = [];
  let current = null;
  let addedLines = 0;
  let removedLines = 0;
  for (const raw of diff.split("\n")) {
    const line = raw.endsWith("\r") ? raw.slice(0, -1) : raw;
    if (line.startsWith("---") || line.startsWith("+++")) continue;
    if (HUNK_RE.test(line)) {
      current = { header: line, oldLines: [], newLines: [] };
      hunks.push(current);
      continue;
    }
    if (!current) continue;
    if (line.startsWith("\\")) continue;
    if (line.startsWith("-")) {
      current.oldLines.push(line.slice(1));
      removedLines += 1;
    } else if (line.startsWith("+")) {
      current.newLines.push(line.slice(1));
      addedLines += 1;
    } else if (line.startsWith(" ")) {
      current.oldLines.push(line.slice(1));
      current.newLines.push(line.slice(1));
    }
  }
  return { hunks, addedLines, removedLines };
}

export function buildViewerTexts(parsed, { maxHunks = 12 } = {}) {
  const total = parsed.hunks.length;
  const shownCount = Math.min(total, Math.max(0, maxHunks));
  const shown = parsed.hunks.slice(0, shownCount);
  const oldText = shown.map((h) => h.oldLines.join("\n")).join(`\n${GAP}\n`);
  const newText = shown.map((h) => h.newLines.join("\n")).join(`\n${GAP}\n`);
  return {
    oldText,
    newText,
    totalHunks: total,
    shownHunks: shownCount,
    truncated: shownCount < total,
  };
}
