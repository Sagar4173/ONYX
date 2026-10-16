import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MessageContent, parseSegments } from "./MessageContent";

const CITATIONS = [
  {
    n: 1,
    header: "CWE-89: SQL Injection",
    source: "cwe",
    source_id: "CWE-89",
    cwe_id: "89",
    text: "Use parameterized queries.",
  },
  {
    n: 2,
    header: "Remediation guidance",
    source: "guidance",
    source_id: "G-2",
    cwe_id: null,
    text: "Escape output.",
  },
];

describe("parseSegments", () => {
  it("turns streaming [[n]] markers into pending chips", () => {
    const segments = parseSegments("See [[2]] now.", null);
    expect(segments).toEqual([
      { type: "text", value: "See " },
      { type: "chip", n: 2, citation: null, pending: true },
      { type: "text", value: " now." },
    ]);
  });

  it("hydrates final [n] markers against citations", () => {
    const segments = parseSegments("See [1] and [2].", CITATIONS);
    expect(segments.filter((s) => s.type === "chip").map((s) => s.citation.header)).toEqual([
      "CWE-89: SQL Injection",
      "Remediation guidance",
    ]);
  });

  it("leaves unknown [n] as plain text", () => {
    const segments = parseSegments("See [9].", CITATIONS);
    expect(segments.every((s) => s.type === "text")).toBe(true);
    expect(segments.map((s) => s.value).join("")).toBe("See [9].");
  });
});

describe("MessageContent", () => {
  it("renders hydrated chips as buttons and streams pending chips", () => {
    render(<MessageContent text="See [[1]]." streaming citations={null} />);
    const chip = screen.getByRole("button", { name: /citation 1/i });
    expect(chip).toBeDisabled();

    const onClick = vi.fn();
    const { unmount } = render(
      <MessageContent text="See [1]." citations={CITATIONS} onCitationClick={onClick} />
    );
    unmount();
    render(<MessageContent text="See [1]." citations={CITATIONS} onCitationClick={onClick} />);
    fireEvent.click(screen.getByRole("button", { name: /CWE-89/i }));
    expect(onClick).toHaveBeenCalledWith(1, CITATIONS[0]);
  });

  it("shows caret while streaming", () => {
    const { container } = render(<MessageContent text="abc" streaming />);
    expect(container.querySelector('[aria-hidden="true"].animate-pulse')).toBeTruthy();
  });
});
