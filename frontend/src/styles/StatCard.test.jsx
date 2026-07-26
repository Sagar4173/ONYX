import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatCard } from "./components";

describe("StatCard", () => {
  it("renders title and value", () => {
    render(<StatCard title="Total Scans" value="1,234" />);
    expect(screen.getByText("Total Scans")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
  });

  it("renders icon", () => {
    render(<StatCard title="Data" value="10" icon={<span data-testid="card-icon">📊</span>} />);
    expect(screen.getByTestId("card-icon")).toBeInTheDocument();
  });

  it("renders change text", () => {
    render(<StatCard title="Users" value="500" change="+12%" />);
    expect(screen.getByText("+12%")).toBeInTheDocument();
  });

  it("renders gradient mode layout when gradient prop is provided", () => {
    render(<StatCard title="GPU" value="89%" gradient="from-cyan-500 to-violet-500" />);
    const title = screen.getByText("GPU");
    expect(title.className).toContain("text-sm");
    expect(title.className).toContain("text-gray-400");
  });

  it("renders trend badge with arrow in gradient mode", () => {
    render(
      <StatCard title="Revenue" value="$10k" trend={15} gradient="from-cyan-500 to-violet-500" />
    );
    expect(document.querySelector(".text-green-400")).toBeInTheDocument();
  });

  it("renders trend badge with negative arrow", () => {
    render(<StatCard title="Errors" value="5" trend={-5} gradient="from-cyan-500 to-violet-500" />);
    expect(document.querySelector(".text-red-400")).toBeInTheDocument();
  });

  it("renders as clickable in gradient mode when onClick is provided", () => {
    render(
      <StatCard
        title="Clickable"
        value="42"
        gradient="from-cyan-500 to-violet-500"
        onClick={() => {}}
      />
    );
    const el = screen.getByText("Clickable").closest("[class*='cursor-pointer']");
    expect(el).toBeTruthy();
  });

  it("merges custom className", () => {
    render(<StatCard title="Custom" value="1" className="my-card" />);
    const el = screen.getByText("Custom").closest("[class*='rounded-xl']");
    expect(el.className).toContain("my-card");
  });
});
