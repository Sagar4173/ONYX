import { useMemo, useEffect } from "react";
import { motion, useAnimation } from "framer-motion";

const LAT_LINES = 6;
const LON_LINES = 8;

const SecurityScoreGlobe = ({ score = 0, isScanActive = false, size = 140, className = "" }) => {
  const controls = useAnimation();
  const scoreColor =
    score >= 80
      ? "rgba(34,197,94,0.4)"
      : score >= 60
        ? "rgba(234,179,8,0.4)"
        : "rgba(239,68,68,0.4)";
  const pulseDuration = score >= 80 ? 3 : score >= 60 ? 2 : 1;
  const radius = size / 2;

  useEffect(() => {
    controls.start({
      rotateY: 360,
      rotateX: [0, 5, 0, -5, 0],
      transition: {
        rotateY: { duration: isScanActive ? 6 : 12, repeat: Infinity, ease: "linear" },
        rotateX: { duration: 8, repeat: Infinity, ease: "easeInOut" },
      },
    });
  }, [isScanActive, controls]);

  const latLines = useMemo(() => {
    return Array.from({ length: LAT_LINES }, (_, i) => {
      const angle = ((i + 1) / (LAT_LINES + 1)) * 180;
      const r = radius * Math.sin((angle * Math.PI) / 180);
      const ry = radius * 0.4;
      return { r, ry, key: `lat-${i}` };
    });
  }, [radius]);

  const lonLines = useMemo(() => {
    return Array.from({ length: LON_LINES }, (_, i) => {
      const angle = (i / LON_LINES) * 360;
      return { angle, key: `lon-${i}` };
    });
  }, []);

  const particles = useMemo(() => {
    return Array.from({ length: isScanActive ? 8 : 5 }, (_, i) => ({
      orbit: 30 + Math.random() * 50,
      speed: (isScanActive ? 2 : 1) * (4 + Math.random() * 6),
      delay: Math.random() * 4,
      color: ["#ef4444", "#f97316", "#eab308", "#22d3ee"][i % 4],
      size: 3 + Math.random() * 2,
    }));
  }, [isScanActive]);

  return (
    <motion.div
      className={`relative ${className}`}
      style={{ width: size, height: size, perspective: size * 4 }}
      animate={{ scale: [1, 1.02, 1] }}
      transition={{ duration: pulseDuration, repeat: Infinity, ease: "easeInOut" }}
    >
      <motion.div
        className="w-full h-full"
        style={{ transformStyle: "preserve-3d" }}
        animate={controls}
      >
        <svg width={size} height={size} className="absolute inset-0">
          {latLines.map(({ r, key }) => (
            <ellipse
              key={key}
              cx={radius}
              cy={radius}
              rx={r}
              ry={r * 0.4}
              fill="none"
              stroke={scoreColor}
              strokeWidth="0.5"
              opacity="0.6"
            />
          ))}
          {lonLines.map(({ angle, key }) => (
            <ellipse
              key={key}
              cx={radius}
              cy={radius}
              rx={radius * Math.abs(Math.cos((angle * Math.PI) / 180))}
              ry={radius * 0.4}
              fill="none"
              stroke={scoreColor}
              strokeWidth="0.5"
              opacity="0.6"
              transform={`rotate(${angle}, ${radius}, ${radius})`}
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="rounded-full"
            style={{
              width: size * 0.5,
              height: size * 0.5,
              background: `radial-gradient(circle, ${scoreColor} 0%, transparent 70%)`,
            }}
          />
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.span
            className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 bg-clip-text text-transparent"
            key={Math.round(score)}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", damping: 15, stiffness: 200 }}
          >
            {Math.round(score)}
          </motion.span>
        </div>
      </motion.div>
      {particles.map((p, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
            left: radius - p.size / 2,
            top: radius - p.size / 2,
            transformOrigin: `${radius}px ${radius}px`,
          }}
          animate={{
            rotate: [0, 360],
          }}
          transition={{ duration: p.speed, repeat: Infinity, ease: "linear", delay: p.delay }}
        />
      ))}
    </motion.div>
  );
};

export default SecurityScoreGlobe;
