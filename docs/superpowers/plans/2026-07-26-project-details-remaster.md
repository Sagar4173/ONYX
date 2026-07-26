# ProjectDetails Remaster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remaster the ProjectDetails page into a security intelligence command center with split-pane layout, circuit-board scan pipeline, CSS 3D security globe, canvas radar chart, vulnerability matrix, animated metrics, and functional settings.

**Architecture:** Single-page remaster across 16 files in `src/components/projects/`. New visual components (Globe, Pipeline, Radar, Console) are pure presentational — they receive data via props and emit nothing. Tab components orchestrate sub-components. The main orchestrator (ProjectDetails.jsx) manages all state, polling, and mutations.

**Tech Stack:** React, Tailwind CSS, framer-motion, Canvas API, SVG, react-router-dom, @tanstack/react-query, react-hot-toast

## Global Constraints

- Zero new npm dependencies — all visualizations use native Canvas, SVG, or CSS
- All new files go in `src/components/projects/`
- Follow existing ONYX design language: cyan-400/violet-500/cyan-400 gradients, glassmorphism, dark theme
- All interactive elements must be keyboard-accessible
- `prefers-reduced-motion: reduce` must disable framer-motion animations
- Lint: `npx eslint src/components/projects/` must pass with 0 errors, 0 warnings
- Every component with async data must handle loading, empty, and error states

---
## File Structure

**New files:**
- `src/components/projects/ParticleBackground.jsx` — CSS ambient particle layer
- `src/components/projects/SecurityScoreGlobe.jsx` — CSS 3D rotating globe
- `src/components/projects/ScanPipeline.jsx` — Circuit-board SVG pipeline
- `src/components/projects/LiveConsole.jsx` — Terminal log viewer
- `src/components/projects/MetricCard.jsx` — Animated stat card with sparkline
- `src/components/projects/MetricsDashboard.jsx` — 4-card metric grid
- `src/components/projects/SecurityRadar.jsx` — Canvas radar chart
- `src/components/projects/VulnerabilityMatrix.jsx` — Heatmap grid
- `src/components/projects/ActivityTimeline.jsx` — Event timeline
- `src/components/projects/OverviewTab.jsx` — Tab orchestrator
- `src/components/projects/ProjectSidebar.jsx` — Left panel

**Modified files:**
- `src/components/projects/ScanHistoryTab.jsx` — Enhanced with compare, trend, timeline
- `src/components/projects/SettingsTab.jsx` — Functional settings panels
- `src/components/projects/EditProjectModal.jsx` — Tabbed modal with live preview
- `src/components/projects/DeleteProjectModal.jsx` — Enhanced with double-confirm
- `src/components/projects/ProjectDetails.jsx` — Main orchestrator integration
- `src/components/projects/index.js` — Add new exports

**Removed files:**
- `src/components/projects/ScanProgressBanner.jsx` — Replaced by ScanPipeline + LiveConsole
- `src/components/projects/QuickStatsCards.jsx` — Replaced by MetricsDashboard + MetricCard
- `src/components/projects/ProjectOverviewTab.jsx` — Replaced by OverviewTab (orchestrator)

---
### Task 1: ParticleBackground.jsx

**Files:**
- Create: `src/components/projects/ParticleBackground.jsx`

**Interface:**
- Consumes: `isScanActive: boolean`
- Produces: A CSS-only particle layer rendered as a fixed-position div behind all content

- [ ] **Step 1: Create the component**

```jsx
const ParticleBackground = ({ isScanActive = false }) => {
  const particleCount = 60;
  const particles = useMemo(() => {
    const p = [];
    const isFast = isScanActive;
    for (let i = 0; i < particleCount; i++) {
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const size = 1 + Math.random() * 2;
      const drift = 8 + Math.random() * 12;
      const sway = 12 + Math.random() * 8;
      const delay = Math.random() * 10;
      const isViolet = Math.random() > 0.6;
      const color = isViolet ? 'rgba(139,92,246,0.12)' : 'rgba(6,182,212,0.15)';
      p.push({ x, y, size, drift, sway, delay, color, isViolet });
    }
    return p;
  }, [isScanActive]);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      {particles.map((p, i) => (
        <div
          key={i}
          className={`absolute rounded-full ${isScanActive ? 'animate-particle-fast' : 'animate-particle-slow'}`}
          style={{
            left: `${p.x}%`, top: `${p.y}%`,
            width: `${p.size}px`, height: `${p.size}px`,
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${isScanActive ? p.drift * 0.5 : p.drift}s, ${isScanActive ? p.sway * 0.5 : p.sway}s`,
            boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
          }}
        />
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Add keyframe animations to index.css**

```css
/* In src/index.css */
@keyframes particle-float-slow {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.4; }
  25% { transform: translateY(-30px) translateX(15px); opacity: 0.8; }
  50% { transform: translateY(-10px) translateX(-10px); opacity: 0.5; }
  75% { transform: translateY(-40px) translateX(5px); opacity: 0.7; }
}
@keyframes particle-float-fast {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.6; }
  25% { transform: translateY(-60px) translateX(30px); opacity: 1; }
  50% { transform: translateY(-20px) translateX(-20px); opacity: 0.8; }
  75% { transform: translateY(-80px) translateX(10px); opacity: 0.9; }
}
```

```css
.animate-particle-slow { animation: particle-float-slow var(--drift, 12s) ease-in-out infinite, particle-sway var(--sway, 15s) ease-in-out infinite; }
.animate-particle-fast { animation: particle-float-fast calc(var(--drift, 12s) * 0.5) ease-in-out infinite, particle-sway calc(var(--sway, 15s) * 0.5) ease-in-out infinite; }
```

- [ ] **Step 3: Verify with lint**

Run: `npx eslint src/components/projects/ParticleBackground.jsx`
Expected: 0 errors, 0 warnings

---
### Task 2: SecurityScoreGlobe.jsx

**Files:**
- Create: `src/components/projects/SecurityScoreGlobe.jsx`

**Interface:**
- Consumes: `score: number (0-100), isScanActive: boolean, size?: number (default 140), className?: string`
- Produces: A CSS 3D rotating sphere with orbiting particles, score display, and color states

- [ ] **Step 1: Create the component**

```jsx
import { useMemo } from "react";
import { motion, useAnimation } from "framer-motion";

const LAT_LINES = 6;
const LON_LINES = 8;

const SecurityScoreGlobe = ({ score = 0, isScanActive = false, size = 140, className = "" }) => {
  const controls = useAnimation();
  const scoreColor = score >= 80 ? "rgba(34,197,94,0.4)" : score >= 60 ? "rgba(234,179,8,0.4)" : "rgba(239,68,68,0.4)";
  const pulseDuration = score >= 80 ? 3 : score >= 60 ? 2 : 1;
  const radius = size / 2;

  useMemo(() => {
    controls.start({
      rotateY: 360, rotateX: [0, 5, 0, -5, 0],
      transition: { rotateY: { duration: isScanActive ? 6 : 12, repeat: Infinity, ease: "linear" }, rotateX: { duration: 8, repeat: Infinity, ease: "easeInOut" } },
    });
  }, [isScanActive, controls]);

  const latLines = useMemo(() => {
    return Array.from({ length: LAT_LINES }, (_, i) => {
      const angle = ((i + 1) / (LAT_LINES + 1)) * 180;
      const r = radius * Math.sin((angle * Math.PI) / 180);
      const ry = radius * Math.cos((angle * Math.PI) / 180);
      return { r, ry, key: `lat-${i}` };
    });
  }, [radius]);

  const lonLines = useMemo(() => {
    return Array.from({ length: LON_LINES }, (_, i) => {
      const angle = (i / LON_LINES) * 360;
      return { angle, key: `lon-${i}` };
    });
  }, []);

  const particles = useMemo(() => {
    return Array.from({ length: isScanActive ? 8 : 5 }, (_, i) => ({
      orbit: 30 + Math.random() * 50,
      speed: (isScanActive ? 2 : 1) * (4 + Math.random() * 6),
      delay: Math.random() * 4,
      color: ["#ef4444", "#f97316", "#eab308", "#22d3ee"][i % 4],
      size: 3 + Math.random() * 2,
    }));
  }, [isScanActive]);

  return (
    <motion.div
      className={`relative ${className}`}
      style={{ width: size, height: size, perspective: size * 4 }}
      animate={{ scale: [1, 1.02, 1] }}
      transition={{ duration: pulseDuration, repeat: Infinity, ease: "easeInOut" }}
    >
      <motion.div
        className="w-full h-full"
        style={{ transformStyle: "preserve-3d" }}
        animate={controls}
      >
        {/* Latitude lines */}
        <svg width={size} height={size} className="absolute inset-0">
          {latLines.map(({ r, key }) => (
            <ellipse key={key} cx={radius} cy={radius} rx={r} ry={r * 0.4}
              fill="none" stroke={scoreColor} strokeWidth="0.5" opacity="0.6"
            />
          ))}
          {lonLines.map(({ angle, key }) => (
            <ellipse key={key} cx={radius} cy={radius}
              rx={radius * Math.abs(Math.cos((angle * Math.PI) / 180))}
              ry={radius * 0.4}
              fill="none" stroke={scoreColor} strokeWidth="0.5" opacity="0.6"
              transform={`rotate(${angle}, ${radius}, ${radius})`}
            />
          ))}
        </svg>

        {/* Glow behind score */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="rounded-full" style={{
            width: size * 0.5, height: size * 0.5,
            background: `radial-gradient(circle, ${scoreColor} 0%, transparent 70%)`,
          }} />
        </div>

        {/* Score number */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.span
            className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 bg-clip-text text-transparent"
            key={Math.round(score)}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", damping: 15, stiffness: 200 }}
          >
            {Math.round(score)}
          </motion.span>
        </div>
      </motion.div>

      {/* Orbiting particles */}
      {particles.map((p, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: p.size, height: p.size,
            backgroundColor: p.color,
            boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
            left: radius - p.size / 2, top: radius - p.size / 2,
          }}
          animate={{
            rotate: [0, 360],
            x: [0, p.orbit * Math.cos(0), 0, p.orbit * Math.cos(Math.PI), 0],
            y: [0, p.orbit * Math.sin(0) * 0.3, 0, p.orbit * Math.sin(Math.PI) * 0.3, 0],
          }}
          transition={{ duration: p.speed, repeat: Infinity, ease: "linear", delay: p.delay }}
          style={{ transformOrigin: `${radius}px ${radius}px` }}
        />
      ))}
    </motion.div>
  );
};

export default SecurityScoreGlobe;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/SecurityScoreGlobe.jsx`
Expected: 0 errors, 0 warnings

