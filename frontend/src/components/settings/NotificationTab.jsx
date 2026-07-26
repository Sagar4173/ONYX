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
        <Toggle
          label="Email Notifications"
          enabled={settings.notifications.email_enabled}
          onChange={(v) => handleSettingChange("notifications", "email_enabled", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="Critical Security Alerts"
        description="Get immediately notified of critical vulnerabilities"
      >
        <Toggle
          label="Critical Security Alerts"
          enabled={settings.notifications.critical_alerts}
          onChange={(v) => handleSettingChange("notifications", "critical_alerts", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Scan Completion" description="Get notified when security scans complete">
        <Toggle
          label="Scan Completion"
          enabled={settings.notifications.scan_completion}
          onChange={(v) => handleSettingChange("notifications", "scan_completion", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="New Vulnerabilities"
        description="Get notified when new vulnerabilities are detected"
      >
        <Toggle
          label="New Vulnerabilities"
          enabled={settings.notifications.new_vulnerabilities}
          onChange={(v) => handleSettingChange("notifications", "new_vulnerabilities", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Weekly Reports" description="Receive weekly security summary reports">
        <Toggle
          label="Weekly Reports"
          enabled={settings.notifications.weekly_reports}
          onChange={(v) => handleSettingChange("notifications", "weekly_reports", v)}
        />
      </SettingCard>
    </motion.div>
  </motion.div>
);

export default NotificationTab;
