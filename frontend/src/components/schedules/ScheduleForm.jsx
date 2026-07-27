import { useState } from "react";
import { motion } from "framer-motion";
import { XMarkIcon } from "@heroicons/react/24/outline";

const CRON_PRESETS = [
  { label: "Every hour", value: "0 * * * *" },
  { label: "Every 6 hours", value: "0 */6 * * *" },
  { label: "Every 12 hours", value: "0 */12 * * *" },
  { label: "Daily at midnight", value: "0 0 * * *" },
  { label: "Daily at 2 AM", value: "0 2 * * *" },
  { label: "Weekly on Sunday midnight", value: "0 0 * * 0" },
  { label: "Monthly on 1st at midnight", value: "0 0 1 * *" },
  { label: "Custom", value: "custom" },
];

const SCAN_TYPE_OPTIONS = [
  { value: "sast", label: "SAST", desc: "Static analysis" },
  { value: "dast", label: "DAST", desc: "Dynamic analysis" },
  { value: "sca", label: "SCA", desc: "Dependency check" },
  { value: "secrets", label: "Secrets", desc: "Secret detection" },
  { value: "iac", label: "IaC", desc: "Infrastructure as Code" },
  { value: "container", label: "Container", desc: "Container scan" },
  { value: "comprehensive", label: "Comprehensive", desc: "All scanners" },
];

const TIMEZONES = [
  "UTC",
  "US/Eastern",
  "US/Central",
  "US/Mountain",
  "US/Pacific",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Kolkata",
  "Australia/Sydney",
];

const ScheduleForm = ({ initial, onSubmit, onCancel }) => {
  const [cronPreset, setCronPreset] = useState(
    initial?.cron_expression && CRON_PRESETS.some((p) => p.value === initial.cron_expression)
      ? initial.cron_expression
      : "custom"
  );
  const [customCron, setCustomCron] = useState(
    initial?.cron_expression && !CRON_PRESETS.some((p) => p.value === initial.cron_expression)
      ? initial.cron_expression
      : "0 2 * * *"
  );
  const [name, setName] = useState(initial?.name || "");
  const [description, setDescription] = useState(initial?.description || "");
  const [target, setTarget] = useState(initial?.target || "");
  const [scanTypes, setScanTypes] = useState(initial?.scan_types || ["sast", "secrets"]);
  const [timezone, setTimezone] = useState(initial?.timezone || "UTC");
  const [submitting, setSubmitting] = useState(false);

  const isEditing = !!initial;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !target.trim()) return;
    if (scanTypes.length === 0) return;

    setSubmitting(true);
    try {
      const cronExpression = cronPreset === "custom" ? customCron : cronPreset;
      await onSubmit({
        name: name.trim(),
        description: description.trim() || null,
        target: target.trim(),
        scan_types: scanTypes,
        cron_expression: cronExpression,
        timezone,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const toggleScanType = (val) => {
    if (val === "comprehensive") {
      setScanTypes(["comprehensive"]);
      return;
    }
    let updated;
    if (scanTypes.includes(val)) {
      updated = scanTypes.filter((s) => s !== val && s !== "comprehensive");
    } else {
      updated = [...scanTypes.filter((s) => s !== "comprehensive"), val];
    }
    setScanTypes(updated.length > 0 ? updated : ["sast"]);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="relative w-full max-w-lg mx-4 bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-2xl shadow-2xl"
      >
        <div className="flex items-center justify-between p-5 border-b border-gray-700/30">
          <h2 className="text-lg font-semibold text-white">
            {isEditing ? "Edit Schedule" : "New Schedule"}
          </h2>
          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-all"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Daily Security Scan"
              className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700/50 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700/50 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Target Repository URL</label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="https://github.com/org/repo.git"
              className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700/50 rounded-lg text-sm text-white placeholder-gray-500 font-mono focus:outline-none focus:border-cyan-500/50 transition-all"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Scan Types</label>
            <div className="grid grid-cols-2 gap-1.5">
              {SCAN_TYPE_OPTIONS.map((opt) => {
                const active = scanTypes.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggleScanType(opt.value)}
                    className={`text-left px-3 py-2 rounded-lg border text-xs transition-all ${
                      active
                        ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300"
                        : "bg-gray-800/80 border-gray-700/50 text-gray-400 hover:border-gray-600"
                    }`}
                  >
                    <div className="font-medium">{opt.label}</div>
                    <div className="text-[10px] opacity-70">{opt.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Schedule (Cron)</label>
            <div className="grid grid-cols-2 gap-1.5 mb-2">
              {CRON_PRESETS.map((preset) => {
                const active = cronPreset === preset.value;
                return (
                  <button
                    key={preset.value}
                    type="button"
                    onClick={() => setCronPreset(preset.value)}
                    className={`px-3 py-2 rounded-lg border text-xs transition-all ${
                      active
                        ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300"
                        : "bg-gray-800/80 border-gray-700/50 text-gray-400 hover:border-gray-600"
                    }`}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>
            {cronPreset === "custom" && (
              <div>
                <input
                  type="text"
                  value={customCron}
                  onChange={(e) => setCustomCron(e.target.value)}
                  placeholder="min hour dom mon dow"
                  className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700/50 rounded-lg text-sm text-white font-mono placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-all"
                />
                <p className="text-[10px] text-gray-500 mt-1">Format: minute hour day-of-month month day-of-week</p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700/50 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-all"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting || !name.trim() || !target.trim() || scanTypes.length === 0}
              className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium hover:from-cyan-400 hover:to-blue-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
            >
              {submitting ? "Saving..." : isEditing ? "Update Schedule" : "Create Schedule"}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-5 py-2.5 rounded-xl bg-gray-800 text-gray-300 text-sm font-medium hover:bg-gray-700 border border-gray-700/50 transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};

export default ScheduleForm;
