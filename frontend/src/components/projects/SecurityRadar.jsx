import { useRef, useEffect } from "react";

const DEFAULT_AXES = [
  { label: "SAST", value: 0 },
  { label: "Secrets", value: 0 },
  { label: "Dependencies", value: 0 },
  { label: "Container", value: 0 },
  { label: "IaC", value: 0 },
  { label: "DAST", value: 0 },
];

const SecurityRadar = ({ data = DEFAULT_AXES, size = 280, className = "" }) => {
  const canvasRef = useRef(null);
  const sweepRef = useRef(0);
  const rafRef = useRef(null);
  const center = size / 2;
  const radius = size * 0.38;
  const numAxes = data.length;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const draw = () => {
      ctx.clearRect(0, 0, size, size);
      const angleStep = (2 * Math.PI) / numAxes;

      for (let g = 1; g <= 4; g++) {
        ctx.beginPath();
        ctx.arc(center, center, (radius / 4) * g, 0, 2 * Math.PI);
        ctx.strokeStyle = `rgba(55, 65, 81, ${0.2 + g * 0.1})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }

      data.forEach((_, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        ctx.beginPath();
        ctx.moveTo(center, center);
        ctx.lineTo(center + radius * Math.cos(angle), center + radius * Math.sin(angle));
        ctx.strokeStyle = "rgba(75, 85, 99, 0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      ctx.beginPath();
      data.forEach((d, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const r = (d.value / 100) * radius;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = "rgba(6, 182, 212, 0.15)";
      ctx.fill();
      ctx.strokeStyle = "#06b6d4";
      ctx.lineWidth = 2;
      ctx.stroke();

      data.forEach((d, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const r = (d.value / 100) * radius;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fillStyle = d.value > 0 ? "#22d3ee" : "rgba(75, 85, 99, 0.5)";
        ctx.fill();
        ctx.strokeStyle = d.value > 0 ? "#67e8f9" : "transparent";
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      sweepRef.current += 0.005;
      if (sweepRef.current > 2 * Math.PI) sweepRef.current = 0;
      const sweepAngle = -Math.PI / 2 + sweepRef.current;
      const gradient = ctx.createRadialGradient(center, center, 0, center, center, radius);
      gradient.addColorStop(0, "rgba(6, 182, 212, 0.08)");
      gradient.addColorStop(
        sweepRef.current / (2 * Math.PI) > 0.5 ? 0.5 : 0,
        "rgba(139, 92, 246, 0.03)"
      );
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.arc(center, center, radius, sweepAngle - 0.3, sweepAngle);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();

      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      data.forEach((d, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const labelR = radius + 20;
        const x = center + labelR * Math.cos(angle);
        const y = center + labelR * Math.sin(angle);
        ctx.fillText(d.label, x, y);
      });

      rafRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [data, size, center, radius, numAxes]);

  return <canvas ref={canvasRef} width={size} height={size} className={className} />;
};

export default SecurityRadar;
