import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Tooltip } from "../components/ui/StyleComponents";

describe("Tooltip", () => {
  it("children are rendered", () => {
    render(
      <Tooltip content="tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    expect(screen.getByRole("button", { name: /hover me/i })).toBeInTheDocument();
  });

  it("tooltip not visible by default", () => {
    render(
      <Tooltip content="tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("on mouse enter, tooltip appears with role='tooltip'", () => {
    render(
      <Tooltip content="tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    const wrapper = screen.getByRole("button").closest("div");
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    expect(screen.getByText("tooltip content")).toBeInTheDocument();
  });

  it("on mouse leave, tooltip disappears", async () => {
    render(
      <Tooltip content="tooltip content">
        <button>Hover me</button>
      </Tooltip>
    );
    const wrapper = screen.getByRole("button").closest("div");
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    fireEvent.mouseLeave(wrapper);
    await waitFor(() => expect(screen.queryByRole("tooltip")).not.toBeInTheDocument(), {
      timeout: 1000,
    });
  });

  it("position prop applies correct positioning classes", () => {
    render(
      <Tooltip content="tooltip content" position="bottom">
        <button>Hover me</button>
      </Tooltip>
    );
    const wrapper = screen.getByRole("button").closest("div");
    fireEvent.mouseEnter(wrapper);
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip.className).toContain("top-full");
    expect(tooltip.className).toContain("mt-2");
  });

  it("tooltip content is rendered", () => {
    render(
      <Tooltip content="Helpful description">
        <button>Hover me</button>
      </Tooltip>
    );
    const wrapper = screen.getByRole("button").closest("div");
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByText("Helpful description")).toBeInTheDocument();
  });
});
