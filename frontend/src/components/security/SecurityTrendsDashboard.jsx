/**
 * Security Trends Dashboard Component
 * Displays security posture trends, metrics, and analytics
 * Features: severity trends, fix velocity, period comparison, projections
 */
import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Shield,
  Target,
  Clock,
  CheckCircle,
  XCircle,
  ArrowUp,
  ArrowDown,
  Activity,
  Calendar,
  BarChart3,
  RefreshCw,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Trend direction indicator
const TrendIndicator = ({ direction, value }) => {
  const icons = {
    improving: <TrendingUp className="w-4 h-4 text-green-500" />,
    stable: <Minus className="w-4 h-4 text-yellow-500" />,
    degrading: <TrendingDown className="w-4 h-4 text-red-500" />,
  };

  const colors = {
    improving: "text-green-600 bg-green-50",
    stable: "text-yellow-600 bg-yellow-50",
    degrading: "text-red-600 bg-red-50",
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
    blue: "stroke-blue-500",
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
          className="stroke-gray-200"
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
        <span className="text-xs text-gray-500">{label}</span>
      </div>
    </div>
  );
};

// Metric card component
const MetricCard = ({ title, value, change, icon: Icon, trend, subtitle }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl font-bold text-gray-900">{value}</span>
          {change !== undefined && (
            <span
              className={`text-sm ${
                change >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {change >= 0 ? (
                <ArrowUp className="w-3 h-3 inline" />
              ) : (
                <ArrowDown className="w-3 h-3 inline" />
              )}
              {Math.abs(change)}%
            </span>
          )}
        </div>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
      {Icon && (
        <div className="p-2 bg-gray-50 rounded-lg">
          <Icon className="w-5 h-5 text-gray-600" />
        </div>
      )}
    </div>
    {trend && (
      <div className="mt-3 pt-3 border-t border-gray-100">
        <TrendIndicator direction={trend.direction} value={trend.value} />
      </div>
    )}
  </div>
);

// Simple bar chart component
const SimpleBarChart = ({ data, height = 200 }) => {
  if (!data || data.length === 0) return null;

  const maxValue = Math.max(...data.map((d) => d.value));
  const barWidth = 100 / data.length;

  return (
    <div className="relative" style={{ height }}>
      <div className="absolute inset-0 flex items-end gap-1">
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full bg-blue-500 rounded-t transition-all duration-300 hover:bg-blue-600"
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                minHeight: 4,
              }}
              title={`${item.label}: ${item.value}`}
            />
            <span className="text-xs text-gray-500 truncate max-w-full">
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Severity trend chart
const SeverityTrendChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No trend data available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b">
            <th className="pb-2">Date</th>
            <th className="pb-2 text-center">Score</th>
            <th className="pb-2 text-center text-red-600">Critical</th>
            <th className="pb-2 text-center text-orange-600">High</th>
            <th className="pb-2 text-center text-yellow-600">Medium</th>
            <th className="pb-2 text-center text-blue-600">Low</th>
            <th className="pb-2 text-center text-green-600">Fixed</th>
            <th className="pb-2 text-center text-purple-600">New</th>
          </tr>
        </thead>
        <tbody>
          {data.slice(-8).map((point, index) => (
            <tr
              key={index}
              className="border-b border-gray-50 hover:bg-gray-50"
            >
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
                      ? "bg-green-100 text-green-700"
                      : point.security_score >= 60
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {point.security_score?.toFixed(0)}
                </span>
              </td>
              <td className="py-2 text-center text-red-600 font-medium">
                {point.critical || 0}
              </td>
              <td className="py-2 text-center text-orange-600 font-medium">
                {point.high || 0}
              </td>
              <td className="py-2 text-center text-yellow-600">
                {point.medium || 0}
              </td>
              <td className="py-2 text-center text-blue-600">
                {point.low || 0}
              </td>
              <td className="py-2 text-center">
                {point.fixed > 0 && (
                  <span className="text-green-600">+{point.fixed}</span>
                )}
              </td>
              <td className="py-2 text-center">
                {point.new > 0 && (
                  <span className="text-purple-600">+{point.new}</span>
                )}
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

      const response = await fetch(
        `${API_BASE_URL}/api/enterprise/trends/dashboard?${params}`
      );
      if (!response.ok) throw new Error("Failed to fetch trends data");
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <AlertTriangle className="w-5 h-5 inline mr-2" />
        Error loading trends data: {error.message}
      </div>
    );
  }

  const data = dashboardData?.data || {};
  const current = data.current || {};
  const trends = data.trends || {};
  const charts = data.charts || {};
  const comparison = data.comparison || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Security Trends</h2>
          <p className="text-gray-500">Track your security posture over time</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">Security Score</p>
            <p className="text-3xl font-bold text-gray-900">
              {current.security_score?.toFixed(0) || 0}
            </p>
            <TrendIndicator
              direction={trends.direction}
              value={trends.improvement_pct}
            />
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
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <p className="text-sm text-gray-500">Risk Score</p>
          <p className="text-3xl font-bold text-gray-900">
            {current.risk_score?.toFixed(0) || 0}
          </p>
          <p className="text-xs text-gray-400 mt-1">Lower is better</p>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                current.risk_score <= 30
                  ? "bg-green-500"
                  : current.risk_score <= 60
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${current.risk_score || 0}%` }}
            />
          </div>
        </div>

        <MetricCard
          title="Open Findings"
          value={current.open_findings || 0}
          subtitle={`${current.fixed_7d || 0} fixed this week`}
          icon={AlertTriangle}
        />

        <MetricCard
          title="Fix Rate"
          value={`${((trends.fix_rate || 0) * 100).toFixed(0)}%`}
          subtitle="Fixed vs New ratio"
          icon={Target}
          trend={
            trends.fix_rate > 1
              ? { direction: "improving" }
              : { direction: "degrading" }
          }
        />
      </div>

      {/* Severity Breakdown */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">
          Current Severity Breakdown
        </h3>
        <div className="grid grid-cols-5 gap-4">
          {[
            {
              label: "Critical",
              key: "critical",
              color: "bg-red-500",
              textColor: "text-red-700",
            },
            {
              label: "High",
              key: "high",
              color: "bg-orange-500",
              textColor: "text-orange-700",
            },
            {
              label: "Medium",
              key: "medium",
              color: "bg-yellow-500",
              textColor: "text-yellow-700",
            },
            {
              label: "Low",
              key: "low",
              color: "bg-blue-500",
              textColor: "text-blue-700",
            },
            {
              label: "Info",
              key: "info",
              color: "bg-gray-400",
              textColor: "text-gray-600",
            },
          ].map(({ label, key, color, textColor }) => (
            <div key={key} className="text-center">
              <div className={`w-full h-2 ${color} rounded-full mb-2`} />
              <p className={`text-2xl font-bold ${textColor}`}>
                {current.severity_counts?.[key] || 0}
              </p>
              <p className="text-sm text-gray-500">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Trends */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">
            Weekly Severity Trends
          </h3>
          <SeverityTrendChart data={charts.weekly} />
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-blue-500" />
                <span className="text-gray-700">Mean Time to Remediate</span>
              </div>
              <span className="font-semibold">
                {current.mttr_hours
                  ? `${(current.mttr_hours / 24).toFixed(1)} days`
                  : "N/A"}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-gray-700">Compliance Rate</span>
              </div>
              <span className="font-semibold">
                {((current.compliance_rate || 0) * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-purple-500" />
                <span className="text-gray-700">Coverage</span>
              </div>
              <span className="font-semibold">
                {((current.coverage || 0) * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Target className="w-5 h-5 text-indigo-500" />
                <span className="text-gray-700">Projected Score (30d)</span>
              </div>
              <span className="font-semibold text-indigo-600">
                {trends.projected_score_30d?.toFixed(0) || "N/A"}
              </span>
            </div>

            {trends.time_to_target && (
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-green-500" />
                  <span className="text-gray-700">
                    Days to Target Score (90)
                  </span>
                </div>
                <span className="font-semibold text-green-600">
                  ~{trends.time_to_target} days
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Period Comparison */}
      {comparison.current_period && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">
            Period-over-Period Comparison
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-2">
                Security Score Change
              </p>
              <p
                className={`text-3xl font-bold ${
                  comparison.changes?.security_score >= 0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {comparison.changes?.security_score >= 0 ? "+" : ""}
                {comparison.changes?.security_score?.toFixed(1) || 0}
              </p>
              <p className="text-xs text-gray-400 mt-1">vs previous 30 days</p>
            </div>

            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-2">Finding Change</p>
              <p
                className={`text-3xl font-bold ${
                  comparison.changes?.findings_pct <= 0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {comparison.changes?.findings_pct > 0 ? "+" : ""}
                {comparison.changes?.findings_pct?.toFixed(1) || 0}%
              </p>
              <p className="text-xs text-gray-400 mt-1">vulnerability count</p>
            </div>

            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-2">Trend Direction</p>
              <div className="flex items-center justify-center gap-2">
                <TrendIndicator
                  direction={comparison.changes?.direction || "stable"}
                />
                <span className="text-lg font-medium capitalize">
                  {comparison.changes?.direction || "Stable"}
                </span>
              </div>
            </div>
          </div>

          {/* Insights */}
          {comparison.insights && comparison.insights.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Key Insights
              </h4>
              <ul className="space-y-1">
                {comparison.insights.map((insight, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-600 flex items-start gap-2"
                  >
                    <Activity className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Notable Changes */}
      {data.notable_changes && data.notable_changes.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">Notable Changes</h4>
          <ul className="space-y-1">
            {data.notable_changes.map((change, index) => (
              <li
                key={index}
                className="text-sm text-blue-700 flex items-center gap-2"
              >
                <BarChart3 className="w-4 h-4" />
                {change}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SecurityTrendsDashboard;
