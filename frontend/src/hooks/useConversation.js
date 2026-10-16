import { useCallback, useSyncExternalStore } from "react";

const stores = new Map();
let seq = 0;

function getStore(scanId) {
  if (!stores.has(scanId)) {
    stores.set(scanId, { messages: [], listeners: new Set() });
  }
  return stores.get(scanId);
}

function notify(store) {
  store.listeners.forEach((listener) => listener());
}

export function useConversation(scanId) {
  const store = getStore(scanId);

  const subscribe = useCallback(
    (listener) => {
      store.listeners.add(listener);
      return () => store.listeners.delete(listener);
    },
    [store]
  );
  const getSnapshot = useCallback(() => store.messages, [store]);
  const messages = useSyncExternalStore(subscribe, getSnapshot);

  const update = useCallback(
    (fn) => {
      store.messages = fn(store.messages);
      notify(store);
    },
    [store]
  );

  const mapMessage = useCallback(
    (id, patch) => {
      update((list) => list.map((m) => (m.id === id ? { ...m, ...patch(m) } : m)));
    },
    [update]
  );

  return {
    messages,
    pushUser: (content) => {
      seq += 1;
      update((list) => [...list, { id: `u-${seq}`, role: "user", content }]);
    },
    beginAssistant: () => {
      seq += 1;
      const id = seq;
      update((list) => [
        ...list,
        {
          id,
          role: "assistant",
          streaming: true,
          text: "",
          citations: null,
          model: null,
          isError: false,
        },
      ]);
      return id;
    },
    appendDelta: (id, text) => mapMessage(id, (m) => ({ text: m.text + text })),
    finishAssistant: (id, { reply, citations, model_used }) =>
      mapMessage(id, (m) =>
        m.streaming
          ? { streaming: false, text: reply, content: reply, citations, model: model_used }
          : m
      ),
    settleAssistant: (id) =>
      mapMessage(id, (m) =>
        m.streaming
          ? { streaming: false, partial: true, ...(m.text ? { content: m.text } : {}) }
          : m
      ),
    failAssistant: (id, detail) =>
      mapMessage(id, () => ({ streaming: false, isError: true, content: detail })),
    removeMessage: (id) => update((list) => list.filter((m) => m.id !== id)),
    getMessage: (id) => store.messages.find((m) => m.id === id),
    clear: () => update(() => []),
  };
}
