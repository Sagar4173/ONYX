import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Spinner, LoadingOverlay } from "../components/ui/StyleComponents";

describe("Spinner", () => {
  it("renders a spinning element", () => {
    const { container } = render(<Spinner />);
    const el = container.firstChild;
    expect(el.className).toContain("animate-spin");
    expect(el.className).toContain("rounded-full");
  });

  it("renders with cyan accent border", () => {
    const { container } = render(<Spinner />);
    const el = container.firstChild;
    expect(el.className).toContain("border-t-cyan-500");
  });

  it("applies default (md) size", () => {
    const { container } = render(<Spinner />);
    expect(container.firstChild.className).toContain("w-6 h-6");
  });

  it("applies sm size", () => {
    const { container } = render(<Spinner size="sm" />);
    expect(container.firstChild.className).toContain("w-4 h-4");
  });

  it("applies lg size", () => {
    const { container } = render(<Spinner size="lg" />);
    expect(container.firstChild.className).toContain("w-8 h-8");
  });

  it("applies xl size", () => {
    const { container } = render(<Spinner size="xl" />);
    expect(container.firstChild.className).toContain("w-12 h-12");
  });

  it("merges custom className", () => {
    const { container } = render(<Spinner className="my-spinner" />);
    expect(container.firstChild.className).toContain("my-spinner");
  });
});

describe("LoadingOverlay", () => {
  it("renders default message", () => {
    render(<LoadingOverlay />);
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<LoadingOverlay message="Processing..." />);
    expect(document.querySelector(".text-gray-300")).toHaveTextContent("Processing...");
  });
});
