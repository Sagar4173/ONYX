# Settings Page Remaster — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster the Settings page with ParticleBackground, animated sidebar tab indicator, staggered tab content, glassmorphism SettingCard, smooth Toggle animation.

**Architecture:** Single-file orchestrator + 5 tab components + 2 shared controls + 1 info component. All files modified in-place, no new files created.

**Tech Stack:** React 18, Vite, tailwindcss, framer-motion, @tanstack/react-query

## Global Constraints
- Zero new npm dependencies
- All visualizations use CSS or framer-motion only
- ONYX design language: cyan-400/violet-500 gradients, glassmorphism, dark theme
- `npx eslint src/` must pass with 0 errors, 0 warnings

---

### Task 1: Settings.jsx — Orchestrator with Particles + Animated Sidebar

**Files:**
- Rewrite: `frontend/src/components/settings/Settings.jsx`

- [ ] **Step 1: Rewrite Settings.jsx**

```jsx
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CogIcon, ShieldCheckIcon, BellIcon, ComputerDesktopIcon, DocumentTextIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { useAuth } from "../auth";
import { Button } from "../../styles/components";
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

const contentAnim = { hidden: { opacity: 0, x: 10 }, show: { opacity: 1, x: 0 } };

const Settings = () => {
  const [activeTab, setActiveTab] = useState("security");
  const { user } = useAuth();

  const [settings, setSettings] = useState({
    security: { two_factor_enabled: false, session_timeout: 30, login_notifications: true, password_policy: { min_length: 8, require_uppercase: true, require_lowercase: true, require_numbers: true, require_symbols: true } },
    notifications: { email_enabled: true, slack_enabled: false, teams_enabled: false, critical_alerts: true, scan_completion: true, new_vulnerabilities: true, weekly_reports: true },
    scanning: { auto_scan_on_push: false, scan_timeout: 300, max_concurrent_scans: 3, enabled_scanners: ["sast", "secrets", "container", "infrastructure"], custom_rules_enabled: false },
    api: { api_key: "sk-••••••••••••••••••••••••••••••••", rate_limit: 1000, webhook_url: "" },
  });

  const saveSettingsMutation = useMutation({
    mutationFn: async (settingsData) => {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${import.meta.env.DEV ? "http://127.0.0.1:8000" : ""}/api/users/me/settings`, {
        method: "PUT", headers: { "Content-Type": "application/json", Authorization: token ? `Bearer ${token}` : "" },
        body: JSON.stringify(settingsData),
      });
      if (!response.ok) { const error = await response.json(); throw new Error(error.detail || "Failed to save settings"); }
      return response.json();
    },
    onSuccess: () => toast.success("Settings saved successfully!"),
    onError: (error) => toast.error(error.message || "Failed to save settings"),
  });

  const handleSettingChange = (category, key, value) => setSettings((prev) => ({ ...prev, [category]: { ...prev[category], [key]: value } }));
  const handleNestedSettingChange = (category, parentKey, key, value) => setSettings((prev) => ({ ...prev, [category]: { ...prev[category], [parentKey]: { ...prev[category][parentKey], [key]: value } } }));
  const handleSaveSettings = () => saveSettingsMutation.mutate(settings);

  const tabContent = {
    security: <SecurityTab settings={settings} handleSettingChange={handleSettingChange} handleNestedSettingChange={handleNestedSettingChange} />,
    notifications: <NotificationTab settings={settings} handleSettingChange={handleSettingChange} />,
    scanning: <ScanningTab settings={settings} handleSettingChange={handleSettingChange} />,
    api: <ApiTab settings={settings} handleSettingChange={handleSettingChange} />,
    system: <SystemTab user={user} />,
  };

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <PageHeader title="Settings" description="Manage your account preferences and platform configuration" icon={CogIcon} breadcrumb={["Settings"]} />
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="lg:w-64 flex-shrink-0">
              <GlassCard noPadding className="p-2 sticky top-8">
                <nav className="space-y-1">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                        className={`relative w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                          activeTab === tab.key ? "text-white" : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                        }`}>
                        {activeTab === tab.key && (
                          <motion.div layoutId="tab-indicator" className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-xl" initial={false} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
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
              <Button onClick={handleSaveSettings} disabled={saveSettingsMutation.isPending}
                className="w-full mt-6 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200">
                {saveSettingsMutation.isPending ? <><ArrowPathIcon className="h-4 w-4 mr-2 animate-spin inline" /> Saving...</> : "Save Settings"}
              </Button>
            </div>
            <div className="flex-1">
              <GlassCard>
                <motion.div key={activeTab} variants={contentAnim} initial="hidden" animate="show" transition={{ duration: 0.2 }}>
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
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/Settings.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/Settings.jsx
git commit -m "feat: Task 1 — Settings orchestrator with particles + animated sidebar"
```

---

### Task 2: SettingCard — Glassmorphism + Accent Stripe

**Files:**
- Rewrite: `frontend/src/components/settings/SettingCard.jsx`

- [ ] **Step 1: Rewrite SettingCard.jsx**

```jsx
import { motion } from "framer-motion";

const accentBorders = {
  warning: "border-l-yellow-500",
  danger: "border-l-red-500",
};

const SettingCard = ({ title, description, children, type = "default" }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.3 }}
    className={`bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 ${
      accentBorders[type] || "border-l-cyan-500/50"
    } border-l-4`}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="text-white font-medium mb-1">{title}</h4>
        {description && <p className="text-gray-400 text-sm mb-4">{description}</p>}
      </div>
      <div className="ml-4 flex-shrink-0">{children}</div>
    </div>
  </motion.div>
);

