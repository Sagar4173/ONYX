import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "./components";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it('sets type="button" by default', () => {
    render(<Button>Submit</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("type", "button");
  });

  it("applies base button classes", () => {
    render(<Button>Base</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("inline-flex");
    expect(btn.className).toContain("rounded-lg");
    expect(btn.className).toContain("transition-all");
  });

  it("applies focus-visible ring classes", () => {
    render(<Button>Focus</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("focus-visible:ring-2");
    expect(btn.className).toContain("focus-visible:ring-offset-2");
  });

  it("applies primary variant classes", () => {
    render(<Button variant="primary">Primary</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-cyan-600");
    expect(btn.className).toContain("text-white");
    expect(btn.className).toContain("hover:bg-cyan-700");
  });

  it("applies danger variant classes", () => {
    render(<Button variant="danger">Danger</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-red-600");
    expect(btn.className).toContain("hover:bg-red-700");
  });

  it("applies ghost variant classes", () => {
    render(<Button variant="ghost">Ghost</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-transparent");
    expect(btn.className).toContain("hover:bg-gray-800");
  });

  it("applies sm size classes", () => {
    render(<Button size="sm">Small</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("px-3 py-1.5 text-sm");
  });

  it("applies lg size classes", () => {
    render(<Button size="lg">Large</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("px-5 py-2.5 text-base");
  });

  it("applies xl size classes", () => {
    render(<Button size="xl">XLarge</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("px-6 py-3 text-lg");
  });

  describe("gradient mode", () => {
    it("applies pill gradient classes when gradient prop is true", () => {
      render(<Button gradient>Gradient</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("rounded-full");
      expect(btn.className).toContain("from-cyan-400");
      expect(btn.className).toContain("via-violet-500");
      expect(btn.className).toContain("to-cyan-400");
    });

    it("includes focus ring classes in gradient mode", () => {
      render(<Button gradient>Gradient</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("focus-visible:ring-cyan-500");
      expect(btn.className).toContain("focus-visible:ring-offset-gray-900");
    });

    it("includes hover/active transform effects", () => {
      render(<Button gradient>Gradient</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("hover:scale-[1.03]");
      expect(btn.className).toContain("active:scale-[0.98]");
    });

    it("includes shadow effects", () => {
      render(<Button gradient>Gradient</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("shadow-lg");
      expect(btn.className).toContain("hover:shadow-xl");
      expect(btn.className).toContain("shadow-cyan-500/20");
    });
  });

  describe("disabled state", () => {
    it("disables the button when disabled is true", () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole("button")).toBeDisabled();
    });

    it("includes disabled visual classes", () => {
      render(<Button disabled>Disabled</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("disabled:opacity-50");
      expect(btn.className).toContain("disabled:cursor-not-allowed");
    });

    it("does not call onClick when disabled", () => {
      const handleClick = vi.fn();
      render(
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      );
      fireEvent.click(screen.getByRole("button"));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("loading state", () => {
    it("renders a spinner when isLoading is true", () => {
      const { container } = render(<Button isLoading>Loading</Button>);
      const btn = screen.getByRole("button");
      expect(btn).toBeDisabled();
      expect(btn.querySelector(".animate-spin")).toBeInTheDocument();
    });

    it("hides children text when loading", () => {
      render(<Button isLoading>Loading</Button>);
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });

    it("does not call onClick when loading", () => {
      const handleClick = vi.fn();
      render(
        <Button isLoading onClick={handleClick}>
          Loading
        </Button>
      );
      fireEvent.click(screen.getByRole("button"));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("icons", () => {
    it("renders left icon", () => {
      render(<Button leftIcon={<span data-testid="left-icon">L</span>}>With Icon</Button>);
      expect(screen.getByTestId("left-icon")).toBeInTheDocument();
    });

    it("renders right icon", () => {
      render(<Button rightIcon={<span data-testid="right-icon">R</span>}>With Icon</Button>);
      expect(screen.getByTestId("right-icon")).toBeInTheDocument();
    });
  });

  it("merges custom className", () => {
    render(<Button className="custom-class extra-class">Custom</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("custom-class");
    expect(btn.className).toContain("extra-class");
  });

  it("calls onClick when clicked", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("passes additional props to the button element", () => {
    render(
      <Button data-testid="custom-btn" aria-label="custom">
        Props
      </Button>
    );
    const btn = screen.getByTestId("custom-btn");
    expect(btn).toHaveAttribute("aria-label", "custom");
  });
});
