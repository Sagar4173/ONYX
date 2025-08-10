/**
 * API Service Layer for SecureDevOps Platform
 * Handles REST API calls and WebSocket connections
 */
import axios from "axios";
import toast from "react-hot-toast";

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

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
    const token = localStorage.getItem("auth_token");
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
  (error) => {
    console.error(
      "❌ API Response Error:",
      error.response?.data || error.message
    );

    // Handle common error cases
    if (error.response?.status === 401) {
      toast.error("Authentication required");
      // Redirect to login if needed
    } else if (error.response?.status === 403) {
      toast.error("Access forbidden");
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
    const response = await api.get("/api/reports", { params });
    return response.data;
  },

  // Get detailed report by ID
  getReport: async (reportId) => {
    if (!reportId || reportId === "undefined" || reportId === "null") {
      throw new Error("Invalid report ID provided");
    }
    const response = await api.get(`/api/reports/${reportId}`);
    return response.data;
  },

  // Get report summary
  getReportSummary: async (reportId) => {
    const response = await api.get(`/api/reports/${reportId}/summary`);
    return response.data;
  },

  // Get analytics overview
  getAnalyticsOverview: async (daysBack = 30, projectName = null) => {
    const params = { days_back: daysBack };
    if (projectName) params.project_name = projectName;

    const response = await api.get("/api/analytics/overview", { params });
    return response.data;
  },

  // Get project-specific reports
  getProjectReports: async (projectName, params = {}) => {
    const response = await api.get(
      `/api/reports/project/${encodeURIComponent(projectName)}`,
      { params }
    );
    return response.data;
  },
};

/**
 * Webhook API
 */
export const webhookAPI = {
  // Get webhook events
  getWebhookEvents: async (params = {}) => {
    const response = await api.get("/webhook/events", { params });
    return response.data;
  },

  // Get webhook event by ID
  getWebhookEvent: async (eventId) => {
    const response = await api.get(`/webhook/events/${eventId}`);
    return response.data;
  },

  // Test webhook endpoint
  testWebhook: async () => {
    const response = await api.post("/webhook/test");
    return response.data;
  },
};

/**
 * System API
 */
export const systemAPI = {
  // Health check
  getHealth: async () => {
    const response = await api.get("/health");
    return response.data;
  },

  // Get metrics
  getMetrics: async () => {
    const response = await api.get("/metrics");
    return response.data;
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
    this.reconnectInterval = 1000;
    this.listeners = new Map();
  }

  connect() {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws`);

      this.ws.onopen = () => {
        console.log("🔌 WebSocket connected");
        this.reconnectAttempts = 0;
        toast.success("Connected to real-time updates");
        this.emit("connected", true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📨 WebSocket message:", data);
          this.emit(data.type, data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      this.ws.onclose = (event) => {
        console.log("🔌 WebSocket disconnected:", event.code, event.reason);
        this.emit("disconnected", false);

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(
            `🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
          );

          setTimeout(() => {
            this.connect();
          }, this.reconnectInterval * this.reconnectAttempts);
        } else {
          toast.error("Lost connection to real-time updates");
        }
      };

      this.ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        this.emit("error", error);
      };
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error("WebSocket listener error:", error);
        }
      });
    }
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
 * Utility Functions
 */
export const utils = {
  // Format date for display
  formatDate: (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString();
  },

  // Format duration in seconds to human readable
  formatDuration: (seconds) => {
    if (!seconds) return "N/A";

    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  },

  // Get severity color class
  getSeverityColor: (severity) => {
    const colors = {
      critical: "text-red-600 bg-red-50 border-red-200",
      high: "text-orange-600 bg-orange-50 border-orange-200",
      medium: "text-yellow-600 bg-yellow-50 border-yellow-200",
      low: "text-blue-600 bg-blue-50 border-blue-200",
      info: "text-gray-600 bg-gray-50 border-gray-200",
    };
    return colors[severity] || colors.info;
  },

  // Get status color class
  getStatusColor: (status) => {
    const colors = {
      completed: "text-green-600 bg-green-50 border-green-200",
      running: "text-blue-600 bg-blue-50 border-blue-200",
      pending: "text-yellow-600 bg-yellow-50 border-yellow-200",
      failed: "text-red-600 bg-red-50 border-red-200",
    };
    return colors[status] || colors.pending;
  },

  // Calculate security score
  calculateSecurityScore: (findingsBySeverity) => {
    if (!findingsBySeverity) return 100;

    const weights = {
      critical: 20,
      high: 10,
      medium: 5,
      low: 2,
      info: 1,
    };

    let totalDeductions = 0;
    Object.entries(findingsBySeverity).forEach(([severity, count]) => {
      totalDeductions += (weights[severity] || 0) * count;
    });

    // Cap score between 0 and 100
    return Math.max(0, Math.min(100, 100 - totalDeductions));
  },

  // Get security score color
  getScoreColor: (score) => {
    if (score >= 90) return "text-green-600";
    if (score >= 70) return "text-yellow-600";
    if (score >= 50) return "text-orange-600";
    return "text-red-600";
  },

  // Download file
  downloadFile: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
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

  // Debounce function
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
};

// Export default API instance
export default api;
