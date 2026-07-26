import { motion, AnimatePresence } from "framer-motion";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { GlassCard } from "../../layouts";

const ROLE_OPTIONS = ["admin", "security_manager", "developer", "viewer"];
const STATUS_OPTIONS = ["active", "inactive", "suspended", "pending_verification"];

const formatLabel = (value) => {
  if (value === "security_manager") return "Security Mgr";
  if (value === "pending_verification") return "Pending";
  return value.charAt(0).toUpperCase() + value.slice(1);
};

const pillColors = {
  active: "border-green-500/30 bg-green-500/20 text-green-400",
  inactive: "border-gray-500/30 bg-gray-500/20 text-gray-400",
  suspended: "border-red-500/30 bg-red-500/20 text-red-400",
  pending_verification: "border-yellow-500/30 bg-yellow-500/20 text-yellow-400",
  admin: "border-red-500/30 bg-red-500/20 text-red-400",
  security_manager: "border-orange-500/30 bg-orange-500/20 text-orange-400",
  developer: "border-cyan-500/30 bg-cyan-500/20 text-cyan-400",
  viewer: "border-gray-500/30 bg-gray-500/20 text-gray-400",
};

const UserFilters = ({
  searchQuery,
  setSearchQuery,
  filters,
  setFilters,
  selectedUsers,
  setSelectedUsers,
}) => (
  <GlassCard>
    <div className="flex flex-col lg:flex-row gap-4">
      <div className="flex-1">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-gray-500 uppercase tracking-wider">Role</span>
        <div className="flex gap-1">
          <button
            onClick={() => setFilters((prev) => ({ ...prev, role: "" }))}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all border ${
              !filters.role
                ? "bg-gray-700/70 text-white border-gray-600/50"
                : "text-gray-400 hover:text-white border-transparent"
            }`}
          >
            All
          </button>
          {ROLE_OPTIONS.map((role) => (
            <button
              key={role}
              onClick={() => setFilters((prev) => ({ ...prev, role }))}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all border ${
                filters.role === role
                  ? pillColors[role]
                  : "text-gray-400 hover:text-white border-transparent"
              }`}
            >
              {formatLabel(role)}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-500 uppercase tracking-wider ml-2">Status</span>
        <div className="flex gap-1">
          <button
            onClick={() => setFilters((prev) => ({ ...prev, status: "" }))}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all border ${
              !filters.status
                ? "bg-gray-700/70 text-white border-gray-600/50"
                : "text-gray-400 hover:text-white border-transparent"
            }`}
          >
            All
          </button>
          {STATUS_OPTIONS.map((status) => (
            <button
              key={status}
              onClick={() => setFilters((prev) => ({ ...prev, status }))}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all border ${
                filters.status === status
                  ? pillColors[status]
                  : "text-gray-400 hover:text-white border-transparent"
              }`}
            >
              {formatLabel(status)}
            </button>
          ))}
        </div>
      </div>
    </div>

    <AnimatePresence>
      {selectedUsers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 overflow-hidden"
        >
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-cyan-400 text-sm">
                {selectedUsers.length} user(s) selected
              </span>
              <div className="flex space-x-2">
                <button className="px-3 py-1 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white text-sm font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                  Bulk Actions
                </button>
                <button
                  onClick={() => setSelectedUsers([])}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  </GlassCard>
);

export default UserFilters;
