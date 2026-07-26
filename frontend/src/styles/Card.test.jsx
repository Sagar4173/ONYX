import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./components";

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Content</Card>);
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("renders as a div", () => {
    render(<Card>Div</Card>);
    expect(screen.getByText("Div").tagName).toBe("DIV");
  });

  it("applies base card classes", () => {
    render(<Card>Base</Card>);
    const el = screen.getByText("Base");
    expect(el.className).toContain("rounded-xl");
    expect(el.className).toContain("border");
    expect(el.className).toContain("backdrop-blur-sm");
  });

  it("applies default variant", () => {
    render(<Card>Default</Card>);
    const el = screen.getByText("Default");
    expect(el.className).toContain("bg-gray-800/50");
    expect(el.className).toContain("border-gray-700/50");
  });

  it("applies elevated variant", () => {
    render(<Card variant="elevated">Elevated</Card>);
    const el = screen.getByText("Elevated");
    expect(el.className).toContain("shadow-lg");
    expect(el.className).toContain("bg-gray-800/70");
  });

  it("applies padding sizes", () => {
    const { rerender } = render(<Card padding="sm">SM</Card>);
    expect(screen.getByText("SM").className).toContain("p-3");

    rerender(<Card padding="lg">LG</Card>);
    expect(screen.getByText("LG").className).toContain("p-6");
  });

  it("applies hoverable classes", () => {
    render(<Card hoverable>Hover</Card>);
    const el = screen.getByText("Hover");
    expect(el.className).toContain("hover:bg-gray-700/50");
    expect(el.className).toContain("hover:-translate-y-0.5");
  });

  it("merges custom className", () => {
    render(<Card className="custom-class">Custom</Card>);
    expect(screen.getByText("Custom").className).toContain("custom-class");
  });
});

describe("CardHeader", () => {
  it("renders children", () => {
    render(<CardHeader>Header</CardHeader>);
    const el = screen.getByText("Header");
    expect(el).toBeInTheDocument();
    expect(el.className).toContain("border-b");
  });
});

describe("CardTitle", () => {
  it("renders as h3", () => {
    render(<CardTitle>Title</CardTitle>);
    const el = screen.getByText("Title");
    expect(el.tagName).toBe("H3");
    expect(el.className).toContain("text-lg");
    expect(el.className).toContain("font-semibold");
  });
});

describe("CardDescription", () => {
  it("renders description text", () => {
    render(<CardDescription>Desc</CardDescription>);
    const el = screen.getByText("Desc");
    expect(el.className).toContain("text-sm");
    expect(el.className).toContain("text-gray-400");
  });
});

describe("CardContent", () => {
  it("renders children with custom className", () => {
    render(<CardContent className="p-4">Content</CardContent>);
    expect(screen.getByText("Content").className).toContain("p-4");
  });
});

describe("CardFooter", () => {
  it("renders children", () => {
    render(<CardFooter>Footer</CardFooter>);
    const el = screen.getByText("Footer");
    expect(el).toBeInTheDocument();
    expect(el.className).toContain("border-t");
  });
});
