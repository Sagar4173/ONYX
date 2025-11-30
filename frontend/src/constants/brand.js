/**
 * ONYX Brand Constants
 * Centralized styling and brand identity for the ONYX Security Intelligence Platform
 * Import this file to ensure consistent branding across all components
 */

// Brand Identity
export const BRAND = {
  name: "ONYX",
  tagline: "Security Intelligence Platform",
  fullName: "ONYX Security Intelligence Platform",
  description: "AI-Powered Security Analysis & Vulnerability Detection",
  copyright: `© ${new Date().getFullYear()} ONYX. All rights reserved.`,
};

// Color Palette - Tailwind CSS classes
export const COLORS = {
  // Primary Colors (Cyan-Violet gradient)
  primary: {
    cyan: "cyan-500",
    violet: "violet-500",
    gradient: "from-cyan-500 to-violet-500",
    gradientHover: "from-cyan-600 to-violet-600",
    gradientVia: "from-cyan-500 via-violet-500 to-cyan-500",
  },

  // Secondary/Accent Colors
  accent: {
    cyan: {
      light: "cyan-300",
      default: "cyan-400",
      medium: "cyan-500",
      dark: "cyan-600",
    },
    violet: {
      light: "violet-300",
      default: "violet-400",
      medium: "violet-500",
      dark: "violet-600",
    },
  },

  // Background Colors
  background: {
    primary: "gray-950",
    secondary: "gray-900",
    tertiary: "gray-800",
    card: "gray-800/50",
    glass: "gray-900/80",
  },

  // Text Colors
  text: {
    primary: "white",
    secondary: "gray-300",
    tertiary: "gray-400",
    muted: "gray-500",
  },

  // Border Colors
  border: {
    default: "gray-700",
    light: "gray-600",
    accent: "cyan-500/30",
  },

  // Status Colors
  status: {
    success: "emerald-500",
    warning: "amber-500",
    error: "red-500",
    info: "cyan-500",
  },

  // Severity Colors
  severity: {
    critical: "red-500",
    high: "orange-500",
    medium: "yellow-500",
    low: "cyan-500",
    info: "gray-500",
  },
};

// Gradient Classes (ready to use)
export const GRADIENTS = {
  // Primary brand gradient
  primary: "bg-gradient-to-r from-cyan-500 to-violet-500",
  primaryHover: "hover:from-cyan-600 hover:to-violet-600",

  // Text gradient
  text: "bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent",
  textHover: "hover:from-cyan-300 hover:to-violet-300",

  // Background gradients
  background: "bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950",
  backgroundAuth: "bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950",
  backgroundCard: "bg-gradient-to-br from-gray-800/90 to-gray-900/90",

  // Glow effects
  glowCyan: "shadow-lg shadow-cyan-500/20",
  glowViolet: "shadow-lg shadow-violet-500/20",
  glowPrimary: "shadow-lg shadow-cyan-500/30",

  // Animated gradients
  animated:
    "bg-gradient-to-r from-cyan-500 via-violet-500 to-cyan-500 bg-size-200 animate-gradient",
};

// Button Styles
export const BUTTONS = {
  primary: `
    bg-gradient-to-r from-cyan-500 to-violet-500 
    text-white font-semibold rounded-xl 
    hover:from-cyan-600 hover:to-violet-600 
    focus:outline-none focus:ring-2 focus:ring-violet-500/50 
    transition-all shadow-lg hover:shadow-xl 
    transform hover:scale-[1.02] active:scale-[0.98]
  `,
  secondary: `
    bg-gray-800 border border-gray-700 
    text-white font-medium rounded-xl 
    hover:bg-gray-700 hover:border-cyan-500/30 
    focus:outline-none focus:ring-2 focus:ring-cyan-500/50 
    transition-all
  `,
  ghost: `
    text-gray-300 hover:text-white 
    hover:bg-gray-800/50 
    rounded-lg transition-all
  `,
  link: `
    text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 
    bg-clip-text font-semibold 
    hover:from-cyan-300 hover:to-violet-300 
    transition-all
  `,
};

// Input Styles
export const INPUTS = {
  default: `
    w-full px-4 py-3 
    bg-gray-700/50 border border-gray-600/50 
    rounded-xl text-white placeholder-gray-500 
    focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 
    transition-all
  `,
  withIcon: `
    w-full px-4 py-3 pl-11 
    bg-gray-700/50 border border-gray-600/50 
    rounded-xl text-white placeholder-gray-500 
    focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 
    transition-all
  `,
};

// Card Styles
export const CARDS = {
  default: `
    bg-gray-800/50 backdrop-blur-xl 
    rounded-2xl border border-gray-700/50 
    shadow-xl
  `,
  glass: `
    bg-gray-900/80 backdrop-blur-xl 
    rounded-3xl border border-gray-800/50 
    shadow-2xl
  `,
  interactive: `
    bg-gray-800/50 backdrop-blur-xl 
    rounded-2xl border border-gray-700/50 
    shadow-xl hover:shadow-cyan-500/10 
    hover:border-cyan-500/30 
    transition-all duration-300
  `,
};

// Animation Classes
export const ANIMATIONS = {
  fadeIn: "animate-fadeIn",
  slideUp: "animate-slideUp",
  pulse: "animate-pulse",
  float: "animate-float",
  glow: "animate-glow",
  gradient: "animate-gradient",
};

// Badge/Tag Styles
export const BADGES = {
  severity: {
    critical: "bg-red-500/20 text-red-400 border border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border border-orange-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    low: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30",
    info: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
  },
  status: {
    success: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
    warning: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
    error: "bg-red-500/20 text-red-400 border border-red-500/30",
    info: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30",
  },
};

// Icon colors for features
export const FEATURE_COLORS = {
  scanning: "text-cyan-400",
  analytics: "text-violet-400",
  security: "text-cyan-300",
  compliance: "text-violet-300",
  ai: "text-cyan-400",
  enterprise: "text-violet-400",
};

// Social/External Links
export const LINKS = {
  github: "https://github.com/Sagar4173/ONYX",
  documentation: "/docs",
  support: "/support",
};

// Default export for convenience
export default {
  BRAND,
  COLORS,
  GRADIENTS,
  BUTTONS,
  INPUTS,
  CARDS,
  ANIMATIONS,
  BADGES,
  FEATURE_COLORS,
  LINKS,
};
