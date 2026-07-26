import { motion } from "framer-motion";
import {
  ShieldCheckIcon,
  CodeBracketIcon,
  KeyIcon,
  CubeIcon,
  CloudIcon,
  BeakerIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

const STAGE_ICONS = [
  ShieldCheckIcon,
  CodeBracketIcon,
  KeyIcon,
  CubeIcon,
  CloudIcon,
  BeakerIcon,
  SparklesIcon,
];

const STAGES = [
  { label: "Initialize", min: 0, max: 10 },
  { label: "Clone", min: 10, max: 20 },
  { label: "SAST", min: 20, max: 35 },
  { label: "Secrets", min: 35, max: 50 },
  { label: "Dependencies", min: 50, max: 70 },
  { label: "Container", min: 70, max: 90 },
  { label: "AI Analysis", min: 90, max: 100 },
];

const NodeState = ({ stage, idx, progress }) => {
  const isActive = progress >= stage.min && progress < stage.max;
  const isComplete = progress >= stage.max;
  const Icon = STAGE_ICONS[idx];

  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: idx * 0.1, type: "spring", damping: 15 }}
    >
      <motion.div
        className={`relative flex items-center justify-center w-14 h-14 rounded-xl border-2 transition-colors ${
          isComplete
            ? "bg-green-900/40 border-green-500 shadow-lg shadow-green-500/20"
            : isActive
              ? "bg-cyan-900/40 border-cyan-400 shadow-lg shadow-cyan-500/30"
              : "bg-gray-800/50 border-gray-700"
        }`}
        animate={isActive ? { scale: [1, 1.1, 1] } : {}}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        {isComplete ? (
          <motion.svg
            className="w-6 h-6 text-green-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.5, type: "spring" }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.5}
              d="M5 13l4 4L19 7"
            />
          </motion.svg>
        ) : (
          <Icon className={`w-6 h-6 ${isActive ? "text-cyan-400" : "text-gray-500"}`} />
        )}
        {isActive && (
          <div className="absolute inset-0 rounded-xl animate-ping opacity-20 bg-cyan-400" />
        )}
      </motion.div>
      <span
        className={`mt-2 text-xs font-medium ${isComplete ? "text-green-400" : isActive ? "text-cyan-400" : "text-gray-500"}`}
      >
        {stage.label}
      </span>
    </motion.div>
  );
};

const ScanPipeline = ({ scanProgress = 0, activeScan, projectName }) => {
  if (!activeScan) return null;

  return (
    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Scan Pipeline</h3>
          <p className="text-sm text-gray-400">{projectName || "Repository"}</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded-full text-xs font-medium border border-cyan-500/30 animate-pulse">
            {activeScan.status?.toUpperCase() || "RUNNING"}
          </span>
          <span className="text-2xl font-bold text-cyan-400">{Math.round(scanProgress)}%</span>
        </div>
      </div>

      <div className="relative">
        <svg
          className="absolute top-7 left-0 w-full h-8 pointer-events-none"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="activeTracer" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
          <line
            x1="30"
            y1="4"
            x2="100%"
            y2="4"
            stroke="#374151"
            strokeWidth="2"
            strokeDasharray="4 4"
          />
          <line
            x1="30"
            y1="4"
            x2={`${30 + (scanProgress / 100) * 90}%`}
            y2="4"
            stroke="url(#activeTracer)"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        </svg>

        <div className="flex justify-between relative">
          {STAGES.map((stage, idx) => (
            <div key={idx} className="flex flex-col items-center relative z-10">
              <NodeState stage={stage} idx={idx} progress={scanProgress} />
            </div>
          ))}
        </div>
      </div>

      {activeScan.current_scanner && (
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="flex items-center space-x-2 text-sm">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-gray-400">Current:</span>
            <span className="text-cyan-300 font-medium">{activeScan.current_scanner}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanPipeline;
