import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Alert } from "./components";

describe("Alert", () => {
  it("renders children", () => {
    render(<Alert>Message</Alert>);
    expect(screen.getByText("Message")).toBeInTheDocument();
  });

  it("renders title", () => {
    render(<Alert title="Warning Title">Body</Alert>);
    expect(screen.getByText("Warning Title")).toBeInTheDocument();
  });

  it("applies info variant by default", () => {
    render(<Alert>Info</Alert>);
    const el = screen.getByText("Info").parentElement.parentElement;
    expect(el.className).toContain("bg-cyan-900/30");
    expect(el.className).toContain("border-cyan-700/50");
  });

  it("applies success variant classes", () => {
    render(<Alert variant="success">OK</Alert>);
    const el = screen.getByText("OK").parentElement.parentElement;
    expect(el.className).toContain("bg-green-900/30");
  });

  it("applies danger variant classes", () => {
    render(<Alert variant="danger">Error</Alert>);
    const el = screen.getByText("Error").parentElement.parentElement;
    expect(el.className).toContain("bg-red-900/30");
  });

  it("applies warning variant classes", () => {
    render(<Alert variant="warning">Caution</Alert>);
    const el = screen.getByText("Caution").parentElement.parentElement;
    expect(el.className).toContain("bg-yellow-900/30");
  });

  it("renders close button when onClose is provided", () => {
    render(<Alert onClose={() => {}}>Dismissible</Alert>);
    expect(screen.getByText("×")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(<Alert onClose={onClose}>Dismiss</Alert>);
    fireEvent.click(screen.getByText("×"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("renders icon when provided", () => {
    render(<Alert icon={<span data-testid="alert-icon">!</span>} />);
    expect(screen.getByTestId("alert-icon")).toBeInTheDocument();
  });

  it("merges custom className", () => {
    render(<Alert className="my-alert">Styled</Alert>);
    const el = screen.getByText("Styled").parentElement.parentElement;
    expect(el.className).toContain("my-alert");
  });
});
