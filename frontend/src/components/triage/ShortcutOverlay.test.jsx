import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ShortcutOverlay, KeyboardHintStrip } from "./ShortcutOverlay";

describe("ShortcutOverlay", () => {
  it("lists the triage keys in a dialog and closes on Escape", () => {
    const onClose = vi.fn();
    render(<ShortcutOverlay isOpen onClose={onClose} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Triage shortcuts")).toBeInTheDocument();
    expect(screen.getByText("Next / previous finding")).toBeInTheDocument();
    expect(screen.getByText("Accept (mark true positive)")).toBeInTheDocument();
    expect(screen.getByText("Untriage (clear your label)")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("renders nothing when closed", () => {
    render(<ShortcutOverlay isOpen={false} onClose={vi.fn()} />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("KeyboardHintStrip", () => {
  it("shows the discoverable hint line", () => {
    render(<KeyboardHintStrip />);
    expect(
      screen.getByText(
        /J\/K move · A accept · F false positive · D dismiss · U untriage · \? shortcuts/
      )
    ).toBeInTheDocument();
  });
});
