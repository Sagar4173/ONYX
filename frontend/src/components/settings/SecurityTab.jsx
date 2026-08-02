import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const SecurityTab = ({ settings, handleSettingChange, handleNestedSettingChange }) => {
  const [ssoConfig, setSsoConfig] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetch(
      `${import.meta.env.DEV ? "http://127.0.0.1:8000" : ""}/api/auth/sso/google/config`
    )
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled) setSsoConfig(data);
      })
      .catch(() => {
        if (!cancelled) setSsoConfig(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <h2 className="text-xl font-semibold text-white">Security Settings</h2>

    <motion.div variants={item}>
      <SettingCard
        title="Google Sign-In (SSO)"
        description="Allow users to sign in with their Google account instead of a password"
      >
        <div className="flex items-center gap-3 w-full">
          <span
            className={`px-2.5 py-1 rounded-full text-xs font-medium ${
              ssoConfig?.enabled
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : "bg-gray-700/40 text-gray-400 border border-gray-600/40"
            }`}
          >
            {ssoConfig === null ? "Checking..." : ssoConfig.enabled ? "Enabled" : "Disabled"}
          </span>
          {ssoConfig?.enabled && ssoConfig.client_id && (
            <code className="text-xs text-gray-400 font-mono break-all min-w-0">
              {ssoConfig.client_id}
            </code>
          )}
          {ssoConfig !== null && !ssoConfig.enabled && (
            <span className="text-xs text-gray-500">
              Set GOOGLE_CLIENT_ID on the server to enable
            </span>
          )}
        </div>
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="Two-Factor Authentication"
        description="Add an extra layer of security to your account"
      >
        <Toggle
          label="Two-Factor Authentication"
          enabled={settings.security.two_factor_enabled}
          onChange={(v) => handleSettingChange("security", "two_factor_enabled", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="Login Notifications"
        description="Get notified when someone logs into your account"
      >
        <Toggle
          label="Login Notifications"
          enabled={settings.security.login_notifications}
          onChange={(v) => handleSettingChange("security", "login_notifications", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="Session Timeout"
        description="Automatically log out after a period of inactivity"
      >
        <select
          value={settings.security.session_timeout}
          onChange={(e) =>
            handleSettingChange("security", "session_timeout", parseInt(e.target.value))
          }
          className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
        >
          <option value={15}>15 minutes</option>
          <option value={30}>30 minutes</option>
          <option value={60}>1 hour</option>
          <option value={120}>2 hours</option>
          <option value={480}>8 hours</option>
        </select>
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="Password Policy"
        description="Configure password requirements for your organization"
        type="warning"
      >
        <div className="space-y-3 w-full max-w-md">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Minimum Length</span>
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
              className="w-16 px-2 py-1 bg-gray-700/50 border border-gray-600/50 rounded text-white text-sm text-center"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Require Uppercase</span>
            <Toggle
              label="Require Uppercase"
              enabled={settings.security.password_policy.require_uppercase}
              onChange={(v) =>
                handleNestedSettingChange("security", "password_policy", "require_uppercase", v)
              }
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Require Numbers</span>
            <Toggle
              label="Require Numbers"
              enabled={settings.security.password_policy.require_numbers}
              onChange={(v) =>
                handleNestedSettingChange("security", "password_policy", "require_numbers", v)
              }
            />
          </div>
        </div>
      </SettingCard>
    </motion.div>
  </motion.div>
);
};

export default SecurityTab;
