import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@services/aiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, getAIFeatures: vi.fn() };
});

const { getAIFeatures } = await import("@services/aiClient");
import { useAIFeatures } from "./useAIFeatures";

function wrapper({ children }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useAIFeatures", () => {
  beforeEach(() => vi.clearAllMocks());

  it("resolves flags from getAIFeatures", async () => {
    getAIFeatures.mockResolvedValue({
      investigate_agent_enabled: true,
      ml_isolation_forest_enabled: false,
    });
    const { result } = renderHook(() => useAIFeatures(), { wrapper });
    await waitFor(() =>
      expect(result.current.data).toEqual({
        investigate_agent_enabled: true,
        ml_isolation_forest_enabled: false,
      })
    );
    expect(result.current.isError).toBe(false);
  });

  it("surfaces fetch failure as isError", async () => {
    getAIFeatures.mockRejectedValue(new Error("features request failed (500)"));
    const { result } = renderHook(() => useAIFeatures(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
