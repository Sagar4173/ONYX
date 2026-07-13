/**
 * Progress - Progress bar and circular progress indicators
 */

import { motion } from "framer-motion";

const Progress = ({
  value = 0,
  max = 100,
  size = "md",
  variant = "primary",
  showLabel = false,
  label,
  animated = true,
  striped = false,
  className = "",
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const sizes = {
    xs: "h-1",
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
    xl: "h-4",
  };

  const variants = {
    primary: "from-blue-500 to-blue-600",
    success: "from-emerald-500 to-emerald-600",
    warning: "from-amber-500 to-amber-600",
    danger: "from-red-500 to-red-600",
    info: "from-cyan-500 to-cyan-600",
    purple: "from-purple-500 to-purple-600",
  };

  return (
    <div className={className}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-400">{label}</span>
          {showLabel && (
            <span className="text-sm font-medium text-white">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}

      <div
        className={`
          w-full ${sizes[size]} 
          bg-gray-700/50 rounded-full overflow-hidden
        `}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={
            animated ? { duration: 0.5, ease: "easeOut" } : { duration: 0 }
          }
          className={`
            h-full rounded-full
            bg-gradient-to-r ${variants[variant]}
            ${striped ? "progress-striped" : ""}
          `}
        />
      </div>

      <style>{`
        .progress-striped {
          background-image: linear-gradient(
            45deg,
            rgba(255, 255, 255, 0.15) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255, 255, 255, 0.15) 50%,
            rgba(255, 255, 255, 0.15) 75%,
            transparent 75%,
            transparent
          );
          background-size: 1rem 1rem;
          animation: progress-stripes 1s linear infinite;
        }

        @keyframes progress-stripes {
          from {
            background-position: 1rem 0;
          }
          to {
            background-position: 0 0;
          }
        }
      `}</style>
    </div>
  );
};

// Circular Progress
export const CircularProgress = ({
  value = 0,
  max = 100,
  size = 80,
  strokeWidth = 8,
  variant = "primary",
  showLabel = true,
  label,
  className = "",
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  const variants = {
    primary: "#3b82f6",
    success: "#10b981",
    warning: "#f59e0b",
    danger: "#ef4444",
    info: "#06b6d4",
    purple: "#8b5cf6",
  };

  return (
    <div className={`relative inline-flex ${className}`}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(75, 85, 99, 0.3)"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={variants[variant]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </svg>

      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-white">
            {Math.round(percentage)}%
          </span>
          {label && <span className="text-xs text-gray-400">{label}</span>}
        </div>
      )}
    </div>
  );
};

// Multi-segment Progress
export const SegmentedProgress = ({
  segments = [],
  size = "md",
  className = "",
}) => {
  const sizes = {
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
  };

  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <div
      className={`
        w-full ${sizes[size]} 
        bg-gray-700/50 rounded-full overflow-hidden
        flex
        ${className}
      `}
    >
      {segments.map((segment, index) => (
        <motion.div
          key={index}
          initial={{ width: 0 }}
          animate={{ width: `${(segment.value / total) * 100}%` }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
          className={`h-full ${segment.color || "bg-blue-500"}`}
          title={`${segment.label}: ${segment.value}`}
        />
      ))}
    </div>
  );
};

export default Progress;
