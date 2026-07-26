const AnimatedBackground = ({ scrollY = 0, mousePosition = { x: 0, y: 0 } }) => (
  <div className="fixed inset-0 pointer-events-none overflow-hidden">
    <div
      className="absolute w-[800px] h-[800px] rounded-full opacity-20 blur-3xl"
      style={{
        background: "radial-gradient(circle, rgba(34,211,238,0.4) 0%, transparent 70%)",
        left: `${-200 + mousePosition.x * 0.02}px`,
        top: `${-200 + mousePosition.y * 0.02}px`,
        transform: `translateY(${scrollY * 0.2}px)`,
      }}
    />
    <div
      className="absolute w-[600px] h-[600px] rounded-full opacity-20 blur-3xl"
      style={{
        background: "radial-gradient(circle, rgba(139,92,246,0.4) 0%, transparent 70%)",
        right: `${-100 - mousePosition.x * 0.01}px`,
        top: `${200 + mousePosition.y * 0.01}px`,
        transform: `translateY(${scrollY * -0.1}px)`,
      }}
    />
    <div
      className="absolute w-[500px] h-[500px] rounded-full opacity-15 blur-3xl"
      style={{
        background: "radial-gradient(circle, rgba(168,85,247,0.4) 0%, transparent 70%)",
        left: "40%",
        bottom: "-200px",
        transform: `translateY(${scrollY * -0.15}px)`,
      }}
    />
    <div
      className="absolute inset-0 opacity-[0.02]"
      style={{
        backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
        backgroundSize: "100px 100px",
        transform: `translateY(${scrollY * 0.1}px)`,
      }}
    />
  </div>
);

export default AnimatedBackground;
