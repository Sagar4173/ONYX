import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  UsersIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";
import api from "../../services/api";
import { useAuth } from "../auth";
import { PageContainer, PageHeader } from "../../layouts";
import ParticleBackground from "../projects/ParticleBackground";
import UserFilters from "./UserFilters";
import UserTable from "./UserTable";
import UserModal from "./UserModal";
import UserStatsTab from "./UserStatsTab";
import UserSecurityTab from "./UserSecurityTab";
import UserSettingsTab from "./UserSettingsTab";

const TABS = [
  { key: "users", label: "Users", icon: UsersIcon },
  { key: "statistics", label: "Statistics", icon: ChartBarIcon },
  { key: "security", label: "Security", icon: ShieldCheckIcon },
  { key: "settings", label: "Settings", icon: Cog6ToothIcon },
];

const contentAnim = { hidden: { opacity: 0, x: 8 }, show: { opacity: 1, x: 0 } };

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

  const hasAdminAccess = user?.role === "admin" || user?.role === "security_manager";

  const { data: usersData, isLoading: usersLoading, error: usersError } = useQuery({
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
    enabled: isAuthenticated && hasAdminAccess,
    retry: false,
  });

  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: ["userStatistics"],
    queryFn: async () => {
      const response = await api.get("/users/statistics");
      return response.data;
    },
    enabled: isAuthenticated && hasAdminAccess,
    retry: false,
  });

  const { data: securityOverview, isLoading: securityLoading } = useQuery({
    queryKey: ["securityOverview"],
    queryFn: async () => {
      const response = await api.get("/users/security/overview");
      return response.data;
    },
    enabled: isAuthenticated && hasAdminAccess,
    retry: false,
  });

  const handleUserSelect = (userId) => {
    setSelectedUsers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    if (selectedUsers.length === usersData?.users?.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(usersData?.users?.map((user) => user.id) || []);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
        <div className="relative max-w-7xl mx-auto">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-8 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Authentication Required</h2>
            <p className="text-gray-400">Please log in to access the user management system.</p>
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
            <h2 className="text-2xl font-bold text-white mb-2">Access Denied</h2>
            <p className="text-gray-400 mb-4">
              You need administrator or security manager privileges to access the user management
              system.
            </p>
            <p className="text-gray-500 text-sm">
              Current role: <span className="text-cyan-400">{user?.role || "Unknown"}</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <PageHeader
            title="User Management"
            description="Manage users, roles, and security settings"
            icon={UsersIcon}
            breadcrumb={["Users"]}
          />

          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-1 mb-6">
            <nav className="flex space-x-1">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setSelectedTab(tab.key)}
                    className={`relative flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                      selectedTab === tab.key
                        ? "text-white"
                        : "text-gray-400 hover:text-gray-300 hover:bg-gray-800/50"
                    }`}
                  >
                    {selectedTab === tab.key && (
                      <motion.div
                        layoutId="user-tab"
                        className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-xl"
                        initial={false}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10 flex items-center space-x-2">
                      <Icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </span>
                  </button>
                );
              })}
            </nav>
          </div>

          <motion.div
            key={selectedTab}
            variants={contentAnim}
            initial="hidden"
            animate="show"
            transition={{ duration: 0.2 }}
          >
            {selectedTab === "users" && (
              <div className="space-y-6">
                <UserFilters
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                  filters={filters}
                  setFilters={setFilters}
                  selectedUsers={selectedUsers}
                  setSelectedUsers={setSelectedUsers}
                />
                <UserTable
                  usersData={usersData}
                  usersLoading={usersLoading}
                  usersError={usersError}
                  selectedUsers={selectedUsers}
                  onSelectAll={handleSelectAll}
                  onSelectUser={handleUserSelect}
                  onViewUser={(user) => {
                    setSelectedUser(user);
                    setShowUserModal(true);
                  }}
                />
              </div>
            )}
            {selectedTab === "statistics" && (
              <UserStatsTab statistics={statistics} statsLoading={statsLoading} />
            )}
            {selectedTab === "security" && (
              <UserSecurityTab
                securityOverview={securityOverview}
                securityLoading={securityLoading}
              />
            )}
            {selectedTab === "settings" && <UserSettingsTab />}
          </motion.div>

          <UserModal
            user={selectedUser}
            isOpen={showUserModal}
            onClose={() => {
              setShowUserModal(false);
              setSelectedUser(null);
            }}
          />
        </div>
      </PageContainer>
    </div>
  );
};

export default UserManagement;
