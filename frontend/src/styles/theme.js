/**
 * ONYX Platform - Centralized Styles System
 * This module provides consistent styling constants, themes, and utility classes
 * Import these in components for maintainable and consistent styling
 */

// =============================================================================
// COLOR PALETTE - Semantic color system
// =============================================================================

export const colors = {
  // Primary brand colors
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
    950: '#172554',
  },
  
  // Background colors (dark theme)
  background: {
    primary: '#0a0e1a',
    secondary: '#111827',
    tertiary: '#1f2937',
    accent: '#374151',
    card: '#111827',
    cardHover: '#1f2937',
  },
  
  // Text colors
  text: {
    primary: '#f9fafb',
    secondary: '#d1d5db',
    muted: '#9ca3af',
    accent: '#60a5fa',
  },
  
  // Semantic colors
  success: {
    light: '#dcfce7',
    main: '#22c55e',
    dark: '#15803d',
    bg: 'rgba(34, 197, 94, 0.1)',
  },
  warning: {
    light: '#fef3c7',
    main: '#f59e0b',
    dark: '#b45309',
    bg: 'rgba(245, 158, 11, 0.1)',
  },
  danger: {
    light: '#fee2e2',
    main: '#ef4444',
    dark: '#b91c1c',
    bg: 'rgba(239, 68, 68, 0.1)',
  },
  info: {
    light: '#dbeafe',
    main: '#3b82f6',
    dark: '#1d4ed8',
    bg: 'rgba(59, 130, 246, 0.1)',
  },
  
  // Severity colors for security findings
  severity: {
    critical: { bg: '#7f1d1d', text: '#fecaca', border: '#dc2626' },
    high: { bg: '#7c2d12', text: '#fed7aa', border: '#ea580c' },
    medium: { bg: '#78350f', text: '#fde68a', border: '#d97706' },
    low: { bg: '#1e3a8a', text: '#bfdbfe', border: '#3b82f6' },
    info: { bg: '#374151', text: '#d1d5db', border: '#6b7280' },
  },
  
  // Border colors
  border: {
    primary: '#374151',
    secondary: '#4b5563',
    light: '#6b7280',
  },
};

// =============================================================================
// GRADIENTS
// =============================================================================

export const gradients = {
  primary: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
  secondary: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
  success: 'linear-gradient(135deg, #10b981, #059669)',
  warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
  danger: 'linear-gradient(135deg, #ef4444, #dc2626)',
  dark: 'linear-gradient(135deg, #1f2937, #111827)',
  glow: 'radial-gradient(ellipse at top, #1e3a8a 0%, #0a0e1a 70%)',
};

// =============================================================================
// SPACING SCALE
// =============================================================================

export const spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
  '3xl': '4rem',   // 64px
};

// =============================================================================
// TYPOGRAPHY
// =============================================================================

export const typography = {
  fontFamily: {
    sans: '"Inter", ui-sans-serif, system-ui, sans-serif',
    mono: '"JetBrains Mono", ui-monospace, monospace',
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

// =============================================================================
// SHADOWS
// =============================================================================

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  glow: '0 0 20px rgba(59, 130, 246, 0.3)',
  glowSuccess: '0 0 20px rgba(34, 197, 94, 0.3)',
  glowDanger: '0 0 20px rgba(239, 68, 68, 0.3)',
};

// =============================================================================
// BORDER RADIUS
// =============================================================================

export const borderRadius = {
  none: '0',
  sm: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
  '2xl': '1rem',
  full: '9999px',
};

// =============================================================================
// TRANSITIONS
// =============================================================================

export const transitions = {
  fast: 'all 0.15s ease',
  normal: 'all 0.2s ease',
  slow: 'all 0.3s ease',
  colors: 'color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease',
};

// =============================================================================
// Z-INDEX SCALE
// =============================================================================

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

export default {
  colors,
  gradients,
  spacing,
  typography,
  shadows,
  borderRadius,
  transitions,
  zIndex,
};
