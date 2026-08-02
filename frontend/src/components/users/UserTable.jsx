import { motion } from "framer-motion";
import {
  UsersIcon,
  UserCircleIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { getRoleColor, getStatusColor, getStatusIcon } from "./userHelpers.jsx";
import { LoadingState, EmptyState, ErrorState } from "../../layouts";

const rowAnim = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0 },
};

const UserTable = ({
  usersData,
  usersLoading,
  usersError,
  selectedUsers,
  onSelectAll,
  onSelectUser,
  onViewUser,
  onRetry,
}) => {
  if (usersLoading) {
    return <LoadingState message="Loading users..." cards={3} />;
  }

  if (usersError) {
    return (
      <ErrorState
        title="Failed to Load Users"
        message={usersError?.message || "An error occurred while fetching users."}
        onRetry={onRetry}
      />
    );
  }

  if (!usersData?.users?.length) {
    return <EmptyState icon={<UsersIcon className="h-12 w-12" />} title="No Users Found" />;
  }

  return (
    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="p-4 text-left">
                <input
                  type="checkbox"
                  checked={
                    selectedUsers.length === usersData.users.length && usersData.users.length > 0
                  }
                  onChange={onSelectAll}
                  className="rounded border-gray-600 bg-gray-700 text-cyan-500 focus:ring-cyan-500"
                />
              </th>
              <th className="p-4 text-left text-gray-300 font-medium">User</th>
              <th className="p-4 text-left text-gray-300 font-medium">Role</th>
              <th className="p-4 text-left text-gray-300 font-medium">Status</th>
              <th className="p-4 text-left text-gray-300 font-medium">Last Login</th>
              <th className="p-4 text-left text-gray-300 font-medium">Actions</th>
            </tr>
          </thead>
          <motion.tbody
            initial="hidden"
            animate="show"
            variants={{ hidden: {}, show: { transition: { staggerChildren: 0.03 } } }}
          >
            {usersData.users.map((user) => (
              <motion.tr
                key={user.id}
                variants={rowAnim}
                className="border-t border-gray-700/30 hover:bg-gray-800/30 transition-colors"
              >
                <td className="p-4">
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(user.id)}
                    onChange={() => onSelectUser(user.id)}
                    className="rounded border-gray-600 bg-gray-700 text-cyan-500 focus:ring-cyan-500"
                  />
                </td>
                <td className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-violet-600 rounded-lg flex items-center justify-center">
                      <UserCircleIcon className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <p className="text-white font-medium">{user.full_name}</p>
                      <p className="text-gray-400 text-sm">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="p-4">
                  <span
                    className={`inline-block px-2 py-1 rounded-lg text-xs font-medium border ${getRoleColor(user.role)}`}
                  >
                    {user.role.replace("_", " ").toUpperCase()}
                  </span>
                </td>
                <td className="p-4">
                  <span
                    className={`inline-flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium border ${getStatusColor(user.status)}`}
                  >
                    {getStatusIcon(user.status)}
                    <span>{user.status.replace("_", " ").toUpperCase()}</span>
                  </span>
                </td>
                <td className="p-4">
                  <span className="text-gray-400 text-sm">
                    {user.last_login ? new Date(user.last_login).toLocaleDateString() : "Never"}
                  </span>
                </td>
                <td className="p-4">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onViewUser(user)}
                      className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                      title="View user"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>
                    <button
                      className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                      title="Edit user"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                    <button
                      className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-red-400 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                      title="Delete user"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </motion.tr>
            ))}
          </motion.tbody>
        </table>
      </div>
    </div>
  );
};

export default UserTable;
