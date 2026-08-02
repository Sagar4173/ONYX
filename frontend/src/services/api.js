/**
 * API Service Layer for ONYX Platform
 * Handles REST API calls and WebSocket connections
 */
import axios from "axios";
import toast from "react-hot-toast";

// API Configuration - Production ready with environment variable support
const API_BASE_URL = import.meta.env.DEV
  ? "http://127.0.0.1:8000/api" // Direct connection in development with /api prefix
  : import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "/api";

// WebSocket URL - Connect directly to backend in development
const WS_BASE_URL = import.meta.env.DEV
  ? "ws://127.0.0.1:8000" // Direct connection in development
  : import.meta.env.VITE_WS_URL ||
    import.meta.env.VITE_WEBSOCKET_URL ||
    (window.location.protocol === "https:" ? "wss:" : "ws:") + "//" + window.location.host;

// Utility function to clean parameters by removing empty values
const cleanParams = (params = {}) => {
  return Object.entries(params).reduce((acc, [key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      acc[key] = value;
    }
    return acc;
  }, {});
};

/**
 * Utility function to extract error message from API error response
 * Handles FastAPI/Pydantic validation errors (422) which return an array of error objects
 * @param {Error} error - Axios error object
 * @param {string} fallbackMessage - Default message if no specific error found
 * @returns {string} - Human-readable error message
 */
export const getApiErrorMessage = (error, fallbackMessage = "An error occurred") => {
  const detail = error.response?.data?.detail;

  if (Array.isArray(detail)) {
    // Handle Pydantic validation errors (422 responses)
    return detail.map((err) => err.msg || err.message || JSON.stringify(err)).join(", ");
  } else if (typeof detail === "string") {
    return detail;
  } else if (error.response?.data?.message) {
    return error.response.data.message;
  } else if (error.message) {
    return error.message;
  }

  return fallbackMessage;
};

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for auth and logging
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // Handle common error cases
    if (error.response?.status === 401) {
      // Extract error message from response
      const _errorMessage = error.response?.data?.detail || "Authentication failed";

      // Try to refresh token only if it's not a login request and we have a refresh token
      const refreshToken = localStorage.getItem("refresh_token");
      const isLoginRequest = error.config?.url?.includes("/auth/login");

      if (refreshToken && !error.config._retry && !isLoginRequest) {
        error.config._retry = true;

        try {
          const response = await api.post("/auth/refresh", {
            refresh_token: refreshToken,
          });
          const { access_token } = response.data;

          localStorage.setItem("access_token", access_token);
          error.config.headers.Authorization = `Bearer ${access_token}`;

          return api.request(error.config);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user_data");
          toast.error("Session expired. Please log in again.");
          window.location.href = "/";
        }
      } else if (isLoginRequest) {
        // For login requests, don't show generic toast, let the login handler deal with it
        // The login function will extract and show the proper error message
      } else {
        toast.error("Authentication required. Please log in.");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user_data");
      }
    } else if (error.response?.status === 403) {
      toast.error("Access denied. Insufficient permissions.");
    } else if (error.response?.status === 429) {
      toast.error("Rate limit exceeded. Please try again later.");
    } else if (error.response?.status >= 500) {
      toast.error("Server error. Please try again later.");
    } else if (error.code === "NETWORK_ERROR") {
      toast.error("Network error. Please check your connection.");
    }

    return Promise.reject(error);
  }
);

/**
 * Authentication API
 */