**Note:** Particles use absolute positioning with transform-origin for orbit. The mathematical simplification (using x/y animation as approximate ellipse) is intentional — perfect orbital mechanics would require JS, which is too heavy for this visual effect.

---
### Task 3: ScanPipeline.jsx (Circuit Board)

**Files:**
- Create: `src/components/projects/ScanPipeline.jsx`

**Interface:**
- Consumes: `stages: Array<{label, icon?, status, progress}>, scanProgress: number, activeScan: object, projectName: string`
- Produces: SVG circuit board visualization with animated tracer lines and node states

- [ ] **Step 1: Create the component**

```jsx
import { motion } from "framer-motion";
import { ShieldCheckIcon, CodeBracketIcon, KeyIcon, CubeIcon, CloudIcon, BeakerIcon, SparklesIcon } from "@heroicons/react/24/outline";

const STAGE_ICONS = [ShieldCheckIcon, CodeBracketIcon, KeyIcon, CubeIcon, CloudIcon, BeakerIcon, SparklesIcon];

const STAGES = [
  { label: "Initialize", min: 0, max: 10 },
  { label: "Clone", min: 10, max: 20 },
  { label: "SAST", min: 20, max: 35 },
  { label: "Secrets", min: 35, max: 50 },
  { label: "Dependencies", min: 50, max: 70 },
  { label: "Container", min: 70, max: 90 },
  { label: "AI Analysis", min: 90, max: 100 },
];

const NodeState = ({ stage, idx, progress, isLast }) => {
  const isActive = progress >= stage.min && progress < stage.max;
  const isComplete = progress >= stage.max;
  const Icon = STAGE_ICONS[idx];

  return (
    <motion.div className="flex flex-col items-center" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: idx * 0.1, type: "spring", damping: 15 }}>
      <motion.div
        className={`relative flex items-center justify-center w-14 h-14 rounded-xl border-2 transition-colors ${
          isComplete ? "bg-green-900/40 border-green-500 shadow-lg shadow-green-500/20" :
          isActive ? "bg-cyan-900/40 border-cyan-400 shadow-lg shadow-cyan-500/30" :
          "bg-gray-800/50 border-gray-700"
        }`}
        animate={isActive ? { scale: [1, 1.1, 1] } : {}}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        {isComplete ? (
          <motion.svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
            transition={{ duration: 0.5, type: "spring" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </motion.svg>
        ) : (
          <Icon className={`w-6 h-6 ${isActive ? "text-cyan-400" : "text-gray-500"}`} />
        )}
        {/* Glow ring for active */}
        {isActive && (
          <div className="absolute inset-0 rounded-xl animate-ping opacity-20 bg-cyan-400" />
        )}
      </motion.div>
      <span className={`mt-2 text-xs font-medium ${isComplete ? "text-green-400" : isActive ? "text-cyan-400" : "text-gray-500"}`}>
        {stage.label}
      </span>
    </motion.div>
  );
};

const ScanPipeline = ({ scanProgress = 0, activeScan, projectName }) => {
  if (!activeScan) return null;

  return (
    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Scan Pipeline</h3>
          <p className="text-sm text-gray-400">{projectName || "Repository"}</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded-full text-xs font-medium border border-cyan-500/30 animate-pulse">
            {activeScan.status?.toUpperCase() || "RUNNING"}
          </span>
          <span className="text-2xl font-bold text-cyan-400">{Math.round(scanProgress)}%</span>
        </div>
      </div>

      {/* Circuit board SVG connectors */}
      <div className="relative">
        <svg className="absolute top-7 left-0 w-full h-8 pointer-events-none" preserveAspectRatio="none">
          <defs>
            <linearGradient id="activeTracer" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
          {/* Background track */}
          <line x1="30" y1="4" x2="100%" y2="4" stroke="#374151" strokeWidth="2" strokeDasharray="4 4" />
          {/* Active progress track */}
          <line x1="30" y1="4" x2={`${30 + (scanProgress / 100) * 90}%`} y2="4" stroke="url(#activeTracer)" strokeWidth="2.5" strokeLinecap="round" />
        </svg>

        {/* Pipeline nodes */}
        <div className="flex justify-between relative">
          {STAGES.map((stage, idx) => (
            <div key={idx} className="flex flex-col items-center relative z-10">
              <NodeState stage={stage} idx={idx} progress={scanProgress} isLast={idx === STAGES.length - 1} />
            </div>
          ))}
        </div>
      </div>

      {/* Current scanner info */}
      {activeScan.current_scanner && (
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="flex items-center space-x-2 text-sm">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-gray-400">Current:</span>
            <span className="text-cyan-300 font-medium">{activeScan.current_scanner}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanPipeline;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/ScanPipeline.jsx`
Expected: 0 errors, 0 warnings

---
### Task 4: LiveConsole.jsx

**Files:**
- Create: `src/components/projects/LiveConsole.jsx`

**Interface:**
- Consumes: `logLines: Array<{timestamp, level, message}>, isExpanded?: boolean, onToggle?: () => void`
- Produces: Collapsible VS Code-style terminal

- [ ] **Step 1: Create the component**

```jsx
import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDownIcon, CodeBracketIcon } from "@heroicons/react/24/outline";

const LEVEL_COLORS = {
  INFO: "text-cyan-400", WARN: "text-yellow-400", ERROR: "text-red-400",
  DEBUG: "text-gray-500", SCAN: "text-green-400",
};

const LiveConsole = ({ logLines = [], isExpanded = false, onToggle }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (isExpanded && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logLines.length, isExpanded]);

  return (
    <div className="mb-6 rounded-xl overflow-hidden border border-gray-700/50">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-900/80 hover:bg-gray-900 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      >
        <div className="flex items-center space-x-2">
          <CodeBracketIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-sm font-medium text-white">Scan Console</span>
          <span className="text-xs text-gray-500">({logLines.length} lines)</span>
        </div>
        <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDownIcon className="h-4 w-4 text-gray-400" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <pre className="bg-gray-950 p-4 text-xs leading-6 font-mono overflow-auto max-h-64 custom-scrollbar">
              <code>
                {logLines.length === 0 ? (
                  <span className="text-gray-600">Waiting for scan output...</span>
                ) : (
                  logLines.map((line, i) => (
                    <div key={i} className="whitespace-pre-wrap break-all">
                      <span className="text-gray-600">[{line.timestamp}] </span>
                      <span className={LEVEL_COLORS[line.level] || "text-gray-300"}>
                        [{line.level}]
                      </span>
                      <span className="text-gray-300"> {line.message}</span>
                    </div>
                  ))
                )}
                <div ref={bottomRef} />
                {logLines.length > 0 && (
                  <span className="inline-block w-2 h-4 bg-cyan-400 animate-pulse ml-1" />
                )}
              </code>
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default LiveConsole;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/LiveConsole.jsx`
Expected: 0 errors, 0 warnings

---
### Task 5: MetricCard.jsx & MetricsDashboard.jsx

**Files:**
- Create: `src/components/projects/MetricCard.jsx`
- Create: `src/components/projects/MetricsDashboard.jsx`

**Interface:**
- Consumes (MetricCard): `icon: Component, label: string, value: number, trend?: number[], color: string, formatter?: (n) => string`
- Consumes (MetricsDashboard): `metrics: array, scanCompleted: boolean, liveSecurityScore: number, ...`
- Produces: Animated stat card with spring counter and SVG sparkline

- [ ] **Step 1: Create MetricCard.jsx**

```jsx
import { useSpring, useTransform, motion } from "framer-motion";

const Sparkline = ({ data = [], color }) => {
  if (data.length < 2) return null;
  const w = 80; const h = 24; const max = Math.max(...data, 1); const min = Math.min(...data, 0);
  const range = max - min || 1;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="flex-shrink-0">
      <defs>
        <linearGradient id={`sparkline-fill-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <polygon points={`0,${h} ${points} ${w},${h}`} fill={`url(#sparkline-fill-${color})`} />
    </svg>
  );
};

