const severities = [
  { key: "critical", label: "Critical", color: "bg-red-500", textColor: "text-red-400" },
  { key: "high", label: "High", color: "bg-orange-500", textColor: "text-orange-400" },
  { key: "medium", label: "Medium", color: "bg-yellow-500", textColor: "text-yellow-400" },
  { key: "low", label: "Low", color: "bg-cyan-500", textColor: "text-cyan-400" },
  { key: "info", label: "Info", color: "bg-gray-500", textColor: "text-gray-400" },
];

const SeverityDistribution = ({ data }) => {
  const total = severities.reduce((sum, s) => sum + (data?.[s.key] || 0), 0) || 1;

  return (
    <div className="space-y-4">
      {severities.map((severity) => {
        const count = data?.[severity.key] || 0;
        const percentage = Math.round((count / total) * 100);
        return (
          <div key={severity.key}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${severity.textColor}`}>{severity.label}</span>
              <span className="text-sm text-gray-400">
                {count} ({percentage}%)
              </span>
            </div>
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${severity.color} rounded-full transition-all duration-500`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SeverityDistribution;
