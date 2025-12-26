/**
 * StatCard - Advanced statistics card with animations and trends
 */
import React from "react";
import { motion } from "framer-motion";
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
} from "@heroicons/react/24/outline";

const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  variant = "default",
  size = "md",
  className = "",
  onClick,
  loading = false,
}) => {
  const variants = {
    default: "bg-gray-800/50 border-gray-700/50",
    primary:
      "bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-500/30",
    success:
      "bg-gradient-to-br from-emerald-600/20 to-emerald-800/20 border-emerald-500/30",
    warning:
      "bg-gradient-to-br from-amber-600/20 to-amber-800/20 border-amber-500/30",
    danger: "bg-gradient-to-br from-red-600/20 to-red-800/20 border-red-500/30",
    purple:
      "bg-gradient-to-br from-purple-600/20 to-purple-800/20 border-purple-500/30",
  };

  const iconVariants = {
    default: "bg-gray-700 text-gray-300",
    primary: "bg-blue-500/20 text-blue-400",
    success: "bg-emerald-500/20 text-emerald-400",
    warning: "bg-amber-500/20 text-amber-400",
    danger: "bg-red-500/20 text-red-400",
    purple: "bg-purple-500/20 text-purple-400",
  };

  const sizes = {
    sm: {
      padding: "p-4",
      iconSize: "w-10 h-10",
      iconInner: "h-5 w-5",
      titleSize: "text-xs",
      valueSize: "text-xl",
      subtitleSize: "text-xs",
    },
    md: {
      padding: "p-5",
      iconSize: "w-12 h-12",
      iconInner: "h-6 w-6",
      titleSize: "text-sm",
      valueSize: "text-2xl",
      subtitleSize: "text-sm",
    },
    lg: {
      padding: "p-6",
      iconSize: "w-14 h-14",
      iconInner: "h-7 w-7",
      titleSize: "text-base",
      valueSize: "text-3xl",
      subtitleSize: "text-base",
    },
  };

  const getTrendColor = () => {
    if (trend === "up") return "text-emerald-400";
    if (trend === "down") return "text-red-400";
    return "text-gray-400";
  };

  const getTrendIcon = () => {
    if (trend === "up") return ArrowTrendingUpIcon;
    if (trend === "down") return ArrowTrendingDownIcon;
    return MinusIcon;
  };

  const TrendIcon = getTrendIcon();
  const sizeConfig = sizes[size];

  if (loading) {
    return (
      <div
        className={`rounded-xl border ${variants[variant]} ${sizeConfig.padding} ${className}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-3">
            <div className="h-4 w-20 bg-gray-700 rounded animate-pulse" />
            <div className="h-8 w-32 bg-gray-700 rounded animate-pulse" />
            <div className="h-3 w-24 bg-gray-700 rounded animate-pulse" />
          </div>
          <div
            className={`${sizeConfig.iconSize} bg-gray-700 rounded-xl animate-pulse`}
          />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: onClick ? 1.02 : 1, y: onClick ? -2 : 0 }}
      whileTap={{ scale: onClick ? 0.98 : 1 }}
      onClick={onClick}
      className={`
        rounded-xl border backdrop-blur-sm
        ${variants[variant]}
        ${sizeConfig.padding}
        ${onClick ? "cursor-pointer" : ""}
        transition-all duration-200
        ${className}
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p
            className={`${sizeConfig.titleSize} font-medium text-gray-400 mb-1`}
          >
            {title}
          </p>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-baseline gap-2"
          >
            <span
              className={`${sizeConfig.valueSize} font-bold text-white truncate`}
            >
              {value}
            </span>

            {(trend || trendValue) && (
              <div className={`flex items-center gap-1 ${getTrendColor()}`}>
                <TrendIcon className="h-4 w-4" />
                <span className="text-sm font-medium">{trendValue}</span>
              </div>
            )}
          </motion.div>

          {subtitle && (
            <p
              className={`${sizeConfig.subtitleSize} text-gray-500 mt-1 truncate`}
            >
              {subtitle}
            </p>
          )}
        </div>

        {Icon && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`
              ${sizeConfig.iconSize} rounded-xl
              ${iconVariants[variant]}
              flex items-center justify-center
              flex-shrink-0 ml-4
            `}
          >
            <Icon className={sizeConfig.iconInner} />
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

// Stats Grid - For displaying multiple stat cards
export const StatsGrid = ({ children, columns = 4, className = "" }) => {
  return (
    <div
      className={`grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-${columns} ${className}`}
    >
      {children}
    </div>
  );
};

// Compact Stat - Inline stat display
export const CompactStat = ({
  label,
  value,
  icon: Icon,
  trend,
  trendValue,
  className = "",
}) => {
  const getTrendColor = () => {
    if (trend === "up") return "text-emerald-400";
    if (trend === "down") return "text-red-400";
    return "text-gray-400";
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {Icon && (
        <div className="w-8 h-8 rounded-lg bg-gray-700/50 flex items-center justify-center">
          <Icon className="h-4 w-4 text-gray-400" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500">{label}</p>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">{value}</span>
          {trendValue && (
            <span className={`text-xs ${getTrendColor()}`}>{trendValue}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatCard;