const MetricCard = ({ icon: Icon, label, value = 0, trend, color = "#06b6d4", formatter = (v) => v }) => {
  const springValue = useSpring(0, { damping: 20, stiffness: 100 });
  const displayValue = useTransform(springValue, (v) => formatter(Math.round(v)));

  springValue.set(value);

  return (
    <motion.div
      className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 group hover:-translate-y-0.5 transition-all duration-200"
      whileHover={{ y: -2 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="p-2.5 rounded-xl" style={{ background: `${color}20` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        {trend && <Sparkline data={trend} color={color} />}
      </div>
      <motion.p className="text-2xl font-bold text-white font-mono">
        {displayValue}
      </motion.p>
      <p className="text-sm text-gray-400 mt-0.5">{label}</p>
    </motion.div>
  );
};

export default MetricCard;
```

- [ ] **Step 2: Create MetricsDashboard.jsx**

```jsx
import { ChartBarIcon, ExclamationTriangleIcon, ShieldCheckIcon, ClockIcon } from "@heroicons/react/24/outline";
import MetricCard from "./MetricCard";

const MetricsDashboard = ({ stats = {}, vulnCounts, totalVulns, liveSecurityScore, scanCompleted, lastScanDate }) => {
  const metrics = [
    {
      icon: ChartBarIcon, label: "Total Scans", color: "#06b6d4",
      value: (scanCompleted ? (stats.total_scans || 0) + 1 : stats.total_scans) || (scanCompleted ? 1 : 0),
    },
    {
      icon: ExclamationTriangleIcon, label: "Vulnerabilities", color: "#ef4444",
      value: totalVulns,
    },
    {
      icon: ShieldCheckIcon, label: "Security Score", color: "#22c55e",
      value: Math.round(liveSecurityScore ?? stats.security_score ?? 0),
    },
    {
      icon: ClockIcon, label: "Last Scan", color: "#a78bfa",
      value: scanCompleted ? "Just now" : lastScanDate ? "View History" : "Never",
      formatter: (v) => v,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {metrics.map((m, i) => (
        <MetricCard key={i} {...m} />
      ))}
    </div>
  );
};

export default MetricsDashboard;
```

- [ ] **Step 3: Verify with lint**

Run: `npx eslint src/components/projects/MetricCard.jsx src/components/projects/MetricsDashboard.jsx`
Expected: 0 errors, 0 warnings

---
### Task 6: SecurityRadar.jsx (Canvas)

**Files:**
- Create: `src/components/projects/SecurityRadar.jsx`

**Interface:**
- Consumes: `data: Array<{label, value: 0-100}>, size?: number, className?: string`
- Produces: Canvas-based 6-axis radar chart with animated sweep line

- [ ] **Step 1: Create the component**

```jsx
import { useRef, useEffect } from "react";

const DEFAULT_AXES = [
  { label: "SAST", value: 0 }, { label: "Secrets", value: 0 },
  { label: "Dependencies", value: 0 }, { label: "Container", value: 0 },
  { label: "IaC", value: 0 }, { label: "DAST", value: 0 },
];

const SecurityRadar = ({ data = DEFAULT_AXES, size = 280, className = "" }) => {
  const canvasRef = useRef(null);
  const sweepRef = useRef(0);
  const rafRef = useRef(null);
  const center = size / 2;
  const radius = size * 0.38;
  const numAxes = data.length;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const draw = () => {
      ctx.clearRect(0, 0, size, size);
      const angleStep = (2 * Math.PI) / numAxes;

      // Draw grid circles
      for (let g = 1; g <= 4; g++) {
        ctx.beginPath();
        ctx.arc(center, center, (radius / 4) * g, 0, 2 * Math.PI);
        ctx.strokeStyle = `rgba(55, 65, 81, ${0.2 + g * 0.1})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }

      // Draw axes
      data.forEach((_, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        ctx.beginPath();
        ctx.moveTo(center, center);
        ctx.lineTo(center + radius * Math.cos(angle), center + radius * Math.sin(angle));
        ctx.strokeStyle = "rgba(75, 85, 99, 0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // Draw data polygon
      ctx.beginPath();
      data.forEach((d, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const r = (d.value / 100) * radius;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = "rgba(6, 182, 212, 0.15)";
      ctx.fill();
      ctx.strokeStyle = "#06b6d4";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Data points
      data.forEach((d, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const r = (d.value / 100) * radius;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fillStyle = d.value > 0 ? "#22d3ee" : "rgba(75, 85, 99, 0.5)";
        ctx.fill();
        ctx.strokeStyle = d.value > 0 ? "#67e8f9" : "transparent";
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      // Sweep line
      sweepRef.current += 0.005;
      if (sweepRef.current > 2 * Math.PI) sweepRef.current = 0;
      const sweepAngle = -Math.PI / 2 + sweepRef.current;
      const gradient = ctx.createRadialGradient(center, center, 0, center, center, radius);
      gradient.addColorStop(0, "rgba(6, 182, 212, 0.08)");
      gradient.addColorStop(sweepRef.current / (2 * Math.PI) > 0.5 ? 0.5 : 0, "rgba(139, 92, 246, 0.03)");
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.arc(center, center, radius, sweepAngle - 0.3, sweepAngle);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();

      // Axes labels
      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      data.forEach((d, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const labelR = radius + 20;
        const x = center + labelR * Math.cos(angle);
        const y = center + labelR * Math.sin(angle);
        ctx.fillText(d.label, x, y);
      });

      rafRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [data, size, center, radius, numAxes]);

  return <canvas ref={canvasRef} width={size} height={size} className={className} />;
};

export default SecurityRadar;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/SecurityRadar.jsx`
Expected: 0 errors, 0 warnings

---
### Task 7: VulnerabilityMatrix.jsx & ActivityTimeline.jsx

**Files:**
- Create: `src/components/projects/VulnerabilityMatrix.jsx`
- Create: `src/components/projects/ActivityTimeline.jsx`

**Interfaces:**
- VulnerabilityMatrix: `vulnCounts: object, findings?: Array<{type, severity, count}>`
- ActivityTimeline: `events: Array<{id, type, description, timestamp, severity}>, isScanActive?: boolean`

- [ ] **Step 1: Create VulnerabilityMatrix.jsx**

```jsx
import { motion } from "framer-motion";

const SEVERITY_CONFIG = {
  critical: { bg: "rgba(239,68,68,", text: "text-red-400", label: "Critical" },
  high: { bg: "rgba(249,115,22,", text: "text-orange-400", label: "High" },
  medium: { bg: "rgba(234,179,8,", text: "text-yellow-400", label: "Medium" },
  low: { bg: "rgba(34,211,238,", text: "text-cyan-400", label: "Low" },
};

const VulnerabilityMatrix = ({ vulnCounts = {} }) => {
  const items = Object.entries(SEVERITY_CONFIG).map(([sev, cfg]) => ({
    severity: sev, count: vulnCounts[sev] || 0, ...cfg,
  }));
  const maxCount = Math.max(...items.map((i) => i.count), 1);

  return (
    <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
      <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Matrix</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {items.map((item) => (
          <motion.div
            key={item.severity}
            className="rounded-xl p-4 text-center border transition-all cursor-default group hover:scale-[1.02]"
            style={{
              backgroundColor: `${item.bg}${Math.min(0.1 + (item.count / maxCount) * 0.4, 0.5)})`,
              borderColor: `${item.bg}${Math.min(0.2 + (item.count / maxCount) * 0.3, 0.5)})`,
            }}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", damping: 15 }}
          >
            <motion.p
              className={`text-3xl font-bold ${item.text} font-mono`}
              key={item.count}
              initial={{ scale: 1.3 }} animate={{ scale: 1 }}
              transition={{ type: "spring", damping: 15 }}
            >
              {item.count}
            </motion.p>
            <p className="text-gray-400 text-sm mt-1 capitalize">{item.label}</p>
          </motion.div>
        ))}
      </div>
      {items.every((i) => i.count === 0) && (
        <p className="text-center text-gray-500 text-sm mt-4">No vulnerabilities found in latest scan</p>
      )}
    </div>
  );
};

export default VulnerabilityMatrix;
```

- [ ] **Step 2: Create ActivityTimeline.jsx**

```jsx
import { motion } from "framer-motion";
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon, ExclamationTriangleIcon } from "@heroicons/react/24/solid";

const EVENT_ICONS = {
  scan_started: ArrowPathIcon, scan_completed: CheckCircleIcon,
  scan_failed: XCircleIcon, finding_detected: ExclamationTriangleIcon,
};

const EVENT_COLORS = {
  scan_started: "text-cyan-400", scan_completed: "text-green-400",
  scan_failed: "text-red-400", finding_detected: "text-yellow-400",
};

const ActivityTimeline = ({ events = [], isScanActive = false }) => {
  if (events.length === 0) {
    return (
      <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">Activity</h3>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="flex space-x-1 justify-center mb-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className={`w-2 h-2 rounded-full bg-gray-600 animate-bounce`} style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
            </div>
            <p className="text-gray-500 text-sm">No recent activity</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
      <h3 className="text-lg font-semibold text-white mb-4">Activity</h3>
      <div className="relative">
        {/* Connector line */}
        <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-gradient-to-b from-cyan-500/40 to-violet-500/40" />
        <div className="space-y-4">
          {events.map((event, i) => {
            const Icon = EVENT_ICONS[event.type] || ArrowPathIcon;
            const color = EVENT_COLORS[event.type] || "text-gray-400";
            return (
              <motion.div
                key={event.id || i}
                className="flex items-start space-x-3"
                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05, type: "spring", damping: 20 }}
              >
                <div className={`relative z-10 p-1.5 rounded-full bg-gray-900 ${color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0 pt-0.5">
                  <p className="text-sm text-white">{event.description}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{event.timestamp}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ActivityTimeline;
```

- [ ] **Step 3: Verify with lint**

Run: `npx eslint src/components/projects/VulnerabilityMatrix.jsx src/components/projects/ActivityTimeline.jsx`
Expected: 0 errors, 0 warnings

---
### Task 8: OverviewTab.jsx (Orchestrator)

**Files:**
- Create: `src/components/projects/OverviewTab.jsx`

**Interface:**
- Consumes: `project, vulnCounts, events?, radarData?`
- Produces: Rendered overview tab composing SecurityRadar, VulnerabilityMatrix, ActivityTimeline, Project Info, and Dependencies Summary

- [ ] **Step 1: Create the component**

```jsx
import { GlobeAltIcon } from "@heroicons/react/24/outline";
import { getPriorityColor, getStatusColor } from "./projectHelpers";
import SecurityRadar from "./SecurityRadar";
import VulnerabilityMatrix from "./VulnerabilityMatrix";
import ActivityTimeline from "./ActivityTimeline";

const OverviewTab = ({ project, vulnCounts, events = [] }) => {
  const radarData = [
    { label: "SAST", value: project.stats?.sast_coverage || 0 },
    { label: "Secrets", value: project.stats?.secrets_coverage || 0 },
    { label: "Dependencies", value: project.stats?.deps_coverage || 0 },
    { label: "Container", value: project.stats?.container_coverage || 0 },
    { label: "IaC", value: project.stats?.iac_coverage || 0 },
    { label: "DAST", value: project.stats?.dast_coverage || 0 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left column: Radar + Matrix */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50 flex items-center justify-center">
          <SecurityRadar data={radarData} />
        </div>
        <VulnerabilityMatrix vulnCounts={vulnCounts} />
      </div>

      {/* Right column: Info + Activity */}
      <div className="space-y-6">
        <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Project Info</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Status</span>
              <span className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getStatusColor(project.status)}`}>{project.status}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Priority</span>
              <span className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getPriorityColor(project.priority)}`}>{project.priority}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Category</span>
              <span className="text-white text-sm">{project.category}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Created</span>
              <span className="text-white text-sm">{new Date(project.created_at).toLocaleDateString()}</span>
            </div>
            {project.repository?.url && (
              <div className="pt-3 border-t border-gray-700/50">
                <div className="flex items-start space-x-2">
                  <GlobeAltIcon className="w-4 h-4 text-gray-400 mt-0.5" />
                  <a href={project.repository.url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 text-sm break-all">{project.repository.url}</a>
                </div>
                <p className="text-gray-500 text-xs mt-1 font-mono">Branch: {project.repository.branch || "main"}</p>
              </div>
            )}
          </div>
        </div>

        <ActivityTimeline events={events} />

        {/* Dependencies Summary */}
        {project.stats?.vulnerable_deps > 0 && (
          <div className="bg-gray-900/50 rounded-xl p-5 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-3">Dependencies</h3>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-400 text-sm">Vulnerable</span>
              <span className="text-red-400 font-bold">{project.stats.vulnerable_deps}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Total packages</span>
              <span className="text-white font-mono">{project.stats.total_deps || "-"}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OverviewTab;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/OverviewTab.jsx`
Expected: 0 errors, 0 warnings

---
### Task 9: ScanHistoryTab.jsx (Enhanced)

**Files:**
- Modify: `src/components/projects/ScanHistoryTab.jsx`

**Scope:** Replace entire file content. Add comparison mode, timeline view toggle, trend sparkline, depth-styled cards.

- [ ] **Step 1: Rewrite ScanHistoryTab.jsx**

```jsx
import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowPathIcon, ClockIcon, EyeIcon, ChartBarIcon, ArrowsRightLeftIcon } from "@heroicons/react/24/outline";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import { Button, EmptyState } from "../../styles/components";
import { utils } from "../../services/api";

const ScanStatusBadge = ({ status }) => {
  const config = {
    completed: "bg-green-500/20 text-green-400 border border-green-500/30",
    running: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse",
    pending: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    failed: "bg-red-500/20 text-red-400 border border-red-500/30",
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${config[status] || config.failed}`}>
      {status === "running" && <ArrowPathIcon className="h-3 w-3 animate-spin" />}
      <span className="capitalize">{status}</span>
    </span>
  );
};

const MiniSeverityBar = ({ findings }) => {
  if (!findings) return null;
  const total = (findings.critical || 0) + (findings.high || 0) + (findings.medium || 0) + (findings.low || 0) || 1;
  return (
    <div className="flex h-1.5 rounded-full overflow-hidden w-24">
      <div style={{ width: `${((findings.critical || 0) / total) * 100}%`, backgroundColor: "#ef4444" }} />
      <div style={{ width: `${((findings.high || 0) / total) * 100}%`, backgroundColor: "#f97316" }} />
      <div style={{ width: `${((findings.medium || 0) / total) * 100}%`, backgroundColor: "#eab308" }} />
      <div style={{ width: `${((findings.low || 0) / total) * 100}%`, backgroundColor: "#22d3ee" }} />
    </div>
  );
};

const CompareOverlay = ({ scanA, scanB, onClose }) => {
  if (!scanA || !scanB) return null;
  const getFindings = (s) => s.findings_by_severity || {};
  return (
    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden mb-6">
      <div className="bg-gray-900/80 rounded-xl p-6 border border-cyan-500/30">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <ArrowsRightLeftIcon className="w-5 h-5 text-cyan-400" />
            <span>Scan Comparison</span>
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-sm">Close</button>
        </div>
        <div className="grid grid-cols-2 gap-6">
          {[scanA, scanB].map((scan, i) => (
            <div key={i} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
              <p className="text-sm text-gray-400 mb-2">Scan #{scan.id?.slice(-8)}</p>
              <div className="space-y-2">
                {["critical", "high", "medium", "low"].map((sev) => {
                  const countA = getFindings(scanA)[sev] || 0;
                  const countB = getFindings(scanB)[sev] || 0;
                  const diff = countB - countA;
                  return (
                    <div key={sev} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-gray-400">{sev}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-white font-mono">{scan === scanA ? countA : countB}</span>
                        {i === 1 && diff !== 0 && (
                          <span className={`text-xs ${diff > 0 ? "text-red-400" : "text-green-400"}`}>
                            {diff > 0 ? `+${diff}` : diff}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

const ScanHistoryTab = ({ scanHistory, scanHistoryLoading, onStartScan, isStarting }) => {
  const [viewMode, setViewMode] = useState("list");
  const [compareIds, setCompareIds] = useState([]);
  const [showCompare, setShowCompare] = useState(false);

  const reports = scanHistory?.reports || [];

  const handleToggleCompare = (id) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  if (scanHistoryLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-gray-900/50 rounded-xl p-6 border border-gray-700/50 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-1/4 mb-2" />
            <div className="h-3 bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!reports.length) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Scan History</h3>
          <button onClick={onStartScan} disabled={isStarting} className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg transition-all disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
            {isStarting ? "Starting..." : "New Scan"}
          </button>
        </div>
        <EmptyState
          icon={<ChartBarIcon className="h-12 w-12" />}
          title="No Scans Yet"
          description="Start your first security scan to see results here."
          action={<Button variant="primary" onClick={onStartScan} disabled={isStarting} isLoading={isStarting}>Start First Scan</Button>}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-white">Scan History</h3>
          <div className="flex bg-gray-800/50 rounded-lg p-0.5 border border-gray-700/50">
            <button onClick={() => setViewMode("list")} className={`px-3 py-1 text-xs rounded-md transition-all ${viewMode === "list" ? "bg-cyan-500/20 text-cyan-400" : "text-gray-400"}`}>List</button>
            <button onClick={() => setViewMode("timeline")} className={`px-3 py-1 text-xs rounded-md transition-all ${viewMode === "timeline" ? "bg-cyan-500/20 text-cyan-400" : "text-gray-400"}`}>Timeline</button>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {compareIds.length === 2 && (
            <button onClick={() => setShowCompare(!showCompare)} className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium border border-cyan-500/30 hover:bg-cyan-500/30 transition-all">
              {showCompare ? "Hide Compare" : "Compare Scans"}
            </button>
          )}
          <button onClick={onStartScan} disabled={isStarting} className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg transition-all disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
            {isStarting ? "Starting..." : "New Scan"}
          </button>
        </div>
      </div>

      {/* Compare overlay */}
      <AnimatePresence>
        {showCompare && compareIds.length === 2 && (
          <CompareOverlay
            scanA={reports.find((r) => r.id === compareIds[0])}
            scanB={reports.find((r) => r.id === compareIds[1])}
            onClose={() => { setShowCompare(false); setCompareIds([]); }}
          />
        )}
      </AnimatePresence>

      {/* Scan list */}
      <div className={viewMode === "timeline" ? "relative" : "space-y-4"}>
        {viewMode === "timeline" && (
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/30 to-violet-500/30" />
        )}
        {reports.map((scan, index) => (
          <motion.div
            key={scan.id}
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05, type: "spring", damping: 20 }}
            className={viewMode === "timeline" ? "relative flex items-start ml-4" : ""}
          >
            {viewMode === "timeline" && (
              <div className={`absolute left-0 w-4 h-4 rounded-full border-2 mt-5 -translate-x-1/2 z-10 ${
                scan.status === "completed" ? "bg-green-500 border-green-400" :
                scan.status === "failed" ? "bg-red-500 border-red-400" :
                "bg-gray-700 border-gray-500"
              }`} />
            )}
            <div className={`bg-gray-900/50 rounded-xl p-5 border transition-all flex-1 ${
              viewMode === "timeline" ? "ml-10" : ""
            } ${index === 0 && scan.status === "completed" ? "border-green-500/50 ring-1 ring-green-500/20" : "border-gray-700/50 hover:border-gray-600/50"}`}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="text-white font-medium">Scan #{scan.id?.slice(-8)}</h4>
                    <ScanStatusBadge status={scan.status} />
                    {index === 0 && scan.status === "completed" && (
                      <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full border border-cyan-500/30">Latest</span>
                    )}
                  </div>
                  <div className="flex items-center flex-wrap gap-4 text-sm text-gray-400 mb-2">
                    <span className="flex items-center space-x-1">
                      <ClockIcon className="h-4 w-4" />
                      <span>{utils.formatRelativeDate(scan.created_at)}</span>
                    </span>
                    <span>Branch: {scan.branch || "main"}</span>
                    {scan.duration_seconds && <span>{utils.formatDuration(scan.duration_seconds)}</span>}
                  </div>
                  {scan.status === "completed" && (
                    <div className="flex items-center space-x-3">
                      <MiniSeverityBar findings={scan.findings_by_severity} />
                      {(scan.total_findings === 0 || !scan.findings_by_severity?.critical && !scan.findings_by_severity?.high && !scan.findings_by_severity?.medium && !scan.findings_by_severity?.low) && (
                        <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-lg border border-green-500/30 font-medium flex items-center space-x-1">
                          <CheckCircleIcon className="h-3 w-3" />
                          <span>No Issues Found</span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <label className={`p-2 rounded-lg cursor-pointer transition-all ${compareIds.includes(scan.id) ? "bg-cyan-500/20 text-cyan-400" : "text-gray-500 hover:text-gray-300"}`}>
                    <input type="checkbox" checked={compareIds.includes(scan.id)} onChange={() => handleToggleCompare(scan.id)} className="sr-only" />
                    <ArrowsRightLeftIcon className="w-4 h-4" />
                  </label>
                  {scan.status === "completed" && (
                    <Link to={`/report/${scan.id}`} className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all">
                      <EyeIcon className="w-4 h-4" />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default ScanHistoryTab;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/ScanHistoryTab.jsx`
Expected: 0 errors, 0 warnings

---
### Task 10: SettingsTab.jsx (Functional)

**Files:**
- Modify: `src/components/projects/SettingsTab.jsx`

**Scope:** Replace placeholder with functional settings panels.

- [ ] **Step 1: Rewrite SettingsTab.jsx**

```jsx
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { projectsAPI } from "../../services/api";

const Panel = ({ title, description, children, defaultExpanded = true }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className="bg-gray-900/50 rounded-xl border border-gray-700/50 overflow-hidden">
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/30 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
        <div className="text-left">
          <h4 className="text-white font-medium">{title}</h4>
          {description && <p className="text-gray-400 text-sm">{description}</p>}
        </div>
        <svg className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && <div className="px-5 pb-5 border-t border-gray-700/50 pt-4">{children}</div>}
    </div>
  );
};

const SettingsTab = () => {
  const { projectId } = useParams();
  const queryClient = useQueryClient();

  const { data: project } = useQuery({ queryKey: ["project", projectId], enabled: !!projectId });

  const [form, setForm] = useState({ name: "", description: "", priority: "medium", status: "active", category: "other" });

  useEffect(() => {
    if (project) {
      setForm({ name: project.name || "", description: project.description || "", priority: project.priority || "medium", status: project.status || "active", category: project.category || "other" });
    }
  }, [project]);

  const updateMutation = useMutation({
    mutationFn: (data) => projectsAPI.updateProject(projectId, data),
    onSuccess: () => { toast.success("Settings saved"); queryClient.invalidateQueries({ queryKey: ["project", projectId] }); },
    onError: (err) => toast.error(err.message || "Failed to save"),
  });

  const handleSave = (section) => {
    updateMutation.mutate(section);
  };

  if (!project) return null;

  return (
    <div className="space-y-4 max-w-2xl">
      <Panel title="General" description="Basic project information" defaultExpanded={true}>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Name</label>
            <input type="text" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Category</label>
            <select value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50">
              <option value="web_application">Web Application</option><option value="api_service">API Service</option>
              <option value="mobile_app">Mobile App</option><option value="microservice">Microservice</option>
              <option value="library">Library</option><option value="infrastructure">Infrastructure</option><option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Priority</label>
            <select value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50">
              <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Status</label>
            <select value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50">
              <option value="active">Active</option><option value="inactive">Inactive</option><option value="archived">Archived</option>
            </select>
          </div>
        </div>
        <div className="mb-4">
          <label className="block text-sm text-gray-300 mb-1.5">Description</label>
          <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={2} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none" />
        </div>
        <button onClick={() => handleSave({ name: form.name, description: form.description, priority: form.priority, status: form.status, category: form.category })}
          disabled={updateMutation.isPending}
          className="px-4 py-2 bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white text-sm font-medium rounded-lg hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 transition-all disabled:opacity-50">
          {updateMutation.isPending ? "Saving..." : "Save"}
        </button>
      </Panel>

      <Panel title="Danger Zone" description="Irreversible destructive actions" defaultExpanded={false}>
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-4">
          <p className="text-red-300 text-sm font-medium mb-2">Delete this project</p>
          <p className="text-red-200/70 text-sm mb-3">Permanently remove this project and all associated scans, reports, and data.</p>
          <button onClick={() => document.dispatchEvent(new CustomEvent("open-delete-modal"))} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-all">
            Delete Project
          </button>
        </div>
      </Panel>
    </div>
  );
};

export default SettingsTab;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/SettingsTab.jsx`
Expected: 0 errors, 0 warnings

---
### Task 11: ProjectSidebar.jsx (Left Panel)

**Files:**
- Create: `src/components/projects/ProjectSidebar.jsx`

**Interface:**
- Consumes: `project, vulnCounts, totalVulns, securityScore, isScanActive, onEdit, onDelete`
- Produces: Glass left panel with project snapshot, globe, repo info, scanners, quick actions

- [ ] **Step 1: Create the component**

```jsx
import { motion } from "framer-motion";
import { PencilIcon, TrashIcon, GlobeAltIcon, ShieldCheckIcon } from "@heroicons/react/24/outline";
import { getPriorityColor, getStatusColor } from "./projectHelpers";
import SecurityScoreGlobe from "./SecurityScoreGlobe";
import LiveIndicator from "../../layouts/UIComponents";

const ProjectSidebar = ({ project, vulnCounts, totalVulns, securityScore, isScanActive, onEdit, onDelete }) => {
  return (
    <motion.aside
      className="w-[300px] flex-shrink-0 bg-gray-800/40 backdrop-blur-xl border-r border-gray-700/50 p-6 space-y-6 overflow-y-auto"
      initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", damping: 20 }}
    >
      {/* Project Snapshot */}
      <div>
        <h2 className="text-lg font-bold text-white mb-3">{project.name}</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          <span className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getStatusColor(project.status)}`}>{project.status}</span>
          <span className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${getPriorityColor(project.priority)}`}>{project.priority}</span>
          {project.category && (
            <span className="px-2.5 py-0.5 bg-gray-700/50 text-gray-300 rounded-lg text-xs">{project.category}</span>
          )}
        </div>
        {project.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {project.tags.slice(0, 5).map((tag) => (
              <span key={tag} className="px-2 py-0.5 bg-gray-700/30 text-gray-400 rounded text-xs">{tag}</span>
            ))}
          </div>
        )}
      </div>

      {/* Security Score Globe */}
      <div className="flex justify-center">
        <SecurityScoreGlobe score={securityScore} isScanActive={isScanActive} />
      </div>
      <div className="text-center -mt-2">
        <p className="text-xs text-gray-500">Security Score</p>
        <p className="text-xs text-gray-400">Last scan: {project.stats?.last_scan_date ? new Date(project.stats.last_scan_date).toLocaleDateString() : "Never"}</p>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-700/50" />

      {/* Repository Info */}
      {project.repository?.url && (
        <div>
          <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2 font-medium">Repository</h4>
          <div className="flex items-start space-x-2">
            <GlobeAltIcon className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <a href={project.repository.url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 text-xs break-all">{project.repository.url}</a>
          </div>
          <p className="text-gray-500 text-xs mt-1 font-mono ml-6">{project.repository.branch || "main"}</p>
        </div>
      )}

      {/* Enabled Scanners */}
      {project.scan_config?.enabled_scanners?.length > 0 && (
        <div>
          <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2 font-medium">Scanners</h4>
          <div className="flex flex-wrap gap-1.5">
            {project.scan_config.enabled_scanners.map((s) => (
              <span key={s} className="px-2 py-1 bg-cyan-500/15 text-cyan-400 rounded text-xs font-medium">{s.toUpperCase()}</span>
            ))}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div>
        <h4 className="text-xs uppercase tracking-wider text-gray-500 mb-2 font-medium">Vulnerabilities</h4>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-red-500/10 rounded-lg p-2.5 text-center border border-red-500/20">
            <p className="text-lg font-bold text-red-400">{vulnCounts.critical}</p>
            <p className="text-xs text-gray-500">Critical</p>
          </div>
          <div className="bg-orange-500/10 rounded-lg p-2.5 text-center border border-orange-500/20">
            <p className="text-lg font-bold text-orange-400">{vulnCounts.high}</p>
            <p className="text-xs text-gray-500">High</p>
          </div>
          <div className="bg-yellow-500/10 rounded-lg p-2.5 text-center border border-yellow-500/20">
            <p className="text-lg font-bold text-yellow-400">{vulnCounts.medium}</p>
            <p className="text-xs text-gray-500">Medium</p>
          </div>
          <div className="bg-cyan-500/10 rounded-lg p-2.5 text-center border border-cyan-500/20">
            <p className="text-lg font-bold text-cyan-400">{vulnCounts.low}</p>
            <p className="text-xs text-gray-500">Low</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="space-y-2 pt-2">
        <button onClick={onEdit} className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-gray-700/50 hover:bg-gray-700/70 text-gray-300 rounded-xl transition-all text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
          <PencilIcon className="w-4 h-4" />
          <span>Edit Project</span>
        </button>
        <button onClick={onDelete} className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl transition-all text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500">
          <TrashIcon className="w-4 h-4" />
          <span>Delete Project</span>
        </button>
      </div>
    </motion.aside>
  );
};

export default ProjectSidebar;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/ProjectSidebar.jsx`
Expected: 0 errors, 0 warnings

---
### Task 12: EditProjectModal.jsx (Tabbed with Live Preview)

**Files:**
- Modify: `src/components/projects/EditProjectModal.jsx`

**Scope:** Add tabbed navigation (Basic | Repository | Scanners | Tags), live preview card, tab entrance animations.

- [ ] **Step 1: Rewrite EditProjectModal.jsx**

```jsx
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { XMarkIcon, PencilIcon, InformationCircleIcon, CodeBracketIcon, ShieldCheckIcon, CheckCircleIcon, TagIcon } from "@heroicons/react/24/outline";
import { Button, Modal } from "../../styles/components";

const SCANNER_OPTIONS = [
  { value: "sast", label: "SAST", description: "Static Application Security Testing" },
  { value: "secrets", label: "Secrets", description: "Secret & credential detection" },
  { value: "dependency", label: "Dependencies", description: "Dependency vulnerability scanning" },
  { value: "container", label: "Container", description: "Container image security scanning" },
  { value: "iac", label: "IaC", description: "Infrastructure as Code scanning" },
  { value: "dast", label: "DAST", description: "Dynamic Application Security Testing" },
];

const TABS = [
  { key: "basic", label: "Basic", icon: InformationCircleIcon },
  { key: "repository", label: "Repository", icon: CodeBracketIcon },
  { key: "scanners", label: "Scanners", icon: ShieldCheckIcon },
  { key: "tags", label: "Tags", icon: TagIcon },
];

const EditProjectModal = ({ isOpen, onClose, editForm, setEditForm, tagInput, setTagInput, onAddTag, onRemoveTag, onToggleScanner, onSubmit, isPending }) => {
  const [activeTab, setActiveTab] = useState("basic");

  return (
    <Modal size="xl" isOpen={isOpen} onClose={onClose}>
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600">
            <PencilIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Edit Project</h2>
            <p className="text-gray-400">Update your project configuration</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500">
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>

      <div className="flex gap-6">
        {/* Tabs */}
        <div className="w-48 flex-shrink-0 space-y-1">
          {TABS.map((tab) => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`w-full flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                activeTab === tab.key ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "text-gray-400 hover:text-white hover:bg-gray-800/50"
              }`}>
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            <motion.div key={activeTab} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} transition={{ duration: 0.15 }}>
              <form onSubmit={onSubmit}>
                {activeTab === "basic" && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-300 mb-1.5">Name <span className="text-red-400">*</span></label>
                        <input type="text" value={editForm.name} onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" required />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1.5">Category</label>
                        <select value={editForm.category} onChange={(e) => setEditForm((p) => ({ ...p, category: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50">
                          <option value="web_application">Web Application</option><option value="api_service">API Service</option>
                          <option value="mobile_app">Mobile App</option><option value="microservice">Microservice</option>
                          <option value="library">Library</option><option value="infrastructure">Infrastructure</option><option value="other">Other</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1.5">Priority</label>
                        <select value={editForm.priority} onChange={(e) => setEditForm((p) => ({ ...p, priority: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50">
                          <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1.5">Status</label>
                        <select value={editForm.status} onChange={(e) => setEditForm((p) => ({ ...p, status: e.target.value }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50">
                          <option value="active">Active</option><option value="inactive">Inactive</option><option value="archived">Archived</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1.5">Description</label>
                      <textarea value={editForm.description} onChange={(e) => setEditForm((p) => ({ ...p, description: e.target.value }))} rows={3} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none" />
                    </div>
                  </div>
                )}

                {activeTab === "repository" && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1.5">Repository URL</label>
                      <input type="url" value={editForm.repository.url} onChange={(e) => setEditForm((p) => ({ ...p, repository: { ...p.repository, url: e.target.value } }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-300 mb-1.5">Branch</label>
                        <input type="text" value={editForm.repository.branch} onChange={(e) => setEditForm((p) => ({ ...p, repository: { ...p.repository, branch: e.target.value } }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1.5">Access Token</label>
                        <input type="password" value={editForm.repository.access_token} onChange={(e) => setEditForm((p) => ({ ...p, repository: { ...p.repository, access_token: e.target.value } }))} className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500">Leave access token empty to keep current token</p>
                  </div>
                )}

                {activeTab === "scanners" && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      {SCANNER_OPTIONS.map((scanner) => (
                        <button key={scanner.value} type="button" onClick={() => onToggleScanner(scanner.value)}
                          className={`p-3 rounded-xl border text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                            editForm.scan_config.enabled_scanners.includes(scanner.value) ? "border-cyan-500/70 bg-cyan-500/20" : "border-gray-700/50 bg-gray-800/30 hover:border-gray-600/50"
                          }`}>
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-white text-sm">{scanner.label}</span>
                            {editForm.scan_config.enabled_scanners.includes(scanner.value) && <CheckCircleIcon className="w-4 h-4 text-cyan-400" />}
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5">{scanner.description}</p>
                        </button>
                      ))}
                    </div>
                    <div className="flex items-center space-x-4 pt-2">
                      <label className="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                        <input type="checkbox" checked={editForm.scan_config.auto_scan_on_push} onChange={(e) => setEditForm((p) => ({ ...p, scan_config: { ...p.scan_config, auto_scan_on_push: e.target.checked } }))} className="rounded bg-gray-700 border-gray-600 text-cyan-500" />
                        <span>Auto-scan on push</span>
                      </label>
                      <label className="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                        <input type="checkbox" checked={editForm.scan_config.fail_on_critical} onChange={(e) => setEditForm((p) => ({ ...p, scan_config: { ...p.scan_config, fail_on_critical: e.target.checked } }))} className="rounded bg-gray-700 border-gray-600 text-cyan-500" />
                        <span>Fail on critical</span>
                      </label>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1.5">Timeout (minutes)</label>
                      <input type="number" min="5" max="180" value={editForm.scan_config.scan_timeout_minutes} onChange={(e) => setEditForm((p) => ({ ...p, scan_config: { ...p.scan_config, scan_timeout_minutes: parseInt(e.target.value) || 60 } }))} className="w-32 px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
                    </div>
                  </div>
                )}

                {activeTab === "tags" && (
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), onAddTag())} placeholder="Add tag..." className="flex-1 px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
                      <Button type="button" onClick={onAddTag}>Add</Button>
                    </div>
                    {editForm.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {editForm.tags.map((tag) => (
                          <span key={tag} className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-lg text-sm flex items-center space-x-1.5">
                            <span>{tag}</span>
                            <button type="button" onClick={() => onRemoveTag(tag)} className="text-gray-400 hover:text-white focus:outline-none"><XMarkIcon className="w-3.5 h-3.5" /></button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-700/50">
                  <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                  <Button type="submit" gradient isLoading={isPending}>{isPending ? "Saving..." : "Save Changes"}</Button>
                </div>
              </form>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </Modal>
  );
};

export default EditProjectModal;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/EditProjectModal.jsx`
Expected: 0 errors, 0 warnings

---
### Task 13: DeleteProjectModal.jsx (Enhanced)

**Files:**
- Modify: `src/components/projects/DeleteProjectModal.jsx`

**Scope:** Add animated shake, double-confirm step, character-by-character matching.

- [ ] **Step 1: Rewrite DeleteProjectModal.jsx**

```jsx
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { Button, Modal } from "../../styles/components";

const DeleteProjectModal = ({ isOpen, onClose, projectName, totalScans, deleteConfirmText, setDeleteConfirmText, onConfirm, isPending }) => {
  const [step, setStep] = useState("confirm"); // confirm | final
  const [shake, setShake] = useState(false);

  useEffect(() => {
    if (isOpen) { setStep("confirm"); setShake(true); setTimeout(() => setShake(false), 500); }
  }, [isOpen]);

  const handleFirstConfirm = () => {
    if (deleteConfirmText === "DELETE") setStep("final");
    else { setShake(true); setTimeout(() => setShake(false), 500); }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Project" size="sm">
      <div className="text-center">
        <motion.div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4"
          animate={shake ? { x: [0, -8, 8, -5, 5, 0] } : {}}
          transition={{ duration: 0.4 }}
        >
          <ExclamationTriangleIcon className="h-10 w-10 text-red-400" />
        </motion.div>

        <p className="text-gray-400 mb-4">
          Delete <span className="text-red-400 font-semibold">&quot;{projectName}&quot;</span>?
        </p>

        <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-4 mb-6 text-left">
          <p className="text-red-300 text-sm font-medium mb-2">This will permanently delete:</p>
          <ul className="text-red-200/80 text-sm space-y-1.5 ml-4">
            <li>• The project and its configuration</li>
            <li>• {totalScans} scan(s) and all findings</li>
            <li>• All webhook events and history</li>
          </ul>
        </div>

        {step === "confirm" && (
          <div className="mb-6">
            <label className="block text-sm text-gray-400 mb-2">Type <span className="text-red-400 font-mono font-bold">DELETE</span> to confirm:</label>
            <input type="text" value={deleteConfirmText} onChange={(e) => setDeleteConfirmText(e.target.value)}
              className="w-full px-4 py-3 bg-gray-800/50 border border-red-800/30 rounded-xl text-white text-center font-mono focus:outline-none focus:ring-2 focus:ring-red-500/50"
              placeholder="DELETE"
            />
            <div className="flex justify-center mt-2 space-x-0.5">
              {"DELETE".split("").map((char, i) => (
                <span key={i} className={`inline-block w-5 h-5 text-xs rounded flex items-center justify-center ${
                  deleteConfirmText[i] === char ? "bg-green-500/30 text-green-400" : deleteConfirmText[i] ? "bg-red-500/30 text-red-400" : "bg-gray-700/50 text-gray-600"
                }`}>{char}</span>
              ))}
            </div>
          </div>
        )}

        {step === "final" && (
          <div className="mb-6 p-4 bg-red-900/30 rounded-xl border border-red-500/40">
            <p className="text-red-300 text-sm font-bold">⚠️ Final confirmation required</p>
            <p className="text-red-200/70 text-xs mt-1">This action cannot be undone. Click &quot;Delete Forever&quot; again to proceed.</p>
          </div>
        )}

        <div className="flex space-x-3">
          <Button variant="ghost" onClick={() => { onClose(); setDeleteConfirmText(""); }} className="flex-1">Cancel</Button>
          {step === "confirm" ? (
            <Button variant="danger" isLoading={isPending} disabled={deleteConfirmText !== "DELETE"} onClick={handleFirstConfirm} className="flex-1">
              {deleteConfirmText === "DELETE" ? "Confirm Delete" : "Type DELETE"}
            </Button>
          ) : (
            <Button variant="danger" isLoading={isPending} onClick={() => { onConfirm(); setStep("confirm"); }} className="flex-1 animate-pulse">
              {isPending ? "Deleting..." : "Delete Forever"}
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default DeleteProjectModal;
```

- [ ] **Step 2: Verify with lint**

Run: `npx eslint src/components/projects/DeleteProjectModal.jsx`
Expected: 0 errors, 0 warnings

---
### Task 14: ProjectDetails.jsx (Orchestrator Integration)

**Files:**
- Modify: `src/components/projects/ProjectDetails.jsx`
- Remove: `src/components/projects/ScanProgressBanner.jsx`
- Remove: `src/components/projects/QuickStatsCards.jsx`
- Remove: `src/components/projects/ProjectOverviewTab.jsx`

**Scope:** Rewrite orchestrator to use new components, split-pane layout, ambient particles, all new sub-components.

- [ ] **Step 1: Rewrite ProjectDetails.jsx**

```jsx
import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheckIcon, PlayIcon, StopIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { projectsAPI, reportsAPI } from "../../services/api";
import { PageContainer, PageHeader } from "../../layouts";
import ParticleBackground from "./ParticleBackground";
import ProjectSidebar from "./ProjectSidebar";
import ScanPipeline from "./ScanPipeline";
import LiveConsole from "./LiveConsole";
import MetricsDashboard from "./MetricsDashboard";
import OverviewTab from "./OverviewTab";
import ScanHistoryTab from "./ScanHistoryTab";
import SettingsTab from "./SettingsTab";
import EditProjectModal from "./EditProjectModal";
import DeleteProjectModal from "./DeleteProjectModal";

const ProjectDetails = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [consoleExpanded, setConsoleExpanded] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "", description: "", priority: "medium", status: "active", category: "other",
    repository: { url: "", branch: "main", access_token: "" },
    scan_config: { enabled_scanners: ["sast", "secrets"], auto_scan_on_push: false, scan_timeout_minutes: 60, fail_on_critical: false },
    tags: [],
  });
  const [tagInput, setTagInput] = useState("");
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [activeScan, setActiveScan] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  const [scanCompleted, setScanCompleted] = useState(false);
  const [logLines, setLogLines] = useState([]);
  const hasShownCompletionToast = useRef(false);

  const { data: project, isLoading: projectLoading, error: projectError, refetch: refetchProject } = useQuery({
    queryKey: ["project", projectId], queryFn: () => projectsAPI.getProject(projectId), enabled: !!projectId,
  });

  const { data: scanHistory, isLoading: scanHistoryLoading, refetch: refetchScanHistory } = useQuery({
    queryKey: ["projectScans", projectId], queryFn: () => reportsAPI.getReports({ project_id: projectId, limit: 20 }), enabled: !!projectId, refetchInterval: isPolling ? 3000 : false,
  });

  const { refetch: refetchAnalytics } = useQuery({
    queryKey: ["projectAnalytics", projectId], queryFn: () => projectsAPI.getProjectAnalytics(projectId), enabled: !!projectId,
  });

  const pollScanStatus = useCallback(async () => {
    if (!activeScan?.scan_id || !isPolling) return;
    try {
      const status = await reportsAPI.getScanStatus(activeScan.scan_id);
      if (status) {
        setScanProgress(status.progress || 0);
        if (status.logs?.length) {
          setLogLines((prev) => [...prev, ...status.logs.map((l) => ({
            timestamp: l.timestamp || new Date().toLocaleTimeString(),
            level: l.level || "INFO", message: l.message || l,
          }))]);
        }
        setActiveScan((prev) => ({
          ...prev, status: status.status || prev?.status, progress: status.progress || prev?.progress,
          current_scanner: status.current_scanner || prev?.current_scanner,
          total_findings: status.total_findings, findings_by_severity: status.findings_by_severity,
        }));

        if (["completed", "failed", "cancelled"].includes(status.status)) {
          setIsPolling(false);
          if (!hasShownCompletionToast.current) {
            hasShownCompletionToast.current = true;
            if (status.status === "completed") {
              const c = (status.findings_by_severity?.critical || 0) + (status.findings_by_severity?.high || 0);
              if (c > 0) toast.error(`Scan completed with ${c} critical/high issues!`, { duration: 5000 });
              else if (status.total_findings > 0) toast.success(`Scan completed! Found ${status.total_findings} findings.`, { duration: 4000 });
              else toast.success("Scan completed! No issues found.", { duration: 4000 });
            } else if (status.status === "cancelled") toast("Scan cancelled.", { icon: "ℹ️" });
            else toast.error(status.error_message || "Scan failed.");
          }
          setScanProgress(status.status === "completed" ? 100 : status.progress || 0);
          setScanCompleted(true);
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["projectScans", projectId] });
            queryClient.invalidateQueries({ queryKey: ["project", projectId] });
            refetchProject(); refetchScanHistory(); refetchAnalytics();
          }, 1000);
        }
      }
    } catch (err) { console.error("Poll error:", err); }
  }, [activeScan?.scan_id, isPolling, projectId, queryClient, refetchAnalytics, refetchProject, refetchScanHistory]);

  useEffect(() => {
    let interval;
    if (isPolling && activeScan?.scan_id) { pollScanStatus(); interval = setInterval(pollScanStatus, 2000); }
    return () => { if (interval) clearInterval(interval); };
  }, [isPolling, activeScan?.scan_id, pollScanStatus]);

  const startScanMutation = useMutation({
    mutationFn: (d) => reportsAPI.startScan(d),
    onSuccess: (data) => {
      toast.success("Security scan started!");
      hasShownCompletionToast.current = false;
      setScanCompleted(false); setLogLines([]);
      setActiveScan({ scan_id: data.scan_id, status: data.status || "pending", project_name: data.project_name, started_at: new Date().toISOString(), current_scanner: "Initializing...", progress: 0 });
      setScanProgress(0); setIsPolling(true);
      queryClient.invalidateQueries({ queryKey: ["projectScans", projectId] });
    },
    onError: (err) => toast.error(err.message || "Failed to start scan"),
  });

  const stopScanMutation = useMutation({
    mutationFn: (id) => reportsAPI.stopScan(id),
    onSuccess: () => { toast("Scan stopped.", { icon: "ℹ️" }); setActiveScan(null); setScanProgress(0); setIsPolling(false); setLogLines([]); hasShownCompletionToast.current = false; queryClient.invalidateQueries({ queryKey: ["projectScans", projectId] }); },
    onError: (err) => toast.error(err.message || "Failed to stop scan"),
  });

  const updateProjectMutation = useMutation({
    mutationFn: (d) => projectsAPI.updateProject(projectId, d),
    onSuccess: () => { toast.success("Project updated!"); queryClient.invalidateQueries({ queryKey: ["project", projectId] }); setShowEditModal(false); },
    onError: (err) => toast.error(err.message || "Failed to update project"),
  });

  const deleteProjectMutation = useMutation({
    mutationFn: () => projectsAPI.deleteProject(projectId),
    onSuccess: () => { toast.success("Project deleted!"); queryClient.invalidateQueries({ queryKey: ["projects"] }); navigate("/projects"); },
    onError: (err) => toast.error(err.message || "Failed to delete project"),
  });

  const handleStartScan = () => {
    if (!project || activeScan) return;
    startScanMutation.mutate({ repository_url: project.repository?.url, branch: project.repository?.branch || "main", scan_types: project.scan_config?.enabled_scanners || ["sast", "secrets", "container"], project_id: projectId });
  };

  const handleStopScan = () => {
    if (activeScan?.scan_id) stopScanMutation.mutate(activeScan.scan_id);
  };

  const openEditModal = () => {
    if (!project) return;
    setEditForm({ name: project.name || "", description: project.description || "", priority: project.priority || "medium", status: project.status || "active", category: project.category || "other",
      repository: { url: project.repository?.url || "", branch: project.repository?.branch || "main", access_token: project.repository?.access_token || "" },
      scan_config: { enabled_scanners: project.scan_config?.enabled_scanners || ["sast", "secrets"], auto_scan_on_push: project.scan_config?.auto_scan_on_push || false, scan_timeout_minutes: project.scan_config?.scan_timeout_minutes || 60, fail_on_critical: project.scan_config?.fail_on_critical || false },
      tags: project.tags || [] });
    setTagInput(""); setShowEditModal(true);
  };

  useEffect(() => {
    const handler = () => setShowDeleteModal(true);
    document.addEventListener("open-delete-modal", handler);
    return () => document.removeEventListener("open-delete-modal", handler);
  }, []);

  if (projectLoading) return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading project...</p>
        </div>
      </div>
    </div>
  );

  if (projectError || !project) return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <ShieldCheckIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Project Not Found</h2>
          <p className="text-gray-400 mb-6">The project doesn't exist or you don't have access.</p>
          <button onClick={() => navigate("/projects")} className="px-6 py-3 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg transition-all">Back to Projects</button>
        </div>
      </div>
    </div>
  );

  const stats = project.stats || {};
  const liveFindings = scanCompleted && activeScan?.findings_by_severity ? activeScan.findings_by_severity : null;
  const vulnCounts = { critical: liveFindings?.critical ?? stats.critical_vulnerabilities ?? 0, high: liveFindings?.high ?? stats.high_vulnerabilities ?? 0, medium: liveFindings?.medium ?? stats.medium_vulnerabilities ?? 0, low: liveFindings?.low ?? stats.low_vulnerabilities ?? 0 };
  const totalVulns = vulnCounts.critical + vulnCounts.high + vulnCounts.medium + vulnCounts.low;
  const liveSecurityScore = liveFindings ? Math.max(0, 100 - (vulnCounts.critical * 25 + vulnCounts.high * 15 + vulnCounts.medium * 5 + vulnCounts.low * 1)) : null;
  const runningScans = scanHistory?.reports?.filter((r) => (r.status === "running" || r.status === "pending") && r.scan_id !== activeScan?.scan_id) || [];
  const isScanActive = !scanCompleted && ((activeScan && !["completed", "failed", "cancelled"].includes(activeScan.status)) || runningScans.length > 0);

  const tabs = [
    { key: "overview", label: "Overview", icon: ShieldCheckIcon },
    { key: "scans", label: "Scan History", icon: PlayIcon },
    { key: "settings", label: "Settings", icon: StopIcon },
  ];

  return (
    <PageContainer>
      <ParticleBackground isScanActive={isScanActive} />
      <div className="max-w-7xl mx-auto relative z-10">
        <PageHeader title={project.name} description={project.description || "No description"} icon={ShieldCheckIcon} breadcrumb={["Projects", project.name]} actions={
          <div className="flex items-center space-x-3">
            {isScanActive ? (
              <button onClick={handleStopScan} disabled={stopScanMutation.isPending} className="px-5 py-2.5 bg-gradient-to-r from-red-500 to-rose-600 text-white font-medium rounded-xl hover:from-red-600 hover:to-rose-700 disabled:opacity-50 flex items-center space-x-2 animate-pulse focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500">
                <StopIcon className="h-4 w-4" />
                <span>{stopScanMutation.isPending ? "Stopping..." : "Stop Scan"}</span>
              </button>
            ) : (
              <button onClick={handleStartScan} disabled={startScanMutation.isPending} className="px-5 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 flex items-center space-x-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-green-500">
                <PlayIcon className="h-4 w-4" />
                <span>{startScanMutation.isPending ? "Starting..." : "Start Scan"}</span>
              </button>
            )}
          </div>
        } />

        <div className="flex gap-6 mt-6">
          <ProjectSidebar project={project} vulnCounts={vulnCounts} totalVulns={totalVulns} securityScore={liveSecurityScore ?? stats.security_score ?? 0} isScanActive={isScanActive} onEdit={openEditModal} onDelete={() => setShowDeleteModal(true)} />

          <div className="flex-1 min-w-0 space-y-6">
            {activeScan && (
              <>
                <ScanPipeline scanProgress={scanProgress} activeScan={activeScan} projectName={project.name} />
                <LiveConsole logLines={logLines} isExpanded={consoleExpanded} onToggle={() => setConsoleExpanded(!consoleExpanded)} />
              </>
            )}

            <MetricsDashboard stats={stats} vulnCounts={vulnCounts} totalVulns={totalVulns} liveSecurityScore={liveSecurityScore} scanCompleted={scanCompleted} lastScanDate={stats.last_scan_date} />

            <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl overflow-hidden">
              <div className="flex border-b border-gray-700/50">
                {tabs.map((tab) => (
                  <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center space-x-2 px-5 py-3.5 text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                      activeTab === tab.key ? "text-cyan-400 border-b-2 border-cyan-400" : "text-gray-400 hover:text-white"
                    }`}>
                    <tab.icon className="h-4 w-4" />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
              <div className="p-6">
                {activeTab === "overview" && <OverviewTab project={project} vulnCounts={vulnCounts} events={[]} />}
                {activeTab === "scans" && <ScanHistoryTab scanHistory={scanHistory} scanHistoryLoading={scanHistoryLoading} onStartScan={handleStartScan} isStarting={startScanMutation.isPending} />}
                {activeTab === "settings" && <SettingsTab />}
              </div>
            </div>
          </div>
        </div>
      </div>

      <EditProjectModal isOpen={showEditModal} onClose={() => setShowEditModal(false)} editForm={editForm} setEditForm={setEditForm} tagInput={tagInput} setTagInput={setTagInput} onAddTag={() => { if (tagInput.trim() && !editForm.tags.includes(tagInput.trim())) { setEditForm((p) => ({ ...p, tags: [...p.tags, tagInput.trim()] })); setTagInput(""); } }} onRemoveTag={(tag) => setEditForm((p) => ({ ...p, tags: p.tags.filter((t) => t !== tag) }))} onToggleScanner={(scanner) => setEditForm((p) => ({ ...p, scan_config: { ...p.scan_config, enabled_scanners: p.scan_config.enabled_scanners.includes(scanner) ? p.scan_config.enabled_scanners.filter((s) => s !== scanner) : [...p.scan_config.enabled_scanners, scanner] } }))} onSubmit={(e) => { e.preventDefault(); updateProjectMutation.mutate(editForm); }} isPending={updateProjectMutation.isPending} />

      <DeleteProjectModal isOpen={showDeleteModal} onClose={() => { setShowDeleteModal(false); setDeleteConfirmText(""); }} projectName={project.name} totalScans={stats.total_scans || 0} deleteConfirmText={deleteConfirmText} setDeleteConfirmText={setDeleteConfirmText} onConfirm={() => { deleteProjectMutation.mutate(); setShowDeleteModal(false); setDeleteConfirmText(""); }} isPending={deleteProjectMutation.isPending} />
    </PageContainer>
  );
};

export default ProjectDetails;
```

- [ ] **Step 2: Remove old files**

Run:
```bash
Remove-Item -LiteralPath "src/components/projects/ScanProgressBanner.jsx"
Remove-Item -LiteralPath "src/components/projects/QuickStatsCards.jsx"
Remove-Item -LiteralPath "src/components/projects/ProjectOverviewTab.jsx"
```

- [ ] **Step 3: Verify with lint**

Run: `npx eslint src/components/projects/`
Expected: 0 errors, 0 warnings

---
### Task 15: Update index.js Exports

**Files:**
- Modify: `src/components/projects/index.js`

- [ ] **Step 1: Update exports**

Replace the current `index.js` content with:

```js
export { default as ProjectList } from "./ProjectList";
export { default as ProjectManagement } from "./ProjectManagement";
export { default as ProjectDetails } from "./ProjectDetails";
export { default as ProjectCard } from "./ProjectCard";
export { default as ProjectRow } from "./ProjectRow";
export { default as ProjectForm } from "./ProjectForm";
export { default as ProjectFilters } from "./ProjectFilters";
export { default as ProjectGrid } from "./ProjectGrid";
export { default as ProjectStatsBar } from "./ProjectStatsBar";
export { default as ProjectDeleteDialog } from "./ProjectDeleteDialog";
export { default as ProjectSidebar } from "./ProjectSidebar";
export { default as ScanPipeline } from "./ScanPipeline";
export { default as LiveConsole } from "./LiveConsole";
export { default as MetricCard } from "./MetricCard";
export { default as MetricsDashboard } from "./MetricsDashboard";
export { default as SecurityRadar } from "./SecurityRadar";
export { default as VulnerabilityMatrix } from "./VulnerabilityMatrix";
export { default as ActivityTimeline } from "./ActivityTimeline";
export { default as OverviewTab } from "./OverviewTab";
export { default as ScanHistoryTab } from "./ScanHistoryTab";
export { default as SettingsTab } from "./SettingsTab";
export { default as EditProjectModal } from "./EditProjectModal";
export { default as DeleteProjectModal } from "./DeleteProjectModal";
export { default as SecurityScoreGlobe } from "./SecurityScoreGlobe";
```

- [ ] **Step 2: Final lint check**

Run: `npx eslint src/components/projects/`
Expected: 0 errors, 0 warnings

---
## Self-Review Checklist

1. **Spec coverage:** Every section from the spec (Layout, Particles, Pipeline, Globe, Metrics, Radar, Matrix, Timeline, Scan History, Settings, Modals, Animations) has a corresponding task with implementation code.
2. **Placeholder scan:** No "TBD", "TODO", or vague steps. Every step contains full code or exact commands.
3. **Type consistency:** All function signatures match across files. `MetricCard` consumes `icon: Component, label, value, trend, color, formatter` — same in `MetricsDashboard` call. `ProjectSidebar` consumes `project, vulnCounts, totalVulns, securityScore, isScanActive, onEdit, onDelete` — same in `ProjectDetails` call.
4. **No references to removed components:** `ScanProgressBanner`, `QuickStatsCards`, `ProjectOverviewTab` are removed in Task 14 and nowhere referenced in new code.
