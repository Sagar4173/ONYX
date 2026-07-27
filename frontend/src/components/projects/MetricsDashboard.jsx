import { motion } from "framer-motion";
import {
  ChartBarIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import MetricCard from "./MetricCard";

const MetricsDashboard = ({
  stats = {},
  totalVulns,
  liveSecurityScore,
  scanCompleted,
  lastScanDate,
}) => {
  const metrics = [
    {
      icon: ChartBarIcon,
      label: "Total Scans",
      color: "#06b6d4",
      value:
        (scanCompleted ? (stats.total_scans || 0) + 1 : stats.total_scans) ||
        (scanCompleted ? 1 : 0),
    },
    {
      icon: ExclamationTriangleIcon,
      label: "Vulnerabilities",
      color: "#ef4444",
      value: totalVulns,
    },
    {
      icon: ShieldCheckIcon,
      label: "Security Score",
      color: "#22c55e",
      value: Math.round(liveSecurityScore ?? stats.security_score ?? 0),
    },
    {
      icon: ClockIcon,
      label: "Last Scan",
      color: "#a78bfa",
      value: scanCompleted ? "Just now" : lastScanDate ? "View History" : "Never",
      formatter: (v) => v,
    },
  ];

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        visible: { transition: { staggerChildren: 0.08 } },
      }}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
    >
      {metrics.map((m, i) => (
        <motion.div
          key={i}
          variants={{
            hidden: { opacity: 0, y: 15 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <MetricCard {...m} />
        </motion.div>
      ))}
    </motion.div>
  );
};

export default MetricsDashboard;
