/**
 * Main Layout Component
 * Wraps authenticated pages with sidebar, header, footer and main content area
 */
import React, { useState, useEffect } from "react";
import { Outlet, Routes, Route, Navigate } from "react-router-dom";
import toast from "react-hot-toast";
import Sidebar, { MobileMenuButton } from "./Sidebar";
import Header from "./Header";
import Footer from "./Footer";
import { useAuth } from "../components/auth";
import { UserProfile } from "../components/auth/UserProfile";
import { websocketService } from "../services/api";

// Import Pages
import Dashboard from "../pages/Dashboard";
import { Analytics, Reports, NotFound } from "../pages";
import { ProjectManagement, ProjectDetails } from "../components/projects";
import { EnhancedReportDetails, ComplianceReport } from "../components/reports";
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
      if (projectName && scanStatus) {
        notificationMessage = `${scanType.toUpperCase()} scan ${scanStatus} for ${projectName}`;
      } else if (customMessage) {
        notificationMessage = customMessage;
        if (progress !== undefined) {
          notificationMessage += ` (${progress}%)`;
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
        toast.success(`✅ Scan completed for ${projectName}`);
      } else if (scanStatus === "failed" && projectName) {
        toast.error(`❌ Scan failed for ${projectName}`);
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

        <main className="flex-1 relative overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={<Dashboard notifications={notifications} />}
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
