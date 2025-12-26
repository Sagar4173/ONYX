/**
 * Skeleton - Loading placeholder with shimmer animation
 * Usage: <Skeleton variant="text" width="200px" />
 */
import React from "react";

const Skeleton = ({
  variant = "rectangular",
  width,
  height,
  className = "",
  animate = true,
  count = 1,
  circle = false,
}) => {
  const baseClasses = `
    bg-gradient-to-r from-gray-800 via-gray-700 to-gray-800 
    bg-[length:200%_100%] rounded-lg
    ${animate ? "animate-shimmer" : ""}
    ${circle ? "!rounded-full" : ""}
  `;

  const variants = {
    text: "h-4 rounded",
    title: "h-8 rounded-lg",
    avatar: "w-12 h-12 rounded-full",
    thumbnail: "w-20 h-20 rounded-xl",
    card: "h-32 rounded-2xl",
    button: "h-10 w-24 rounded-xl",
    rectangular: "rounded-xl",
    circular: "rounded-full aspect-square",
  };

  const getStyles = () => {
    const styles = {};
    if (width) styles.width = width;
    if (height) styles.height = height;
    return styles;
  };

  const skeletons = Array(count).fill(null);

  return (
    <>
      {skeletons.map((_, index) => (
        <div
          key={index}
          className={`${baseClasses} ${variants[variant]} ${className}`}
          style={getStyles()}
          aria-hidden="true"
        />
      ))}
    </>
  );
};

// Pre-configured skeleton components
export const SkeletonText = ({ lines = 3, className = "" }) => (
  <div className={`space-y-3 ${className}`}>
    {Array(lines)
      .fill(null)
      .map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? "70%" : "100%"}
        />
      ))}
  </div>
);

export const SkeletonCard = ({ className = "" }) => (
  <div
    className={`p-6 bg-gray-800/50 rounded-2xl border border-gray-700/50 space-y-4 ${className}`}
  >
    <div className="flex items-center space-x-4">
      <Skeleton variant="avatar" />
      <div className="flex-1 space-y-2">
        <Skeleton variant="text" width="60%" />
        <Skeleton variant="text" width="40%" />
      </div>
    </div>
    <Skeleton variant="card" />
    <div className="flex space-x-2">
      <Skeleton variant="button" />
      <Skeleton variant="button" />
    </div>
  </div>
);

export const SkeletonTable = ({ rows = 5, cols = 4, className = "" }) => (
  <div className={`space-y-3 ${className}`}>
    {/* Header */}
    <div className="flex space-x-4 pb-4 border-b border-gray-700/50">
      {Array(cols)
        .fill(null)
        .map((_, i) => (
          <Skeleton key={i} variant="text" className="flex-1" height="20px" />
        ))}
    </div>
    {/* Rows */}
    {Array(rows)
      .fill(null)
      .map((_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4 py-3">
          {Array(cols)
            .fill(null)
            .map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                variant="text"
                className="flex-1"
                height="16px"
              />
            ))}
        </div>
      ))}
  </div>
);

export const SkeletonStats = ({ count = 4, className = "" }) => (
  <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${className}`}>
    {Array(count)
      .fill(null)
      .map((_, i) => (
        <div
          key={i}
          className="p-6 bg-gray-800/50 rounded-2xl border border-gray-700/50 space-y-3"
        >
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="title" width="80%" />
          <Skeleton variant="text" width="40%" />
        </div>
      ))}
  </div>
);

export default Skeleton;
