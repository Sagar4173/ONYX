import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UsersIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UserCircleIcon,
  KeyIcon,
  ComputerDesktopIcon,
  DevicePhoneMobileIcon,
  GlobeAltIcon,
  ArrowDownTrayIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  LockClosedIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";
import api from "../services/api";
import { useAuth } from "./auth";

const UserManagement = () => {
  const { user, isAuthenticated } = useAuth();
  const [selectedTab, setSelectedTab] = useState("users");
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState({
    role: "",
    status: "",
    sortBy: "created_at",
    sortOrder: "desc",
  });
  const [showUserModal, setShowUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showBulkActions, setShowBulkActions] = useState(false);

  const queryClient = useQueryClient();

  // Check if user has admin access
  const hasAdminAccess =
    user?.role === "admin" || user?.role === "security_manager";

  // Fetch users with pagination and filters
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users", searchQuery, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        search: searchQuery,
        role: filters.role,
        status: filters.status,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
        limit: "50",
      });
      const response = await api.get(`/users?${params}`);
      return response.data;
    },
    enabled: isAuthenticated && hasAdminAccess, // Only fetch if user is authenticated and has admin access
    retry: false,
  });

  // Fetch user statistics
  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: ["userStatistics"],
    queryFn: async () => {
      const response = await api.get("/users/statistics");
      return response.data;
    },
    enabled: isAuthenticated && hasAdminAccess,
    retry: false,
  });

  // Fetch security overview
  const { data: securityOverview, isLoading: securityLoading } = useQuery({
    queryKey: ["securityOverview"],
    queryFn: async () => {
      const response = await api.get("/users/security/overview");
      return response.data;
    },
    enabled: isAuthenticated && hasAdminAccess,
    retry: false,
  });

  // Update user mutations
  const updateUserRoleMutation = useMutation({
    mutationFn: async ({ userId, role }) => {
      await api.put(`/users/${userId}/role`, role);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["users"]);
      queryClient.invalidateQueries(["userStatistics"]);
    },
  });

  const updateUserStatusMutation = useMutation({
    mutationFn: async ({ userId, status }) => {
      await api.put(`/users/${userId}/status`, status);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["users"]);
      queryClient.invalidateQueries(["userStatistics"]);
    },
  });

  const bulkUpdateMutation = useMutation({
    mutationFn: async ({ userIds, updateData }) => {
      await api.post("/users/bulk-update", {
        user_ids: userIds,
        ...updateData,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["users"]);
      queryClient.invalidateQueries(["userStatistics"]);
      setSelectedUsers([]);
      setShowBulkActions(false);
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: async (userId) => {
      await api.delete(`/users/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["users"]);
      queryClient.invalidateQueries(["userStatistics"]);
    },
  });

  const handleUserSelect = (userId) => {
    setSelectedUsers((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    if (selectedUsers.length === usersData?.users?.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(usersData?.users?.map((user) => user.id) || []);
    }
  };

  // Check authentication and authorization
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="relative max-w-7xl mx-auto">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-8 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Authentication Required
            </h2>
            <p className="text-gray-400">
              Please log in to access the user management system.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!hasAdminAccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="relative max-w-7xl mx-auto">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-8 text-center">
            <div className="w-16 h-16 bg-orange-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
              <LockClosedIcon className="w-8 h-8 text-orange-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Access Denied
            </h2>
            <p className="text-gray-400 mb-4">
              You need administrator or security manager privileges to access
              the user management system.
            </p>
            <p className="text-gray-500 text-sm">
              Current role:{" "}
              <span className="text-blue-400">{user?.role || "Unknown"}</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getRoleColor = (role) => {
    switch (role) {
      case "admin":
        return "bg-red-100 text-red-800 border-red-200";
      case "security_manager":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "developer":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "viewer":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800 border-green-200";
      case "inactive":
        return "bg-gray-100 text-gray-800 border-gray-200";
      case "suspended":
        return "bg-red-100 text-red-800 border-red-200";
      case "pending_verification":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status) => {
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

  const StatCard = ({ title, value, icon: Icon, color = "blue", subtitle }) => (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6 hover:border-gray-700/50 transition-all duration-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className={`text-2xl font-bold mt-1 text-${color}-400`}>{value}</p>
          {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
        </div>
        <div
          className={`p-3 rounded-lg bg-${color}-500/10 border border-${color}-500/20`}
        >
          <Icon className={`w-6 h-6 text-${color}-400`} />
        </div>
      </div>
    </div>
  );

  const UserModal = ({ user, isOpen, onClose }) => {
    const [activeTab, setActiveTab] = useState("profile");
    const [userSessions, setUserSessions] = useState([]);
    const [userTokens, setUserTokens] = useState([]);
    const [userActivity, setUserActivity] = useState([]);

    useEffect(() => {
      if (isOpen && user) {
        // Fetch user details
        Promise.all([
          api.get(`/users/${user.id}/sessions`),
          api.get(`/users/${user.id}/api-tokens`),
          api.get(`/users/${user.id}/activity`),
        ]).then(([sessions, tokens, activity]) => {
          setUserSessions(sessions.data.sessions);
          setUserTokens(tokens.data.tokens);
          setUserActivity(activity.data.activities);
        });
      }
    }, [isOpen, user]);

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
          <div className="p-6 border-b border-gray-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <UserCircleIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {user.full_name}
                  </h2>
                  <p className="text-gray-400">@{user.username}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <XCircleIcon className="w-6 h-6 text-gray-400" />
              </button>
            </div>

            <div className="flex space-x-1 mt-6">
              {["profile", "sessions", "tokens", "activity"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      : "text-gray-400 hover:text-white hover:bg-gray-800"
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {activeTab === "profile" && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-gray-400 text-sm">Email</label>
                    <p className="text-white">{user.email}</p>
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm">Role</label>
                    <span
                      className={`inline-block px-2 py-1 rounded-lg text-xs font-medium border ${getRoleColor(
                        user.role
                      )}`}
                    >
                      {user.role.replace("_", " ").toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm">Status</label>
                    <span
                      className={`inline-flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium border ${getStatusColor(
                        user.status
                      )}`}
                    >
                      {getStatusIcon(user.status)}
                      <span>{user.status.replace("_", " ").toUpperCase()}</span>
                    </span>
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm">
                      Organization
                    </label>
                    <p className="text-white">
                      {user.organization || "Not specified"}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "sessions" && (
              <div className="space-y-4">
                {userSessions.map((session) => (
                  <div
                    key={session.session_id}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <ComputerDesktopIcon className="w-5 h-5 text-gray-400" />
                        <div>
                          <p className="text-white text-sm">
                            {session.ip_address}
                          </p>
                          <p className="text-gray-400 text-xs">
                            {session.user_agent}
                          </p>
                        </div>
                      </div>
                      <button className="text-red-400 hover:text-red-300 text-sm">
                        Revoke
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "tokens" && (
              <div className="space-y-4">
                {userTokens.map((token) => (
                  <div
                    key={token.token_id}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <KeyIcon className="w-5 h-5 text-gray-400" />
                        <div>
                          <p className="text-white text-sm">{token.name}</p>
                          <p className="text-gray-400 text-xs">
                            {token.prefix}...
                          </p>
                        </div>
                      </div>
                      <button className="text-red-400 hover:text-red-300 text-sm">
                        Revoke
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "activity" && (
              <div className="space-y-4">
                {userActivity.map((activity, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          activity.type === "login"
                            ? "bg-green-400"
                            : "bg-red-400"
                        }`}
                      />
                      <div>
                        <p className="text-white text-sm">
                          {activity.type} from {activity.ip_address}
                        </p>
                        <p className="text-gray-400 text-xs">
                          {new Date(activity.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
      <div className="relative max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <UsersIcon className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">User Management</h1>
          </div>
          <p className="text-gray-400">
            Manage users, roles, and security settings
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-6">
          {[
            { key: "users", label: "Users", icon: UsersIcon },
            { key: "statistics", label: "Statistics", icon: ChartBarIcon },
            { key: "security", label: "Security", icon: ShieldCheckIcon },
            { key: "settings", label: "Settings", icon: Cog6ToothIcon },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setSelectedTab(tab.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedTab === tab.key
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content based on selected tab */}
        {selectedTab === "users" && (
          <div className="space-y-6">
            {/* Search and Filters */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={filters.role}
                    onChange={(e) =>
                      setFilters((prev) => ({ ...prev, role: e.target.value }))
                    }
                    className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Roles</option>
                    <option value="admin">Admin</option>
                    <option value="security_manager">Security Manager</option>
                    <option value="developer">Developer</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  <select
                    value={filters.status}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        status: e.target.value,
                      }))
                    }
                    className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="suspended">Suspended</option>
                    <option value="pending_verification">Pending</option>
                  </select>
                </div>
              </div>

              {selectedUsers.length > 0 && (
                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-blue-400 text-sm">
                      {selectedUsers.length} user(s) selected
                    </span>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setShowBulkActions(true)}
                        className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
                      >
                        Bulk Actions
                      </button>
                      <button
                        onClick={() => setSelectedUsers([])}
                        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Users Table */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800/50">
                    <tr>
                      <th className="p-4 text-left">
                        <input
                          type="checkbox"
                          checked={
                            selectedUsers.length === usersData?.users?.length &&
                            usersData?.users?.length > 0
                          }
                          onChange={handleSelectAll}
                          className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
                        />
                      </th>
                      <th className="p-4 text-left text-gray-300 font-medium">
                        User
                      </th>
                      <th className="p-4 text-left text-gray-300 font-medium">
                        Role
                      </th>
                      <th className="p-4 text-left text-gray-300 font-medium">
                        Status
                      </th>
                      <th className="p-4 text-left text-gray-300 font-medium">
                        Last Login
                      </th>
                      <th className="p-4 text-left text-gray-300 font-medium">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersData?.users?.map((user) => (
                      <tr
                        key={user.id}
                        className="border-t border-gray-800/50 hover:bg-gray-800/30"
                      >
                        <td className="p-4">
                          <input
                            type="checkbox"
                            checked={selectedUsers.includes(user.id)}
                            onChange={() => handleUserSelect(user.id)}
                            className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
                          />
                        </td>
                        <td className="p-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                              <UserCircleIcon className="w-4 h-4 text-white" />
                            </div>
                            <div>
                              <p className="text-white font-medium">
                                {user.full_name}
                              </p>
                              <p className="text-gray-400 text-sm">
                                {user.email}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <span
                            className={`inline-block px-2 py-1 rounded-lg text-xs font-medium border ${getRoleColor(
                              user.role
                            )}`}
                          >
                            {user.role.replace("_", " ").toUpperCase()}
                          </span>
                        </td>
                        <td className="p-4">
                          <span
                            className={`inline-flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium border ${getStatusColor(
                              user.status
                            )}`}
                          >
                            {getStatusIcon(user.status)}
                            <span>
                              {user.status.replace("_", " ").toUpperCase()}
                            </span>
                          </span>
                        </td>
                        <td className="p-4">
                          <span className="text-gray-400 text-sm">
                            {user.last_login
                              ? new Date(user.last_login).toLocaleDateString()
                              : "Never"}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => {
                                setSelectedUser(user);
                                setShowUserModal(true);
                              }}
                              className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                            >
                              <EyeIcon className="w-4 h-4" />
                            </button>
                            <button className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors">
                              <PencilIcon className="w-4 h-4" />
                            </button>
                            <button className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-red-400 transition-colors">
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedTab === "statistics" && (
          <div className="space-y-6">
            {!statsLoading && statistics && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                  title="Total Users"
                  value={statistics.total_users}
                  icon={UsersIcon}
                  color="blue"
                />
                <StatCard
                  title="Active Users"
                  value={statistics.active_users}
                  icon={CheckCircleIcon}
                  color="green"
                />
                <StatCard
                  title="Pending Users"
                  value={statistics.pending_users}
                  icon={ClockIcon}
                  color="yellow"
                />
                <StatCard
                  title="Suspended Users"
                  value={statistics.suspended_users}
                  icon={ExclamationTriangleIcon}
                  color="red"
                />
              </div>
            )}

            {!statsLoading && statistics?.role_distribution && (
              <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
                <h3 className="text-xl font-bold text-white mb-4">
                  Role Distribution
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(statistics.role_distribution).map(
                    ([role, count]) => (
                      <div key={role} className="text-center">
                        <p className="text-2xl font-bold text-blue-400">
                          {count}
                        </p>
                        <p className="text-gray-400 text-sm">
                          {role.replace("_", " ").toUpperCase()}
                        </p>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === "security" && (
          <div className="space-y-6">
            {!securityLoading && securityOverview && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatCard
                    title="Failed Login Attempts"
                    value={
                      securityOverview.security_metrics
                        ?.users_with_failed_logins || 0
                    }
                    icon={ExclamationTriangleIcon}
                    color="red"
                  />
                  <StatCard
                    title="Locked Accounts"
                    value={
                      securityOverview.security_metrics?.locked_accounts || 0
                    }
                    icon={LockClosedIcon}
                    color="orange"
                  />
                  <StatCard
                    title="Unverified Emails"
                    value={
                      securityOverview.security_metrics?.unverified_emails || 0
                    }
                    icon={ExclamationTriangleIcon}
                    color="yellow"
                  />
                </div>

                <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">
                    Security Overview
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-lg font-semibold text-white mb-2">
                        Active Sessions
                      </h4>
                      <p className="text-3xl font-bold text-green-400">
                        {securityOverview.active_sessions}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white mb-2">
                        Recent Registrations
                      </h4>
                      <p className="text-3xl font-bold text-blue-400">
                        {securityOverview.recent_registrations}
                      </p>
                      <p className="text-gray-400 text-sm">Last 30 days</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {selectedTab === "settings" && (
          <div className="space-y-6">
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
              <h3 className="text-xl font-bold text-white mb-4">
                User Management Settings
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">
                      Allow User Registration
                    </h4>
                    <p className="text-gray-400 text-sm">
                      Allow users to register new accounts
                    </p>
                  </div>
                  <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                    Configure
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">Password Policy</h4>
                    <p className="text-gray-400 text-sm">
                      Configure password requirements
                    </p>
                  </div>
                  <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                    Configure
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">
                      Session Management
                    </h4>
                    <p className="text-gray-400 text-sm">
                      Configure session timeout and security
                    </p>
                  </div>
                  <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                    Configure
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* User Detail Modal */}
        <UserModal
          user={selectedUser}
          isOpen={showUserModal}
          onClose={() => {
            setShowUserModal(false);
            setSelectedUser(null);
          }}
        />
      </div>
    </div>
  );
};

export default UserManagement;
