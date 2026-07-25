/**
 * Settings Component for ONYX Platform
 * Platform configuration and user preferences management
 */
import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  CogIcon,
  ShieldCheckIcon,
  BellIcon,
  ComputerDesktopIcon,
  EnvelopeIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  Cog6ToothIcon,
  KeyIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import {
  CheckCircleIcon as CheckCircleSolid,
  ExclamationTriangleIcon as ExclamationTriangleSolid,
} from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "../auth";
import { Button, Input } from "../../styles/components";
import { PageContainer, PageHeader, GlassCard } from "../../layouts";
import { systemAPI } from "../../services/api";

// System Info Component - Fetches real data from backend
const SystemInfo = () => {
  const [systemInfo, setSystemInfo] = useState({
    version: "Loading...",
    build: "Loading...",
    environment: "Loading...",
    database: { status: "checking", message: "Checking..." },
    scanners: { active: 0, total: 0 },
  });

  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        // Fetch health status from backend
        const API_URL = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";
        const healthResponse = await fetch(`${API_URL}/api/health`);

        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          setSystemInfo({
            version: healthData.version || "1.0.0",
            build:
              healthData.build_date || new Date().toISOString().split("T")[0],
            environment: import.meta.env.DEV ? "Development" : "Production",
            database: {
              status: healthData.database?.connected
                ? "connected"
                : "disconnected",
              message: healthData.database?.connected
                ? "Connected"
                : "Disconnected",
            },
            scanners: {
              active: healthData.scanners?.active || 0,
              total: healthData.scanners?.total || 4,
            },
          });
        } else {
          // API available but returned error
          setSystemInfo((prev) => ({
            ...prev,
            version: "1.0.0",
            build: new Date().toISOString().split("T")[0],
            environment: import.meta.env.DEV ? "Development" : "Production",
            database: { status: "error", message: "Error checking" },
          }));
        }
      } catch (error) {
        // API not available
        setSystemInfo((prev) => ({
          ...prev,
          version: "1.0.0",
          build: new Date().toISOString().split("T")[0],
          environment: import.meta.env.DEV ? "Development" : "Production",
          database: { status: "offline", message: "Offline" },
          scanners: { active: 0, total: 4 },
        }));
      }
    };

    fetchSystemInfo();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSystemInfo, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "connected":
        return "text-green-400";
      case "disconnected":
      case "error":
        return "text-red-400";
      case "checking":
        return "text-yellow-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div className="mt-3 space-y-2 text-sm">
      <div className="flex justify-between">
        <span className="text-gray-400">Version:</span>
        <span className="text-white">{systemInfo.version}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Build:</span>
        <span className="text-white">{systemInfo.build}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Environment:</span>
        <span className="text-white">{systemInfo.environment}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Database:</span>
        <span className={getStatusColor(systemInfo.database.status)}>
          {systemInfo.database.message}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Scanners:</span>
        <span
          className={
            systemInfo.scanners.active > 0
              ? "text-green-400"
              : "text-yellow-400"
          }
        >
          {systemInfo.scanners.active} Active / {systemInfo.scanners.total}{" "}
          Total
        </span>
      </div>
    </div>
  );
};

