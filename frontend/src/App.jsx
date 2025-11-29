/**
 * SecureDevOps AI Platform - Next-Level UI/UX Design
 * Modern Dark Theme with Glassmorphism & Advanced Animations
 */
import React, { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
  useNavigate,
  Link,
} from "react-router-dom";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useMutation,
} from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import {
  ShieldCheckIcon,
  HomeIcon,
  DocumentTextIcon as DocumentReportIcon,
  CogIcon,
  BellIcon,
  UserCircleIcon,
  Bars3Icon as MenuIcon,
  XMarkIcon as XIcon,
  ChartBarIcon as AnalyticsIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  CommandLineIcon,
  GlobeAltIcon,
  CodeBracketIcon,
  BoltIcon,
  EyeIcon,
  ArrowPathIcon,
  PlayIcon,
  UsersIcon,
  ClockIcon,
  ArchiveBoxIcon,
  BuildingOfficeIcon,
} from "@heroicons/react/24/outline";
import {
  ChartBarIcon,
  ShieldCheckIcon as ShieldCheckSolid,
  SparklesIcon as SparklesSolid,
} from "@heroicons/react/24/solid";

// Components - Organized by category
import {
  ProjectList,
  ProjectManagement,
  ProjectDetails,
} from "./components/projects";
import {
  ReportDetails,
  EnhancedReportDetails,
  ComplianceReport,
} from "./components/reports";
import {
  AdvancedCompliance,
  DataRetentionPolicies,
} from "./components/compliance";
import { UserManagement, AuditLogs } from "./components/users";
import { Settings } from "./components/settings";
import { LandingPage } from "./components/marketing";
import { Analytics, Reports, NotFound } from "./pages";
import { PageContainer, PageHeader, GlassCard, SectionHeader } from "./layouts";
import {
  AuthProvider,
  useAuth,
  AuthModal,
  EmailVerification,
} from "./components/auth";
import { UserProfile } from "./components/auth/UserProfile";
import { websocketService, reportsAPI, authAPI } from "./services/api";
import useScanTracker from "./hooks/useScanTracker";
import toast from "react-hot-toast";

// Create a client for React Query with enhanced settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
      refetchInterval: 30000, // Real-time updates every 30s
    },
  },
});

