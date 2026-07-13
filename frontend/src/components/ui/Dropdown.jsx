/**
 * Dropdown - Accessible dropdown menu with animations
 */
import { useState, useRef, useEffect } from "react";
import { ChevronDownIcon } from "@heroicons/react/24/outline";
import { motion, AnimatePresence } from "framer-motion";

const Dropdown = ({
  trigger,
  items = [],
  position = "bottom-left",
  className = "",
  menuClassName = "",
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const positions = {
    "bottom-left": "top-full left-0 mt-2",
    "bottom-right": "top-full right-0 mt-2",
    "top-left": "bottom-full left-0 mb-2",
    "top-right": "bottom-full right-0 mb-2",
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const handleItemClick = (item) => {
    if (item.onClick) {
      item.onClick();
    }
    if (!item.keepOpen) {
      setIsOpen(false);
    }
  };

  return (
    <div ref={dropdownRef} className={`relative inline-block ${className}`}>
      {/* Trigger */}
      <div onClick={() => !disabled && setIsOpen(!isOpen)}>{trigger}</div>

      {/* Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={`
              absolute z-50 ${positions[position]}
              min-w-[200px] py-2
              bg-gray-800 border border-gray-700/50
              rounded-xl shadow-2xl
              backdrop-blur-xl
              ${menuClassName}
            `}
          >
            {items.map((item, index) => {
              if (item.divider) {
                return (
                  <div
                    key={index}
                    className="my-2 border-t border-gray-700/50"
                  />
                );
              }

              if (item.header) {
                return (
                  <div
                    key={index}
                    className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider"
                  >
                    {item.header}
                  </div>
                );
              }

              const Icon = item.icon;

              return (
                <button
                  key={index}
                  onClick={() => handleItemClick(item)}
                  disabled={item.disabled}
                  className={`
                    w-full flex items-center space-x-3 px-4 py-2.5
                    text-left text-sm
                    ${
                      item.disabled
                        ? "text-gray-500 cursor-not-allowed"
                        : item.danger
                        ? "text-red-400 hover:bg-red-500/10 hover:text-red-300"
                        : "text-gray-300 hover:bg-gray-700/50 hover:text-white"
                    }
                    transition-colors duration-150
                  `}
                >
                  {Icon && (
                    <Icon
                      className={`h-4 w-4 flex-shrink-0 ${
                        item.danger ? "text-red-400" : "text-gray-400"
                      }`}
                    />
                  )}
                  <span className="flex-1">{item.label}</span>
                  {item.shortcut && (
                    <span className="text-xs text-gray-500">
                      {item.shortcut}
                    </span>
                  )}
                  {item.badge && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-400">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Dropdown Button preset
export const DropdownButton = ({
  label,
  items,
  variant = "secondary",
  size = "md",
  icon: Icon,
  ...props
}) => {
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white border-blue-500",
    secondary:
      "bg-gray-800 hover:bg-gray-700 text-gray-300 border-gray-700 hover:text-white",
    ghost:
      "bg-transparent hover:bg-gray-800 text-gray-400 border-transparent hover:text-white",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-5 py-2.5 text-base",
  };

  return (
    <Dropdown
      trigger={
        <button
          className={`
            inline-flex items-center space-x-2
            ${sizes[size]} ${variants[variant]}
            border rounded-xl
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900
          `}
        >
          {Icon && <Icon className="h-4 w-4" />}
          <span>{label}</span>
          <ChevronDownIcon className="h-4 w-4" />
        </button>
      }
      items={items}
      {...props}
    />
  );
};

export default Dropdown;
