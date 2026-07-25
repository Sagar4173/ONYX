/**
 * ONYX Platform - Reusable UI Components
 * Styled components that use the centralized theme system
 */
import React from "react";
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from "@heroicons/react/24/outline";
import {
  getButtonClasses,
  getBadgeClasses,
  getCardClasses,
  getInputClasses,
  getAlertClasses,
  getProgressClasses,
  loadingStyles,
  statusStyles,
  modalStyles,
  codeStyles,
  navStyles,
  formStyles,
} from "./classNames";
import { animations, dynamicStyles, severityColors } from "./theme";

// =============================================================================
// BUTTON COMPONENT
// =============================================================================

export const Button = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  gradient = false,
  className = "",
  ...props
}) => {
  const gradientClasses = gradient
    ? "bg-gradient-to-r from-cyan-500 via-violet-500 to-cyan-500 text-white font-semibold hover:from-cyan-600 hover:via-violet-600 hover:to-cyan-600 shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
    : getButtonClasses(variant, size);

  return (
    <button
      type="button"
      className={`${gradientClasses} ${className}`}
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
  variant = "ghost",
  size = "md",
  label,
  className = "",
  ...props
}) => {
  const sizeClasses = {
    sm: "p-1.5",
    md: "p-2",
    lg: "p-2.5",
  };

  if (!label) {
    console.warn("IconButton requires a `label` prop for accessibility");
  }

  return (
    <button
      className={`${getButtonClasses(variant, size, true)} ${
        sizeClasses[size]
      } ${className}`}
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
  variant = "default",
  padding = "md",
  hoverable = false,
  className = "",
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

export const CardHeader = ({ children, className = "" }) => (
  <div className={`pb-4 border-b border-gray-700/50 mb-4 ${className}`}>
    {children}
  </div>
);

export const CardTitle = ({ children, className = "" }) => (
  <h3 className={`text-lg font-semibold text-white ${className}`}>
    {children}
  </h3>
);

export const CardDescription = ({ children, className = "" }) => (
  <p className={`text-sm text-gray-400 mt-1 ${className}`}>{children}</p>
);

export const CardContent = ({ children, className = "" }) => (
  <div className={className}>{children}</div>
);

export const CardFooter = ({ children, className = "" }) => (
  <div className={`pt-4 border-t border-gray-700/50 mt-4 ${className}`}>
    {children}
  </div>
);

// =============================================================================
// BADGE COMPONENT
// =============================================================================

export const Badge = React.memo(({
  children,
  variant = "default",
  size = "sm",
  className = "",
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
});

// Severity-specific badge
export const SeverityBadge = React.memo(({ severity, className = "" }) => {
  const severityMap = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low",
    info: "default",
  };

  return (
    <Badge
      variant={severityMap[severity?.toLowerCase()] || "default"}
      className={className}
    >
      {severity?.toUpperCase()}
    </Badge>
  );
});

// =============================================================================
// INPUT COMPONENT
// =============================================================================

export const Input = ({
  variant = "default",
  size = "md",
  error,
  label,
  leadingIcon,
  className = "",
  ...props
}) => {
  const inputVariant = error ? "error" : variant;
  const inputId = React.useId();

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-300 mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {leadingIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            {leadingIcon}
          </div>
        )}
        <input
          id={inputId}
          className={`${getInputClasses(inputVariant, size)} ${leadingIcon ? "pl-11" : ""} ${className}`}
          {...props}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
};

// =============================================================================
// TEXTAREA COMPONENT
// =============================================================================

export const Textarea = ({
  variant = "default",
  error,
  rows = 3,
  className = "",
  ...props
}) => {
  const baseClasses =
    "w-full rounded-lg border bg-gray-800 text-gray-100 placeholder-gray-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0 px-4 py-2 text-sm resize-none";
  const variantClasses = error
    ? "border-red-500 focus:border-red-500 focus:ring-red-500/20"
    : "border-gray-600 focus:border-blue-500 focus:ring-blue-500/20";

  return (
    <div className="w-full">
      <textarea
        className={`${baseClasses} ${variantClasses} ${className}`}
        rows={rows}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
};

// =============================================================================
// SELECT COMPONENT
// =============================================================================

export const Select = ({
  options = [],
  placeholder = "Select...",
  variant = "default",
  size = "md",
  error,
  className = "",
  ...props
}) => {
  return (
    <div className="w-full">
      <select
        className={`${getInputClasses(
          error ? "error" : variant,
          size
        )} cursor-pointer ${className}`}
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
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
};

// =============================================================================
// ALERT COMPONENT
// =============================================================================

export const Alert = ({
  variant = "info",
  title,
  children,
  icon,
  onClose,
  className = "",
}) => {
  return (
    <div className={`${getAlertClasses(variant)} ${className}`}>
      {icon && <span className="w-5 h-5 flex-shrink-0">{icon}</span>}
      <div className="flex-1">
        {title && <p className="font-medium">{title}</p>}
        {children && <p className="text-sm opacity-90 mt-1">{children}</p>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 opacity-70 hover:opacity-100"
        >
          ×
        </button>
      )}
    </div>
  );
};

// =============================================================================
// SPINNER/LOADING COMPONENT
// =============================================================================

export const Spinner = ({ size = "md", className = "" }) => {
  return (
    <div
      className={`${loadingStyles.spinner} ${loadingStyles.sizes[size]} ${className}`}
    />
  );
};

export const LoadingOverlay = ({ message = "Loading..." }) => (
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

export const Skeleton = ({ className = "", variant = "text" }) => {
  const variants = {
    text: "h-4 w-full",
    title: "h-6 w-3/4",
    avatar: "h-10 w-10 rounded-full",
    button: "h-9 w-24",
    card: "h-32 w-full",
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

export const StatusDot = ({ status = "neutral", className = "" }) => {
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
      className={`${statusStyles.dot.base} ${
        statusMap[status] || statusMap.neutral
      } ${className}`}
    />
  );
};

export const StatusIndicator = ({
  status = "neutral",
  label,
  className = "",
}) => {
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
    <span
      className={`${statusStyles.indicator.base} ${
        statusMap[status] || statusMap.neutral
      } ${className}`}
    >
      <StatusDot status={status} />
      {label}
    </span>
  );
};

// =============================================================================
// MODAL COMPONENT
// =============================================================================

const FOCUSABLE_MODAL = 'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
}) => {
  const titleId = React.useId();
  const containerRef = React.useRef(null);

  React.useEffect(() => {
    if (!isOpen) return;
    const container = containerRef.current;
    if (!container) return;
    const prevFocus = document.activeElement;
    const handleKey = (e) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key !== "Tab") return;
      const focusable = container.querySelectorAll(FOCUSABLE_MODAL);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("keydown", handleKey);
      prevFocus?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
    full: "max-w-full mx-4",
  };

  return (
    <div className={modalStyles.overlay} onClick={onClose}>
      <div
        ref={containerRef}
        className={`${modalStyles.container} ${sizeClasses[size]}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className={modalStyles.header}>
            <h2 id={titleId} className={modalStyles.title}>{title}</h2>
            <button
              onClick={onClose}
              aria-label="Close dialog"
              className="text-gray-400 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
            >
              ×
            </button>
          </div>
        )}
        <div className={modalStyles.body}>{children}</div>
        {footer && <div className={modalStyles.footer}>{footer}</div>}
      </div>
    </div>
  );
};

// =============================================================================
// DIVIDER COMPONENT
// =============================================================================

export const Divider = ({ className = "" }) => (
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
  className = "",
}) => (
  <div
    className={`flex flex-col items-center justify-center py-12 text-center ${className}`}
  >
    {icon && <div className="text-gray-500 mb-4">{icon}</div>}
    {title && (
      <h3 className="text-lg font-medium text-gray-300 mb-2">{title}</h3>
    )}
    {description && (
      <p className="text-gray-500 max-w-sm mb-4">{description}</p>
    )}
    {action}
  </div>
);

// =============================================================================
// STAT CARD COMPONENT
// =============================================================================

export const AnimatedCounter = ({ value, duration = 1000, suffix = "" }) => {
  const [count, setCount] = React.useState(0);
  const countRef = React.useRef(null);
  const hasAnimated = React.useRef(false);
  const shouldAnimate = suffix !== "";

  React.useEffect(() => {
    const numValue = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(numValue)) {
      setCount(value);
      return;
    }

    const animate = () => {
      let start = 0;
      const end = numValue;
      const startTime = Date.now();

      const frame = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 4);
        setCount(Math.floor(easeOut * end));
        if (progress < 1) requestAnimationFrame(frame);
      };
      frame();
    };

    if (shouldAnimate) {
      if (countRef.current) {
        const observer = new IntersectionObserver(
          (entries) => {
            if (entries[0].isIntersecting && !hasAnimated.current) {
              hasAnimated.current = true;
              animate();
            }
          },
          { threshold: 0.5 }
        );
        observer.observe(countRef.current);
        return () => observer.disconnect();
      }
    } else {
      animate();
    }
  }, [value, duration, shouldAnimate]);

  return (
    <span ref={countRef}>
      {typeof value === "string" && String(value).includes("%")
        ? `${count}%`
        : count.toLocaleString()}
      {suffix}
    </span>
  );
};

export const StatCard = React.memo(({
  title,
  value,
  change,
  changeType = "neutral",
  icon,
  className = "",
  trend,
  trendPositive = true,
  subtitle,
  gradient,
  bgGradient,
  animated = false,
  animatedDuration = 1000,
  onClick,
}) => {
  const changeColors = {
    increase: "text-green-400",
    decrease: "text-red-400",
    positive: "text-green-400",
    negative: "text-red-400",
    neutral: "text-gray-400",
  };

  const TrendIcon =
    trend >= 0 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon;
  const trendColor = trendPositive
    ? trend >= 0 ? "text-emerald-400" : "text-red-400"
    : trend >= 0 ? "text-red-400" : "text-emerald-400";

  if (gradient) {
    const cardBg = bgGradient || "bg-gray-800/30";
    return (
      <div
        onClick={onClick}
        className={`group relative ${cardBg} rounded-2xl p-5 border border-gray-800/50
          hover:border-gray-700/50 transition-all ${onClick ? "cursor-pointer" : ""} ${className}`}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-gray-800/30 to-gray-700/30 rounded-2xl blur-xl group-hover:blur-2xl transition-all" />
        <div className="relative">
          <div className="flex items-center justify-between mb-3">
            <div
              className={`p-2.5 rounded-xl bg-gradient-to-r ${gradient} shadow-lg`}
            >
              {icon}
            </div>
            {trend !== undefined && trend !== null && (
              <div
                className={`flex items-center gap-1 px-2 py-0.5 rounded-lg text-sm font-medium ${
                  trend >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                <TrendIcon className="h-4 w-4" />
                {Math.abs(trend)}%
              </div>
            )}
          </div>
          <h3 className="text-2xl font-bold text-white mb-1">
            {animated ? <AnimatedCounter value={value} duration={animatedDuration} /> : value}
          </h3>
          <p className="text-gray-400 text-sm">{title}</p>
        </div>
      </div>
    );
  }

  return (
    <Card className={className}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">
            {animated ? <AnimatedCounter value={value} duration={animatedDuration} /> : value}
          </p>
          {change !== undefined && (
            <p className={`text-sm mt-1 ${changeColors[changeType]}`}>
              {changeType === "increase" && "↑"}
              {changeType === "decrease" && "↓"}
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
});

// =============================================================================
// PROGRESS BAR COMPONENT
// =============================================================================

export const ProgressBar = ({
  value = 0,
  max = 100,
  color = "primary",
  size = "md",
  showLabel = false,
  animated = false,
  className = "",
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const { container, bar } = getProgressClasses(color, size);

  return (
    <div className={`${className}`}>
      <div
        className={container}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          className={`${bar} ${animated ? "animate-pulse" : ""}`}
          style={dynamicStyles.progressWidth(percentage)}
        />
      </div>
      {showLabel && (
        <span className="text-xs text-gray-400 mt-1">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
};

// =============================================================================
// SEVERITY PROGRESS BAR (for vulnerability counts)
// =============================================================================

export const SeverityProgressBar = ({
  critical = 0,
  high = 0,
  medium = 0,
  low = 0,
  size = "md",
  className = "",
}) => {
  const total = critical + high + medium + low || 1;

  const getWidth = (value) => `${(value / total) * 100}%`;

  const heights = {
    xs: "h-1",
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
    xl: "h-4",
  };

  return (
    <div
      className={`w-full ${heights[size]} bg-gray-700 rounded-full overflow-hidden flex ${className}`}
    >
      <div
        className="bg-red-500 transition-all duration-500"
        style={{ width: getWidth(critical) }}
      />
      <div
        className="bg-orange-500 transition-all duration-500"
        style={{ width: getWidth(high) }}
      />
      <div
        className="bg-yellow-500 transition-all duration-500"
        style={{ width: getWidth(medium) }}
      />
      <div
        className="bg-blue-500 transition-all duration-500"
        style={{ width: getWidth(low) }}
      />
    </div>
  );
};

// =============================================================================
// ANIMATED LIST ITEM (handles stagger animation)
// =============================================================================

export const AnimatedListItem = ({
  children,
  index,
  delay = 0.1,
  className = "",
  ...props
}) => {
  return (
    <div
      className={`animate-fade-in-up ${className}`}
      style={animations.staggerDelay(index, delay)}
      {...props}
    >
      {children}
    </div>
  );
};

// =============================================================================
// DONUT/RING CHART COMPONENT
// =============================================================================

export const DonutChart = ({
  value = 0,
  max = 100,
  size = 120,
  strokeWidth = 8,
  color = "#3b82f6",
  bgColor = "#374151",
  children,
  className = "",
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div
      className={`relative ${className}`}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={bgColor}
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children || (
          <span className="text-xl font-bold text-white">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// CODE DISPLAY COMPONENT
// =============================================================================

export const Code = ({ children, inline = false, className = "" }) => {
  if (inline) {
    return (
      <code className={`${codeStyles.inline} ${className}`}>{children}</code>
    );
  }

  return (
    <pre className={`${codeStyles.block} ${className}`}>
      <code>{children}</code>
    </pre>
  );
};

// =============================================================================
// TABS COMPONENT
// =============================================================================

export const Tabs = ({ tabs, activeTab, onChange, className = "" }) => {
  return (
    <div className={`border-b border-gray-700 ${className}`}>
      <nav className="flex gap-1" role="tablist" aria-orientation="horizontal">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            onClick={() => onChange(tab.id)}
            className={
              activeTab === tab.id ? navStyles.tabActive : navStyles.tab
            }
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
            {tab.count !== undefined && (
              <Badge size="xs" variant="default" className="ml-2">
                {tab.count}
              </Badge>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
};

// =============================================================================
// FORM COMPONENTS
// =============================================================================

export const FormGroup = ({ children, className = "" }) => (
  <div className={`${formStyles.group} ${className}`}>{children}</div>
);

export const FormLabel = ({ children, required = false, className = "" }) => (
  <label className={`${formStyles.label} ${className}`}>
    {children}
    {required && <span className={formStyles.required}>*</span>}
  </label>
);

export const FormHint = ({ children, className = "" }) => (
  <p className={`${formStyles.hint} ${className}`}>{children}</p>
);

export const FormError = ({ children, className = "" }) => (
  <p className={`${formStyles.error} ${className}`}>{children}</p>
);

// =============================================================================
// TOOLTIP COMPONENT (simple)
// =============================================================================

export const Tooltip = ({ content, children, position = "top" }) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const tooltipId = React.useId();

  const positions = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      aria-describedby={isVisible ? tooltipId : undefined}
    >
      {children}
      {isVisible && (
        <div
          id={tooltipId}
          role="tooltip"
          className={`absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded shadow-lg border border-gray-700 whitespace-nowrap ${positions[position]}`}
        >
          {content}
        </div>
      )}
    </div>
  );
};

// =============================================================================
// AVATAR COMPONENT
// =============================================================================

export const Avatar = ({ src, alt, name, size = "md", className = "" }) => {
  const sizes = {
    xs: "w-6 h-6 text-xs",
    sm: "w-8 h-8 text-sm",
    md: "w-10 h-10 text-base",
    lg: "w-12 h-12 text-lg",
    xl: "w-16 h-16 text-xl",
  };

  const getInitials = (name) => {
    if (!name) return "?";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (src) {
    return (
      <img
        src={src}
        alt={alt || name}
        className={`${sizes[size]} rounded-full object-cover ${className}`}
      />
    );
  }

  return (
    <div
      className={`${sizes[size]} rounded-full bg-gray-700 flex items-center justify-center font-medium text-gray-300 ${className}`}
    >
      {getInitials(name)}
    </div>
  );
};

// =============================================================================
// TRUNCATE TEXT COMPONENT
// =============================================================================

export const Truncate = ({ text, maxLength = 100, className = "" }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  if (!text || text.length <= maxLength) {
    return <span className={className}>{text}</span>;
  }

  return (
    <span className={className}>
      {isExpanded ? text : `${text.slice(0, maxLength)}...`}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="ml-1 text-blue-400 hover:text-blue-300 text-sm"
      >
        {isExpanded ? "Show less" : "Show more"}
      </button>
    </span>
  );
};

// =============================================================================
// DATA TABLE COMPONENT
// =============================================================================

const TableSkeleton = ({ rows = 5, columns = 4 }) => (
  <>
    {Array.from({ length: rows }).map((_, i) => (
      <tr key={i} className="border-b border-gray-700/50">
        {Array.from({ length: columns }).map((_, j) => (
          <td key={j} className="px-4 py-3">
            <div className="h-4 bg-gray-700/50 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
          </td>
        ))}
      </tr>
    ))}
  </>
);

export const DataTable = ({
  columns = [],
  data = [],
  onSort,
  sortKey,
  sortDirection,
  onPageChange,
  currentPage = 1,
  pageSize = 20,
  totalItems,
  loading = false,
  emptyMessage = "No data available",
  onRowClick,
  className = "",
}) => {
  const totalPages = Math.ceil((totalItems || data.length) / pageSize);

  return (
    <div className={`overflow-x-auto rounded-xl border border-gray-700/50 ${className}`}>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-800/50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider ${
                  col.sortable ? "cursor-pointer hover:text-white select-none" : ""
                }`}
                style={col.width ? { width: col.width } : undefined}
                onClick={() => {
                  if (col.sortable && onSort) {
                    onSort(col.key);
                  }
                }}
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && sortKey === col.key && (
                    <span className="text-blue-400">
                      {sortDirection === "asc" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700/50">
          {loading ? (
            <TableSkeleton rows={5} columns={columns.length} />
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-gray-400"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr
                key={row.id || row._id || i}
                className={`transition-colors duration-150 ${
                  onRowClick ? "cursor-pointer hover:bg-gray-800/30" : "hover:bg-gray-800/10"
                }`}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-gray-300">
                    {col.render ? col.render(row[col.key], row) : row[col.key] ?? "-"}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-700/50 bg-gray-800/30">
          <span className="text-sm text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-1 text-sm rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-1 text-sm rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// CONFIRM DIALOG COMPONENT
// =============================================================================

export const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm",
  message = "Are you sure?",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  requireTypeToConfirm = false,
  confirmText = "",
}) => {
  const [typedText, setTypedText] = React.useState("");
  const titleId = React.useId();

  if (!isOpen) return null;

  const buttonColors = {
    danger: "bg-red-600 hover:bg-red-700 focus:ring-red-500",
    warning: "bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500",
    primary: "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500",
  };

  const canConfirm = requireTypeToConfirm
    ? typedText === confirmText
    : true;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700/50 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id={titleId} className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-gray-400 text-sm mb-4">{message}</p>

        {requireTypeToConfirm && (
          <div className="mb-4">
            <p className="text-sm text-gray-400 mb-2">
              Type <span className="font-mono text-red-400 bg-red-900/30 px-1.5 py-0.5 rounded">{confirmText}</span> to confirm:
            </p>
            <input
              type="text"
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700/50 rounded-lg text-white text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
              autoFocus
            />
          </div>
        )}

        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={() => { onConfirm(); onClose(); }}
            disabled={!canConfirm}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-all disabled:opacity-50 ${buttonColors[variant]}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// METRIC CARD COMPONENT
// =============================================================================

export const MetricCard = React.memo(({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  direction = "up",
  color = "blue",
  className = "",
}) => {
  const colorMap = {
    blue: "from-blue-500 to-cyan-500",
    green: "from-emerald-500 to-green-500",
    red: "from-red-500 to-rose-500",
    yellow: "from-yellow-500 to-amber-500",
    purple: "from-purple-500 to-violet-500",
    indigo: "from-indigo-500 to-blue-500",
  };

  return (
    <div className={`bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        {Icon && (
          <div className={`p-2.5 rounded-xl bg-gradient-to-r ${colorMap[color] || colorMap.blue} shadow-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
        )}
        {trend !== undefined && (
          <span className={`text-sm font-medium ${direction === "up" ? "text-green-400" : "text-red-400"}`}>
            {direction === "up" ? "↑" : "↓"} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-gray-400 mt-1">{title}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
    </div>
  );
});

// =============================================================================
// STATUS BADGE COMPONENT
// =============================================================================

const statusBadgeVariants = {
  active: "bg-green-900/30 text-green-400 border-green-700/50",
  inactive: "bg-gray-700/30 text-gray-300 border-gray-700/50",
  suspended: "bg-red-900/30 text-red-400 border-red-700/50",
  pending: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
  verified: "bg-green-900/30 text-green-400 border-green-700/50",
  unverified: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
  healthy: "bg-green-900/30 text-green-400 border-green-700/50",
  warning: "bg-yellow-900/30 text-yellow-400 border-yellow-700/50",
  critical: "bg-red-900/30 text-red-400 border-red-700/50",
};

export const StatusBadge = ({ status = "inactive", label, className = "" }) => {
  const variant = statusBadgeVariants[status] || statusBadgeVariants.inactive;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${variant} ${className}`}>
      {label || status}
    </span>
  );
};

// =============================================================================
// FINDING CARD COMPONENT
// =============================================================================

export const FindingCard = React.memo(({
  title,
  severity = "info",
  scanner,
  filePath,
  ruleId,
  status = "open",
  onClick,
  className = "",
}) => {
  const severityGradients = {
    critical: "from-red-500 to-rose-600",
    high: "from-orange-500 to-red-500",
    medium: "from-yellow-500 to-amber-500",
    low: "from-blue-500 to-cyan-500",
    info: "from-gray-500 to-gray-400",
  };

  const severityLabels = {
    critical: "text-red-400 bg-red-900/30 border-red-700/50",
    high: "text-orange-400 bg-orange-900/30 border-orange-700/50",
    medium: "text-yellow-400 bg-yellow-900/30 border-yellow-700/50",
    low: "text-blue-400 bg-blue-900/30 border-blue-700/50",
    info: "text-gray-400 bg-gray-700/30 border-gray-700/50",
  };

  return (
    <div
      className={`bg-gray-800/30 border border-gray-700/50 rounded-xl p-4 hover:border-gray-600/50 transition-all ${
        onClick ? "cursor-pointer hover:-translate-y-0.5" : ""
      } ${className}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`w-1 h-10 rounded-full bg-gradient-to-b ${severityGradients[severity] || severityGradients.info} flex-shrink-0`} />
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{title}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-1.5 py-0.5 text-xs font-medium rounded border ${severityLabels[severity] || severityLabels.info}`}>
                {severity.toUpperCase()}
              </span>
              {scanner && <span className="text-xs text-gray-500">{scanner}</span>}
            </div>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>
      {(filePath || ruleId) && (
        <div className="mt-3 pt-3 border-t border-gray-700/50 flex items-center gap-4 text-xs text-gray-500">
          {filePath && <span className="truncate">{filePath}</span>}
          {ruleId && <span className="font-mono">{ruleId}</span>}
        </div>
      )}
    </div>
  );
});

// =============================================================================
// PAGE TRANSITION COMPONENT
// =============================================================================

export const PageTransition = ({ children, className = "" }) => (
  <div className={`page-enter ${className}`}>
    {children}
  </div>
);

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
  ProgressBar,
  SeverityProgressBar,
  AnimatedListItem,
  DonutChart,
  Code,
  Tabs,
  FormGroup,
  FormLabel,
  FormHint,
  FormError,
  Tooltip,
  Avatar,
  Truncate,
  DataTable,
  ConfirmDialog,
  MetricCard,
  StatusBadge,
  FindingCard,
  PageTransition,
};
