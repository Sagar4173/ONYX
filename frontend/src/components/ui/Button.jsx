/**
 * Button - Enhanced button component with variants, sizes, and animations
 */
import React from "react";
import { motion } from "framer-motion";
import { ArrowPathIcon } from "@heroicons/react/24/outline";

const Button = ({
  children,
  variant = "primary",
  size = "md",
  icon: Icon,
  iconPosition = "left",
  loading = false,
  disabled = false,
  fullWidth = false,
  rounded = "xl",
  className = "",
  onClick,
  type = "button",
  as: Component = "button",
  href,
  ...props
}) => {
  const variants = {
    primary: `
      bg-gradient-to-r from-blue-600 to-blue-700 
      hover:from-blue-500 hover:to-blue-600 
      text-white shadow-lg shadow-blue-500/25
      focus:ring-blue-500/50
    `,
    secondary: `
      bg-gray-800 hover:bg-gray-700 
      text-white border border-gray-700
      focus:ring-gray-500/50
    `,
    success: `
      bg-gradient-to-r from-emerald-600 to-emerald-700 
      hover:from-emerald-500 hover:to-emerald-600 
      text-white shadow-lg shadow-emerald-500/25
      focus:ring-emerald-500/50
    `,
    danger: `
      bg-gradient-to-r from-red-600 to-red-700 
      hover:from-red-500 hover:to-red-600 
      text-white shadow-lg shadow-red-500/25
      focus:ring-red-500/50
    `,
    warning: `
      bg-gradient-to-r from-amber-600 to-amber-700 
      hover:from-amber-500 hover:to-amber-600 
      text-white shadow-lg shadow-amber-500/25
      focus:ring-amber-500/50
    `,
    purple: `
      bg-gradient-to-r from-purple-600 to-violet-700 
      hover:from-purple-500 hover:to-violet-600 
      text-white shadow-lg shadow-purple-500/25
      focus:ring-purple-500/50
    `,
    ghost: `
      bg-transparent hover:bg-gray-800/50 
      text-gray-300 hover:text-white
      focus:ring-gray-500/50
    `,
    outline: `
      bg-transparent border-2 border-gray-600 
      hover:border-gray-500 hover:bg-gray-800/30
      text-gray-300 hover:text-white
      focus:ring-gray-500/50
    `,
    glass: `
      glass-card border-white/10 hover:border-white/20
      text-white
      focus:ring-white/20
    `,
    gradient: `
      bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-600
      hover:from-cyan-400 hover:via-blue-400 hover:to-purple-500
      text-white shadow-lg shadow-blue-500/30
      focus:ring-blue-500/50
    `,
  };

  const sizes = {
    xs: "h-7 px-2.5 text-xs gap-1.5",
    sm: "h-8 px-3 text-sm gap-2",
    md: "h-10 px-4 text-sm gap-2",
    lg: "h-12 px-6 text-base gap-2.5",
    xl: "h-14 px-8 text-lg gap-3",
  };

  const iconSizes = {
    xs: "h-3.5 w-3.5",
    sm: "h-4 w-4",
    md: "h-4 w-4",
    lg: "h-5 w-5",
    xl: "h-6 w-6",
  };

  const roundedStyles = {
    none: "rounded-none",
    sm: "rounded-sm",
    md: "rounded-md",
    lg: "rounded-lg",
    xl: "rounded-xl",
    "2xl": "rounded-2xl",
    full: "rounded-full",
  };

  const buttonProps = {
    type: Component === "button" ? type : undefined,
    href: Component === "a" ? href : undefined,
    disabled: disabled || loading,
    onClick,
    className: `
      inline-flex items-center justify-center
      font-medium transition-all duration-200
      focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
      disabled:opacity-50 disabled:cursor-not-allowed
      ${variants[variant]}
      ${sizes[size]}
      ${roundedStyles[rounded]}
      ${fullWidth ? "w-full" : ""}
      ${className}
    `,
    ...props,
  };

  const content = (
    <>
      {loading ? (
        <ArrowPathIcon className={`${iconSizes[size]} animate-spin`} />
      ) : (
        Icon && iconPosition === "left" && <Icon className={iconSizes[size]} />
      )}
      {children}
      {!loading && Icon && iconPosition === "right" && (
        <Icon className={iconSizes[size]} />
      )}
    </>
  );

  // Use motion component for animation
  const MotionComponent = motion[Component] || motion.button;

  return (
    <MotionComponent
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      {...buttonProps}
    >
      {content}
    </MotionComponent>
  );
};

/**
 * IconButton - Button with only an icon
 */
export const IconButton = ({
  icon: Icon,
  variant = "ghost",
  size = "md",
  rounded = "lg",
  tooltip,
  className = "",
  ...props
}) => {
  const sizes = {
    xs: "h-6 w-6",
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
    xl: "h-14 w-14",
  };

  const iconSizes = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
    xl: "h-7 w-7",
  };

  const variants = {
    ghost: "bg-transparent hover:bg-gray-800/50 text-gray-400 hover:text-white",
    subtle:
      "bg-gray-800/30 hover:bg-gray-700/50 text-gray-400 hover:text-white",
    solid: "bg-gray-700 hover:bg-gray-600 text-white",
    primary: "bg-blue-600 hover:bg-blue-500 text-white",
    danger: "bg-red-600/10 hover:bg-red-600/20 text-red-400 hover:text-red-300",
  };

  const roundedStyles = {
    md: "rounded-md",
    lg: "rounded-lg",
    xl: "rounded-xl",
    full: "rounded-full",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      title={tooltip}
      className={`
        ${sizes[size]} 
        ${variants[variant]}
        ${roundedStyles[rounded]}
        inline-flex items-center justify-center
        transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-blue-500/50
        ${className}
      `}
      {...props}
    >
      <Icon className={iconSizes[size]} />
    </motion.button>
  );
};

/**
 * ButtonGroup - Group of buttons
 */
export const ButtonGroup = ({ children, attached = false, className = "" }) => {
  if (attached) {
    return (
      <div className={`inline-flex ${className}`}>
        {React.Children.map(children, (child, index) => {
          if (!React.isValidElement(child)) return child;
          const isFirst = index === 0;
          const isLast = index === React.Children.count(children) - 1;
          return React.cloneElement(child, {
            rounded: "none",
            className: `
              ${child.props.className || ""}
              ${isFirst ? "rounded-l-xl" : ""}
              ${isLast ? "rounded-r-xl" : ""}
              ${!isLast ? "border-r-0" : ""}
            `,
          });
        })}
      </div>
    );
  }

  return <div className={`inline-flex gap-2 ${className}`}>{children}</div>;
};

export default Button;
