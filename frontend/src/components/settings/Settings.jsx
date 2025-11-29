/**
 * Settings Component for SecureDevOps Platform
 * Platform configuration and user preferences management
 */
import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
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
} from "@heroicons/react/24/outline";
import {
  CheckCircleIcon as CheckCircleSolid,
  ExclamationTriangleIcon as ExclamationTriangleSolid,
} from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "../auth";
import { PageContainer, PageHeader, GlassCard } from "../../layouts";

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
    mutationFn: (settingsData) => {
      // Mock API call - replace with actual API endpoint
      return new Promise((resolve) => {
        setTimeout(() => resolve(settingsData), 1000);
      });
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

  const Toggle = ({ enabled, onChange, disabled = false }) => (
    <button
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
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

            {/* Save Button */}
            <button
              onClick={handleSaveSettings}
              disabled={saveSettingsMutation.isPending}
              className="w-full mt-6 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition-all"
            >
              {saveSettingsMutation.isPending ? "Saving..." : "Save Settings"}
            </button>
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
                        <button
                          onClick={() =>
                            toast.success("New API key generated!")
                          }
                          className="px-3 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-all text-sm"
                        >
                          Regenerate
                        </button>
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
                        <div className="mt-3 space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Version:</span>
                            <span className="text-white">1.0.0</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Build:</span>
                            <span className="text-white">2024.08.16</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Environment:</span>
                            <span className="text-white">Production</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Database:</span>
                            <span className="text-green-400">Connected</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Scanners:</span>
                            <span className="text-green-400">4 Active</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <SettingCard
                    title="Maintenance Mode"
                    description="Temporarily disable new scans for system maintenance"
                    type="danger"
                  >
                    <Toggle
                      enabled={false}
                      onChange={() =>
                        toast.info("Maintenance mode requires admin privileges")
                      }
                      disabled={user?.role !== "admin"}
                    />
                  </SettingCard>

                  <SettingCard
                    title="Export Data"
                    description="Download your security scan data and reports"
                  >
                    <button
                      onClick={() =>
                        toast.success(
                          "Data export initiated! You'll receive an email when ready."
                        )
                      }
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all"
                    >
                      Export Data
                    </button>
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
