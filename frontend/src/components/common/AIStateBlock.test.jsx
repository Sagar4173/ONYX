import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AIStateBlock } from "./AIStateBlock";

describe("AIStateBlock", () => {
  it("loading renders polite status region with title", () => {
    render(<AIStateBlock variant="loading" title="Analyzing scan data..." />);
    const region = screen.getByRole("status");
    expect(region).toHaveAttribute("aria-live", "polite");
    expect(screen.getByText("Analyzing scan data...")).toBeInTheDocument();
  });

  it("error is an alert with working retry", async () => {
    const onRetry = vi.fn();
    render(
      <AIStateBlock
        variant="error"
        title="Connection lost"
        detail="stream ended"
        onRetry={onRetry}
      />
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("stream ended")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("degraded and disabled map to titled alerts", () => {
    const { unmount } = render(
      <AIStateBlock variant="degraded" description="provider fell back" />
    );
    expect(screen.getByRole("status")).toBeTruthy();
    unmount();
    render(<AIStateBlock variant="disabled" description="feature off" />);
    expect(screen.getByText("feature off")).toBeInTheDocument();
  });

  it("empty uses EmptyState title", () => {
    render(<AIStateBlock variant="empty" title="No results" />);
    expect(screen.getByText("No results")).toBeInTheDocument();
  });
});
