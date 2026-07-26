import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UsersIcon,
  FolderIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BoltIcon,
  ServerIcon,
  CommandLineIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  UserPlusIcon,
  StarIcon,
  FireIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";
import { StatCard, Spinner } from "../styles/components";
import { adminAPI } from "../services/api";
import { useAuth } from "../components/auth";
import toast from "react-hot-toast";
import HealthScoreRing from "../components/admin/HealthScoreRing";
import ActivityItem from "../components/admin/ActivityItem";
import UserRow from "../components/admin/UserRow";
import ProjectRow from "../components/admin/ProjectRow";
import AdminRoleModal from "../components/admin/AdminRoleModal";
import AdminStatusModal from "../components/admin/AdminStatusModal";

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

const AdminDashboard = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");
  const [userSearch, setUserSearch] = useState("");
  const [projectSearch, setProjectSearch] = useState("");
  const [editModal, setEditModal] = useState({ type: null, user: null });

  const isAdmin = user?.role === "admin";

  const { data: stats } = useQuery({
    queryKey: ["admin-dashboard-stats"],
    queryFn: adminAPI.getDashboardStats,
    enabled: isAdmin,
    refetchInterval: 30000,
    staleTime: 30000,
  });

  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ["admin-users", userSearch],
    queryFn: () => adminAPI.getAllUsers({ search: userSearch, limit: 100 }),
    enabled: isAdmin && activeTab === "users",
    staleTime: 30000,
  });

  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ["admin-projects", projectSearch],
    queryFn: () => adminAPI.getAllProjects({ search: projectSearch, limit: 100 }),
    enabled: isAdmin && activeTab === "projects",
    staleTime: 30000,
  });

  const { data: activityData, isLoading: activityLoading } = useQuery({
    queryKey: ["admin-activity"],
    queryFn: () => adminAPI.getRecentActivity(30),
    enabled: isAdmin,
    staleTime: 30000,
  });

  const deleteUserMutation = useMutation({
    mutationFn: (userId) => adminAPI.deleteUser(userId),
    onSuccess: () => {
      toast.success("User deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete user");
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: (projectId) => adminAPI.deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete project");
    },
  });

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="max-w-2xl mx-auto mt-20">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-red-500/30 rounded-2xl p-8 text-center">
            <div className="w-20 h-20 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <LockClosedIcon className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">Admin Access Required</h2>
            <p className="text-gray-400 mb-6">This area is restricted to administrators only.</p>
            <p className="text-sm text-gray-500">
              Your current role:{" "}
              <span className="text-cyan-400 font-medium">{user?.role || "Unknown"}</span>
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
                Complete system control and monitoring • Logged in as {user?.username}
              </p>
            </div>
          </div>
        </div>

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

        {activeTab === "overview" && (
          <div className="space-y-6">
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
                subtitle="Across all users"
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
                subtitle={`${stats?.scans?.findings_by_severity?.critical || 0} critical`}
                icon={<ExclamationTriangleIcon className="h-5 w-5 text-white" />}
                gradient={
                  stats?.scans?.findings_by_severity?.critical > 0
                    ? colorToGradient.red
                    : colorToGradient.green
                }
                bgGradient={
                  stats?.scans?.findings_by_severity?.critical > 0
                    ? colorToBgGradient.red
                    : colorToBgGradient.green
                }
              />
            </div>

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
                subtitle={`${stats?.scans?.by_status?.completed || 0} completed`}
                icon={<CheckCircleIcon className="h-5 w-5 text-white" />}
                gradient={colorToGradient.green}
                bgGradient={colorToBgGradient.green}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                  {Object.entries(stats?.users?.by_role || {}).map(([role, count]) => (
                    <div key={role} className="flex items-center justify-between">
                      <span className="text-sm text-gray-500 capitalize">
                        {role.replace("_", " ")}
                      </span>
                      <span className="text-sm text-white font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="lg:col-span-2 bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <BoltIcon className="h-5 w-5 text-amber-400" />
                    Recent Activity
                  </h3>
                  <button
                    onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-activity"] })}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
                  >
                    <ArrowPathIcon className="h-4 w-4" />
                  </button>
                </div>
                <div className="space-y-1 max-h-80 overflow-y-auto">
                  {activityLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Spinner size="lg" />
                    </div>
                  ) : (
                    activityData?.activities
                      ?.slice(0, 10)
                      .map((activity) => (
                        <ActivityItem key={activity.id || activity.timestamp} activity={activity} />
                      ))
                  )}
                </div>
              </div>
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FireIcon className="h-5 w-5 text-red-400" />
                Findings by Severity (All Projects)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                {["critical", "high", "medium", "low", "info"].map((severity) => {
                  const count = stats?.scans?.findings_by_severity?.[severity] || 0;
                  const total = stats?.scans?.total_findings || 1;
                  const percentage = Math.round((count / total) * 100) || 0;
                  const barColors = {
                    critical: "bg-red-500",
                    high: "bg-orange-500",
                    medium: "bg-amber-500",
                    low: "bg-cyan-500",
                    info: "bg-gray-500",
                  };
                  return (
                    <div key={severity} className="text-center">
                      <div className="h-24 flex items-end justify-center mb-2">
                        <div
                          className={`w-full max-w-[60px] ${barColors[severity]} rounded-t-lg transition-all duration-500`}
                          style={{ height: `${Math.max(percentage, 5)}%` }}
                        />
                      </div>
                      <p className="text-2xl font-bold text-white">{count}</p>
                      <p className="text-xs text-gray-500 capitalize">{severity}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === "users" && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search users by name, email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                />
              </div>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-users"] })}
                className="p-2.5 text-gray-400 hover:text-white bg-gray-800/50 border border-gray-700 rounded-xl hover:bg-gray-700/50 transition-colors"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>

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
                        <Spinner size="lg" />
                      </td>
                    </tr>
                  ) : (
                    usersData?.users?.map((u) => (
                      <UserRow
                        key={u.id}
                        user={u}
                        onEditRole={(u) => setEditModal({ type: "role", user: u })}
                        onEditStatus={(u) => setEditModal({ type: "status", user: u })}
                        onDelete={(u) => {
                          if (confirm(`Are you sure you want to delete user "${u.username}"?`)) {
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
                  Showing {usersData.users?.length || 0} of {usersData.pagination.total} users
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "projects" && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search projects..."
                  value={projectSearch}
                  onChange={(e) => setProjectSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                />
              </div>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-projects"] })}
                className="p-2.5 text-gray-400 hover:text-white bg-gray-800/50 border border-gray-700 rounded-xl hover:bg-gray-700/50 transition-colors"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>

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
                        <Spinner size="lg" />
                      </td>
                    </tr>
                  ) : (
                    projectsData?.projects?.map((p) => (
                      <ProjectRow
                        key={p.id}
                        project={p}
                        onDelete={(p) => {
                          if (confirm(`Are you sure you want to delete project "${p.name}"?`)) {
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
                  Showing {projectsData.projects?.length || 0} of {projectsData.pagination.total}{" "}
                  projects
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "activity" && (
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <BoltIcon className="h-5 w-5 text-amber-400" />
                System Activity Log
              </h3>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-activity"] })}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 transition-colors flex items-center gap-2"
              >
                <ArrowPathIcon className="h-4 w-4" />
                Refresh
              </button>
            </div>
            <div className="space-y-1">
              {activityLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Spinner size="lg" />
                </div>
              ) : (
                activityData?.activities?.map((activity) => (
                  <ActivityItem key={activity.id || activity.timestamp} activity={activity} />
                ))
              )}
            </div>
          </div>
        )}

        {editModal.type === "role" && editModal.user && (
          <AdminRoleModal
            user={editModal.user}
            onClose={() => setEditModal({ type: null, user: null })}
          />
        )}
        {editModal.type === "status" && editModal.user && (
          <AdminStatusModal
            user={editModal.user}
            onClose={() => setEditModal({ type: null, user: null })}
          />
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