export default SettingCard;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/SettingCard.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/SettingCard.jsx
git commit -m "feat: Task 2 — SettingCard with glassmorphism + accent stripe"
```

---

### Task 3: Toggle — Smooth Spring Animation

**Files:**
- Rewrite: `frontend/src/components/settings/Toggle.jsx`

- [ ] **Step 1: Rewrite Toggle.jsx**

```jsx
import { motion } from "framer-motion";

const Toggle = ({ enabled, onChange, disabled = false, label }) => (
  <button
    role="switch"
    aria-checked={enabled}
    aria-label={label}
    onClick={() => !disabled && onChange(!enabled)}
    disabled={disabled}
    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
      enabled ? "bg-cyan-600/80" : "bg-gray-700/50"
    } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
  >
    <motion.span
      layout
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={`inline-block h-4 w-4 rounded-full bg-white shadow-sm ${
        enabled ? "translate-x-6" : "translate-x-1"
      }`}
    />
  </button>
);

export default Toggle;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/Toggle.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/Toggle.jsx
git commit -m "feat: Task 3 — Toggle with spring animation"
```

---

### Task 4: SecurityTab — Stagger Entry

**Files:**
- Rewrite: `frontend/src/components/settings/SecurityTab.jsx`

- [ ] **Step 1: Rewrite SecurityTab.jsx**

```jsx
import { motion } from "framer-motion";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const SecurityTab = ({ settings, handleSettingChange, handleNestedSettingChange }) => (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <h2 className="text-xl font-semibold text-white">Security Settings</h2>

    <motion.div variants={item}>
      <SettingCard title="Two-Factor Authentication" description="Add an extra layer of security to your account">
        <Toggle label="Two-Factor Authentication" enabled={settings.security.two_factor_enabled}
          onChange={(v) => handleSettingChange("security", "two_factor_enabled", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Login Notifications" description="Get notified when someone logs into your account">
        <Toggle label="Login Notifications" enabled={settings.security.login_notifications}
          onChange={(v) => handleSettingChange("security", "login_notifications", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Session Timeout" description="Automatically log out after a period of inactivity">
        <select value={settings.security.session_timeout}
          onChange={(e) => handleSettingChange("security", "session_timeout", parseInt(e.target.value))}
          className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white">
          <option value={15}>15 minutes</option>
          <option value={30}>30 minutes</option>
          <option value={60}>1 hour</option>
          <option value={120}>2 hours</option>
          <option value={480}>8 hours</option>
        </select>
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Password Policy" description="Configure password requirements for your organization" type="warning">
        <div className="space-y-3 w-full max-w-md">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Minimum Length</span>
            <input type="number" min="6" max="32" value={settings.security.password_policy.min_length}
              onChange={(e) => handleNestedSettingChange("security", "password_policy", "min_length", parseInt(e.target.value))}
              className="w-16 px-2 py-1 bg-gray-700/50 border border-gray-600/50 rounded text-white text-sm text-center" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Require Uppercase</span>
            <Toggle label="Require Uppercase" enabled={settings.security.password_policy.require_uppercase}
              onChange={(v) => handleNestedSettingChange("security", "password_policy", "require_uppercase", v)} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Require Numbers</span>
            <Toggle label="Require Numbers" enabled={settings.security.password_policy.require_numbers}
              onChange={(v) => handleNestedSettingChange("security", "password_policy", "require_numbers", v)} />
          </div>
        </div>
      </SettingCard>
    </motion.div>
  </motion.div>
);

export default SecurityTab;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/SecurityTab.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/SecurityTab.jsx
git commit -m "feat: Task 4 — SecurityTab with stagger entry"
```

---

### Task 5: NotificationTab — Stagger Entry

**Files:**
- Rewrite: `frontend/src/components/settings/NotificationTab.jsx`

- [ ] **Step 1: Rewrite NotificationTab.jsx**

```jsx
import { motion } from "framer-motion";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const NotificationTab = ({ settings, handleSettingChange }) => (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <h2 className="text-xl font-semibold text-white">Notification Settings</h2>

    <motion.div variants={item}>
      <SettingCard title="Email Notifications" description="Receive notifications via email">
        <Toggle label="Email Notifications" enabled={settings.notifications.email_enabled}
          onChange={(v) => handleSettingChange("notifications", "email_enabled", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Critical Security Alerts" description="Get immediately notified of critical vulnerabilities">
        <Toggle label="Critical Security Alerts" enabled={settings.notifications.critical_alerts}
          onChange={(v) => handleSettingChange("notifications", "critical_alerts", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Scan Completion" description="Get notified when security scans complete">
        <Toggle label="Scan Completion" enabled={settings.notifications.scan_completion}
          onChange={(v) => handleSettingChange("notifications", "scan_completion", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="New Vulnerabilities" description="Get notified when new vulnerabilities are detected">
        <Toggle label="New Vulnerabilities" enabled={settings.notifications.new_vulnerabilities}
          onChange={(v) => handleSettingChange("notifications", "new_vulnerabilities", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Weekly Reports" description="Receive weekly security summary reports">
        <Toggle label="Weekly Reports" enabled={settings.notifications.weekly_reports}
          onChange={(v) => handleSettingChange("notifications", "weekly_reports", v)} />
      </SettingCard>
    </motion.div>
  </motion.div>
);

export default NotificationTab;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/NotificationTab.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/NotificationTab.jsx
git commit -m "feat: Task 5 — NotificationTab with stagger entry"
```

---

### Task 6: ScanningTab — Stagger + Scanner Icons

**Files:**
- Rewrite: `frontend/src/components/settings/ScanningTab.jsx`

- [ ] **Step 1: Rewrite ScanningTab.jsx**

```jsx
import { motion } from "framer-motion";
import { CodeBracketIcon, EyeIcon, CubeIcon, ServerIcon } from "@heroicons/react/24/outline";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const scannerIcons = { sast: CodeBracketIcon, secrets: EyeIcon, container: CubeIcon, infrastructure: ServerIcon };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const ScanningTab = ({ settings, handleSettingChange }) => (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <h2 className="text-xl font-semibold text-white">Scanning Configuration</h2>

    <motion.div variants={item}>
      <SettingCard title="Auto-scan on Push" description="Automatically run scans when code is pushed to repositories">
        <Toggle label="Auto-scan on Push" enabled={settings.scanning.auto_scan_on_push}
          onChange={(v) => handleSettingChange("scanning", "auto_scan_on_push", v)} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Scan Timeout" description="Maximum time allowed for a scan to complete">
        <select value={settings.scanning.scan_timeout}
          onChange={(e) => handleSettingChange("scanning", "scan_timeout", parseInt(e.target.value))}
          className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white">
          <option value={180}>3 minutes</option>
          <option value={300}>5 minutes</option>
          <option value={600}>10 minutes</option>
          <option value={1200}>20 minutes</option>
          <option value={1800}>30 minutes</option>
        </select>
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Concurrent Scans" description="Maximum number of scans that can run simultaneously">
        <select value={settings.scanning.max_concurrent_scans}
          onChange={(e) => handleSettingChange("scanning", "max_concurrent_scans", parseInt(e.target.value))}
          className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white">
          <option value={1}>1 scan</option>
          <option value={2}>2 scans</option>
          <option value={3}>3 scans</option>
          <option value={5}>5 scans</option>
          <option value={10}>10 scans</option>
        </select>
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Enabled Scanners" description="Choose which security scanners to use by default">
        <div className="space-y-2 w-full max-w-md">
          {["sast", "secrets", "container", "infrastructure"].map((scanner) => {
            const Icon = scannerIcons[scanner];
            return (
              <div key={scanner} className="flex items-center justify-between py-1">
                <span className="text-sm text-gray-300 flex items-center gap-2">
                  {Icon && <Icon className="h-4 w-4 text-cyan-400" />}
                  <span className="capitalize">{scanner}</span>
                </span>
                <Toggle label={`${scanner} Analysis`} enabled={settings.scanning.enabled_scanners.includes(scanner)}
                  onChange={(enabled) => {
                    const newScanners = enabled ? [...settings.scanning.enabled_scanners, scanner] : settings.scanning.enabled_scanners.filter((s) => s !== scanner);
                    handleSettingChange("scanning", "enabled_scanners", newScanners);
                  }} />
              </div>
            );
          })}
        </div>
      </SettingCard>
    </motion.div>
  </motion.div>
);

export default ScanningTab;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/ScanningTab.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/ScanningTab.jsx
git commit -m "feat: Task 6 — ScanningTab with stagger + scanner icons"
```

---

### Task 7: ApiTab — Stagger + Copy Button

**Files:**
- Rewrite: `frontend/src/components/settings/ApiTab.jsx`

- [ ] **Step 1: Rewrite ApiTab.jsx**

```jsx
import { useState } from "react";
import { motion } from "framer-motion";
import { EyeIcon, EyeSlashIcon, ClipboardIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { Button } from "../../styles/components";
import SettingCard from "./SettingCard";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const ApiTab = ({ settings, handleSettingChange }) => {
  const [showApiKey, setShowApiKey] = useState(false);

  const handleCopyKey = () => {
    navigator.clipboard.writeText(settings.api.api_key);
    toast.success("API key copied to clipboard");
  };

  return (
    <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
      <h2 className="text-xl font-semibold text-white">API & Integration</h2>

      <motion.div variants={item}>
        <SettingCard title="API Key" description="Your API key for integrating with external services" type="warning">
          <div className="space-y-3 w-full max-w-md">
            <div className="flex items-center space-x-2">
              <div className="relative flex-1">
                <input type={showApiKey ? "text" : "password"} value={settings.api.api_key} readOnly
                  className="w-full px-3 py-2 pr-10 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white font-mono text-sm" />
                <button onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white">
                  {showApiKey ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                </button>
              </div>
              <button onClick={handleCopyKey}
                className="p-2 rounded-lg bg-gray-700/50 border border-gray-600/50 text-gray-400 hover:text-white hover:bg-gray-700 transition-all">
                <ClipboardIcon className="h-4 w-4" />
              </button>
              <Button onClick={() => toast.success("New API key generated!")} variant="warning" size="sm">Regenerate</Button>
            </div>
            <p className="text-xs text-yellow-400">Keep your API key secure. Don't share it or expose it in client-side code.</p>
          </div>
        </SettingCard>
      </motion.div>

      <motion.div variants={item}>
        <SettingCard title="Webhook URL" description="Receive scan results and notifications via webhook">
          <input type="url" value={settings.api.webhook_url}
            onChange={(e) => handleSettingChange("api", "webhook_url", e.target.value)}
            placeholder="https://your-domain.com/webhook"
            className="w-full max-w-md px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
        </SettingCard>
      </motion.div>

      <motion.div variants={item}>
        <SettingCard title="Rate Limiting" description="API request limits per hour">
          <div className="flex items-center space-x-3">
            <input type="number" value={settings.api.rate_limit}
              onChange={(e) => handleSettingChange("api", "rate_limit", parseInt(e.target.value))}
              className="w-24 px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
            <span className="text-gray-400">requests/hour</span>
          </div>
        </SettingCard>
      </motion.div>
    </motion.div>
  );
};

export default ApiTab;
```

- [ ] **Step 2: Lint**

Run: `npx eslint src/components/settings/ApiTab.jsx`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/ApiTab.jsx
git commit -m "feat: Task 7 — ApiTab with stagger + copy button"
```

---

### Task 8: SystemTab + SystemInfo — Stagger + Live Dots

**Files:**
- Rewrite: `frontend/src/components/settings/SystemTab.jsx`
- Rewrite: `frontend/src/components/settings/SystemInfo.jsx`

- [ ] **Step 1: Rewrite SystemTab.jsx**

```jsx
import { motion } from "framer-motion";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { Button } from "../../styles/components";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";
import SystemInfo from "./SystemInfo";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const SystemTab = ({ user }) => (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <h2 className="text-xl font-semibold text-white">System Information</h2>

    <motion.div variants={item}>
      <div className="bg-cyan-500/10 backdrop-blur-sm border border-cyan-500/30 rounded-xl p-6">
        <div className="flex items-start space-x-3">
          <InformationCircleIcon className="h-5 w-5 text-cyan-400 mt-0.5" />
          <div className="flex-1">
            <p className="text-cyan-400 font-medium">Platform Information</p>
            <SystemInfo />
          </div>
        </div>
      </div>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Maintenance Mode" description="Temporarily disable new scans for system maintenance" type="danger">
        <Toggle label="Maintenance Mode" enabled={false}
          onChange={() => toast("Maintenance mode requires admin privileges", { icon: "ℹ️" })}
          disabled={user?.role !== "admin"} />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Export Data" description="Download your security scan data and reports">
        <Button onClick={() => toast.success("Data export initiated! You'll receive an email when ready.")} variant="success">Export Data</Button>
      </SettingCard>
    </motion.div>
  </motion.div>
);

export default SystemTab;
```

- [ ] **Step 2: Rewrite SystemInfo.jsx**

```jsx
import { useState, useEffect } from "react";

const statusDot = {
  connected: "bg-green-500 shadow-lg shadow-green-500/30",
  disconnected: "bg-red-500 shadow-lg shadow-red-500/30",
  error: "bg-red-500 shadow-lg shadow-red-500/30",
  checking: "bg-yellow-500 shadow-lg shadow-yellow-500/30",
  offline: "bg-gray-500 shadow-lg shadow-gray-500/30",
};

const statusLabel = {
  connected: "Connected",
  disconnected: "Disconnected",
  error: "Error",
  checking: "Checking...",
  offline: "Offline",
};

const SystemInfo = () => {
  const [systemInfo, setSystemInfo] = useState({
    version: "Loading...", build: "Loading...", environment: "Loading...",
    database: { status: "checking", message: "Checking..." },
    scanners: { active: 0, total: 0 },
  });

  useEffect(() => {
    let cancelled = false;
    const fetchSystemInfo = async () => {
      try {
        const API_URL = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";
        const healthResponse = await fetch(`${API_URL}/api/health`);
        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          if (!cancelled) setSystemInfo({
            version: healthData.version || "1.0.0",
            build: healthData.build_date || new Date().toISOString().split("T")[0],
            environment: import.meta.env.DEV ? "Development" : "Production",
            database: { status: healthData.database?.connected ? "connected" : "disconnected", message: healthData.database?.connected ? "Connected" : "Disconnected" },
            scanners: { active: healthData.scanners?.active || 0, total: healthData.scanners?.total || 4 },
          });
        } else if (!cancelled) setSystemInfo((p) => ({ ...p, database: { status: "error", message: "Error checking" } }));
      } catch {
        if (!cancelled) setSystemInfo((p) => ({ ...p, version: "1.0.0", build: new Date().toISOString().split("T")[0], environment: import.meta.env.DEV ? "Development" : "Production", database: { status: "offline", message: "Offline" }, scanners: { active: 0, total: 4 } }));
      }
    };
    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 30000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const dbDot = statusDot[systemInfo.database.status] || statusDot.offline;
  const dbLabel = statusLabel[systemInfo.database.status] || "Unknown";

  return (
    <div className="mt-3 space-y-2 text-sm">
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Version</span>
        <span className="text-white font-mono text-xs">{systemInfo.version}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Build</span>
        <span className="text-white font-mono text-xs">{systemInfo.build}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Environment</span>
        <span className="text-white">{systemInfo.environment}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Database</span>
        <span className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${dbDot}`} />
          <span className="text-gray-300">{dbLabel}</span>
        </span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Scanners</span>
        <span className="flex items-center gap-2">
          <div className="h-1.5 w-16 bg-gray-700/50 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all"
              style={{ width: `${systemInfo.scanners.total > 0 ? (systemInfo.scanners.active / systemInfo.scanners.total) * 100 : 0}%` }} />
          </div>
          <span className={systemInfo.scanners.active > 0 ? "text-green-400" : "text-yellow-400"}>
            {systemInfo.scanners.active}/{systemInfo.scanners.total}
          </span>
        </span>
      </div>
    </div>
  );
};

export default SystemInfo;
```

- [ ] **Step 3: Lint both files**

Run:
```bash
npx eslint src/components/settings/SystemTab.jsx src/components/settings/SystemInfo.jsx
Expected: 0 errors, 0 warnings
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/settings/SystemTab.jsx frontend/src/components/settings/SystemInfo.jsx
git commit -m "feat: Task 8 — SystemTab + SystemInfo with stagger + live dots"
```

---

### Verification

- [ ] **Full lint**

Run: `npx eslint src/`
Expected: 0 errors, 0 warnings
