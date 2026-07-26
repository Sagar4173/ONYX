import { useRef, useEffect } from "react";
import { ChartBarIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const ScoreTrendChart = ({ reports = [] }) => {
  const canvasRef = useRef(null);

  const dataPoints = reports
    .filter((r) => r.security_score != null)
    .map((r) => ({ score: r.security_score, date: new Date(r.created_at) }))
    .sort((a, b) => a.date - b.date);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || dataPoints.length < 2) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = rect.height;
    const pad = { top: 20, right: 20, bottom: 30, left: 40 };
    const plotW = w - pad.left - pad.right;
    const plotH = h - pad.top - pad.bottom;

    const xMin = dataPoints[0].date.getTime();
    const xMax = dataPoints[dataPoints.length - 1].date.getTime();
    const yMin = 0;
    const yMax = 100;

    const x = (d) => pad.left + ((d.getTime() - xMin) / (xMax - xMin)) * plotW;
    const y = (s) => pad.top + plotH - ((s - yMin) / (yMax - yMin)) * plotH;

    ctx.clearRect(0, 0, w, h);

    ctx.strokeStyle = "rgba(75, 85, 99, 0.3)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gy = pad.top + (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, gy);
      ctx.lineTo(w - pad.right, gy);
      ctx.stroke();
      ctx.fillStyle = "#6b7280";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(Math.round(yMax - (yMax / 4) * i).toString(), pad.left - 8, gy + 4);
    }

    const lastScore = dataPoints[dataPoints.length - 1].score;
    const gradient = ctx.createLinearGradient(0, pad.top, 0, h - pad.bottom);
    if (lastScore >= 60) {
      gradient.addColorStop(0, "rgba(34, 211, 238, 0.3)");
      gradient.addColorStop(1, "rgba(34, 211, 238, 0.02)");
    } else {
      gradient.addColorStop(0, "rgba(239, 68, 68, 0.3)");
      gradient.addColorStop(1, "rgba(239, 68, 68, 0.02)");
    }

    ctx.beginPath();
    ctx.moveTo(x(dataPoints[0].date), pad.top + plotH);
    dataPoints.forEach((p) => ctx.lineTo(x(p.date), y(p.score)));
    ctx.lineTo(x(dataPoints[dataPoints.length - 1].date), pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    dataPoints.forEach((p, i) => {
      const px = x(p.date);
      const py = y(p.score);
      if (i === 0) ctx.moveTo(px, py);
      else {
        const cp1x = x(dataPoints[i - 1].date) + (px - x(dataPoints[i - 1].date)) / 2;
        ctx.bezierCurveTo(cp1x, y(dataPoints[i - 1].score), cp1x, py, px, py);
      }
    });
    ctx.strokeStyle = lastScore >= 60 ? "#22d3ee" : "#ef4444";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    dataPoints.forEach((p) => {
      ctx.beginPath();
      ctx.arc(x(p.date), y(p.score), 3, 0, Math.PI * 2);
      ctx.fillStyle = lastScore >= 60 ? "#22d3ee" : "#ef4444";
      ctx.fill();
    });
  }, [dataPoints]);

  if (dataPoints.length < 2) {
    return (
      <div className="flex items-center justify-center h-[220px]">
        <EmptyState
          icon={ChartBarIcon}
          title="No trend data"
          description="Run scans to see your security score trend over time"
        />
      </div>
    );
  }

  return (
    <div>
      <canvas ref={canvasRef} className="w-full h-[220px]" />
    </div>
  );
};

export default ScoreTrendChart;
