import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Modal } from "../components/ui/StyleComponents";

describe("Modal", () => {
  it("returns null when isOpen is false", () => {
    const { container } = render(<Modal isOpen={false} onClose={() => {}} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders dialog when isOpen is true", () => {
    render(
      <Modal isOpen={true} onClose={() => {}}>
        Content
      </Modal>
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("renders children in the body", () => {
    render(
      <Modal isOpen={true} onClose={() => {}}>
        Hello World
      </Modal>
    );
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("renders title and close button when title is provided", () => {
    render(<Modal isOpen={true} onClose={() => {}} title="My Title" />);
    expect(screen.getByText("My Title")).toBeInTheDocument();
    expect(screen.getByLabelText("Close dialog")).toBeInTheDocument();
  });

  it("renders footer when footer prop is provided", () => {
    render(<Modal isOpen={true} onClose={() => {}} footer={<span>Footer</span>} />);
    expect(screen.getByText("Footer")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(<Modal isOpen={true} onClose={onClose} title="Title" />);
    fireEvent.click(screen.getByLabelText("Close dialog"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when overlay is clicked", () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose}>
        Content
      </Modal>
    );
    const dialog = screen.getByRole("dialog");
    const overlay = dialog.parentElement;
    fireEvent.click(overlay);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not call onClose when inner container is clicked", () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose}>
        Content
      </Modal>
    );
    fireEvent.click(screen.getByRole("dialog"));
    expect(onClose).not.toHaveBeenCalled();
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(<Modal isOpen={true} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("applies size class", () => {
    render(<Modal isOpen={true} onClose={() => {}} size="sm" />);
    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toContain("max-w-sm");
  });

  it("applies large size class", () => {
    render(<Modal isOpen={true} onClose={() => {}} size="xl" />);
    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toContain("max-w-4xl");
  });

  it("links title via aria-labelledby", () => {
    render(<Modal isOpen={true} onClose={() => {}} title="Accessible" />);
    const dialog = screen.getByRole("dialog");
    const titleId = dialog.getAttribute("aria-labelledby");
    expect(titleId).toBeTruthy();
    expect(document.getElementById(titleId)).toHaveTextContent("Accessible");
  });
});
