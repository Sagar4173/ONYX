import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CitationPanel } from "./CitationPanel";

const CITATION = {
  n: 1,
  header: "CWE-89: SQL Injection",
  source: "cwe",
  source_id: "CWE-89",
  cwe_id: "89",
  text: "Use parameterized queries.",
};

describe("CitationPanel", () => {
  it("renders citation body and closes via onClose", () => {
    const onClose = vi.fn();
    render(<CitationPanel isOpen onClose={onClose} n={1} citation={CITATION} />);
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText(/CWE-89: SQL Injection/)).toBeInTheDocument();
    expect(screen.getByText("Use parameterized queries.")).toBeInTheDocument();
    expect(screen.getByText("CWE-89")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("handles missing citation gracefully", () => {
    render(<CitationPanel isOpen onClose={() => {}} n={3} citation={null} />);
    expect(screen.getByText("No source text available.")).toBeInTheDocument();
  });
});
