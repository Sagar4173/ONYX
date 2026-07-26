const HealthScoreRing = ({ score }) => {
  const radius = 60;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (score >= 80) return { stroke: "#10b981", text: "text-green-400", bg: "bg-green-500/20" };
    if (score >= 60) return { stroke: "#f59e0b", text: "text-amber-400", bg: "bg-amber-500/20" };
    return { stroke: "#ef4444", text: "text-red-400", bg: "bg-red-500/20" };
  };

  const colors = getColor();

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg height={radius * 2} width={radius * 2} className="transform -rotate-90">
        <circle
          stroke="#374151"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={colors.stroke}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={`${circumference} ${circumference}`}
          style={{ strokeDashoffset, transition: "stroke-dashoffset 0.5s ease-in-out" }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className={`text-2xl font-bold ${colors.text}`}>{score}</span>
        <span className="text-xs text-gray-500">Health</span>
      </div>
    </div>
  );
};

export default HealthScoreRing;
