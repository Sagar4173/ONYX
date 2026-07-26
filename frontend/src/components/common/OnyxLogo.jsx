/**
 * ONYX Logo Component
 * Premium unified logo component - Cyber Shield with Quantum Eye
 */
import React from "react";

/**
 * ONYX Logo SVG - Premium cyber shield with quantum AI eye
 * @param {string} className - Tailwind classes for sizing
 * @param {string} variant - 'default' | 'glow' | 'mini'
 */
const OnyxLogo = ({ className = "w-10 h-10", variant = "default" }) => {
  const uniqueId = React.useId().replace(/:/g, "");

  if (variant === "mini") {
    return (
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <defs>
          <linearGradient id={`mini-bg-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0c1222" />
            <stop offset="100%" stopColor="#1a1f35" />
          </linearGradient>
          <linearGradient id={`mini-stroke-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="50%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
          <linearGradient id={`mini-eye-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
          <filter id={`mini-glow-${uniqueId}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* Hexagon body */}
        <path
          d="M16 2L28 9V23L16 30L4 23V9L16 2Z"
          fill={`url(#mini-bg-${uniqueId})`}
          stroke={`url(#mini-stroke-${uniqueId})`}
          strokeWidth="1.5"
        />
        {/* Inner hexagon accent */}
        <path
          d="M16 6L24 10.5V21.5L16 26L8 21.5V10.5L16 6Z"
          fill="none"
          stroke={`url(#mini-stroke-${uniqueId})`}
          strokeWidth="0.5"
          opacity="0.3"
        />
        {/* Quantum eye */}
        <circle
          cx="16"
          cy="16"
          r="6"
          fill="none"
          stroke={`url(#mini-eye-${uniqueId})`}
          strokeWidth="1"
          opacity="0.6"
        />
        <circle cx="16" cy="16" r="4" fill={`url(#mini-eye-${uniqueId})`} opacity="0.2" />
        <circle cx="16" cy="16" r="3" fill="#0e7490" filter={`url(#mini-glow-${uniqueId})`} />
        <circle cx="16" cy="16" r="1.5" fill="#22d3ee" />
        <circle cx="15" cy="15" r="0.6" fill="white" />
      </svg>
    );
  }

  if (variant === "glow") {
    return (
      <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id={`glow-bg-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0c1222" />
            <stop offset="50%" stopColor="#1a1f35" />
            <stop offset="100%" stopColor="#0c1222" />
          </linearGradient>
          <linearGradient id={`glow-stroke-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="33%" stopColor="#8b5cf6" />
            <stop offset="66%" stopColor="#ec4899" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
          <linearGradient id={`glow-eye-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#a855f7" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
          <radialGradient id={`glow-core-${uniqueId}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#67e8f9" />
            <stop offset="50%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#0891b2" />
          </radialGradient>
          <filter id={`outer-glow-${uniqueId}`} x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id={`eye-glow-${uniqueId}`} x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer glow aura */}
        <polygon
          points="32,4 58,18 58,46 32,60 6,46 6,18"
          fill="none"
          stroke={`url(#glow-stroke-${uniqueId})`}
          strokeWidth="1"
          opacity="0.3"
          filter={`url(#outer-glow-${uniqueId})`}
        />

        {/* Main hexagon body */}
        <polygon
          points="32,6 56,19 56,45 32,58 8,45 8,19"
          fill={`url(#glow-bg-${uniqueId})`}
          stroke={`url(#glow-stroke-${uniqueId})`}
          strokeWidth="2"
        />

        {/* Inner hexagon layer 1 */}
        <polygon
          points="32,12 50,22 50,42 32,52 14,42 14,22"
          fill="none"
          stroke={`url(#glow-stroke-${uniqueId})`}
          strokeWidth="1"
          opacity="0.4"
        />

        {/* Inner hexagon layer 2 */}
        <polygon
          points="32,18 44,25 44,39 32,46 20,39 20,25"
          fill="none"
          stroke={`url(#glow-stroke-${uniqueId})`}
          strokeWidth="0.5"
          opacity="0.2"
        />

        {/* Quantum rings */}
        <circle
          cx="32"
          cy="32"
          r="14"
          fill="none"
          stroke={`url(#glow-eye-${uniqueId})`}
          strokeWidth="1"
          opacity="0.4"
        />
        <circle
          cx="32"
          cy="32"
          r="10"
          fill="none"
          stroke={`url(#glow-eye-${uniqueId})`}
          strokeWidth="1.5"
          opacity="0.6"
        />

        {/* AI Eye core */}
        <circle cx="32" cy="32" r="8" fill={`url(#glow-eye-${uniqueId})`} opacity="0.15" />
        <circle cx="32" cy="32" r="6" fill="#0e7490" filter={`url(#eye-glow-${uniqueId})`} />
        <circle cx="32" cy="32" r="4" fill={`url(#glow-core-${uniqueId})`} />
        <circle cx="32" cy="32" r="2" fill="#67e8f9" />
        <circle cx="30" cy="30" r="1" fill="white" />

        {/* Orbital particles */}
        <circle cx="32" cy="18" r="1.5" fill="#22d3ee" opacity="0.8" />
        <circle cx="46" cy="32" r="1" fill="#a855f7" opacity="0.6" />
        <circle cx="32" cy="46" r="1.5" fill="#22d3ee" opacity="0.8" />
        <circle cx="18" cy="32" r="1" fill="#a855f7" opacity="0.6" />
      </svg>
    );
  }

  // Default variant - balanced design for sidebars/headers
  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <linearGradient id={`def-bg-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0c1222" />
          <stop offset="50%" stopColor="#1a1f35" />
          <stop offset="100%" stopColor="#0c1222" />
        </linearGradient>
        <linearGradient id={`def-stroke-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06b6d4" />
          <stop offset="50%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
        <linearGradient id={`def-eye-${uniqueId}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#22d3ee" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
        <radialGradient id={`def-core-${uniqueId}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#67e8f9" />
          <stop offset="100%" stopColor="#0891b2" />
        </radialGradient>
        <filter id={`def-glow-${uniqueId}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Main hexagon body */}
      <path
        d="M16 2L28 9V23L16 30L4 23V9L16 2Z"
        fill={`url(#def-bg-${uniqueId})`}
        stroke={`url(#def-stroke-${uniqueId})`}
        strokeWidth="1.5"
      />

      {/* Inner hexagon accent */}
      <path
        d="M16 6L24 10.5V21.5L16 26L8 21.5V10.5L16 6Z"
        fill="none"
        stroke={`url(#def-stroke-${uniqueId})`}
        strokeWidth="0.5"
        opacity="0.3"
      />

      {/* Quantum ring */}
      <circle
        cx="16"
        cy="16"
        r="7"
        fill="none"
        stroke={`url(#def-eye-${uniqueId})`}
        strokeWidth="0.75"
        opacity="0.5"
      />
      <circle
        cx="16"
        cy="16"
        r="5"
        fill="none"
        stroke={`url(#def-eye-${uniqueId})`}
        strokeWidth="1"
        opacity="0.7"
      />

      {/* AI Eye core */}
      <circle cx="16" cy="16" r="4" fill={`url(#def-eye-${uniqueId})`} opacity="0.2" />
      <circle cx="16" cy="16" r="3" fill="#0e7490" filter={`url(#def-glow-${uniqueId})`} />
      <circle cx="16" cy="16" r="2" fill={`url(#def-core-${uniqueId})`} />
      <circle cx="16" cy="16" r="1" fill="#67e8f9" />
      <circle cx="15" cy="15" r="0.4" fill="white" />

      {/* Corner accents */}
      <circle cx="16" cy="6" r="0.8" fill="#22d3ee" opacity="0.7" />
      <circle cx="16" cy="26" r="0.8" fill="#22d3ee" opacity="0.7" />
    </svg>
  );
};

export default OnyxLogo;
