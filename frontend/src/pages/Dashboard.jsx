/**
 * Dashboard Page Component
 * Main dashboard with analytics overview and recent activity
 */
import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  SparklesIcon,
  PlusIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";
import { ChartBarIcon } from "@heroicons/react/24/solid";
import {
  PageContainer,
  PageHeader,
  GlassCard,
  SectionHeader,
} from "../layouts";
import { ProjectList } from "../components/projects";
import { reportsAPI } from "../services/api";

/**
 * Stat Card Component
 */
const StatCard = ({ stat, index }) => (
  <div
    className="group relative bg-gray-800/30 rounded-xl lg:rounded-2xl p-4 lg:p-6 border border-gray-700/30 hover:border-gray-600/50 transition-all duration-300 hover:scale-[1.02]"
    style={{ animationDelay: `${index * 0.1}s` }}
  >
    <div
      className={`absolute inset-0 rounded-xl lg:rounded-2xl bg-gradient-to-r ${stat.gradient} opacity-0 group-hover:opacity-5 transition-opacity`}
    />
    <div className="relative">
      <div className="flex items-center justify-between mb-3 lg:mb-4">
        <div
          className={`p-2 lg:p-3 rounded-xl lg:rounded-2xl bg-gradient-to-r ${stat.gradient} shadow-lg`}
        >
          <stat.icon className="h-5 w-5 lg:h-6 lg:w-6 text-white" />
        </div>
        <span
          className={`text-xs lg:text-sm font-medium ${
            stat.trend >= 0 ? "text-green-400" : "text-red-400"
          } flex items-center`}
        >
          {stat.trend >= 0 ? "↑" : "↓"} {Math.abs(stat.trend)}%
        </span>
      </div>
      <h3 className="text-2xl lg:text-3xl font-bold text-white mb-1">
        {stat.value}
      </h3>
      <p className="text-xs lg:text-sm text-gray-400">{stat.label}</p>
    </div>
  </div>
);

/**
 * Quick Action Card Component
 */
const QuickActionCard = ({ action, index }) => (
  <button
    key={action.name}
    onClick={action.action}
    style={{ animationDelay: `${index * 0.1}s` }}
    className="group relative p-4 lg:p-6 rounded-xl lg:rounded-2xl bg-gray-800/30 border border-gray-700/30 hover:border-gray-600/50 transition-all duration-300 hover:scale-[1.02] text-left animate-fade-in-up"
  >
    <div
      className={`absolute inset-0 rounded-xl lg:rounded-2xl bg-gradient-to-r ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity`}
    />
    <div className="relative flex items-center space-x-3 lg:space-x-4">
      <div
        className={`p-2.5 lg:p-3 rounded-xl lg:rounded-2xl bg-gradient-to-r ${action.gradient} shadow-lg`}
      >
        <action.icon className="h-5 w-5 lg:h-6 lg:w-6 text-white" />
      </div>
      <div>
        <h4 className="text-sm lg:text-base font-semibold text-white">
          {action.name}
        </h4>
        <p className="text-xs lg:text-sm text-gray-400">{action.description}</p>
      </div>
    </div>
  </button>
);

/**
 * Activity Item Component
 */
const ActivityItem = ({ notification }) => (
  <div className="flex items-center space-x-3 lg:space-x-4 p-3 lg:p-4 rounded-xl lg:rounded-2xl bg-gray-800/30 hover:bg-gray-800/50 transition-all">
    <div className="p-1.5 lg:p-2 rounded-lg lg:rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 flex-shrink-0">
      <CheckCircleIcon className="h-3.5 w-3.5 lg:h-4 lg:w-4 text-white" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs lg:text-sm font-medium text-white truncate">
        {notification.data?.project_name || "Unknown Project"}
      </p>
      <p className="text-xs text-gray-400 truncate">{notification.message}</p>
    </div>
    <span className="text-xs text-gray-500 flex-shrink-0">
      {notification.timestamp.toLocaleTimeString()}
    </span>
  </div>
);

/**
 * Dashboard Page
 */
