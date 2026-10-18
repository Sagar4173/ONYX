import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Button, AnimatedCounter } from "../ui/StyleComponents";
import { AIStateBlock } from "../common/AIStateBlock";
import { mlAPI } from "../../services/api";
import { BeakerIcon } from "@heroicons/react/24/outline";

const MLTrainPanel = ({ status }) => {
  const queryClient = useQueryClient();
  const [metrics, setMetrics] = useState(null);
  const [gateBlocked, setGateBlocked] = useState(null);

  const mutation = useMutation({
    mutationFn: mlAPI.train,
    onSuccess: (data) => {
      setMetrics(data);
      setGateBlocked(null);
      toast.success("Model trained");
      queryClient.invalidateQueries({ queryKey: ["ml-status"] });
      queryClient.invalidateQueries({ queryKey: ["ml-anomalies"] });
    },
    onError: (error) => {
      if (error.response?.status === 409) {
        setGateBlocked(error.response.data?.detail || "Training is currently unavailable.");
        return;
      }
      toast.error(error.response?.data?.detail || "Training failed");
    },
  });

  const flagDisabled = !status.isolation_forest_enabled;
  const sklearnDisabled = !status.sklearn_available;
  const disabled = flagDisabled || sklearnDisabled || mutation.isPending || Boolean(gateBlocked);
  const disabledReason = flagDisabled
    ? "Isolation Forest is disabled on the server (ML_ISOLATION_FOREST_ENABLED=false)"
    : sklearnDisabled
      ? "scikit-learn is not installed on the server"
      : undefined;

  return (
    <div className="space-y-4">
      <Button
        onClick={() => mutation.mutate()}
        disabled={disabled}
        isLoading={mutation.isPending}
        title={disabledReason}
        leftIcon={<BeakerIcon className="w-5 h-5" />}
      >
        Train Model
      </Button>

      {mutation.isPending && (
        <p className="text-sm text-gray-400">Training model… this may take a few minutes.</p>
      )}

      {gateBlocked && (
        <div className="space-y-2">
          <AIStateBlock variant="disabled" title="Training unavailable" description={gateBlocked} />
          <p className="text-sm text-gray-400">
            Requires at least {status.min_training_scans} scans within the last{" "}
            {status.training_window_days} days.
          </p>
        </div>
      )}

      {metrics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
          <div>
            <p className="text-xs text-gray-500">Anomaly rate</p>
            <p className="text-lg font-bold text-white">
              <AnimatedCounter value={metrics.anomaly_rate * 100} decimals={2} suffix="%" />
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Score mean</p>
            <p className="text-lg font-bold text-white">
              <AnimatedCounter value={metrics.score_mean} decimals={4} />
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Score std</p>
            <p className="text-lg font-bold text-white">
              <AnimatedCounter value={metrics.score_std} decimals={4} />
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Training scans</p>
            <p className="text-lg font-bold text-white">{metrics.training_data_size}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MLTrainPanel;
