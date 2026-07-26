import { motion } from "framer-motion";
import {
  UsersIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import MetricCard from "../projects/MetricCard";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } };

const cardColors = {
  total: "#06b6d4",
  active: "#10b981",
  pending: "#f59e0b",
  suspended: "#ef4444",
};

const UserStatsTab = ({ statistics, statsLoading }) => {
  if (statsLoading || !statistics) return null;

  const roleDist = statistics?.role_distribution || {};
  const roleTotal = Object.values(roleDist).reduce((a, b) => a + b, 0) || 1;

  return (
    <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={stagger}
      >
        <motion.div variants={item}>
          <MetricCard
            icon={UsersIcon}
            label="Total Users"
            value={statistics.total_users}
            color={cardColors.total}
          />
        </motion.div>
        <motion.div variants={item}>
          <MetricCard
            icon={CheckCircleIcon}
            label="Active Users"
            value={statistics.active_users}
            color={cardColors.active}
          />
        </motion.div>
        <motion.div variants={item}>
          <MetricCard
            icon={ClockIcon}
            label="Pending Users"
            value={statistics.pending_users}
            color={cardColors.pending}
          />
        </motion.div>
        <motion.div variants={item}>
          <MetricCard
            icon={ExclamationTriangleIcon}
            label="Suspended Users"
            value={statistics.suspended_users}
            color={cardColors.suspended}
          />
        </motion.div>
      </motion.div>

      {Object.keys(roleDist).length > 0 && (
        <motion.div variants={item} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-4">Role Distribution</h3>
          <div className="space-y-3">
            {Object.entries(roleDist).map(([role, count]) => {
              const pct = Math.round((count / roleTotal) * 100);
              const colors = {
                admin: "bg-gradient-to-r from-red-500 to-red-400",
                security_manager: "bg-gradient-to-r from-orange-500 to-orange-400",
                developer: "bg-gradient-to-r from-cyan-500 to-cyan-400",
                viewer: "bg-gradient-to-r from-gray-500 to-gray-400",
              };
              return (
                <div key={role}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-300 capitalize">
                      {role.replace("_", " ")}
                    </span>
                    <span className="text-sm text-gray-400">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full ${colors[role] || colors.viewer}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default UserStatsTab;