const Dashboard = ({ notifications = [] }) => {
  // Fetch analytics data
  const { data: analyticsData } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => reportsAPI.getAnalyticsOverview(30),
  });

  const { data: reportsData } = useQuery({
    queryKey: ["recent-reports"],
    queryFn: () => reportsAPI.getReports({ limit: 100 }),
  });

  // Calculate stats from real data
  const stats = [
    {
      label: "Total Scans",
      value: reportsData?.data?.length || 0,
      trend: 12,
      icon: ShieldCheckIcon,
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      label: "Critical Issues",
      value: analyticsData?.critical_count || 0,
      trend: -8,
      icon: ExclamationTriangleIcon,
      gradient: "from-red-500 to-pink-500",
    },
    {
      label: "Issues Resolved",
      value: analyticsData?.fixed_count || 0,
      trend: 24,
      icon: CheckCircleIcon,
      gradient: "from-green-500 to-emerald-500",
    },
    {
      label: "Security Score",
      value: `${analyticsData?.security_score || 85}%`,
      trend: 5,
      icon: SparklesIcon,
      gradient: "from-purple-500 to-pink-500",
    },
  ];

  // Quick actions
  const quickActions = [
    {
      name: "New Project",
      description: "Create and scan a repository",
      icon: PlusIcon,
      gradient: "from-blue-500 to-purple-600",
      action: () => (window.location.href = "/projects?action=new"),
    },
    {
      name: "View Reports",
      description: "Review security findings",
      icon: ShieldCheckIcon,
      gradient: "from-green-500 to-emerald-500",
      action: () => (window.location.href = "/reports"),
    },
    {
      name: "Analytics",
      description: "Explore security trends",
      icon: BoltIcon,
      gradient: "from-orange-500 to-red-500",
      action: () => (window.location.href = "/analytics"),
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Security Dashboard"
        description="Real-time overview of your security posture"
        icon={ShieldCheckIcon}
        breadcrumb={["Dashboard"]}
        actions={
          <Link
            to="/projects?action=new"
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all flex items-center gap-2 shadow-lg"
          >
            <PlusIcon className="h-4 w-4" />
            <span>New Project</span>
          </Link>
        }
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-6 mb-8 lg:mb-12">
        {stats.map((stat, index) => (
          <StatCard key={stat.label} stat={stat} index={index} />
        ))}
      </div>

      {/* Quick Actions */}
      <GlassCard className="mb-8 lg:mb-12">
        <SectionHeader
          title="Quick Actions"
          description="Common security operations"
        />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 lg:gap-4">
          {quickActions.map((action, index) => (
            <QuickActionCard key={action.name} action={action} index={index} />
          ))}
        </div>
      </GlassCard>

      {/* Activity and Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6 mb-8 lg:mb-12">
        {/* Recent Activity */}
        <GlassCard>
          <SectionHeader
            title="Recent Activity"
            description="Latest security scan updates"
          />
          <div className="space-y-3 lg:space-y-4 max-h-64 lg:max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="text-center py-6 lg:py-8">
                <div className="p-3 lg:p-4 rounded-xl lg:rounded-2xl bg-gray-800/50 inline-block mb-3 lg:mb-4">
                  <SparklesIcon className="h-6 w-6 lg:h-8 lg:w-8 text-gray-400" />
                </div>
                <p className="text-gray-400 text-sm lg:text-base">
                  No recent activity
                </p>
                <p className="text-xs lg:text-sm text-gray-500 mt-1 lg:mt-2">
                  Start a scan to see activity here
                </p>
              </div>
            ) : (
              notifications
                .slice(0, 5)
                .map((notification) => (
                  <ActivityItem
                    key={notification.id}
                    notification={notification}
                  />
                ))
            )}
          </div>
        </GlassCard>

        {/* Security Trends */}
        <GlassCard>
          <SectionHeader
            title="Security Trends"
            description="Vulnerability insights over time"
          />
          <div className="flex-1 flex flex-col items-center justify-center py-8 lg:py-12">
            <div className="p-3 lg:p-4 rounded-xl lg:rounded-2xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 inline-block mb-3 lg:mb-4">
              <ChartBarIcon className="h-8 w-8 lg:h-12 lg:w-12 text-purple-400" />
            </div>
            <p className="text-gray-400 text-sm lg:text-base mb-1 lg:mb-2">
              Advanced Analytics
            </p>
            <p className="text-xs lg:text-sm text-gray-500 text-center">
              View detailed trends in the Analytics section
            </p>
            <Link
              to="/analytics"
              className="mt-4 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg text-sm transition-colors"
            >
              View Analytics →
            </Link>
          </div>
        </GlassCard>
      </div>

      {/* Recent Projects */}
      <GlassCard>
        <SectionHeader
          title="Recent Scan Reports"
          description="Your latest security scan results"
          action={
            <Link
              to="/reports"
              className="px-3 lg:px-4 py-2 rounded-xl bg-gray-800/50 border border-gray-700/50 text-gray-300 hover:text-white hover:bg-gray-800 transition-all text-xs lg:text-sm"
            >
              View All Reports
            </Link>
          }
        />
        <ProjectList />
      </GlassCard>
    </PageContainer>
  );
};

export default Dashboard;
