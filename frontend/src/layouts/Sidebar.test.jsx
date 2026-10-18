import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../components/auth", async (importOriginal) => ({
  ...(await importOriginal()),
  useAuth: vi.fn(),
}));

import { useAuth } from "../components/auth";
import Sidebar from "./Sidebar";

function renderSidebar(role, path = "/admin/ml") {
  useAuth.mockReturnValue({ user: { role } });
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar collapsed={false} onToggle={vi.fn()} mobileOpen={false} onMobileClose={vi.fn()} />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Sidebar administration navigation", () => {
  it("shows the ML Dashboard link for admins", () => {
    renderSidebar("admin");

    expect(screen.getByText("ML Dashboard")).toBeInTheDocument();
    expect(screen.getByText("ML Dashboard").closest("a")).toHaveAttribute("href", "/admin/ml");
  });

  it("hides the ML Dashboard link for non-admins", () => {
    renderSidebar("analyst");

    expect(screen.queryByText("ML Dashboard")).not.toBeInTheDocument();
    expect(screen.queryByText("Admin Panel")).not.toBeInTheDocument();
  });

  it("highlights only the ML Dashboard on /admin/ml", () => {
    renderSidebar("admin");

    const active = screen
      .getAllByRole("link")
      .filter((el) => el.getAttribute("aria-current") === "page");

    expect(active).toHaveLength(1);
    expect(active[0]).toHaveTextContent("ML Dashboard");
  });
});
