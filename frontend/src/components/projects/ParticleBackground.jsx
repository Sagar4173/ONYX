import { useMemo } from "react";

const PARTICLE_COUNT = 60;

const ParticleBackground = ({ isScanActive = false }) => {
  const particles = useMemo(() => {
    const p = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const size = 1 + Math.random() * 2;
      const drift = 8 + Math.random() * 12;
      const sway = 12 + Math.random() * 8;
      const delay = Math.random() * 10;
      const isViolet = Math.random() > 0.6;
      const color = isViolet ? "rgba(139,92,246,0.12)" : "rgba(6,182,212,0.15)";
      p.push({ x, y, size, drift, sway, delay, color, isViolet, left: `${x}%`, top: `${y}%` });
    }
    return p;
  }, [isScanActive]);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      {particles.map((p, i) => (
        <div
          key={i}
          className={`absolute rounded-full ${isScanActive ? "animate-particle-fast" : "animate-particle-slow"}`}
          style={{
            left: p.left,
            top: p.top,
            width: `${p.size}px`,
            height: `${p.size}px`,
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${isScanActive ? p.drift * 0.5 : p.drift}s, ${isScanActive ? p.sway * 0.5 : p.sway}s`,
            boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
            "--drift": `${isScanActive ? p.drift * 0.5 : p.drift}s`,
            "--sway": `${isScanActive ? p.sway * 0.5 : p.sway}s`,
          }}
        />
      ))}
    </div>
  );
};

export default ParticleBackground;
