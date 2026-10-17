import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LabelControls } from "./LabelControls";

describe("LabelControls", () => {
  it("renders the three label actions and reports selection", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelControls onChange={onChange} />);

    await user.click(screen.getByRole("button", { name: "Label as Accept" }));
    expect(onChange).toHaveBeenCalledWith("accepted");
    await user.click(screen.getByRole("button", { name: "Label as False positive" }));
    expect(onChange).toHaveBeenCalledWith("false_positive");
    await user.click(screen.getByRole("button", { name: "Label as Dismissed" }));
    expect(onChange).toHaveBeenCalledWith("dismissed");
  });

  it("shows current label, offers Untriage, and toggles via the active button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelControls value="accepted" onChange={onChange} />);

    expect(screen.getByRole("button", { name: "Your label: Accepted" })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
    expect(screen.getByText("Your label: Accepted")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Untriage" }));
    expect(onChange).toHaveBeenCalledWith("untriaged");

    await user.click(screen.getByRole("button", { name: "Your label: Accepted" }));
    expect(onChange).toHaveBeenLastCalledWith("untriaged");
  });

  it("renders a compact icon row with accessible names", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelControls compact value="dismissed" onChange={onChange} />);

    const active = screen.getByRole("button", { name: "Your label: Dismissed" });
    expect(active).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("button", { name: "Untriage" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Label as Accept" }));
    expect(onChange).toHaveBeenCalledWith("accepted");
  });

  it("ignores interaction while disabled", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelControls disabled onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: "Label as Accept" }));
    expect(onChange).not.toHaveBeenCalled();
  });
});
