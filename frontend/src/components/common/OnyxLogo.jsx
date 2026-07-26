import React from "react";

const OnyxLogo = ({ className = "w-10 h-10", variant = "default" }) => {
  const id = React.useId().replace(/:/g, "");

  if (variant === "mini") {
    return (
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <circle cx="16" cy="16" r="14.5" fill="none" stroke={`url(#ms-${id})`} strokeWidth="2.5" />
        <circle cx="16" cy="16" r="1.5" fill="#00e5ff" opacity="0.2" />
        <defs>
          <linearGradient id={`ms-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00e5ff" />
            <stop offset="50%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#00e5ff" />
          </linearGradient>
        </defs>
      </svg>
    );
  }

  if (variant === "glow") {
    return (
      <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <defs>
          <radialGradient id={`ga-${id}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.12" />
            <stop offset="50%" stopColor="#7c3aed" stopOpacity="0.04" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <linearGradient id={`gs-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00e5ff" />
            <stop offset="50%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#00e5ff" />
          </linearGradient>
          <filter id={`gf-${id}`}>
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle cx="32" cy="32" r="34" fill={`url(#ga-${id})`} />
        <circle
          cx="32"
          cy="32"
          r="29"
          fill="none"
          stroke={`url(#gs-${id})`}
          strokeWidth="3.5"
          filter={`url(#gf-${id})`}
        />
        <path
          d="M 50 12 L 54 16 L 46 24 Z"
          fill="rgba(0,229,255,0.08)"
          stroke="rgba(0,229,255,0.35)"
          strokeWidth="0.8"
        />
        <circle
          cx="32"
          cy="32"
          r="23"
          fill="none"
          stroke={`url(#gs-${id})`}
          strokeWidth="0.5"
          opacity="0.12"
        />
        <path
          d="M 12 24 A 22 22 0 0 1 52 24"
          fill="none"
          stroke="#00e5ff"
          strokeWidth="1.5"
          opacity="0.15"
        />
        <circle cx="32" cy="32" r="3" fill="#00e5ff" opacity="0.1" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <linearGradient id={`ds-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00e5ff" />
          <stop offset="50%" stopColor="#7c3aed" />
          <stop offset="100%" stopColor="#00e5ff" />
        </linearGradient>
      </defs>
      <circle cx="16" cy="16" r="14" fill="none" stroke={`url(#ds-${id})`} strokeWidth="2.8" />
      <path
        d="M 24 6 L 26.5 8.5 L 22 12 Z"
        fill="rgba(0,229,255,0.07)"
        stroke="rgba(0,229,255,0.35)"
        strokeWidth="0.6"
      />
      <circle
        cx="16"
        cy="16"
        r="9"
        fill="none"
        stroke={`url(#ds-${id})`}
        strokeWidth="0.3"
        opacity="0.12"
      />
      <path
        d="M 6 12 A 13 13 0 0 1 26 12"
        fill="none"
        stroke="#00e5ff"
        strokeWidth="0.8"
        opacity="0.15"
      />
    </svg>
  );
};

export default OnyxLogo;
