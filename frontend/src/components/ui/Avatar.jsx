/**
 * Avatar - User avatar with fallback and status indicator
 */
import React, { useState } from "react";

const Avatar = ({
  src,
  alt = "Avatar",
  name,
  size = "md",
  status,
  className = "",
  onClick,
}) => {
  const [imageError, setImageError] = useState(false);

  const sizes = {
    xs: "h-6 w-6 text-xs",
    sm: "h-8 w-8 text-sm",
    md: "h-10 w-10 text-base",
    lg: "h-12 w-12 text-lg",
    xl: "h-16 w-16 text-xl",
    "2xl": "h-20 w-20 text-2xl",
  };

  const statusSizes = {
    xs: "h-1.5 w-1.5 border",
    sm: "h-2 w-2 border",
    md: "h-2.5 w-2.5 border-2",
    lg: "h-3 w-3 border-2",
    xl: "h-3.5 w-3.5 border-2",
    "2xl": "h-4 w-4 border-2",
  };

  const statusColors = {
    online: "bg-emerald-500",
    offline: "bg-gray-500",
    away: "bg-amber-500",
    busy: "bg-red-500",
  };

  // Generate initials from name
  const getInitials = (name) => {
    if (!name) return "?";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  // Generate consistent color from name
  const getColorFromName = (name) => {
    if (!name) return "from-gray-600 to-gray-700";
    const colors = [
      "from-blue-600 to-blue-700",
      "from-emerald-600 to-emerald-700",
      "from-purple-600 to-purple-700",
      "from-rose-600 to-rose-700",
      "from-amber-600 to-amber-700",
      "from-cyan-600 to-cyan-700",
      "from-indigo-600 to-indigo-700",
      "from-pink-600 to-pink-700",
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  const showFallback = !src || imageError;

  return (
    <div
      className={`relative inline-flex flex-shrink-0 ${
        onClick ? "cursor-pointer" : ""
      } ${className}`}
      onClick={onClick}
    >
      {showFallback ? (
        <div
          className={`
            ${sizes[size]}
            rounded-full flex items-center justify-center
            bg-gradient-to-br ${getColorFromName(name)}
            text-white font-semibold
            ring-2 ring-gray-800
          `}
        >
          {getInitials(name)}
        </div>
      ) : (
        <img
          src={src}
          alt={alt}
          onError={() => setImageError(true)}
          className={`
            ${sizes[size]}
            rounded-full object-cover
            ring-2 ring-gray-800
          `}
        />
      )}

      {/* Status indicator */}
      {status && (
        <span
          className={`
            absolute bottom-0 right-0
            ${statusSizes[size]}
            ${statusColors[status]}
            rounded-full border-gray-900
          `}
        />
      )}
    </div>
  );
};

// Avatar Group
export const AvatarGroup = ({
  users = [],
  max = 4,
  size = "md",
  className = "",
}) => {
  const displayUsers = users.slice(0, max);
  const remainingCount = users.length - max;

  const overlapSizes = {
    xs: "-ml-1.5",
    sm: "-ml-2",
    md: "-ml-2.5",
    lg: "-ml-3",
    xl: "-ml-4",
    "2xl": "-ml-5",
  };

  return (
    <div className={`flex items-center ${className}`}>
      {displayUsers.map((user, index) => (
        <div
          key={user.id || index}
          className={`${index > 0 ? overlapSizes[size] : ""}`}
          style={{ zIndex: displayUsers.length - index }}
        >
          <Avatar
            src={user.avatar}
            name={user.name}
            size={size}
            status={user.status}
          />
        </div>
      ))}

      {remainingCount > 0 && (
        <div
          className={`
            ${overlapSizes[size]}
            ${
              {
                xs: "h-6 w-6 text-[10px]",
                sm: "h-8 w-8 text-xs",
                md: "h-10 w-10 text-sm",
                lg: "h-12 w-12 text-base",
                xl: "h-16 w-16 text-lg",
                "2xl": "h-20 w-20 text-xl",
              }[size]
            }
            rounded-full flex items-center justify-center
            bg-gray-700 text-gray-300
            ring-2 ring-gray-900
            font-medium
          `}
        >
          +{remainingCount}
        </div>
      )}
    </div>
  );
};

export default Avatar;
