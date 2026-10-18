import MLAnomaliesPanel from "../components/admin/MLAnomaliesPanel";

const ACTIVE_DATA = {
  recent_alerts: [
    {
      alert_id: "a1",
      anomaly_type: "severity_spike",
      severity: "CRITICAL",
      description: "Critical findings spiked 3x above the training baseline",
      timestamp: "2026-10-17 10:30:00",
    },
    {
      alert_id: "a2",
      anomaly_type: "frequency_anomaly",
      severity: "HIGH",
      description: "Scan frequency doubled within the trailing window",
      timestamp: "2026-10-16 09:00:00",
    },
  ],
  alert_statistics: { CRITICAL: 2, HIGH: 1 },
  active_model: {
    model_id: "iso-forest-4f2a91",
    model_type: "isolation_forest",
    training_data_size: 120,
    last_trained: "2026-10-18 08:00:00",
    anomaly_rate: 0.0833,
    score_mean: -0.0412,
    score_std: 0.0119,
  },
  total_recent_alerts: 3,
  anomaly_detection_status: "active",
};

export default {
  title: "Admin/MLAnomaliesPanel",
  component: MLAnomaliesPanel,
  decorators: [
    (Story) => (
      <div className="bg-gray-900 p-6">
        <Story />
      </div>
    ),
  ],
};

export const Active = {
  args: { data: ACTIVE_DATA },
};

export const EmptyActive = {
  args: { data: { ...ACTIVE_DATA, recent_alerts: [], total_recent_alerts: 0 } },
};

export const TrainingRequired = {
  args: {
    data: {
      recent_alerts: [],
      alert_statistics: {},
      active_model: null,
      total_recent_alerts: 0,
      anomaly_detection_status: "training_required",
    },
  },
};

export const Degraded = {
  args: {
    data: {
      recent_alerts: [],
      alert_statistics: {},
      active_model: null,
      total_recent_alerts: 0,
      anomaly_detection_status: "degraded",
      error: "no such table: anomaly_alerts",
    },
  },
};
