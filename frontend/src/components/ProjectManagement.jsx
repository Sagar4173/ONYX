/**
 * Project Management Components for SecureDevOps Platform
 * Handles project creation, editing, and management
 */
import React, { useState, useEffect } from "react";
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  UserPlusIcon,
  UsersIcon,
  ChartBarIcon,
  CalendarIcon,
  TagIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import {
  ChartBarIcon as ChartBarSolid,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/solid";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuth } from "./auth";
import { projectsAPI } from "../services/api";
import { useNavigate } from "react-router-dom";

// Project Card Component
const ProjectCard = ({ project, onEdit, onDelete, onView }) => {
  const [showActions, setShowActions] = useState(false);

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "critical":
        return "from-red-500 to-red-600";
      case "high":
        return "from-orange-500 to-orange-600";
      case "medium":
        return "from-yellow-500 to-yellow-600";
      case "low":
        return "from-green-500 to-green-600";
      default:
        return "from-gray-500 to-gray-600";
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

  const getCategoryIcon = (category) => {
    switch (category) {
      case "web_application":
        return "🌐";
      case "mobile_application":
        return "📱";
      case "api_service":
        return "🔌";
      case "infrastructure":
        return "🏗️";
      case "microservice":
        return "⚡";
      case "library":
        return "📚";
      default:
        return "📦";
    }
  };

  const totalVulns =
    project.vulnerability_count.critical +
    project.vulnerability_count.high +
    project.vulnerability_count.medium +
    project.vulnerability_count.low;

  return (
    <div className="relative group">
      <div className="absolute inset-0 bg-gradient-to-r from-gray-800/30 to-gray-700/30 rounded-2xl blur-xl group-hover:blur-2xl group-hover:scale-105 transition-all duration-300" />

      <div className="relative bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-gray-600/50 transition-all duration-300">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">{getCategoryIcon(project.category)}</div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-blue-400 transition-colors">
                {project.name}
              </h3>
              <div className="flex items-center space-x-2">
                <span
                  className={`px-2 py-1 rounded-lg text-xs font-medium ${getStatusColor(
                    project.status
                  )}`}
                >
                  {project.status}
                </span>
                <div
                  className={`px-2 py-1 rounded-lg bg-gradient-to-r ${getPriorityColor(
                    project.priority
                  )} text-white text-xs font-medium`}
                >
                  {project.priority}
                </div>
              </div>
            </div>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all"
            >
              <EllipsisVerticalIcon className="h-5 w-5" />
            </button>

            {showActions && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-gray-800/95 backdrop-blur-xl rounded-xl border border-gray-700/50 shadow-xl z-10">
                <button
                  onClick={() => {
                    onView(project);
                    setShowActions(false);
                  }}
                  className="w-full px-4 py-3 text-left text-gray-300 hover:text-white hover:bg-gray-700/50 transition-all flex items-center space-x-2"
                >
                  <ChartBarIcon className="h-4 w-4" />
                  <span>View Details</span>
                </button>
                <button
                  onClick={() => {
                    onEdit(project);
                    setShowActions(false);
                  }}
                  className="w-full px-4 py-3 text-left text-gray-300 hover:text-white hover:bg-gray-700/50 transition-all flex items-center space-x-2"
                >
                  <PencilIcon className="h-4 w-4" />
                  <span>Edit Project</span>
                </button>
                <button
                  onClick={() => {
                    onDelete(project);
                    setShowActions(false);
                  }}
                  className="w-full px-4 py-3 text-left text-red-400 hover:text-red-300 hover:bg-red-500/20 transition-all flex items-center space-x-2"
                >
                  <TrashIcon className="h-4 w-4" />
                  <span>Delete Project</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        {project.description && (
          <p className="text-gray-400 text-sm mb-4 line-clamp-2">
            {project.description}
          </p>
        )}

        {/* Repository */}
        <div className="flex items-center space-x-2 mb-4">
          <GlobeAltIcon className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-400 truncate">
            {project.repository_url
              .replace("https://", "")
              .replace("http://", "")}
          </span>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-lg font-bold text-white">
              {project.total_scans}
            </div>
            <div className="text-xs text-gray-400">Scans</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-white">{totalVulns}</div>
            <div className="text-xs text-gray-400">Issues</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-white">
              {Math.round(project.security_score || 0)}
            </div>
            <div className="text-xs text-gray-400">Score</div>
          </div>
        </div>

        {/* Vulnerability Breakdown */}
        {totalVulns > 0 && (
          <div className="flex items-center justify-between text-xs mb-4">
            <div className="flex items-center space-x-1 text-red-400">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span>{project.vulnerability_count.critical}</span>
            </div>
            <div className="flex items-center space-x-1 text-orange-400">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              <span>{project.vulnerability_count.high}</span>
            </div>
            <div className="flex items-center space-x-1 text-yellow-400">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span>{project.vulnerability_count.medium}</span>
            </div>
            <div className="flex items-center space-x-1 text-blue-400">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>{project.vulnerability_count.low}</span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-700/50">
          <span>
            {project.last_scan
              ? `Last scan: ${new Date(project.last_scan).toLocaleDateString()}`
              : "No scans yet"}
          </span>
          <span>{new Date(project.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
};

// Create Project Modal
const CreateProjectModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "other",
    priority: "medium",
    repository: {
      url: "",
      branch: "main",
      access_token: "",
      scan_paths: ["/"],
      exclude_paths: [],
    },
    scan_config: {
      enabled_scanners: ["sast", "secrets"],
      auto_scan_on_push: false,
      scan_timeout_minutes: 60,
      fail_on_critical: false,
    },
    tags: [],
  });

  const [tagInput, setTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: templates } = useQuery({
    queryKey: ["projectTemplates"],
    queryFn: projectsAPI.getTemplateCategories,
  });

  const createMutation = useMutation({
    mutationFn: projectsAPI.createProject,
    onSuccess: (data) => {
      toast.success("Project created successfully!");
      onSuccess(data);
      onClose();
      setFormData({
        name: "",
        description: "",
        category: "other",
        priority: "medium",
        repository: {
          url: "",
          branch: "main",
          access_token: "",
          scan_paths: ["/"],
          exclude_paths: [],
        },
        scan_config: {
          enabled_scanners: ["sast", "secrets"],
          auto_scan_on_push: false,
          scan_timeout_minutes: 60,
          fail_on_critical: false,
        },
        tags: [],
      });
    },
    onError: (error) => {
      toast.error(error.message || "Failed to create project");
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.repository.url.trim()) {
      toast.error("Please fill in required fields");
      return;
    }

    setIsSubmitting(true);
    try {
      await createMutation.mutateAsync(formData);
    } finally {
      setIsSubmitting(false);
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()],
      }));
      setTagInput("");
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const toggleScanner = (scanner) => {
    setFormData((prev) => ({
      ...prev,
      scan_config: {
        ...prev.scan_config,
        enabled_scanners: prev.scan_config.enabled_scanners.includes(scanner)
          ? prev.scan_config.enabled_scanners.filter((s) => s !== scanner)
          : [...prev.scan_config.enabled_scanners, scanner],
      },
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl" />

            <div className="relative p-8">
              {/* Header */}
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-3">
                  <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600">
                    <PlusIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">
                      Create New Project
                    </h2>
                    <p className="text-gray-400">
                      Set up a new security scanning project
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-8">
                {/* Basic Information */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">
                    Basic Information
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Project Name *
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            name: e.target.value,
                          }))
                        }
                        placeholder="My Awesome Project"
                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Category
                      </label>
                      <select
                        value={formData.category}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            category: e.target.value,
                          }))
                        }
                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                      >
                        {templates?.categories.map((category) => (
                          <option key={category.value} value={category.value}>
                            {category.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          description: e.target.value,
                        }))
                      }
                      placeholder="Describe your project..."
                      rows={3}
                      className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Priority
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          priority: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                    >
                      {templates?.priorities.map((priority) => (
                        <option key={priority.value} value={priority.value}>
                          {priority.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Repository Configuration */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">
                    Repository Configuration
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Repository URL *
                      </label>
                      <input
                        type="url"
                        value={formData.repository.url}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            repository: {
                              ...prev.repository,
                              url: e.target.value,
                            },
                          }))
                        }
                        placeholder="https://github.com/user/repo"
                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Default Branch
                      </label>
                      <input
                        type="text"
                        value={formData.repository.branch}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            repository: {
                              ...prev.repository,
                              branch: e.target.value,
                            },
                          }))
                        }
                        placeholder="main"
                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Access Token (for private repositories)
                    </label>
                    <input
                      type="password"
                      value={formData.repository.access_token}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          repository: {
                            ...prev.repository,
                            access_token: e.target.value,
                          },
                        }))
                      }
                      placeholder="ghp_xxxxxxxxxxxx"
                      className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                    />
                  </div>
                </div>

                {/* Security Scanners */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">
                    Security Scanners
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {templates?.scan_types.map((scanner) => (
                      <button
                        key={scanner.value}
                        type="button"
                        onClick={() => toggleScanner(scanner.value)}
                        className={`p-4 rounded-xl border-2 transition-all text-left ${
                          formData.scan_config.enabled_scanners.includes(
                            scanner.value
                          )
                            ? "border-blue-500/70 bg-blue-500/20"
                            : "border-gray-700/50 bg-gray-800/30 hover:border-gray-600/50"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-white">
                            {scanner.label}
                          </span>
                          {formData.scan_config.enabled_scanners.includes(
                            scanner.value
                          ) && (
                            <CheckCircleIcon className="h-5 w-5 text-blue-400" />
                          )}
                        </div>
                        <p className="text-sm text-gray-400">
                          {scanner.description}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tags */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">Tags</h3>

                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) =>
                        e.key === "Enter" && (e.preventDefault(), addTag())
                      }
                      placeholder="Add tags..."
                      className="flex-1 px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all"
                    >
                      Add
                    </button>
                  </div>

                  {formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-lg text-sm flex items-center space-x-2"
                        >
                          <span>{tag}</span>
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="text-gray-400 hover:text-white"
                          >
                            <XMarkIcon className="h-4 w-4" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Submit */}
                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-700/50">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-6 py-3 text-gray-300 hover:text-white transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || createMutation.isPending}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition-all"
                  >
                    {isSubmitting || createMutation.isPending
                      ? "Creating..."
                      : "Create Project"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Project Management Component
export const ProjectManagement = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    status: "",
    category: "",
    priority: "",
  });
  const [showFilters, setShowFilters] = useState(false);

  const queryClient = useQueryClient();
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: projectsData, isLoading } = useQuery({
    queryKey: ["projects", filters],
    queryFn: () => projectsAPI.getProjects(filters),
  });

  const { data: analytics } = useQuery({
    queryKey: ["projectAnalytics"],
    queryFn: projectsAPI.getAnalyticsOverview,
  });

  const handleProjectCreated = () => {
    queryClient.invalidateQueries(["projects"]);
    queryClient.invalidateQueries(["projectAnalytics"]);
  };

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: (projectId) => projectsAPI.deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted successfully!");
      setDeletingProject(null);
      queryClient.invalidateQueries(["projects"]);
      queryClient.invalidateQueries(["projectAnalytics"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete project");
    },
  });

  // Update project mutation
  const updateProjectMutation = useMutation({
    mutationFn: ({ projectId, projectData }) =>
      projectsAPI.updateProject(projectId, projectData),
    onSuccess: () => {
      toast.success("Project updated successfully!");
      setEditingProject(null);
      queryClient.invalidateQueries(["projects"]);
      queryClient.invalidateQueries(["projectAnalytics"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update project");
    },
  });

  const confirmDeleteProject = () => {
    if (deletingProject) {
      deleteProjectMutation.mutate(deletingProject.id);
    }
  };

  const [editingProject, setEditingProject] = useState(null);
  const [deletingProject, setDeletingProject] = useState(null);

  const handleEditProject = (project) => {
    setEditingProject(project);
  };

  const handleDeleteProject = (project) => {
    setDeletingProject(project);
  };

  const handleViewProject = (project) => {
    // Navigate to project details page
    navigate(`/project/${project.id}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-8">
        <div className="flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading projects...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Project Management
          </h1>
          <p className="text-gray-400">
            Manage your security scanning projects and team collaboration
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>New Project</span>
        </button>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500">
                <UsersIcon className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">
                {analytics.total_projects}
              </span>
            </div>
            <h3 className="text-gray-400 font-medium">Total Projects</h3>
          </div>

          <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500">
                <CheckCircleIcon className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">
                {analytics.active_projects}
              </span>
            </div>
            <h3 className="text-gray-400 font-medium">Active Projects</h3>
          </div>

          <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500">
                <ChartBarSolid className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">
                {analytics.total_scans}
              </span>
            </div>
            <h3 className="text-gray-400 font-medium">Total Scans</h3>
          </div>

          <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-r from-orange-500 to-red-500">
                <ExclamationTriangleIcon className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">
                {analytics.total_vulnerabilities}
              </span>
            </div>
            <h3 className="text-gray-400 font-medium">Total Issues</h3>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Search & Filter</h3>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all"
          >
            <FunnelIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, search: e.target.value }))
              }
              placeholder="Search projects..."
              className="w-full pl-10 pr-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          {showFilters && (
            <>
              <select
                value={filters.status}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, status: e.target.value }))
                }
                className="px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="archived">Archived</option>
              </select>

              <select
                value={filters.category}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, category: e.target.value }))
                }
                className="px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              >
                <option value="">All Categories</option>
                <option value="web_application">Web Application</option>
                <option value="mobile_application">Mobile Application</option>
                <option value="api_service">API Service</option>
                <option value="infrastructure">Infrastructure</option>
                <option value="microservice">Microservice</option>
                <option value="library">Library</option>
                <option value="other">Other</option>
              </select>

              <select
                value={filters.priority}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, priority: e.target.value }))
                }
                className="px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              >
                <option value="">All Priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </>
          )}
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projectsData?.projects?.map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onEdit={handleEditProject}
            onDelete={handleDeleteProject}
            onView={handleViewProject}
          />
        ))}
      </div>

      {/* Empty State */}
      {projectsData?.projects?.length === 0 && (
        <div className="text-center py-16">
          <div className="p-4 rounded-2xl bg-gray-800/50 inline-block mb-4">
            <UsersIcon className="h-12 w-12 text-gray-400" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">
            No Projects Found
          </h3>
          <p className="text-gray-400 mb-6">
            {filters.search ||
            filters.status ||
            filters.category ||
            filters.priority
              ? "No projects match your current filters"
              : "Get started by creating your first project"}
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
          >
            Create First Project
          </button>
        </div>
      )}

      {/* Pagination */}
      {projectsData?.pagination?.has_more && (
        <div className="flex justify-center mt-8">
          <button className="px-6 py-3 bg-gray-800/50 text-white rounded-xl hover:bg-gray-700/50 transition-all">
            Load More Projects
          </button>
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleProjectCreated}
      />

      {/* Edit Project Modal */}
      {editingProject && (
        <EditProjectModal
          project={editingProject}
          isOpen={!!editingProject}
          onClose={() => setEditingProject(null)}
          onSuccess={() => {
            setEditingProject(null);
            queryClient.invalidateQueries(["projects"]);
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deletingProject && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setDeletingProject(null)}
          />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl p-6 w-full max-w-md">
              <div className="text-center">
                <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">
                  Delete Project
                </h3>
                <p className="text-gray-400 mb-6">
                  Are you sure you want to delete "{deletingProject.name}"? This
                  action cannot be undone and will remove all associated scan
                  data.
                </p>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setDeletingProject(null)}
                    className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmDeleteProject}
                    disabled={deleteProjectMutation.isPending}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-all"
                  >
                    {deleteProjectMutation.isPending ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Edit Project Modal
const EditProjectModal = ({ project, isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: project?.name || "",
    description: project?.description || "",
    category: project?.category || "other",
    priority: project?.priority || "medium",
    repository: {
      url: project?.repository_url || "",
      branch: project?.repository?.branch || "main",
      access_token: project?.repository?.access_token || "",
      scan_paths: project?.repository?.scan_paths || ["/"],
      exclude_paths: project?.repository?.exclude_paths || [],
    },
    scan_config: {
      enabled_scanners: project?.scan_config?.enabled_scanners || [
        "sast",
        "secrets",
      ],
      auto_scan_on_push: project?.scan_config?.auto_scan_on_push || false,
      scan_timeout_minutes: project?.scan_config?.scan_timeout_minutes || 60,
      fail_on_critical: project?.scan_config?.fail_on_critical || false,
    },
    tags: project?.tags || [],
  });

  const [tagInput, setTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: templates } = useQuery({
    queryKey: ["projectTemplates"],
    queryFn: projectsAPI.getTemplateCategories,
  });

  const updateMutation = useMutation({
    mutationFn: (data) => projectsAPI.updateProject(project.id, data),
    onSuccess: (data) => {
      toast.success("Project updated successfully!");
      onSuccess(data);
      onClose();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update project");
    },
  });

  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name || "",
        description: project.description || "",
        category: project.category || "other",
        priority: project.priority || "medium",
        repository: {
          url: project.repository_url || "",
          branch: project.repository?.branch || "main",
          access_token: project.repository?.access_token || "",
          scan_paths: project.repository?.scan_paths || ["/"],
          exclude_paths: project.repository?.exclude_paths || [],
        },
        scan_config: {
          enabled_scanners: project.scan_config?.enabled_scanners || [
            "sast",
            "secrets",
          ],
          auto_scan_on_push: project.scan_config?.auto_scan_on_push || false,
          scan_timeout_minutes: project.scan_config?.scan_timeout_minutes || 60,
          fail_on_critical: project.scan_config?.fail_on_critical || false,
        },
        tags: project.tags || [],
      });
    }
  }, [project]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.repository.url.trim()) {
      toast.error("Please fill in required fields");
      return;
    }

    setIsSubmitting(true);
    try {
      await updateMutation.mutateAsync(formData);
    } finally {
      setIsSubmitting(false);
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()],
      }));
      setTagInput("");
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const toggleScanner = (scanner) => {
    setFormData((prev) => ({
      ...prev,
      scan_config: {
        ...prev.scan_config,
        enabled_scanners: prev.scan_config.enabled_scanners.includes(scanner)
          ? prev.scan_config.enabled_scanners.filter((s) => s !== scanner)
          : [...prev.scan_config.enabled_scanners, scanner],
      },
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl" />

            <div className="relative p-8">
              {/* Header */}
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-3">
                  <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600">
                    <PencilIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">
                      Edit Project
                    </h2>
                    <p className="text-gray-400">
                      Update your project configuration
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-8">
                {/* Basic Information */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">
                    Basic Information
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Project Name *
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            name: e.target.value,
                          }))
                        }
                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Category
                      </label>
                      <select
                        value={formData.category}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            category: e.target.value,
                          }))
                        }
                        className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                      >
                        {templates?.categories?.map((category) => (
                          <option key={category.value} value={category.value}>
                            {category.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          description: e.target.value,
                        }))
                      }
                      placeholder="Describe your project..."
                      rows={3}
                      className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Priority
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          priority: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                    >
                      {templates?.priorities?.map((priority) => (
                        <option key={priority.value} value={priority.value}>
                          {priority.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Security Scanners */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">
                    Security Scanners
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {templates?.scan_types?.map((scanner) => (
                      <button
                        key={scanner.value}
                        type="button"
                        onClick={() => toggleScanner(scanner.value)}
                        className={`p-4 rounded-xl border-2 transition-all text-left ${
                          formData.scan_config.enabled_scanners.includes(
                            scanner.value
                          )
                            ? "border-blue-500/70 bg-blue-500/20"
                            : "border-gray-700/50 bg-gray-800/30 hover:border-gray-600/50"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-white">
                            {scanner.label}
                          </span>
                          {formData.scan_config.enabled_scanners.includes(
                            scanner.value
                          ) && (
                            <CheckCircleIcon className="h-5 w-5 text-blue-400" />
                          )}
                        </div>
                        <p className="text-sm text-gray-400">
                          {scanner.description}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tags */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white">Tags</h3>

                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) =>
                        e.key === "Enter" && (e.preventDefault(), addTag())
                      }
                      placeholder="Add tags..."
                      className="flex-1 px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all"
                    >
                      Add
                    </button>
                  </div>

                  {formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-lg text-sm flex items-center space-x-2"
                        >
                          <span>{tag}</span>
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="text-gray-400 hover:text-white"
                          >
                            <XMarkIcon className="h-4 w-4" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Submit */}
                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-700/50">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-6 py-3 text-gray-300 hover:text-white transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || updateMutation.isPending}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition-all"
                  >
                    {isSubmitting || updateMutation.isPending
                      ? "Updating..."
                      : "Update Project"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectManagement;
