/**
 * Admin Dashboard - System Administration Center
 * Comprehensive system overview and management for administrators
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  UsersIcon,
  FolderIcon,
  DocumentChartBarIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  CogIcon,
  BoltIcon,
  GlobeAltIcon,
  ServerIcon,
  CommandLineIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  UserPlusIcon,
  UserMinusIcon,
  KeyIcon,
  BuildingOfficeIcon,
  CalendarDaysIcon,
  FireIcon,
  SparklesIcon,
  LockClosedIcon,
  LockOpenIcon,
} from "@heroicons/react/24/outline";
import { StarIcon } from "@heroicons/react/24/solid";
import { StatCard } from "../styles/components";
import { adminAPI } from "../services/api";
import { useAuth } from "../components/auth";
import toast from "react-hot-toast";

const colorToGradient = {
  blue: "from-blue-500 to-cyan-500",
  green: "from-green-500 to-emerald-500",
  purple: "from-purple-500 to-violet-500",
  orange: "from-orange-500 to-amber-500",
  red: "from-red-500 to-rose-500",
  cyan: "from-cyan-500 to-teal-500",
};

const colorToBgGradient = {
  blue: "from-blue-500/20 to-cyan-500/20",
  green: "from-green-500/20 to-emerald-500/20",
  purple: "from-purple-500/20 to-violet-500/20",
  orange: "from-orange-500/20 to-amber-500/20",
  red: "from-red-500/20 to-rose-500/20",
  cyan: "from-cyan-500/20 to-teal-500/20",
};

// Health Score Ring
const HealthScoreRing = ({ score }) => {
  const radius = 60;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (score >= 80)
      return {
        stroke: "#10b981",
        text: "text-green-400",
        bg: "bg-green-500/20",
      };
    if (score >= 60)
      return {
        stroke: "#f59e0b",
        text: "text-amber-400",
        bg: "bg-amber-500/20",
      };
    return { stroke: "#ef4444", text: "text-red-400", bg: "bg-red-500/20" };
  };

  const colors = getColor();

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        height={radius * 2}
        width={radius * 2}
        className="transform -rotate-90"
      >
        <circle
          stroke="#374151"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={colors.stroke}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={circumference + " " + circumference}
          style={{
            strokeDashoffset,
            transition: "stroke-dashoffset 0.5s ease-in-out",
          }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className={`text-2xl font-bold ${colors.text}`}>{score}</span>
        <span className="text-xs text-gray-500">Health</span>
      </div>
    </div>
  );
};

// Activity Item Component
const ActivityItem = ({ activity }) => {
  const getIcon = () => {
    switch (activity.icon) {
      case "user":
        return <UserPlusIcon className="h-4 w-4" />;
      case "login":
        return <KeyIcon className="h-4 w-4" />;
      case "folder":
        return <FolderIcon className="h-4 w-4" />;
      case "check":
        return <CheckCircleIcon className="h-4 w-4" />;
      case "x":
        return <XCircleIcon className="h-4 w-4" />;
      case "clock":
        return <ClockIcon className="h-4 w-4" />;
      default:
        return <BoltIcon className="h-4 w-4" />;
    }
  };

  const getColor = () => {
    if (activity.type.includes("completed"))
      return "text-green-400 bg-green-500/20";
    if (activity.type.includes("failed")) return "text-red-400 bg-red-500/20";
    if (activity.type.includes("user")) return "text-blue-400 bg-blue-500/20";
    if (activity.type.includes("project"))
      return "text-purple-400 bg-purple-500/20";
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
      <div className={`p-2 rounded-lg ${getColor()}`}>{getIcon()}</div>
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

// User Row Component
const UserRow = ({ user, onEditRole, onEditStatus, onDelete }) => {
  const [showActions, setShowActions] = useState(false);

  const getRoleBadge = (role) => {
    const colors = {
      admin: "bg-red-500/20 text-red-400 border-red-500/30",
      security_manager: "bg-purple-500/20 text-purple-400 border-purple-500/30",
      developer: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      viewer: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    };
    return colors[role] || colors.viewer;
  };

  const getStatusBadge = (status) => {
    const colors = {
      active: "bg-green-500/20 text-green-400",
      inactive: "bg-gray-500/20 text-gray-400",
      suspended: "bg-red-500/20 text-red-400",
      pending_verification: "bg-amber-500/20 text-amber-400",
    };
    return colors[status] || colors.inactive;
  };

  return (
    <tr
      className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
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
          className={`px-2 py-1 text-xs rounded-full border ${getRoleBadge(
            user.role
          )}`}
        >
          {user.role?.replace("_", " ")}
        </span>
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(
            user.status
          )}`}
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
        {user.last_login
          ? new Date(user.last_login).toLocaleDateString()
          : "Never"}
      </td>
      <td className="px-4 py-3">
        <div
          className={`flex items-center gap-2 transition-opacity ${
            showActions ? "opacity-100" : "opacity-0"
          }`}
        >
          <button
            onClick={() => onEditRole(user)}
            className="p-1.5 text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
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
    </tr>
  );
};

// Project Row Component
const ProjectRow = ({ project, onDelete }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <tr
      className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <td className="px-4 py-3">
        <div>
          <Link
            to={`/project/${project.id}`}
            className="text-sm font-medium text-white hover:text-blue-400 transition-colors"
          >
            {project.name}
          </Link>
          <p className="text-xs text-gray-500 truncate max-w-xs">
            {project.description}
          </p>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <UsersIcon className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-400">
            {project.owner?.username || "Unknown"}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400">
        {project.total_scans || 0} scans
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {project.critical_findings > 0 && (
            <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">
              {project.critical_findings} critical
            </span>
          )}
          <span className="text-sm text-gray-400">
            {project.total_findings || 0} total
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {project.created_at
          ? new Date(project.created_at).toLocaleDateString()
          : "Unknown"}
      </td>
      <td className="px-4 py-3">
        <div
          className={`flex items-center gap-2 transition-opacity ${
            showActions ? "opacity-100" : "opacity-0"
          }`}
        >
          <Link
            to={`/project/${project.id}`}
            className="p-1.5 text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
            title="View Project"
          >
            <EyeIcon className="h-4 w-4" />
          </Link>
          <button
            onClick={() => onDelete(project)}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
            title="Delete Project"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  );
};

// Main Admin Dashboard Component
const AdminDashboard = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");
  const [userSearch, setUserSearch] = useState("");
  const [projectSearch, setProjectSearch] = useState("");
  const [selectedUserForEdit, setSelectedUserForEdit] = useState(null);
  const [editModal, setEditModal] = useState({ type: null, user: null });

  // Check admin access
  const isAdmin = user?.role === "admin";

  // Fetch dashboard stats
  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ["admin-dashboard-stats"],
    queryFn: adminAPI.getDashboardStats,
    enabled: isAdmin,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch all users
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ["admin-users", userSearch],
    queryFn: () => adminAPI.getAllUsers({ search: userSearch, limit: 100 }),
    enabled: isAdmin && activeTab === "users",
  });

  // Fetch all projects
  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ["admin-projects", projectSearch],
    queryFn: () =>
      adminAPI.getAllProjects({ search: projectSearch, limit: 100 }),
    enabled: isAdmin && activeTab === "projects",
  });

  // Fetch recent activity
  const { data: activityData, isLoading: activityLoading } = useQuery({
    queryKey: ["admin-activity"],
    queryFn: () => adminAPI.getRecentActivity(30),
    enabled: isAdmin,
  });

  // Mutations
  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }) => adminAPI.updateUserRole(userId, role),
    onSuccess: () => {
      toast.success("User role updated successfully");
      queryClient.invalidateQueries(["admin-users"]);
      queryClient.invalidateQueries(["admin-dashboard-stats"]);
      setEditModal({ type: null, user: null });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update role");
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ userId, status }) =>
      adminAPI.updateUserStatus(userId, status),
    onSuccess: () => {
      toast.success("User status updated successfully");
      queryClient.invalidateQueries(["admin-users"]);
      queryClient.invalidateQueries(["admin-dashboard-stats"]);
      setEditModal({ type: null, user: null });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update status");
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: (userId) => adminAPI.deleteUser(userId),
    onSuccess: () => {
      toast.success("User deleted successfully");
      queryClient.invalidateQueries(["admin-users"]);
      queryClient.invalidateQueries(["admin-dashboard-stats"]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete user");
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: (projectId) => adminAPI.deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted successfully");
      queryClient.invalidateQueries(["admin-projects"]);
      queryClient.invalidateQueries(["admin-dashboard-stats"]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete project");
    },
  });

  // Access denied view
  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-2xl mx-auto mt-20">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-red-500/30 rounded-2xl p-8 text-center">
            <div className="w-20 h-20 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <LockClosedIcon className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">
              Admin Access Required
            </h2>
            <p className="text-gray-400 mb-6">
              This area is restricted to administrators only. Please contact
              your system administrator if you need access to these features.
            </p>
            <p className="text-sm text-gray-500">
              Your current role:{" "}
              <span className="text-blue-400 font-medium">
                {user?.role || "Unknown"}
              </span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: "Overview", icon: ChartBarIcon },
    { id: "users", label: "Users", icon: UsersIcon },
    { id: "projects", label: "Projects", icon: FolderIcon },
    { id: "activity", label: "Activity", icon: BoltIcon },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl shadow-lg shadow-red-500/25">
              <CommandLineIcon className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                System Administration
                <span className="px-2 py-1 text-xs font-medium bg-red-500/20 text-red-400 rounded-full border border-red-500/30">
                  Admin
                </span>
              </h1>
              <p className="text-gray-400 mt-1">
                Complete system control and monitoring • Logged in as{" "}
                {user?.username}
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="flex gap-2 p-1 bg-gray-800/50 rounded-xl border border-gray-700/50 w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === tab.id
                    ? "bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Users"
                value={stats?.users?.total || 0}
                subtitle={`${stats?.users?.active_24h || 0} active today`}
                icon={<UsersIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.blue}
                bgGradient={colorToBgGradient.blue}
              />
              <StatCard
                title="Total Projects"
                value={stats?.projects?.total || 0}
                subtitle={`Across all users`}
                icon={<FolderIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.purple}
                bgGradient={colorToBgGradient.purple}
              />
              <StatCard
                title="Total Scans"
                value={stats?.scans?.total || 0}
                subtitle={`${stats?.scans?.last_24h || 0} in last 24h`}
                icon={<ShieldCheckIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.cyan}
                bgGradient={colorToBgGradient.cyan}
              />
              <StatCard
                title="Total Findings"
                value={stats?.scans?.total_findings || 0}
                subtitle={`${
                  stats?.scans?.findings_by_severity?.critical || 0
                } critical`}
                icon={<ExclamationTriangleIcon className="h-5 w-5 text-white" />}
                gradient={stats?.scans?.findings_by_severity?.critical > 0 ? colorToGradient.red : colorToGradient.green}
                bgGradient={stats?.scans?.findings_by_severity?.critical > 0 ? colorToBgGradient.red : colorToBgGradient.green}
              />
            </div>

            {/* Second Row - More Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard
                title="New Users (7d)"
                value={stats?.users?.new_7d || 0}
                subtitle={`${stats?.users?.new_24h || 0} today`}
                icon={<UserPlusIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.green}
                bgGradient={colorToBgGradient.green}
              />
              <StatCard
                title="Admin Users"
                value={stats?.users?.admin_count || 0}
                subtitle="System administrators"
                icon={<StarIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.orange}
                bgGradient={colorToBgGradient.orange}
              />
              <StatCard
                title="Scan Success Rate"
                value={`${stats?.scans?.success_rate || 0}%`}
                subtitle={`${
                  stats?.scans?.by_status?.completed || 0
                } completed`}
                icon={<CheckCircleIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.green}
                bgGradient={colorToBgGradient.green}
              />
            </div>

            {/* Health Score and Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* System Health */}
              <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                  <ServerIcon className="h-5 w-5 text-cyan-400" />
                  System Health
                </h3>
                <div className="flex items-center justify-center mb-6">
                  <HealthScoreRing score={stats?.system?.health_score || 0} />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Users by Role</span>
                  </div>
                  {Object.entries(stats?.users?.by_role || {}).map(
                    ([role, count]) => (
                      <div
                        key={role}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm text-gray-500 capitalize">
                          {role.replace("_", " ")}
                        </span>
                        <span className="text-sm text-white font-medium">
                          {count}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* Recent Activity */}
              <div className="lg:col-span-2 bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <BoltIcon className="h-5 w-5 text-amber-400" />
                    Recent Activity
                  </h3>
                  <button
                    onClick={() =>
                      queryClient.invalidateQueries(["admin-activity"])
                    }
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
                  >
                    <ArrowPathIcon className="h-4 w-4" />
                  </button>
                </div>
                <div className="space-y-1 max-h-80 overflow-y-auto">
                  {activityLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <ArrowPathIcon className="h-6 w-6 text-gray-400 animate-spin" />
                    </div>
                  ) : (
                    activityData?.activities
                      ?.slice(0, 10)
                      .map((activity, index) => (
                        <ActivityItem key={index} activity={activity} />
                      ))
                  )}
                </div>
              </div>
            </div>

            {/* Findings Distribution */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FireIcon className="h-5 w-5 text-red-400" />
                Findings by Severity (All Projects)
              </h3>
              <div className="grid grid-cols-5 gap-4">
                {["critical", "high", "medium", "low", "info"].map(
                  (severity) => {
                    const count =
                      stats?.scans?.findings_by_severity?.[severity] || 0;
                    const total = stats?.scans?.total_findings || 1;
                    const percentage = Math.round((count / total) * 100) || 0;
                    const colors = {
                      critical: "bg-red-500",
                      high: "bg-orange-500",
                      medium: "bg-amber-500",
                      low: "bg-blue-500",
                      info: "bg-gray-500",
                    };
                    return (
                      <div key={severity} className="text-center">
                        <div className="h-24 flex items-end justify-center mb-2">
                          <div
                            className={`w-full max-w-[60px] ${colors[severity]} rounded-t-lg transition-all duration-500`}
                            style={{ height: `${Math.max(percentage, 5)}%` }}
                          />
                        </div>
                        <p className="text-2xl font-bold text-white">{count}</p>
                        <p className="text-xs text-gray-500 capitalize">
                          {severity}
                        </p>
                      </div>
                    );
                  }
                )}
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === "users" && (
          <div className="space-y-6">
            {/* Search and Filters */}
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search users by name, email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
              <button
                onClick={() => queryClient.invalidateQueries(["admin-users"])}
                className="p-2.5 text-gray-400 hover:text-white bg-gray-800/50 border border-gray-700 rounded-xl hover:bg-gray-700/50 transition-colors"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Users Table */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-800/50 border-b border-gray-700/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Activity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Last Login
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {usersLoading ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center">
                        <ArrowPathIcon className="h-6 w-6 text-gray-400 animate-spin mx-auto" />
                      </td>
                    </tr>
                  ) : (
                    usersData?.users?.map((u) => (
                      <UserRow
                        key={u.id}
                        user={u}
                        onEditRole={(u) =>
                          setEditModal({ type: "role", user: u })
                        }
                        onEditStatus={(u) =>
                          setEditModal({ type: "status", user: u })
                        }
                        onDelete={(u) => {
                          if (
                            confirm(
                              `Are you sure you want to delete user "${u.username}"?`
                            )
                          ) {
                            deleteUserMutation.mutate(u.id);
                          }
                        }}
                      />
                    ))
                  )}
                </tbody>
              </table>
              {usersData?.pagination && (
                <div className="px-4 py-3 border-t border-gray-700/50 text-sm text-gray-500">
                  Showing {usersData.users?.length || 0} of{" "}
                  {usersData.pagination.total} users
                </div>
              )}
            </div>
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === "projects" && (
          <div className="space-y-6">
            {/* Search */}
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search projects..."
                  value={projectSearch}
                  onChange={(e) => setProjectSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
              <button
                onClick={() =>
                  queryClient.invalidateQueries(["admin-projects"])
                }
                className="p-2.5 text-gray-400 hover:text-white bg-gray-800/50 border border-gray-700 rounded-xl hover:bg-gray-700/50 transition-colors"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Projects Table */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-800/50 border-b border-gray-700/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Project
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Owner
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Scans
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Findings
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {projectsLoading ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center">
                        <ArrowPathIcon className="h-6 w-6 text-gray-400 animate-spin mx-auto" />
                      </td>
                    </tr>
                  ) : (
                    projectsData?.projects?.map((p) => (
                      <ProjectRow
                        key={p.id}
                        project={p}
                        onDelete={(p) => {
                          if (
                            confirm(
                              `Are you sure you want to delete project "${p.name}"? This will also delete all associated scan reports.`
                            )
                          ) {
                            deleteProjectMutation.mutate(p.id);
                          }
                        }}
                      />
                    ))
                  )}
                </tbody>
              </table>
              {projectsData?.pagination && (
                <div className="px-4 py-3 border-t border-gray-700/50 text-sm text-gray-500">
                  Showing {projectsData.projects?.length || 0} of{" "}
                  {projectsData.pagination.total} projects
                </div>
              )}
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === "activity" && (
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <BoltIcon className="h-5 w-5 text-amber-400" />
                System Activity Log
              </h3>
              <button
                onClick={() =>
                  queryClient.invalidateQueries(["admin-activity"])
                }
                className="px-4 py-2 text-sm text-gray-400 hover:text-white bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 transition-colors flex items-center gap-2"
              >
                <ArrowPathIcon className="h-4 w-4" />
                Refresh
              </button>
            </div>
            <div className="space-y-1">
              {activityLoading ? (
                <div className="flex items-center justify-center py-12">
                  <ArrowPathIcon className="h-8 w-8 text-gray-400 animate-spin" />
                </div>
              ) : (
                activityData?.activities?.map((activity, index) => (
                  <ActivityItem key={index} activity={activity} />
                ))
              )}
            </div>
          </div>
        )}

        {/* Edit Role Modal */}
        {editModal.type === "role" && editModal.user && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-white mb-4">
                Change User Role
              </h3>
              <p className="text-gray-400 mb-4">
                Updating role for{" "}
                <span className="text-white font-medium">
                  {editModal.user.username}
                </span>
              </p>
              <div className="space-y-2 mb-6">
                {["admin", "security_manager", "developer", "viewer"].map(
                  (role) => (
                    <button
                      key={role}
                      onClick={() =>
                        updateRoleMutation.mutate({
                          userId: editModal.user.id,
                          role,
                        })
                      }
                      disabled={updateRoleMutation.isPending}
                      className={`w-full p-3 rounded-lg border text-left transition-colors ${
                        editModal.user.role === role
                          ? "border-blue-500 bg-blue-500/20 text-white"
                          : "border-gray-700 hover:border-gray-600 text-gray-400 hover:text-white"
                      }`}
                    >
                      <span className="capitalize">
                        {role.replace("_", " ")}
                      </span>
                    </button>
                  )
                )}
              </div>
              <button
                onClick={() => setEditModal({ type: null, user: null })}
                className="w-full py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Edit Status Modal */}
        {editModal.type === "status" && editModal.user && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-white mb-4">
                Change User Status
              </h3>
              <p className="text-gray-400 mb-4">
                Updating status for{" "}
                <span className="text-white font-medium">
                  {editModal.user.username}
                </span>
              </p>
              <div className="space-y-2 mb-6">
                {[
                  "active",
                  "inactive",
                  "suspended",
                  "pending_verification",
                ].map((status) => (
                  <button
                    key={status}
                    onClick={() =>
                      updateStatusMutation.mutate({
                        userId: editModal.user.id,
                        status,
                      })
                    }
                    disabled={updateStatusMutation.isPending}
                    className={`w-full p-3 rounded-lg border text-left transition-colors ${
                      editModal.user.status === status
                        ? "border-blue-500 bg-blue-500/20 text-white"
                        : "border-gray-700 hover:border-gray-600 text-gray-400 hover:text-white"
                    }`}
                  >
                    <span className="capitalize">
                      {status.replace("_", " ")}
                    </span>
                  </button>
                ))}
              </div>
              <button
                onClick={() => setEditModal({ type: null, user: null })}
                className="w-full py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
