import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("framer-motion", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useReducedMotion: vi.fn(() => false) };
});

import { useReducedMotion } from "framer-motion";
import { FixStatusRail } from "./FixStatusRail";
import { VerifiedBadge } from "./VerifiedBadge";

describe("FixStatusRail", () => {
  it("renders the four lifecycle steps with the current one marked", () => {
    render(<FixStatusRail status="awaiting_approval" />);
    expect(screen.getByText("Awaiting approval").closest("li")).toHaveAttribute(
      "aria-current",
      "step"
    );
    expect(screen.getByText("Proposed")).toBeInTheDocument();
    expect(screen.getByText("PR created")).toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(screen.getByTestId("fix-rail-done")).toBeInTheDocument();
  });

  it("marks all prior steps done at verified", () => {
    render(<FixStatusRail status="verified" />);
    expect(screen.getAllByTestId("fix-rail-done")).toHaveLength(3);
    expect(screen.getByText("Verified").closest("li")).toHaveAttribute("aria-current", "step");
  });

  it("highlights only the first step for dry_run", () => {
    render(<FixStatusRail status="dry_run" />);
    expect(screen.getByText("Proposed").closest("li")).toHaveAttribute("aria-current", "step");
    expect(screen.queryByTestId("fix-rail-done")).toBeNull();
  });
});

describe("VerifiedBadge", () => {
  it("announces the verification result", () => {
    render(<VerifiedBadge verification={{ verified: true, total_findings: 2 }} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveTextContent("Verified");
    expect(badge).toHaveTextContent("total findings dropped to 2");
  });

  it("omits the sweep when reduced motion is on", () => {
    useReducedMotion.mockReturnValue(true);
    render(<VerifiedBadge verification={{ verified: true, total_findings: 0 }} />);
    expect(screen.queryByTestId("verified-sweep")).toBeNull();
    useReducedMotion.mockReturnValue(false);
  });

  it("renders the sweep for the signature moment", () => {
    render(<VerifiedBadge verification={{ verified: true, total_findings: 0 }} />);
    expect(screen.getByTestId("verified-sweep")).toBeInTheDocument();
  });
});
