import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@services/aiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, runInvestigate: vi.fn() };
});

import { runInvestigate } from "@services/aiClient";
import { useInvestigate } from "./useInvestigate";

const ENVELOPE = {
  report: { finding_id: "f-1", summary: "blast radius", evidence: [] },
  provider: "groq",
  model: "llama-3.3-70b",
  usage: { prompt_tokens: 5, completion_tokens: 7, requests: 1 },
};

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function makeWrapper(client) {
  const Wrapper = ({ children }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return Wrapper;
}

beforeEach(() => {
  vi.clearAllMocks();
  runInvestigate.mockResolvedValue(ENVELOPE);
});

describe("useInvestigate", () => {
  it("stays idle until a question is submitted", () => {
    const client = makeQueryClient();
    renderHook(() => useInvestigate({ scanId: "s1", findingId: "f-1", question: null }), {
      wrapper: makeWrapper(client),
    });

    expect(runInvestigate).not.toHaveBeenCalled();
  });

  it("runs with an empty question string", async () => {
    const client = makeQueryClient();
    const { result } = renderHook(
      () => useInvestigate({ scanId: "s1", findingId: "f-1", question: "" }),
      { wrapper: makeWrapper(client) }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(runInvestigate).toHaveBeenCalledWith({ scanId: "s1", findingId: "f-1", question: "" });
  });

  it("fetches per (scan, finding, question) key", async () => {
    const client = makeQueryClient();
    const { result, rerender } = renderHook(
      ({ question }) => useInvestigate({ scanId: "s1", findingId: "f-1", question }),
      { wrapper: makeWrapper(client), initialProps: { question: "" } }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    rerender({ question: "why?" });

    await waitFor(() => expect(runInvestigate).toHaveBeenCalledTimes(2));
    expect(runInvestigate).toHaveBeenLastCalledWith({
      scanId: "s1",
      findingId: "f-1",
      question: "why?",
    });
  });

  it("does not refetch a cached question on remount", async () => {
    const client = makeQueryClient();
    const wrapper = makeWrapper(client);
    const options = { wrapper };

    const first = renderHook(
      () => useInvestigate({ scanId: "s1", findingId: "f-1", question: "" }),
      options
    );
    await waitFor(() => expect(first.result.current.isSuccess).toBe(true));
    first.unmount();

    const second = renderHook(
      () => useInvestigate({ scanId: "s1", findingId: "f-1", question: "" }),
      options
    );
    await waitFor(() => expect(second.result.current.isSuccess).toBe(true));

    expect(runInvestigate).toHaveBeenCalledTimes(1);
  });

  it("never polls even when the app client defaults to refetchInterval", async () => {
    vi.useFakeTimers();
    try {
      const client = new QueryClient({
        defaultOptions: { queries: { retry: false, refetchInterval: 30000 } },
      });
      renderHook(() => useInvestigate({ scanId: "s1", findingId: "f-1", question: "" }), {
        wrapper: makeWrapper(client),
      });

      await vi.advanceTimersByTimeAsync(0);
      expect(runInvestigate).toHaveBeenCalledTimes(1);

      await vi.advanceTimersByTimeAsync(90000);
      expect(runInvestigate).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });
});
