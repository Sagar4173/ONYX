/**
 * ONYX Platform - Reusable UI Components
 * Styled components that use the centralized theme system
 */
import React from 'react';
import { getButtonClasses, getBadgeClasses, getCardClasses, getInputClasses, getAlertClasses, loadingStyles, statusStyles, modalStyles } from './classNames';

// =============================================================================
// BUTTON COMPONENT
// =============================================================================

export const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  isLoading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  className = '',
  ...props 
}) => {
  return (
    <button
      className={`${getButtonClasses(variant, size)} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Spinner size="sm" />
      ) : (
        <>
          {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
        </>
      )}
    </button>
  );
};

// =============================================================================
// ICON BUTTON COMPONENT
// =============================================================================

export const IconButton = ({ 
  icon, 
  variant = 'ghost', 
  size = 'md',
  label,
  className = '',
  ...props 
}) => {
  const sizeClasses = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-2.5',
  };
  
  return (
    <button
      className={`${getButtonClasses(variant, size, true)} ${sizeClasses[size]} ${className}`}
      aria-label={label}
      title={label}
      {...props}
    >
      {icon}
    </button>
  );
};

// =============================================================================
// CARD COMPONENT
// =============================================================================

export const Card = ({ 
  children, 
  variant = 'default', 
  padding = 'md',
  hoverable = false,
  className = '',
  ...props 
}) => {
  return (
    <div 
      className={`${getCardClasses(variant, padding, hoverable)} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '' }) => (
  <div className={`pb-4 border-b border-gray-700/50 mb-4 ${className}`}>
    {children}
  </div>
);

export const CardTitle = ({ children, className = '' }) => (
  <h3 className={`text-lg font-semibold text-white ${className}`}>
    {children}
  </h3>
);

export const CardDescription = ({ children, className = '' }) => (
  <p className={`text-sm text-gray-400 mt-1 ${className}`}>
    {children}
  </p>
);

export const CardContent = ({ children, className = '' }) => (
  <div className={className}>{children}</div>
);

export const CardFooter = ({ children, className = '' }) => (
  <div className={`pt-4 border-t border-gray-700/50 mt-4 ${className}`}>
    {children}
  </div>
);

// =============================================================================
// BADGE COMPONENT
// =============================================================================

export const Badge = ({ 
  children, 
  variant = 'default', 
  size = 'sm',
  className = '',
  ...props 
}) => {
  return (
    <span 
      className={`${getBadgeClasses(variant, size)} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

// Severity-specific badge
export const SeverityBadge = ({ severity, className = '' }) => {
  const severityMap = {
    critical: 'critical',
    high: 'high',
    medium: 'medium',
    low: 'low',
    info: 'default',
  };
  
  return (
    <Badge variant={severityMap[severity?.toLowerCase()] || 'default'} className={className}>
      {severity?.toUpperCase()}
    </Badge>
  );
};

// =============================================================================
// INPUT COMPONENT
// =============================================================================

export const Input = ({ 
  variant = 'default', 
  size = 'md',
  error,
  className = '',
  ...props 
}) => {
  const inputVariant = error ? 'error' : variant;
  
  return (
    <div className="w-full">
      <input 
        className={`${getInputClasses(inputVariant, size)} ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
};

// =============================================================================
// TEXTAREA COMPONENT
// =============================================================================

export const Textarea = ({ 
  variant = 'default', 
  error,
  rows = 3,
  className = '',
  ...props 
}) => {
  const baseClasses = 'w-full rounded-lg border bg-gray-800 text-gray-100 placeholder-gray-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0 px-4 py-2 text-sm resize-none';
  const variantClasses = error 
    ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
    : 'border-gray-600 focus:border-blue-500 focus:ring-blue-500/20';
  
  return (
    <div className="w-full">
      <textarea 
        className={`${baseClasses} ${variantClasses} ${className}`}
        rows={rows}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
};

// =============================================================================
// SELECT COMPONENT
// =============================================================================

export const Select = ({ 
  options = [], 
  placeholder = 'Select...',
  variant = 'default',
  size = 'md',
  error,
  className = '',
  ...props 
}) => {
  return (
    <div className="w-full">
      <select 
        className={`${getInputClasses(error ? 'error' : variant, size)} cursor-pointer ${className}`}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="mt-1 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
};

// =============================================================================
// ALERT COMPONENT
// =============================================================================

export const Alert = ({ 
  variant = 'info', 
  title,
  children,
  icon,
  onClose,
  className = '',
}) => {
  return (
    <div className={`${getAlertClasses(variant)} ${className}`}>
      {icon && <span className="w-5 h-5 flex-shrink-0">{icon}</span>}
      <div className="flex-1">
        {title && <p className="font-medium">{title}</p>}
        {children && <p className="text-sm opacity-90 mt-1">{children}</p>}
      </div>
      {onClose && (
        <button onClick={onClose} className="flex-shrink-0 opacity-70 hover:opacity-100">
          ×
        </button>
      )}
    </div>
  );
};

// =============================================================================
// SPINNER/LOADING COMPONENT
// =============================================================================

export const Spinner = ({ size = 'md', className = '' }) => {
  return (
    <div 
      className={`${loadingStyles.spinner} ${loadingStyles.sizes[size]} ${className}`}
    />
  );
};

export const LoadingOverlay = ({ message = 'Loading...' }) => (
  <div className="absolute inset-0 bg-gray-900/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
    <div className="flex flex-col items-center gap-3">
      <Spinner size="lg" />
      <span className="text-gray-300 text-sm">{message}</span>
    </div>
  </div>
);

// =============================================================================
// SKELETON LOADING
// =============================================================================

export const Skeleton = ({ className = '', variant = 'text' }) => {
  const variants = {
    text: 'h-4 w-full',
    title: 'h-6 w-3/4',
    avatar: 'h-10 w-10 rounded-full',
    button: 'h-9 w-24',
    card: 'h-32 w-full',
  };
  
  return (
    <div 
      className={`${loadingStyles.skeleton} ${variants[variant]} ${className}`}
    />
  );
};

// =============================================================================
// STATUS INDICATOR
// =============================================================================

export const StatusDot = ({ status = 'neutral', className = '' }) => {
  const statusMap = {
    success: statusStyles.dot.success,
    active: statusStyles.dot.success,
    online: statusStyles.dot.success,
    warning: statusStyles.dot.warning,
    pending: statusStyles.dot.warning,
    danger: statusStyles.dot.danger,
    error: statusStyles.dot.danger,
    offline: statusStyles.dot.danger,
    info: statusStyles.dot.info,
    neutral: statusStyles.dot.neutral,
    inactive: statusStyles.dot.neutral,
  };
  
  return (
    <span 
      className={`${statusStyles.dot.base} ${statusMap[status] || statusMap.neutral} ${className}`}
    />
  );
};

export const StatusIndicator = ({ status = 'neutral', label, className = '' }) => {
  const statusMap = {
    success: statusStyles.indicator.success,
    active: statusStyles.indicator.success,
    warning: statusStyles.indicator.warning,
    pending: statusStyles.indicator.warning,
    danger: statusStyles.indicator.danger,
    error: statusStyles.indicator.danger,
    info: statusStyles.indicator.info,
    neutral: statusStyles.indicator.neutral,
  };
  
  return (
    <span className={`${statusStyles.indicator.base} ${statusMap[status] || statusMap.neutral} ${className}`}>
      <StatusDot status={status} />
      {label}
    </span>
  );
};

// =============================================================================
// MODAL COMPONENT
// =============================================================================

export const Modal = ({ 
  isOpen, 
  onClose, 
  title,
  children,
  footer,
  size = 'md',
}) => {
  if (!isOpen) return null;
  
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  };
  
  return (
    <div className={modalStyles.overlay} onClick={onClose}>
      <div 
        className={`${modalStyles.container} ${sizeClasses[size]}`}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className={modalStyles.header}>
            <h2 className={modalStyles.title}>{title}</h2>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ×
            </button>
          </div>
        )}
        <div className={modalStyles.body}>
          {children}
        </div>
        {footer && (
          <div className={modalStyles.footer}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// DIVIDER COMPONENT
// =============================================================================

export const Divider = ({ className = '' }) => (
  <hr className={`border-gray-700/50 my-4 ${className}`} />
);

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

export const EmptyState = ({ 
  icon,
  title,
  description,
  action,
  className = '',
}) => (
  <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
    {icon && <div className="text-gray-500 mb-4">{icon}</div>}
    {title && <h3 className="text-lg font-medium text-gray-300 mb-2">{title}</h3>}
    {description && <p className="text-gray-500 max-w-sm mb-4">{description}</p>}
    {action}
  </div>
);

// =============================================================================
// STAT CARD COMPONENT
// =============================================================================

export const StatCard = ({ 
  title, 
  value, 
  change,
  changeType = 'neutral', // 'increase', 'decrease', 'neutral'
  icon,
  className = '',
}) => {
  const changeColors = {
    increase: 'text-green-400',
    decrease: 'text-red-400',
    neutral: 'text-gray-400',
  };
  
  return (
    <Card className={className}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {change !== undefined && (
            <p className={`text-sm mt-1 ${changeColors[changeType]}`}>
              {changeType === 'increase' && '↑'}
              {changeType === 'decrease' && '↓'}
              {change}
            </p>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-gray-700/50 rounded-lg text-gray-400">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
};

export default {
  Button,
  IconButton,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  SeverityBadge,
  Input,
  Textarea,
  Select,
  Alert,
  Spinner,
  LoadingOverlay,
  Skeleton,
  StatusDot,
  StatusIndicator,
  Modal,
  Divider,
  EmptyState,
  StatCard,
};
