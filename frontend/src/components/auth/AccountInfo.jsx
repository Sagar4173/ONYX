import { motion } from "framer-motion";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EnvelopeIcon,
  ChevronRightIcon,
  ShieldCheckIcon,
  CheckBadgeIcon,
  StarIcon,
  ClockIcon,
  CalendarIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";

const staggerVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, duration: 0.3 },
  }),
};

export const AccountInfo = ({ user, handleResendVerification, formatDate, formatDateTime }) => {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      className="space-y-5"
      variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
    >
      <motion.div custom={0} variants={staggerVariants}>
        <div
          className={`relative overflow-hidden rounded-2xl p-6 border transition-all duration-500 ${
            user?.is_email_verified
              ? "bg-gradient-to-br from-emerald-500/10 via-green-500/5 to-teal-500/10 border-emerald-500/20"
              : "bg-gradient-to-br from-amber-500/10 via-orange-500/5 to-yellow-500/10 border-amber-500/20"
          }`}
        >
        <div className="absolute inset-0 opacity-30">
          <div
            className={`absolute inset-0 ${user?.is_email_verified ? "bg-[radial-gradient(circle_at_50%_50%,rgba(16,185,129,0.1),transparent_70%)]" : "bg-[radial-gradient(circle_at_50%_50%,rgba(245,158,11,0.1),transparent_70%)]"}`}
          />
        </div>
        <div className="relative flex items-start gap-4">
          <div
            className={`p-3.5 rounded-2xl ${user?.is_email_verified ? "bg-gradient-to-br from-emerald-500/30 to-green-500/20" : "bg-gradient-to-br from-amber-500/30 to-orange-500/20"} shadow-lg`}
          >
            {user?.is_email_verified ? (
              <CheckCircleIcon className="h-8 w-8 text-emerald-400" />
            ) : (
              <ExclamationTriangleIcon className="h-8 w-8 text-amber-400 animate-pulse" />
            )}
          </div>
          <div className="flex-1">
            <h4 className="text-white font-bold text-lg mb-1 flex items-center gap-2">
              Email Verification
              {user?.is_email_verified && (
                <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                  Complete
                </span>
              )}
            </h4>
            <p className="text-gray-400 text-sm leading-relaxed">
              {user?.is_email_verified
                ? "Your email address has been verified."
                : "Verify your email to unlock all features, improve account security, and receive important notifications."}
            </p>
            {!user?.is_email_verified && (
              <button
                onClick={handleResendVerification}
                className="mt-4 px-5 py-2.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 text-amber-300 text-sm font-semibold rounded-xl border border-amber-500/30 hover:border-amber-500/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-all duration-300 flex items-center gap-2 group"
              >
                <EnvelopeIcon className="h-4 w-4 group-hover:scale-110 transition-transform" />
                Resend Verification Email
                <ChevronRightIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </motion.div>

      <motion.div custom={1} variants={staggerVariants}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="group bg-gray-800/30 border border-gray-700/50 hover:border-cyan-500/30 rounded-2xl p-5 hover:bg-gray-800/50 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2.5 bg-gradient-to-br from-cyan-500/20 to-violet-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
              <ShieldCheckIcon className="h-6 w-6 text-cyan-400" />
            </div>
            <h4 className="text-white font-semibold text-lg">Account Status</h4>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-900/40 rounded-xl">
              <span className="text-gray-400 text-sm flex items-center gap-2">
                <CheckBadgeIcon className="h-4 w-4 text-emerald-400" /> Status
              </span>
              <span className="px-3 py-1.5 bg-gradient-to-r from-emerald-500/20 to-green-500/20 text-emerald-400 text-xs font-semibold rounded-lg border border-emerald-500/30 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />{" "}
                {user?.status || "Active"}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-900/40 rounded-xl">
              <span className="text-gray-400 text-sm flex items-center gap-2">
                <StarIcon className="h-4 w-4 text-cyan-400" /> Role
              </span>
              <span className="px-3 py-1.5 bg-gradient-to-r from-cyan-500/20 to-violet-500/20 text-cyan-400 text-xs font-semibold rounded-lg border border-cyan-500/30 capitalize">
                {user?.role || "User"}
              </span>
            </div>
          </div>
        </div>

        <div className="group bg-gray-800/30 border border-gray-700/50 hover:border-violet-500/30 rounded-2xl p-5 hover:bg-gray-800/50 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/5">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2.5 bg-gradient-to-br from-violet-500/20 to-cyan-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
              <ClockIcon className="h-6 w-6 text-violet-400" />
            </div>
            <h4 className="text-white font-semibold text-lg">Activity</h4>
          </div>
          <div className="space-y-4">
            <div className="p-3 bg-gray-900/40 rounded-xl">
              <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                <CalendarIcon className="h-3.5 w-3.5" /> Member Since
              </div>
              <span className="text-white text-sm font-medium">{formatDate(user?.created_at)}</span>
            </div>
            <div className="p-3 bg-gray-900/40 rounded-xl">
              <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                <ArrowPathIcon className="h-3.5 w-3.5" /> Last Login
              </div>
              <span className="text-white text-sm font-medium">
                {formatDateTime(user?.last_login)}
              </span>
            </div>
          </div>
        </div>
      </div>
      </motion.div>
    </motion.div>
  );
};
