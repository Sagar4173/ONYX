import {
  UserPlusIcon,
  KeyIcon,
  FolderIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";

const iconMap = {
  user: UserPlusIcon,
  login: KeyIcon,
  folder: FolderIcon,
  check: CheckCircleIcon,
  x: XCircleIcon,
  clock: ClockIcon,
};

const ActivityItem = ({ activity }) => {
  const Icon = iconMap[activity.icon] || BoltIcon;

  const getColor = () => {
    if (activity.type?.includes("completed")) return "text-green-400 bg-green-500/20";
    if (activity.type?.includes("failed")) return "text-red-400 bg-red-500/20";
    if (activity.type?.includes("user")) return "text-cyan-400 bg-cyan-500/20";
    if (activity.type?.includes("project")) return "text-purple-400 bg-purple-500/20";
    return "text-gray-400 bg-gray-500/20";
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-800/50 transition-colors">
      <div className={`p-2 rounded-lg ${getColor()}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{activity.title}</p>
        <p className="text-xs text-gray-500">{activity.description}</p>
      </div>
      <span className="text-xs text-gray-500 whitespace-nowrap">
        {formatTime(activity.timestamp)}
      </span>
    </div>
  );
};

export default ActivityItem;
