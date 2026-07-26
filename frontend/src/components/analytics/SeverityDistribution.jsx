import { motion } from "framer-motion";

const severities = [
  {
    key: "critical",
    label: "Critical",
    bar: "bg-gradient-to-r from-red-500 to-red-400",
    text: "text-red-400",
    dot: "bg-red-500",
  },
  {
    key: "high",
    label: "High",
    bar: "bg-gradient-to-r from-orange-500 to-orange-400",
    text: "text-orange-400",
    dot: "bg-orange-500",
  },
  {
    key: "medium",
    label: "Medium",
    bar: "bg-gradient-to-r from-yellow-500 to-yellow-400",
    text: "text-yellow-400",
    dot: "bg-yellow-500",
  },
  {
    key: "low",
    label: "Low",
    bar: "bg-gradient-to-r from-cyan-500 to-cyan-400",
    text: "text-cyan-400",
    dot: "bg-cyan-500",
  },
  {
    key: "info",
    label: "Info",
    bar: "bg-gradient-to-r from-gray-500 to-gray-400",
    text: "text-gray-400",
    dot: "bg-gray-500",
  },
];

const SeverityDistribution = ({ data }) => {
  const total = severities.reduce((sum, s) => sum + (data?.[s.key] || 0), 0) || 1;

  return (
    <div className="space-y-4">
      {severities.map((severity) => {
        const count = data?.[severity.key] || 0;
        const pct = Math.round((count / total) * 100);
        return (
          <div key={severity.key}>
            <div className="flex items-center justify-between mb-2">
              <span className={`flex items-center gap-2 text-sm font-medium ${severity.text}`}>
                <span className={`w-2 h-2 rounded-full ${severity.dot}`} />
                {severity.label}
              </span>
              <span className="text-sm text-gray-400">
                {count} ({pct}%)
              </span>
            </div>
            <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${severity.bar} rounded-full`}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SeverityDistribution;
