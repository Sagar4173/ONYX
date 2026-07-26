import { ExclamationTriangleIcon, LockClosedIcon } from "@heroicons/react/24/outline";
import { StatCard } from "../../styles/components";
import { userColorToGradient, userColorToBgGradient } from "./userHelpers";

const UserSecurityTab = ({ securityOverview, securityLoading }) => {
  if (securityLoading || !securityOverview) return null;

  const metrics = securityOverview.security_metrics || {};

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Failed Login Attempts"
          value={metrics.users_with_failed_logins || 0}
          icon={<ExclamationTriangleIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.red}
          bgGradient={userColorToBgGradient.red}
        />
        <StatCard
          title="Locked Accounts"
          value={metrics.locked_accounts || 0}
          icon={<LockClosedIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.orange}
          bgGradient={userColorToBgGradient.orange}
        />
        <StatCard
          title="Unverified Emails"
          value={metrics.unverified_emails || 0}
          icon={<ExclamationTriangleIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.yellow}
          bgGradient={userColorToBgGradient.yellow}
        />
      </div>

      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
        <h3 className="text-xl font-bold text-white mb-4">Security Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">Active Sessions</h4>
            <p className="text-3xl font-bold text-green-400">{securityOverview.active_sessions}</p>
          </div>
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">Recent Registrations</h4>
            <p className="text-3xl font-bold text-cyan-400">
              {securityOverview.recent_registrations}
            </p>
            <p className="text-gray-400 text-sm">Last 30 days</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserSecurityTab;
