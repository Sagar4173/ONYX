import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  CogIcon,
  ShieldCheckIcon,
  BellIcon,
  ComputerDesktopIcon,
  DocumentTextIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { useAuth } from "../auth";
import { Button } from "../../styles/components";
import { PageContainer, PageHeader, GlassCard } from "../../layouts";
import SecurityTab from "./SecurityTab";
import NotificationTab from "./NotificationTab";
import ScanningTab from "./ScanningTab";
import ApiTab from "./ApiTab";
import SystemTab from "./SystemTab";

const Settings = () => {
  const [activeTab, setActiveTab] = useState("security");
  const { user } = useAuth();

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

  const saveSettingsMutation = useMutation({
    mutationFn: async (settingsData) => {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `${import.meta.env.DEV ? "http://127.0.0.1:8000" : ""}/api/users/me/settings`,
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

  const tabContent = {
    security: (
      <SecurityTab
        settings={settings}
        handleSettingChange={handleSettingChange}
        handleNestedSettingChange={handleNestedSettingChange}
      />
    ),
    notifications: (
      <NotificationTab settings={settings} handleSettingChange={handleSettingChange} />
    ),
    scanning: <ScanningTab settings={settings} handleSettingChange={handleSettingChange} />,
    api: <ApiTab settings={settings} handleSettingChange={handleSettingChange} />,
    system: <SystemTab user={user} />,
  };

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        <PageHeader
          title="Settings"
          description="Manage your account preferences and platform configuration"
          icon={CogIcon}
          breadcrumb={["Settings"]}
        />

        <div className="flex flex-col lg:flex-row gap-8">
          <div className="lg:w-64 flex-shrink-0">
            <GlassCard noPadding className="p-2">
              <nav className="space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      activeTab === tab.key
                        ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
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
              className="w-full mt-6 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200"
            >
              Save Settings
            </Button>
          </div>

          <div className="flex-1">
            <GlassCard>{tabContent[activeTab]}</GlassCard>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export default Settings;
