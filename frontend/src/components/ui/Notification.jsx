/**
 * Notification - Toast-style notification component
 */
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

const Notification = ({
  type = "info",
  title,
  message,
  duration = 5000,
  onClose,
  action,
  showProgress = true,
  position = "top-right",
  className = "",
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);

  const types = {
    success: {
      icon: CheckCircleIcon,
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      iconColor: "text-emerald-400",
      progressColor: "bg-emerald-500",
    },
    warning: {
      icon: ExclamationTriangleIcon,
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      iconColor: "text-amber-400",
      progressColor: "bg-amber-500",
    },
    error: {
      icon: XCircleIcon,
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      iconColor: "text-red-400",
      progressColor: "bg-red-500",
    },
    info: {
      icon: InformationCircleIcon,
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
      iconColor: "text-blue-400",
      progressColor: "bg-blue-500",
    },
  };

  const config = types[type];
  const Icon = config.icon;

  useEffect(() => {
    if (duration && duration > 0) {
      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
        setProgress(remaining);

        if (remaining === 0) {
          clearInterval(interval);
          handleClose();
        }
      }, 50);

      return () => clearInterval(interval);
    }
  }, [duration]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      if (onClose) onClose();
    }, 200);
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className={`
            relative w-full max-w-sm
            ${config.bg} ${config.border}
            border rounded-xl shadow-2xl
            backdrop-blur-xl
            overflow-hidden
            ${className}
          `}
        >
          <div className="p-4">
            <div className="flex items-start">
              <Icon className={`h-5 w-5 ${config.iconColor} flex-shrink-0`} />
              <div className="ml-3 flex-1">
                {title && (
                  <h4 className="text-sm font-semibold text-white">{title}</h4>
                )}
                {message && (
                  <p className={`text-sm text-gray-300 ${title ? "mt-1" : ""}`}>
                    {message}
                  </p>
                )}
                {action && <div className="mt-3">{action}</div>}
              </div>
              <button
                onClick={handleClose}
                className="
                  ml-3 p-1 rounded-lg
                  text-gray-400 hover:text-white
                  hover:bg-gray-700/50
                  transition-colors duration-150
                "
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Progress bar */}
          {showProgress && duration > 0 && (
            <div className="h-1 bg-gray-800">
              <motion.div
                initial={{ width: "100%" }}
                animate={{ width: `${progress}%` }}
                className={`h-full ${config.progressColor}`}
              />
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Notification Container for managing multiple notifications
export const NotificationContainer = ({
  notifications = [],
  position = "top-right",
  onRemove,
}) => {
  const positions = {
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-center": "top-4 left-1/2 -translate-x-1/2",
    "bottom-center": "bottom-4 left-1/2 -translate-x-1/2",
  };

  return (
    <div
      className={`
        fixed z-[100] ${positions[position]}
        flex flex-col space-y-3
        pointer-events-none
      `}
    >
      <AnimatePresence>
        {notifications.map((notification) => (
          <div key={notification.id} className="pointer-events-auto">
            <Notification
              {...notification}
              onClose={() => onRemove && onRemove(notification.id)}
            />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default Notification;
