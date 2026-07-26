import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { StatusDot } from "./components";

describe("StatusDot", () => {
  it("renders a span", () => {
    const { container } = render(<StatusDot />);
    const el = container.querySelector("span");
    expect(el).toBeInTheDocument();
  });

  it("default status uses bg-gray-500", () => {
    const { container } = render(<StatusDot />);
    const el = container.querySelector("span");
    expect(el.className).toContain("bg-gray-500");
  });

  it("success status uses bg-green-500", () => {
    const { container } = render(<StatusDot status="success" />);
    const el = container.querySelector("span");
    expect(el.className).toContain("bg-green-500");
  });

  it("danger status uses bg-red-500", () => {
    const { container } = render(<StatusDot status="danger" />);
    const el = container.querySelector("span");
    expect(el.className).toContain("bg-red-500");
  });

  it("info status uses bg-cyan-500", () => {
    const { container } = render(<StatusDot status="info" />);
    const el = container.querySelector("span");
    expect(el.className).toContain("bg-cyan-500");
  });
});
