import { motion } from "framer-motion";
import {
  CodeBracketIcon,
  EyeIcon,
  CubeIcon,
  ServerIcon,
} from "@heroicons/react/24/outline";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";

const scannerIcons = {
  sast: CodeBracketIcon,
  secrets: EyeIcon,
  container: CubeIcon,
  infrastructure: ServerIcon,
};

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const ScanningTab = ({ settings, handleSettingChange }) => (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <h2 className="text-xl font-semibold text-white">Scanning Configuration</h2>

    <motion.div variants={item}>
      <SettingCard
        title="Auto-scan on Push"
        description="Automatically run scans when code is pushed to repositories"
      >
        <Toggle
          label="Auto-scan on Push"
          enabled={settings.scanning.auto_scan_on_push}
          onChange={(v) => handleSettingChange("scanning", "auto_scan_on_push", v)}
        />
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
      <SettingCard title="Scan Timeout" description="Maximum time allowed for a scan to complete">
        <select
          value={settings.scanning.scan_timeout}
          onChange={(e) =>
            handleSettingChange("scanning", "scan_timeout", parseInt(e.target.value))
          }
          className="px-3 py-2 bg-gray-800 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
        >
          <option value={180}>3 minutes</option>
          <option value={300}>5 minutes</option>
          <option value={600}>10 minutes</option>
          <option value={1200}>20 minutes</option>
          <option value={1800}>30 minutes</option>
        </select>
      </SettingCard>
    </motion.div>

    <motion.div variants={item}>
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
    </motion.div>

    <motion.div variants={item}>
      <SettingCard
        title="Enabled Scanners"
        description="Choose which security scanners to use by default"
      >
        <div className="space-y-2 w-full max-w-md">
          {["sast", "secrets", "container", "infrastructure"].map((scanner) => {
            const Icon = scannerIcons[scanner];
            return (
              <div key={scanner} className="flex items-center justify-between py-1">
                <span className="text-sm text-gray-300 flex items-center gap-2">
                  {Icon && <Icon className="h-4 w-4 text-cyan-400" />}
                  <span className="capitalize">{scanner}</span>
                </span>
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
            );
          })}
        </div>
      </SettingCard>
    </motion.div>
  </motion.div>
);

export default ScanningTab;
