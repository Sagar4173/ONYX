import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const NotificationTab = ({ settings, handleSettingChange }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-white">Notification Settings</h2>

    <SettingCard title="Email Notifications" description="Receive notifications via email">
      <Toggle
        label="Email Notifications"
        enabled={settings.notifications.email_enabled}
        onChange={(value) => handleSettingChange("notifications", "email_enabled", value)}
      />
    </SettingCard>

    <SettingCard
      title="Critical Security Alerts"
      description="Get immediately notified of critical vulnerabilities"
    >
      <Toggle
        label="Critical Security Alerts"
        enabled={settings.notifications.critical_alerts}
        onChange={(value) => handleSettingChange("notifications", "critical_alerts", value)}
      />
    </SettingCard>

    <SettingCard title="Scan Completion" description="Get notified when security scans complete">
      <Toggle
        label="Scan Completion"
        enabled={settings.notifications.scan_completion}
        onChange={(value) => handleSettingChange("notifications", "scan_completion", value)}
      />
    </SettingCard>

    <SettingCard
      title="New Vulnerabilities"
      description="Get notified when new vulnerabilities are detected"
    >
      <Toggle
        label="New Vulnerabilities"
        enabled={settings.notifications.new_vulnerabilities}
        onChange={(value) => handleSettingChange("notifications", "new_vulnerabilities", value)}
      />
    </SettingCard>

    <SettingCard title="Weekly Reports" description="Receive weekly security summary reports">
      <Toggle
        label="Weekly Reports"
        enabled={settings.notifications.weekly_reports}
        onChange={(value) => handleSettingChange("notifications", "weekly_reports", value)}
      />
    </SettingCard>
  </div>
);

export default NotificationTab;
