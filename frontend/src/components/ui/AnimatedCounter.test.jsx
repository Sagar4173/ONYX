import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AnimatedCounter } from "./StyleComponents";

const originalMatchMedia = window.matchMedia;

function stubReducedMotion(matches) {
  window.matchMedia = vi.fn().mockImplementation((media) => ({
    matches,
    media,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
  }));
}

beforeEach(() => stubReducedMotion(false));
afterEach(() => {
  window.matchMedia = originalMatchMedia;
});

describe("AnimatedCounter", () => {
  it("swaps instantly to the final decimal value under reduced motion", () => {
    stubReducedMotion(true);
    render(<AnimatedCounter value={87.2} decimals={1} />);
    expect(screen.getByText("87.2")).toBeInTheDocument();
  });

  it("starts from 0 and animates when motion is allowed", () => {
    render(<AnimatedCounter value={5} decimals={0} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders non-numeric strings as-is under reduced motion", () => {
    stubReducedMotion(true);
    render(<AnimatedCounter value="Loading" />);
    expect(screen.getByText("Loading")).toBeInTheDocument();
  });

  it("keeps percent-style values intact under reduced motion", () => {
    stubReducedMotion(true);
    render(<AnimatedCounter value="42%" />);
    expect(screen.getByText("42%")).toBeInTheDocument();
  });
});
