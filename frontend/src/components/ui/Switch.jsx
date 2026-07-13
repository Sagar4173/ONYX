/**
 * Switch - Toggle switch component with smooth animations
 */

import { motion } from "framer-motion";

const Switch = ({
  checked = false,
  onChange,
  label,
  description,
  size = "md",
  disabled = false,
  variant = "primary",
  className = "",
}) => {
  const sizes = {
    sm: {
      track: "h-5 w-9",
      thumb: "h-4 w-4",
      translate: "translate-x-4",
    },
    md: {
      track: "h-6 w-11",
      thumb: "h-5 w-5",
      translate: "translate-x-5",
    },
    lg: {
      track: "h-7 w-14",
      thumb: "h-6 w-6",
      translate: "translate-x-7",
    },
  };

  const variants = {
    primary: "bg-blue-600",
    success: "bg-emerald-600",
    warning: "bg-amber-600",
    danger: "bg-red-600",
    purple: "bg-purple-600",
  };

  const handleChange = () => {
    if (!disabled && onChange) {
      onChange(!checked);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      handleChange();
    }
  };

  return (
    <label
      className={`
        flex items-start cursor-pointer select-none
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        ${className}
      `}
    >
      <div className="relative">
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          disabled={disabled}
          onClick={handleChange}
          onKeyDown={handleKeyDown}
          className={`
            relative inline-flex flex-shrink-0
            ${sizes[size].track}
            rounded-full cursor-pointer
            transition-colors duration-200 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900
            ${checked ? variants[variant] : "bg-gray-700"}
            ${disabled ? "cursor-not-allowed" : ""}
          `}
        >
          <motion.span
            layout
            className={`
              ${sizes[size].thumb}
              rounded-full bg-white shadow-lg
              pointer-events-none
            `}
            initial={false}
            animate={{
              x: checked
                ? parseInt(sizes[size].translate.replace(/[^0-9]/g, "")) * 4
                : 2,
              y: 2,
            }}
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
          />
        </button>
      </div>

      {(label || description) && (
        <div className="ml-3">
          {label && (
            <span
              className={`text-sm font-medium ${
                disabled ? "text-gray-500" : "text-white"
              }`}
            >
              {label}
            </span>
          )}
          {description && (
            <p
              className={`text-sm ${
                disabled ? "text-gray-600" : "text-gray-400"
              }`}
            >
              {description}
            </p>
          )}
        </div>
      )}
    </label>
  );
};

// Switch Group for multiple toggles
export const SwitchGroup = ({
  options = [],
  values = {},
  onChange,
  className = "",
}) => {
  const handleChange = (key, value) => {
    if (onChange) {
      onChange({ ...values, [key]: value });
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {options.map((option) => (
        <Switch
          key={option.key}
          checked={values[option.key] || false}
          onChange={(value) => handleChange(option.key, value)}
          label={option.label}
          description={option.description}
          disabled={option.disabled}
        />
      ))}
    </div>
  );
};

export default Switch;
