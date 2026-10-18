import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MLAnomaliesPanel from "./MLAnomaliesPanel";

const ACTIVE_DATA = {
  recent_alerts: [
    {
      alert_id: "a1",
      anomaly_type: "severity_spike",
      severity: "CRITICAL",
      description: "Critical findings spiked 3x",
      timestamp: "2026-10-17 10:30:00",
    },
    {
      alert_id: "a2",
      anomaly_type: "frequency_anomaly",
      severity: "HIGH",
      description: "Scan frequency doubled",
      timestamp: "2026-10-16 09:00:00",
    },
  ],
  alert_statistics: { CRITICAL: 2, HIGH: 1 },
  active_model: {
    model_id: "m1",
    model_type: "isolation_forest",
    training_data_size: 120,
    last_trained: "2026-10-18 08:00:00",
    anomaly_rate: 0.08,
    score_mean: -0.04,
    score_std: 0.01,
  },
  total_recent_alerts: 3,
  anomaly_detection_status: "active",
};

describe("MLAnomaliesPanel", () => {
  it("renders the degraded state with the error detail", () => {
    render(
      <MLAnomaliesPanel
        data={{
          recent_alerts: [],
          alert_statistics: {},
          active_model: null,
          total_recent_alerts: 0,
          anomaly_detection_status: "degraded",
          error: "no such table: anomaly_alerts",
        }}
      />
    );

    expect(screen.getByText("Anomaly detection unavailable")).toBeInTheDocument();
    expect(screen.getByText("no such table: anomaly_alerts")).toBeInTheDocument();
  });

  it("renders the not-trained empty state", () => {
    render(
      <MLAnomaliesPanel
        data={{
          recent_alerts: [],
          alert_statistics: {},
          active_model: null,
          total_recent_alerts: 0,
          anomaly_detection_status: "training_required",
        }}
      />
    );

    expect(screen.getByText("No model trained yet")).toBeInTheDocument();
    expect(screen.getByText("Train a model to enable anomaly alerts.")).toBeInTheDocument();
  });

  it("renders alert rows with severity, type, description, and timestamp", () => {
    render(<MLAnomaliesPanel data={ACTIVE_DATA} />);

    expect(screen.getByText("severity_spike")).toBeInTheDocument();
    expect(screen.getByText("Critical findings spiked 3x")).toBeInTheDocument();
    expect(screen.getByText("frequency_anomaly")).toBeInTheDocument();
    expect(screen.getByText("Scan frequency doubled")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText(new Date("2026-10-17 10:30:00").toLocaleString())).toBeInTheDocument();
  });

  it("renders the statistics and total count", () => {
    render(<MLAnomaliesPanel data={ACTIVE_DATA} />);

    expect(screen.getByText("3 alerts in the last 7 days")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL 2")).toBeInTheDocument();
    expect(screen.getByText("HIGH 1")).toBeInTheDocument();
  });

  it("renders an empty state when there are no recent alerts", () => {
    render(
      <MLAnomaliesPanel data={{ ...ACTIVE_DATA, recent_alerts: [], total_recent_alerts: 0 }} />
    );

    expect(screen.getByText("No anomalies detected in the last 7 days")).toBeInTheDocument();
  });
});
