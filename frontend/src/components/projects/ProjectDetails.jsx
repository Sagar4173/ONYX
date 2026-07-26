import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ShieldCheckIcon,
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { projectsAPI, reportsAPI } from "../../services/api";
import { PageContainer, PageHeader } from "../../layouts";
import ProjectSidebar from "./ProjectSidebar";
import ParticleBackground from "./ParticleBackground";
import ScanPipeline from "./ScanPipeline";
import LiveConsole from "./LiveConsole";
import MetricsDashboard from "./MetricsDashboard";
import OverviewTab from "./OverviewTab";
import ScanHistoryTab from "./ScanHistoryTab";
import SettingsTab from "./SettingsTab";
import EditProjectModal from "./EditProjectModal";
import DeleteProjectModal from "./DeleteProjectModal";

const TABS = [
  { key: "overview", label: "Overview", icon: ShieldCheckIcon },
  { key: "scans", label: "Scan History", icon: ArrowPathIcon },
  { key: "settings", label: "Settings", icon: ArrowPathIcon },
];

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
    repository: { url: "", branch: "main", access_token: "" },
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
  const [activeScan, setActiveScan] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  const [scanCompleted, setScanCompleted] = useState(false);
  const hasShownCompletionToast = useRef(false);

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

  const {
    data: scanHistory,
    isLoading: scanHistoryLoading,
    refetch: refetchScanHistory,
  } = useQuery({
    queryKey: ["projectScans", projectId],
    queryFn: () => reportsAPI.getReports({ project_id: projectId, limit: 20 }),
    enabled: !!projectId,
    refetchInterval: isPolling ? 3000 : false,
  });

  const { refetch: refetchAnalytics } = useQuery({
    queryKey: ["projectAnalytics", projectId],
    queryFn: () => projectsAPI.getProjectAnalytics(projectId),
    enabled: !!projectId,
  });

  useEffect(() => {
    const handler = () => setShowDeleteModal(true);
    document.addEventListener("open-delete-modal", handler);
    return () => document.removeEventListener("open-delete-modal", handler);
  }, []);

  const pollScanStatus = useCallback(async () => {
    if (!activeScan?.scan_id || !isPolling) return;
    try {
      const status = await reportsAPI.getScanStatus(activeScan.scan_id);
      if (status) {
        setScanProgress(status.progress || 0);
        setActiveScan((prev) => ({
          ...prev,
          status: status.status || prev?.status,
          progress: status.progress || prev?.progress,
          current_scanner: status.current_scanner || prev?.current_scanner,
          total_findings: status.total_findings,
          findings_by_severity: status.findings_by_severity,
        }));
        if (
          status.status === "completed" ||
          status.status === "failed" ||
          status.status === "cancelled"
        ) {
          setIsPolling(false);
          if (!hasShownCompletionToast.current) {
            hasShownCompletionToast.current = true;
            if (status.status === "completed") {
              const criticalHigh =
                (status.findings_by_severity?.critical || 0) +
                (status.findings_by_severity?.high || 0);
              if (criticalHigh > 0)
                toast.error(
                  `Scan completed with ${criticalHigh} critical/high severity issues! Total: ${status.total_findings || 0} findings.`,
                  { duration: 5000 }
                );
              else if (status.total_findings > 0)
                toast.success(
                  `Scan completed! Found ${status.total_findings} findings (no critical/high issues).`,
                  { duration: 4000 }
                );
              else toast.success("Scan completed! No security issues found.", { duration: 4000 });
            } else if (status.status === "cancelled") {
              toast("Scan was cancelled.", { icon: "info" });
            } else {
              toast.error(status.error_message || "Scan failed.");
            }
          }
          const completedTime = new Date().toISOString();
          const finalProgress = status.status === "completed" ? 100 : status.progress || 0;
          setActiveScan((prev) => ({
            ...prev,
            ...status,
            started_at: prev?.started_at,
            report_id: status.id || prev?.scan_id,
            status: status.status,
            progress: finalProgress,
            total_findings: status.total_findings || 0,
            findings_by_severity: status.findings_by_severity || {},
            error_message: status.error_message || null,
            completed_at: completedTime,
          }));
          setScanProgress(finalProgress);
          setScanCompleted(true);
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["projectScans", projectId] });
            queryClient.invalidateQueries({ queryKey: ["project", projectId] });
            queryClient.invalidateQueries({ queryKey: ["projectAnalytics", projectId] });
            refetchProject();
            refetchScanHistory();
            refetchAnalytics();
          }, 1000);
        }
      }
    } catch (error) {
      console.error("Error polling scan status:", error);
    }
  }, [
    activeScan?.scan_id,
    isPolling,
    projectId,
    queryClient,
    refetchAnalytics,
    refetchProject,
    refetchScanHistory,
  ]);

  useEffect(() => {
    let interval;
    if (isPolling && activeScan?.scan_id) {
      pollScanStatus();
      interval = setInterval(pollScanStatus, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPolling, activeScan?.scan_id, pollScanStatus]);

  const startScanMutation = useMutation({
    mutationFn: (scanData) => reportsAPI.startScan(scanData),
    onSuccess: (data) => {
      toast.success("Security scan started! Monitoring progress...");
      hasShownCompletionToast.current = false;
      setScanCompleted(false);
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
      queryClient.invalidateQueries({ queryKey: ["projectScans", projectId] });
    },
    onError: (error) => toast.error(error.message || "Failed to start scan"),
  });

  const stopScanMutation = useMutation({
    mutationFn: (scanId) => reportsAPI.stopScan(scanId),
    onSuccess: () => {
      toast("Scan stopped.", { icon: "info" });
      setActiveScan(null);
      setScanProgress(0);
      setIsPolling(false);
      hasShownCompletionToast.current = false;
      queryClient.invalidateQueries({ queryKey: ["projectScans", projectId] });
    },
    onError: (error) => toast.error(error.message || "Failed to stop scan"),
  });

  const updateProjectMutation = useMutation({
    mutationFn: (updateData) => projectsAPI.updateProject(projectId, updateData),
    onSuccess: () => {
      toast.success("Project updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setShowEditModal(false);
    },
    onError: (error) => toast.error(error.message || "Failed to update project"),
  });

  const deleteProjectMutation = useMutation({
    mutationFn: () => projectsAPI.deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["userProjects"] });
      navigate("/projects");
    },
    onError: (error) => toast.error(error.message || "Failed to delete project"),
  });

  const handleStartScan = () => {
    if (!project || activeScan) return;
    startScanMutation.mutate({
      repository_url: project.repository?.url,
      branch: project.repository?.branch || "main",
      scan_types: project.scan_config?.enabled_scanners || ["sast", "secrets", "container"],
      project_id: projectId,
    });
  };

  const handleStopScan = () => {
    if (activeScan?.scan_id) stopScanMutation.mutate(activeScan.scan_id);
  };

  const handleDeleteProject = () => {
    if (deleteConfirmText !== "DELETE") return;
    deleteProjectMutation.mutate();
    setShowDeleteModal(false);
    setDeleteConfirmText("");
  };

  const openEditModal = () => {
    if (!project) return;
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
        enabled_scanners: project.scan_config?.enabled_scanners || ["sast", "secrets"],
        auto_scan_on_push: project.scan_config?.auto_scan_on_push || false,
        scan_timeout_minutes: project.scan_config?.scan_timeout_minutes || 60,
        fail_on_critical: project.scan_config?.fail_on_critical || false,
      },
      tags: project.tags || [],
    });
    setTagInput("");
    setShowEditModal(true);
  };

  const handleUpdateProject = (e) => {
    e.preventDefault();
    updateProjectMutation.mutate(editForm);
  };

  const addTag = () => {
    if (tagInput.trim() && !editForm.tags.includes(tagInput.trim())) {
      setEditForm((prev) => ({ ...prev, tags: [...prev.tags, tagInput.trim()] }));
      setTagInput("");
    }
  };
  const removeTag = (tagToRemove) => {
    setEditForm((prev) => ({ ...prev, tags: prev.tags.filter((tag) => tag !== tagToRemove) }));
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
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4" />
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
            <h2 className="text-xl font-semibold text-white mb-2">Project Not Found</h2>
            <p className="text-gray-400 mb-6">
              The project you're looking for doesn't exist or you don't have access to it.
            </p>
            <button
              onClick={() => navigate("/projects")}
              className="px-6 py-3 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
            >
              Back to Projects
            </button>
          </div>
        </div>
      </div>
    );
  }

  const stats = project.stats || {};
  const liveFindings =
    scanCompleted && activeScan?.findings_by_severity ? activeScan.findings_by_severity : null;
  const vulnCounts = {
    critical: liveFindings?.critical ?? stats.critical_vulnerabilities ?? 0,
    high: liveFindings?.high ?? stats.high_vulnerabilities ?? 0,
    medium: liveFindings?.medium ?? stats.medium_vulnerabilities ?? 0,
    low: liveFindings?.low ?? stats.low_vulnerabilities ?? 0,
  };
  const totalVulns = vulnCounts.critical + vulnCounts.high + vulnCounts.medium + vulnCounts.low;
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
  const securityScore = liveSecurityScore ?? stats.security_score ?? 85;

  const runningScans =
    scanHistory?.reports?.filter(
      (r) => (r.status === "running" || r.status === "pending") && r.scan_id !== activeScan?.scan_id
    ) || [];
  const isScanActive =
    !scanCompleted &&
    ((activeScan &&
      activeScan.status !== "completed" &&
      activeScan.status !== "failed" &&
      activeScan.status !== "cancelled") ||
      runningScans.length > 0);

  const liveScanData = {
    activeScan,
    scanProgress,
    scanCompleted,
    isScanActive,
    isStopping: stopScanMutation.isPending,
    isStarting: startScanMutation.isPending,
    onStopScan: handleStopScan,
    onStartScan: handleStartScan,
    onDismiss: () => {
      setActiveScan(null);
      setScanCompleted(false);
      setScanProgress(0);
    },
    onRunNewScan: () => {
      setActiveScan(null);
      setScanCompleted(false);
      setScanProgress(0);
      hasShownCompletionToast.current = false;
      handleStartScan();
    },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <PageHeader
            title={project.name}
            description={project.description || "No description provided"}
            icon={ShieldCheckIcon}
            breadcrumb={["Projects", project.name]}
            actions={
              <div className="flex items-center space-x-3">
                {isScanActive ? (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleStopScan}
                      disabled={stopScanMutation.isPending}
                      className="px-6 py-3 bg-gradient-to-r from-red-500 to-rose-600 text-white font-medium rounded-xl hover:from-red-600 hover:to-rose-700 disabled:opacity-50 transition-all flex items-center space-x-2 animate-pulse focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                    >
                      <StopIcon className="h-5 w-5" />
                      <span>{stopScanMutation.isPending ? "Stopping..." : "Stop Scan"}</span>
                    </button>
                    <div className="px-4 py-2 bg-cyan-500/20 rounded-xl flex items-center space-x-2">
                      <ArrowPathIcon className="h-4 w-4 text-cyan-400 animate-spin" />
                      <span className="text-cyan-400 text-sm font-medium">
                        {activeScan?.status === "running" ? "Scanning..." : "Pending..."}
                      </span>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={handleStartScan}
                    disabled={startScanMutation.isPending}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition-all flex items-center space-x-2 group focus:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                  >
                    <PlayIcon className="h-5 w-5 group-hover:scale-110 transition-transform" />
                    <span>{startScanMutation.isPending ? "Starting..." : "Start Scan"}</span>
                  </button>
                )}
              </div>
            }
          />

          <ScanPipeline liveScanData={liveScanData} />

          <MetricsDashboard
            stats={stats}
            vulnCounts={vulnCounts}
            totalVulns={totalVulns}
            liveSecurityScore={liveSecurityScore}
            securityScore={securityScore}
            scanCompleted={scanCompleted}
          />

          <LiveConsole liveScanData={liveScanData} />

          <div className="flex space-x-6">
            <ProjectSidebar
              project={project}
              vulnCounts={vulnCounts}
              securityScore={securityScore}
              isScanActive={isScanActive}
              onEdit={openEditModal}
              onDelete={() => setShowDeleteModal(true)}
            />

            <div className="flex-1 min-w-0">
              <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl mb-6">
                <div className="flex border-b border-gray-700/50">
                  {TABS.map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`flex items-center space-x-2 px-6 py-4 text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                        activeTab === tab.key
                          ? "text-cyan-400 border-b-2 border-cyan-400"
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
                    <OverviewTab
                      project={project}
                      vulnCounts={vulnCounts}
                      totalVulns={totalVulns}
                      securityScore={securityScore}
                    />
                  )}
                  {activeTab === "scans" && (
                    <ScanHistoryTab
                      scanHistory={scanHistory}
                      scanHistoryLoading={scanHistoryLoading}
                      onStartScan={handleStartScan}
                      isStarting={startScanMutation.isPending}
                    />
                  )}
                  {activeTab === "settings" && <SettingsTab />}
                </div>
              </div>
            </div>
          </div>

          <EditProjectModal
            isOpen={showEditModal}
            onClose={() => setShowEditModal(false)}
            editForm={editForm}
            setEditForm={setEditForm}
            tagInput={tagInput}
            setTagInput={setTagInput}
            onAddTag={addTag}
            onRemoveTag={removeTag}
            onToggleScanner={toggleScanner}
            onSubmit={handleUpdateProject}
            isPending={updateProjectMutation.isPending}
          />
          <DeleteProjectModal
            isOpen={showDeleteModal}
            onClose={() => {
              setShowDeleteModal(false);
              setDeleteConfirmText("");
            }}
            projectName={project.name}
            totalScans={stats.total_scans || 0}
            deleteConfirmText={deleteConfirmText}
            setDeleteConfirmText={setDeleteConfirmText}
            onConfirm={handleDeleteProject}
            isPending={deleteProjectMutation.isPending}
          />
        </div>
      </PageContainer>
    </div>
  );
};

export default ProjectDetails;
