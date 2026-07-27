import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Divider } from "../components/ui/StyleComponents";

describe("Divider", () => {
  it("renders an hr element", () => {
    const { container } = render(<Divider />);
    expect(container.querySelector("hr")).toBeInTheDocument();
  });

  it("merges custom className", () => {
    const { container } = render(<Divider className="custom-divider" />);
    const hr = container.querySelector("hr");
    expect(hr.className).toContain("border-gray-700/50");
    expect(hr.className).toContain("my-4");
    expect(hr.className).toContain("custom-divider");
  });
});
