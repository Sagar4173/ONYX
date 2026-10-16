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

  it("offers Try again immediately when indeterminate with onRetry", () => {
    const onRetry = vi.fn();
    render(<QuotaNotice retryAfter={null} onRetry={onRetry} />);
    expect(screen.getByText(/try again shortly/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("announces via a single sr-only live span; visible countdown is aria-hidden", () => {
    render(<QuotaNotice retryAfter={3} onRetry={() => {}} />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
    const visible = screen.getByText(/retry in 3s/i);
    expect(visible).toHaveAttribute("aria-hidden", "true");
    expect(screen.getByText("3s remaining")).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByText("2s remaining")).toBeInTheDocument();
  });

  it("announces readiness at expiry instead of 'retry in 0s'", () => {
    render(<QuotaNotice retryAfter={1} onRetry={() => {}} />);
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.queryByText(/retry in 0s/i)).toBeNull();
    expect(screen.getByText(/you can retry now/i)).toBeInTheDocument();
    expect(screen.getByText(/ready to retry/i)).toBeInTheDocument();
  });
});
