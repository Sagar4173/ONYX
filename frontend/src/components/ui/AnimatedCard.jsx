/**
 * AnimatedCard - Card with hover animations and effects
 */
import React, { useState, useRef } from "react";
import { motion } from "framer-motion";

const AnimatedCard = ({
  children,
  variant = "default",
  hover = true,
  tilt = false,
  glow = false,
  gradient,
  className = "",
  onClick,
  ...props
}) => {
  const [tiltPosition, setTiltPosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const cardRef = useRef(null);

  const variants = {
    default: `
      bg-gray-800/50 border-gray-700/50
      hover:border-gray-600/50 hover:bg-gray-800/70
    `,
    glass: `
      bg-gray-900/50 backdrop-blur-xl border-gray-700/30
      hover:bg-gray-900/70 hover:border-gray-600/50
    `,
    outlined: `
      bg-transparent border-gray-700
      hover:border-gray-500 hover:bg-gray-800/30
    `,
    elevated: `
      bg-gray-800 border-gray-700/50
      shadow-lg shadow-black/20
      hover:shadow-xl hover:shadow-black/30
    `,
    gradient: `
      bg-gradient-to-br ${gradient || "from-gray-800 to-gray-900"}
      border-gray-700/30
    `,
  };

  const handleMouseMove = (e) => {
    if (!tilt || !cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    setTiltPosition({
      x: (y - centerY) / 20,
      y: (centerX - x) / 20,
    });
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setTiltPosition({ x: 0, y: 0 });
  };

  return (
    <motion.div
      ref={cardRef}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileHover={hover ? { y: -4, scale: 1.02 } : {}}
      animate={{
        rotateX: tiltPosition.x,
        rotateY: tiltPosition.y,
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 20,
      }}
      className={`
        relative p-6 rounded-2xl border
        transition-all duration-300
        ${variants[variant]}
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
      style={{ transformStyle: "preserve-3d" }}
      {...props}
    >
      {/* Glow effect */}
      {glow && isHovered && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-blue-500/30 to-purple-500/30 blur-lg -z-10"
        />
      )}

      {/* Gradient border on hover */}
      {isHovered && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute inset-0 rounded-2xl p-[1px] bg-gradient-to-r from-blue-500/50 to-purple-500/50 -z-10"
        />
      )}

      {/* Content */}
      <div style={{ transform: "translateZ(20px)" }}>{children}</div>
    </motion.div>
  );
};

// Feature Card - Pre-styled card for feature highlights
export const FeatureCard = ({
  icon: Icon,
  title,
  description,
  gradient = "from-blue-500 to-cyan-500",
  className = "",
  ...props
}) => {
  return (
    <AnimatedCard variant="glass" glow className={className} {...props}>
      <div
        className={`
        inline-flex p-3 rounded-xl mb-4
        bg-gradient-to-br ${gradient}
      `}
      >
        <Icon className="h-6 w-6 text-white" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </AnimatedCard>
  );
};

// Stat Card - Pre-styled card for statistics
export const StatCard = ({
  label,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  gradient = "from-blue-500 to-cyan-500",
  className = "",
  ...props
}) => {
  const changeColors = {
    positive: "text-emerald-400",
    negative: "text-red-400",
    neutral: "text-gray-400",
  };

  return (
    <AnimatedCard variant="glass" className={className} {...props}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {change !== undefined && (
            <p className={`text-sm mt-1 ${changeColors[changeType]}`}>
              {change > 0 ? "+" : ""}
              {change}%
            </p>
          )}
        </div>
        {Icon && (
          <div
            className={`p-3 rounded-xl bg-gradient-to-br ${gradient} opacity-80`}
          >
            <Icon className="h-5 w-5 text-white" />
          </div>
        )}
      </div>
    </AnimatedCard>
  );
};

export default AnimatedCard;
