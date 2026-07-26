import { useSpring, useTransform, motion } from "framer-motion";

const Sparkline = ({ data = [], color }) => {
  if (data.length < 2) return null;
  const w = 80;
  const h = 24;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const points = data
    .map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="flex-shrink-0">
      <defs>
        <linearGradient id={`sf-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polygon points={`0,${h} ${points} ${w},${h}`} fill={`url(#sf-${color.replace("#", "")})`} />
    </svg>
  );
};

const MetricCard = ({
  icon: Icon,
  label,
  value = 0,
  trend,
  color = "#06b6d4",
  formatter = (v) => v,
}) => {
  const springValue = useSpring(0, { damping: 20, stiffness: 100 });
  const displayValue = useTransform(springValue, (v) => formatter(Math.round(v)));
  springValue.set(value);

  return (
    <motion.div
      className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 group hover:-translate-y-0.5 transition-all duration-200"
      whileHover={{ y: -2 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="p-2.5 rounded-xl" style={{ background: `${color}20` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        {trend && <Sparkline data={trend} color={color} />}
      </div>
      <motion.p className="text-2xl font-bold text-white font-mono">{displayValue}</motion.p>
      <p className="text-sm text-gray-400 mt-0.5">{label}</p>
    </motion.div>
  );
};

export default MetricCard;
