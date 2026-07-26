import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, SeverityBadge } from "./components";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders as a span", () => {
    render(<Badge>Tag</Badge>);
    expect(screen.getByText("Tag").tagName).toBe("SPAN");
  });

  it("applies base badge classes", () => {
    render(<Badge>Base</Badge>);
    const el = screen.getByText("Base");
    expect(el.className).toContain("inline-flex");
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("rounded-full");
  });

  it("applies default variant classes", () => {
    render(<Badge variant="default">Default</Badge>);
    const el = screen.getByText("Default");
    expect(el.className).toContain("bg-gray-700");
    expect(el.className).toContain("text-gray-300");
  });

  it("applies primary variant classes", () => {
    render(<Badge variant="primary">Primary</Badge>);
    const el = screen.getByText("Primary");
    expect(el.className).toContain("bg-cyan-900/50");
    expect(el.className).toContain("text-cyan-300");
  });

  it("applies success variant classes", () => {
    render(<Badge variant="success">Success</Badge>);
    const el = screen.getByText("Success");
    expect(el.className).toContain("bg-green-900/50");
    expect(el.className).toContain("text-green-300");
  });

  it("applies danger variant classes", () => {
    render(<Badge variant="danger">Danger</Badge>);
    const el = screen.getByText("Danger");
    expect(el.className).toContain("bg-red-900/50");
    expect(el.className).toContain("text-red-300");
  });

  it("applies warning variant classes", () => {
    render(<Badge variant="warning">Warning</Badge>);
    const el = screen.getByText("Warning");
    expect(el.className).toContain("bg-yellow-900/50");
    expect(el.className).toContain("text-yellow-300");
  });

  it("applies severity variants correctly", () => {
    const { rerender } = render(<Badge variant="critical">Critical</Badge>);
    expect(screen.getByText("Critical").className).toContain("bg-red-900/70");

    rerender(<Badge variant="high">High</Badge>);
    expect(screen.getByText("High").className).toContain("bg-orange-900/70");

    rerender(<Badge variant="medium">Medium</Badge>);
    expect(screen.getByText("Medium").className).toContain("bg-yellow-900/70");

    rerender(<Badge variant="low">Low</Badge>);
    expect(screen.getByText("Low").className).toContain("bg-cyan-900/70");
  });

  it("applies size classes", () => {
    const { rerender } = render(<Badge size="xs">XS</Badge>);
    expect(screen.getByText("XS").className).toContain("px-1.5 py-0.5 text-xs");

    rerender(<Badge size="lg">LG</Badge>);
    expect(screen.getByText("LG").className).toContain("px-3 py-1.5 text-sm");
  });

  it("merges custom className", () => {
    render(<Badge className="extra-class">Merged</Badge>);
    expect(screen.getByText("Merged").className).toContain("extra-class");
  });

  it("forwards additional props", () => {
    render(<Badge data-testid="badge-el">Test</Badge>);
    expect(screen.getByTestId("badge-el")).toBeInTheDocument();
  });
});

describe("SeverityBadge", () => {
  it("renders severity text in uppercase", () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("maps critical severity to correct badge variant", () => {
    render(<SeverityBadge severity="critical" />);
    expect(screen.getByText("CRITICAL").className).toContain("bg-red-900/70");
  });

  it("maps low severity to cyan badge", () => {
    render(<SeverityBadge severity="low" />);
    expect(screen.getByText("LOW").className).toContain("bg-cyan-900/70");
  });

  it("maps info severity to default variant", () => {
    render(<SeverityBadge severity="info" />);
    expect(screen.getByText("INFO").className).toContain("bg-gray-700");
  });

  it("handles unknown severity as default", () => {
    render(<SeverityBadge severity="unknown" />);
    expect(screen.getByText("UNKNOWN").className).toContain("bg-gray-700");
  });

  it("merges custom className", () => {
    render(<SeverityBadge severity="high" className="my-class" />);
    expect(screen.getByText("HIGH").className).toContain("my-class");
  });
});
