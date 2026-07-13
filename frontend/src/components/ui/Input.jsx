/**
 * Input - Enhanced input component with variants, validation, and animations
 */
import { forwardRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ExclamationCircleIcon,
  CheckCircleIcon,
  EyeIcon,
  EyeSlashIcon,
} from "@heroicons/react/24/outline";

const Input = forwardRef(
  (
    {
      label,
      error,
      success,
      hint,
      icon: Icon,
      iconPosition = "left",
      variant = "default",
      size = "md",
      type = "text",
      fullWidth = true,
      disabled = false,
      required = false,
      showPasswordToggle = false,
      className = "",
      inputClassName = "",
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const [isFocused, setIsFocused] = useState(false);

    const isPassword = type === "password";
    const inputType = isPassword && showPassword ? "text" : type;

    const variants = {
      default: `
      bg-gray-800/50 border border-gray-700
      focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20
    `,
      glass: `
      glass-card border-white/10
      focus-within:border-white/20 focus-within:ring-2 focus-within:ring-white/10
    `,
      minimal: `
      bg-transparent border-b-2 border-gray-700 rounded-none
      focus-within:border-blue-500
    `,
      filled: `
      bg-gray-700/50 border border-transparent
      focus-within:bg-gray-700/70 focus-within:border-blue-500
    `,
    };

    const sizes = {
      sm: {
        wrapper: "h-9",
        padding: Icon
          ? iconPosition === "left"
            ? "pl-9 pr-3"
            : "pl-3 pr-9"
          : "px-3",
        text: "text-sm",
        icon: "h-4 w-4",
        label: "text-xs",
      },
      md: {
        wrapper: "h-11",
        padding: Icon
          ? iconPosition === "left"
            ? "pl-10 pr-4"
            : "pl-4 pr-10"
          : "px-4",
        text: "text-sm",
        icon: "h-5 w-5",
        label: "text-sm",
      },
      lg: {
        wrapper: "h-13",
        padding: Icon
          ? iconPosition === "left"
            ? "pl-11 pr-5"
            : "pl-5 pr-11"
          : "px-5",
        text: "text-base",
        icon: "h-5 w-5",
        label: "text-base",
      },
    };

    const sizeConfig = sizes[size];

    const getStateStyles = () => {
      if (error)
        return "border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20";
      if (success)
        return "border-emerald-500 focus-within:border-emerald-500 focus-within:ring-emerald-500/20";
      return "";
    };

    return (
      <div className={`${fullWidth ? "w-full" : ""} ${className}`}>
        {/* Label */}
        {label && (
          <label
            className={`block ${sizeConfig.label} font-medium text-gray-300 mb-1.5`}
          >
            {label}
            {required && <span className="text-red-400 ml-1">*</span>}
          </label>
        )}

        {/* Input wrapper */}
        <div className="relative">
          <div
            className={`
            relative flex items-center rounded-xl transition-all duration-200
            ${sizeConfig.wrapper}
            ${variants[variant]}
            ${getStateStyles()}
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
          >
            {/* Left icon */}
            {Icon && iconPosition === "left" && (
              <div className="absolute left-3 flex items-center pointer-events-none">
                <Icon className={`${sizeConfig.icon} text-gray-400`} />
              </div>
            )}

            {/* Input */}
            <input
              ref={ref}
              type={inputType}
              disabled={disabled}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              className={`
              w-full h-full bg-transparent border-none outline-none
              text-white placeholder-gray-500 rounded-xl
              ${sizeConfig.padding}
              ${sizeConfig.text}
              ${isPassword && showPasswordToggle ? "pr-10" : ""}
              ${inputClassName}
            `}
              {...props}
            />

            {/* Right icon */}
            {Icon && iconPosition === "right" && !isPassword && (
              <div className="absolute right-3 flex items-center pointer-events-none">
                <Icon className={`${sizeConfig.icon} text-gray-400`} />
              </div>
            )}

            {/* Password toggle */}
            {isPassword && showPasswordToggle && (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 text-gray-400 hover:text-gray-300 transition-colors"
              >
                {showPassword ? (
                  <EyeSlashIcon className={sizeConfig.icon} />
                ) : (
                  <EyeIcon className={sizeConfig.icon} />
                )}
              </button>
            )}

            {/* Status icon */}
            {(error || success) && !isPassword && (
              <div className="absolute right-3 flex items-center">
                {error && (
                  <ExclamationCircleIcon
                    className={`${sizeConfig.icon} text-red-400`}
                  />
                )}
                {success && (
                  <CheckCircleIcon
                    className={`${sizeConfig.icon} text-emerald-400`}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Helper text */}
        <AnimatePresence mode="wait">
          {(error || success || hint) && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className={`mt-1.5 text-xs ${
                error
                  ? "text-red-400"
                  : success
                  ? "text-emerald-400"
                  : "text-gray-500"
              }`}
            >
              {error || success || hint}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

Input.displayName = "Input";

/**
 * TextArea - Multi-line input
 */
export const TextArea = forwardRef(
  (
    {
      label,
      error,
      success,
      hint,
      rows = 4,
      resize = true,
      variant = "default",
      fullWidth = true,
      disabled = false,
      required = false,
      className = "",
      ...props
    },
    ref
  ) => {
    const variants = {
      default: `
      bg-gray-800/50 border border-gray-700
      focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20
    `,
      glass: `
      glass-card border-white/10
      focus:border-white/20 focus:ring-2 focus:ring-white/10
    `,
    };

    const getStateStyles = () => {
      if (error)
        return "border-red-500 focus:border-red-500 focus:ring-red-500/20";
      if (success)
        return "border-emerald-500 focus:border-emerald-500 focus:ring-emerald-500/20";
      return "";
    };

    return (
      <div className={`${fullWidth ? "w-full" : ""} ${className}`}>
        {label && (
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            {label}
            {required && <span className="text-red-400 ml-1">*</span>}
          </label>
        )}

        <textarea
          ref={ref}
          rows={rows}
          disabled={disabled}
          className={`
          w-full px-4 py-3 rounded-xl outline-none
          text-white placeholder-gray-500 text-sm
          transition-all duration-200
          ${variants[variant]}
          ${getStateStyles()}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          ${resize ? "resize-y" : "resize-none"}
        `}
          {...props}
        />

        <AnimatePresence mode="wait">
          {(error || success || hint) && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className={`mt-1.5 text-xs ${
                error
                  ? "text-red-400"
                  : success
                  ? "text-emerald-400"
                  : "text-gray-500"
              }`}
            >
              {error || success || hint}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

TextArea.displayName = "TextArea";

/**
 * Select - Dropdown select input
 */
export const Select = forwardRef(
  (
    {
      label,
      options = [],
      error,
      placeholder = "Select an option",
      variant = "default",
      size = "md",
      fullWidth = true,
      disabled = false,
      required = false,
      className = "",
      ...props
    },
    ref
  ) => {
    const variants = {
      default: `
      bg-gray-800/50 border border-gray-700
      focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20
    `,
      glass: `
      glass-card border-white/10
      focus:border-white/20
    `,
    };

    const sizes = {
      sm: "h-9 text-sm px-3",
      md: "h-11 text-sm px-4",
      lg: "h-13 text-base px-5",
    };

    return (
      <div className={`${fullWidth ? "w-full" : ""} ${className}`}>
        {label && (
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            {label}
            {required && <span className="text-red-400 ml-1">*</span>}
          </label>
        )}

        <select
          ref={ref}
          disabled={disabled}
          className={`
          w-full rounded-xl outline-none appearance-none cursor-pointer
          text-white bg-no-repeat bg-right
          transition-all duration-200
          ${variants[variant]}
          ${sizes[size]}
          ${error ? "border-red-500" : ""}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
          style={{
            backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
            backgroundPosition: "right 0.75rem center",
            backgroundSize: "1.5em 1.5em",
            paddingRight: "2.5rem",
          }}
          {...props}
        >
          <option value="" disabled className="bg-gray-800 text-gray-500">
            {placeholder}
          </option>
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              className="bg-gray-800 text-white"
            >
              {option.label}
            </option>
          ))}
        </select>

        {error && <p className="mt-1.5 text-xs text-red-400">{error}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";

export default Input;
