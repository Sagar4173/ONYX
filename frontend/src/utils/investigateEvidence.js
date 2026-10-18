const PATH_TOKEN_RE = /^([\w.\\/-]+\.[A-Za-z0-9]+:\d+)\b/;

export function splitPathToken(text) {
  if (!text) return null;
  const match = PATH_TOKEN_RE.exec(text);
  if (!match) return null;
  return { path: match[1], rest: text.slice(match[1].length) };
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function segmentEvidence(text, findingIds = []) {
  const value = text || "";
  const ids = [...new Set(findingIds.filter(Boolean))].sort((a, b) => b.length - a.length);
  if (!value) return [];
  if (ids.length === 0) return [{ type: "text", value }];

  const pattern = new RegExp(`(?<![\\w-])(${ids.map(escapeRegExp).join("|")})(?![\\w-])`, "g");
  const segments = [];
  let last = 0;
  for (const match of value.matchAll(pattern)) {
    if (match.index > last) {
      segments.push({ type: "text", value: value.slice(last, match.index) });
    }
    segments.push({ type: "finding", value: match[1], findingId: match[1] });
    last = match.index + match[1].length;
  }
  if (last < value.length) {
    segments.push({ type: "text", value: value.slice(last) });
  }
  return segments.length > 0 ? segments : [{ type: "text", value }];
}
