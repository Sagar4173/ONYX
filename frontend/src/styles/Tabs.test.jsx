import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Tabs } from "./components";

const tabs = [
  { id: "tab1", label: "Tab One" },
  { id: "tab2", label: "Tab Two", count: 5 },
  { id: "tab3", label: "Tab Three", icon: <span data-testid="tab-icon">I</span> },
];

describe("Tabs", () => {
  it("renders tab list with role='tablist'", () => {
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={() => {}} />);
    expect(screen.getByRole("tablist")).toBeInTheDocument();
  });

  it("each tab has role='tab' and aria-selected", () => {
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={() => {}} />);
    const tabElements = screen.getAllByRole("tab");
    expect(tabElements).toHaveLength(3);
    expect(tabElements[0]).toHaveAttribute("aria-selected", "true");
    expect(tabElements[1]).toHaveAttribute("aria-selected", "false");
    expect(tabElements[2]).toHaveAttribute("aria-selected", "false");
  });

  it("active tab gets selected styling", () => {
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={() => {}} />);
    const tabElements = screen.getAllByRole("tab");
    expect(tabElements[0].className).toContain("text-cyan-400");
    expect(tabElements[0].className).toContain("border-cyan-400");
    expect(tabElements[1].className).toContain("text-gray-400");
  });

  it("onChange fires with correct tab id", () => {
    const handleChange = vi.fn();
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={handleChange} />);
    fireEvent.click(screen.getByText("Tab Two"));
    expect(handleChange).toHaveBeenCalledWith("tab2");
  });

  it("count renders badge inside tab", () => {
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={() => {}} />);
    const tabTwo = screen.getByText("Tab Two").closest("button");
    expect(tabTwo.querySelector("span")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("icon is rendered when provided", () => {
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={() => {}} />);
    expect(screen.getByTestId("tab-icon")).toBeInTheDocument();
  });

  it("aria-controls attribute is set", () => {
    render(<Tabs tabs={tabs} activeTab="tab1" onChange={() => {}} />);
    const tabElements = screen.getAllByRole("tab");
    expect(tabElements[0]).toHaveAttribute("aria-controls", "tabpanel-tab1");
    expect(tabElements[1]).toHaveAttribute("aria-controls", "tabpanel-tab2");
    expect(tabElements[2]).toHaveAttribute("aria-controls", "tabpanel-tab3");
  });
});
