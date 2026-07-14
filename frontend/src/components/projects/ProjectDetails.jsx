/**
 * Project Details Component for ONYX Platform
 * Comprehensive project overview with security metrics and scan history
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeftIcon,
  ArrowPathIcon,
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
  StopIcon,
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
import { projectsAPI, reportsAPI, utils } from "../../services/api";
import { PageContainer, PageHeader } from "../../layouts";

const ProjectDetails = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    priority: "medium",
    status: "active",
    category: "other",
    repository: {
      url: "",
      branch: "main",
      access_token: "",
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
  const [deleteConfirmText, setDeleteConfirmText] = useState("");

  // Scan tracking state
  const [activeScan, setActiveScan] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  const [scanCompleted, setScanCompleted] = useState(false); // Track if scan just completed

  // Fetch project details
  const {
    data: project,
    isLoading: projectLoading,
    error: projectError,
    refetch: refetchProject,
  } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsAPI.getProject(projectId),
    enabled: !!projectId,
  });

  // Fetch project scan history
  const {
    data: scanHistory,
    isLoading: scanHistoryLoading,
    refetch: refetchScanHistory,
  } = useQuery({
    queryKey: ["projectScans", projectId],
    queryFn: () => reportsAPI.getReports({ project_id: projectId, limit: 20 }),
    enabled: !!projectId,
    refetchInterval: isPolling ? 3000 : false, // Auto-refetch when scan is running
  });

  // Fetch project analytics
  const { data: projectAnalytics, refetch: refetchAnalytics } = useQuery({
    queryKey: ["projectAnalytics", projectId],
    queryFn: () => projectsAPI.getProjectAnalytics(projectId),
    enabled: !!projectId,
  });

  // Track if we've already shown completion toast to prevent duplicates
  const hasShownCompletionToast = useRef(false);

  // Poll for scan status when active scan exists
  const pollScanStatus = useCallback(async () => {
    if (!activeScan?.scan_id || !isPolling) return;

    try {
      const status = await reportsAPI.getScanStatus(activeScan.scan_id);

      if (status) {
        // Update progress immediately
        setScanProgress(status.progress || 0);
        setActiveScan((prev) => ({
          ...prev,
          // Only update specific fields, preserve started_at from when scan was initiated
          status: status.status || prev?.status,
          progress: status.progress || prev?.progress,
          current_scanner: status.current_scanner || prev?.current_scanner,
          total_findings: status.total_findings,
          findings_by_severity: status.findings_by_severity,
          // Keep original started_at from frontend
        }));

        // Check if scan completed
        if (
          status.status === "completed" ||
          status.status === "failed" ||
          status.status === "cancelled"
        ) {
          // Stop polling immediately
          setIsPolling(false);

          // Show toast only once
          if (!hasShownCompletionToast.current) {
            hasShownCompletionToast.current = true;

            if (status.status === "completed") {
              const findings = status.findings_by_severity || {};
              const criticalHigh =
                (findings.critical || 0) + (findings.high || 0);

              if (criticalHigh > 0) {
                toast.error(
                  `🚨 Scan completed with ${criticalHigh} critical/high severity issues! Total: ${
                    status.total_findings || 0
                  } findings.`,
                  { duration: 5000 }
                );
              } else if (status.total_findings > 0) {
                toast.success(
                  `✅ Scan completed! Found ${status.total_findings} findings (no critical/high issues).`,
                  { duration: 4000 }
                );
              } else {
                toast.success(`🎉 Scan completed! No security issues found.`, {
                  duration: 4000,
                });
              }
            } else if (status.status === "cancelled") {
              toast("Scan was cancelled.", { icon: "ℹ️" });
            } else {
              toast.error(status.error_message || "Scan failed.");
            }
          }

          // Update activeScan with final status (keep the card visible)
          // Use current local time for completed_at to ensure consistent duration calculation
          const completedTime = new Date().toISOString();
          const finalProgress =
            status.status === "completed" ? 100 : status.progress || 0;
          setActiveScan((prev) => ({
            ...prev,
            ...status,
            // Preserve frontend started_at for accurate duration calculation
            started_at: prev?.started_at,
            report_id: status.id || prev?.scan_id, // MongoDB ObjectId for report link
            status: status.status,
            progress: finalProgress,
            total_findings: status.total_findings || 0,
            findings_by_severity: status.findings_by_severity || {},
            error_message: status.error_message || null,
            // Always use frontend local time for completion to match started_at
            completed_at: completedTime,
          }));
          setScanProgress(finalProgress);
          setScanCompleted(true);

          // Refresh all data after scan completes
          setTimeout(() => {
            queryClient.invalidateQueries(["projectScans", projectId]);
            queryClient.invalidateQueries(["project", projectId]);
            queryClient.invalidateQueries(["projectAnalytics", projectId]);
            refetchProject();
            refetchScanHistory();
            refetchAnalytics();
          }, 1000);
        }
      }
    } catch (error) {
      console.error("Error polling scan status:", error);
      // Don't stop polling on transient errors, just log them
    }
  }, [activeScan?.scan_id, isPolling, projectId, queryClient]);

  // Set up polling interval
  useEffect(() => {
    let interval;
    if (isPolling && activeScan?.scan_id) {
      // Poll immediately on start
      pollScanStatus();
      interval = setInterval(pollScanStatus, 2000); // Poll every 2 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPolling, activeScan?.scan_id, pollScanStatus]);

  // Start new scan mutation
  const startScanMutation = useMutation({
    mutationFn: (scanData) => reportsAPI.startScan(scanData),
    onSuccess: (data) => {
      toast.success("Security scan started! Monitoring progress...");
      hasShownCompletionToast.current = false; // Reset for new scan
      setScanCompleted(false); // Reset completion state
      setActiveScan({
        scan_id: data.scan_id,
        status: data.status || "pending",
        project_name: data.project_name,
        started_at: new Date().toISOString(),
        current_scanner: "Initializing...",
        progress: 0,
      });
      setScanProgress(0);
      setIsPolling(true);
      queryClient.invalidateQueries(["projectScans", projectId]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to start scan");
    },
  });

  // Stop scan mutation
  const stopScanMutation = useMutation({
    mutationFn: (scanId) => reportsAPI.stopScan(scanId),
    onSuccess: () => {
      toast("Scan stopped.", { icon: "ℹ️" });
      setActiveScan(null);
      setScanProgress(0);
      setIsPolling(false);
      hasShownCompletionToast.current = false;
      queryClient.invalidateQueries(["projectScans", projectId]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to stop scan");
    },
  });

  // Update project mutation
  const updateProjectMutation = useMutation({
    mutationFn: (updateData) =>
      projectsAPI.updateProject(projectId, updateData),
    onSuccess: () => {
      toast.success("Project updated successfully!");
      queryClient.invalidateQueries(["project", projectId]);
      setShowEditModal(false);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update project");
    },
  });

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: () => projectsAPI.deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted successfully!");
      // Invalidate projects list cache so the list updates
      queryClient.invalidateQueries(["projects"]);
      queryClient.invalidateQueries(["userProjects"]);
      navigate("/projects");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete project");
    },
  });

  const handleStartScan = () => {
    if (!project || activeScan) return;

    startScanMutation.mutate({
      repository_url: project.repository?.url,
      branch: project.repository?.branch || "main",
      scan_types: project.scan_config?.enabled_scanners || [
        "sast",
        "secrets",
        "container",
      ],
      project_id: projectId,
    });
  };

  const handleStopScan = () => {
    if (activeScan?.scan_id) {
      stopScanMutation.mutate(activeScan.scan_id);
    }
  };

  const handleDeleteProject = () => {
    if (deleteConfirmText !== "DELETE") return;
    deleteProjectMutation.mutate();
    setShowDeleteModal(false);
    setDeleteConfirmText("");
  };

  const openEditModal = () => {
    if (project) {
      setEditForm({
        name: project.name || "",
        description: project.description || "",
        priority: project.priority || "medium",
        status: project.status || "active",
        category: project.category || "other",
        repository: {
          url: project.repository?.url || "",
          branch: project.repository?.branch || "main",
          access_token: project.repository?.access_token || "",
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
      setTagInput("");
      setShowEditModal(true);
    }
  };

  const handleUpdateProject = (e) => {
    e.preventDefault();
    // Transform form data to match API expectations
    const updateData = {
      name: editForm.name,
      description: editForm.description,
      priority: editForm.priority,
      status: editForm.status,
      category: editForm.category,
      repository: editForm.repository,
      scan_config: editForm.scan_config,
      tags: editForm.tags,
    };
    updateProjectMutation.mutate(updateData);
  };

  const addTag = () => {
    if (tagInput.trim() && !editForm.tags.includes(tagInput.trim())) {
      setEditForm((prev) => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()],
      }));
      setTagInput("");
    }
  };

  const removeTag = (tagToRemove) => {
    setEditForm((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const toggleScanner = (scanner) => {
    setEditForm((prev) => ({
      ...prev,
      scan_config: {
        ...prev.scan_config,
        enabled_scanners: prev.scan_config.enabled_scanners.includes(scanner)
          ? prev.scan_config.enabled_scanners.filter((s) => s !== scanner)
          : [...prev.scan_config.enabled_scanners, scanner],
      },
    }));
  };

  if (projectLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
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
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
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

  // Access vulnerability counts from stats (with safe fallbacks)
  // When scan just completed, prefer the live data from activeScan
  const stats = project.stats || {};
  const liveFindings =
    scanCompleted && activeScan?.findings_by_severity
      ? activeScan.findings_by_severity
      : null;

  const vulnCounts = {
    critical: liveFindings?.critical ?? stats.critical_vulnerabilities ?? 0,
    high: liveFindings?.high ?? stats.high_vulnerabilities ?? 0,
    medium: liveFindings?.medium ?? stats.medium_vulnerabilities ?? 0,
    low: liveFindings?.low ?? stats.low_vulnerabilities ?? 0,
  };
  const totalVulns =
    vulnCounts.critical + vulnCounts.high + vulnCounts.medium + vulnCounts.low;

  // Calculate live security score if scan just completed
  const liveSecurityScore = liveFindings
    ? Math.max(
        0,
        100 -
          (vulnCounts.critical * 25 +
            vulnCounts.high * 15 +
            vulnCounts.medium * 5 +
            vulnCounts.low * 1)
      )
    : null;

  // Check if there's an active scan from scan history
  const runningScans =
    scanHistory?.reports?.filter(
      (r) => r.status === "running" || r.status === "pending"
    ) || [];

  // Determine if scan is actively running (not completed/failed/cancelled)
  const isScanActive =
    (activeScan &&
      !scanCompleted &&
      activeScan.status !== "completed" &&
      activeScan.status !== "failed" &&
      activeScan.status !== "cancelled") ||
    runningScans.length > 0;

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title={project.name}
          description={project.description || "No description provided"}
          icon={ShieldCheckIcon}
          breadcrumb={["Projects", project.name]}
          actions={
            <div className="flex items-center space-x-3">
              {/* Scan Button - Dynamic based on scan state */}
              {isScanActive ? (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleStopScan}
                    disabled={stopScanMutation.isPending}
                    className="px-6 py-3 bg-gradient-to-r from-red-500 to-rose-600 text-white font-medium rounded-xl hover:from-red-600 hover:to-rose-700 disabled:opacity-50 transition-all flex items-center space-x-2 animate-pulse"
                  >
                    <StopIcon className="h-5 w-5" />
                    <span>
                      {stopScanMutation.isPending ? "Stopping..." : "Stop Scan"}
                    </span>
                  </button>
                  <div className="px-4 py-2 bg-blue-500/20 rounded-xl flex items-center space-x-2">
                    <ArrowPathIcon className="h-4 w-4 text-blue-400 animate-spin" />
                    <span className="text-blue-400 text-sm font-medium">
                      {activeScan?.status === "running"
                        ? "Scanning..."
                        : "Pending..."}
                    </span>
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleStartScan}
                  disabled={startScanMutation.isPending}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition-all flex items-center space-x-2 group"
                >
                  <PlayIcon className="h-5 w-5 group-hover:scale-110 transition-transform" />
                  <span>
                    {startScanMutation.isPending ? "Starting..." : "Start Scan"}
                  </span>
                </button>
              )}
              <button
                onClick={openEditModal}
                className="p-3 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
                title="Edit Project"
              >
                <PencilIcon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setShowDeleteModal(true)}
                className="p-3 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/20 transition-all"
                title="Delete Project"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          }
        />

        {/* Enhanced Scan Progress/Completion Banner */}
        {activeScan && (
          <div
            className={`mb-6 rounded-2xl overflow-hidden shadow-xl transition-all duration-500 ${
              scanCompleted
                ? activeScan.status === "completed"
                  ? "bg-gradient-to-r from-gray-900 via-green-900/30 to-gray-900 border border-green-500/40 shadow-green-500/10"
                  : activeScan.status === "cancelled"
                  ? "bg-gradient-to-r from-gray-900 via-yellow-900/30 to-gray-900 border border-yellow-500/40 shadow-yellow-500/10"
                  : "bg-gradient-to-r from-gray-900 via-red-900/30 to-gray-900 border border-red-500/40 shadow-red-500/10"
                : "bg-gradient-to-r from-gray-900 via-blue-900/30 to-gray-900 border border-blue-500/40 shadow-blue-500/10"
            }`}
          >
            {/* Header */}
            <div
              className={`px-6 py-4 border-b ${
                scanCompleted
                  ? activeScan.status === "completed"
                    ? "bg-gradient-to-r from-green-600/20 to-emerald-600/20 border-green-500/30"
                    : activeScan.status === "cancelled"
                    ? "bg-gradient-to-r from-yellow-600/20 to-amber-600/20 border-yellow-500/30"
                    : "bg-gradient-to-r from-red-600/20 to-rose-600/20 border-red-500/30"
                  : "bg-gradient-to-r from-blue-600/20 to-indigo-600/20 border-blue-500/30"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <div
                      className={`p-3 rounded-xl ${
                        scanCompleted
                          ? activeScan.status === "completed"
                            ? "bg-green-500/30"
                            : activeScan.status === "cancelled"
                            ? "bg-yellow-500/30"
                            : "bg-red-500/30"
                          : "bg-blue-500/30"
                      }`}
                    >
                      {scanCompleted ? (
                        activeScan.status === "completed" ? (
                          <CheckCircleIcon className="h-7 w-7 text-green-400" />
                        ) : (
                          <ExclamationCircleIcon className="h-7 w-7 text-yellow-400" />
                        )
                      ) : (
                        <ShieldCheckIcon className="h-7 w-7 text-blue-400" />
                      )}
                    </div>
                    {!scanCompleted && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse border-2 border-gray-900" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                      {scanCompleted
                        ? activeScan.status === "completed"
                          ? "Scan Completed Successfully"
                          : activeScan.status === "cancelled"
                          ? "Scan Cancelled"
                          : "Scan Failed"
                        : "Security Scan in Progress"}
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
                          scanCompleted
                            ? activeScan.status === "completed"
                              ? "bg-green-500/20 text-green-400 border-green-500/30"
                              : activeScan.status === "cancelled"
                              ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                              : "bg-red-500/20 text-red-400 border-red-500/30"
                            : "bg-green-500/20 text-green-400 border-green-500/30"
                        }`}
                      >
                        {scanCompleted
                          ? activeScan.status?.toUpperCase()
                          : "LIVE"}
                      </span>
                    </h3>
                    <p
                      className={`text-sm mt-0.5 ${
                        scanCompleted ? "text-gray-300" : "text-blue-300"
                      }`}
                    >
                      {project?.name || "Repository"} •{" "}
                      {scanCompleted
                        ? `Completed at ${new Date(
                            activeScan.completed_at
                          ).toLocaleTimeString()}`
                        : activeScan?.project_name || "Scanning..."}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  {scanCompleted ? (
                    <>
                      {activeScan.status === "completed" &&
                        activeScan.report_id && (
                          <Link
                            to={`/report/${activeScan.report_id}`}
                            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all flex items-center space-x-2 shadow-lg shadow-blue-500/20"
                          >
                            <EyeIcon className="h-5 w-5" />
                            <span className="font-medium">View Report</span>
                          </Link>
                        )}
                      <button
                        onClick={() => {
                          setActiveScan(null);
                          setScanCompleted(false);
                          setScanProgress(0);
                        }}
                        className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
                        title="Dismiss"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={handleStopScan}
                      disabled={stopScanMutation.isPending}
                      className="px-4 py-2 bg-red-500/20 text-red-400 rounded-xl hover:bg-red-500/30 border border-red-500/30 transition-all flex items-center space-x-2 group"
                    >
                      <StopIcon className="h-5 w-5 group-hover:scale-110 transition-transform" />
                      <span className="font-medium">Stop Scan</span>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Progress Section */}
            <div className="px-6 py-5">
              {/* Current Stage / Completion Message */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {scanCompleted ? (
                    activeScan.status === "completed" ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-400" />
                    ) : (
                      <ExclamationCircleIcon className="h-5 w-5 text-yellow-400" />
                    )
                  ) : (
                    <ArrowPathIcon className="h-5 w-5 text-blue-400 animate-spin" />
                  )}
                  <span className="text-white font-medium">
                    {scanCompleted
                      ? activeScan.status === "completed"
                        ? `Found ${
                            activeScan.total_findings || 0
                          } security findings`
                        : activeScan.status === "cancelled"
                        ? "Scan was cancelled by user"
                        : activeScan.error_message ||
                          "Scan encountered an error"
                      : activeScan?.current_scanner || "Initializing scan..."}
                  </span>
                </div>
                <span
                  className={`text-2xl font-bold ${
                    scanCompleted
                      ? activeScan.status === "completed"
                        ? "text-green-400"
                        : "text-yellow-400"
                      : "text-blue-400"
                  }`}
                >
                  {scanProgress}%
                </span>
              </div>

              {/* Main Progress Bar */}
              <div className="relative w-full h-4 bg-gray-800/80 rounded-full overflow-hidden mb-4">
                <div
                  className={`absolute inset-0 h-full rounded-full transition-all duration-700 ease-out ${
                    scanCompleted
                      ? activeScan.status === "completed"
                        ? "bg-gradient-to-r from-green-600 via-emerald-500 to-green-400"
                        : "bg-gradient-to-r from-yellow-600 via-amber-500 to-yellow-400"
                      : "bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500"
                  }`}
                  style={{ width: `${Math.max(scanProgress, 2)}%` }}
                />
                {!scanCompleted && (
                  <div
                    className="absolute inset-0 h-full bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full animate-shimmer"
                    style={{ width: `${Math.max(scanProgress, 2)}%` }}
                  />
                )}
              </div>

              {/* Stage Indicators */}
              <div className="grid grid-cols-7 gap-2 mb-4">
                {[
                  { label: "Initialize", min: 0, max: 10 },
                  { label: "Clone", min: 10, max: 20 },
                  { label: "SAST", min: 20, max: 35 },
                  { label: "Secrets", min: 35, max: 50 },
                  { label: "Dependencies", min: 50, max: 70 },
                  { label: "Process", min: 70, max: 90 },
                  { label: "AI Analysis", min: 90, max: 100 },
                ].map((stage, idx) => {
                  const isActive =
                    scanProgress >= stage.min && scanProgress < stage.max;
                  const isComplete = scanProgress >= stage.max;
                  return (
                    <div key={idx} className="text-center">
                      <div
                        className={`h-1.5 rounded-full mb-2 transition-all duration-300 ${
                          isComplete
                            ? "bg-green-500"
                            : isActive && !scanCompleted
                            ? "bg-blue-500 animate-pulse"
                            : "bg-gray-700"
                        }`}
                      />
                      <span
                        className={`text-xs font-medium transition-colors ${
                          isComplete
                            ? "text-green-400"
                            : isActive && !scanCompleted
                            ? "text-blue-400"
                            : "text-gray-500"
                        }`}
                      >
                        {isComplete ? "✓ " : ""}
                        {stage.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Findings Summary (only show when completed) */}
              {scanCompleted && activeScan.status === "completed" && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4 pt-4 border-t border-gray-700/50">
                  <div className="bg-gray-800/50 rounded-xl p-3 text-center border border-gray-700/50">
                    <p className="text-2xl font-bold text-white mb-0.5">
                      {activeScan.total_findings || 0}
                    </p>
                    <p className="text-gray-400 text-xs">Total</p>
                  </div>
                  <div
                    className={`rounded-xl p-3 text-center border ${
                      (activeScan.findings_by_severity?.critical || 0) > 0
                        ? "bg-red-500/20 border-red-500/40"
                        : "bg-gray-800/50 border-gray-700/50"
                    }`}
                  >
                    <p
                      className={`text-2xl font-bold mb-0.5 ${
                        (activeScan.findings_by_severity?.critical || 0) > 0
                          ? "text-red-400"
                          : "text-gray-500"
                      }`}
                    >
                      {activeScan.findings_by_severity?.critical || 0}
                    </p>
                    <p className="text-gray-400 text-xs">Critical</p>
                  </div>
                  <div
                    className={`rounded-xl p-3 text-center border ${
                      (activeScan.findings_by_severity?.high || 0) > 0
                        ? "bg-orange-500/20 border-orange-500/40"
                        : "bg-gray-800/50 border-gray-700/50"
                    }`}
                  >
                    <p
                      className={`text-2xl font-bold mb-0.5 ${
                        (activeScan.findings_by_severity?.high || 0) > 0
                          ? "text-orange-400"
                          : "text-gray-500"
                      }`}
                    >
                      {activeScan.findings_by_severity?.high || 0}
                    </p>
                    <p className="text-gray-400 text-xs">High</p>
                  </div>
                  <div
                    className={`rounded-xl p-3 text-center border ${
                      (activeScan.findings_by_severity?.medium || 0) > 0
                        ? "bg-yellow-500/20 border-yellow-500/40"
                        : "bg-gray-800/50 border-gray-700/50"
                    }`}
                  >
                    <p
                      className={`text-2xl font-bold mb-0.5 ${
                        (activeScan.findings_by_severity?.medium || 0) > 0
                          ? "text-yellow-400"
                          : "text-gray-500"
                      }`}
                    >
                      {activeScan.findings_by_severity?.medium || 0}
                    </p>
                    <p className="text-gray-400 text-xs">Medium</p>
                  </div>
                  <div
                    className={`rounded-xl p-3 text-center border ${
                      (activeScan.findings_by_severity?.low || 0) > 0
                        ? "bg-blue-500/20 border-blue-500/40"
                        : "bg-gray-800/50 border-gray-700/50"
                    }`}
                  >
                    <p
                      className={`text-2xl font-bold mb-0.5 ${
                        (activeScan.findings_by_severity?.low || 0) > 0
                          ? "text-blue-400"
                          : "text-gray-500"
                      }`}
                    >
                      {activeScan.findings_by_severity?.low || 0}
                    </p>
                    <p className="text-gray-400 text-xs">Low</p>
                  </div>
                </div>
              )}

              {/* Scan Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-800/50">
                <div className="bg-gray-800/30 rounded-xl p-3">
                  <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">
                    Scan ID
                  </p>
                  <p className="text-gray-300 font-mono text-sm">
                    {activeScan?.scan_id?.slice(0, 12) || "..."}
                  </p>
                </div>
                <div className="bg-gray-800/30 rounded-xl p-3">
                  <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">
                    Started
                  </p>
                  <p className="text-gray-300 text-sm">
                    {activeScan?.started_at
                      ? new Date(activeScan.started_at).toLocaleTimeString()
                      : "Just now"}
                  </p>
                </div>
                <div className="bg-gray-800/30 rounded-xl p-3">
                  <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">
                    {scanCompleted ? "Completed" : "Status"}
                  </p>
                  <p
                    className={`text-sm font-medium capitalize ${
                      scanCompleted
                        ? activeScan.status === "completed"
                          ? "text-green-400"
                          : "text-yellow-400"
                        : "text-blue-400"
                    }`}
                  >
                    {scanCompleted && activeScan.completed_at
                      ? new Date(activeScan.completed_at).toLocaleTimeString()
                      : activeScan?.status || "pending"}
                  </p>
                </div>
                <div className="bg-gray-800/30 rounded-xl p-3">
                  <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">
                    {scanCompleted ? "Duration" : "Findings"}
                  </p>
                  <p className="text-gray-300 text-sm">
                    {scanCompleted
                      ? activeScan.started_at && activeScan.completed_at
                        ? (() => {
                            const duration = Math.round(
                              (new Date(activeScan.completed_at).getTime() -
                                new Date(activeScan.started_at).getTime()) /
                                1000
                            );
                            // Ensure positive duration
                            const absDuration = Math.abs(duration);
                            if (absDuration < 60) return `${absDuration}s`;
                            if (absDuration < 3600)
                              return `${Math.round(absDuration / 60)}m ${
                                absDuration % 60
                              }s`;
                            return `${Math.floor(
                              absDuration / 3600
                            )}h ${Math.round((absDuration % 3600) / 60)}m`;
                          })()
                        : "N/A"
                      : activeScan?.total_findings !== undefined
                      ? activeScan.total_findings
                      : "Scanning..."}
                  </p>
                </div>
              </div>

              {/* Quick Actions (only show when completed) */}
              {scanCompleted && (
                <div className="flex items-center justify-center space-x-4 mt-5 pt-4 border-t border-gray-700/50">
                  <button
                    onClick={() => {
                      setActiveScan(null);
                      setScanCompleted(false);
                      setScanProgress(0);
                      hasShownCompletionToast.current = false;
                      handleStartScan();
                    }}
                    disabled={startScanMutation.isPending}
                    className="px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center space-x-2"
                  >
                    <PlayIcon className="h-5 w-5" />
                    <span>Run New Scan</span>
                  </button>
                  {activeScan.status === "completed" &&
                    activeScan.report_id && (
                      <Link
                        to={`/report/${activeScan.report_id}`}
                        className="px-5 py-2.5 bg-gray-700 text-white rounded-xl hover:bg-gray-600 transition-all flex items-center space-x-2"
                      >
                        <EyeIcon className="h-5 w-5" />
                        <span>View Detailed Report</span>
                      </Link>
                    )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:border-blue-500/30 transition-all">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Scans</p>
                <p className="text-2xl font-bold text-white">
                  {(scanCompleted
                    ? (stats.total_scans || 0) + 1
                    : stats.total_scans) || (scanCompleted ? 1 : 0)}
                </p>
              </div>
              <ChartBarIcon className="h-8 w-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:border-red-500/30 transition-all group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Vulnerabilities</p>
                <p className="text-2xl font-bold text-white">{totalVulns}</p>
                {totalVulns > 0 && (
                  <div className="flex items-center space-x-2 mt-1">
                    {vulnCounts.critical > 0 && (
                      <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">
                        {vulnCounts.critical} critical
                      </span>
                    )}
                    {vulnCounts.high > 0 && (
                      <span className="text-xs px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded">
                        {vulnCounts.high} high
                      </span>
                    )}
                  </div>
                )}
              </div>
              <ExclamationTriangleIcon className="h-8 w-8 text-red-400 group-hover:scale-110 transition-transform" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:border-green-500/30 transition-all group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Security Score</p>
                <p
                  className={`text-2xl font-bold ${
                    (liveSecurityScore ?? stats.security_score ?? 0) >= 80
                      ? "text-green-400"
                      : (liveSecurityScore ?? stats.security_score ?? 0) >= 60
                      ? "text-yellow-400"
                      : "text-red-400"
                  }`}
                >
                  {Math.round(liveSecurityScore ?? stats.security_score ?? 0)}
                </p>
                <div className="w-full bg-gray-700/50 rounded-full h-1.5 mt-2">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      (liveSecurityScore ?? stats.security_score ?? 0) >= 80
                        ? "bg-green-500"
                        : (liveSecurityScore ?? stats.security_score ?? 0) >= 60
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                    style={{
                      width: `${
                        liveSecurityScore ?? stats.security_score ?? 0
                      }%`,
                    }}
                  />
                </div>
              </div>
              <ShieldCheckIcon className="h-8 w-8 text-green-400 group-hover:scale-110 transition-transform" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:border-purple-500/30 transition-all group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Last Scan</p>
                <p className="text-sm font-medium text-white">
                  {scanCompleted
                    ? "Just now"
                    : stats.last_scan_date
                    ? utils.formatRelativeDate(stats.last_scan_date)
                    : "Never"}
                </p>
                {!stats.last_scan_date && !scanCompleted && (
                  <button
                    onClick={handleStartScan}
                    disabled={!!activeScan || startScanMutation.isPending}
                    className="mt-2 text-xs text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-50"
                  >
                    Run first scan →
                  </button>
                )}
              </div>
              <ClockIcon className="h-8 w-8 text-purple-400 group-hover:scale-110 transition-transform" />
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
                              href={project.repository?.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 transition-colors break-all"
                            >
                              {project.repository?.url || "Not configured"}
                            </a>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Branch</span>
                          <span className="text-white font-mono">
                            {project.repository?.branch || "main"}
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
                            count: vulnCounts.critical,
                            color: "text-red-400",
                          },
                          {
                            severity: "high",
                            count: vulnCounts.high,
                            color: "text-orange-400",
                          },
                          {
                            severity: "medium",
                            count: vulnCounts.medium,
                            color: "text-yellow-400",
                          },
                          {
                            severity: "low",
                            count: vulnCounts.low,
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
                    {scanHistory.reports.map((scan, index) => (
                      <div
                        key={scan.id}
                        className={`bg-gray-900/50 rounded-xl p-6 border transition-all ${
                          index === 0 && scan.status === "completed"
                            ? "border-green-500/50 ring-1 ring-green-500/20"
                            : "border-gray-700/50 hover:border-gray-600/50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h4 className="text-white font-medium">
                                Scan #{scan.id.slice(-8)}
                              </h4>
                              <span
                                className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${
                                  scan.status === "completed"
                                    ? "bg-green-500/20 text-green-400 border border-green-500/30"
                                    : scan.status === "running"
                                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                                    : scan.status === "pending"
                                    ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                                    : "bg-red-500/20 text-red-400 border border-red-500/30"
                                }`}
                              >
                                {scan.status === "running" && (
                                  <ArrowPathIcon className="h-3 w-3 animate-spin" />
                                )}
                                <span className="capitalize">
                                  {scan.status}
                                </span>
                              </span>
                              {index === 0 && scan.status === "completed" && (
                                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full border border-blue-500/30">
                                  Latest
                                </span>
                              )}
                            </div>
                            <div className="flex items-center flex-wrap gap-4 text-sm text-gray-400 mb-3">
                              <span className="flex items-center space-x-1">
                                <ClockIcon className="h-4 w-4" />
                                <span>
                                  {utils.formatRelativeDate(scan.created_at)}
                                </span>
                              </span>
                              <span>Branch: {scan.branch || "main"}</span>
                              {scan.duration_seconds && (
                                <span>
                                  Duration:{" "}
                                  {utils.formatDuration(scan.duration_seconds)}
                                </span>
                              )}
                            </div>

                            {/* Vulnerability Summary for completed scans */}
                            {scan.status === "completed" && (
                              <div className="flex items-center space-x-3">
                                <span className="text-gray-500 text-sm">
                                  Findings:
                                </span>
                                {scan.findings_by_severity?.critical > 0 && (
                                  <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-lg border border-red-500/30 font-medium">
                                    {scan.findings_by_severity.critical}{" "}
                                    Critical
                                  </span>
                                )}
                                {scan.findings_by_severity?.high > 0 && (
                                  <span className="px-2 py-1 bg-orange-500/20 text-orange-400 text-xs rounded-lg border border-orange-500/30 font-medium">
                                    {scan.findings_by_severity.high} High
                                  </span>
                                )}
                                {scan.findings_by_severity?.medium > 0 && (
                                  <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded-lg border border-yellow-500/30 font-medium">
                                    {scan.findings_by_severity.medium} Medium
                                  </span>
                                )}
                                {scan.findings_by_severity?.low > 0 && (
                                  <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-lg border border-blue-500/30 font-medium">
                                    {scan.findings_by_severity.low} Low
                                  </span>
                                )}
                                {(scan.total_findings === 0 ||
                                  (!scan.findings_by_severity?.critical &&
                                    !scan.findings_by_severity?.high &&
                                    !scan.findings_by_severity?.medium &&
                                    !scan.findings_by_severity?.low)) && (
                                  <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-lg border border-green-500/30 font-medium flex items-center space-x-1">
                                    <CheckCircleIcon className="h-3 w-3" />
                                    <span>No Issues Found</span>
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center space-x-3">
                            {scan.status === "completed" && (
                              <Link
                                to={`/report/${scan.id}`}
                                className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all flex items-center space-x-2 shadow-lg shadow-blue-500/20"
                              >
                                <EyeIcon className="h-4 w-4" />
                                <span>View Report</span>
                              </Link>
                            )}
                            {scan.status === "running" && (
                              <div className="px-4 py-2.5 bg-blue-500/20 text-blue-400 rounded-xl flex items-center space-x-2">
                                <ArrowPathIcon className="h-4 w-4 animate-spin" />
                                <span>In Progress...</span>
                              </div>
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

        {/* Enhanced Edit Project Modal - Matching Create Modal */}
        {showEditModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setShowEditModal(false)}
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
                        onClick={() => setShowEditModal(false)}
                        className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
                      >
                        <XMarkIcon className="h-6 w-6" />
                      </button>
                    </div>

                    <form onSubmit={handleUpdateProject} className="space-y-8">
                      {/* Basic Information */}
                      <div className="space-y-6">
                        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                          <InformationCircleIcon className="h-5 w-5 text-blue-400" />
                          <span>Basic Information</span>
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-3">
                              Project Name{" "}
                              <span className="text-red-400">*</span>
                            </label>
                            <input
                              type="text"
                              value={editForm.name}
                              onChange={(e) =>
                                setEditForm((prev) => ({
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
                              value={editForm.category}
                              onChange={(e) =>
                                setEditForm((prev) => ({
                                  ...prev,
                                  category: e.target.value,
                                }))
                              }
                              className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                            >
                              <option value="web_application">
                                🌐 Web Application
                              </option>
                              <option value="api_service">
                                🔌 API Service
                              </option>
                              <option value="mobile_app">📱 Mobile App</option>
                              <option value="microservice">
                                🔷 Microservice
                              </option>
                              <option value="library">📚 Library</option>
                              <option value="infrastructure">
                                🏗️ Infrastructure
                              </option>
                              <option value="other">📦 Other</option>
                            </select>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-3">
                            Description
                          </label>
                          <textarea
                            value={editForm.description}
                            onChange={(e) =>
                              setEditForm((prev) => ({
                                ...prev,
                                description: e.target.value,
                              }))
                            }
                            placeholder="Describe your project..."
                            rows={3}
                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none"
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-3">
                              Priority
                            </label>
                            <select
                              value={editForm.priority}
                              onChange={(e) =>
                                setEditForm((prev) => ({
                                  ...prev,
                                  priority: e.target.value,
                                }))
                              }
                              className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                            >
                              <option value="low">🟢 Low</option>
                              <option value="medium">🟡 Medium</option>
                              <option value="high">🟠 High</option>
                              <option value="critical">🔴 Critical</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-3">
                              Status
                            </label>
                            <select
                              value={editForm.status}
                              onChange={(e) =>
                                setEditForm((prev) => ({
                                  ...prev,
                                  status: e.target.value,
                                }))
                              }
                              className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                            >
                              <option value="active">✅ Active</option>
                              <option value="inactive">⏸️ Inactive</option>
                              <option value="archived">📁 Archived</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Repository Configuration */}
                      <div className="space-y-6">
                        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                          <CodeBracketIcon className="h-5 w-5 text-purple-400" />
                          <span>Repository Configuration</span>
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-3">
                              Repository URL
                            </label>
                            <input
                              type="url"
                              value={editForm.repository.url}
                              onChange={(e) =>
                                setEditForm((prev) => ({
                                  ...prev,
                                  repository: {
                                    ...prev.repository,
                                    url: e.target.value,
                                  },
                                }))
                              }
                              placeholder="https://github.com/user/repo"
                              className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-3">
                              Default Branch
                            </label>
                            <input
                              type="text"
                              value={editForm.repository.branch}
                              onChange={(e) =>
                                setEditForm((prev) => ({
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
                            value={editForm.repository.access_token}
                            onChange={(e) =>
                              setEditForm((prev) => ({
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
                          <p className="text-xs text-gray-500 mt-2">
                            Leave empty to keep current token
                          </p>
                        </div>
                      </div>

                      {/* Security Scanners */}
                      <div className="space-y-6">
                        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                          <ShieldCheckIcon className="h-5 w-5 text-green-400" />
                          <span>Security Scanners</span>
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {[
                            {
                              value: "sast",
                              label: "SAST",
                              description:
                                "Static Application Security Testing",
                            },
                            {
                              value: "secrets",
                              label: "Secrets",
                              description: "Secret & credential detection",
                            },
                            {
                              value: "dependency",
                              label: "Dependencies",
                              description: "Dependency vulnerability scanning",
                            },
                            {
                              value: "container",
                              label: "Container",
                              description: "Container image security scanning",
                            },
                            {
                              value: "iac",
                              label: "IaC",
                              description: "Infrastructure as Code scanning",
                            },
                            {
                              value: "dast",
                              label: "DAST",
                              description:
                                "Dynamic Application Security Testing",
                            },
                          ].map((scanner) => (
                            <button
                              key={scanner.value}
                              type="button"
                              onClick={() => toggleScanner(scanner.value)}
                              className={`p-4 rounded-xl border-2 transition-all text-left ${
                                editForm.scan_config.enabled_scanners.includes(
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
                                {editForm.scan_config.enabled_scanners.includes(
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

                        {/* Scan Configuration Options */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                          <label className="flex items-center space-x-3 p-4 bg-gray-800/30 rounded-xl border border-gray-700/50 cursor-pointer hover:bg-gray-800/50 transition-all">
                            <input
                              type="checkbox"
                              checked={editForm.scan_config.auto_scan_on_push}
                              onChange={(e) =>
                                setEditForm((prev) => ({
                                  ...prev,
                                  scan_config: {
                                    ...prev.scan_config,
                                    auto_scan_on_push: e.target.checked,
                                  },
                                }))
                              }
                              className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50"
                            />
                            <div>
                              <p className="text-white font-medium">
                                Auto-scan on Push
                              </p>
                              <p className="text-xs text-gray-400">
                                Automatically scan when code is pushed
                              </p>
                            </div>
                          </label>

                          <label className="flex items-center space-x-3 p-4 bg-gray-800/30 rounded-xl border border-gray-700/50 cursor-pointer hover:bg-gray-800/50 transition-all">
                            <input
                              type="checkbox"
                              checked={editForm.scan_config.fail_on_critical}
                              onChange={(e) =>
                                setEditForm((prev) => ({
                                  ...prev,
                                  scan_config: {
                                    ...prev.scan_config,
                                    fail_on_critical: e.target.checked,
                                  },
                                }))
                              }
                              className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50"
                            />
                            <div>
                              <p className="text-white font-medium">
                                Fail on Critical
                              </p>
                              <p className="text-xs text-gray-400">
                                Mark scan as failed if critical issues found
                              </p>
                            </div>
                          </label>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-3">
                            Scan Timeout (minutes)
                          </label>
                          <input
                            type="number"
                            min="5"
                            max="180"
                            value={editForm.scan_config.scan_timeout_minutes}
                            onChange={(e) =>
                              setEditForm((prev) => ({
                                ...prev,
                                scan_config: {
                                  ...prev.scan_config,
                                  scan_timeout_minutes:
                                    parseInt(e.target.value) || 60,
                                },
                              }))
                            }
                            className="w-full md:w-48 px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                          />
                        </div>
                      </div>

                      {/* Tags */}
                      <div className="space-y-6">
                        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                          <TagIcon className="h-5 w-5 text-yellow-400" />
                          <span>Tags</span>
                        </h3>

                        <div className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={tagInput}
                            onChange={(e) => setTagInput(e.target.value)}
                            onKeyPress={(e) =>
                              e.key === "Enter" &&
                              (e.preventDefault(), addTag())
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

                        {editForm.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {editForm.tags.map((tag) => (
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
                          onClick={() => setShowEditModal(false)}
                          className="px-6 py-3 text-gray-300 hover:text-white transition-all"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={updateProjectMutation.isPending}
                          className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition-all flex items-center space-x-2"
                        >
                          {updateProjectMutation.isPending ? (
                            <>
                              <ArrowPathIcon className="h-5 w-5 animate-spin" />
                              <span>Saving...</span>
                            </>
                          ) : (
                            <>
                              <CheckCircleIcon className="h-5 w-5" />
                              <span>Save Changes</span>
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div
              className="fixed inset-0 bg-black/70 backdrop-blur-sm"
              onClick={() => {
                setShowDeleteModal(false);
                setDeleteConfirmText("");
              }}
            />
            <div className="flex min-h-full items-center justify-center p-4">
              <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-red-900/30 shadow-2xl p-6 w-full max-w-md">
                <div className="text-center">
                  {/* Warning Icon with Animation */}
                  <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4 animate-pulse">
                    <ExclamationTriangleIcon className="h-10 w-10 text-red-400" />
                  </div>

                  <h3 className="text-xl font-bold text-white mb-2">
                    Delete Project Permanently
                  </h3>
                  <p className="text-gray-400 mb-4">
                    You are about to permanently delete{" "}
                    <span className="text-red-400 font-semibold">
                      "{project.name}"
                    </span>
                    .
                  </p>

                  {/* Warning Box */}
                  <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-4 mb-6 text-left">
                    <p className="text-red-300 text-sm font-medium mb-2">
                      ⚠️ This action will permanently delete:
                    </p>
                    <ul className="text-red-200/80 text-sm space-y-1.5 ml-4">
                      <li>• The project and all its configuration</li>
                      <li>
                        • All scan reports and vulnerability findings (
                        {stats.total_scans || 0} scans)
                      </li>
                      <li>• All webhook events and history</li>
                      <li>• All team member associations</li>
                    </ul>
                    <p className="text-red-400 text-sm font-bold mt-3 text-center">
                      🚫 This action cannot be undone!
                    </p>
                  </div>

                  {/* Confirmation Input */}
                  <div className="mb-6">
                    <label className="block text-sm text-gray-400 mb-2">
                      Type{" "}
                      <span className="text-red-400 font-mono font-bold">
                        DELETE
                      </span>{" "}
                      to confirm:
                    </label>
                    <input
                      type="text"
                      value={deleteConfirmText}
                      onChange={(e) => setDeleteConfirmText(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-800/50 border border-red-800/30 rounded-xl text-white text-center font-mono focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50"
                      placeholder="DELETE"
                    />
                  </div>

                  {/* Buttons */}
                  <div className="flex space-x-3">
                    <button
                      onClick={() => {
                        setShowDeleteModal(false);
                        setDeleteConfirmText("");
                      }}
                      className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-xl hover:bg-gray-600 transition-all font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDeleteProject}
                      disabled={
                        deleteProjectMutation.isPending ||
                        deleteConfirmText !== "DELETE"
                      }
                      className="flex-1 px-4 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center justify-center space-x-2"
                    >
                      {deleteProjectMutation.isPending ? (
                        <>
                          <ArrowPathIcon className="h-5 w-5 animate-spin" />
                          <span>Deleting...</span>
                        </>
                      ) : (
                        <>
                          <TrashIcon className="h-5 w-5" />
                          <span>Delete Forever</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
};

export default ProjectDetails;
