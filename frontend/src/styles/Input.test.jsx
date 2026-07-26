import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Input } from "./components";

describe("Input", () => {
  it("renders an input element", () => {
    render(<Input />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("renders label when label prop is provided", () => {
    render(<Input label="Email" />);
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Email").tagName).toBe("LABEL");
  });

  it("links label to input via htmlFor/id", () => {
    render(<Input label="Name" />);
    const label = screen.getByText("Name");
    const input = screen.getByRole("textbox");
    expect(label).toHaveAttribute("for", input.id);
  });

  it("applies base input classes", () => {
    render(<Input />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("w-full");
    expect(input.className).toContain("rounded-lg");
    expect(input.className).toContain("bg-gray-800");
  });

  it("applies error variant when error prop is truthy", () => {
    render(<Input error="Required field" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("border-red-500");
  });

  it("renders error message text", () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("renders leading icon", () => {
    render(<Input leadingIcon={<span data-testid="icon">@</span>} />);
    expect(screen.getByTestId("icon")).toBeInTheDocument();
  });

  it("applies size classes", () => {
    render(<Input size="lg" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("px-4 py-3 text-base");
  });

  it("forwards additional props", () => {
    render(<Input placeholder="Enter name" data-testid="my-input" />);
    expect(screen.getByTestId("my-input")).toHaveAttribute("placeholder", "Enter name");
  });

  it("calls onChange when value changes", () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "test" } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it("merges custom className", () => {
    render(<Input className="custom-class" />);
    expect(screen.getByRole("textbox").className).toContain("custom-class");
  });
});
