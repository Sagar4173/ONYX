import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { CodeBracketIcon, EyeIcon, CubeIcon, ServerIcon } from "@heroicons/react/24/outline";

const scanTypes = [
  {
    key: "sast",
    label: "Static Analysis",
    icon: CodeBracketIcon,
    color: "#06b6d4",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    key: "secrets",
    label: "Secret Detection",
    icon: EyeIcon,
    color: "#a855f7",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    key: "container",
    label: "Container Scan",
    icon: CubeIcon,
    color: "#10b981",
    gradient: "from-green-500 to-emerald-500",
  },
  {
    key: "infrastructure",
    label: "Infrastructure",
    icon: ServerIcon,
    color: "#f97316",
    gradient: "from-orange-500 to-red-500",
  },
];

const getCount = (data, key) => {
  if (!data) return 0;
  if (typeof data[key] === "number") return data[key];
  if (data[key]?.total_runs) return data[key].total_runs;
  const map = {
    sast: ["semgrep", "bandit", "eslint"],
    secrets: ["gitleaks", "trufflehog"],
    container: ["trivy", "grype"],
    infrastructure: ["checkov", "tfsec"],
  };
  return (map[key] || []).reduce((a, s) => a + (data[s]?.total_runs || 0), 0);
};

const getTotal = (data) => {
  if (!data) return 0;
  return scanTypes.reduce((a, t) => a + getCount(data, t.key), 0);
};

const Donut = ({ value, total, color }) => {
  const ref = useRef();
  useEffect(() => {
    const cvs = ref.current;
    if (!cvs) return;
    const ctx = cvs.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const s = 75;
    cvs.width = s * dpr;
    cvs.height = s * dpr;
    cvs.style.width = `${s}px`;
    cvs.style.height = `${s}px`;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, s, s);
    const cx = s / 2;
    const cy = s / 2;
    const r = 28;
    const lw = 5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    ctx.lineWidth = lw;
    ctx.stroke();
    if (total > 0 && value > 0) {
      const pct = value / total;
      ctx.beginPath();
      ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * pct);
      ctx.strokeStyle = color;
      ctx.lineWidth = lw;
      ctx.lineCap = "round";
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.font = `600 ${Math.round(12 * dpr)}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`${Math.round(pct * 100)}%`, cx, cy);
    }
  }, [value, total, color]);
  return <canvas ref={ref} className="flex-shrink-0" />;
};

const ScanTypeDistribution = ({ data }) => {
  const total = getTotal(data);
  return (
    <motion.div
      className="grid grid-cols-2 gap-4"
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.08 } } }}
    >
      {scanTypes.map((type) => {
        const count = getCount(data, type.key);
        return (
          <motion.div
            key={type.key}
            variants={{
              hidden: { opacity: 0, y: 15 },
              show: { opacity: 1, y: 0 },
            }}
            className="p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 hover:-translate-y-1 hover:shadow-xl transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`inline-flex p-2.5 rounded-xl bg-gradient-to-r ${type.gradient}`}>
                <type.icon className="h-5 w-5 text-white" />
              </div>
              {total > 0 && <Donut value={count} total={total} color={type.color} />}
            </div>
            <p className="text-2xl font-bold text-white">{count}</p>
            <p className="text-sm text-gray-400">{type.label}</p>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default ScanTypeDistribution;
