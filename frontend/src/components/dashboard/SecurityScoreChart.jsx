import { AnimatedCounter } from "../../styles/components";

const SecurityScoreChart = ({ score = 0, severitySummary, size = 160 }) => {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getScoreColor = (s) => {
    if (s >= 80) return { stroke: "url(#scoreGreen)", text: "text-emerald-400" };
    if (s >= 60) return { stroke: "url(#scoreYellow)", text: "text-amber-400" };
    return { stroke: "url(#scoreRed)", text: "text-red-400" };
  };

  const colors = getScoreColor(score);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <defs>
            <linearGradient id="scoreGreen" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
            <linearGradient id="scoreYellow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#eab308" />
            </linearGradient>
            <linearGradient id="scoreRed" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="100%" stopColor="#f43f5e" />
            </linearGradient>
          </defs>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(75, 85, 99, 0.3)"
            strokeWidth="12"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={colors.stroke}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${colors.text}`}>
            <AnimatedCounter value={score} />
          </span>
          <span className="text-xs text-gray-400 uppercase tracking-wider mt-1">Score</span>
        </div>
      </div>
      <p className="text-sm text-gray-400 mt-4 text-center">
        {score == null
          ? "Run your first scan to see your score"
          : score >= 80
            ? "Your security posture is healthy"
            : score >= 60
              ? "Some issues need attention"
              : "Critical issues detected"}
      </p>
      {severitySummary && (
        <div className="w-full mt-6 pt-6 border-t border-gray-800/50">
          <h4 className="text-sm font-medium text-white mb-4">Vulnerability Distribution</h4>
          {[
            {
              label: "Critical",
              count: severitySummary.critical || 0,
              color: "from-red-500 to-rose-500",
            },
            {
              label: "High",
              count: severitySummary.high || 0,
              color: "from-orange-500 to-amber-500",
            },
            {
              label: "Medium",
              count: severitySummary.medium || 0,
              color: "from-yellow-500 to-lime-500",
            },
            { label: "Low", count: severitySummary.low || 0, color: "from-blue-500 to-cyan-500" },
          ].map(({ label, count, color }) => (
            <div key={label} className="flex items-center justify-between text-sm py-1.5">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${color}`} />
                <span className="text-gray-400">{label}</span>
              </div>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SecurityScoreChart;
