/**
 * Card - Versatile card components with glass morphism
 */
import { motion } from "framer-motion";
import { ChevronRightIcon } from "@heroicons/react/24/outline";

const Card = ({
  children,
  variant = "default",
  padding = "md",
  hover = false,
  onClick,
  className = "",
  ...props
}) => {
  const variants = {
    default: "bg-gray-800/30 border-gray-700/30",
    glass: "glass-card border-white/10",
    solid: "bg-gray-800 border-gray-700",
    elevated: "bg-gray-800/50 border-gray-700/50 shadow-xl",
    gradient:
      "bg-gradient-to-br from-gray-800/50 to-gray-900/50 border-gray-700/30",
  };

  const paddings = {
    none: "",
    sm: "p-4",
    md: "p-5 sm:p-6",
    lg: "p-6 sm:p-8",
  };

  const Component = onClick ? motion.button : motion.div;

  return (
    <Component
      onClick={onClick}
      whileHover={hover ? { scale: 1.02, y: -2 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={`
        rounded-2xl border backdrop-blur-sm
        ${variants[variant]}
        ${paddings[padding]}
        ${onClick ? "cursor-pointer" : ""}
        ${
          hover ? "transition-shadow hover:shadow-xl hover:shadow-black/20" : ""
        }
        ${className}
      `}
      {...props}
    >
      {children}
    </Component>
  );
};

/**
 * Card Header
 */
export const CardHeader = ({
  title,
  subtitle,
  icon: Icon,
  action,
  className = "",
}) => (
  <div className={`flex items-center justify-between ${className}`}>
    <div className="flex items-center gap-3">
      {Icon && (
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20">
          <Icon className="h-5 w-5 text-blue-400" />
        </div>
      )}
      <div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        {subtitle && <p className="text-sm text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
    {action}
  </div>
);

/**
 * Card Content
 */
export const CardContent = ({ children, className = "" }) => (
  <div className={`mt-4 ${className}`}>{children}</div>
);

/**
 * Card Footer
 */
export const CardFooter = ({ children, className = "" }) => (
  <div className={`mt-4 pt-4 border-t border-gray-700/50 ${className}`}>
    {children}
  </div>
);

/**
 * Clickable List Card
 */
export const ListCard = ({
  title,
  subtitle,
  icon: Icon,
  iconGradient = "from-blue-500 to-purple-500",
  badge,
  onClick,
  href,
  className = "",
}) => {
  const content = (
    <>
      <div className="flex items-center gap-4 min-w-0">
        {Icon && (
          <div
            className={`p-2.5 rounded-xl bg-gradient-to-br ${iconGradient} flex-shrink-0`}
          >
            <Icon className="h-5 w-5 text-white" />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <h4 className="text-white font-medium truncate group-hover:text-blue-400 transition-colors">
            {title}
          </h4>
          {subtitle && (
            <p className="text-sm text-gray-400 truncate mt-0.5">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        {badge}
        <ChevronRightIcon className="h-5 w-5 text-gray-600 group-hover:text-gray-400 transition-colors" />
      </div>
    </>
  );

  const baseClassName = `
    group flex items-center justify-between gap-4
    p-4 rounded-xl
    bg-gray-800/30 border border-gray-700/30
    hover:bg-gray-800/50 hover:border-gray-600/50
    transition-all duration-300
    ${className}
  `;

  if (href) {
    return (
      <a href={href} className={baseClassName}>
        {content}
      </a>
    );
  }

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ x: 4 }}
      className={baseClassName}
    >
      {content}
    </motion.button>
  );
};

/**
 * Stats Card with icon and trend
 */
export const StatsCard = ({
  title,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  iconGradient = "from-blue-500 to-cyan-500",
  className = "",
}) => {
  const changeColors = {
    positive: "text-emerald-400 bg-emerald-500/10",
    negative: "text-red-400 bg-red-500/10",
    neutral: "text-gray-400 bg-gray-500/10",
  };

  return (
    <Card hover className={className}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 font-medium">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold text-white mt-1">
            {value}
          </p>
          {change && (
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium mt-2 ${changeColors[changeType]}`}
            >
              {change}
            </span>
          )}
        </div>
        {Icon && (
          <div className={`p-3 rounded-xl bg-gradient-to-br ${iconGradient}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        )}
      </div>
    </Card>
  );
};

/**
 * Feature Card with gradient border
 */
export const GradientCard = ({
  children,
  gradient = "from-blue-500 via-purple-500 to-pink-500",
  padding = "md",
  className = "",
}) => (
  <div
    className={`relative p-[1px] rounded-2xl bg-gradient-to-r ${gradient} ${className}`}
  >
    <div
      className={`rounded-2xl bg-gray-900 ${
        padding === "md" ? "p-5 sm:p-6" : "p-4"
      }`}
    >
      {children}
    </div>
  </div>
);

export default Card;
