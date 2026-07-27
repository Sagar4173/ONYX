/**
 * Main Layout Component
 * Wraps authenticated pages with sidebar, header, footer and main content area
 */
import { useState, useEffect, lazy, Suspense } from "react";
import { Routes, Route, Navigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { PageTransition } from "../components/ui/StyleComponents";
import ErrorBoundary from "../components/common/ErrorBoundary";

// Redirect component for /compliance/:reportId to /report/:reportId
const ComplianceRedirect = () => {
  const { reportId } = useParams();
  return <Navigate to={`/report/${reportId}`} replace />;
};
import toast from "react-hot-toast";
import Sidebar from "./Sidebar";
import Header from "./Header";
import Footer from "./Footer";
import { useAuth, VerificationBanner, AdminRoute } from "../components/auth";
import { UserProfile } from "../components/auth/UserProfile";
import { CommandPalette } from "../components/common";
import { websocketService } from "../services/api";

// Lazy-loaded page components
const Dashboard = lazy(() => import("../pages/Dashboard"));
const Analytics = lazy(() => import("../pages/Analytics"));
const Reports = lazy(() => import("../pages/Reports"));
const NotFound = lazy(() => import("../pages/NotFound"));
const AdminDashboard = lazy(() => import("../pages/AdminDashboard"));
const ProjectManagement = lazy(() => import("../components/projects/ProjectManagement"));
const ProjectDetails = lazy(() => import("../components/projects/ProjectDetails"));
const ReportDetails = lazy(() => import("../components/reports/ReportDetails"));
const AdvancedCompliance = lazy(() => import("../components/compliance/AdvancedCompliance"));
const DataRetentionPolicies = lazy(() => import("../components/compliance/DataRetentionPolicies"));
const UserManagement = lazy(() => import("../components/users/UserManagement"));
const AuditLogs = lazy(() => import("../components/users/AuditLogs"));
const Settings = lazy(() => import("../components/settings/Settings"));
const ScheduledScansPage = lazy(() => import("../components/schedules/ScheduledScansPage"));
const SecretHistoryPanel = lazy(() => import("../components/security/SecretHistoryPanel"));

/**
 * Main Layout with Sidebar and Header
 */
export const MainLayout = () => {
  const { user: _user, isAuthenticated: _isAuthenticated } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Global keyboard shortcut for command palette
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    // Add a small delay to let the backend fully start up
    const timeoutId = setTimeout(() => {
      websocketService.connect();
    }, 1000);

    websocketService.on("connected", (connected) => {
      setIsConnected(connected);
      if (connected && isConnected === false) {
        toast.success("🔗 Real-time connection restored");
      }
    });

    websocketService.on("disconnected", () => {
      setIsConnected(false);
      if (isConnected) {
        toast.error("🔴 Connection lost");
      }
    });

    websocketService.on("scan_update", (data) => {
      const scanData = data.data || data;
      const projectName = scanData.project_name || scanData.projectName;
      const scanStatus = scanData.status;
      const scanType = scanData.scan_type || scanData.type || "security";
      const progress = scanData.progress;
      const customMessage = scanData.message;

      // Build notification message
      let notificationMessage;
      if (customMessage) {
        notificationMessage = customMessage;
      } else if (projectName && scanStatus) {
        if (scanStatus === "started") {
          notificationMessage = `🔍 Scan started for ${projectName}`;
        } else if (scanStatus === "running") {
          notificationMessage = `⏳ Scanning ${projectName}... ${progress || 0}%`;
        } else if (scanStatus === "completed") {
          const findings = scanData.total_findings || 0;
          notificationMessage = `✅ Scan completed for ${projectName} - ${findings} findings`;
        } else if (scanStatus === "failed") {
          notificationMessage = `❌ Scan failed for ${projectName}`;
        } else {
          notificationMessage = `${scanType.toUpperCase()} scan ${scanStatus} for ${projectName}`;
        }
      } else if (progress !== undefined) {
        notificationMessage = `Scan in progress: ${progress}%`;
      } else {
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
        ...prev.slice(0, 19),
      ]);

      // Toast for important updates
      if (scanStatus === "completed" && projectName) {
        const critical = scanData.findings_by_severity?.critical || 0;
        const high = scanData.findings_by_severity?.high || 0;
        if (critical > 0) {
          toast.error(`🚨 ${critical} CRITICAL issues found in ${projectName}!`, {
            duration: 6000,
          });
        } else if (high > 0) {
          toast.warning(`⚠️ ${high} high severity issues in ${projectName}`, {
            duration: 5000,
          });
        } else {
          toast.success(`✅ Scan completed for ${projectName}`);
        }
      } else if (scanStatus === "failed" && projectName) {
        toast.error(`❌ Scan failed for ${projectName}`);
      } else if (scanStatus === "started" && projectName) {
        toast(`🔍 Security scan started for ${projectName}`, { icon: "🔍" });
      }
    });

    // Handle security alerts (critical vulnerabilities, new logins, etc.)
    websocketService.on("security_alert", (data) => {
      const alertData = data.data || data;
      const alertType = alertData.alert_type;
      const severity = alertData.severity;
      const message = alertData.message;

      setNotifications((prev) => [
        {
          id: Date.now(),
          type: "security_alert",
          message: message,
          timestamp: new Date(),
          data: alertData,
          severity: severity,
        },
        ...prev.slice(0, 19),
      ]);

      // Show toast based on alert type
      if (alertType === "vulnerability" && (severity === "critical" || severity === "high")) {
        toast.error(`🚨 ${message}`, { duration: 8000 });
      } else if (alertType === "new_login") {
        toast(`🔐 ${message}`, { duration: 5000 });
      } else {
        toast(message, { icon: "⚠️" });
      }
    });

    return () => {
      clearTimeout(timeoutId);
      websocketService.disconnect();
    };
  }, [isConnected]);

  // Notification handlers
  const handleClearNotifications = () => {
    setNotifications([]);
  };

  const handleDismissNotification = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-slate-950 flex"
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[60] focus:px-4 focus:py-2 focus:bg-gray-900 focus:text-cyan-400 focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Skip to content
      </a>
      {/* Sidebar - Handles both mobile and desktop */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={sidebarOpen}
        onMobileClose={() => setSidebarOpen(false)}
      />

      {/* Main Content - Adjusts for sidebar width */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${
          sidebarCollapsed ? "lg:ml-[80px]" : "lg:ml-[280px]"
        }`}
      >
        <Header
          onMenuClick={() => setSidebarOpen(true)}
          notifications={notifications}
          onClearNotifications={handleClearNotifications}
          onDismissNotification={handleDismissNotification}
          onProfileClick={() => setProfileModalOpen(true)}
          onCommandPaletteOpen={() => setCommandPaletteOpen(true)}
        />

        {/* Email Verification Banner for unverified users */}
        <VerificationBanner />

        <main id="main-content" className="flex-1 relative overflow-auto">
          <Suspense
            fallback={
              <div className="animate-pulse space-y-6 p-6">
                <div className="h-8 w-64 bg-gray-700 rounded-lg" />
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="h-28 bg-gray-700/50 rounded-xl" />
                  <div className="h-28 bg-gray-700/50 rounded-xl" />
                  <div className="h-28 bg-gray-700/50 rounded-xl" />
                  <div className="h-28 bg-gray-700/50 rounded-xl" />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="h-64 bg-gray-700/50 rounded-xl" />
                  <div className="h-64 bg-gray-700/50 rounded-xl" />
                  <div className="h-64 bg-gray-700/50 rounded-xl" />
                </div>
              </div>
            }
          >
            <PageTransition>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route
                  path="/dashboard"
                  element={
                    <ErrorBoundary>
                      <Dashboard notifications={notifications} />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/projects"
                  element={
                    <ErrorBoundary>
                      <ProjectManagement />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/project/:projectId"
                  element={
                    <ErrorBoundary>
                      <ProjectDetails />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/users"
                  element={
                    <ErrorBoundary>
                      <AdminRoute>
                        <UserManagement />
                      </AdminRoute>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/audit-logs"
                  element={
                    <ErrorBoundary>
                      <AdminRoute>
                        <AuditLogs />
                      </AdminRoute>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/retention-policies"
                  element={
                    <ErrorBoundary>
                      <AdminRoute>
                        <DataRetentionPolicies />
                      </AdminRoute>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/compliance"
                  element={
                    <ErrorBoundary>
                      <AdvancedCompliance />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ErrorBoundary>
                      <Reports />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/report/:reportId"
                  element={
                    <ErrorBoundary>
                      <ReportDetails />
                    </ErrorBoundary>
                  }
                />
                {/* Redirect /compliance/:reportId to unified /report/:reportId */}
                <Route path="/compliance/:reportId" element={<ComplianceRedirect />} />
                <Route
                  path="/analytics"
                  element={
                    <ErrorBoundary>
                      <Analytics />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/admin"
                  element={
                    <ErrorBoundary>
                      <AdminRoute>
                        <AdminDashboard />
                      </AdminRoute>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/scheduled-scans"
                  element={
                    <ErrorBoundary>
                      <ScheduledScansPage />
                    </ErrorBoundary>
                  }
                />
                  <Route
                  path="/secret-history"
                  element={
                    <ErrorBoundary>
                      <SecretHistoryPanel />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <ErrorBoundary>
                      <Settings />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="*"
                  element={
                    <ErrorBoundary>
                      <NotFound />
                    </ErrorBoundary>
                  }
                />
              </Routes>
            </PageTransition>
          </Suspense>
        </main>

        {/* Footer */}
        <Footer />
      </div>

      {/* User Profile Modal */}
      {profileModalOpen && <UserProfile onClose={() => setProfileModalOpen(false)} />}

      {/* Command Palette */}
      <CommandPalette isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />
    </motion.div>
  );
};

export default MainLayout;
