import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "./components";

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="No data" />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders description", () => {
    render(<EmptyState description="Add some items to get started" />);
    expect(screen.getByText("Add some items to get started")).toBeInTheDocument();
  });

  it("renders icon when provided", () => {
    render(<EmptyState icon={<span data-testid="empty-icon">📭</span>} />);
    expect(screen.getByTestId("empty-icon")).toBeInTheDocument();
  });

  it("renders action element", () => {
    render(<EmptyState action={<button>Create</button>} />);
    expect(screen.getByRole("button", { name: "Create" })).toBeInTheDocument();
  });

  it("applies base layout classes", () => {
    render(<EmptyState title="Empty" />);
    const el = screen.getByText("Empty").parentElement;
    expect(el.className).toContain("flex");
    expect(el.className).toContain("flex-col");
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("py-16");
  });

  it("merges custom className", () => {
    render(<EmptyState title="Custom" className="my-empty" />);
    const el = screen.getByText("Custom").parentElement;
    expect(el.className).toContain("my-empty");
  });
});
