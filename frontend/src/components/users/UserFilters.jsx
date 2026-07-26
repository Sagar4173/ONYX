import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { GlassCard } from "../../layouts";

const ROLE_OPTIONS = ["admin", "security_manager", "developer", "viewer"];
const STATUS_OPTIONS = ["active", "inactive", "suspended", "pending_verification"];

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
      <div className="flex gap-2">
        <select
          value={filters.role}
          onChange={(e) => setFilters((prev) => ({ ...prev, role: e.target.value }))}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
          <option value="">All Roles</option>
          {ROLE_OPTIONS.map((role) => (
            <option key={role} value={role}>
              {role === "security_manager"
                ? "Security Manager"
                : role.charAt(0).toUpperCase() + role.slice(1)}
            </option>
          ))}
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
          <option value="">All Status</option>
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {status === "pending_verification"
                ? "Pending"
                : status.charAt(0).toUpperCase() + status.slice(1)}
            </option>
          ))}
        </select>
      </div>
    </div>

    {selectedUsers.length > 0 && (
      <div className="mt-4 p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-cyan-400 text-sm">{selectedUsers.length} user(s) selected</span>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
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
    )}
  </GlassCard>
);

export default UserFilters;
