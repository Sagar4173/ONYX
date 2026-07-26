import { useState } from "react";
import { motion } from "framer-motion";
import {
  FolderIcon,
  DocumentChartBarIcon,
  KeyIcon,
  LockClosedIcon,
  LockOpenIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

const roleBadgeColors = {
  admin: "bg-red-500/20 text-red-400 border-red-500/30",
  security_manager: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  developer: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  viewer: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const statusBadgeColors = {
  active: "bg-green-500/20 text-green-400",
  inactive: "bg-gray-500/20 text-gray-400",
  suspended: "bg-red-500/20 text-red-400",
  pending_verification: "bg-amber-500/20 text-amber-400",
};

const UserRow = ({ user, onEditRole, onEditStatus, onDelete }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <motion.tr
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ backgroundColor: "rgba(255,255,255,0.03)" }}
      className="border-b border-gray-800/50 transition-colors"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center text-white font-semibold">
            {user.username?.charAt(0).toUpperCase() || "U"}
          </div>
          <div>
            <p className="text-sm font-medium text-white">{user.username}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 text-xs rounded-full border ${roleBadgeColors[user.role] || roleBadgeColors.viewer}`}
        >
          {user.role?.replace("_", " ")}
        </span>
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 text-xs rounded-full ${statusBadgeColors[user.status] || statusBadgeColors.inactive}`}
        >
          {user.status?.replace("_", " ")}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span className="flex items-center gap-1">
            <FolderIcon className="h-4 w-4" />
            {user.project_count || 0}
          </span>
          <span className="flex items-center gap-1">
            <DocumentChartBarIcon className="h-4 w-4" />
            {user.scan_count || 0}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {user.last_login ? new Date(user.last_login).toLocaleDateString() : "Never"}
      </td>
      <td className="px-4 py-3">
        <div
          className={`flex items-center gap-2 transition-opacity ${showActions ? "opacity-100" : "opacity-0"}`}
        >
          <button
            onClick={() => onEditRole(user)}
            className="p-1.5 text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/20 rounded-lg transition-colors"
            title="Change Role"
          >
            <KeyIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => onEditStatus(user)}
            className="p-1.5 text-gray-400 hover:text-amber-400 hover:bg-amber-500/20 rounded-lg transition-colors"
            title="Change Status"
          >
            {user.status === "active" ? (
              <LockOpenIcon className="h-4 w-4" />
            ) : (
              <LockClosedIcon className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() => onDelete(user)}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
            title="Delete User"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </td>
    </motion.tr>
  );
};

export default UserRow;
