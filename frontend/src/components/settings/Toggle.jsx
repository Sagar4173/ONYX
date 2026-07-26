import { motion } from "framer-motion";

const Toggle = ({ enabled, onChange, disabled = false, label }) => (
  <button
    role="switch"
    aria-checked={enabled}
    aria-label={label}
    onClick={() => !disabled && onChange(!enabled)}
    disabled={disabled}
    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
      enabled ? "bg-cyan-600/80" : "bg-gray-700/50"
    } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
  >
    <motion.span
      layout
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={`inline-block h-4 w-4 rounded-full bg-white shadow-sm ${
        enabled ? "translate-x-6" : "translate-x-1"
      }`}
    />
  </button>
);

export default Toggle;
