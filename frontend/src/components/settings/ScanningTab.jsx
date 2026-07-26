import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const ScanningTab = ({ settings, handleSettingChange }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-white">Scanning Configuration</h2>

    <SettingCard
      title="Auto-scan on Push"
      description="Automatically run scans when code is pushed to repositories"
    >
      <Toggle
        label="Auto-scan on Push"
        enabled={settings.scanning.auto_scan_on_push}
        onChange={(value) => handleSettingChange("scanning", "auto_scan_on_push", value)}
      />
    </SettingCard>

    <SettingCard title="Scan Timeout" description="Maximum time allowed for a scan to complete">
      <select
        value={settings.scanning.scan_timeout}
        onChange={(e) => handleSettingChange("scanning", "scan_timeout", parseInt(e.target.value))}
        className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
      >
        <option value={180}>3 minutes</option>
        <option value={300}>5 minutes</option>
        <option value={600}>10 minutes</option>
        <option value={1200}>20 minutes</option>
        <option value={1800}>30 minutes</option>
      </select>
    </SettingCard>

    <SettingCard
      title="Concurrent Scans"
      description="Maximum number of scans that can run simultaneously"
    >
      <select
        value={settings.scanning.max_concurrent_scans}
        onChange={(e) =>
          handleSettingChange("scanning", "max_concurrent_scans", parseInt(e.target.value))
        }
        className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
      >
        <option value={1}>1 scan</option>
        <option value={2}>2 scans</option>
        <option value={3}>3 scans</option>
        <option value={5}>5 scans</option>
        <option value={10}>10 scans</option>
      </select>
    </SettingCard>

    <SettingCard
      title="Enabled Scanners"
      description="Choose which security scanners to use by default"
    >
      <div className="space-y-2 w-full max-w-md">
        {["sast", "secrets", "container", "infrastructure"].map((scanner) => (
          <div key={scanner} className="flex items-center justify-between">
            <span className="text-sm text-gray-300 capitalize">{scanner} Analysis</span>
            <Toggle
              label={`${scanner} Analysis`}
              enabled={settings.scanning.enabled_scanners.includes(scanner)}
              onChange={(enabled) => {
                const newScanners = enabled
                  ? [...settings.scanning.enabled_scanners, scanner]
                  : settings.scanning.enabled_scanners.filter((s) => s !== scanner);
                handleSettingChange("scanning", "enabled_scanners", newScanners);
              }}
            />
          </div>
        ))}
      </div>
    </SettingCard>
  </div>
);

export default ScanningTab;
