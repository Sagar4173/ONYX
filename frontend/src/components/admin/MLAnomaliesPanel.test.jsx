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
  alert_statistics: { CRITICAL: 4, HIGH: 2 },
  active_model: {
    model_id: "m1",
    model_type: "isolation_forest",
    training_data_size: 120,
    last_trained: "2026-10-18 08:00:00",
    anomaly_rate: 0.08,
    score_mean: -0.04,
    score_std: 0.01,
  },
  total_recent_alerts: 2,
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

  it("renders the not-trained empty state with the beaker icon", () => {
    const { container } = render(
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
    expect(container.querySelector("svg.h-12.w-12")).toBeInTheDocument();
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

  it("renders the labeled 30-day statistics and the 7-day count", () => {
    render(<MLAnomaliesPanel data={ACTIVE_DATA} />);

    expect(screen.getByText("2 alerts in the last 7 days")).toBeInTheDocument();
    expect(screen.getByText("Last 30 days")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL 4")).toBeInTheDocument();
    expect(screen.getByText("HIGH 2")).toBeInTheDocument();
  });

  it("discloses truncation when the total exceeds the returned list", () => {
    render(<MLAnomaliesPanel data={{ ...ACTIVE_DATA, total_recent_alerts: 23 }} />);

    expect(screen.getByText("Latest 2 of 23 alerts in the last 7 days")).toBeInTheDocument();
  });

  it("uses singular grammar for a single alert", () => {
    render(<MLAnomaliesPanel data={{ ...ACTIVE_DATA, total_recent_alerts: 1 }} />);

    expect(screen.getByText("1 alert in the last 7 days")).toBeInTheDocument();
    expect(screen.queryByText("1 alerts in the last 7 days")).not.toBeInTheDocument();
  });

  it("renders an empty state with the bell icon when there are no recent alerts", () => {
    const { container } = render(
      <MLAnomaliesPanel data={{ ...ACTIVE_DATA, recent_alerts: [], total_recent_alerts: 0 }} />
    );

    expect(screen.getByText("No anomalies detected in the last 7 days")).toBeInTheDocument();
    expect(container.querySelector("svg.h-12.w-12")).toBeInTheDocument();
  });
});
