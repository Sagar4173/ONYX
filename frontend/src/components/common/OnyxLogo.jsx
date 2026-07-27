import React from "react";

const OnyxLogo = ({ className = "w-10 h-10", variant = "default" }) => {
  const id = React.useId().replace(/:/g, "");

  if (variant === "mini") {
    return (
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <defs>
          <linearGradient id={`ms-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00e5ff" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
        </defs>
        <circle cx="16" cy="16" r="15" fill="#0f0520" stroke={`url(#ms-${id})`} strokeWidth="0.6" />
        <path
          d="M 24 8 L 26 10 L 23 13 Z"
          fill="rgba(0,229,255,0.08)"
          stroke="rgba(0,229,255,0.2)"
          strokeWidth="0.3"
        />
        <circle cx="16" cy="16" r="1" fill="#00e5ff" opacity="0.1" />
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
          <linearGradient id={`gl-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0a0318" />
            <stop offset="100%" stopColor="#12062a" />
          </linearGradient>
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
          r="30"
          fill={`url(#gl-${id})`}
          stroke={`url(#gs-${id})`}
          strokeWidth="1.2"
        />
        <path
          d="M 48 16 L 52 20 L 46 26 Z"
          fill="rgba(0,229,255,0.08)"
          stroke="rgba(0,229,255,0.2)"
          strokeWidth="0.5"
        />
        <circle
          cx="32"
          cy="32"
          r="22"
          fill="none"
          stroke={`url(#gs-${id})`}
          strokeWidth="0.3"
          opacity="0.15"
        />
        <path
          d="M 10 22 A 26 26 0 0 1 54 22"
          fill="none"
          stroke="#00e5ff"
          strokeWidth="1"
          opacity="0.15"
        />
        <path
          d="M 14 42 A 26 26 0 0 0 50 42"
          fill="none"
          stroke="#7c3aed"
          strokeWidth="0.8"
          opacity="0.1"
        />
        <circle cx="32" cy="32" r="2" fill="#00e5ff" opacity="0.1" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <linearGradient id={`bg-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0a0318" />
          <stop offset="100%" stopColor="#12062a" />
        </linearGradient>
        <linearGradient id={`ds-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00e5ff" />
          <stop offset="50%" stopColor="#7c3aed" />
          <stop offset="100%" stopColor="#00e5ff" />
        </linearGradient>
      </defs>
      <circle
        cx="16"
        cy="16"
        r="15"
        fill={`url(#bg-${id})`}
        stroke={`url(#ds-${id})`}
        strokeWidth="0.6"
      />
      <path
        d="M 24 8 L 26 10 L 23 13 Z"
        fill="rgba(0,229,255,0.08)"
        stroke="rgba(0,229,255,0.2)"
        strokeWidth="0.3"
      />
      <circle
        cx="16"
        cy="16"
        r="11"
        fill="none"
        stroke={`url(#ds-${id})`}
        strokeWidth="0.15"
        opacity="0.15"
      />
      <path
        d="M 5 11 A 13 13 0 0 1 27 11"
        fill="none"
        stroke="#00e5ff"
        strokeWidth="0.5"
        opacity="0.15"
      />
      <path
        d="M 7 21 A 13 13 0 0 0 25 21"
        fill="none"
        stroke="#7c3aed"
        strokeWidth="0.4"
        opacity="0.1"
      />
      <circle cx="16" cy="16" r="1" fill="#00e5ff" opacity="0.1" />
    </svg>
  );
};

export default OnyxLogo;
