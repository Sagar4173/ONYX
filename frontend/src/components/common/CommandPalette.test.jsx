import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../../services/api", () => ({
  projectsAPI: { list: vi.fn() },
}));

import { projectsAPI } from "../../services/api";
import { CommandPalette } from "./CommandPalette";

function renderPalette() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <CommandPalette isOpen onClose={vi.fn()} />
      </QueryClientProvider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  projectsAPI.list.mockResolvedValue({ data: { projects: [] } });
});

describe("CommandPalette navigation actions", () => {
  it("offers navigation to the ML Dashboard", async () => {
    renderPalette();

    expect(await screen.findByText("Go to ML Dashboard")).toBeInTheDocument();
  });
});
