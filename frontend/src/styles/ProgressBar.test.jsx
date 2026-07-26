import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressBar } from "./components";

describe("ProgressBar", () => {
  it("renders with role='progressbar'", () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("has aria-valuenow, aria-valuemin, aria-valuemax attributes", () => {
    render(<ProgressBar value={50} max={100} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "50");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("showLabel renders percentage text", () => {
    render(<ProgressBar value={75} showLabel />);
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("does not show label by default", () => {
    render(<ProgressBar value={75} />);
    expect(screen.queryByText("75%")).not.toBeInTheDocument();
  });

  it("animated adds animate-pulse", () => {
    const { container } = render(<ProgressBar value={50} animated />);
    const innerBar = container.querySelector("[role='progressbar'] > div");
    expect(innerBar.className).toContain("animate-pulse");
  });

  it("value is clamped to 0-100", () => {
    const { container: containerLow } = render(<ProgressBar value={-20} />);
    const lowBar = containerLow.querySelector("[role='progressbar']");
    expect(lowBar).toHaveAttribute("aria-valuenow", "-20");

    const { container: containerHigh } = render(<ProgressBar value={150} />);
    const highBar = containerHigh.querySelector("[role='progressbar']");
    expect(highBar).toHaveAttribute("aria-valuenow", "150");
  });

  it("label shows clamped percentage when value exceeds 0-100", () => {
    render(<ProgressBar value={150} showLabel />);
    expect(screen.getByText("100%")).toBeInTheDocument();

    render(<ProgressBar value={-20} showLabel />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("color prop applies correct classes", () => {
    const { container } = render(<ProgressBar value={50} color="success" />);
    const innerBar = container.querySelector("[role='progressbar'] > div");
    expect(innerBar.className).toContain("bg-green-500");
  });

  it("size prop applies correct height classes", () => {
    const { container } = render(<ProgressBar value={50} size="lg" />);
    const outerBar = container.querySelector(".overflow-hidden");
    expect(outerBar.className).toContain("h-3");
  });
});
