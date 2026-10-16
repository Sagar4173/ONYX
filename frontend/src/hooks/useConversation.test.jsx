import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useConversation } from "./useConversation";

describe("useConversation", () => {
  it("streams a message end-to-end and isolates stores per scan", () => {
    const { result } = renderHook(() => useConversation("scan-A"));
    const { result: other } = renderHook(() => useConversation("scan-B"));

    act(() => result.current.pushUser("hello"));
    let id;
    act(() => {
      id = result.current.beginAssistant();
    });
    act(() => result.current.appendDelta(id, "wor"));
    act(() => result.current.appendDelta(id, "ld"));

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1]).toMatchObject({ streaming: true, text: "world" });
    expect(other.current.messages).toHaveLength(0);

    act(() =>
      result.current.finishAssistant(id, { reply: "world", citations: [{ n: 1 }], model_used: "m" })
    );
    expect(result.current.messages[1]).toMatchObject({
      streaming: false,
      content: "world",
      model: "m",
    });
    expect(result.current.messages[1].citations).toEqual([{ n: 1 }]);
  });

  it("settleAssistant keeps partial text and is idempotent", () => {
    const { result } = renderHook(() => useConversation("scan-partial"));
    let id;
    act(() => {
      id = result.current.beginAssistant();
    });
    act(() => result.current.appendDelta(id, "half an answer"));
    act(() => result.current.settleAssistant(id));
    act(() => result.current.settleAssistant(id));
    const msg = result.current.getMessage(id);
    expect(msg).toMatchObject({ streaming: false, partial: true, content: "half an answer" });
  });

  it("finishAssistant after settle does not clobber", () => {
    const { result } = renderHook(() => useConversation("scan-race"));
    let id;
    act(() => {
      id = result.current.beginAssistant();
    });
    act(() => result.current.settleAssistant(id));
    act(() =>
      result.current.finishAssistant(id, { reply: "full", citations: [], model_used: "m" })
    );
    expect(result.current.getMessage(id).content).toBeUndefined();
  });

  it("failAssistant marks error; removeMessage drops; clear empties", () => {
    const { result } = renderHook(() => useConversation("scan-fail"));
    act(() => result.current.pushUser("q"));
    let id;
    act(() => {
      id = result.current.beginAssistant();
    });
    act(() => result.current.failAssistant(id, "boom"));
    expect(result.current.getMessage(id)).toMatchObject({
      isError: true,
      content: "boom",
      streaming: false,
    });
    act(() => result.current.removeMessage(id));
    expect(result.current.messages).toHaveLength(1);
    act(() => result.current.clear());
    expect(result.current.messages).toHaveLength(0);
  });
});
