/**
 * API Service Layer for SecureDevOps Platform
 * Handles REST API calls and WebSocket connections
 */
import axios from "axios";
import toast from "react-hot-toast";

// API Configuration - Production ready with environment variable support
const API_BASE_URL =
  import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "/api";

// Check if we're in demo mode (no backend available)
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true" || false;

// WebSocket URL - Connect directly to backend in development
const WS_BASE_URL = import.meta.env.DEV
  ? "ws://127.0.0.1:8000" // Direct connection in development
  : import.meta.env.VITE_WS_URL ||
    import.meta.env.VITE_WEBSOCKET_URL ||
    (window.location.protocol === "https:" ? "wss:" : "ws:") +
      "//" +
      window.location.host;

// Debug: Log the configuration values (only in development)
if (import.meta.env.DEV) {
  console.log("🔧 API Configuration:", {
    API_BASE_URL,
    WS_BASE_URL,
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_WS_URL: import.meta.env.VITE_WS_URL,
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    VITE_WEBSOCKET_URL: import.meta.env.VITE_WEBSOCKET_URL,
  });
}

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

    console.log(
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
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
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    console.error(
      "❌ API Response Error:",
      error.response?.data || error.message
    );

    // Handle common error cases
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken && !error.config._retry) {
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
 * Reports API
 */
export const reportsAPI = {
  // Get all reports with filtering and pagination
  getReports: async (params = {}) => {
    try {
      const response = await api.get("/reports", { params });
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

  // Get analytics overview
  getAnalyticsOverview: async (daysBack = 30, projectName = null) => {
    try {
      const params = { days_back: daysBack };
      if (projectName) params.project_name = projectName;

      const response = await api.get("/analytics/overview", { params });
      return response.data;
    } catch (error) {
      console.error("Error fetching analytics:", error);
      throw error;
    }
  },

  // Get project-specific reports
  getProjectReports: async (projectName, params = {}) => {
    try {
      const response = await api.get(
        `/reports/project/${encodeURIComponent(projectName)}`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching project reports:", error);
      throw error;
    }
  },

  // Start a new scan
  startScan: async (scanData) => {
    try {
      // Webhook endpoints are not under /api prefix, so use direct fetch
      const backendBaseUrl = API_BASE_URL.replace("/api", "");
      const response = await fetch(`${backendBaseUrl}/webhook/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(scanData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error starting scan:", error);
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
      const url = `${backendBaseUrl}/webhook/events${
        queryParams ? "?" + queryParams : ""
      }`;

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
        (this.ws.readyState === WebSocket.CONNECTING ||
          this.ws.readyState === WebSocket.OPEN)
      ) {
        return;
      }

      // Close existing connection if it's in a bad state
      if (this.ws && this.ws.readyState === WebSocket.CLOSING) {
        this.ws = null;
      }

      console.log(
        "🔌 Attempting WebSocket connection to:",
        WS_BASE_URL.endsWith("/ws") ? WS_BASE_URL : `${WS_BASE_URL}/ws`
      );
      this.ws = new WebSocket(
        WS_BASE_URL.endsWith("/ws") ? WS_BASE_URL : `${WS_BASE_URL}/ws`
      );

      this.ws.onopen = () => {
        console.log("🔌 WebSocket connected successfully");
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
          console.log("📨 WebSocket message:", data);

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
        console.log("🔌 WebSocket disconnected:", event.code, event.reason);

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
          console.log(
            `🔄 Attempting to reconnect (${this.reconnectAttempts}/${
              this.maxReconnectAttempts
            }) in ${this.reconnectInterval / 1000}s...`
          );

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
      low: "text-blue-600 bg-blue-100",
      info: "text-gray-600 bg-gray-100",
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
    const gitUrlPattern =
      /^https?:\/\/(github\.com|gitlab\.com|bitbucket\.org)\/.+\/.+/;
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
      running: "text-blue-400 bg-blue-400/10 border-blue-400/30",
      pending: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
      failed: "text-red-400 bg-red-400/10 border-red-400/30",
    };
    return colors[status] || colors.pending;
  },

  // Get color class for severity
  getSeverityColor: (severity) => {
    const colors = {
      critical: "text-red-400 bg-red-400/10 border-red-400/30",
      high: "text-orange-400 bg-orange-400/10 border-orange-400/30",
      medium: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
      low: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    };
    return colors[severity] || colors.low;
  },
};

// Default export
export default api;
