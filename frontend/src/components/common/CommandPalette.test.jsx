import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../../services/api", () => ({
  projectsAPI: { list: vi.fn() },
}));

import { projectsAPI } from "../../services/api";
import { CommandPalette } from "./CommandPalette";

const LocationProbe = () => {
  const location = useLocation();
  return <span data-testid="location">{location.pathname}</span>;
};

function renderPalette(onClose = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const utils = render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <CommandPalette isOpen onClose={onClose} />
        <Routes>
          <Route path="*" element={<LocationProbe />} />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>
  );
  return { ...utils, onClose };
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

  it("navigates to the ML Dashboard and closes on selection", async () => {
    const user = userEvent.setup();
    const { onClose } = renderPalette();

    await user.click(await screen.findByText("Go to ML Dashboard"));

    expect(screen.getByTestId("location")).toHaveTextContent("/admin/ml");
    expect(onClose).toHaveBeenCalled();
  });
});
