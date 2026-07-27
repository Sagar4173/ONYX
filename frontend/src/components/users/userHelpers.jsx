import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  UserCircleIcon,
} from "@heroicons/react/24/outline";

export const userColorToGradient = {
  blue: "from-blue-500 to-cyan-500",
  green: "from-green-500 to-emerald-500",
  yellow: "from-yellow-500 to-amber-500",
  red: "from-red-500 to-rose-500",
  orange: "from-orange-500 to-amber-500",
};

export const userColorToBgGradient = {
  blue: "from-blue-500/10 to-cyan-500/10",
  green: "from-green-500/10 to-emerald-500/10",
  yellow: "from-yellow-500/10 to-amber-500/10",
  red: "from-red-500/10 to-rose-500/10",
  orange: "from-orange-500/10 to-amber-500/10",
};

export const getRoleColor = (role) => {
  switch (role) {
    case "admin":
      return "bg-red-900/30 text-red-400 border-red-700/50";
    case "security_manager":
      return "bg-orange-900/30 text-orange-400 border-orange-700/50";
    case "developer":
      return "bg-cyan-900/30 text-cyan-400 border-cyan-700/50";
    case "viewer":
      return "bg-gray-700/30 text-gray-300 border-gray-700/50";
    default:
      return "bg-gray-700/30 text-gray-300 border-gray-700/50";
  }
};

export const getStatusColor = (status) => {
  switch (status) {
    case "active":
      return "bg-green-900/30 text-green-400 border-green-700/50";
    case "inactive":
      return "bg-gray-700/30 text-gray-300 border-gray-700/50";
    case "suspended":
      return "bg-red-900/30 text-red-400 border-red-700/50";
    case "pending_verification":
      return "bg-yellow-900/30 text-yellow-400 border-yellow-700/50";
    default:
      return "bg-gray-700/30 text-gray-300 border-gray-700/50";
  }
};

export const getStatusIcon = (status) => {
  switch (status) {
    case "active":
      return <CheckCircleIcon className="w-4 h-4" />;
    case "inactive":
      return <XCircleIcon className="w-4 h-4" />;
    case "suspended":
      return <ExclamationTriangleIcon className="w-4 h-4" />;
    case "pending_verification":
      return <ClockIcon className="w-4 h-4" />;
    default:
      return <UserCircleIcon className="w-4 h-4" />;
  }
};
