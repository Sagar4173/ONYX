import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, fireEvent } from "@testing-library/react";
import { useTriageShortcuts } from "./useTriageShortcuts";

function setup(enabled = true) {
  const onLabel = vi.fn();
  const onMove = vi.fn();
  const onToggleHelp = vi.fn();
  renderHook(() => useTriageShortcuts({ enabled, onLabel, onMove, onToggleHelp }));
  return { onLabel, onMove, onToggleHelp };
}

beforeEach(() => vi.clearAllMocks());

describe("useTriageShortcuts", () => {
  it("maps label and movement keys", () => {
    const { onLabel, onMove } = setup();
    fireEvent.keyDown(document, { key: "a" });
    fireEvent.keyDown(document, { key: "F" });
    fireEvent.keyDown(document, { key: "d" });
    fireEvent.keyDown(document, { key: "u" });
    fireEvent.keyDown(document, { key: "j" });
    fireEvent.keyDown(document, { key: "K" });
    expect(onLabel.mock.calls).toEqual([
      ["accepted"],
      ["false_positive"],
      ["dismissed"],
      ["untriaged"],
    ]);
    expect(onMove.mock.calls).toEqual([[1], [-1]]);
  });

  it("opens help on ?", () => {
    const { onToggleHelp } = setup();
    fireEvent.keyDown(document, { key: "?" });
    expect(onToggleHelp).toHaveBeenCalledTimes(1);
  });

  it("suppresses keys while typing and with modifiers", () => {
    const { onLabel, onMove } = setup();
    const input = document.createElement("input");
    document.body.appendChild(input);
    fireEvent.keyDown(input, { key: "a" });
    fireEvent.keyDown(document, { key: "j", ctrlKey: true });
    fireEvent.keyDown(document, { key: "j", metaKey: true });
    expect(onLabel).not.toHaveBeenCalled();
    expect(onMove).not.toHaveBeenCalled();
  });

  it("fires shortcuts while a checkbox input has focus", () => {
    const { onLabel } = setup();
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    document.body.appendChild(checkbox);
    fireEvent.keyDown(checkbox, { key: "a" });
    expect(onLabel).toHaveBeenCalledWith("accepted");
  });

  it("suppresses keys on a text input", () => {
    const { onLabel, onMove } = setup();
    const textInput = document.createElement("input");
    textInput.type = "text";
    document.body.appendChild(textInput);
    fireEvent.keyDown(textInput, { key: "a" });
    fireEvent.keyDown(textInput, { key: "j" });
    expect(onLabel).not.toHaveBeenCalled();
    expect(onMove).not.toHaveBeenCalled();
  });

  it("does nothing when disabled", () => {
    const { onLabel, onMove, onToggleHelp } = setup(false);
    fireEvent.keyDown(document, { key: "a" });
    fireEvent.keyDown(document, { key: "?" });
    expect(onLabel).not.toHaveBeenCalled();
    expect(onMove).not.toHaveBeenCalled();
    expect(onToggleHelp).not.toHaveBeenCalled();
  });
});
