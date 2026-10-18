import MLStatusPanel from "../components/admin/MLStatusPanel";

const DISABLED_STATUS = {
  isolation_forest_enabled: false,
  min_training_scans: 30,
  training_window_days: 90,
  model_trained: false,
  sklearn_available: false,
  active_model: null,
};

const READY_STATUS = {
  isolation_forest_enabled: true,
  min_training_scans: 30,
  training_window_days: 90,
  model_trained: false,
  sklearn_available: true,
  active_model: null,
};

const TRAINED_STATUS = {
  ...READY_STATUS,
  model_trained: true,
  active_model: {
    model_id: "iso-forest-4f2a91",
    training_data_size: 120,
    anomaly_rate: 0.0833,
    last_trained: "2026-10-18T12:00:00Z",
  },
};

export default {
  title: "Admin/MLStatusPanel",
  component: MLStatusPanel,
  decorators: [
    (Story) => (
      <div className="bg-gray-900 p-6">
        <Story />
      </div>
    ),
  ],
};

export const Disabled = {
  args: { status: DISABLED_STATUS },
};

export const Ready = {
  args: { status: READY_STATUS },
};

export const Trained = {
  args: { status: TRAINED_STATUS },
};
