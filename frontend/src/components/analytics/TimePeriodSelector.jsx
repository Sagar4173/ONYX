import { motion } from "framer-motion";

const periods = [
  { value: 7, label: "7 Days" },
  { value: 30, label: "30 Days" },
  { value: 90, label: "90 Days" },
];

const TimePeriodSelector = ({ value, onChange }) => (
  <div className="flex items-center gap-1 bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-lg p-1">
    {periods.map((period) => (
      <button
        key={period.value}
        onClick={() => onChange(period.value)}
        className={`relative px-3 py-1.5 rounded-md text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
          value === period.value ? "text-white" : "text-gray-400 hover:text-white"
        }`}
      >
        {value === period.value && (
          <motion.div
            layoutId="period-indicator"
            className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-md"
            initial={false}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          />
        )}
        <span className="relative z-10">{period.label}</span>
      </button>
    ))}
  </div>
);

export default TimePeriodSelector;
