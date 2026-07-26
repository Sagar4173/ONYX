import { useEffect, useRef } from "react";

const FloatingParticles = () => {
  const particlesRef = useRef(null);

  useEffect(() => {
    const particles = particlesRef.current?.children;
    if (!particles) return;
    const animations = Array.from(particles).map((p) => {
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const duration = 3 + Math.random() * 4;
      const delay = Math.random() * 2;
      p.style.left = `${x}%`;
      p.style.top = `${y}%`;
      p.style.animation = `float ${duration}s ease-in-out ${delay}s infinite`;
      return null;
    });
    return () => animations;
  }, []);

  return (
    <div ref={particlesRef} className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: 15 }).map((_, i) => (
        <div key={i} className="absolute w-1 h-1 bg-cyan-400/30 rounded-full" />
      ))}
      <style>{`@keyframes float { 0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; } 50% { transform: translateY(-20px) scale(1.5); opacity: 0.8; } }`}</style>
    </div>
  );
};

export default FloatingParticles;
