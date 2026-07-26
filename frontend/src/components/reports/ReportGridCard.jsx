import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Badge } from "../../styles/components";

const scanTypeColors = {
  sast: "from-cyan-500 to-blue-600",
  secrets: "from-purple-500 to-pink-600",
  dependency: "from-amber-500 to-orange-600",
  container: "from-teal-500 to-emerald-600",
  iac: "from-violet-500 to-indigo-600",
  dast: "from-rose-500 to-red-600",
};

const donutColors = [
  { stroke: "#22d3ee", text: "#22d3ee" },
  { stroke: "#fbbf24", text: "#fbbf24" },
  { stroke: "#f87171", text: "#f87171" },
];

const MiniDonut = ({ score, size = 64 }) => {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const cx = size / 2,
      cy = size / 2,
      r = size / 2 - 6,
      lineW = 6;
    const color = score >= 80 ? donutColors[0] : score >= 60 ? donutColors[1] : donutColors[2];
    const fraction = Math.min(score, 100) / 100;
    ctx.clearRect(0, 0, size, size);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(75, 85, 99, 0.3)";
    ctx.lineWidth = lineW;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * fraction);
    ctx.strokeStyle = color.stroke;
    ctx.lineWidth = lineW;
    ctx.lineCap = "round";
    ctx.stroke();
    ctx.fillStyle = color.text;
    ctx.font = `bold ${size * 0.23}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(Math.round(score).toString(), cx, cy);
  }, [score, size]);
  return <canvas ref={canvasRef} style={{ width: size, height: size }} />;
};

const itemAnim = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const ReportGridCard = ({ report }) => {
  const navigate = useNavigate();
  const sev = report.findings_by_severity || {};
  const critical = sev.critical || 0;
  const high = sev.high || 0;
  const medium = sev.medium || 0;
  const total = critical + high + medium + (sev.low || 0);
  const scanType = report.scan_type || report.type || "sast";

  return (
    <motion.div
      variants={itemAnim}
      onClick={() => navigate(`/report/${report.id}`)}
      className="group bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 hover:border-cyan-500/40 hover:shadow-lg hover:shadow-cyan-500/5 transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter") navigate(`/report/${report.id}`);
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <MiniDonut score={report.security_score || 0} size={64} />
        <div className="flex flex-col items-end gap-1">
          <span
            className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[10px] font-bold text-white bg-gradient-to-r ${scanTypeColors[scanType] || "from-gray-500 to-gray-600"}`}
          >
            {scanType.toUpperCase()}
          </span>
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${report.security_score >= 80 ? "bg-emerald-500/20 text-emerald-400" : report.security_score >= 60 ? "bg-amber-500/20 text-amber-400" : "bg-red-500/20 text-red-400"}`}
          >
            Score: {report.security_score ?? "—"}
          </span>
        </div>
      </div>
      <h3 className="text-sm font-semibold text-white truncate mb-2">
        {report.project_name || "Untitled"}
      </h3>
      {report.created_at && (
        <p className="text-xs text-gray-500 mb-3">
          {new Date(report.created_at).toLocaleDateString()}
        </p>
      )}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {critical > 0 && (
            <Badge variant="critical" size="xs">
              {critical}
            </Badge>
          )}
          {high > 0 && (
            <Badge variant="high" size="xs">
              {high}
            </Badge>
          )}
          {medium > 0 && (
            <Badge variant="medium" size="xs">
              {medium}
            </Badge>
          )}
          {total === 0 && (
            <Badge variant="success" size="xs">
              Clean
            </Badge>
          )}
        </div>
        <span className="text-xs text-gray-500">{total} findings</span>
      </div>
    </motion.div>
  );
};

export default ReportGridCard;
