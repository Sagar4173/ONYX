/**
 * Security Trends Dashboard Component
 * Displays security posture trends, metrics, and analytics
 * Features: severity trends, fix velocity, period comparison, projections
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ViewfinderCircleIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChartBarSquareIcon,
  CalendarIcon,
  ChartBarIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";

// Import centralized styles
import { Card, statusStyles } from "@styles";

// API Configuration - Production ready with environment variable support
const API_BASE_URL = import.meta.env.DEV
  ? "http://127.0.0.1:8000"
  : import.meta.env.VITE_API_URL || "/api";

// Trend direction indicator - using centralized status styles
const TrendIndicator = ({ direction, value }) => {
  const icons = {
    improving: <ArrowTrendingUpIcon className="w-4 h-4 text-green-500" />,
    stable: <MinusIcon className="w-4 h-4 text-yellow-500" />,
    degrading: <ArrowTrendingDownIcon className="w-4 h-4 text-red-500" />,
  };

  const colors = {
    improving: statusStyles.indicator.success,
    stable: statusStyles.indicator.warning,
    degrading: statusStyles.indicator.danger,
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
        colors[direction] || colors.stable
      }`}
    >
      {icons[direction]}
      {value !== undefined && (
        <span>
          {value > 0 ? "+" : ""}
          {value.toFixed(1)}%
        </span>
      )}
    </span>
  );
};

// Circular progress indicator
const CircularProgress = ({ value, label, color = "blue", size = 120 }) => {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (value / 100) * circumference;

  const colorClasses = {
    blue: "stroke-cyan-500",
    green: "stroke-green-500",
    red: "stroke-red-500",
    yellow: "stroke-yellow-500",
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          className="stroke-gray-700"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`${colorClasses[color]} transition-all duration-500`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{value.toFixed(0)}</span>
        <span className="text-xs text-gray-400">{label}</span>
      </div>
    </div>
  );
};

// Metric card component
const MetricCard = ({ title, value, change, icon: Icon, trend, subtitle }) => (
  <Card className="hover:shadow-md transition-shadow">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-400">{title}</p>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl font-bold text-white">{value}</span>
          {change !== undefined && (
            <span className={`text-sm ${change >= 0 ? "text-green-400" : "text-red-400"}`}>
              {change >= 0 ? (
                <ArrowUpIcon className="w-3 h-3 inline" />
              ) : (
                <ArrowDownIcon className="w-3 h-3 inline" />
              )}
              {Math.abs(change)}%
            </span>
          )}
        </div>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
      {Icon && (
        <div className="p-2 bg-gray-800/30 rounded-lg">
          <Icon className="w-5 h-5 text-gray-300" />
        </div>
      )}
    </div>
    {trend && (
      <div className="mt-3 pt-3 border-t border-gray-700/50">
        <TrendIndicator direction={trend.direction} value={trend.value} />
      </div>
    )}
  </Card>
);

// Simple bar chart component
const _SimpleBarChart = ({ data, height = 200 }) => {
  if (!data || data.length === 0) return null;

  const maxValue = Math.max(...data.map((d) => d.value));
  const _barWidth = 100 / data.length;

  return (
    <div className="relative" style={{ height }}>
      <div className="absolute inset-0 flex items-end gap-1">
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full bg-cyan-500 rounded-t transition-all duration-300 hover:bg-cyan-600"
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                minHeight: 4,
              }}
              title={`${item.label}: ${item.value}`}
            />
            <span className="text-xs text-gray-400 truncate max-w-full">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Severity trend chart
const SeverityTrendChart = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="text-center text-gray-400 py-8">No trend data available</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b">
            <th className="pb-2">Date</th>
            <th className="pb-2 text-center">Score</th>
            <th className="pb-2 text-center text-red-400">Critical</th>
            <th className="pb-2 text-center text-orange-600">High</th>
            <th className="pb-2 text-center text-yellow-600">Medium</th>
            <th className="pb-2 text-center text-cyan-600">Low</th>
            <th className="pb-2 text-center text-green-400">Fixed</th>
            <th className="pb-2 text-center text-violet-400">New</th>
          </tr>
        </thead>
        <tbody>
          {data.slice(-8).map((point, index) => (
            <tr key={index} className="border-b border-gray-700/50 hover:bg-gray-800/30">
              <td className="py-2">
                {new Date(point.date).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })}
              </td>
              <td className="py-2 text-center">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    point.security_score >= 80
                      ? "bg-green-900/30 text-green-400"
                      : point.security_score >= 60
                        ? "bg-yellow-900/30 text-yellow-400"
                        : "bg-red-900/30 text-red-400"
                  }`}
                >
                  {point.security_score?.toFixed(0)}
                </span>
              </td>
              <td className="py-2 text-center text-red-400 font-medium">{point.critical || 0}</td>
              <td className="py-2 text-center text-orange-600 font-medium">{point.high || 0}</td>
              <td className="py-2 text-center text-yellow-600">{point.medium || 0}</td>
              <td className="py-2 text-center text-cyan-600">{point.low || 0}</td>
              <td className="py-2 text-center">
                {point.fixed > 0 && <span className="text-green-400">+{point.fixed}</span>}
              </td>
              <td className="py-2 text-center">
                {point.new > 0 && <span className="text-violet-400">+{point.new}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Main component
const SecurityTrendsDashboard = ({ projectId = null }) => {
  const [period, setPeriod] = useState("weekly");

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["security-trends-dashboard", projectId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (projectId) params.append("project_id", projectId);

      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/api/enterprise/trends/dashboard?${params}`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
        },
      });
      if (!response.ok) throw new Error("Failed to fetch trends data");
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-center h-64"
      >
        <ArrowPathIcon className="w-8 h-8 text-cyan-500 animate-spin" />
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-900/30 border border-red-700/50 rounded-lg p-4 text-red-400"
      >
        <ExclamationTriangleIcon className="w-5 h-5 inline mr-2" />
        Error loading trends data: {error.message}
      </motion.div>
    );
  }

  const data = dashboardData?.data || {};
  const current = data.current || {};
  const trends = data.trends || {};
  const charts = data.charts || {};
  const comparison = data.comparison || {};

  const staggerVariants = {
    hidden: { opacity: 0, y: 12 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: { delay: i * 0.06, duration: 0.3 },
    }),
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      className="space-y-6"
      variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
    >
      <motion.div custom={0} variants={staggerVariants}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">Security Trends</h2>
            <p className="text-gray-400">Track your security posture over time</p>
          </div>
        <div className="flex items-center gap-3">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 border border-gray-700/50 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500 bg-gray-800 text-white"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
          >
            <ArrowPathIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
      </motion.div>

      <motion.div custom={1} variants={staggerVariants}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Security Score</p>
            <p className="text-3xl font-bold text-white">
              {current.security_score?.toFixed(0) || 0}
            </p>
            <TrendIndicator direction={trends.direction} value={trends.improvement_pct} />
          </div>
          <CircularProgress
            value={current.security_score || 0}
            label="Score"
            color={
              current.security_score >= 80
                ? "green"
                : current.security_score >= 60
                  ? "yellow"
                  : "red"
            }
            size={80}
          />
        </Card>

        <Card>
          <p className="text-sm text-gray-400">Risk Score</p>
          <p className="text-3xl font-bold text-white">{current.risk_score?.toFixed(0) || 0}</p>
          <p className="text-xs text-gray-400 mt-1">Lower is better</p>
          <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                current.risk_score <= 30
                  ? "bg-green-900/300"
                  : current.risk_score <= 60
                    ? "bg-yellow-500"
                    : "bg-red-500"
              }`}
              style={{ width: `${current.risk_score || 0}%` }}
            />
          </div>
        </Card>

        <MetricCard
          title="Open Findings"
          value={current.open_findings || 0}
          subtitle={`${current.fixed_7d || 0} fixed this week`}
          icon={ExclamationTriangleIcon}
        />

        <MetricCard
          title="Fix Rate"
          value={`${((trends.fix_rate || 0) * 100).toFixed(0)}%`}
          subtitle="Fixed vs New ratio"
          icon={ViewfinderCircleIcon}
          trend={trends.fix_rate > 1 ? { direction: "improving" } : { direction: "degrading" }}
        />
      </div>
      </motion.div>

      <motion.div custom={2} variants={staggerVariants}>
        <Card padding="lg">
        <h3 className="font-semibold text-white mb-4">Current Severity Breakdown</h3>
        <div className="grid grid-cols-5 gap-4">
          {[
            {
              label: "Critical",
              key: "critical",
              color: "bg-red-500",
              textColor: "text-red-400",
            },
            {
              label: "High",
              key: "high",
              color: "bg-orange-500",
              textColor: "text-orange-400",
            },
            {
              label: "Medium",
              key: "medium",
              color: "bg-yellow-500",
              textColor: "text-yellow-400",
            },
            {
              label: "Low",
              key: "low",
              color: "bg-cyan-500",
              textColor: "text-cyan-400",
            },
            {
              label: "Info",
              key: "info",
              color: "bg-gray-400",
              textColor: "text-gray-300",
            },
          ].map(({ label, key, color, textColor }) => (
            <div key={key} className="text-center">
              <div className={`w-full h-2 ${color} rounded-full mb-2`} />
              <p className={`text-2xl font-bold ${textColor}`}>
                {current.severity_counts?.[key] || 0}
              </p>
              <p className="text-sm text-gray-400">{label}</p>
            </div>
          ))}
        </div>
      </Card>
      </motion.div>

      <motion.div custom={3} variants={staggerVariants}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Trends */}
        <Card padding="lg">
          <h3 className="font-semibold text-white mb-4">Weekly Severity Trends</h3>
          <SeverityTrendChart data={charts.weekly} />
        </Card>

        {/* Quick Stats */}
        <Card padding="lg">
          <h3 className="font-semibold text-white mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <ClockIcon className="w-5 h-5 text-cyan-500" />
                <span className="text-gray-200">Mean Time to Remediate</span>
              </div>
              <span className="font-semibold">
                {current.mttr_hours ? `${(current.mttr_hours / 24).toFixed(1)} days` : "N/A"}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                <span className="text-gray-200">Compliance Rate</span>
              </div>
              <span className="font-semibold">
                {((current.compliance_rate || 0) * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <ShieldCheckIcon className="w-5 h-5 text-violet-500" />
                <span className="text-gray-200">Coverage</span>
              </div>
              <span className="font-semibold">{((current.coverage || 0) * 100).toFixed(0)}%</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <ViewfinderCircleIcon className="w-5 h-5 text-cyan-500" />
                <span className="text-gray-200">Projected Score (30d)</span>
              </div>
              <span className="font-semibold text-cyan-400">
                {trends.projected_score_30d?.toFixed(0) || "N/A"}
              </span>
            </div>

            {trends.time_to_target && (
              <div className="flex items-center justify-between p-3 bg-green-900/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <CalendarIcon className="w-5 h-5 text-green-500" />
                  <span className="text-gray-200">Days to Target Score (90)</span>
                </div>
                <span className="font-semibold text-green-400">~{trends.time_to_target} days</span>
              </div>
            )}
          </div>
        </Card>
      </div>
      </motion.div>

      {comparison.current_period && (
        <motion.div custom={4} variants={staggerVariants}>
          <Card padding="lg">
          <h3 className="font-semibold text-white mb-4">Period-over-Period Comparison</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-gray-800/30 rounded-lg">
              <p className="text-sm text-gray-400 mb-2">Security Score Change</p>
              <p
                className={`text-3xl font-bold ${
                  comparison.changes?.security_score >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {comparison.changes?.security_score >= 0 ? "+" : ""}
                {comparison.changes?.security_score?.toFixed(1) || 0}
              </p>
              <p className="text-xs text-gray-400 mt-1">vs previous 30 days</p>
            </div>

            <div className="text-center p-4 bg-gray-800/30 rounded-lg">
              <p className="text-sm text-gray-400 mb-2">Finding Change</p>
              <p
                className={`text-3xl font-bold ${
                  comparison.changes?.findings_pct <= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {comparison.changes?.findings_pct > 0 ? "+" : ""}
                {comparison.changes?.findings_pct?.toFixed(1) || 0}%
              </p>
              <p className="text-xs text-gray-400 mt-1">vulnerability count</p>
            </div>

            <div className="text-center p-4 bg-gray-800/30 rounded-lg">
              <p className="text-sm text-gray-400 mb-2">Trend Direction</p>
              <div className="flex items-center justify-center gap-2">
                <TrendIndicator direction={comparison.changes?.direction || "stable"} />
                <span className="text-lg font-medium capitalize">
                  {comparison.changes?.direction || "Stable"}
                </span>
              </div>
            </div>
          </div>

          {/* Insights */}
          {comparison.insights && comparison.insights.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-700/50">
              <h4 className="text-sm font-medium text-gray-200 mb-2">Key Insights</h4>
              <ul className="space-y-1">
                {comparison.insights.map((insight, index) => (
                  <li key={index} className="text-sm text-gray-300 flex items-start gap-2">
                    <ChartBarSquareIcon className="w-4 h-4 text-cyan-500 mt-0.5 flex-shrink-0" />
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
        </motion.div>
      )}

      {/* Notable Changes */}
      {data.notable_changes && data.notable_changes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          custom={5}
          variants={staggerVariants}
          className="bg-cyan-900/30 border border-cyan-700/50 rounded-lg p-4"
        >
          <h4 className="font-medium text-cyan-300 mb-2">Notable Changes</h4>
          <ul className="space-y-1">
            {data.notable_changes.map((change, index) => (
              <li key={index} className="text-sm text-cyan-300 flex items-center gap-2">
                <ChartBarIcon className="w-4 h-4" />
                {change}
              </li>
            ))}
          </ul>
        </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default SecurityTrendsDashboard;