// Modern Scan Submission Modal with Glassmorphism
const ScanModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    repository_url: "",
    branch: "main",
    scan_types: ["sast", "secrets", "container"],
    access_token: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const scanTypes = [
    {
      id: "sast",
      label: "Static Analysis",
      icon: CodeBracketIcon,
      color: "from-blue-500 to-cyan-500",
    },
    {
      id: "secrets",
      label: "Secret Detection",
      icon: EyeIcon,
      color: "from-purple-500 to-pink-500",
    },
    {
      id: "container",
      label: "Container Scan",
      icon: CommandLineIcon,
      color: "from-green-500 to-emerald-500",
    },
    {
      id: "infrastructure",
      label: "Infrastructure",
      icon: GlobeAltIcon,
      color: "from-orange-500 to-red-500",
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate repository URL
    if (!formData.repository_url.trim()) {
      toast.error("Please enter a repository URL");
      return;
    }

    // Basic URL validation
    const urlPattern = /^https?:\/\/.+/i;
    if (!urlPattern.test(formData.repository_url.trim())) {
      toast.error(
        "Please enter a valid repository URL (must start with http:// or https://)"
      );
      return;
    }

    setIsSubmitting(true);
    try {
      console.log("🚀 Submitting scan with data:", formData);
      await onSubmit(formData);

      // Reset form and close modal
      setFormData({
        repository_url: "",
        branch: "main",
        scan_types: ["sast", "secrets", "container"],
        access_token: "",
      });
      onClose();

      // Success message is handled by the mutation
    } catch (error) {
      console.error("❌ Modal handleSubmit error:", error);

      // Extract error message for modal-specific handling
      let errorMessage = "Failed to start scan";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }

      // Show error in modal context (shorter message)
      toast.error(`❌ ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleScanType = (type) => {
    setFormData((prev) => ({
      ...prev,
      scan_types: prev.scan_types.includes(type)
        ? prev.scan_types.filter((t) => t !== type)
        : [...prev.scan_types, type],
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop with Blur */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto transform rounded-2xl lg:rounded-3xl bg-gray-900/90 backdrop-blur-xl border border-gray-800/50 shadow-2xl transition-all">
          {/* Gradient Background */}
          <div className="absolute inset-0 rounded-2xl lg:rounded-3xl bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10" />

          {/* Content */}
          <div className="relative p-4 sm:p-6 lg:p-8">
            {/* Header */}
            <div className="flex items-start sm:items-center justify-between mb-6 lg:mb-8 gap-4">
              <div className="flex items-center space-x-3 min-w-0">
                <div className="p-2 lg:p-3 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 flex-shrink-0">
                  <SparklesSolid className="h-5 w-5 lg:h-6 lg:w-6 text-white" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-white">
                    Start Security Scan
                  </h3>
                  <p className="text-gray-400 text-sm lg:text-base">
                    AI-powered vulnerability detection
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all flex-shrink-0"
              >
                <XIcon className="h-5 w-5 lg:h-6 lg:w-6" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4 lg:space-y-6">
              {/* Repository URL */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 lg:mb-3">
                  Repository URL
                </label>
                <div className="relative">
                  <GlobeAltIcon className="absolute left-3 lg:left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 lg:h-5 lg:w-5 text-gray-400" />
                  <input
                    type="url"
                    value={formData.repository_url}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        repository_url: e.target.value,
                      }))
                    }
                    placeholder="https://github.com/username/repository"
                    className="w-full pl-10 lg:pl-12 pr-3 lg:pr-4 py-3 lg:py-4 bg-gray-800/50 border border-gray-700/50 rounded-xl lg:rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm lg:text-base"
                    required
                  />
                </div>
              </div>

              {/* Access Token for Private Repositories */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Access Token (Optional - for private repositories)
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                    <svg
                      className="h-5 w-5 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                      />
                    </svg>
                  </div>
                  <input
                    type="password"
                    value={formData.access_token || ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        access_token: e.target.value,
                      }))
                    }
                    placeholder="ghp_xxxxxxxxxxxx (GitHub) or glpat-xxxxxxxxxxxx (GitLab)"
                    className="w-full pl-12 pr-4 py-4 bg-gray-800/50 border border-gray-700/50 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  />
                </div>
                <div className="mt-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                  <div className="flex items-start space-x-2">
                    <svg
                      className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div className="text-xs text-blue-300">
                      <p className="font-medium mb-1">
                        For Private Repositories:
                      </p>
                      <p>
                        • GitHub: Generate token at Settings → Developer
                        settings → Personal access tokens
                      </p>
                      <p>
                        • GitLab: Generate token at User Settings → Access
                        Tokens
                      </p>
                      <p>
                        • Required permissions:{" "}
                        <span className="font-medium">repo</span> (GitHub) or{" "}
                        <span className="font-medium">read_repository</span>{" "}
                        (GitLab)
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Branch */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Branch
                </label>
                <input
                  type="text"
                  value={formData.branch}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, branch: e.target.value }))
                  }
                  placeholder="main"
                  className="w-full px-4 py-4 bg-gray-800/50 border border-gray-700/50 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                />
              </div>

              {/* Enhanced Scan Types with better visual feedback */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-4">
                  Scan Types
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {scanTypes.map((type, index) => (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => toggleScanType(type.id)}
                      style={{ animationDelay: `${index * 0.1}s` }}
                      className={`group relative p-4 rounded-2xl border-2 transition-all duration-300 animate-fade-in-up hover:scale-105 ${
                        formData.scan_types.includes(type.id)
                          ? "border-blue-500/70 bg-blue-500/20 shadow-lg shadow-blue-500/20"
                          : "border-gray-700/50 bg-gray-800/30 hover:border-gray-600/50 hover:bg-gray-700/40"
                      }`}
                    >
                      {formData.scan_types.includes(type.id) && (
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl animate-glow" />
                      )}
                      <div className="relative flex items-center space-x-3">
                        <div
                          className={`p-2 rounded-xl bg-gradient-to-r ${type.color} shadow-lg group-hover:shadow-xl transition-all`}
                        >
                          <type.icon className="h-5 w-5 text-white" />
                        </div>
                        <div className="text-left">
                          <span className="text-white font-medium block">
                            {type.label}
                          </span>
                          <span className="text-xs text-gray-400">
                            {type.id === "sast" && "Static analysis"}
                            {type.id === "secrets" && "Secret detection"}
                            {type.id === "container" && "Container security"}
                            {type.id === "infrastructure" && "IaC scanning"}
                          </span>
                        </div>
                      </div>
                      {formData.scan_types.includes(type.id) && (
                        <div className="absolute -top-1 -right-1 h-4 w-4 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                          <CheckCircleIcon className="h-3 w-3 text-white" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-3 lg:py-4 px-4 lg:px-6 rounded-xl lg:rounded-2xl border border-gray-700/50 text-gray-300 hover:text-white hover:bg-gray-800/50 transition-all text-sm lg:text-base font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-3 lg:py-4 px-4 lg:px-6 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition-all flex items-center justify-center space-x-2 text-sm lg:text-base"
                >
                  {isSubmitting ? (
                    <>
                      <ArrowPathIcon className="h-4 w-4 lg:h-5 lg:w-5 animate-spin" />
                      <span>Starting Scan...</span>
                    </>
                  ) : (
                    <>
                      <PlayIcon className="h-4 w-4 lg:h-5 lg:w-5" />
                      <span>Start Scan</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

// Email Verification Page Component
const EmailVerificationPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get("token");

  const handleVerificationSuccess = () => {
    if (isAuthenticated) {
      // User is logged in - redirect to dashboard
      navigate("/dashboard", {
        state: {
          message: "Email verified successfully!",
          from: "verification",
        },
        replace: true,
      });
    } else {
      // User is not logged in - show success and prompt to login
      // Show success message via toast
      toast.success(
        "Email verified successfully! Please log in to access your account."
      );

      // Navigate to home with login modal open after a short delay
      setTimeout(() => {
        navigate("/login", { replace: true });
      }, 2000);
    }
  };

  const handleVerificationError = () => {
    navigate("/login");
  };

  return (
    <EmailVerification
      token={token}
      onSuccess={handleVerificationSuccess}
      onError={handleVerificationError}
    />
  );
};

// Password Reset Page Component
const PasswordResetPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get("token");

  const handleResetSuccess = () => {
    navigate("/dashboard", {
      state: {
        message:
          "Password reset successfully! Please log in with your new password.",
      },
    });
  };

  const handleSwitchToLogin = () => {
    navigate("/login");
  };

  if (!token) {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-red-500 to-pink-600 rounded-2xl mb-4">
          <ExclamationTriangleIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          Invalid Reset Link
        </h2>
        <p className="text-gray-400 mb-6">
          The password reset link is invalid or has expired.
        </p>
        <button
          onClick={handleSwitchToLogin}
          className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
        >
          Back to Login
        </button>
      </div>
    );
  }

  return (
    <AuthModal
      isOpen={true}
      onClose={handleSwitchToLogin}
      initialView="reset-password"
      resetToken={token}
    />
  );
};

// Component to handle authentication routing inside Router context
const AuthRoutingHandler = ({ authModalOpen, setAuthModalOpen }) => {
  const location = useLocation();

  const publicRoutes = [
    "/",
    "/landing",
    "/login",
    "/register",
    "/reset-password",
    "/verify-email",
  ];
  const isPublicRoute = publicRoutes.some(
    (route) => location.pathname.startsWith(route) || location.pathname === "/"
  );

  if (isPublicRoute) {
    // For public routes, render the specific route components
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/landing" element={<LandingPage />} />
          <Route
            path="/login"
            element={
              <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                <AuthModal
                  isOpen={true}
                  onClose={() => window.history.back()}
                  initialView="login"
                />
              </div>
            }
          />
          <Route
            path="/register"
            element={
              <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                <AuthModal
                  isOpen={true}
                  onClose={() => window.history.back()}
                  initialView="register"
                />
              </div>
            }
          />
          <Route
            path="/verify-email"
            element={
              <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                <EmailVerificationPage />
              </div>
            }
          />
          <Route
            path="/reset-password"
            element={
              <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                <PasswordResetPage />
              </div>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    );
  }

  // For non-public routes when not authenticated, show login modal
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <AuthModal isOpen={true} onClose={() => setAuthModalOpen(false)} />
    </div>
  );
};

// Separate AppContent component that uses QueryClient hooks
function AppContent() {
  // Always call ALL hooks at the top level, before any conditional returns
  const { user, isAuthenticated, isLoading, logout, refreshUserProfile } =
    useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [scanModalOpen, setScanModalOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [notificationPanelOpen, setNotificationPanelOpen] = useState(false);
  const location = useLocation();

  // Check for verification success message and refresh profile
  useEffect(() => {
    if (
      isAuthenticated &&
      location.state?.message &&
      location.state?.from === "verification"
    ) {
      // If there's a verification success message, refresh the user profile
      refreshUserProfile()
        .then(() => {
          // Clear the state after processing to prevent infinite loops
          window.history.replaceState({}, document.title, location.pathname);
        })
        .catch((error) => {
          console.log("Could not refresh profile:", error);
        });
    }
  }, [isAuthenticated, location.state?.message, location.state?.from]);

  // Close notification panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        notificationPanelOpen &&
        !event.target.closest(".notification-panel")
      ) {
        setNotificationPanelOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [notificationPanelOpen]);

  // Scan mutation for repository submission - moved to top
  const scanMutation = useMutation({
    mutationFn: async (scanData) => {
      // Use the reportsAPI service for scan calls
      return await reportsAPI.startScan(scanData);
    },
    onSuccess: (data) => {
      console.log("✅ Scan started successfully:", data);

      // Show detailed success message with scan ID
      const projectName = data.project_name || "Repository";
      const scanId = data.scan_id?.slice(-8) || "Unknown";

      toast.success(
        `🚀 Scan initiated for ${projectName}!\nScan ID: ${scanId}\n⏳ Processing in background...`,
        { duration: 8000 }
      );

      // Add notification for successful scan start with more details
      setNotifications((prev) => [
        {
          id: Date.now(),
          type: "scan_started",
          message: `Security scan initiated for ${projectName} (ID: ${scanId})`,
          timestamp: new Date(),
          data: {
            ...data,
            scan_url: `/scans/${data.scan_id}`,
            status_message:
              "Scan is processing. Check the Reports section for updates.",
          },
        },
        ...prev.slice(0, 9),
      ]);

      // Show follow-up instructions
      setTimeout(() => {
        toast(
          `💡 Tip: Check the Reports section to monitor your scan progress`,
          {
            icon: "💡",
            duration: 6000,
          }
        );
      }, 3000);

      queryClient.invalidateQueries(["reports"]);

      // Auto-refresh reports after a short delay to show new scan
      setTimeout(() => {
        queryClient.invalidateQueries(["reports"]);
      }, 2000);
    },
    onError: (error) => {
      console.error("❌ Scan submission failed:", error);

      // Extract meaningful error message
      let errorMessage = "Failed to start scan";
      let errorDetails = "";
      let suggestions = "";

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }

        // Add helpful suggestions based on error type
        if (error.response.status === 400) {
          suggestions = "\n💡 Check your repository URL format";
        } else if (error.response.status === 403) {
          suggestions = "\n💡 Check repository permissions";
        } else if (error.response.status === 500) {
          suggestions = "\n💡 Server error - try again in a few minutes";
        }

        // Add status code context
        errorDetails = ` (${error.response.status})`;
      } else if (error.message) {
        errorMessage = error.message;
        suggestions = "\n💡 Check your internet connection";
      }

      // Show detailed error message
      toast.error(`❌ ${errorMessage}${errorDetails}${suggestions}`, {
        duration: 10000,
      });

      // Add error notification
      setNotifications((prev) => [
        {
          id: Date.now(),
          type: "scan_error",
          message: `Scan submission failed: ${errorMessage}`,
          timestamp: new Date(),
          data: {
            error: error.response?.data || error.message,
            suggestions: suggestions.replace("\n💡 ", ""),
          },
        },
        ...prev.slice(0, 9),
      ]);
    },
  });

  // Enhanced WebSocket connection with better error handling - moved to top
  useEffect(() => {
    // Add a small delay to let the backend fully start up
    setTimeout(() => {
      websocketService.connect();
    }, 1000);

    websocketService.on("connected", (connected) => {
      setIsConnected(connected);
      // Only show toast on reconnection, not initial connection
      if (connected && isConnected === false) {
        toast.success("🔗 Real-time connection restored");
      }
    });

    websocketService.on("disconnected", () => {
      setIsConnected(false);
      // Only show error if we were previously connected
      if (isConnected) {
        toast.error("🔴 Connection lost");
      }
    });

    websocketService.on("scan_update", (data) => {
      const scanData = data.data || data;

      // Handle different message formats
      const projectName = scanData.project_name || scanData.projectName;
      const scanStatus = scanData.status;
      const scanType = scanData.scan_type || scanData.type || "security";
      const progress = scanData.progress;
      const customMessage = scanData.message;

      // Build notification message based on available data
      let notificationMessage;
      if (projectName && scanStatus) {
        // Real scan notification with project info
        notificationMessage = `${scanType.toUpperCase()} scan ${scanStatus} for ${projectName}`;
      } else if (customMessage) {
        // Use the message field from demo/progress updates
        notificationMessage = customMessage;
        if (progress !== undefined) {
          notificationMessage += ` (${progress}%)`;
        }
      } else if (progress !== undefined) {
        // Progress-only update
        notificationMessage = `Scan in progress: ${progress}%`;
      } else {
        // Fallback
        notificationMessage = "Scan update received";
      }

      setNotifications((prev) => [
        {
          id: Date.now(),
          type: "scan_update",
          message: notificationMessage,
          timestamp: new Date(),
          data: scanData,
        },
        ...prev.slice(0, 9),
      ]);

      // Show toast for important updates
      if (scanStatus === "completed" && projectName) {
        toast.success(`✅ Scan completed for ${projectName}`);
      } else if (scanStatus === "failed" && projectName) {
        toast.error(`❌ Scan failed for ${projectName}`);
      }
    });

    return () => {
      websocketService.disconnect();
    };
  }, []);

  // Now handle conditional rendering after all hooks are called
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4 animate-pulse">
            <ShieldCheckIcon className="h-8 w-8 text-white" />
          </div>
          <p className="text-white text-lg">Loading SecureDevOps Platform...</p>
        </div>
      </div>
    );
  }

  // Show authentication modal if not authenticated, but allow certain routes to be handled by their own components
  if (!isAuthenticated) {
    return (
      <AuthRoutingHandler
        authModalOpen={authModalOpen}
        setAuthModalOpen={setAuthModalOpen}
      />
    );
  }

  const navigation = [
    // Primary Navigation
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: HomeIcon,
      gradient: "from-blue-500 to-cyan-500",
      category: "main",
    },
    {
      name: "Projects",
      href: "/projects",
      icon: UsersIcon,
      gradient: "from-indigo-500 to-purple-500",
      category: "main",
    },
    {
      name: "Reports",
      href: "/reports",
      icon: DocumentReportIcon,
      gradient: "from-purple-500 to-pink-500",
      category: "main",
    },
    {
      name: "Analytics",
      href: "/analytics",
      icon: ChartBarIcon,
      gradient: "from-green-500 to-emerald-500",
      category: "main",
    },
    // Enterprise Features
    {
      name: "User Management",
      href: "/users",
      icon: UserCircleIcon,
      gradient: "from-teal-500 to-blue-500",
      category: "enterprise",
    },
    {
      name: "Audit Logs",
      href: "/audit-logs",
      icon: ClockIcon,
      gradient: "from-amber-500 to-orange-500",
      category: "enterprise",
    },
    {
      name: "Data Retention",
      href: "/retention-policies",
      icon: ArchiveBoxIcon,
      gradient: "from-rose-500 to-pink-500",
      category: "enterprise",
    },
    {
      name: "Compliance",
      href: "/compliance",
      icon: BuildingOfficeIcon,
      gradient: "from-cyan-500 to-blue-500",
      category: "enterprise",
    },
    // Settings
    {
      name: "Settings",
      href: "/settings",
      icon: CogIcon,
      gradient: "from-gray-500 to-gray-600",
      category: "settings",
    },
  ];

  // Modern Sidebar with Glassmorphism
  const ModernSidebar = () => (
    <div className="fixed inset-y-0 left-0 z-40 w-72 transform bg-gray-900/95 backdrop-blur-xl border-r border-gray-800/50 translate-x-0">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-purple-500/5 to-pink-500/5" />

      <div className="relative flex flex-col h-full">
        {/* Brand Header */}
        <div className="flex items-center px-6 py-8">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
              <ShieldCheckSolid className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                SecureDevOps AI
              </h1>
              <p className="text-xs text-gray-400">
                Advanced Security Platform
              </p>
            </div>
          </div>
        </div>

        {/* Enhanced Quick Scan Button */}
        <div className="px-6 mb-8">
          <button
            onClick={() => setScanModalOpen(true)}
            className="relative w-full p-4 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-2xl flex items-center justify-center space-x-2 group overflow-hidden transform hover:scale-105"
          >
            {/* Animated background */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-700 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Shimmer effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />

            <div className="relative flex items-center space-x-2">
              <PlusIcon className="h-5 w-5 group-hover:rotate-90 transition-all duration-300" />
              <span className="font-semibold">Start New Scan</span>
              <ArrowPathIcon className="h-4 w-4 opacity-0 group-hover:opacity-100 group-hover:animate-spin transition-all" />
            </div>
          </button>
        </div>

        {/* Navigation - Grouped */}
        <nav className="flex-1 px-6 overflow-y-auto">
          {/* Main Navigation */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
              Main
            </p>
            <div className="space-y-1">
              {navigation
                .filter((item) => item.category === "main")
                .map((item) => {
                  const isActive =
                    location.pathname === item.href ||
                    (item.href === "/dashboard" &&
                      location.pathname === "/dashboard") ||
                    (item.href !== "/dashboard" &&
                      location.pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-3 py-3 rounded-xl transition-all group ${
                        isActive
                          ? "bg-gray-800/50 text-white shadow-lg border border-gray-700/30"
                          : "text-gray-400 hover:text-white hover:bg-gray-800/30"
                      }`}
                    >
                      <div
                        className={`p-2 rounded-xl bg-gradient-to-r ${
                          item.gradient
                        } ${
                          isActive
                            ? "shadow-lg"
                            : "opacity-60 group-hover:opacity-100"
                        }`}
                      >
                        <item.icon className="h-4 w-4 text-white" />
                      </div>
                      <span className="ml-3 font-medium text-sm">
                        {item.name}
                      </span>
                      {isActive && (
                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-600" />
                      )}
                    </Link>
                  );
                })}
            </div>
          </div>

          {/* Enterprise Features */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
              Enterprise
            </p>
            <div className="space-y-1">
              {navigation
                .filter((item) => item.category === "enterprise")
                .map((item) => {
                  const isActive =
                    location.pathname === item.href ||
                    (item.href !== "/" &&
                      location.pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-3 py-3 rounded-xl transition-all group ${
                        isActive
                          ? "bg-gray-800/50 text-white shadow-lg border border-gray-700/30"
                          : "text-gray-400 hover:text-white hover:bg-gray-800/30"
                      }`}
                    >
                      <div
                        className={`p-2 rounded-xl bg-gradient-to-r ${
                          item.gradient
                        } ${
                          isActive
                            ? "shadow-lg"
                            : "opacity-60 group-hover:opacity-100"
                        }`}
                      >
                        <item.icon className="h-4 w-4 text-white" />
                      </div>
                      <span className="ml-3 font-medium text-sm">
                        {item.name}
                      </span>
                      {isActive && (
                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-600" />
                      )}
                    </Link>
                  );
                })}
            </div>
          </div>

          {/* Settings */}
          <div className="mb-6">
            <div className="space-y-1">
              {navigation
                .filter((item) => item.category === "settings")
                .map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`flex items-center px-3 py-3 rounded-xl transition-all group ${
                        isActive
                          ? "bg-gray-800/50 text-white shadow-lg border border-gray-700/30"
                          : "text-gray-400 hover:text-white hover:bg-gray-800/30"
                      }`}
                    >
                      <div
                        className={`p-2 rounded-xl bg-gradient-to-r ${
                          item.gradient
                        } ${
                          isActive
                            ? "shadow-lg"
                            : "opacity-60 group-hover:opacity-100"
                        }`}
                      >
                        <item.icon className="h-4 w-4 text-white" />
                      </div>
                      <span className="ml-3 font-medium text-sm">
                        {item.name}
                      </span>
                      {isActive && (
                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-600" />
                      )}
                    </Link>
                  );
                })}
            </div>
          </div>
        </nav>

        {/* Enhanced Connection Status */}
        <div className="p-6 border-t border-gray-800/50">
          <div
            className={`relative flex items-center p-4 rounded-2xl transition-all duration-500 ${
              isConnected
                ? "bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30"
                : "bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30"
            }`}
          >
            {/* Animated background glow */}
            <div
              className={`absolute inset-0 rounded-2xl blur-xl transition-all ${
                isConnected ? "bg-green-500/20 animate-glow" : "bg-red-500/20"
              }`}
            />

            <div className="relative flex items-center">
              <div className="relative mr-3">
                <div
                  className={`h-3 w-3 rounded-full ${
                    isConnected ? "bg-green-400" : "bg-red-400"
                  } animate-pulse`}
                />
                {isConnected && (
                  <div className="absolute inset-0 h-3 w-3 rounded-full bg-green-400 animate-ping" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-white flex items-center">
                  {isConnected ? (
                    <>
                      <span>Real-time Active</span>
                      <CheckCircleIcon className="h-4 w-4 text-green-400 ml-1" />
                    </>
                  ) : (
                    <>
                      <span>Disconnected</span>
                      <ArrowPathIcon className="h-4 w-4 text-red-400 ml-1 animate-spin" />
                    </>
                  )}
                </p>
                <p className="text-xs text-gray-400">
                  {isConnected
                    ? "Live monitoring & notifications"
                    : "Attempting to reconnect..."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Modern Header with Glassmorphism
  const ModernHeader = () => {
    const { resendVerificationEmail } = useAuth();

    return (
      <div className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50">
        {/* Email Verification Banner */}
        {user && !user.is_email_verified && (
          <div className="bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 text-center">
            <p className="text-white text-sm font-medium">
              Please verify your email address to access all features.{" "}
              <button
                onClick={async () => {
                  try {
                    await resendVerificationEmail();
                  } catch (error) {
                    // Error already handled in the function
                  }
                }}
                className="underline hover:no-underline font-semibold"
              >
                Resend verification email
              </button>
            </p>
          </div>
        )}

        <div className="flex h-16 lg:h-20 items-center justify-between px-4 lg:px-8">
          {/* Mobile menu button */}
          <button
            type="button"
            className="lg:hidden p-3 rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
            onClick={() => setSidebarOpen(true)}
          >
            <MenuIcon className="h-6 w-6" />
          </button>

          {/* Enhanced Search Bar */}
          <div className="flex-1 max-w-lg mx-4 lg:mx-8 hidden sm:block">
            <div className="relative group">
              <MagnifyingGlassIcon className="absolute left-3 lg:left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 lg:h-5 lg:w-5 text-gray-400 group-focus-within:text-blue-400 transition-colors" />
              <input
                type="text"
                placeholder="Search repositories, scans, vulnerabilities..."
                className="w-full pl-10 lg:pl-12 pr-3 lg:pr-4 py-2 lg:py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl lg:rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-gray-800/70 transition-all hover:bg-gray-800/60 text-sm lg:text-base"
              />
              <div className="absolute inset-0 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500/0 via-purple-500/0 to-pink-500/0 group-focus-within:from-blue-500/10 group-focus-within:via-purple-500/5 group-focus-within:to-pink-500/10 transition-all pointer-events-none" />
            </div>
          </div>

          {/* Enhanced Right side actions */}
          <div className="flex items-center space-x-2 lg:space-x-4">
            {/* Mobile search button */}
            <button className="sm:hidden p-2 lg:p-3 rounded-xl lg:rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all">
              <MagnifyingGlassIcon className="h-5 w-5 lg:h-6 lg:w-6" />
            </button>

            {/* Enhanced Notifications */}
            <div className="relative group notification-panel">
              <button
                onClick={() => setNotificationPanelOpen(!notificationPanelOpen)}
                className="relative p-2 lg:p-3 rounded-xl lg:rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all group-hover:scale-105"
              >
                <BellIcon className="h-5 w-5 lg:h-6 lg:w-6" />
                {notifications.length > 0 && (
                  <span className="absolute -top-1 -right-1 h-4 w-4 lg:h-5 lg:w-5 bg-gradient-to-r from-red-500 to-pink-500 rounded-full text-xs text-white flex items-center justify-center animate-pulse shadow-lg">
                    {notifications.length > 9 ? "9+" : notifications.length}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {notificationPanelOpen && (
                <div className="absolute right-0 top-full mt-2 w-80 bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50">
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">
                        Notifications
                      </h3>
                      {notifications.length > 0 && (
                        <button
                          onClick={() => setNotifications([])}
                          className="text-sm text-gray-400 hover:text-white transition-colors"
                        >
                          Clear All
                        </button>
                      )}
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="text-center py-8">
                          <BellIcon className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                          <p className="text-gray-400">No notifications</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {notifications.map((notification) => (
                            <div
                              key={notification.id}
                              className="p-3 rounded-xl bg-gray-700/50 border border-gray-600/30 hover:bg-gray-700/70 transition-colors"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    {notification.type === "scan_started" && (
                                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                    )}
                                    {notification.type === "scan_update" && (
                                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                                    )}
                                    {notification.type === "scan_error" && (
                                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                                    )}
                                    {notification.type === "scan_completed" && (
                                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                    )}
                                    {notification.type === "system" && (
                                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                                    )}
                                    <p className="text-sm font-medium text-white truncate">
                                      {notification.data?.project_name ||
                                        notification.data?.projectName ||
                                        (notification.type === "scan_update"
                                          ? "Scan Update"
                                          : notification.type === "scan_started"
                                          ? "Scan Started"
                                          : notification.type ===
                                            "scan_completed"
                                          ? "Scan Completed"
                                          : notification.type === "scan_error"
                                          ? "Scan Error"
                                          : "System Notification")}
                                    </p>
                                  </div>
                                  <p className="text-sm text-gray-300">
                                    {notification.message || "Notification"}
                                  </p>
                                  <p className="text-xs text-gray-500 mt-1">
                                    {notification.timestamp instanceof Date
                                      ? notification.timestamp.toLocaleString()
                                      : new Date(
                                          notification.timestamp
                                        ).toLocaleString()}
                                  </p>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setNotifications((prev) =>
                                      prev.filter(
                                        (n) => n.id !== notification.id
                                      )
                                    );
                                  }}
                                  className="text-gray-500 hover:text-gray-300 transition-colors"
                                >
                                  <svg
                                    className="w-4 h-4"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth="2"
                                      d="M6 18L18 6M6 6l12 12"
                                    ></path>
                                  </svg>
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Tooltip */}
              <div className="absolute -bottom-12 left-1/2 transform -translate-x-1/2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none">
                {notifications.length} notifications
              </div>
            </div>

            {/* User Profile */}
            <button
              onClick={() => setProfileModalOpen(true)}
              className="flex items-center space-x-2 lg:space-x-3 p-2 rounded-xl lg:rounded-2xl hover:bg-gray-800/50 transition-all"
            >
              <div className="h-8 w-8 lg:h-10 lg:w-10 rounded-xl lg:rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center overflow-hidden">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt="Avatar"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <UserCircleIcon className="h-5 w-5 lg:h-6 lg:w-6 text-white" />
                )}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-white">
                  {user?.full_name || user?.username || "User"}
                </p>
                <span className="inline-block px-2 py-0.5 text-xs bg-blue-500/20 text-blue-300 rounded-lg capitalize">
                  {user?.role || "viewer"}
                </span>
              </div>
            </button>

            {/* Logout Button */}
            <button
              onClick={logout}
              className="p-2 lg:p-3 rounded-xl lg:rounded-2xl text-gray-400 hover:text-white hover:bg-red-500/20 transition-all group"
              title="Logout"
            >
              <svg
                className="h-5 w-5 lg:h-6 lg:w-6 group-hover:text-red-400 transition-colors"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Enhanced Modern Dashboard
  const ModernDashboard = ({ notifications }) => {
    const { data: analytics, isLoading: analyticsLoading } = useQuery({
      queryKey: ["analytics"],
      queryFn: () => reportsAPI.getAnalyticsOverview(30),
    });

    const { data: reportsData } = useQuery({
      queryKey: ["reports", { limit: 100 }],
      queryFn: () => reportsAPI.getReports({ limit: 100 }),
    });

    // Calculate correct metrics from API response
    const uniqueProjects = analytics?.top_projects?.length || 0;
    const totalScans = analytics?.scan_summary?.total_scans || 0;
    const criticalIssues = analytics?.vulnerability_summary?.critical || 0;
    const highIssues = analytics?.vulnerability_summary?.high || 0;

    // Calculate security score based on findings (inverse of vulnerability density)
    const totalFindings =
      (analytics?.vulnerability_summary?.critical || 0) * 10 +
      (analytics?.vulnerability_summary?.high || 0) * 5 +
      (analytics?.vulnerability_summary?.medium || 0) * 2 +
      (analytics?.vulnerability_summary?.low || 0);
    const avgSecurityScore =
      totalScans > 0
        ? Math.max(
            0,
            Math.min(100, 100 - Math.min(totalFindings / totalScans, 100))
          )
        : 100;

    // Scans from reports data
    const scansToday =
      reportsData?.reports?.filter((r) => {
        const today = new Date();
        const scanDate = new Date(r.created_at);
        return scanDate.toDateString() === today.toDateString();
      }).length || 0;

    const stats = [
      {
        title: "Active Projects",
        value: analyticsLoading ? "..." : uniqueProjects.toString(),
        change: `${totalScans} scans`,
        icon: DocumentReportIcon,
        gradient: "from-blue-500 to-cyan-500",
        bgGradient: "from-blue-500/10 to-cyan-500/10",
      },
      {
        title: "Critical Issues",
        value: analyticsLoading ? "..." : criticalIssues.toString(),
        change: `${highIssues} high`,
        icon: ExclamationTriangleIcon,
        gradient: "from-red-500 to-pink-500",
        bgGradient: "from-red-500/10 to-pink-500/10",
      },
      {
        title: "Security Score",
        value: analyticsLoading ? "..." : `${Math.round(avgSecurityScore)}/100`,
        change:
          avgSecurityScore >= 80
            ? "Good"
            : avgSecurityScore >= 50
            ? "Fair"
            : "Needs Work",
        icon: ShieldCheckIcon,
        gradient: "from-green-500 to-emerald-500",
        bgGradient: "from-green-500/10 to-emerald-500/10",
      },
      {
        title: "Scans Today",
        value: analyticsLoading ? "..." : scansToday.toString(),
        change: "24h",
        icon: BoltIcon,
        gradient: "from-purple-500 to-violet-500",
        bgGradient: "from-purple-500/10 to-violet-500/10",
      },
    ];

    return (
      <PageContainer>
        {/* Page Header */}
        <PageHeader
          title="Dashboard"
          description="AI-powered security insights and vulnerability management"
          icon={HomeIcon}
          breadcrumb={["Dashboard"]}
          actions={
            <button
              onClick={() => setScanModalOpen(true)}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all flex items-center gap-2 shadow-lg"
            >
              <PlusIcon className="h-4 w-4" />
              <span>New Scan</span>
            </button>
          }
        />

        {/* Stats Grid */}
        <div className="mb-8 lg:mb-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            {stats.map((stat, index) => (
              <div
                key={stat.title}
                className="relative group cursor-pointer animate-fade-in-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-gray-800/30 to-gray-700/30 rounded-2xl lg:rounded-3xl blur-xl group-hover:blur-2xl group-hover:scale-105 transition-all duration-300" />
                <div
                  className={`relative p-4 sm:p-6 rounded-2xl lg:rounded-3xl border border-gray-800/50 bg-gradient-to-br ${stat.bgGradient} backdrop-blur-xl hover:border-gray-700/50 hover:scale-105 transition-all duration-300`}
                >
                  <div className="flex items-center justify-between mb-3 lg:mb-4">
                    <div
                      className={`p-2 lg:p-3 rounded-xl lg:rounded-2xl bg-gradient-to-r ${stat.gradient} shadow-lg group-hover:shadow-xl transition-all`}
                    >
                      <stat.icon className="h-4 w-4 lg:h-6 lg:w-6 text-white" />
                    </div>
                    <span
                      className={`text-xs lg:text-sm font-medium ${
                        stat.change.startsWith("+")
                          ? "text-green-400"
                          : stat.change.startsWith("-")
                          ? "text-red-400"
                          : "text-gray-400"
                      }`}
                    >
                      {stat.change}
                    </span>
                  </div>
                  <h3 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white mb-2">
                    {stat.value}
                  </h3>
                  <p className="text-gray-400 font-medium text-xs lg:text-sm">
                    {stat.title}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

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
                notifications.slice(0, 5).map((notification) => (
                  <div
                    key={notification.id}
                    className="flex items-center space-x-3 lg:space-x-4 p-3 lg:p-4 rounded-xl lg:rounded-2xl bg-gray-800/30 hover:bg-gray-800/50 transition-all"
                  >
                    <div className="p-1.5 lg:p-2 rounded-lg lg:rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 flex-shrink-0">
                      <CheckCircleIcon className="h-3.5 w-3.5 lg:h-4 lg:w-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs lg:text-sm font-medium text-white truncate">
                        {notification.data?.project_name || "Unknown Project"}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {notification.message}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {notification.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
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

  // AppContent Return
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        >
          <div
            className="fixed inset-y-0 left-0 w-80 max-w-[85vw] bg-gray-900/95 backdrop-blur-xl border-r border-gray-800/50 overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-800/50">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600">
                  <ShieldCheckSolid className="h-5 w-5 text-white" />
                </div>
                <span className="text-base font-bold text-white">
                  SecureDevOps AI
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
              >
                <XIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Mobile Quick Scan Button */}
            <div className="p-4 border-b border-gray-800/50">
              <button
                onClick={() => {
                  setScanModalOpen(true);
                  setSidebarOpen(false);
                }}
                className="w-full p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg flex items-center justify-center space-x-2"
              >
                <PlusIcon className="h-4 w-4" />
                <span className="text-sm">Start New Scan</span>
              </button>
            </div>

            <nav className="px-4 py-4">
              {/* Main Navigation */}
              <div className="mb-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-3">
                  Main
                </p>
                <div className="space-y-1">
                  {navigation
                    .filter((item) => item.category === "main")
                    .map((item) => {
                      const isActive =
                        location.pathname === item.href ||
                        (item.href === "/dashboard" &&
                          location.pathname === "/dashboard") ||
                        (item.href !== "/dashboard" &&
                          location.pathname.startsWith(item.href));
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          onClick={() => setSidebarOpen(false)}
                          className={`flex items-center px-3 py-2.5 rounded-xl transition-all ${
                            isActive
                              ? "bg-gray-800/50 text-white border border-blue-500/20"
                              : "text-gray-300 hover:text-white hover:bg-gray-800/50"
                          }`}
                        >
                          <div
                            className={`p-2 rounded-lg bg-gradient-to-r ${item.gradient} mr-3 flex-shrink-0`}
                          >
                            <item.icon className="h-4 w-4 text-white" />
                          </div>
                          <span className="font-medium text-sm">
                            {item.name}
                          </span>
                        </Link>
                      );
                    })}
                </div>
              </div>

              {/* Enterprise Features */}
              <div className="mb-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-3">
                  Enterprise
                </p>
                <div className="space-y-1">
                  {navigation
                    .filter((item) => item.category === "enterprise")
                    .map((item) => {
                      const isActive =
                        location.pathname === item.href ||
                        location.pathname.startsWith(item.href);
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          onClick={() => setSidebarOpen(false)}
                          className={`flex items-center px-3 py-2.5 rounded-xl transition-all ${
                            isActive
                              ? "bg-gray-800/50 text-white border border-blue-500/20"
                              : "text-gray-300 hover:text-white hover:bg-gray-800/50"
                          }`}
                        >
                          <div
                            className={`p-2 rounded-lg bg-gradient-to-r ${item.gradient} mr-3 flex-shrink-0`}
                          >
                            <item.icon className="h-4 w-4 text-white" />
                          </div>
                          <span className="font-medium text-sm">
                            {item.name}
                          </span>
                        </Link>
                      );
                    })}
                </div>
              </div>

              {/* Settings */}
              <div className="space-y-1">
                {navigation
                  .filter((item) => item.category === "settings")
                  .map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center px-3 py-2.5 rounded-xl transition-all ${
                          isActive
                            ? "bg-gray-800/50 text-white border border-blue-500/20"
                            : "text-gray-300 hover:text-white hover:bg-gray-800/50"
                        }`}
                      >
                        <div
                          className={`p-2 rounded-lg bg-gradient-to-r ${item.gradient} mr-3 flex-shrink-0`}
                        >
                          <item.icon className="h-4 w-4 text-white" />
                        </div>
                        <span className="font-medium text-sm">{item.name}</span>
                      </Link>
                    );
                  })}
              </div>
            </nav>
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <ModernSidebar />
      </div>

      {/* Main Content */}
      <div className="lg:pl-72">
        <ModernHeader />

        <main className="relative min-h-screen">
          <Routes>
            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={<ModernDashboard notifications={notifications} />}
            />
            <Route path="/projects" element={<ProjectManagement />} />
            <Route path="/project/:projectId" element={<ProjectDetails />} />
            <Route path="/users" element={<UserManagement />} />
            <Route path="/audit-logs" element={<AuditLogs />} />
            <Route
              path="/retention-policies"
              element={<DataRetentionPolicies />}
            />
            <Route path="/compliance" element={<AdvancedCompliance />} />
            <Route path="/reports" element={<Reports />} />
            <Route
              path="/report/:reportId"
              element={<EnhancedReportDetails />}
            />
            <Route
              path="/compliance/:reportId"
              element={<ComplianceReport />}
            />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
            <Route
              path="/verify-email"
              element={
                <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                  <EmailVerificationPage />
                </div>
              }
            />
            <Route
              path="/reset-password"
              element={
                <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                  <PasswordResetPage />
                </div>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>

      {/* Scan Modal */}
      <ScanModal
        isOpen={scanModalOpen}
        onClose={() => setScanModalOpen(false)}
        onSubmit={scanMutation.mutateAsync}
      />

      {/* Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />

      {/* User Profile Modal */}
      {profileModalOpen && (
        <UserProfile onClose={() => setProfileModalOpen(false)} />
      )}
    </div>
  );
}

// Main App function that provides QueryClient context
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
      {/* Enhanced Toast Notifications - Must be outside providers to work globally */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        containerClassName=""
        containerStyle={{
          zIndex: 9999,
        }}
        toastOptions={{
          duration: 4000,
          style: {
            background:
              "linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(31, 41, 55, 0.95) 100%)",
            color: "#fff",
            border: "1px solid rgba(75, 85, 99, 0.3)",
            borderRadius: "1rem",
            backdropFilter: "blur(16px)",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            maxWidth: "500px",
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: "#10b981",
              secondary: "#fff",
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: "#ef4444",
              secondary: "#fff",
            },
          },
          loading: {
            duration: Infinity,
            iconTheme: {
              primary: "#3b82f6",
              secondary: "#fff",
            },
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
