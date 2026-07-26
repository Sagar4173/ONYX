import { motion } from "framer-motion";
import { ExclamationTriangleIcon, LockClosedIcon, ShieldCheckIcon, UserGroupIcon } from "@heroicons/react/24/outline";
import MetricCard from "../projects/MetricCard";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } };

const cardColors = {
  failed: "#ef4444",
  locked: "#f97316",
  unverified: "#f59e0b",
};

const UserSecurityTab = ({ securityOverview, securityLoading }) => {
  if (securityLoading || !securityOverview) return null;

  const metrics = securityOverview.security_metrics || {};

  return (
    <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
      <motion.div className="grid grid-cols-1 md:grid-cols-3 gap-6" variants={stagger}>
        <motion.div variants={item}>
          <MetricCard
            icon={ExclamationTriangleIcon}
            label="Failed Login Attempts"
            value={metrics.users_with_failed_logins || 0}
            color={cardColors.failed}
          />
        </motion.div>
        <motion.div variants={item}>
          <MetricCard
            icon={LockClosedIcon}
            label="Locked Accounts"
            value={metrics.locked_accounts || 0}
            color={cardColors.locked}
          />
        </motion.div>
        <motion.div variants={item}>
          <MetricCard
            icon={ShieldCheckIcon}
            label="Unverified Emails"
            value={metrics.unverified_emails || 0}
            color={cardColors.unverified}
          />
        </motion.div>
      </motion.div>

      <motion.div variants={item} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
        <h3 className="text-xl font-bold text-white mb-4">Security Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-800/30 rounded-xl p-5 border border-gray-700/30">
            <div className="flex items-center gap-3 mb-2">
              <UserGroupIcon className="h-5 w-5 text-green-400" />
              <h4 className="text-lg font-semibold text-white">Active Sessions</h4>
            </div>
            <p className="text-3xl font-bold text-green-400">{securityOverview.active_sessions}</p>
          </div>
          <div className="bg-gray-800/30 rounded-xl p-5 border border-gray-700/30">
            <div className="flex items-center gap-3 mb-2">
              <UserGroupIcon className="h-5 w-5 text-cyan-400" />
              <h4 className="text-lg font-semibold text-white">Recent Registrations</h4>
            </div>
            <p className="text-3xl font-bold text-cyan-400">
              {securityOverview.recent_registrations}
            </p>
            <p className="text-gray-400 text-sm mt-1">Last 30 days</p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default UserSecurityTab;
