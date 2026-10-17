import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRowSelection } from "./useRowSelection";

const IDS = ["f1", "f2", "f3", "f4"];

describe("useRowSelection", () => {
  it("toggles single rows", () => {
    const { result } = renderHook(() => useRowSelection());
    act(() => result.current.toggle("f2"));
    expect(result.current.isSelected("f2")).toBe(true);
    expect(result.current.count).toBe(1);
    act(() => result.current.toggle("f2"));
    expect(result.current.count).toBe(0);
  });

  it("extends a range on shift-click from the anchor", () => {
    const { result } = renderHook(() => useRowSelection());
    act(() => result.current.toggle("f2", { orderedIds: IDS }));
    act(() => result.current.toggle("f4", { shift: true, orderedIds: IDS }));
    expect([...result.current.selectedIds].sort()).toEqual(["f2", "f3", "f4"]);
    act(() => result.current.toggle("f1", { shift: true, orderedIds: IDS }));
    expect(result.current.count).toBe(4);
  });

  it("clears everything", () => {
    const { result } = renderHook(() => useRowSelection());
    act(() => result.current.toggle("f1"));
    act(() => result.current.clear());
    expect(result.current.count).toBe(0);
  });
});
