import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MLStatusPanel from "./MLStatusPanel";

const baseStatus = {
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

describe("MLStatusPanel", () => {
  it("shows enabled flag states and the training gate line", () => {
    render(<MLStatusPanel status={baseStatus} />);

    expect(screen.getByText("Enabled")).toBeInTheDocument();
    expect(screen.getByText("Available")).toBeInTheDocument();
    expect(screen.getByText("Trained")).toBeInTheDocument();
    expect(
      screen.getByText(/Minimum 30 scans within the last 90 days required to train/)
    ).toBeInTheDocument();
  });

  it("shows disabled flag states", () => {
    render(
      <MLStatusPanel
        status={{
          ...baseStatus,
          isolation_forest_enabled: false,
          sklearn_available: false,
          model_trained: false,
          active_model: null,
        }}
      />
    );

    expect(screen.getByText("Disabled")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.getByText("Not trained")).toBeInTheDocument();
  });

  it("renders the active model summary with formatted anomaly rate", () => {
    render(<MLStatusPanel status={baseStatus} />);

    expect(screen.getByText("iso-forest-abc123")).toBeInTheDocument();
    expect(screen.getByText("120 scans")).toBeInTheDocument();
    expect(screen.getByText("8.33%")).toBeInTheDocument();
    expect(
      screen.getByText(new Date(baseStatus.active_model.last_trained).toLocaleString())
    ).toBeInTheDocument();
  });

  it("shows an empty state with the beaker icon when no model is trained", () => {
    const { container } = render(
      <MLStatusPanel status={{ ...baseStatus, model_trained: false, active_model: null }} />
    );

    expect(screen.getByText("No model trained yet")).toBeInTheDocument();
    expect(container.querySelector("svg.h-12.w-12")).toBeInTheDocument();
  });

  it("documents the persisted model lifecycle", () => {
    render(<MLStatusPanel status={baseStatus} />);

    expect(
      screen.getByText(
        /The trained model is saved and reloaded on backend restart; retrain to incorporate new scan data\./
      )
    ).toBeInTheDocument();
  });
});
