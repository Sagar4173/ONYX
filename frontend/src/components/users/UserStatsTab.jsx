import {
  UsersIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { StatCard } from "../../styles/components";
import { userColorToGradient, userColorToBgGradient } from "./userHelpers";

const UserStatsTab = ({ statistics, statsLoading }) => {
  if (statsLoading || !statistics) return null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={statistics.total_users}
          icon={<UsersIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.blue}
          bgGradient={userColorToBgGradient.blue}
        />
        <StatCard
          title="Active Users"
          value={statistics.active_users}
          icon={<CheckCircleIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.green}
          bgGradient={userColorToBgGradient.green}
        />
        <StatCard
          title="Pending Users"
          value={statistics.pending_users}
          icon={<ClockIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.yellow}
          bgGradient={userColorToBgGradient.yellow}
        />
        <StatCard
          title="Suspended Users"
          value={statistics.suspended_users}
          icon={<ExclamationTriangleIcon className="h-5 w-5 text-white" />}
          gradient={userColorToGradient.red}
          bgGradient={userColorToBgGradient.red}
        />
      </div>

      {statistics?.role_distribution && (
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-4">Role Distribution</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(statistics.role_distribution).map(([role, count]) => (
              <div key={role} className="text-center">
                <p className="text-2xl font-bold text-cyan-400">{count}</p>
                <p className="text-gray-400 text-sm">{role.replace("_", " ").toUpperCase()}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserStatsTab;
