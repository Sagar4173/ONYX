/**
 * Project Details Component for SecureDevOps Platform
 * Comprehensive project overview with security metrics and scan history
 */
import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeftIcon,
  CalendarIcon,
  ChartBarIcon,
  ClockIcon,
  CodeBracketIcon,
  CogIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  GlobeAltIcon,
  PencilIcon,
  PlayIcon,
  ShieldCheckIcon,
  TagIcon,
  TrashIcon,
  UserIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { projectsAPI, reportsAPI, utils } from "../services/api";

const ProjectDetails = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  // Fetch project details
  const {
    data: project,
    isLoading: projectLoading,
    error: projectError,
  } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsAPI.getProject(projectId),
    enabled: !!projectId,
  });

  // Fetch project scan history
  const { data: scanHistory, isLoading: scanHistoryLoading } = useQuery({
    queryKey: ["projectScans", projectId],
    queryFn: () => reportsAPI.getReports({ project_id: projectId, limit: 20 }),
    enabled: !!projectId,
  });

  // Fetch project analytics
  const { data: projectAnalytics } = useQuery({
    queryKey: ["projectAnalytics", projectId],
    queryFn: () => projectsAPI.getProjectAnalytics(projectId),
    enabled: !!projectId,
  });

  // Start new scan mutation
  const startScanMutation = useMutation({
    mutationFn: (scanData) => reportsAPI.startScan(scanData),
    onSuccess: () => {
      toast.success("Security scan started successfully!");
      queryClient.invalidateQueries(["projectScans", projectId]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to start scan");
    },
  });

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: () => projectsAPI.deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted successfully!");
      navigate("/projects");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete project");
    },
  });

  const handleStartScan = () => {
    if (!project) return;

    startScanMutation.mutate({
      repository_url: project.repository_url,
      branch: project.repository.branch || "main",
      scan_types: project.scan_config.enabled_scanners,
      project_id: projectId,
    });
  };

  const handleDeleteProject = () => {
    deleteProjectMutation.mutate();
    setShowDeleteModal(false);
  };

  if (projectLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-8">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading project details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-8">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <ExclamationCircleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">
              Project Not Found
            </h2>
            <p className="text-gray-400 mb-6">
              The project you're looking for doesn't exist or you don't have
              access to it.
            </p>
            <button
              onClick={() => navigate("/projects")}
              className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all"
            >
              Back to Projects
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "critical":
        return "text-red-400 bg-red-500/20";
      case "high":
        return "text-orange-400 bg-orange-500/20";
      case "medium":
        return "text-yellow-400 bg-yellow-500/20";
      case "low":
        return "text-green-400 bg-green-500/20";
      default:
        return "text-gray-400 bg-gray-500/20";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "text-green-400 bg-green-500/20";
      case "inactive":
        return "text-yellow-400 bg-yellow-500/20";
      case "archived":
        return "text-gray-400 bg-gray-500/20";
      default:
        return "text-gray-400 bg-gray-500/20";
    }
  };

  const totalVulns =
    project.vulnerability_count.critical +
    project.vulnerability_count.high +
    project.vulnerability_count.medium +
    project.vulnerability_count.low;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate("/projects")}
              className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-white">{project.name}</h1>
              <p className="text-gray-400 mt-1">
                {project.description || "No description provided"}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleStartScan}
              disabled={startScanMutation.isPending}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition-all flex items-center space-x-2"
            >
              <PlayIcon className="h-5 w-5" />
              <span>
                {startScanMutation.isPending ? "Starting..." : "Start Scan"}
              </span>
            </button>
            <button
              onClick={() => setShowEditModal(true)}
              className="p-3 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
            >
              <PencilIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="p-3 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/20 transition-all"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Scans</p>
                <p className="text-2xl font-bold text-white">
                  {project.total_scans}
                </p>
              </div>
              <ChartBarIcon className="h-8 w-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Vulnerabilities</p>
                <p className="text-2xl font-bold text-white">{totalVulns}</p>
              </div>
              <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Security Score</p>
                <p className="text-2xl font-bold text-white">
                  {Math.round(project.security_score || 0)}
                </p>
              </div>
              <ShieldCheckIcon className="h-8 w-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Last Scan</p>
                <p className="text-sm font-medium text-white">
                  {project.last_scan
                    ? utils.formatRelativeDate(project.last_scan)
                    : "Never"}
                </p>
              </div>
              <ClockIcon className="h-8 w-8 text-purple-400" />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl mb-6">
          <div className="flex border-b border-gray-700/50">
            {[
              {
                key: "overview",
                label: "Overview",
                icon: InformationCircleIcon,
              },
              { key: "scans", label: "Scan History", icon: ChartBarIcon },
              { key: "settings", label: "Settings", icon: CogIcon },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center space-x-2 px-6 py-4 text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? "text-blue-400 border-b-2 border-blue-400"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          <div className="p-6">
            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* Project Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-6">
                    <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Project Information
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Status</span>
                          <span
                            className={`px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(
                              project.status
                            )}`}
                          >
                            {project.status}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Priority</span>
                          <span
                            className={`px-3 py-1 rounded-lg text-sm font-medium ${getPriorityColor(
                              project.priority
                            )}`}
                          >
                            {project.priority}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Category</span>
                          <span className="text-white">{project.category}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Created</span>
                          <span className="text-white">
                            {new Date(project.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Repository
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-start space-x-3">
                          <GlobeAltIcon className="h-5 w-5 text-gray-400 mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <p className="text-gray-400 text-sm">
                              Repository URL
                            </p>
                            <a
                              href={project.repository_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 transition-colors break-all"
                            >
                              {project.repository_url}
                            </a>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Branch</span>
                          <span className="text-white font-mono">
                            {project.repository.branch || "main"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Vulnerability Breakdown
                      </h3>
                      <div className="space-y-4">
                        {[
                          {
                            severity: "critical",
                            count: project.vulnerability_count.critical,
                            color: "text-red-400",
                          },
                          {
                            severity: "high",
                            count: project.vulnerability_count.high,
                            color: "text-orange-400",
                          },
                          {
                            severity: "medium",
                            count: project.vulnerability_count.medium,
                            color: "text-yellow-400",
                          },
                          {
                            severity: "low",
                            count: project.vulnerability_count.low,
                            color: "text-blue-400",
                          },
                        ].map(({ severity, count, color }) => (
                          <div
                            key={severity}
                            className="flex items-center justify-between"
                          >
                            <div className="flex items-center space-x-2">
                              <div
                                className={`w-3 h-3 rounded-full ${color.replace(
                                  "text-",
                                  "bg-"
                                )}`}
                              ></div>
                              <span className="text-gray-400 capitalize">
                                {severity}
                              </span>
                            </div>
                            <span className={`font-medium ${color}`}>
                              {count}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        Enabled Scanners
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {project.scan_config.enabled_scanners.map((scanner) => (
                          <span
                            key={scanner}
                            className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm font-medium"
                          >
                            {scanner.toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>

                    {project.tags && project.tags.length > 0 && (
                      <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold text-white mb-4">
                          Tags
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {project.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-lg text-sm"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "scans" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">
                    Scan History
                  </h3>
                  <button
                    onClick={handleStartScan}
                    disabled={startScanMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all"
                  >
                    {startScanMutation.isPending ? "Starting..." : "New Scan"}
                  </button>
                </div>

                {scanHistoryLoading ? (
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50 animate-pulse"
                      >
                        <div className="h-4 bg-gray-700 rounded w-1/4 mb-2"></div>
                        <div className="h-3 bg-gray-700 rounded w-1/2"></div>
                      </div>
                    ))}
                  </div>
                ) : scanHistory?.reports?.length > 0 ? (
                  <div className="space-y-4">
                    {scanHistory.reports.map((scan) => (
                      <div
                        key={scan.id}
                        className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50 hover:border-gray-600/50 transition-all"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h4 className="text-white font-medium">
                                Scan #{scan.id.slice(-8)}
                              </h4>
                              <span
                                className={`px-2 py-1 rounded text-xs ${
                                  scan.status === "completed"
                                    ? "bg-green-500/20 text-green-400"
                                    : scan.status === "running"
                                    ? "bg-blue-500/20 text-blue-400"
                                    : "bg-red-500/20 text-red-400"
                                }`}
                              >
                                {scan.status}
                              </span>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-gray-400">
                              <span>
                                {utils.formatRelativeDate(scan.created_at)}
                              </span>
                              <span>Branch: {scan.branch || "main"}</span>
                              {scan.duration_seconds && (
                                <span>
                                  Duration:{" "}
                                  {utils.formatDuration(scan.duration_seconds)}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            {scan.status === "completed" && (
                              <Link
                                to={`/report/${scan.id}`}
                                className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-all flex items-center space-x-2"
                              >
                                <EyeIcon className="h-4 w-4" />
                                <span>View Report</span>
                              </Link>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16">
                    <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">
                      No Scans Yet
                    </h3>
                    <p className="text-gray-400 mb-6">
                      Start your first security scan to see results here.
                    </p>
                    <button
                      onClick={handleStartScan}
                      disabled={startScanMutation.isPending}
                      className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all"
                    >
                      Start First Scan
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === "settings" && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-white">
                  Project Settings
                </h3>
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                  <div className="flex items-start space-x-3">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5" />
                    <div>
                      <p className="text-yellow-400 font-medium">
                        Settings Configuration
                      </p>
                      <p className="text-yellow-300 text-sm mt-1">
                        Project settings will be available in a future update.
                        Currently, you can edit basic project information using
                        the edit button above.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setShowDeleteModal(false)}
            />
            <div className="flex min-h-full items-center justify-center p-4">
              <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl p-6 w-full max-w-md">
                <div className="text-center">
                  <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Delete Project
                  </h3>
                  <p className="text-gray-400 mb-6">
                    Are you sure you want to delete "{project.name}"? This
                    action cannot be undone and will remove all associated scan
                    data.
                  </p>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setShowDeleteModal(false)}
                      className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDeleteProject}
                      disabled={deleteProjectMutation.isPending}
                      className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-all"
                    >
                      {deleteProjectMutation.isPending
                        ? "Deleting..."
                        : "Delete"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectDetails;
