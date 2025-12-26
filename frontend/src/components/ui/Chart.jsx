/**
 * Chart - Lightweight chart components without external dependencies
 * Supports: Line, Bar, Pie, Donut, Area charts
 */
import React, { useMemo } from "react";
import { motion } from "framer-motion";

/**
 * Base Chart Container
 */
const ChartContainer = ({ children, title, subtitle, className = "" }) => (
  <div
    className={`bg-gray-800/30 rounded-2xl border border-gray-700/30 p-6 ${className}`}
  >
    {(title || subtitle) && (
      <div className="mb-6">
        {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
        {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
      </div>
    )}
    {children}
  </div>
);

/**
 * Bar Chart Component
 */
export const BarChart = ({
  data = [],
  height = 200,
  barColor = "from-blue-500 to-purple-600",
  showValues = true,
  animated = true,
  className = "",
}) => {
  const maxValue = useMemo(
    () => Math.max(...data.map((d) => d.value), 1),
    [data]
  );

  return (
    <div className={`relative ${className}`} style={{ height }}>
      <div className="absolute inset-0 flex items-end justify-around gap-2 pb-8">
        {data.map((item, index) => {
          const heightPercent = (item.value / maxValue) * 100;
          return (
            <div key={index} className="flex-1 flex flex-col items-center">
              <motion.div
                initial={animated ? { height: 0 } : false}
                animate={{ height: `${heightPercent}%` }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`w-full max-w-[60px] bg-gradient-to-t ${
                  item.color || barColor
                } rounded-t-lg relative group`}
              >
                {showValues && (
                  <span className="absolute -top-7 left-1/2 -translate-x-1/2 text-xs font-medium text-white opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.value}
                  </span>
                )}
              </motion.div>
              <span className="absolute bottom-0 text-xs text-gray-400 text-center truncate max-w-full">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Horizontal Bar Chart
 */
export const HorizontalBarChart = ({
  data = [],
  height = "auto",
  showValues = true,
  animated = true,
  className = "",
}) => {
  const maxValue = useMemo(
    () => Math.max(...data.map((d) => d.value), 1),
    [data]
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {data.map((item, index) => {
        const widthPercent = (item.value / maxValue) * 100;
        return (
          <div key={index} className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">{item.label}</span>
              {showValues && (
                <span className="text-gray-400 font-medium">{item.value}</span>
              )}
            </div>
            <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden">
              <motion.div
                initial={animated ? { width: 0 } : false}
                animate={{ width: `${widthPercent}%` }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`h-full bg-gradient-to-r ${
                  item.color || "from-blue-500 to-purple-600"
                } rounded-full`}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * Donut/Pie Chart
 */
export const DonutChart = ({
  data = [],
  size = 200,
  strokeWidth = 30,
  showLegend = true,
  showCenter = true,
  centerValue,
  centerLabel,
  animated = true,
  className = "",
}) => {
  const total = useMemo(
    () => data.reduce((sum, item) => sum + item.value, 0),
    [data]
  );
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const segments = useMemo(() => {
    let currentOffset = 0;
    return data.map((item) => {
      const percentage = item.value / total;
      const dashLength = percentage * circumference;
      const segment = {
        ...item,
        percentage,
        dashArray: `${dashLength} ${circumference - dashLength}`,
        dashOffset: -currentOffset,
      };
      currentOffset += dashLength;
      return segment;
    });
  }, [data, total, circumference]);

  return (
    <div className={`flex flex-col items-center gap-6 ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(75, 85, 99, 0.3)"
            strokeWidth={strokeWidth}
          />

          {/* Data segments */}
          {segments.map((segment, index) => (
            <motion.circle
              key={index}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={segment.color || `url(#gradient-${index})`}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={segment.dashArray}
              initial={animated ? { strokeDashoffset: circumference } : false}
              animate={{ strokeDashoffset: segment.dashOffset }}
              transition={{ duration: 1, delay: index * 0.1 }}
            />
          ))}

          {/* Gradient definitions */}
          <defs>
            {segments.map((segment, index) => (
              <linearGradient key={index} id={`gradient-${index}`}>
                <stop
                  offset="0%"
                  stopColor={segment.gradientStart || "#3b82f6"}
                />
                <stop
                  offset="100%"
                  stopColor={segment.gradientEnd || "#8b5cf6"}
                />
              </linearGradient>
            ))}
          </defs>
        </svg>

        {/* Center content */}
        {showCenter && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-white">
              {centerValue ?? total}
            </span>
            {centerLabel && (
              <span className="text-sm text-gray-400">{centerLabel}</span>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap justify-center gap-4">
          {data.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color || "#3b82f6" }}
              />
              <span className="text-sm text-gray-400">{item.label}</span>
              <span className="text-sm font-medium text-white">
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Line Chart / Sparkline
 */
export const LineChart = ({
  data = [],
  height = 100,
  width = "100%",
  lineColor = "#3b82f6",
  showArea = false,
  showDots = false,
  showGrid = false,
  animated = true,
  className = "",
}) => {
  const maxValue = useMemo(
    () => Math.max(...data.map((d) => d.value), 1),
    [data]
  );
  const minValue = useMemo(
    () => Math.min(...data.map((d) => d.value), 0),
    [data]
  );
  const range = maxValue - minValue;

  const points = useMemo(() => {
    const padding = 10;
    const usableHeight = height - padding * 2;
    const stepX = 100 / (data.length - 1);

    return data.map((item, index) => ({
      x: `${index * stepX}%`,
      y:
        padding +
        usableHeight -
        ((item.value - minValue) / range) * usableHeight,
      ...item,
    }));
  }, [data, height, range, minValue]);

  const pathD = points.length
    ? `M ${points.map((p) => `${p.x} ${p.y}`).join(" L ")}`
    : "";

  const areaPathD = points.length
    ? `${pathD} L 100% ${height} L 0% ${height} Z`
    : "";

  return (
    <div className={className} style={{ height, width }}>
      <svg width="100%" height={height} className="overflow-visible">
        {/* Grid lines */}
        {showGrid && (
          <g className="text-gray-700">
            {[0, 25, 50, 75, 100].map((y) => (
              <line
                key={y}
                x1="0%"
                y1={`${y}%`}
                x2="100%"
                y2={`${y}%`}
                stroke="currentColor"
                strokeDasharray="4 4"
                opacity={0.3}
              />
            ))}
          </g>
        )}

        {/* Area fill */}
        {showArea && (
          <motion.path
            d={areaPathD}
            fill={`url(#areaGradient)`}
            initial={animated ? { opacity: 0 } : false}
            animate={{ opacity: 0.3 }}
            transition={{ duration: 1 }}
          />
        )}

        {/* Line */}
        <motion.path
          d={pathD}
          fill="none"
          stroke={lineColor}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={animated ? { pathLength: 0, opacity: 0 } : false}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.5 }}
        />

        {/* Dots */}
        {showDots &&
          points.map((point, index) => (
            <motion.circle
              key={index}
              cx={point.x}
              cy={point.y}
              r={4}
              fill={lineColor}
              initial={animated ? { scale: 0 } : false}
              animate={{ scale: 1 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="hover:r-6 cursor-pointer"
            />
          ))}

        {/* Gradient definition */}
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity={0.4} />
            <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};

/**
 * Mini Sparkline for inline use
 */
export const Sparkline = ({
  data = [],
  width = 100,
  height = 30,
  color = "#3b82f6",
  showArea = true,
}) => {
  const maxValue = Math.max(...data, 1);
  const minValue = Math.min(...data, 0);
  const range = maxValue - minValue || 1;

  const points = data.map((value, index) => ({
    x: (index / (data.length - 1)) * width,
    y: height - ((value - minValue) / range) * height,
  }));

  const pathD = points.length
    ? `M ${points.map((p) => `${p.x} ${p.y}`).join(" L ")}`
    : "";

  const areaPathD = points.length
    ? `${pathD} L ${width} ${height} L 0 ${height} Z`
    : "";

  return (
    <svg width={width} height={height} className="overflow-visible">
      {showArea && <path d={areaPathD} fill={color} opacity={0.2} />}
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

/**
 * Gauge Chart
 */
export const GaugeChart = ({
  value = 0,
  max = 100,
  size = 150,
  strokeWidth = 12,
  color = "from-blue-500 to-purple-600",
  label,
  animated = true,
  className = "",
}) => {
  const percentage = Math.min(Math.max(value / max, 0), 1);
  const radius = (size - strokeWidth) / 2;
  const circumference = Math.PI * radius; // Half circle
  const dashOffset = circumference * (1 - percentage);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width: size, height: size / 2 + 20 }}>
        <svg width={size} height={size / 2 + 20} className="overflow-visible">
          {/* Background arc */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${
              size - strokeWidth / 2
            } ${size / 2}`}
            fill="none"
            stroke="rgba(75, 85, 99, 0.3)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Value arc */}
          <motion.path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${
              size - strokeWidth / 2
            } ${size / 2}`}
            fill="none"
            stroke={`url(#gaugeGradient-${size})`}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={animated ? { strokeDashoffset: circumference } : false}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1 }}
          />

          <defs>
            <linearGradient
              id={`gaugeGradient-${size}`}
              x1="0%"
              y1="0%"
              x2="100%"
              y2="0%"
            >
              <stop
                offset="0%"
                className="text-blue-500"
                stopColor="currentColor"
              />
              <stop
                offset="100%"
                className="text-purple-600"
                stopColor="currentColor"
              />
            </linearGradient>
          </defs>
        </svg>

        {/* Center value */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
          <span className="text-2xl font-bold text-white">{value}</span>
          {label && (
            <span className="block text-sm text-gray-400">{label}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export { ChartContainer };
export default {
  BarChart,
  HorizontalBarChart,
  DonutChart,
  LineChart,
  Sparkline,
  GaugeChart,
  ChartContainer,
};
