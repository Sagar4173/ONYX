import { describe, it, expect } from "vitest";
import { splitPathToken, segmentEvidence } from "./investigateEvidence";

describe("splitPathToken", () => {
  it("splits a leading path:line token", () => {
    expect(splitPathToken("src/auth.py:10 - user input reaches query")).toEqual({
      path: "src/auth.py:10",
      rest: " - user input reaches query",
    });
  });

  it("returns null when no path:line token leads", () => {
    expect(splitPathToken("CWE-89: SQL injection")).toBeNull();
  });

  it("returns null for empty input", () => {
    expect(splitPathToken(null)).toBeNull();
    expect(splitPathToken("")).toBeNull();
  });
});

describe("segmentEvidence", () => {
  it("returns [] for empty text", () => {
    expect(segmentEvidence("", ["f-1"])).toEqual([]);
  });

  it("returns a single text segment when no finding ids are known", () => {
    expect(segmentEvidence("Sibling finding f-1 shares a file", [])).toEqual([
      { type: "text", value: "Sibling finding f-1 shares a file" },
    ]);
  });

  it("wraps known finding ids in finding segments", () => {
    expect(segmentEvidence("Sibling finding f-2 shares src/app.py", ["f-2"])).toEqual([
      { type: "text", value: "Sibling finding " },
      { type: "finding", value: "f-2", findingId: "f-2" },
      { type: "text", value: " shares src/app.py" },
    ]);
  });

  it("respects token boundaries and prefers the longest id", () => {
    expect(segmentEvidence("see f-12 for context", ["f-1"])).toEqual([
      { type: "text", value: "see f-12 for context" },
    ]);
    expect(segmentEvidence("see f-12 for context", ["f-1", "f-12"])).toEqual([
      { type: "text", value: "see " },
      { type: "finding", value: "f-12", findingId: "f-12" },
      { type: "text", value: " for context" },
    ]);
  });
});
