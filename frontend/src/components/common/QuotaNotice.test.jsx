import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, fireEvent } from "@testing-library/react";
import { QuotaNotice } from "./QuotaNotice";

describe("QuotaNotice", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("counts down from retryAfter then enables retry", () => {
    const onRetry = vi.fn();
    render(<QuotaNotice retryAfter={3} onRetry={onRetry} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
    expect(screen.getByText(/retry in 3s/i)).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByText(/retry in 2s/i)).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(2000));
    expect(screen.getByRole("button", { name: /try again/i })).not.toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("indeterminate when retryAfter is null", () => {
    render(<QuotaNotice retryAfter={null} />);
    expect(screen.getByText(/rate limit reached/i)).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
