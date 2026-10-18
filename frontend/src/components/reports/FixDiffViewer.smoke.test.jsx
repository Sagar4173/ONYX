import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { FixDiffViewer } from "./FixDiffViewer";

const DIFF = [
  "--- a/src/app.py",
  "+++ b/src/app.py",
  "@@ -1,3 +1,4 @@",
  " import os",
  "-query = 'SELECT * FROM users WHERE id=' + user_id",
  "+query = 'SELECT * FROM users WHERE id=%s'",
  "+cursor.execute(query, (user_id,))",
  " return cursor.fetchall()",
].join("\n");

describe("FixDiffViewer (real react-diff-viewer-continued)", () => {
  it("renders the real viewer without throwing", async () => {
    render(<FixDiffViewer diff={DIFF} />);
    const region = screen.getByRole("region", { name: "Proposed fix diff" });
    expect(region).toBeInTheDocument();
    await waitFor(() => {
      expect(region.textContent).toContain("cursor.execute");
      expect(region.textContent).toContain("id=%s");
    });
  });
});
