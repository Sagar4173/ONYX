import { CitationChip } from "./CitationChip";

// eslint-disable-next-line react-refresh/only-export-components
export function parseSegments(text, citations) {
  if (!text) return [];
  const segments = [];
  if (!citations || citations.length === 0) {
    const re = /\[\[(\d+)\]\]/g;
    let last = 0;
    let match;
    while ((match = re.exec(text)) !== null) {
      if (match.index > last) segments.push({ type: "text", value: text.slice(last, match.index) });
      segments.push({ type: "chip", n: parseInt(match[1], 10), citation: null, pending: true });
      last = match.index + match[0].length;
    }
    if (last < text.length) segments.push({ type: "text", value: text.slice(last) });
    return segments;
  }
  const byN = new Map(citations.map((c) => [c.n, c]));
  const re = /\[(\d+)\]/g;
  let last = 0;
  let match;
  while ((match = re.exec(text)) !== null) {
    const n = parseInt(match[1], 10);
    const citation = byN.get(n);
    if (!citation) continue; // unknown [n] stays inside the next text slice
    if (match.index > last) segments.push({ type: "text", value: text.slice(last, match.index) });
    segments.push({ type: "chip", n, citation, pending: false });
    last = match.index + match[0].length;
  }
  if (last < text.length) segments.push({ type: "text", value: text.slice(last) });
  return segments;
}

export const MessageContent = ({ text, citations = null, streaming = false, onCitationClick }) => {
  const segments = parseSegments(text, citations);
  return (
    <p className="text-sm whitespace-pre-wrap break-words">
      {segments.map((seg, i) =>
        seg.type === "text" ? (
          <span key={i}>{seg.value}</span>
        ) : (
          <CitationChip
            key={i}
            n={seg.n}
            citation={seg.citation}
            pending={seg.pending}
            onClick={() => onCitationClick?.(seg.n, seg.citation)}
          />
        )
      )}
      {streaming && (
        <span
          className="inline-block w-2 h-4 ml-0.5 bg-cyan-400 align-middle animate-pulse"
          aria-hidden="true"
        />
      )}
    </p>
  );
};
