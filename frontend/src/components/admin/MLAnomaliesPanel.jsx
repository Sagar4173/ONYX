import { Badge, SeverityBadge, EmptyState } from "../ui/StyleComponents";
import { AIStateBlock } from "../common/AIStateBlock";
import { BeakerIcon, BellAlertIcon } from "@heroicons/react/24/outline";

const MLAnomaliesPanel = ({ data }) => {
  if (data.anomaly_detection_status === "degraded") {
    return (
      <AIStateBlock
        variant="degraded"
        title="Anomaly detection unavailable"
        description={data.error}
      />
    );
  }

  if (data.anomaly_detection_status === "training_required") {
    return (
      <EmptyState
        icon={<BeakerIcon className="h-12 w-12" />}
        title="No model trained yet"
        description="Train a model to enable anomaly alerts."
      />
    );
  }

  const statistics = Object.entries(data.alert_statistics || {});
  const total = data.total_recent_alerts ?? 0;
  const recentCount = data.recent_alerts.length;
  const countLabel =
    total > recentCount
      ? `Latest ${recentCount} of ${total} alerts in the last 7 days`
      : `${total} alert${total === 1 ? "" : "s"} in the last 7 days`;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-sm text-gray-400">{countLabel}</p>
        {statistics.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
              Last 30 days
            </span>
            {statistics.map(([severity, count]) => (
              <Badge key={severity} variant={severity.toLowerCase()}>
                {`${severity} ${count}`}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {data.recent_alerts.length === 0 ? (
        <EmptyState
          icon={<BellAlertIcon className="h-12 w-12" />}
          title="No anomalies detected in the last 7 days"
          description="The model has not flagged any unusual scan activity."
        />
      ) : (
        <ul className="divide-y divide-gray-700/50 bg-gray-800/50 border border-gray-700/50 rounded-xl">
          {data.recent_alerts.map((alert) => (
            <li key={alert.alert_id} className="p-4 space-y-1">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={alert.severity} />
                  <span className="text-sm font-medium text-white">{alert.anomaly_type}</span>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-gray-400">{alert.description}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default MLAnomaliesPanel;
