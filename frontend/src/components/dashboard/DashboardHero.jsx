import { motion } from "framer-motion";
import SecurityScoreGlobe from "../projects/SecurityScoreGlobe";
import { AnimatedCounter } from "../../styles/components";

const DashboardHero = ({ securityScore, scoreTrend }) => {
  const trendColor =
    scoreTrend > 0 ? "text-emerald-400" : scoreTrend < 0 ? "text-red-400" : "text-gray-400";
  const trendArrow = scoreTrend > 0 ? "↑" : scoreTrend < 0 ? "↓" : "→";

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-gray-800/40 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 mb-6"
    >
      <div className="flex items-center gap-8">
        <div className="flex-shrink-0">
          <SecurityScoreGlobe score={securityScore || 0} isScanActive={false} />
        </div>
        <div className="flex-1">
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1 font-medium">
            Organization Security Posture
          </p>
          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-bold text-white">
              {securityScore != null ? <AnimatedCounter value={securityScore} /> : "—"}
            </span>
            {scoreTrend != null && securityScore != null && (
              <span className={`text-lg font-medium ${trendColor}`}>
                {trendArrow} {Math.abs(scoreTrend)}%
              </span>
            )}
          </div>
          <p className="text-gray-500 text-xs mt-1">
            Last updated: {new Date().toLocaleTimeString()}
          </p>
        </div>
      </div>
    </motion.div>
  );
};

export default DashboardHero;
