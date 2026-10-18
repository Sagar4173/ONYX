import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../services/api", () => ({
  mlAPI: { train: vi.fn(), getStatus: vi.fn(), getAnomalies: vi.fn() },
}));
vi.mock("react-hot-toast", () => ({ default: { success: vi.fn(), error: vi.fn() } }));
vi.mock("../components/auth", async (importOriginal) => ({
  ...(await importOriginal()),
  useAuth: vi.fn(),
}));

import { mlAPI } from "../services/api";
import { useAuth } from "../components/auth";
import MLDashboard from "./MLDashboard";

const STATUS = {
  isolation_forest_enabled: true,
  min_training_scans: 30,
  training_window_days: 90,
  model_trained: true,
  sklearn_available: true,
  active_model: {
    model_id: "iso-forest-abc123",
    training_data_size: 120,
    anomaly_rate: 0.0833,
    last_trained: "2026-10-18T12:00:00Z",
  },
};

const ANOMALIES = {
  recent_alerts: [
    {
      alert_id: "a1",
      anomaly_type: "severity_spike",
      severity: "HIGH",
      description: "Spike detected",
      timestamp: "2026-10-17 10:30:00",
    },
  ],
  alert_statistics: { HIGH: 1 },
  active_model: null,
  total_recent_alerts: 1,
  anomaly_detection_status: "active",
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MemoryRouter initialEntries={["/admin/ml"]}>
      <QueryClientProvider client={client}>
        <MLDashboard />
      </QueryClientProvider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  useAuth.mockReturnValue({ user: { role: "admin" } });
  mlAPI.getStatus.mockResolvedValue(STATUS);
  mlAPI.getAnomalies.mockResolvedValue(ANOMALIES);
});

describe("MLDashboard", () => {
  it("blocks non-admins without calling the API", () => {
    useAuth.mockReturnValue({ user: { role: "analyst" } });

    renderPage();

    expect(screen.getByText("Admin Access Required")).toBeInTheDocument();
    expect(mlAPI.getStatus).not.toHaveBeenCalled();
    expect(mlAPI.getAnomalies).not.toHaveBeenCalled();
  });

  it("shows loading states while fetching", () => {
    mlAPI.getStatus.mockReturnValue(new Promise(() => {}));
    mlAPI.getAnomalies.mockReturnValue(new Promise(() => {}));

    renderPage();

    expect(screen.getByText("Loading ML status...")).toBeInTheDocument();
    expect(screen.getByText("Loading anomaly data...")).toBeInTheDocument();
  });

  it("renders status, training, and anomaly data for admins", async () => {
    renderPage();

    expect(await screen.findByText("Enabled")).toBeInTheDocument();
    expect(screen.getByText("Trained")).toBeInTheDocument();
    expect(screen.getByText("iso-forest-abc123")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /train model/i })).toBeEnabled();
    expect(screen.getByText("severity_spike")).toBeInTheDocument();
    expect(screen.getByText("1 alerts in the last 7 days")).toBeInTheDocument();
  });

  it("surfaces a status failure with retry that recovers", async () => {
    mlAPI.getStatus.mockRejectedValueOnce({
      response: { status: 500, data: { detail: "boom" } },
    });
    const user = userEvent.setup();

    renderPage();

    expect(await screen.findByText("Failed to load ML status")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(await screen.findByText("Enabled")).toBeInTheDocument();
    expect(mlAPI.getStatus).toHaveBeenCalledTimes(2);
  });

  it("isolates anomaly failures from the status panel", async () => {
    mlAPI.getAnomalies.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "Admin access required" } },
    });

    renderPage();

    expect(await screen.findByText("Failed to load anomaly data")).toBeInTheDocument();
    expect(screen.getByText("Enabled")).toBeInTheDocument();
  });

  it("renders the degraded anomaly state", async () => {
    mlAPI.getAnomalies.mockResolvedValue({
      recent_alerts: [],
      alert_statistics: {},
      active_model: null,
      total_recent_alerts: 0,
      anomaly_detection_status: "degraded",
      error: "no such table: anomaly_alerts",
    });

    renderPage();

    expect(await screen.findByText("Anomaly detection unavailable")).toBeInTheDocument();
    expect(screen.getByText("no such table: anomaly_alerts")).toBeInTheDocument();
  });
});
