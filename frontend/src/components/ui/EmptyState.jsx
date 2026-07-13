/**
 * EmptyState - Beautiful empty state illustrations
 */

import { motion } from "framer-motion";
import {
  FolderOpenIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ShieldExclamationIcon,
  ChartBarIcon,
  UserGroupIcon,
  CogIcon,
  BellIcon,
  CloudIcon,
} from "@heroicons/react/24/outline";

const iconMap = {
  folder: FolderOpenIcon,
  document: DocumentTextIcon,
  search: MagnifyingGlassIcon,
  shield: ShieldExclamationIcon,
  chart: ChartBarIcon,
  users: UserGroupIcon,
  settings: CogIcon,
  notification: BellIcon,
  cloud: CloudIcon,
};

const EmptyState = ({
  icon = "folder",
  title = "No data found",
  description,
  action,
  variant = "default",
  size = "md",
  className = "",
}) => {
  const Icon = typeof icon === "string" ? iconMap[icon] : icon;

  const sizes = {
    sm: {
      container: "py-8",
      iconWrapper: "w-14 h-14",
      iconSize: "h-7 w-7",
      title: "text-base",
      description: "text-sm",
    },
    md: {
      container: "py-12",
      iconWrapper: "w-20 h-20",
      iconSize: "h-10 w-10",
      title: "text-lg",
      description: "text-base",
    },
    lg: {
      container: "py-16",
      iconWrapper: "w-28 h-28",
      iconSize: "h-14 w-14",
      title: "text-xl",
      description: "text-base",
    },
  };

  const sizeConfig = sizes[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col items-center justify-center text-center ${sizeConfig.container} ${className}`}
    >
      {/* Animated icon container */}
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="relative mb-6"
      >
        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-xl" />

        {/* Icon wrapper */}
        <div
          className={`
          relative ${sizeConfig.iconWrapper} rounded-full 
          bg-gradient-to-br from-gray-800 to-gray-900
          border border-gray-700/50
          flex items-center justify-center
          shadow-2xl
        `}
        >
          {/* Decorative circles */}
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.1, 0.2, 0.1],
            }}
            transition={{ duration: 3, repeat: Infinity }}
            className="absolute inset-0 rounded-full border border-blue-500/30"
          />
          <motion.div
            animate={{
              scale: [1, 1.4, 1],
              opacity: [0.1, 0.15, 0.1],
            }}
            transition={{ duration: 4, repeat: Infinity, delay: 0.5 }}
            className="absolute inset-0 rounded-full border border-purple-500/20"
          />

          {Icon && <Icon className={`${sizeConfig.iconSize} text-gray-400`} />}
        </div>
      </motion.div>

      {/* Text content */}
      <motion.h3
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className={`${sizeConfig.title} font-semibold text-white mb-2`}
      >
        {title}
      </motion.h3>

      {description && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className={`${sizeConfig.description} text-gray-400 max-w-md mb-6`}
        >
          {description}
        </motion.p>
      )}

      {/* Action */}
      {action && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {action}
        </motion.div>
      )}
    </motion.div>
  );
};

/**
 * No Search Results State
 */
export const NoSearchResults = ({ query, onClear, className = "" }) => (
  <EmptyState
    icon="search"
    title="No results found"
    description={
      query
        ? `We couldn't find anything matching "${query}". Try adjusting your search.`
        : "Start typing to search for items."
    }
    action={
      onClear &&
      query && (
        <button
          onClick={onClear}
          className="px-4 py-2 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
        >
          Clear search
        </button>
      )
    }
    className={className}
  />
);

/**
 * No Data State
 */
export const NoDataState = ({ type = "items", onCreate, className = "" }) => (
  <EmptyState
    icon="folder"
    title={`No ${type} yet`}
    description={`Get started by creating your first ${type.slice(0, -1)}.`}
    action={
      onCreate && (
        <button
          onClick={onCreate}
          className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium text-sm hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg shadow-blue-500/25"
        >
          Create {type.slice(0, -1)}
        </button>
      )
    }
    className={className}
  />
);

/**
 * Error State
 */
export const ErrorState = ({
  title = "Something went wrong",
  description = "An error occurred while loading this content. Please try again.",
  onRetry,
  className = "",
}) => (
  <EmptyState
    icon="shield"
    title={title}
    description={description}
    action={
      onRetry && (
        <button
          onClick={onRetry}
          className="px-5 py-2.5 bg-red-600/20 text-red-400 border border-red-500/30 rounded-xl font-medium text-sm hover:bg-red-600/30 transition-all"
        >
          Try again
        </button>
      )
    }
    className={className}
  />
);

/**
 * Coming Soon State
 */
export const ComingSoonState = ({
  feature = "This feature",
  className = "",
}) => (
  <EmptyState
    icon="cloud"
    title="Coming Soon"
    description={`${feature} is currently under development. Check back soon for updates!`}
    className={className}
  />
);

export default EmptyState;
