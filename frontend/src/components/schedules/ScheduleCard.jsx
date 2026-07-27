import { useState } from "react";
import { motion } from "framer-motion";
import {
  PlayIcon,
  PauseIcon,
  TrashIcon,
  ClockIcon,
  ArrowPathIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import { schedulesAPI } from "../../services/api";
import toast from "react-hot-toast";

const CRON_PRESETS = [
  { label: "Every hour", value: "0 * * * *" },
  { label: "Daily at midnight", value: "0 0 * * *" },
  { label: "Daily at 2 AM", value: "0 2 * * *" },
  { label: "Weekly on Sunday", value: "0 0 * * 0" },
  { label: "Every 6 hours", value: "0 */6 * * *" },
  { label: "Every 12 hours", value: "0 */12 * * *" },
  { label: "Custom", value: "custom" },
];

export const getCronDescription = (cron) => {
  const preset = CRON_PRESETS.find((p) => p.value === cron);
  if (preset && preset.label !== "Custom") return preset.label;
  const parts = cron.split(" ");
  if (parts.length !== 5) return cron;
  const [min, hour, dom, mon, dow] = parts;
  if (min === "0" && hour === "2" && dom === "*" && mon === "*" && dow === "*") return "Daily at 2 AM";
  if (min === "0" && hour === "0" && dom === "*" && mon === "*" && dow === "*") return "Daily at midnight";
  if (min === "0" && hour === "*" && dom === "*" && mon === "*" && dow === "*") return "Every hour";
  return cron;
};

export const getStatusBadge = (status) => {
  const badges = {
    success: "bg-green-500/20 text-green-300 border-green-500/30",
    failed: "bg-red-500/20 text-red-300 border-red-500/30",
    running: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
    completed: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  };
  const cls = badges[status] || "bg-gray-500/20 text-gray-300 border-gray-500/30";
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {status || "pending"}
    </span>
  );
};

const ScheduleCard = ({ schedule, onUpdate, onDelete }) => {
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleToggle = async () => {
    setToggling(true);
    try {
      await schedulesAPI.toggleSchedule(schedule.id);
      toast.success(schedule.enabled ? "Schedule paused" : "Schedule resumed");
      if (onUpdate) onUpdate();
    } catch (err) {
      toast.error("Failed to toggle schedule");
    } finally {
      setToggling(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await schedulesAPI.deleteSchedule(schedule.id);
      toast.success("Schedule deleted");
      if (onDelete) onDelete();
    } catch (err) {
      toast.error("Failed to delete schedule");
    } finally {
      setDeleting(false);
    }
  };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await schedulesAPI.triggerRun(schedule.id);
      toast.success("Scan triggered");
      if (onUpdate) onUpdate();
    } catch (err) {
      toast.error("Failed to trigger scan");
    } finally {
      setTriggering(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Never";
    const d = new Date(dateStr);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString();
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 rounded-xl p-5 hover:border-cyan-500/30 transition-all duration-300"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
            <ClockIcon className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{schedule.name}</h3>
            {schedule.description && (
              <p className="text-xs text-gray-400 mt-0.5">{schedule.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge(schedule.last_status)}
          <span
            className={`w-2 h-2 rounded-full ${
              schedule.enabled ? "bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]" : "bg-gray-500"
            }`}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4 text-xs">
        <div>
          <span className="text-gray-500">Target</span>
          <p className="text-gray-300 truncate mt-0.5 font-mono text-[11px]">{schedule.target}</p>
        </div>
        <div>
          <span className="text-gray-500">Schedule</span>
          <p className="text-gray-300 mt-0.5">{getCronDescription(schedule.cron_expression)}</p>
        </div>
        <div>
          <span className="text-gray-500">Scan Types</span>
          <div className="flex gap-1 mt-1 flex-wrap">
            {(schedule.scan_types || []).map((st) => (
              <span
                key={st}
                className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 text-[10px] uppercase tracking-wider"
              >
                {st}
              </span>
            ))}
          </div>
        </div>
        <div>
          <span className="text-gray-500">Next Run</span>
          <p className="text-gray-300 mt-0.5">{formatDate(schedule.next_run)}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-3 border-t border-gray-700/30">
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 border border-cyan-500/20 text-xs font-medium transition-all disabled:opacity-50"
        >
          <PlayIcon className="w-3.5 h-3.5" />
          Run Now
        </button>
        <button
          onClick={handleToggle}
          disabled={toggling}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700/50 text-xs font-medium transition-all disabled:opacity-50"
        >
          {schedule.enabled ? (
            <PauseIcon className="w-3.5 h-3.5" />
          ) : (
            <ArrowPathIcon className="w-3.5 h-3.5" />
          )}
          {schedule.enabled ? "Pause" : "Resume"}
        </button>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-gray-300 border border-gray-700/50 text-xs font-medium transition-all"
        >
          <ChevronDownIcon
            className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
          History
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-300 hover:bg-red-500/20 border border-red-500/20 text-xs font-medium transition-all ml-auto disabled:opacity-50"
        >
          <TrashIcon className="w-3.5 h-3.5" />
          Delete
        </button>
      </div>

      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          className="mt-3 pt-3 border-t border-gray-700/30"
        >
          <ScheduleHistory scheduleId={schedule.id} />
        </motion.div>
      )}
    </motion.div>
  );
};

const ScheduleHistory = ({ scheduleId }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useState(() => {
    const load = async () => {
      try {
        const data = await schedulesAPI.getScheduleHistory(scheduleId);
        setHistory(data.history || []);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [scheduleId]);

  if (loading) {
    return <div className="text-xs text-gray-500 py-2 text-center">Loading history...</div>;
  }

  if (history.length === 0) {
    return <div className="text-xs text-gray-500 py-2 text-center">No runs yet</div>;
  }

  return (
    <div className="space-y-1.5">
      {history.map((run, i) => (
        <div key={run.scan_id || i} className="flex items-center justify-between text-xs py-1.5 px-2 rounded bg-gray-800/50">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">{run.scan_id?.slice(0, 8)}...</span>
            {getStatusBadge(run.status)}
          </div>
          <div className="flex items-center gap-3 text-gray-500">
            <span>{run.total_findings || 0} findings</span>
            <span>{run.created_at ? new Date(run.created_at).toLocaleTimeString() : ""}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ScheduleCard;
