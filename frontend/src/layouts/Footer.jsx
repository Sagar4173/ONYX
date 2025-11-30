// f:\Project\SecureDevOpsAI-Platform\frontend\src\layouts\Footer.jsx
// Enterprise Premium Footer with Real API Integration
// Features: Real-time health status, version info, professional design

import { useState, useEffect, memo, useCallback } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import {
  HeartIcon,
  ServerIcon,
  BoltIcon,
  ShieldCheckIcon,
  ArrowTopRightOnSquareIcon,
  ChevronUpIcon,
} from "@heroicons/react/24/outline";
import { HeartIcon as HeartSolidIcon } from "@heroicons/react/24/solid";

// Import real dashboard service
import dashboardService from "../services/dashboardService";

// ============================================================================
// VERSION & BUILD INFO
// ============================================================================
const VERSION = import.meta.env.VITE_APP_VERSION || "2.5.0";
const BUILD_DATE =
  import.meta.env.VITE_BUILD_DATE || new Date().toISOString().split("T")[0];
const ENVIRONMENT = import.meta.env.MODE || "development";

// ============================================================================
// HEALTH STATUS INDICATOR
// ============================================================================
const HealthStatus = memo(function HealthStatus() {
  const [health, setHealth] = useState({
    status: "checking",
    latency: null,
    lastChecked: null,
    services: {
      api: { status: "unknown" },
      database: { status: "unknown" },
      ai: { status: "unknown" },
    },
  });
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let retryCount = 0;

    const checkHealth = async () => {
      try {
        const start = performance.now();
        const healthData = await dashboardService.getSystemHealth();
        const latency = Math.round(performance.now() - start);

        if (isMounted) {
          setHealth({
            status: healthData?.status || "healthy",
            latency,
            lastChecked: new Date(),
            services: {
              api: {
                status:
                  healthData?.status === "healthy" ? "operational" : "degraded",
              },
              database: {
                status: healthData?.database?.connected
                  ? "operational"
                  : "error",
              },
              ai: {
                status: healthData?.ai?.available ? "operational" : "unknown",
              },
            },
          });
          retryCount = 0;
        }
      } catch (error) {
        console.error("Health check failed:", error);
        if (isMounted) {
          retryCount++;
          setHealth((prev) => ({
            ...prev,
            status: retryCount > 2 ? "error" : "degraded",
            latency: null,
            lastChecked: new Date(),
          }));
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const statusConfig = {
    healthy: {
      color: "bg-green-400",
      glow: "shadow-green-400/50",
      text: "All Systems Operational",
      textColor: "text-green-400",
    },
    operational: {
      color: "bg-green-400",
      glow: "shadow-green-400/50",
      text: "Operational",
      textColor: "text-green-400",
    },
    degraded: {
      color: "bg-amber-400",
      glow: "shadow-amber-400/50",
      text: "Degraded Performance",
      textColor: "text-amber-400",
    },
    error: {
      color: "bg-red-400",
      glow: "shadow-red-400/50",
      text: "Service Disruption",
      textColor: "text-red-400",
    },
    checking: {
      color: "bg-slate-400",
      glow: "shadow-slate-400/50",
      text: "Checking...",
      textColor: "text-slate-400",
    },
    unknown: {
      color: "bg-slate-500",
      glow: "shadow-slate-500/50",
      text: "Unknown",
      textColor: "text-slate-500",
    },
  };

  const config = statusConfig[health.status] || statusConfig.unknown;

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={clsx(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg",
          "bg-white/5 hover:bg-white/10 transition-all duration-200",
          "border border-white/5 hover:border-white/10",
          "group"
        )}
      >
        {/* Status indicator */}
        <div className="relative">
          <div
            className={clsx(
              "w-2 h-2 rounded-full",
              config.color,
              health.status !== "checking" && "animate-pulse"
            )}
          />
          <div
            className={clsx(
              "absolute inset-0 w-2 h-2 rounded-full",
              config.color,
              config.glow,
              "blur-sm"
            )}
          />
        </div>

        {/* Status text */}
        <span className={clsx("text-xs font-medium", config.textColor)}>
          {config.text}
        </span>

        {/* Latency */}
        {health.latency && (
          <span
            className={clsx(
              "text-[10px] font-mono px-1.5 py-0.5 rounded",
              health.latency < 100
                ? "bg-green-500/10 text-green-400"
                : health.latency < 300
                ? "bg-amber-500/10 text-amber-400"
                : "bg-red-500/10 text-red-400"
            )}
          >
            {health.latency}ms
          </span>
        )}

        <ChevronUpIcon
          className={clsx(
            "w-3 h-3 text-slate-500 transition-transform duration-200",
            showDetails && "rotate-180"
          )}
        />
      </button>

      {/* Details popup */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={clsx(
              "absolute bottom-full mb-2 left-0",
              "w-64 p-4 rounded-xl",
              "bg-slate-900/98 backdrop-blur-xl",
              "border border-white/10",
              "shadow-2xl shadow-black/40"
            )}
          >
            <h4 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
              <ServerIcon className="w-4 h-4 text-blue-400" />
              System Status
            </h4>

            <div className="space-y-2">
              {Object.entries(health.services).map(([service, data]) => {
                const sConfig =
                  statusConfig[data.status] || statusConfig.unknown;
                return (
                  <div
                    key={service}
                    className="flex items-center justify-between"
                  >
                    <span className="text-xs text-slate-400 capitalize">
                      {service}
                    </span>
                    <div className="flex items-center gap-2">
                      <div
                        className={clsx(
                          "w-1.5 h-1.5 rounded-full",
                          sConfig.color
                        )}
                      />
                      <span className={clsx("text-[10px]", sConfig.textColor)}>
                        {sConfig.text}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {health.lastChecked && (
              <p className="text-[10px] text-slate-500 mt-3 pt-2 border-t border-white/5">
                Last checked: {health.lastChecked.toLocaleTimeString()}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

// ============================================================================
// QUICK LINKS
// ============================================================================
const QuickLinks = memo(function QuickLinks() {
  const links = [
    { label: "Documentation", path: "/docs", external: false },
    { label: "API Reference", path: "/docs/api", external: false },
    { label: "Support", path: "/support", external: false },
    {
      label: "GitHub",
      path: "https://github.com/securedevops",
      external: true,
    },
  ];

  return (
    <div className="flex items-center gap-4">
      {links.map((link) =>
        link.external ? (
          <a
            key={link.label}
            href={link.path}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors
                     flex items-center gap-1 group"
          >
            {link.label}
            <ArrowTopRightOnSquareIcon className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        ) : (
          <Link
            key={link.label}
            to={link.path}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            {link.label}
          </Link>
        )
      )}
    </div>
  );
});

// ============================================================================
// SECURITY BADGES
// ============================================================================
const SecurityBadges = memo(function SecurityBadges() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-green-500/10 border border-green-500/20">
        <ShieldCheckIcon className="w-3.5 h-3.5 text-green-400" />
        <span className="text-[10px] font-medium text-green-400">SOC 2</span>
      </div>
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-blue-500/10 border border-blue-500/20">
        <BoltIcon className="w-3.5 h-3.5 text-blue-400" />
        <span className="text-[10px] font-medium text-blue-400">GDPR</span>
      </div>
    </div>
  );
});

// ============================================================================
// VERSION INFO
// ============================================================================
const VersionInfo = memo(function VersionInfo() {
  const [showBuildInfo, setShowBuildInfo] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setShowBuildInfo(!showBuildInfo)}
        onMouseEnter={() => setShowBuildInfo(true)}
        onMouseLeave={() => setShowBuildInfo(false)}
        className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
      >
        <span className="font-mono">v{VERSION}</span>
        <span
          className={clsx(
            "px-1.5 py-0.5 rounded text-[9px] font-medium uppercase",
            ENVIRONMENT === "production"
              ? "bg-green-500/10 text-green-400"
              : "bg-amber-500/10 text-amber-400"
          )}
        >
          {ENVIRONMENT}
        </span>
      </button>

      <AnimatePresence>
        {showBuildInfo && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className={clsx(
              "absolute bottom-full mb-2 left-0",
              "p-3 rounded-lg",
              "bg-slate-900/98 backdrop-blur-xl",
              "border border-white/10",
              "shadow-xl"
            )}
          >
            <div className="space-y-1.5 text-[10px] whitespace-nowrap">
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Version:</span>
                <span className="text-slate-300 font-mono">{VERSION}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Build Date:</span>
                <span className="text-slate-300 font-mono">{BUILD_DATE}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Environment:</span>
                <span className="text-slate-300 font-mono">{ENVIRONMENT}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

// ============================================================================
// MAIN FOOTER COMPONENT
// ============================================================================
export default function Footer({ className }) {
  const currentYear = new Date().getFullYear();
  const [isHovered, setIsHovered] = useState(false);

  return (
    <footer
      className={clsx(
        "relative border-t border-white/5",
        "bg-slate-900/80 backdrop-blur-lg",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Gradient border */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />

      {/* Main Footer Content */}
      <div className="max-w-[1800px] mx-auto px-4 lg:px-8">
        {/* Primary Row */}
        <div className="flex flex-wrap items-center justify-between gap-4 py-4">
          {/* Left: Health Status */}
          <HealthStatus />

          {/* Center: Quick Links (hidden on mobile) */}
          <div className="hidden md:block">
            <QuickLinks />
          </div>

          {/* Right: Security Badges & Version */}
          <div className="flex items-center gap-4">
            <div className="hidden lg:block">
              <SecurityBadges />
            </div>
            <div className="h-4 w-px bg-white/10 hidden lg:block" />
            <VersionInfo />
          </div>
        </div>

        {/* Secondary Row (visible on larger screens or hover) */}
        <AnimatePresence>
          {(isHovered || window.innerWidth < 768) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div
                className="flex flex-wrap items-center justify-between gap-4 py-3 
                            border-t border-white/5"
              >
                {/* Copyright */}
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>© {currentYear} SecureDevOps AI.</span>
                  <span className="hidden sm:inline">All rights reserved.</span>
                </div>

                {/* Made with love */}
                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <span>Made with</span>
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <HeartSolidIcon className="w-3.5 h-3.5 text-red-400" />
                  </motion.div>
                  <span>by the SecureDevOps Team</span>
                </div>

                {/* Legal Links */}
                <div className="flex items-center gap-4">
                  <Link
                    to="/privacy"
                    className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    Privacy Policy
                  </Link>
                  <Link
                    to="/terms"
                    className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    Terms of Service
                  </Link>
                  <Link
                    to="/security"
                    className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    Security
                  </Link>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </footer>
  );
}
