import { motion } from "framer-motion";
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/solid";

const EVENT_ICONS = {
  scan_started: ArrowPathIcon,
  scan_completed: CheckCircleIcon,
  scan_failed: XCircleIcon,
  finding_detected: ExclamationTriangleIcon,
};

const EVENT_COLORS = {
  scan_started: "text-cyan-400",
  scan_completed: "text-green-400",
  scan_failed: "text-red-400",
  finding_detected: "text-yellow-400",
};

const ActivityTimeline = ({ events = [], isScanActive = false }) => {
  if (events.length === 0) {
    return (
      <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">Activity</h3>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            {isScanActive && (
              <div className="flex space-x-1 justify-center mb-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  />
                ))}
              </div>
            )}
            <p className="text-gray-500 text-sm">
              {isScanActive ? "Scan in progress..." : "No recent activity"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
      <h3 className="text-lg font-semibold text-white mb-4">Activity</h3>
      <div className="relative">
        <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-gradient-to-b from-cyan-500/40 to-violet-500/40" />
        <div className="space-y-4">
          {events.map((event, i) => {
            const Icon = EVENT_ICONS[event.type] || ArrowPathIcon;
            const color = EVENT_COLORS[event.type] || "text-gray-400";
            return (
              <motion.div
                key={event.id || i}
                className="flex items-start space-x-3"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05, type: "spring", damping: 20 }}
              >
                <div className={`relative z-10 p-1.5 rounded-full bg-gray-900 ${color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0 pt-0.5">
                  <p className="text-sm text-white">{event.description}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{event.timestamp}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ActivityTimeline;
