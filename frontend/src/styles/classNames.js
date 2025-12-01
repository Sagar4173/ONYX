/**
 * ONYX Platform - Tailwind CSS Class Utilities
 * Pre-defined class combinations for consistent component styling
 * Use these instead of writing inline Tailwind classes
 */

// =============================================================================
// BUTTON STYLES
// =============================================================================

export const buttonStyles = {
  // Base button classes
  base: 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed',
  
  // Size variants
  sizes: {
    xs: 'px-2 py-1 text-xs gap-1',
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-5 py-2.5 text-base gap-2',
    xl: 'px-6 py-3 text-lg gap-2.5',
  },
  
  // Color variants
  variants: {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-700 text-gray-200 hover:bg-gray-600 focus:ring-gray-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    warning: 'bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500',
    ghost: 'bg-transparent text-gray-300 hover:bg-gray-800 hover:text-white focus:ring-gray-500',
    outline: 'border border-gray-600 text-gray-300 hover:bg-gray-800 hover:border-gray-500 focus:ring-gray-500',
    link: 'text-blue-400 hover:text-blue-300 hover:underline p-0',
  },
  
  // Icon-only button
  icon: {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-2.5',
  },
};

// Helper function to get button classes
export const getButtonClasses = (variant = 'primary', size = 'md', isIconOnly = false) => {
  const sizeClass = isIconOnly ? buttonStyles.icon[size] : buttonStyles.sizes[size];
  return `${buttonStyles.base} ${sizeClass} ${buttonStyles.variants[variant]}`;
};

// =============================================================================
// CARD STYLES
// =============================================================================

export const cardStyles = {
  base: 'bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl',
  
  variants: {
    default: 'bg-gray-800/50 border-gray-700/50',
    elevated: 'bg-gray-800/70 border-gray-600/50 shadow-lg',
    outlined: 'bg-transparent border-gray-600',
    success: 'bg-green-900/20 border-green-700/50',
    danger: 'bg-red-900/20 border-red-700/50',
    warning: 'bg-yellow-900/20 border-yellow-700/50',
    info: 'bg-blue-900/20 border-blue-700/50',
  },
  
  padding: {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8',
  },
  
  hover: 'hover:bg-gray-700/50 hover:border-gray-600/50 transition-all duration-200',
};

export const getCardClasses = (variant = 'default', padding = 'md', hoverable = false) => {
  const classes = [
    'backdrop-blur-sm rounded-xl border',
    cardStyles.variants[variant],
    cardStyles.padding[padding],
  ];
  if (hoverable) classes.push(cardStyles.hover);
  return classes.join(' ');
};

// =============================================================================
// INPUT STYLES
// =============================================================================

export const inputStyles = {
  base: 'w-full rounded-lg border bg-gray-800 text-gray-100 placeholder-gray-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0',
  
  sizes: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  },
  
  variants: {
    default: 'border-gray-600 focus:border-blue-500 focus:ring-blue-500/20',
    error: 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
    success: 'border-green-500 focus:border-green-500 focus:ring-green-500/20',
  },
};

export const getInputClasses = (variant = 'default', size = 'md') => {
  return `${inputStyles.base} ${inputStyles.sizes[size]} ${inputStyles.variants[variant]}`;
};

// =============================================================================
// BADGE STYLES
// =============================================================================

export const badgeStyles = {
  base: 'inline-flex items-center font-medium rounded-full',
  
  sizes: {
    xs: 'px-1.5 py-0.5 text-xs',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-sm',
  },
  
  variants: {
    default: 'bg-gray-700 text-gray-300',
    primary: 'bg-blue-900/50 text-blue-300 border border-blue-700/50',
    success: 'bg-green-900/50 text-green-300 border border-green-700/50',
    danger: 'bg-red-900/50 text-red-300 border border-red-700/50',
    warning: 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50',
    info: 'bg-cyan-900/50 text-cyan-300 border border-cyan-700/50',
    // Severity badges
    critical: 'bg-red-900/70 text-red-200 border border-red-600',
    high: 'bg-orange-900/70 text-orange-200 border border-orange-600',
    medium: 'bg-yellow-900/70 text-yellow-200 border border-yellow-600',
    low: 'bg-blue-900/70 text-blue-200 border border-blue-600',
  },
};

