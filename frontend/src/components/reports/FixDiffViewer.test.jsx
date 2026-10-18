import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("react-diff-viewer-continued", () => ({
  default: ({ oldValue, newValue, splitView }) => (
    <div data-testid="rdv" data-split={String(splitView)}>
      <pre>{oldValue}</pre>
      <pre>{newValue}</pre>
    </div>
  ),
}));

import { FixDiffViewer } from "./FixDiffViewer";

const DIFF = [
  "--- a/src/app.py",
  "+++ b/src/app.py",
  "@@ -1,1 +1,1 @@",
  "-old line",
  "+new line",
].join("\n");

const manyHunks = (n) =>
  [
    "--- a/x.py",
    "+++ b/x.py",
    ...Array.from({ length: n }, (_, i) => [
      `@@ -${i + 1},1 +${i + 1},1 @@`,
      `-a${i}`,
      `+b${i}`,
    ]).flat(),
  ].join("\n");

describe("FixDiffViewer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the parsed hunk in the viewer region", () => {
    render(<FixDiffViewer diff={DIFF} />);
    expect(screen.getByRole("region", { name: "Proposed fix diff" })).toHaveAttribute(
      "tabindex",
      "0"
    );
    const rdv = screen.getByTestId("rdv");
    expect(rdv.textContent).toContain("old line");
    expect(rdv.textContent).toContain("new line");
    expect(screen.getByText(/\+1 −1/)).toBeInTheDocument();
  });

  it("toggles split↔unified with aria-pressed", async () => {
    const user = userEvent.setup();
    render(<FixDiffViewer diff={DIFF} />);
    const split = screen.getByRole("button", { name: "Split" });
    const unified = screen.getByRole("button", { name: "Unified" });
    expect(split).toHaveAttribute("aria-pressed", "true");

    await user.click(unified);
    expect(unified).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByTestId("rdv")).toHaveAttribute("data-split", "false");

    await user.click(split);
    expect(screen.getByTestId("rdv")).toHaveAttribute("data-split", "true");
  });

  it("caps very long diffs and expands on demand", async () => {
    const user = userEvent.setup();
    render(<FixDiffViewer diff={manyHunks(15)} maxHunks={12} />);
    const expand = screen.getByRole("button", { name: /Show full diff \(3 more hunks\)/ });
    expect(screen.getByTestId("rdv").textContent).not.toContain("b14");

    await user.click(expand);
    expect(screen.queryByRole("button", { name: /Show full diff/ })).toBeNull();
    expect(screen.getByTestId("rdv").textContent).toContain("b14");
  });

  it("renders an empty state for a diff with no hunks", () => {
    render(<FixDiffViewer diff="" />);
    expect(screen.getByText("No changes")).toBeInTheDocument();
  });
});
