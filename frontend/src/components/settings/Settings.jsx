import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  CogIcon,
  ShieldCheckIcon,
  BellIcon,
  ComputerDesktopIcon,
  DocumentTextIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { useAuth } from "../auth";
import { Button } from "../ui/StyleComponents";
import { PageContainer, PageHeader, GlassCard } from "../../layouts";
import ParticleBackground from "../projects/ParticleBackground";
import SecurityTab from "./SecurityTab";
import NotificationTab from "./NotificationTab";
import ScanningTab from "./ScanningTab";
import ApiTab from "./ApiTab";
import SystemTab from "./SystemTab";

const TABS = [
  { key: "security", label: "Security", icon: ShieldCheckIcon },
  { key: "notifications", label: "Notifications", icon: BellIcon },
  { key: "scanning", label: "Scanning", icon: CogIcon },
  { key: "api", label: "API & Integration", icon: DocumentTextIcon },
  { key: "system", label: "System", icon: ComputerDesktopIcon },
];

const contentAnim = {
  hidden: { opacity: 0, x: 10 },
  show: { opacity: 1, x: 0 },
};

const Settings = () => {
  const [activeTab, setActiveTab] = useState("security");
  const { user } = useAuth();

  const settingsApiUrl = `${import.meta.env.DEV ? "http://127.0.0.1:8000" : ""}/api/users/me/settings`;

  const { data: savedSettings } = useQuery({
    queryKey: ["userSettings"],
    queryFn: async () => {
      const token = localStorage.getItem("access_token");
      const response = await fetch(settingsApiUrl, {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!response.ok) return {};
      return response.json();
    },
  });

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
      const response = await fetch(settingsApiUrl, {
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

  useEffect(() => {
    if (savedSettings && Object.keys(savedSettings).length > 0) {
      setSettings((prev) => ({ ...prev, ...savedSettings }));
    }
  }, [savedSettings]);

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
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <PageHeader
            title="Settings"
            description="Manage your account preferences and platform configuration"
            icon={CogIcon}
            breadcrumb={["Settings"]}
          />
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="lg:w-64 flex-shrink-0">
              <GlassCard noPadding className="p-2 sticky top-8">
                <nav className="space-y-1">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`relative w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                          activeTab === tab.key
                            ? "text-white"
                            : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                        }`}
                      >
                        {activeTab === tab.key && (
                          <motion.div
                            layoutId="tab-indicator"
                            className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-xl"
                            initial={false}
                            transition={{
                              type: "spring",
                              stiffness: 500,
                              damping: 30,
                            }}
                          />
                        )}
                        <span className="relative z-10 flex items-center space-x-3">
                          <Icon className="w-4 h-4" />
                          <span>{tab.label}</span>
                        </span>
                      </button>
                    );
                  })}
                </nav>
              </GlassCard>
              <button
                onClick={handleSaveSettings}
                disabled={saveSettingsMutation.isPending}
                className="w-full mt-6 inline-flex items-center justify-center px-4 py-2.5 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                {saveSettingsMutation.isPending ? (
                  <>
                    <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" /> Saving...
                  </>
                ) : (
                  "Save Settings"
                )}
              </button>
            </div>
            <div className="flex-1">
              <GlassCard>
                <motion.div
                  key={activeTab}
                  variants={contentAnim}
                  initial="hidden"
                  animate="show"
                  transition={{ duration: 0.2 }}
                >
                  {tabContent[activeTab]}
                </motion.div>
              </GlassCard>
            </div>
          </div>
        </div>
      </PageContainer>
    </div>
  );
};

export default Settings;
