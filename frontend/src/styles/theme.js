export const colors = {
  primary: {
    50: "#ecfeff",
    100: "#cffafe",
    200: "#a5f3fc",
    300: "#67e8f9",
    400: "#22d3ee",
    500: "#06b6d4",
    600: "#0891b2",
    700: "#0e7490",
    800: "#155e75",
    900: "#164e63",
    950: "#083344",
  },

  accent: {
    50: "#f5f3ff",
    100: "#ede9fe",
    200: "#ddd6fe",
    300: "#c4b5fd",
    400: "#a78bfa",
    500: "#8b5cf6",
    600: "#7c3aed",
    700: "#6d28d9",
    800: "#5b21b6",
    900: "#4c1d95",
    950: "#2e1065",
  },

  background: {
    primary: "#05080f",
    secondary: "#0a0318",
    tertiary: "#0f0520",
    accent: "#1a0a30",
    card: "#0f0520",
    cardHover: "#1a0a30",
  },

  text: {
    primary: "#f9fafb",
    secondary: "#d1d5db",
    muted: "#9ca3af",
    accent: "#06b6d4",
  },

  success: {
    light: "#dcfce7",
    main: "#22c55e",
    dark: "#15803d",
    bg: "rgba(34, 197, 94, 0.1)",
  },
  warning: {
    light: "#fef3c7",
    main: "#f59e0b",
    dark: "#b45309",
    bg: "rgba(245, 158, 11, 0.1)",
  },
  danger: {
    light: "#fee2e2",
    main: "#ef4444",
    dark: "#b91c1c",
    bg: "rgba(239, 68, 68, 0.1)",
  },
  info: {
    light: "#cffafe",
    main: "#06b6d4",
    dark: "#0e7490",
    bg: "rgba(6, 182, 212, 0.1)",
  },

  severity: {
    critical: { bg: "#7f1d1d", text: "#fecaca", border: "#dc2626" },
    high: { bg: "#7c2d12", text: "#fed7aa", border: "#ea580c" },
    medium: { bg: "#78350f", text: "#fde68a", border: "#d97706" },
    low: { bg: "#0e7490", text: "#67e8f9", border: "#06b6d4" },
    info: { bg: "#374151", text: "#d1d5db", border: "#6b7280" },
  },

  border: {
    primary: "#374151",
    secondary: "#4b5563",
    light: "#6b7280",
  },
};

export const gradients = {
  primary: "linear-gradient(135deg, #06b6d4, #7c3aed)",
  secondary: "linear-gradient(135deg, #00e5ff, #06b6d4)",
  success: "linear-gradient(135deg, #10b981, #059669)",
  warning: "linear-gradient(135deg, #f59e0b, #d97706)",
  danger: "linear-gradient(135deg, #ef4444, #dc2626)",
  dark: "linear-gradient(135deg, #0f0520, #05080f)",
  glow: "radial-gradient(ellipse at top, #0f0520 0%, #05080f 70%)",
};

export const spacing = {
  xs: "0.25rem",
  sm: "0.5rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
  "2xl": "3rem",
  "3xl": "4rem",
};

export const typography = {
  fontFamily: {
    sans: '"Inter", ui-sans-serif, system-ui, sans-serif',
    mono: '"JetBrains Mono", ui-monospace, monospace',
  },
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    base: "1rem",
    lg: "1.125rem",
    xl: "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    "4xl": "2.25rem",
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const shadows = {
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
  xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
  glow: "0 0 20px rgba(6, 182, 212, 0.3)",
  glowSuccess: "0 0 20px rgba(34, 197, 94, 0.3)",
  glowDanger: "0 0 20px rgba(239, 68, 68, 0.3)",
};

export const borderRadius = {
  none: "0",
  sm: "0.25rem",
  md: "0.375rem",
  lg: "0.5rem",
  xl: "0.75rem",
  "2xl": "1rem",
  full: "9999px",
};

export const transitions = {
  fast: "all 0.15s ease",
  normal: "all 0.2s ease",
  slow: "all 0.3s ease",
  colors: "color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease",
};

export const zIndex = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
  toast: 1080,
};

export const animations = {
  staggerDelay: (index, baseDelay = 0.1) => ({
    animationDelay: `${index * baseDelay}s`,
  }),
  duration: (seconds) => ({
    animationDuration: `${seconds}s`,
  }),
  timing: (delay, duration) => ({
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
  }),
};

export const dynamicStyles = {
  progressWidth: (percentage) => ({
    width: `${Math.min(Math.max(percentage, 0), 100)}%`,
  }),
  size: (width, height = width) => ({
    width: typeof width === "number" ? `${width}px` : width,
    height: typeof height === "number" ? `${height}px` : height,
  }),
  chartDimensions: (width, height) => ({ width, height }),
  barHeight: (value, maxValue, maxHeight = 100) => ({
    height: `${(value / maxValue) * maxHeight}%`,
  }),
  glow: (color, intensity = 6) => ({
    filter: `drop-shadow(0 0 ${intensity}px ${color}40)`,
  }),
  boxGlow: (color, spread = 20, opacity = 0.3) => ({
    boxShadow: `0 0 ${spread}px rgba(${color}, ${opacity})`,
  }),
};

export const severityColors = {
  critical: {
    bg: "#7f1d1d",
    text: "#fecaca",
    border: "#dc2626",
    gradient: "from-red-900 to-red-700",
    tailwind: "bg-red-900/70 text-red-200 border-red-600",
  },
  high: {
    bg: "#7c2d12",
    text: "#fed7aa",
    border: "#ea580c",
    gradient: "from-orange-900 to-orange-700",
    tailwind: "bg-orange-900/70 text-orange-200 border-orange-600",
  },
  medium: {
    bg: "#78350f",
    text: "#fde68a",
    border: "#d97706",
    gradient: "from-yellow-900 to-yellow-700",
    tailwind: "bg-yellow-900/70 text-yellow-200 border-yellow-600",
  },
  low: {
    bg: "#0e7490",
    text: "#67e8f9",
    border: "#06b6d4",
    gradient: "from-cyan-900 to-cyan-700",
    tailwind: "bg-cyan-900/70 text-cyan-200 border-cyan-600",
  },
  info: {
    bg: "#374151",
    text: "#d1d5db",
    border: "#6b7280",
    gradient: "from-gray-800 to-gray-700",
    tailwind: "bg-gray-700 text-gray-300 border-gray-600",
  },
};

export const getSeverityStyles = (severity) => {
  return severityColors[severity?.toLowerCase()] || severityColors.info;
};

export default {
  colors,
  gradients,
  spacing,
  typography,
  shadows,
  borderRadius,
  transitions,
  zIndex,
  animations,
  dynamicStyles,
  severityColors,
  getSeverityStyles,
};