export const authAPI = {
  // Login user
  login: async (credentials) => {
    const response = await api.post("/auth/login", credentials);
    return response.data;
  },

  // Register user
  register: async (userData) => {
    const response = await api.post("/auth/register", userData);
    return response.data;
  },

  // Logout user
  logout: async () => {
    const response = await api.post("/auth/logout");
    return response.data;
  },

  // Refresh token
  refreshToken: async (refreshToken) => {
    const response = await api.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // Get current user profile
  getProfile: async () => {
    const response = await api.get("/auth/me");
    return response.data;
  },

  // Update user profile
  updateProfile: async (profileData) => {
    const response = await api.put("/auth/me", profileData);
    return response.data;
  },

  // Change password
  changePassword: async (passwordData) => {
    const response = await api.post("/auth/change-password", passwordData);
    return response.data;
  },

  // Request password reset
  requestPasswordReset: async (email) => {
    const response = await api.post("/auth/request-password-reset", {
      email,
    });
    return response.data;
  },

  // Confirm password reset
  confirmPasswordReset: async (resetData) => {
    const response = await api.post("/auth/reset-password", resetData);
    return response.data;
  },

  // Reset password (used by AuthContext)
  resetPassword: async (token, newPassword) => {
    const response = await api.post("/auth/reset-password", {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  // Verify email
  verifyEmail: async (token) => {
    const response = await api.post("/auth/verify-email", { token });
    return response.data;
  },

  // Resend verification email
  resendVerificationEmail: async (email) => {
    const response = await api.post("/auth/resend-verification", { email });
    return response.data;
  },

  // ===== NOTIFICATION PREFERENCES =====

  // Get notification preferences
  getNotificationPreferences: async () => {
    const response = await api.get("/auth/me/notifications");
    return response.data;
  },

  // Update notification preferences
  updateNotificationPreferences: async (preferences) => {
    const response = await api.put("/auth/me/notifications", preferences);
    return response.data;
  },

  // ===== TWO-FACTOR AUTHENTICATION =====

  // Get 2FA status
  get2FAStatus: async () => {
    const response = await api.get("/auth/me/2fa/status");
    return response.data;
  },

  // Setup 2FA (get secret and QR code)
  setup2FA: async () => {
    const response = await api.post("/auth/me/2fa/setup");
    return response.data;
  },

  // Enable 2FA after verification
  enable2FA: async (code) => {
    const response = await api.post("/auth/me/2fa/enable", { code });
    return response.data;
  },

  // Disable 2FA
  disable2FA: async (code) => {
    const response = await api.post("/auth/me/2fa/disable", { code });
    return response.data;
  },

  // ===== SESSION MANAGEMENT =====

  // Get active sessions
  getSessions: async () => {
    const response = await api.get("/auth/me/sessions");
    return response.data;
  },

  // Revoke a specific session
  revokeSession: async (sessionId) => {
    const response = await api.delete(`/auth/me/sessions/${sessionId}`);
    return response.data;
  },

  // Revoke all other sessions
  revokeAllOtherSessions: async () => {
    const response = await api.delete("/auth/me/sessions");
    return response.data;
  },

  // ===== AVATAR =====

  // Update avatar
  updateAvatar: async (avatarUrl) => {
    const response = await api.post("/auth/me/avatar", {
      avatar_url: avatarUrl,
    });
    return response.data;
  },
};

/**
 * Reports API
 */
export const reportsAPI = {
  // Get all reports with filtering and pagination
  getReports: async (params = {}) => {
    try {
      const response = await api.get("/reports", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching reports:", error);
      throw error;
    }
  },

  // Get detailed report by ID
  getReport: async (reportId) => {
    if (!reportId || reportId === "undefined" || reportId === "null") {
      throw new Error("Invalid report ID provided");
    }
    try {
      const response = await api.get(`/reports/${reportId}`);
      return response.data;
    } catch (error) {
      console.error("Error fetching report:", error);
      throw error;
    }
  },

  // Get report summary
  getReportSummary: async (reportId) => {
    try {
      const response = await api.get(`/reports/${reportId}/summary`);
      return response.data;
    } catch (error) {
      console.error("Error fetching report summary:", error);
      throw error;
    }
  },

  // Get AI analysis for a report
  getAIAnalysis: async (reportId) => {
    try {
      const response = await api.get(`/reports/${reportId}/ai-analysis`);
      return response.data;
    } catch (error) {
      // Don't throw error if AI analysis is not available - just return null
      if (error.response?.status === 404) {
        return null;
      }
      console.error("Error fetching AI analysis:", error);
      throw error;
    }
  },

  aiChat: async (scanId, message, conversationHistory = []) => {
    const response = await api.post("/ai/chat", {
      scan_id: scanId,
      message,
      conversation_history: conversationHistory.slice(-20),
    }, { timeout: 300000 });
    return response.data;
  },

  // Get analytics overview
  getAnalyticsOverview: async (daysBack = 30, projectName = null) => {
    try {
      const params = { days_back: daysBack };
      if (projectName) params.project_name = projectName;

      const response = await api.get("/analytics/overview", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching analytics:", error);
      throw error;
    }
  },

  // Get project-specific reports
  getProjectReports: async (projectName, params = {}) => {
    try {
      const response = await api.get(`/reports/project/${encodeURIComponent(projectName)}`, {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching project reports:", error);
      throw error;
    }
  },

  // Start a new scan
  startScan: async (scanData) => {
    try {
      const response = await api.post("/webhook/scan", scanData);
      return response.data;
    } catch (error) {
      console.error("❌ Error starting scan:", error);

      // Enhanced error logging for debugging
      if (error.response) {
        console.error("❌ Response data:", error.response.data);
        console.error("❌ Response status:", error.response.status);
        console.error("❌ Response headers:", error.response.headers);
      } else if (error.request) {
        console.error("❌ No response received:", error.request);
      } else {
        console.error("❌ Request setup error:", error.message);
      }

      throw error;
    }
  },

  // Get scan status by scan ID (using new dedicated endpoint)
  getScanStatus: async (scanId) => {
    try {
      const response = await api.get(`/webhook/scan/${scanId}/status`);
      return response.data;
    } catch (error) {
      console.error("❌ Error getting scan status:", error);
      // Fallback to reports if endpoint not available
      if (error.response?.status === 404) {
        const reports = await api.get("/reports/");
        const scanReport = reports.data.reports?.find((report) => report.scan_id === scanId);
        if (scanReport) {
          return {
            scan_id: scanReport.scan_id,
            status: scanReport.status,
            project_name: scanReport.project_name,
            total_findings: scanReport.total_findings,
            findings_by_severity: scanReport.findings_by_severity,
            created_at: scanReport.created_at,
            completed_at: scanReport.completed_at,
            duration_seconds: scanReport.duration_seconds,
            error_message: scanReport.error_message,
            progress: scanReport.progress || (scanReport.status === "completed" ? 100 : 0),
            current_scanner: scanReport.current_scanner || null,
          };
        }
      }
      throw error;
    }
  },

  // Stop a running scan
  stopScan: async (scanId) => {
    try {
      const response = await api.post(`/webhook/scan/${scanId}/stop`);
      return response.data;
    } catch (error) {
      console.error("❌ Error stopping scan:", error);
      throw error;
    }
  },
};

/**
 * Projects API
 */
export const projectsAPI = {
  // Get all projects with filtering and pagination
  getProjects: async (params = {}) => {
    try {
      const response = await api.get("/projects/", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching projects:", error);
      throw error;
    }
  },

  // Get project by ID
  getProject: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      console.error("Error fetching project:", error);
      throw error;
    }
  },

  // Create new project
  createProject: async (projectData) => {
    try {
      const response = await api.post("/projects/", projectData);
      return response.data;
    } catch (error) {
      console.error("Error creating project:", error);
      throw error;
    }
  },

  // Update project
  updateProject: async (projectId, projectData) => {
    try {
      const response = await api.put(`/projects/${projectId}`, projectData);
      return response.data;
    } catch (error) {
      console.error("Error updating project:", error);
      throw error;
    }
  },

  // Delete project
  deleteProject: async (projectId) => {
    try {
      const response = await api.delete(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      console.error("Error deleting project:", error);
      throw error;
    }
  },

  // Get project templates
  getProjectTemplates: async () => {
    try {
      const response = await api.get("/projects/templates");
      return response.data;
    } catch (error) {
      console.error("Error fetching project templates:", error);
      throw error;
    }
  },

  // Get project template categories
  getTemplateCategories: async () => {
    try {
      const response = await api.get("/projects/templates/categories");
      return response.data;
    } catch (error) {
      console.error("Error fetching template categories:", error);
      throw error;
    }
  },

  // Get project analytics overview
  getAnalyticsOverview: async (params = {}) => {
    try {
      const response = await api.get("/projects/analytics/overview", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching analytics overview:", error);
      throw error;
    }
  },

  // Get project analytics/stats for a specific project
  getProjectAnalytics: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}/stats`);
      return response.data;
    } catch (error) {
      console.error("Error fetching project analytics:", error);
      throw error;
    }
  },

  // Add member to project
  addMember: async (projectId, memberData) => {
    try {
      const response = await api.post(`/projects/${projectId}/members`, memberData);
      return response.data;
    } catch (error) {
      console.error("Error adding project member:", error);
      throw error;
    }
  },

  // Remove member from project
  removeMember: async (projectId, memberId) => {
    try {
      const response = await api.delete(`/projects/${projectId}/members/${memberId}`);
      return response.data;
    } catch (error) {
      console.error("Error removing project member:", error);
      throw error;
    }
  },

  // Update member role
  updateMemberRole: async (projectId, memberId, roleData) => {
    try {
      const response = await api.put(`/projects/${projectId}/members/${memberId}`, roleData);
      return response.data;
    } catch (error) {
      console.error("Error updating member role:", error);
      throw error;
    }
  },
};

/**
 * Users API
 */
export const usersAPI = {
  // Get all users with filtering and pagination
  getUsers: async (params = {}) => {
    try {
      const response = await api.get("/users", { params: cleanParams(params) });
      return response.data;
    } catch (error) {
      console.error("Error fetching users:", error);
      throw error;
    }
  },

  // Get user by ID
  getUser: async (userId) => {
    try {
      const response = await api.get(`/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error("Error fetching user:", error);
      throw error;
    }
  },

  // Create new user (admin only)
  createUser: async (userData) => {
    try {
      const response = await api.post("/users", userData);
      return response.data;
    } catch (error) {
      console.error("Error creating user:", error);
      throw error;
    }
  },

  // Update user
  updateUser: async (userId, userData) => {
    try {
      const response = await api.put(`/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      console.error("Error updating user:", error);
      throw error;
    }
  },

  // Delete user
  deleteUser: async (userId) => {
    try {
      const response = await api.delete(`/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error("Error deleting user:", error);
      throw error;
    }
  },

  // Update user status
  updateUserStatus: async (userId, status) => {
    try {
      const response = await api.patch(`/users/${userId}/status`, { status });
      return response.data;
    } catch (error) {
      console.error("Error updating user status:", error);
      throw error;
    }
  },

  // Update user role
  updateUserRole: async (userId, role) => {
    try {
      const response = await api.patch(`/users/${userId}/role`, { role });
      return response.data;
    } catch (error) {
      console.error("Error updating user role:", error);
      throw error;
    }
  },

  // Get user activity
  getUserActivity: async (userId, params = {}) => {
    try {
      const response = await api.get(`/users/${userId}/activity`, {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching user activity:", error);
      throw error;
    }
  },
};

/**
 * Admin API - Admin-only endpoints for system management
 */
export const adminAPI = {
  // Get system-wide statistics / dashboard stats
  getSystemStats: async () => {
    try {
      const response = await api.get("/admin/dashboard/stats");
      return response.data;
    } catch (error) {
      console.error("Error fetching system stats:", error);
      throw error;
    }
  },

  // Alias for getSystemStats
  getDashboardStats: async () => {
    try {
      const response = await api.get("/admin/dashboard/stats");
      return response.data;
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
      throw error;
    }
  },

  // Get all users with filtering and pagination (admin view)
  getAllUsers: async (params = {}) => {
    try {
      const response = await api.get("/admin/users/all", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching all users:", error);
      throw error;
    }
  },

  // Get all projects across all users
  getAllProjects: async (params = {}) => {
    try {
      const response = await api.get("/admin/projects/all", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching all projects:", error);
      throw error;
    }
  },

  // Get all reports across all users
  getAllReports: async (params = {}) => {
    try {
      const response = await api.get("/admin/reports/all", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching all reports:", error);
      throw error;
    }
  },

  // Get recent activity
  getRecentActivity: async (limit = 50) => {
    try {
      const response = await api.get("/admin/activity/recent", {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching recent activity:", error);
      throw error;
    }
  },

  // Get user activity logs
  getUserActivity: async (userId) => {
    try {
      const response = await api.get(`/admin/users/${userId}/activity`);
      return response.data;
    } catch (error) {
      console.error("Error fetching user activity:", error);
      throw error;
    }
  },

  // Update user role (admin only)
  updateUserRole: async (userId, role) => {
    try {
      const response = await api.put(`/admin/users/${userId}/role`, { role });
      return response.data;
    } catch (error) {
      console.error("Error updating user role:", error);
      throw error;
    }
  },

  // Update user status (admin only)
  updateUserStatus: async (userId, status) => {
    try {
      const response = await api.put(`/admin/users/${userId}/status`, {
        status,
      });
      return response.data;
    } catch (error) {
      console.error("Error updating user status:", error);
      throw error;
    }
  },

  // Delete user (admin only)
  deleteUser: async (userId) => {
    try {
      const response = await api.delete(`/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error("Error deleting user:", error);
      throw error;
    }
  },

  // Delete project (admin only)
  deleteProject: async (projectId) => {
    try {
      const response = await api.delete(`/admin/projects/${projectId}`);
      return response.data;
    } catch (error) {
      console.error("Error deleting project:", error);
      throw error;
    }
  },

  // Get system audit summary
  getAuditSummary: async (params = {}) => {
    try {
      const response = await api.get("/admin/audit-summary", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching audit summary:", error);
      throw error;
    }
  },
};

/**
 * Webhook API
 */
export const webhookAPI = {
  // Get webhook events
  getWebhookEvents: async (params = {}) => {
    try {
      // Webhook endpoints are not under /api prefix
      const backendBaseUrl = API_BASE_URL.replace("/api", "");
      const queryParams = new URLSearchParams(params).toString();
      const url = `${backendBaseUrl}/webhook/events${queryParams ? "?" + queryParams : ""}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching webhook events:", error);
      throw error;
    }
  },

  // Trigger webhook
  triggerWebhook: async (webhookData) => {
    try {
      // Webhook endpoints are not under /api prefix
      const backendBaseUrl = API_BASE_URL.replace("/api", "");
      const response = await fetch(`${backendBaseUrl}/webhook`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(webhookData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error triggering webhook:", error);
      throw error;
    }
  },
};

/**
 * System API
 */
export const systemAPI = {
  // Get system health
  getHealth: async () => {
    try {
      const response = await api.get("/health");
      return response.data;
    } catch (error) {
      console.error("Error fetching system health:", error);
      throw error;
    }
  },

  // Get scanner health
  getScannersHealth: async () => {
    try {
      const response = await api.get("/scanners/health");
      return response.data;
    } catch (error) {
      console.error("Error fetching scanner health:", error);
      throw error;
    }
  },
};

/**
 * WebSocket Service for Real-time Updates
 * Supports authenticated connections for user-specific notifications
 */
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 5000; // 5 seconds
    this.listeners = new Map();
  }

  connect() {
    try {
      // Don't create a new connection if one already exists and is connecting/open
      if (
        this.ws &&
        (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)
      ) {
        return;
      }

      // Close existing connection if it's in a bad state
      if (this.ws && this.ws.readyState === WebSocket.CLOSING) {
        this.ws = null;
      }

      // Build WebSocket URL with optional auth token
      let wsUrl = WS_BASE_URL.endsWith("/ws") ? WS_BASE_URL : `${WS_BASE_URL}/ws`;

      // Append auth token if available for authenticated notifications
      const token = localStorage.getItem("access_token");
      if (token) {
        wsUrl += `?token=${encodeURIComponent(token)}`;
      }

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;

        // Emit connected event
        this.listeners.forEach((callback, type) => {
          if (type === "connected") {
            try {
              callback(true);
            } catch (error) {
              console.error("WebSocket listener error:", error);
            }
          }
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Notify all listeners
          this.listeners.forEach((callback, type) => {
            if (!type || data.type === type || type === "message") {
              try {
                callback(data);
              } catch (error) {
                console.error("WebSocket listener error:", error);
              }
            }
          });

          // Emit specific events based on message type
          if (data.type === "scan_progress" || data.type === "scan_update") {
            this.listeners.forEach((callback, type) => {
              if (type === "scan_update") {
                try {
                  callback(data);
                } catch (error) {
                  console.error("WebSocket listener error:", error);
                }
              }
            });
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      this.ws.onclose = (event) => {
        // Emit disconnected event
        this.listeners.forEach((callback, type) => {
          if (type === "disconnected") {
            try {
              callback();
            } catch (error) {
              console.error("WebSocket listener error:", error);
            }
          }
        });

        // Attempt to reconnect if not intentionally closed
        if (
          event.code !== 1000 && // Normal closure
          event.code !== 1001 && // Going away
          this.reconnectAttempts < this.maxReconnectAttempts
        ) {
          this.reconnectAttempts++;
          setTimeout(() => {
            this.connect();
          }, this.reconnectInterval);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.warn("❌ Max reconnection attempts reached");
          // Don't show toast here - let the App component handle it
        }
      };

      this.ws.onerror = (error) => {
        // Only log significant errors
        if (this.reconnectAttempts === 0) {
          console.error("❌ WebSocket connection error:", error);
        }
      };
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, "Client disconnecting");
      this.ws = null;
    }
  }

  // Add event listener
  addEventListener(type, callback) {
    this.listeners.set(type, callback);
  }

  // Add event listener (alias for addEventListener)
  on(type, callback) {
    this.addEventListener(type, callback);
  }

  // Remove event listener
  removeEventListener(type) {
    this.listeners.delete(type);
  }

  // Remove event listener (alias for removeEventListener)
  off(type) {
    this.removeEventListener(type);
  }

  // Send message
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not connected");
    }
  }
}

// Global WebSocket instance
export const websocketService = new WebSocketService();

/**
 * Utility functions
 */
export const utils = {
  // Format file size
  formatFileSize: (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  },

  // Format date
  formatDate: (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  },

  // Format duration from seconds to human readable format
  formatDuration: (seconds) => {
    if (!seconds || seconds < 0) return "0s";

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  },

  // Get severity color
  getSeverityColor: (severity) => {
    const colors = {
      critical: "text-red-600 bg-red-100",
      high: "text-orange-600 bg-orange-100",
      medium: "text-yellow-600 bg-yellow-100",
      low: "text-cyan-600 bg-cyan-100",
      info: "text-gray-600 bg-gray-100",
    };
    return colors[severity?.toLowerCase()] || colors.info;
  },

  // Get severity background color
  getSeverityBgColor: (severity) => {
    const colors = {
      critical: "bg-red-100",
      high: "bg-orange-100",
      medium: "bg-yellow-100",
      low: "bg-cyan-100",
      info: "bg-gray-100",
    };
    return colors[severity?.toLowerCase()] || colors.info;
  },

  // Get severity text color
  getSeverityTextColor: (severity) => {
    const colors = {
      critical: "text-red-600",
      high: "text-orange-600",
      medium: "text-yellow-600",
      low: "text-cyan-600",
      info: "text-gray-600",
    };
    return colors[severity?.toLowerCase()] || colors.info;
  },

  // Download file
  downloadFile: (data, filename, mimeType = "application/octet-stream") => {
    const blob = new Blob([data], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // Debounce function for search inputs
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Copy to clipboard
  copyToClipboard: async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard");
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
      toast.error("Failed to copy to clipboard");
    }
  },

  // Validate repository URL
  validateRepoUrl: (url) => {
    const gitUrlPattern = /^https?:\/\/(github\.com|gitlab\.com|bitbucket\.org)\/.+\/.+/;
    return gitUrlPattern.test(url);
  },

  // Extract project name from repository URL
  getProjectNameFromUrl: (url) => {
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split("/").filter(Boolean);
      if (pathParts.length >= 2) {
        return pathParts[1].replace(/\.git$/, "");
      }
      return "Unknown Project";
    } catch {
      return "Unknown Project";
    }
  },

  // Format relative date (e.g., "2 days ago", "Today")
  formatRelativeDate: (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  },

  // Calculate security score based on findings
  calculateSecurityScore: (findings) => {
    if (!findings) return 100;
    const { critical = 0, high = 0, medium = 0, low = 0 } = findings;
    const total = critical + high + medium + low;
    if (total === 0) return 100;

    const weightedScore = critical * 25 + high * 10 + medium * 5 + low * 1;
    return Math.max(0, Math.min(100, 100 - Math.min(weightedScore, 100)));
  },

  // Get color class for security score
  getScoreColor: (score) => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    if (score >= 40) return "text-orange-400";
    return "text-red-400";
  },

  // Get color class for status
  getStatusColor: (status) => {
    const colors = {
      completed: "text-green-400 bg-green-400/10 border-green-400/30",
      running: "text-cyan-400 bg-cyan-400/10 border-cyan-400/30",
      pending: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
      failed: "text-red-400 bg-red-400/10 border-red-400/30",
    };
    return colors[status] || colors.pending;
  },
};

// ==================== Enterprise API ====================
export const enterpriseAPI = {
  // ---------- Audit Logs ----------

  // Get audit logs with filters
  getAuditLogs: async (params = {}) => {
    try {
      const cleanedParams = cleanParams(params);
      const response = await api.get("/enterprise/audit-logs", {
        params: cleanedParams,
      });
      return response.data;
    } catch (error) {
      console.error("Get audit logs error:", error);
      throw error;
    }
  },

  // Get audit log by ID
  getAuditLogById: async (logId) => {
    try {
      const response = await api.get(`/enterprise/audit-logs/${logId}`);
      return response.data;
    } catch (error) {
      console.error("Get audit log error:", error);
      throw error;
    }
  },

  // Get audit users for filtering
  getAuditUsers: async () => {
    try {
      const response = await api.get("/enterprise/audit-logs/users");
      return response.data;
    } catch (error) {
      console.error("Get audit users error:", error);
      throw error;
    }
  },

  // Get audit event types
  getAuditEventTypes: async () => {
    try {
      const response = await api.get("/enterprise/audit-logs/event-types");
      return response.data;
    } catch (error) {
      console.error("Get audit event types error:", error);
      throw error;
    }
  },

  // Export audit logs
  exportAuditLogs: async (params = {}) => {
    try {
      const cleanedParams = cleanParams(params);
      const response = await api.get("/enterprise/audit-logs/export", {
        params: cleanedParams,
      });
      return response.data;
    } catch (error) {
      console.error("Export audit logs error:", error);
      throw error;
    }
  },

  // Get audit statistics
  getAuditStatistics: async (params = {}) => {
    try {
      const cleanedParams = cleanParams(params);
      const response = await api.get("/enterprise/audit-logs/statistics", {
        params: cleanedParams,
      });
      return response.data;
    } catch (error) {
      console.error("Get audit statistics error:", error);
      throw error;
    }
  },

  // Verify audit log integrity
  verifyAuditLogIntegrity: async (logId) => {
    try {
      const response = await api.post(`/enterprise/audit-logs/${logId}/verify`);
      return response.data;
    } catch (error) {
      console.error("Verify audit log integrity error:", error);
      throw error;
    }
  },

  // ---------- Data Retention Policies ----------

  // Get all retention policies
  getRetentionPolicies: async (params = {}) => {
    try {
      const cleanedParams = cleanParams(params);
      const response = await api.get("/enterprise/retention-policies", {
        params: cleanedParams,
      });
      return response.data;
    } catch (error) {
      console.error("Get retention policies error:", error);
      throw error;
    }
  },

  // Get retention policy by ID
  getRetentionPolicyById: async (policyId) => {
    try {
      const response = await api.get(`/enterprise/retention-policies/${policyId}`);
      return response.data;
    } catch (error) {
      console.error("Get retention policy error:", error);
      throw error;
    }
  },

  // Create retention policy
  createRetentionPolicy: async (policyData) => {
    try {
      const response = await api.post("/enterprise/retention-policies", policyData);
      return response.data;
    } catch (error) {
      console.error("Create retention policy error:", error);
      throw error;
    }
  },

  // Update retention policy
  updateRetentionPolicy: async (policyId, policyData) => {
    try {
      const response = await api.put(`/enterprise/retention-policies/${policyId}`, policyData);
      return response.data;
    } catch (error) {
      console.error("Update retention policy error:", error);
      throw error;
    }
  },

  // Delete retention policy
  deleteRetentionPolicy: async (policyId) => {
    try {
      const response = await api.delete(`/enterprise/retention-policies/${policyId}`);
      return response.data;
    } catch (error) {
      console.error("Delete retention policy error:", error);
      throw error;
    }
  },

  // Execute retention policy
  executeRetentionPolicy: async (policyId) => {
    try {
      const response = await api.post(`/enterprise/retention-policies/${policyId}/execute`);
      return response.data;
    } catch (error) {
      console.error("Execute retention policy error:", error);
      throw error;
    }
  },

  // ---------- Advanced Compliance ----------

  // Get compliance assessments
  getComplianceAssessments: async (params = {}) => {
    try {
      const cleanedParams = cleanParams(params);
      const response = await api.get("/enterprise/compliance/assessments", {
        params: cleanedParams,
      });
      return response.data;
    } catch (error) {
      console.error("Get compliance assessments error:", error);
      throw error;
    }
  },

  // Get compliance assessment by ID
  getComplianceAssessmentById: async (assessmentId) => {
    try {
      const response = await api.get(`/enterprise/compliance/assessments/${assessmentId}`);
      return response.data;
    } catch (error) {
      console.error("Get compliance assessment error:", error);
      throw error;
    }
  },

  // Create compliance assessment
  createComplianceAssessment: async (assessmentData) => {
    try {
      const response = await api.post("/enterprise/compliance/assessments", assessmentData);
      return response.data;
    } catch (error) {
      console.error("Create compliance assessment error:", error);
      throw error;
    }
  },

  // Get compliance framework summary
  getComplianceFrameworkSummary: async () => {
    try {
      const response = await api.get("/enterprise/compliance/framework-summary");
      return response.data;
    } catch (error) {
      console.error("Get compliance framework summary error:", error);
      throw error;
    }
  },

  // Export compliance report
  exportComplianceReport: async ({ assessmentId, format = "json" }) => {
    try {
      const response = await api.get(`/enterprise/compliance/assessments/${assessmentId}/export`, {
        params: { format },
      });
      return response.data;
    } catch (error) {
      console.error("Export compliance report error:", error);
      throw error;
    }
  },

  // Get compliance gap analysis
  getComplianceGapAnalysis: async (assessmentId) => {
    try {
      const response = await api.get(
        `/enterprise/compliance/assessments/${assessmentId}/gap-analysis`
      );
      return response.data;
    } catch (error) {
      console.error("Get compliance gap analysis error:", error);
      throw error;
    }
  },

  // ---------- OSV/NVD Integration ----------

  // Query OSV database for package vulnerabilities
  queryOSV: async ({ ecosystem, packageName, version }) => {
    try {
      const response = await api.post("/enterprise/osv/query", {
        ecosystem,
        package_name: packageName,
        version,
      });
      return response.data;
    } catch (error) {
      console.error("OSV query error:", error);
      throw error;
    }
  },

  // Query NVD for CVE details
  queryNVD: async (cveId) => {
    try {
      const response = await api.get(`/enterprise/nvd/cve/${cveId}`);
      return response.data;
    } catch (error) {
      console.error("NVD query error:", error);
      throw error;
    }
  },

  // Get vulnerability enrichment for findings
  enrichVulnerabilities: async (findings) => {
    try {
      const response = await api.post("/enterprise/vulnerabilities/enrich", {
        findings,
      });
      return response.data;
    } catch (error) {
      console.error("Vulnerability enrichment error:", error);
      throw error;
    }
  },

  // ---------- SBOM Generation ----------

  // Generate SBOM for repository
  generateSBOM: async ({ repositoryPath, format = "cyclonedx" }) => {
    try {
      const response = await api.post("/enterprise/sbom/generate", {
        repository_path: repositoryPath,
        format,
      });
      return response.data;
    } catch (error) {
      console.error("SBOM generation error:", error);
      throw error;
    }
  },

  // Get SBOM for project
  getSBOM: async (projectId) => {
    try {
      const response = await api.get(`/enterprise/sbom/${projectId}`);
      return response.data;
    } catch (error) {
      console.error("Get SBOM error:", error);
      throw error;
    }
  },

  // Export SBOM in different format
  exportSBOM: async ({ sbomId, format }) => {
    try {
      const response = await api.get(`/enterprise/sbom/${sbomId}/export`, {
        params: { format },
      });
      return response.data;
    } catch (error) {
      console.error("Export SBOM error:", error);
      throw error;
    }
  },

  // ---------- Security Trends ----------

  // Get security trends dashboard data
  getSecurityTrends: async (params = {}) => {
    try {
      const cleanedParams = cleanParams(params);
      const response = await api.get("/enterprise/trends/security", {
        params: cleanedParams,
      });
      return response.data;
    } catch (error) {
      console.error("Get security trends error:", error);
      throw error;
    }
  },

  // Get severity trends over time
  getSeverityTrends: async ({ projectId, period = "30d" }) => {
    try {
      const response = await api.get("/enterprise/trends/severity", {
        params: { project_id: projectId, period },
      });
      return response.data;
    } catch (error) {
      console.error("Get severity trends error:", error);
      throw error;
    }
  },

  // Get fix velocity metrics
  getFixVelocity: async (projectId) => {
    try {
      const response = await api.get("/enterprise/trends/fix-velocity", {
        params: { project_id: projectId },
      });
      return response.data;
    } catch (error) {
      console.error("Get fix velocity error:", error);
      throw error;
    }
  },

  // Get security posture score
  getSecurityPosture: async (projectId) => {
    try {
      const response = await api.get("/enterprise/trends/security-posture", {
        params: { project_id: projectId },
      });
      return response.data;
    } catch (error) {
      console.error("Get security posture error:", error);
      throw error;
    }
  },

  // ---------- Scan Comparison ----------

  // Compare two scans
  compareScans: async ({ baseScanId, compareScanId }) => {
    try {
      const response = await api.post("/enterprise-security/scans/compare", {
        base_scan_id: baseScanId,
        compare_scan_id: compareScanId,
      });
      return response.data;
    } catch (error) {
      console.error("Scan comparison error:", error);
      throw error;
    }
  },

  // Get available scans for comparison
  getAvailableScans: async (projectId) => {
    try {
      const response = await api.get("/enterprise/scans/list", {
        params: { project_id: projectId },
      });
      return response.data;
    } catch (error) {
      console.error("Get available scans error:", error);
      throw error;
    }
  },

  // Get scan delta summary
  getScanDelta: async (comparisonId) => {
    try {
      const response = await api.get(`/enterprise/scans/comparison/${comparisonId}/delta`);
      return response.data;
    } catch (error) {
      console.error("Get scan delta error:", error);
      throw error;
    }
  },
};

/**
 * Advanced Security API (Consolidated)
 * Combines threat intelligence, vulnerability management, security metrics,
 * rule management, baseline scanning, and policy enforcement.
 */
export const advancedSecurityAPI = {
  // ===== STATUS & HEALTH =====

  // Get comprehensive security system status
  getStatus: async () => {
    try {
      const response = await api.get("/v1/security/status");
      return response.data;
    } catch (error) {
      console.error("Error getting security status:", error);
      throw error;
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get("/v1/security/health");
      return response.data;
    } catch (error) {
      console.error("Error checking security health:", error);
      throw error;
    }
  },

  // ===== THREAT INTELLIGENCE =====

  // Get threat intelligence feeds
  getThreatFeeds: async () => {
    try {
      const response = await api.get("/v1/security/threat-intel/feeds");
      return response.data;
    } catch (error) {
      console.error("Error getting threat feeds:", error);
      throw error;
    }
  },

  // Analyze threat indicators
  analyzeThreats: async (indicators) => {
    try {
      const response = await api.post("/v1/security/threat-intel/analyze", {
        indicators,
      });
      return response.data;
    } catch (error) {
      console.error("Error analyzing threats:", error);
      throw error;
    }
  },

  // ===== VULNERABILITY MANAGEMENT =====

  // Get vulnerability dashboard
  getVulnerabilityDashboard: async () => {
    try {
      const response = await api.get("/v1/security/vulnerabilities/dashboard");
      return response.data;
    } catch (error) {
      console.error("Error getting vulnerability dashboard:", error);
      throw error;
    }
  },

  // Initiate vulnerability scan
  scanVulnerabilities: async (config = {}) => {
    try {
      const response = await api.post("/v1/security/vulnerabilities/scan", {
        config,
      });
      return response.data;
    } catch (error) {
      console.error("Error initiating vulnerability scan:", error);
      throw error;
    }
  },

  // ===== SECURITY METRICS =====

  // Get security score
  getSecurityScore: async () => {
    try {
      const response = await api.get("/v1/security/metrics/security-score");
      return response.data;
    } catch (error) {
      console.error("Error getting security score:", error);
      throw error;
    }
  },

  // Get metrics dashboard
  getMetricsDashboard: async () => {
    try {
      const response = await api.get("/v1/security/metrics/dashboard");
      return response.data;
    } catch (error) {
      console.error("Error getting metrics dashboard:", error);
      throw error;
    }
  },

  // ===== PENETRATION TESTING =====

  // Execute penetration test
  executePentest: async (config = {}) => {
    try {
      const response = await api.post("/v1/security/pentest/execute", {
        config,
      });
      return response.data;
    } catch (error) {
      console.error("Error executing pentest:", error);
      throw error;
    }
  },

  // ===== RULE ENGINE =====

  // Parse security rules
  parseRules: async (rules) => {
    try {
      const response = await api.post("/v1/security/rules/parse", { rules });
      return response.data;
    } catch (error) {
      console.error("Error parsing rules:", error);
      throw error;
    }
  },

  // Get rule test status
  getRuleTestStatus: async (ruleId) => {
    try {
      const response = await api.get(`/v1/security/rules/test-status/${ruleId}`);
      return response.data;
    } catch (error) {
      console.error("Error getting rule test status:", error);
      throw error;
    }
  },

  // ===== BASELINE MANAGEMENT =====

  // Get baseline status
  getBaselineStatus: async (repository = null, branch = "main") => {
    try {
      const params = {};
      if (repository) params.repository = repository;
      if (branch) params.branch = branch;
      const response = await api.get("/v1/security/baseline/status", {
        params,
      });
      return response.data;
    } catch (error) {
      console.error("Error getting baseline status:", error);
      throw error;
    }
  },

  // ===== POLICY ENGINE =====

  // Evaluate policy
  evaluatePolicy: async (repository, commitHash, policies = []) => {
    try {
      const response = await api.post("/v1/security/policy/evaluate", {
        repository,
        commit_hash: commitHash,
        policies,
      });
      return response.data;
    } catch (error) {
      console.error("Error evaluating policy:", error);
      throw error;
    }
  },

  // Enforce policy
  enforcePolicy: async (policy) => {
    try {
      const response = await api.post("/v1/security/policy/enforce", {
        policy,
      });
      return response.data;
    } catch (error) {
      console.error("Error enforcing policy:", error);
      throw error;
    }
  },

  // ===== ADVANCED SCANNING =====

  // Execute advanced scan
  executeAdvancedScan: async (config = {}) => {
    try {
      const response = await api.post("/v1/security/scan/execute", { config });
      return response.data;
    } catch (error) {
      console.error("Error executing advanced scan:", error);
      throw error;
    }
  },

  // Test security boundaries
  testBoundaries: async (ruleId, testInput, boundaryType = "resource") => {
    try {
      const response = await api.post("/v1/security/scan/boundaries/test", {
        rule_id: ruleId,
        test_input: testInput,
        boundary_type: boundaryType,
      });
      return response.data;
    } catch (error) {
      console.error("Error testing boundaries:", error);
      throw error;
    }
  },

  // Get security boundaries status
  getBoundariesStatus: async () => {
    try {
      const response = await api.get("/v1/security/boundaries/status");
      return response.data;
    } catch (error) {
      console.error("Error getting boundaries status:", error);
      throw error;
    }
  },

  // ===== COMPLIANCE =====

  // Get compliance frameworks
  getComplianceFrameworks: async () => {
    try {
      const response = await api.get("/v1/security/compliance/frameworks");
      return response.data;
    } catch (error) {
      console.error("Error getting compliance frameworks:", error);
      throw error;
    }
  },

  // Get compliance dashboard
  getComplianceDashboard: async () => {
    try {
      const response = await api.get("/v1/security/compliance/dashboard");
      return response.data;
    } catch (error) {
      console.error("Error getting compliance dashboard:", error);
      throw error;
    }
  },
};

/**
 * Scheduled Scans API
 * Cron-based automatic scanning schedules
 */
export const schedulesAPI = {
  listSchedules: async (params = {}) => {
    try {
      const response = await api.get("/schedules", {
        params: cleanParams(params),
      });
      return response.data;
    } catch (error) {
      console.error("Error listing schedules:", error);
      throw error;
    }
  },

  getSchedule: async (scheduleId) => {
    try {
      const response = await api.get(`/schedules/${scheduleId}`);
      return response.data;
    } catch (error) {
      console.error("Error getting schedule:", error);
      throw error;
    }
  },

  createSchedule: async (scheduleData) => {
    try {
      const response = await api.post("/schedules", scheduleData);
      return response.data;
    } catch (error) {
      console.error("Error creating schedule:", error);
      throw error;
    }
  },

  updateSchedule: async (scheduleId, scheduleData) => {
    try {
      const response = await api.put(`/schedules/${scheduleId}`, scheduleData);
      return response.data;
    } catch (error) {
      console.error("Error updating schedule:", error);
      throw error;
    }
  },

  deleteSchedule: async (scheduleId) => {
    try {
      const response = await api.delete(`/schedules/${scheduleId}`);
      return response.data;
    } catch (error) {
      console.error("Error deleting schedule:", error);
      throw error;
    }
  },

  triggerRun: async (scheduleId) => {
    try {
      const response = await api.post(`/schedules/${scheduleId}/run`);
      return response.data;
    } catch (error) {
      console.error("Error triggering schedule run:", error);
      throw error;
    }
  },

  toggleSchedule: async (scheduleId) => {
    try {
      const response = await api.patch(`/schedules/${scheduleId}/toggle`);
      return response.data;
    } catch (error) {
      console.error("Error toggling schedule:", error);
      throw error;
    }
  },

  getScheduleHistory: async (scheduleId, limit = 20) => {
    try {
      const response = await api.get(`/schedules/${scheduleId}/history`, {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error("Error getting schedule history:", error);
      throw error;
    }
  },
};

/**
 * Triage API
 * Intelligent vulnerability prioritization and business impact scoring
 */
export const triageAPI = {
  getTriage: async (scanId, topN = 20) => {
    try {
      const response = await api.get(`/triage/${scanId}?top_n=${topN}`);
      return response.data;
    } catch (error) {
      console.error("Error getting triage data:", error);
      throw error;
    }
  },

  rescoreTriage: async (scanId, context, topN = 20) => {
    try {
      const response = await api.post(`/triage/${scanId}?top_n=${topN}`, context);
      return response.data;
    } catch (error) {
      console.error("Error re-scoring triage:", error);
      throw error;
    }
  },
};

export const secretHistoryAPI = {
  list: async (projectName, { limit = 50, offset = 0, status } = {}) => {
    try {
      const params = { project_name: projectName, limit, offset };
      if (status) params.status = status;
      const response = await api.get("/secret-history", { params });
      return response.data;
    } catch (error) {
      console.error("Error listing secret history:", error);
      throw error;
    }
  },

  trends: async (projectName, limit = 30) => {
    try {
      const response = await api.get("/secret-history/trends", {
        params: { project_name: projectName, limit },
      });
      return response.data;
    } catch (error) {
      console.error("Error getting secret trends:", error);
      throw error;
    }
  },

  summary: async (projectName) => {
    try {
      const response = await api.get("/secret-history/summary", {
        params: { project_name: projectName },
      });
      return response.data;
    } catch (error) {
      console.error("Error getting secret summary:", error);
      throw error;
    }
  },

  updateStatus: async (recordId, status) => {
    try {
      const response = await api.patch(`/secret-history/${recordId}`, null, {
        params: { status },
      });
      return response.data;
    } catch (error) {
      console.error("Error updating secret status:", error);
      throw error;
    }
  },
};

// Default export
export default api;
