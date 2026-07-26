const periods = [
  { value: 7, label: "7 Days" },
  { value: 30, label: "30 Days" },
  { value: 90, label: "90 Days" },
];

const TimePeriodSelector = ({ value, onChange }) => (
  <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg p-1">
    {periods.map((period) => (
      <button
        key={period.value}
        onClick={() => onChange(period.value)}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
          value === period.value
            ? "bg-cyan-500 text-white"
            : "text-gray-400 hover:text-white hover:bg-gray-700/50"
        }`}
      >
        {period.label}
      </button>
    ))}
  </div>
);

export default TimePeriodSelector;
