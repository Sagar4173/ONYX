/**
 * FloatingActionButton - Floating action button with menu
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PlusIcon, XMarkIcon } from "@heroicons/react/24/outline";

const FloatingActionButton = ({
  icon: Icon = PlusIcon,
  actions = [],
  position = "bottom-right",
  variant = "primary",
  size = "lg",
  tooltip,
  onClick,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positions = {
    "bottom-right": "bottom-6 right-6",
    "bottom-left": "bottom-6 left-6",
    "bottom-center": "bottom-6 left-1/2 -translate-x-1/2",
  };

  const variants = {
    primary:
      "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 shadow-blue-500/30",
    success:
      "bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 shadow-emerald-500/30",
    danger:
      "bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 shadow-red-500/30",
    purple:
      "bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 shadow-purple-500/30",
  };

  const sizes = {
    md: "w-12 h-12",
    lg: "w-14 h-14",
    xl: "w-16 h-16",
  };

  const iconSizes = {
    md: "h-5 w-5",
    lg: "h-6 w-6",
    xl: "h-7 w-7",
  };

  const handleClick = () => {
    if (actions.length > 0) {
      setIsOpen(!isOpen);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div className={`fixed ${positions[position]} z-50 ${className}`}>
      {/* Actions menu */}
      <AnimatePresence>
        {isOpen && actions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.8 }}
            className="absolute bottom-full mb-4 right-0 space-y-3"
          >
            {actions.map((action, index) => {
              const ActionIcon = action.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-end space-x-3"
                >
                  {action.label && (
                    <span className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm text-white shadow-lg whitespace-nowrap">
                      {action.label}
                    </span>
                  )}
                  <button
                    onClick={() => {
                      action.onClick?.();
                      setIsOpen(false);
                    }}
                    className={`
                      ${sizes.md} rounded-full
                      flex items-center justify-center
                      ${
                        action.variant
                          ? variants[action.variant]
                          : "bg-gray-700 hover:bg-gray-600"
                      }
                      text-white shadow-lg
                      transition-all duration-200
                      hover:scale-110
                    `}
                  >
                    {ActionIcon && <ActionIcon className={iconSizes.md} />}
                  </button>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main FAB */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleClick}
        className={`
          ${sizes[size]} rounded-full
          flex items-center justify-center
          ${variants[variant]}
          text-white shadow-xl
          transition-all duration-300
          focus:outline-none focus:ring-4 focus:ring-blue-500/30
        `}
        title={tooltip}
      >
        <motion.div
          animate={{ rotate: isOpen ? 45 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <Icon className={iconSizes[size]} />
        </motion.div>
      </motion.button>
    </div>
  );
};

export default FloatingActionButton;
