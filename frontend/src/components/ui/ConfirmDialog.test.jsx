import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConfirmDialog } from "./StyleComponents";

describe("ConfirmDialog", () => {
  it("returns null when isOpen is false", () => {
    const { container } = render(<ConfirmDialog isOpen={false} onClose={() => {}} />);
    expect(container.innerHTML).toBe("");
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(<ConfirmDialog isOpen onClose={onClose} onConfirm={() => {}} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("wraps Tab focus within the dialog", () => {
    render(<ConfirmDialog isOpen onClose={() => {}} onConfirm={() => {}} confirmLabel="Do it" />);
    const cancel = screen.getByRole("button", { name: "Cancel" });
    const confirm = screen.getByRole("button", { name: "Do it" });

    confirm.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(cancel);

    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(confirm);
  });

  it("focuses the first focusable when opened without an autofocused input", () => {
    render(<ConfirmDialog isOpen onClose={() => {}} onConfirm={() => {}} />);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Cancel" }));
  });

  it("keeps focus on the type-to-confirm input when opened", () => {
    render(
      <ConfirmDialog
        isOpen
        onClose={() => {}}
        onConfirm={() => {}}
        requireTypeToConfirm
        confirmText="APPROVE"
        confirmLabel="Open pull request"
      />
    );
    expect(document.activeElement).toBe(screen.getByRole("textbox"));
  });

  it("disables confirm until the exact text is typed", () => {
    render(
      <ConfirmDialog
        isOpen
        onClose={() => {}}
        onConfirm={() => {}}
        requireTypeToConfirm
        confirmText="APPROVE"
        confirmLabel="Open pull request"
      />
    );
    const confirm = screen.getByRole("button", { name: "Open pull request" });
    expect(confirm).toBeDisabled();

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "APPROV" } });
    expect(confirm).toBeDisabled();

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "APPROVE" } });
    expect(confirm).toBeEnabled();
  });

  it("restores focus to the previously focused element on close", () => {
    function Harness() {
      const [open, setOpen] = React.useState(false);
      return (
        <>
          <button onClick={() => setOpen(true)}>open</button>
          <ConfirmDialog isOpen={open} onClose={() => setOpen(false)} onConfirm={() => {}} />
        </>
      );
    }
    render(<Harness />);
    const opener = screen.getByRole("button", { name: "open" });
    opener.focus();
    fireEvent.click(opener);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Cancel" }));

    fireEvent.keyDown(document, { key: "Escape" });
    expect(document.activeElement).toBe(opener);
  });
});