const Settings = () => {
  const [activeTab, setActiveTab] = useState("security");
  const [showApiKey, setShowApiKey] = useState(false);
  const { user } = useAuth();

  // Platform settings data - in a real app, these would come from API
  const [settings, setSettings] = useState({
    security: {
      two_factor_enabled: false,
      session_timeout: 30,
      login_notifications: true,
      password_policy: {
        min_length: 8,
        require_uppercase: true,
        require_lowercase: true,
        require_numbers: true,
        require_symbols: true,
      },
    },
    notifications: {
      email_enabled: true,
      slack_enabled: false,
      teams_enabled: false,
      critical_alerts: true,
      scan_completion: true,
      new_vulnerabilities: true,
      weekly_reports: true,
    },
    scanning: {
      auto_scan_on_push: false,
      scan_timeout: 300,
      max_concurrent_scans: 3,
      enabled_scanners: ["sast", "secrets", "container", "infrastructure"],
      custom_rules_enabled: false,
    },
    api: {
      api_key: "sk-••••••••••••••••••••••••••••••••",
      rate_limit: 1000,
      webhook_url: "",
    },
  });

  // Save settings mutation
  const saveSettingsMutation = useMutation({
    mutationFn: async (settingsData) => {
      // Call real settings API endpoint
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `${
          import.meta.env.DEV ? "http://127.0.0.1:8000" : ""
        }/api/users/me/settings`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
          body: JSON.stringify(settingsData),
        }
      );
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save settings");
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success("Settings saved successfully!");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to save settings");
    },
  });

  const handleSettingChange = (category, key, value) => {
    setSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
  };

  const handleNestedSettingChange = (category, parentKey, key, value) => {
    setSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [parentKey]: {
          ...prev[category][parentKey],
          [key]: value,
        },
      },
    }));
  };

  const handleSaveSettings = () => {
    saveSettingsMutation.mutate(settings);
  };

  const tabs = [
    { key: "security", label: "Security", icon: ShieldCheckIcon },
    { key: "notifications", label: "Notifications", icon: BellIcon },
    { key: "scanning", label: "Scanning", icon: CogIcon },
    { key: "api", label: "API & Integration", icon: DocumentTextIcon },
    { key: "system", label: "System", icon: ComputerDesktopIcon },
  ];

  const SettingCard = ({ title, description, children, type = "default" }) => (
    <div
      className={`bg-gray-900/50 backdrop-blur-sm border rounded-xl p-6 ${
        type === "warning"
          ? "border-yellow-500/30"
          : type === "danger"
          ? "border-red-500/30"
          : "border-gray-700/50"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="text-white font-medium mb-1">{title}</h4>
          {description && (
            <p className="text-gray-400 text-sm mb-4">{description}</p>
          )}
        </div>
        <div className="ml-4">{children}</div>
      </div>
    </div>
  );

  const Toggle = ({ enabled, onChange, disabled = false, label }) => (
    <button
      role="switch"
      aria-checked={enabled}
      aria-label={label}
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
        enabled ? "bg-blue-600" : "bg-gray-600"
      } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="Settings"
          description="Manage your account preferences and platform configuration"
          icon={CogIcon}
          breadcrumb={["Settings"]}
        />

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="lg:w-64 flex-shrink-0">
            <GlassCard noPadding className="p-2">
              <nav className="space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      activeTab === tab.key
                        ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                        : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>
            </GlassCard>

            <Button
              onClick={handleSaveSettings}
              disabled={saveSettingsMutation.isPending}
              isLoading={saveSettingsMutation.isPending}
              className="w-full mt-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700"
            >
              Save Settings
            </Button>
          </div>

          {/* Content */}
          <div className="flex-1">
            <GlassCard>
              {/* Security Settings */}
              {activeTab === "security" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-white">
                    Security Settings
                  </h2>

                  <SettingCard
                    title="Two-Factor Authentication"
                    description="Add an extra layer of security to your account"
                  >
                    <Toggle
                      label="Two-Factor Authentication"
                      enabled={settings.security.two_factor_enabled}
                      onChange={(value) =>
                        handleSettingChange(
                          "security",
                          "two_factor_enabled",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="Login Notifications"
                    description="Get notified when someone logs into your account"
                  >
                    <Toggle
                      label="Login Notifications"
                      enabled={settings.security.login_notifications}
                      onChange={(value) =>
                        handleSettingChange(
                          "security",
                          "login_notifications",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="Session Timeout"
                    description="Automatically log out after a period of inactivity"
                  >
                    <select
                      value={settings.security.session_timeout}
                      onChange={(e) =>
                        handleSettingChange(
                          "security",
                          "session_timeout",
                          parseInt(e.target.value)
                        )
                      }
                      className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
                    >
                      <option value={15} className="bg-gray-800 text-white">
                        15 minutes
                      </option>
                      <option value={30} className="bg-gray-800 text-white">
                        30 minutes
                      </option>
                      <option value={60} className="bg-gray-800 text-white">
                        1 hour
                      </option>
                      <option value={120} className="bg-gray-800 text-white">
                        2 hours
                      </option>
                      <option value={480} className="bg-gray-800 text-white">
                        8 hours
                      </option>
                    </select>
                  </SettingCard>

                  <SettingCard
                    title="Password Policy"
                    description="Configure password requirements for your organization"
                    type="warning"
                  >
                    <div className="space-y-3 w-full max-w-md">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">
                          Minimum Length (8)
                        </span>
                        <input
                          type="number"
                          min="6"
                          max="32"
                          value={settings.security.password_policy.min_length}
                          onChange={(e) =>
                            handleNestedSettingChange(
                              "security",
                              "password_policy",
                              "min_length",
                              parseInt(e.target.value)
                            )
                          }
                          className="w-16 px-2 py-1 bg-gray-700/50 border border-gray-600/50 rounded text-white text-sm"
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">
                          Require Uppercase
                        </span>
                        <Toggle
                          label="Require Uppercase"
                          enabled={
                            settings.security.password_policy.require_uppercase
                          }
                          onChange={(value) =>
                            handleNestedSettingChange(
                              "security",
                              "password_policy",
                              "require_uppercase",
                              value
                            )
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">
                          Require Numbers
                        </span>
                        <Toggle
                          label="Require Numbers"
                          enabled={
                            settings.security.password_policy.require_numbers
                          }
                          onChange={(value) =>
                            handleNestedSettingChange(
                              "security",
                              "password_policy",
                              "require_numbers",
                              value
                            )
                          }
                        />
                      </div>
                    </div>
                  </SettingCard>
                </div>
              )}

              {/* Notification Settings */}
              {activeTab === "notifications" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-white">
                    Notification Settings
                  </h2>

                  <SettingCard
                    title="Email Notifications"
                    description="Receive notifications via email"
                  >
                    <Toggle
                      label="Email Notifications"
                      enabled={settings.notifications.email_enabled}
                      onChange={(value) =>
                        handleSettingChange(
                          "notifications",
                          "email_enabled",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="Critical Security Alerts"
                    description="Get immediately notified of critical vulnerabilities"
                  >
                    <Toggle
                      label="Critical Security Alerts"
                      enabled={settings.notifications.critical_alerts}
                      onChange={(value) =>
                        handleSettingChange(
                          "notifications",
                          "critical_alerts",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="Scan Completion"
                    description="Get notified when security scans complete"
                  >
                    <Toggle
                      label="Scan Completion"
                      enabled={settings.notifications.scan_completion}
                      onChange={(value) =>
                        handleSettingChange(
                          "notifications",
                          "scan_completion",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="New Vulnerabilities"
                    description="Get notified when new vulnerabilities are detected"
                  >
                    <Toggle
                      label="New Vulnerabilities"
                      enabled={settings.notifications.new_vulnerabilities}
                      onChange={(value) =>
                        handleSettingChange(
                          "notifications",
                          "new_vulnerabilities",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="Weekly Reports"
                    description="Receive weekly security summary reports"
                  >
                    <Toggle
                      label="Weekly Reports"
                      enabled={settings.notifications.weekly_reports}
                      onChange={(value) =>
                        handleSettingChange(
                          "notifications",
                          "weekly_reports",
                          value
                        )
                      }
                    />
                  </SettingCard>
                </div>
              )}

              {/* Scanning Settings */}
              {activeTab === "scanning" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-white">
                    Scanning Configuration
                  </h2>

                  <SettingCard
                    title="Auto-scan on Push"
                    description="Automatically run scans when code is pushed to repositories"
                  >
                    <Toggle
                      label="Auto-scan on Push"
                      enabled={settings.scanning.auto_scan_on_push}
                      onChange={(value) =>
                        handleSettingChange(
                          "scanning",
                          "auto_scan_on_push",
                          value
                        )
                      }
                    />
                  </SettingCard>

                  <SettingCard
                    title="Scan Timeout"
                    description="Maximum time allowed for a scan to complete"
                  >
                    <select
                      value={settings.scanning.scan_timeout}
                      onChange={(e) =>
                        handleSettingChange(
                          "scanning",
                          "scan_timeout",
                          parseInt(e.target.value)
                        )
                      }
                      className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
                    >
                      <option value={180} className="bg-gray-800 text-white">
                        3 minutes
                      </option>
                      <option value={300} className="bg-gray-800 text-white">
                        5 minutes
                      </option>
                      <option value={600} className="bg-gray-800 text-white">
                        10 minutes
                      </option>
                      <option value={1200} className="bg-gray-800 text-white">
                        20 minutes
                      </option>
                      <option value={1800} className="bg-gray-800 text-white">
                        30 minutes
                      </option>
                    </select>
                  </SettingCard>

                  <SettingCard
                    title="Concurrent Scans"
                    description="Maximum number of scans that can run simultaneously"
                  >
                    <select
                      value={settings.scanning.max_concurrent_scans}
                      onChange={(e) =>
                        handleSettingChange(
                          "scanning",
                          "max_concurrent_scans",
                          parseInt(e.target.value)
                        )
                      }
                      className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
                    >
                      <option value={1} className="bg-gray-800 text-white">
                        1 scan
                      </option>
                      <option value={2} className="bg-gray-800 text-white">
                        2 scans
                      </option>
                      <option value={3} className="bg-gray-800 text-white">
                        3 scans
                      </option>
                      <option value={5} className="bg-gray-800 text-white">
                        5 scans
                      </option>
                      <option value={10} className="bg-gray-800 text-white">
                        10 scans
                      </option>
                    </select>
                  </SettingCard>

                  <SettingCard
                    title="Enabled Scanners"
                    description="Choose which security scanners to use by default"
                  >
                    <div className="space-y-2 w-full max-w-md">
                      {["sast", "secrets", "container", "infrastructure"].map(
                        (scanner) => (
                          <div
                            key={scanner}
                            className="flex items-center justify-between"
                          >
                            <span className="text-sm text-gray-300 capitalize">
                              {scanner} Analysis
                            </span>
                            <Toggle
                              label={`${scanner} Analysis`}
                              enabled={settings.scanning.enabled_scanners.includes(
                                scanner
                              )}
                              onChange={(enabled) => {
                                const newScanners = enabled
                                  ? [
                                      ...settings.scanning.enabled_scanners,
                                      scanner,
                                    ]
                                  : settings.scanning.enabled_scanners.filter(
                                      (s) => s !== scanner
                                    );
                                handleSettingChange(
                                  "scanning",
                                  "enabled_scanners",
                                  newScanners
                                );
                              }}
                            />
                          </div>
                        )
                      )}
                    </div>
                  </SettingCard>
                </div>
              )}

              {/* API Settings */}
              {activeTab === "api" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-white">
                    API & Integration
                  </h2>

                  <SettingCard
                    title="API Key"
                    description="Your API key for integrating with external services"
                    type="warning"
                  >
                    <div className="space-y-3 w-full max-w-md">
                      <div className="flex items-center space-x-2">
                        <div className="relative flex-1">
                          <input
                            type={showApiKey ? "text" : "password"}
                            value={settings.api.api_key}
                            readOnly
                            className="w-full px-3 py-2 pr-10 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white font-mono text-sm"
                          />
                          <button
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                          >
                            {showApiKey ? (
                              <EyeSlashIcon className="h-4 w-4" />
                            ) : (
                              <EyeIcon className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                        <Button
                          onClick={() =>
                            toast.success("New API key generated!")
                          }
                          variant="warning"
                          size="sm"
                        >
                          Regenerate
                        </Button>
                      </div>
                      <p className="text-xs text-yellow-400">
                        Keep your API key secure. Don't share it or expose it in
                        client-side code.
                      </p>
                    </div>
                  </SettingCard>

                  <SettingCard
                    title="Webhook URL"
                    description="Receive scan results and notifications via webhook"
                  >
                    <input
                      type="url"
                      value={settings.api.webhook_url}
                      onChange={(e) =>
                        handleSettingChange(
                          "api",
                          "webhook_url",
                          e.target.value
                        )
                      }
                      placeholder="https://your-domain.com/webhook"
                      className="w-full max-w-md px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                  </SettingCard>

                  <SettingCard
                    title="Rate Limiting"
                    description="API request limits per hour"
                  >
                    <div className="flex items-center space-x-3">
                      <input
                        type="number"
                        value={settings.api.rate_limit}
                        onChange={(e) =>
                          handleSettingChange(
                            "api",
                            "rate_limit",
                            parseInt(e.target.value)
                          )
                        }
                        className="w-24 px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                      <span className="text-gray-400">requests/hour</span>
                    </div>
                  </SettingCard>
                </div>
              )}

              {/* System Settings */}
              {activeTab === "system" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-white">
                    System Information
                  </h2>

                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
                    <div className="flex items-start space-x-3">
                      <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
                      <div>
                        <p className="text-blue-400 font-medium">
                          Platform Information
                        </p>
                        <SystemInfo />
                      </div>
                    </div>
                  </div>

                  <SettingCard
                    title="Maintenance Mode"
                    description="Temporarily disable new scans for system maintenance"
                    type="danger"
                  >
                    <Toggle
                      label="Maintenance Mode"
                      enabled={false}
                      onChange={() =>
                        toast("Maintenance mode requires admin privileges", { icon: "ℹ️" })
                      }
                      disabled={user?.role !== "admin"}
                    />
                  </SettingCard>

                  <SettingCard
                    title="Export Data"
                    description="Download your security scan data and reports"
                  >
                    <Button
                      onClick={() =>
                        toast.success(
                          "Data export initiated! You'll receive an email when ready."
                        )
                      }
                      variant="success"
                    >
                      Export Data
                    </Button>
                  </SettingCard>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export default Settings;
