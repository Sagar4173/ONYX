import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../../services/api", () => ({
  mlAPI: { train: vi.fn(), getStatus: vi.fn(), getAnomalies: vi.fn() },
}));
vi.mock("react-hot-toast", () => ({ default: { success: vi.fn(), error: vi.fn() } }));

import { mlAPI } from "../../services/api";
import toast from "react-hot-toast";
import MLTrainPanel from "./MLTrainPanel";

const baseStatus = {
  isolation_forest_enabled: true,
  min_training_scans: 30,
  training_window_days: 90,
  model_trained: false,
  sklearn_available: true,
  active_model: null,
};

const TRAIN_RESULT = {
  model_id: "m-1",
  training_data_size: 120,
  anomaly_rate: 0.0833,
  score_mean: -0.0412,
  score_std: 0.0119,
  last_trained: "2026-10-18T12:00:00Z",
};

const originalMatchMedia = window.matchMedia;

function renderPanel(status = baseStatus, client) {
  const qc =
    client ||
    new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
  return render(
    <QueryClientProvider client={qc}>
      <MLTrainPanel status={status} />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  window.matchMedia = vi.fn().mockImplementation((media) => ({
    matches: true,
    media,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
  }));
});

afterEach(() => {
  window.matchMedia = originalMatchMedia;
});

describe("MLTrainPanel", () => {
  it("disables training when isolation forest is off", () => {
    renderPanel({ ...baseStatus, isolation_forest_enabled: false });

    const button = screen.getByRole("button", { name: /train model/i });
    expect(button).toBeDisabled();
    expect(button.getAttribute("title")).toContain("ML_ISOLATION_FOREST_ENABLED");
  });

  it("disables training when scikit-learn is unavailable", () => {
    renderPanel({ ...baseStatus, sklearn_available: false });

    const button = screen.getByRole("button", { name: /train model/i });
    expect(button).toBeDisabled();
    expect(button.getAttribute("title")).toContain("scikit-learn");
  });

  it("calls the train endpoint when ready", async () => {
    mlAPI.train.mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: /train model/i }));

    expect(mlAPI.train).toHaveBeenCalledTimes(1);
  });

  it("shows a pending state while training", async () => {
    mlAPI.train.mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: /train model/i }));

    expect(await screen.findByText(/Training model/)).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("renders honest metrics after training", async () => {
    mlAPI.train.mockResolvedValue(TRAIN_RESULT);
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: /train model/i }));

    expect(await screen.findByText("8.33%")).toBeInTheDocument();
    expect(screen.getByText("-0.0412")).toBeInTheDocument();
    expect(screen.getByText("0.0119")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(toast.success).toHaveBeenCalled();
  });

  it("invalidates status and anomalies queries after success", async () => {
    mlAPI.train.mockResolvedValue(TRAIN_RESULT);
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(client, "invalidateQueries");
    const user = userEvent.setup();
    renderPanel(baseStatus, client);

    await user.click(screen.getByRole("button", { name: /train model/i }));

    await waitFor(() => expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["ml-status"] }));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["ml-anomalies"] });
  });

  it("explains a 409 gate instead of surfacing an error", async () => {
    mlAPI.train.mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "Training skipped: insufficient scan history or sklearn unavailable" },
      },
    });
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: /train model/i }));

    expect(await screen.findByText(/insufficient scan history/)).toBeInTheDocument();
    expect(screen.getByText(/30 scans within the last 90 days/)).toBeInTheDocument();
    expect(toast.error).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /train model/i })).toBeDisabled();
  });

  it("surfaces other failures and allows retry", async () => {
    mlAPI.train.mockRejectedValueOnce({
      response: { status: 500, data: { detail: "Boom" } },
    });
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: /train model/i }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Boom"));
    expect(screen.getByRole("button", { name: /train model/i })).toBeEnabled();
  });
});
