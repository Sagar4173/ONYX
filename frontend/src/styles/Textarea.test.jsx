import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Textarea } from "../components/ui/StyleComponents";

describe("Textarea", () => {
  it("renders a textarea", () => {
    render(<Textarea />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("default rows is 3", () => {
    render(<Textarea />);
    expect(screen.getByRole("textbox")).toHaveAttribute("rows", "3");
  });

  it("accepts custom rows", () => {
    render(<Textarea rows={6} />);
    expect(screen.getByRole("textbox")).toHaveAttribute("rows", "6");
  });

  it("error prop renders error message", () => {
    render(<Textarea error="Please enter a value" />);
    expect(screen.getByText("Please enter a value")).toBeInTheDocument();
  });

  it("error prop flips to error variant", () => {
    render(<Textarea />);
    expect(screen.getByRole("textbox").className).toContain("border-gray-600");

    render(<Textarea error="Error" />);
    const textareas = screen.getAllByRole("textbox");
    expect(textareas[1].className).toContain("border-red-500");
  });
});
