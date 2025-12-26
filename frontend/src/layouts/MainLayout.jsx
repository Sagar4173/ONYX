/**
 * Main Layout Component
 * Wraps authenticated pages with sidebar, header, footer and main content area
 */
import React, { useState, useEffect } from "react";
import { Outlet, Routes, Route, Navigate, useParams } from "react-router-dom";

// Redirect component for /compliance/:reportId to /report/:reportId
const ComplianceRedirect = () => {
  const { reportId } = useParams();
  return <Navigate to={`/report/${reportId}`} replace />;
};
import toast from "react-hot-toast";
import Sidebar, { MobileMenuButton } from "./Sidebar";
import Header from "./Header";
import Footer from "./Footer";
import { useAuth, VerificationBanner, AdminRoute } from "../components/auth";
import { UserProfile } from "../components/auth/UserProfile";
import { websocketService } from "../services/api";

// Import Pages
import Dashboard from "../pages/Dashboard";
import { Analytics, Reports, NotFound, AdminDashboard } from "../pages";
import { ProjectManagement, ProjectDetails } from "../components/projects";
import { EnhancedReportDetails } from "../components/reports";
import {
  AdvancedCompliance,
  DataRetentionPolicies,
} from "../components/compliance";
import { UserManagement, AuditLogs } from "../components/users";
import { Settings } from "../components/settings";

/**
 * Main Layout with Sidebar and Header
 */
export const MainLayout = () => {
  const { user, isAuthenticated } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [profileModalOpen, setProfileModalOpen] = useState(false);

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
          notificationMessage = `⏳ Scanning ${projectName}... ${
            progress || 0
          }%`;
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
        ...prev.slice(0, 9),
      ]);

      // Toast for important updates
      if (scanStatus === "completed" && projectName) {
        const critical = scanData.findings_by_severity?.critical || 0;
        const high = scanData.findings_by_severity?.high || 0;
        if (critical > 0) {
          toast.error(
            `🚨 ${critical} CRITICAL issues found in ${projectName}!`,
            { duration: 6000 }
          );
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
        toast.info(`🔍 Security scan started for ${projectName}`);
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
        ...prev.slice(0, 9),
      ]);

      // Show toast based on alert type
      if (
        alertType === "vulnerability" &&
        (severity === "critical" || severity === "high")
      ) {
        toast.error(`🚨 ${message}`, { duration: 8000 });
      } else if (alertType === "new_login") {
        toast.info(`🔐 ${message}`, { duration: 5000 });
      } else {
        toast(message, { icon: "⚠️" });
      }
    });

    return () => {
      clearTimeout(timeoutId);
      websocketService.disconnect();
    };
  }, []);

  // Notification handlers
  const handleClearNotifications = () => {
    setNotifications([]);
  };

  const handleDismissNotification = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="min-h-screen bg-slate-950 flex">
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
        />

        {/* Email Verification Banner for unverified users */}
        <VerificationBanner />

        <main className="flex-1 relative overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={<Dashboard notifications={notifications} />}
            />
            <Route path="/projects" element={<ProjectManagement />} />
            <Route path="/project/:projectId" element={<ProjectDetails />} />
            <Route
              path="/users"
              element={
                <AdminRoute>
                  <UserManagement />
                </AdminRoute>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <AdminRoute>
                  <AuditLogs />
                </AdminRoute>
              }
            />
            <Route
              path="/retention-policies"
              element={
                <AdminRoute>
                  <DataRetentionPolicies />
                </AdminRoute>
              }
            />
            <Route path="/compliance" element={<AdvancedCompliance />} />
            <Route path="/reports" element={<Reports />} />
            <Route
              path="/report/:reportId"
              element={<EnhancedReportDetails />}
            />
            {/* Redirect /compliance/:reportId to unified /report/:reportId */}
            <Route
              path="/compliance/:reportId"
              element={<ComplianceRedirect />}
            />
            <Route path="/analytics" element={<Analytics />} />
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboard />
                </AdminRoute>
              }
            />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        {/* Footer */}
        <Footer />
      </div>

      {/* User Profile Modal */}
      {profileModalOpen && (
        <UserProfile onClose={() => setProfileModalOpen(false)} />
      )}
    </div>
  );
};

export default MainLayout;
