/**
 * Badge - Status and label badges with variants
 */


const Badge = ({
  children,
  variant = "default",
  size = "md",
  dot = false,
  pulse = false,
  icon: Icon,
  className = "",
  onClick,
}) => {
  const variants = {
    default: "bg-gray-700 text-gray-300 border-gray-600",
    primary: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    danger: "bg-red-500/20 text-red-400 border-red-500/30",
    info: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    purple: "bg-purple-500/20 text-purple-400 border-purple-500/30",

    // Solid variants
    "solid-primary": "bg-blue-600 text-white border-blue-500",
    "solid-success": "bg-emerald-600 text-white border-emerald-500",
    "solid-warning": "bg-amber-600 text-white border-amber-500",
    "solid-danger": "bg-red-600 text-white border-red-500",

    // Severity variants
    critical: "bg-red-900/50 text-red-300 border-red-500/50",
    high: "bg-orange-900/50 text-orange-300 border-orange-500/50",
    medium: "bg-yellow-900/50 text-yellow-300 border-yellow-500/50",
    low: "bg-blue-900/50 text-blue-300 border-blue-500/50",
  };

  const sizes = {
    xs: "px-1.5 py-0.5 text-[10px]",
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-sm",
  };

  const dotColors = {
    default: "bg-gray-400",
    primary: "bg-blue-400",
    success: "bg-emerald-400",
    warning: "bg-amber-400",
    danger: "bg-red-400",
    info: "bg-cyan-400",
    purple: "bg-purple-400",
    critical: "bg-red-400",
    high: "bg-orange-400",
    medium: "bg-yellow-400",
    low: "bg-blue-400",
  };

  return (
    <span
      className={`
        inline-flex items-center space-x-1.5
        ${sizes[size]}
        ${variants[variant]}
        font-medium rounded-full border
        ${onClick ? "cursor-pointer hover:opacity-80 transition-opacity" : ""}
        ${className}
      `}
      onClick={onClick}
    >
      {dot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${
                dotColors[variant] || dotColors.default
              }`}
            />
          )}
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${
              dotColors[variant] || dotColors.default
            }`}
          />
        </span>
      )}
      {Icon && <Icon className="h-3 w-3" />}
      <span>{children}</span>
    </span>
  );
};

// Severity Badge preset
export const SeverityBadge = ({ severity, count, className = "" }) => {
  const severityMap = {
    critical: { variant: "critical", label: "Critical" },
    high: { variant: "high", label: "High" },
    medium: { variant: "medium", label: "Medium" },
    low: { variant: "low", label: "Low" },
    info: { variant: "info", label: "Info" },
  };

  const config = severityMap[severity?.toLowerCase()] || severityMap.info;

  return (
    <Badge
      variant={config.variant}
      dot
      pulse={severity === "critical"}
      className={className}
    >
      {config.label}
      {count !== undefined && ` (${count})`}
    </Badge>
  );
};

// Status Badge preset
export const StatusBadge = ({ status, className = "" }) => {
  const statusMap = {
    active: { variant: "success", label: "Active", dot: true, pulse: true },
    inactive: { variant: "default", label: "Inactive", dot: true },
    pending: { variant: "warning", label: "Pending", dot: true, pulse: true },
    completed: { variant: "success", label: "Completed" },
    failed: { variant: "danger", label: "Failed" },
    running: { variant: "primary", label: "Running", dot: true, pulse: true },
  };

  const config = statusMap[status?.toLowerCase()] || {
    variant: "default",
    label: status,
  };

  return (
    <Badge
      variant={config.variant}
      dot={config.dot}
      pulse={config.pulse}
      className={className}
    >
      {config.label}
    </Badge>
  );
};

export default Badge;
