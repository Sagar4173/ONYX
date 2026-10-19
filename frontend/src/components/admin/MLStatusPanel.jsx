import { MetricCard, EmptyState } from "../ui/StyleComponents";
import { BeakerIcon, CpuChipIcon, ServerStackIcon } from "@heroicons/react/24/outline";

const MLStatusPanel = ({ status }) => {
  const model = status.active_model;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <MetricCard
          title="Isolation Forest"
          value={status.isolation_forest_enabled ? "Enabled" : "Disabled"}
          icon={ServerStackIcon}
          color={status.isolation_forest_enabled ? "green" : "red"}
        />
        <MetricCard
          title="scikit-learn"
          value={status.sklearn_available ? "Available" : "Unavailable"}
          icon={CpuChipIcon}
          color={status.sklearn_available ? "green" : "red"}
        />
        <MetricCard
          title="Model"
          value={status.model_trained ? "Trained" : "Not trained"}
          icon={BeakerIcon}
          color={status.model_trained ? "green" : "yellow"}
        />
      </div>

      <p className="text-sm text-gray-400">
        Minimum {status.min_training_scans} scans within the last {status.training_window_days} days
        required to train.
      </p>

      {model ? (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500">Model ID</p>
            <p className="text-sm text-white font-medium break-all">{model.model_id}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Training data</p>
            <p className="text-sm text-white font-medium">{model.training_data_size} scans</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Anomaly rate</p>
            <p className="text-sm text-white font-medium">
              {(model.anomaly_rate * 100).toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Last trained</p>
            <p className="text-sm text-white font-medium">
              {model.last_trained ? new Date(model.last_trained).toLocaleString() : "—"}
            </p>
          </div>
        </div>
      ) : (
        <EmptyState
          icon={<BeakerIcon className="h-12 w-12" />}
          title="No model trained yet"
          description="Train a model to enable anomaly detection."
        />
      )}

      <p className="text-xs text-gray-500">
        The trained model is saved and reloaded on backend restart; retrain to incorporate new scan
        data.
      </p>
    </div>
  );
};

export default MLStatusPanel;
