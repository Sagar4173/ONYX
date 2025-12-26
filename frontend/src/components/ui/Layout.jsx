/**
 * Layout Components - Containers and layout utilities
 */
import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { HomeIcon, ChevronRightIcon } from "@heroicons/react/24/outline";

/**
 * Container - Responsive page container
 */
export const Container = ({
  children,
  size = "default",
  padding = true,
  className = "",
}) => {
  const sizes = {
    sm: "max-w-3xl",
    default: "max-w-7xl",
    lg: "max-w-[1400px]",
    xl: "max-w-[1600px]",
    full: "max-w-full",
  };

  return (
    <div
      className={`
        mx-auto w-full
        ${sizes[size]}
        ${padding ? "px-4 sm:px-6 lg:px-8" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

/**
 * Grid - Responsive grid layout
 */
export const Grid = ({ children, cols = 4, gap = 6, className = "" }) => {
  const colsMap = {
    1: "grid-cols-1",
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5",
    6: "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6",
  };

  const gapMap = {
    2: "gap-2",
    3: "gap-3",
    4: "gap-4",
    5: "gap-5",
    6: "gap-6",
    8: "gap-8",
  };

  return (
    <div className={`grid ${colsMap[cols]} ${gapMap[gap]} ${className}`}>
      {children}
    </div>
  );
};

/**
 * Flex - Flexible layout container
 */
export const Flex = ({
  children,
  direction = "row",
  align = "center",
  justify = "start",
  wrap = false,
  gap = 4,
  className = "",
}) => {
  const directions = {
    row: "flex-row",
    col: "flex-col",
    "row-reverse": "flex-row-reverse",
    "col-reverse": "flex-col-reverse",
  };

  const alignments = {
    start: "items-start",
    center: "items-center",
    end: "items-end",
    stretch: "items-stretch",
    baseline: "items-baseline",
  };

  const justifications = {
    start: "justify-start",
    center: "justify-center",
    end: "justify-end",
    between: "justify-between",
    around: "justify-around",
    evenly: "justify-evenly",
  };

  const gaps = {
    0: "gap-0",
    1: "gap-1",
    2: "gap-2",
    3: "gap-3",
    4: "gap-4",
    5: "gap-5",
    6: "gap-6",
    8: "gap-8",
  };

  return (
    <div
      className={`
        flex
        ${directions[direction]}
        ${alignments[align]}
        ${justifications[justify]}
        ${wrap ? "flex-wrap" : "flex-nowrap"}
        ${gaps[gap]}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

/**
 * Breadcrumb - Navigation breadcrumb
 */
export const Breadcrumb = ({ items = [], separator, className = "" }) => {
  if (items.length === 0) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={`flex items-center space-x-2 text-sm ${className}`}
    >
      <Link
        to="/dashboard"
        className="text-gray-400 hover:text-white transition-colors"
      >
        <HomeIcon className="h-4 w-4" />
      </Link>

      {items.map((item, index) => (
        <React.Fragment key={index}>
          {separator || <ChevronRightIcon className="h-4 w-4 text-gray-600" />}

          {item.href && index < items.length - 1 ? (
            <Link
              to={item.href}
              className="text-gray-400 hover:text-white transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span
              className={
                index === items.length - 1
                  ? "text-white font-medium"
                  : "text-gray-400"
              }
            >
              {item.label}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

/**
 * PageHeader - Page header with title, description, and actions
 */
export const PageHeader = ({
  title,
  description,
  icon: Icon,
  iconGradient = "from-blue-500 to-purple-600",
  breadcrumb = [],
  actions,
  className = "",
}) => {
  return (
    <div className={`mb-6 lg:mb-8 ${className}`}>
      {breadcrumb.length > 0 && (
        <Breadcrumb items={breadcrumb} className="mb-4" />
      )}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          {Icon && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={`p-3 rounded-2xl bg-gradient-to-r ${iconGradient} shadow-lg`}
            >
              <Icon className="h-6 w-6 text-white" />
            </motion.div>
          )}
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-2xl sm:text-3xl font-bold text-white"
            >
              {title}
            </motion.h1>
            {description && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="text-gray-400 mt-1 text-sm sm:text-base"
              >
                {description}
              </motion.p>
            )}
          </div>
        </div>

        {actions && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-3"
          >
            {actions}
          </motion.div>
        )}
      </div>
    </div>
  );
};

/**
 * Section - Content section with optional header
 */
export const Section = ({
  children,
  title,
  description,
  action,
  className = "",
}) => {
  return (
    <section className={className}>
      {(title || action) && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            {title && (
              <h2 className="text-lg lg:text-xl font-bold text-white">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-sm text-gray-400 mt-1">{description}</p>
            )}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
};

/**
 * Divider - Visual separator
 */
export const Divider = ({
  orientation = "horizontal",
  color = "gray-700/50",
  className = "",
}) => {
  if (orientation === "vertical") {
    return <div className={`w-px h-full bg-${color} ${className}`} />;
  }
  return <div className={`w-full h-px bg-${color} ${className}`} />;
};

/**
 * Stack - Vertical stack of elements
 */
export const Stack = ({
  children,
  gap = 4,
  divider = false,
  className = "",
}) => {
  const gaps = {
    0: "space-y-0",
    1: "space-y-1",
    2: "space-y-2",
    3: "space-y-3",
    4: "space-y-4",
    5: "space-y-5",
    6: "space-y-6",
    8: "space-y-8",
  };

  if (divider) {
    return (
      <div className={`${className}`}>
        {React.Children.map(children, (child, index) => (
          <React.Fragment key={index}>
            {index > 0 && <Divider className="my-4" />}
            {child}
          </React.Fragment>
        ))}
      </div>
    );
  }

  return <div className={`${gaps[gap]} ${className}`}>{children}</div>;
};

/**
 * Aspect Ratio Container
 */
export const AspectRatio = ({ children, ratio = "16/9", className = "" }) => {
  const ratios = {
    "1/1": "aspect-square",
    "4/3": "aspect-[4/3]",
    "16/9": "aspect-video",
    "21/9": "aspect-[21/9]",
  };

  return (
    <div
      className={`relative ${
        ratios[ratio] || `aspect-[${ratio}]`
      } ${className}`}
    >
      <div className="absolute inset-0">{children}</div>
    </div>
  );
};

/**
 * Centered Content
 */
export const Center = ({ children, className = "" }) => (
  <div className={`flex items-center justify-center ${className}`}>
    {children}
  </div>
);

export default {
  Container,
  Grid,
  Flex,
  Breadcrumb,
  PageHeader,
  Section,
  Divider,
  Stack,
  AspectRatio,
  Center,
};
