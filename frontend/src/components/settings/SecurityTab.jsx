import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const SecurityTab = ({ settings, handleSettingChange, handleNestedSettingChange }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-white">Security Settings</h2>

    <SettingCard
      title="Two-Factor Authentication"
      description="Add an extra layer of security to your account"
    >
      <Toggle
        label="Two-Factor Authentication"
        enabled={settings.security.two_factor_enabled}
        onChange={(value) => handleSettingChange("security", "two_factor_enabled", value)}
      />
    </SettingCard>

    <SettingCard
      title="Login Notifications"
      description="Get notified when someone logs into your account"
    >
      <Toggle
        label="Login Notifications"
        enabled={settings.security.login_notifications}
        onChange={(value) => handleSettingChange("security", "login_notifications", value)}
      />
    </SettingCard>

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

    <SettingCard
      title="Password Policy"
      description="Configure password requirements for your organization"
      type="warning"
    >
      <div className="space-y-3 w-full max-w-md">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-300">Minimum Length (8)</span>
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
          <span className="text-sm text-gray-300">Require Uppercase</span>
          <Toggle
            label="Require Uppercase"
            enabled={settings.security.password_policy.require_uppercase}
            onChange={(value) =>
              handleNestedSettingChange("security", "password_policy", "require_uppercase", value)
            }
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-300">Require Numbers</span>
          <Toggle
            label="Require Numbers"
            enabled={settings.security.password_policy.require_numbers}
            onChange={(value) =>
              handleNestedSettingChange("security", "password_policy", "require_numbers", value)
            }
          />
        </div>
      </div>
    </SettingCard>
  </div>
);

export default SecurityTab;
