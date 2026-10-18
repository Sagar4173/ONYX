import { describe, it, expect } from "vitest";
import { parseUnifiedDiff, buildViewerTexts } from "./fixDiff";

const SINGLE_HUNK = [
  "--- a/src/app.py",
  "+++ b/src/app.py",
  "@@ -1,3 +1,4 @@",
  " import os",
  "-query = 'SELECT * FROM users WHERE id=' + user_id",
  "+query = 'SELECT * FROM users WHERE id=%s'",
  "+cursor.execute(query, (user_id,))",
  " return cursor.fetchall()",
].join("\n");

describe("parseUnifiedDiff", () => {
  it("splits a single hunk into aligned old/new texts with counts", () => {
    const parsed = parseUnifiedDiff(SINGLE_HUNK);
    expect(parsed.hunks).toHaveLength(1);
    expect(parsed.addedLines).toBe(2);
    expect(parsed.removedLines).toBe(1);
    expect(parsed.hunks[0].oldLines).toEqual([
      "import os",
      "query = 'SELECT * FROM users WHERE id=' + user_id",
      "return cursor.fetchall()",
    ]);
    expect(parsed.hunks[0].newLines).toEqual([
      "import os",
      "query = 'SELECT * FROM users WHERE id=%s'",
      "cursor.execute(query, (user_id,))",
      "return cursor.fetchall()",
    ]);
  });

  it("handles multiple hunks, CRLF, and the no-newline marker", () => {
    const diff = [
      "--- a/x.py",
      "+++ b/x.py",
      "@@ -1,1 +1,1 @@",
      "-a",
      "+b",
      "\\ No newline at end of file",
      "@@ -10,1 +10,2 @@",
      " ctx",
      "+new line",
      "",
    ].join("\r\n");
    const parsed = parseUnifiedDiff(diff);
    expect(parsed.hunks).toHaveLength(2);
    expect(parsed.addedLines).toBe(2);
    expect(parsed.removedLines).toBe(1);
    expect(parsed.hunks[0].newLines).toEqual(["b"]);
    expect(parsed.hunks[1].newLines).toEqual(["ctx", "new line"]);
  });

  it("keeps in-hunk lines whose content starts with -- or ++", () => {
    const diff = [
      "--- a/x.sql",
      "+++ b/x.sql",
      "@@ -1,2 +1,2 @@",
      "--- stale comment",
      "+++ fresh comment",
      " SELECT 1",
    ].join("\n");
    const parsed = parseUnifiedDiff(diff);
    expect(parsed.hunks).toHaveLength(1);
    expect(parsed.removedLines).toBe(1);
    expect(parsed.addedLines).toBe(1);
    expect(parsed.hunks[0].oldLines).toEqual(["-- stale comment", "SELECT 1"]);
    expect(parsed.hunks[0].newLines).toEqual(["++ fresh comment", "SELECT 1"]);
  });

  it("returns an empty result for null / empty input", () => {
    expect(parseUnifiedDiff(null)).toEqual({ hunks: [], addedLines: 0, removedLines: 0 });
    expect(parseUnifiedDiff("")).toEqual({ hunks: [], addedLines: 0, removedLines: 0 });
  });
});

describe("buildViewerTexts", () => {
  const THREE_HUNKS = [
    "--- a/x.py",
    "+++ b/x.py",
    "@@ -1,1 +1,1 @@",
    "-a",
    "+b",
    "@@ -5,1 +5,1 @@",
    "-c",
    "+d",
    "@@ -9,1 +9,1 @@",
    "-e",
    "+f",
  ].join("\n");

  it("joins hunks with a context gap marker on both sides", () => {
    const view = buildViewerTexts(parseUnifiedDiff(SINGLE_HUNK));
    expect(view.oldText).toContain("query = 'SELECT * FROM users WHERE id=' + user_id");
    expect(view.newText).toContain("cursor.execute(query, (user_id,))");
    expect(view.truncated).toBe(false);
    expect(view.totalHunks).toBe(1);
  });

  it("caps the number of hunks and reports truncation", () => {
    const view = buildViewerTexts(parseUnifiedDiff(THREE_HUNKS), { maxHunks: 2 });
    expect(view.shownHunks).toBe(2);
    expect(view.truncated).toBe(true);
    expect(view.oldText).toContain("⋯");
    expect(view.oldText).not.toContain("\ne\n");
  });

  it("expands again when given Infinity", () => {
    const view = buildViewerTexts(parseUnifiedDiff(THREE_HUNKS), { maxHunks: Infinity });
    expect(view.shownHunks).toBe(3);
    expect(view.truncated).toBe(false);
  });
});
