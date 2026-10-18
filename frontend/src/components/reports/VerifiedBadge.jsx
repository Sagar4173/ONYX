import { CheckIcon } from "@heroicons/react/24/outline";
import { motion, useReducedMotion } from "framer-motion";

export function VerifiedBadge({ verification, className = "" }) {
  const reduceMotion = useReducedMotion();
  const total = verification?.total_findings;
  return (
    <div
      role="status"
      className={`relative overflow-hidden rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-500/10 via-transparent to-violet-500/10 p-4 ${className}`}
    >
      <motion.div
        className="flex items-center gap-3"
        initial={reduceMotion ? false : { opacity: 0, y: 6, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
      >
        <motion.span
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-violet-500 text-white shadow-lg shadow-cyan-500/30"
          initial={reduceMotion ? false : { scale: 0.4 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.05 }}
        >
          <CheckIcon className="h-6 w-6" />
        </motion.span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white">
            Verified — re-scan no longer detects this finding
          </p>
          <p className="text-xs text-gray-400">
            {total != null
              ? `The fix branch was re-scanned; total findings dropped to ${total}.`
              : "The fix branch was re-scanned and the original check now passes."}
          </p>
        </div>
      </motion.div>
      {!reduceMotion && (
        <motion.span
          aria-hidden="true"
          data-testid="verified-sweep"
          className="pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          initial={{ x: "0%" }}
          animate={{ x: "400%" }}
          transition={{ duration: 1.1, ease: "easeInOut", delay: 0.2 }}
        />
      )}
    </div>
  );
}
