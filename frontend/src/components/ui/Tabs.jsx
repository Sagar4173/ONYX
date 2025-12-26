/**
 * Tabs - Accessible tabbed interface with animations
 */
import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

const Tabs = ({
  tabs = [],
  defaultTab = 0,
  onChange,
  variant = "default",
  className = "",
  fullWidth = false,
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [indicatorStyle, setIndicatorStyle] = useState({});
  const tabRefs = useRef([]);

  const variants = {
    default: {
      container:
        "bg-gray-800/50 p-1 rounded-xl border border-gray-700/50 inline-flex",
      tab: "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
      active: "text-white",
      inactive: "text-gray-400 hover:text-gray-200",
      indicator: "bg-gray-700/80",
    },
    pills: {
      container: "inline-flex space-x-2",
      tab: "px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 border",
      active: "text-white bg-blue-600 border-blue-500",
      inactive:
        "text-gray-400 hover:text-white border-gray-700 hover:border-gray-600 bg-gray-800/50",
      indicator: "",
    },
    underline: {
      container: "inline-flex space-x-6 border-b border-gray-700",
      tab: "pb-3 text-sm font-medium transition-all duration-200 relative",
      active: "text-white",
      inactive: "text-gray-400 hover:text-gray-200",
      indicator: "bg-blue-500",
    },
    cards: {
      container: "grid gap-2",
      tab: "p-4 rounded-xl text-left transition-all duration-200 border",
      active: "text-white bg-blue-600/10 border-blue-500/50",
      inactive: "text-gray-400 hover:text-white border-gray-700 bg-gray-800/30",
      indicator: "",
    },
  };

  const currentVariant = variants[variant];

  // Update indicator position
  useEffect(() => {
    if (variant === "default" && tabRefs.current[activeTab]) {
      const tab = tabRefs.current[activeTab];
      setIndicatorStyle({
        width: tab.offsetWidth,
        left: tab.offsetLeft,
      });
    }
  }, [activeTab, variant]);

  const handleTabClick = (index) => {
    setActiveTab(index);
    if (onChange) {
      onChange(index, tabs[index]);
    }
  };

  return (
    <div className={className}>
      {/* Tab List */}
      <div
        role="tablist"
        className={`
          ${currentVariant.container}
          ${fullWidth ? "w-full" : ""}
          ${variant === "cards" ? `grid-cols-${tabs.length}` : ""}
        `}
        style={
          variant === "cards"
            ? { gridTemplateColumns: `repeat(${tabs.length}, 1fr)` }
            : {}
        }
      >
        {variant === "default" && (
          <motion.div
            className={`absolute ${currentVariant.indicator} rounded-lg`}
            layoutId="tab-indicator"
            initial={false}
            animate={{
              width: indicatorStyle.width,
              x: indicatorStyle.left,
            }}
            style={{ height: "100%", top: 0 }}
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
          />
        )}

        {tabs.map((tab, index) => {
          const Icon = tab.icon;
          const isActive = activeTab === index;

          return (
            <button
              key={index}
              ref={(el) => (tabRefs.current[index] = el)}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${index}`}
              onClick={() => handleTabClick(index)}
              disabled={tab.disabled}
              className={`
                ${currentVariant.tab}
                ${isActive ? currentVariant.active : currentVariant.inactive}
                ${fullWidth ? "flex-1" : ""}
                ${tab.disabled ? "opacity-50 cursor-not-allowed" : ""}
                relative z-10 flex items-center justify-center space-x-2
              `}
            >
              {Icon && <Icon className="h-4 w-4" />}
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`
                  ml-2 px-2 py-0.5 text-xs rounded-full
                  ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-gray-700 text-gray-300"
                  }
                `}
                >
                  {tab.badge}
                </span>
              )}

              {/* Underline indicator */}
              {variant === "underline" && isActive && (
                <motion.div
                  layoutId="underline"
                  className={`absolute bottom-0 left-0 right-0 h-0.5 ${currentVariant.indicator}`}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="mt-6">
        {tabs.map((tab, index) => (
          <div
            key={index}
            role="tabpanel"
            id={`tabpanel-${index}`}
            aria-labelledby={`tab-${index}`}
            hidden={activeTab !== index}
          >
            {activeTab === index && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                {tab.content}
              </motion.div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Tabs;