export const getBadgeClasses = (variant = 'default', size = 'sm') => {
  return `${badgeStyles.base} ${badgeStyles.sizes[size]} ${badgeStyles.variants[variant]}`;
};

// =============================================================================
// TABLE STYLES
// =============================================================================

export const tableStyles = {
  container: 'overflow-x-auto rounded-lg border border-gray-700/50',
  table: 'min-w-full divide-y divide-gray-700',
  thead: 'bg-gray-800/50',
  th: 'px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider',
  tbody: 'divide-y divide-gray-700/50 bg-gray-800/30',
  tr: 'hover:bg-gray-700/30 transition-colors duration-150',
  td: 'px-4 py-3 text-sm text-gray-300 whitespace-nowrap',
  tdWrap: 'px-4 py-3 text-sm text-gray-300',
};

// =============================================================================
// LAYOUT STYLES
// =============================================================================

export const layoutStyles = {
  // Page containers
  page: 'min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900',
  pageContent: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8',
  
  // Section
  section: 'space-y-6',
  sectionHeader: 'flex items-center justify-between',
  sectionTitle: 'text-2xl font-bold text-white',
  sectionDescription: 'text-gray-400 mt-1',
  
  // Grid layouts
  grid: {
    cols2: 'grid grid-cols-1 md:grid-cols-2 gap-4',
    cols3: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4',
    cols4: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4',
  },
  
  // Flex layouts
  flex: {
    center: 'flex items-center justify-center',
    between: 'flex items-center justify-between',
    start: 'flex items-center justify-start',
    end: 'flex items-center justify-end',
    col: 'flex flex-col',
    colCenter: 'flex flex-col items-center',
  },
};

// =============================================================================
// STATUS INDICATOR STYLES
// =============================================================================

export const statusStyles = {
  dot: {
    base: 'w-2 h-2 rounded-full',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
    info: 'bg-blue-500',
    neutral: 'bg-gray-500',
  },
  
  indicator: {
    base: 'inline-flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium',
    success: 'bg-green-900/30 text-green-400',
    warning: 'bg-yellow-900/30 text-yellow-400',
    danger: 'bg-red-900/30 text-red-400',
    info: 'bg-blue-900/30 text-blue-400',
    neutral: 'bg-gray-700/50 text-gray-400',
  },
};

// =============================================================================
// MODAL STYLES
// =============================================================================

export const modalStyles = {
  overlay: 'fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4',
  container: 'bg-gray-800 border border-gray-700 rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden',
  header: 'px-6 py-4 border-b border-gray-700 flex items-center justify-between',
  title: 'text-lg font-semibold text-white',
  body: 'px-6 py-4 overflow-y-auto',
  footer: 'px-6 py-4 border-t border-gray-700 flex items-center justify-end gap-3',
};

// =============================================================================
// ALERT STYLES
// =============================================================================

export const alertStyles = {
  base: 'rounded-lg p-4 flex items-start gap-3',
  variants: {
    success: 'bg-green-900/30 border border-green-700/50 text-green-300',
    danger: 'bg-red-900/30 border border-red-700/50 text-red-300',
    warning: 'bg-yellow-900/30 border border-yellow-700/50 text-yellow-300',
    info: 'bg-blue-900/30 border border-blue-700/50 text-blue-300',
  },
  icon: 'w-5 h-5 flex-shrink-0 mt-0.5',
  content: 'flex-1',
  title: 'font-medium',
  message: 'text-sm opacity-90 mt-1',
};

export const getAlertClasses = (variant = 'info') => {
  return `${alertStyles.base} ${alertStyles.variants[variant]}`;
};

// =============================================================================
// TOOLTIP STYLES
// =============================================================================

export const tooltipStyles = {
  base: 'absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded shadow-lg border border-gray-700',
};

// =============================================================================
// LOADING STYLES
// =============================================================================

export const loadingStyles = {
  spinner: 'animate-spin rounded-full border-2 border-gray-600 border-t-blue-500',
  sizes: {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  },
  skeleton: 'animate-pulse bg-gray-700 rounded',
};

export default {
  buttonStyles,
  getButtonClasses,
  cardStyles,
  getCardClasses,
  inputStyles,
  getInputClasses,
  badgeStyles,
  getBadgeClasses,
  tableStyles,
  layoutStyles,
  statusStyles,
  modalStyles,
  alertStyles,
  getAlertClasses,
  tooltipStyles,
  loadingStyles,
};
