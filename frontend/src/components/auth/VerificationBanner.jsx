/**
 * Email Verification Banner
 * Shows a persistent banner for unverified users prompting them to verify their email
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ExclamationTriangleIcon,
  EnvelopeIcon,
  XMarkIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";

export const VerificationBanner = () => {
  const { user, resendVerificationEmail } = useAuth();
  const [isResending, setIsResending] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  // Don't show if user is verified
  if (!user || user.is_email_verified) {
    return null;
  }

  const handleResendEmail = async () => {
    if (isResending) return;

    setIsResending(true);
    try {
      await resendVerificationEmail(user.email);
      setEmailSent(true);
      toast.success("Verification email sent! Check your inbox.");
    } catch (error) {
      toast.error("Failed to send verification email. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <AnimatePresence>
      {!dismissed && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          <div className="bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border-b border-amber-500/20">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0 p-2 bg-amber-500/20 rounded-lg">
              <ExclamationTriangleIcon className="h-5 w-5 text-amber-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-amber-200">Email not verified</p>
              <p className="text-xs text-amber-300/70 truncate">
                Verify your email ({user.email}) to access all features
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {emailSent ? (
              <div className="flex items-center gap-2 text-emerald-400 text-sm">
                <CheckCircleIcon className="h-4 w-4" />
                <span>Email sent!</span>
              </div>
            ) : (
              <button
                onClick={handleResendEmail}
                disabled={isResending}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-amber-900 bg-amber-400 hover:bg-amber-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isResending ? (
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                ) : (
                  <EnvelopeIcon className="h-4 w-4" />
                )}
                {isResending ? "Sending..." : "Resend Email"}
              </button>
            )}

            <button
              onClick={() => setDismissed(true)}
              className="p-1.5 text-amber-400/60 hover:text-amber-400 hover:bg-amber-500/20 rounded-lg transition-colors"
              title="Dismiss for now"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
      </div>
    </motion.div>
      )}
    </AnimatePresence>
  );
};

export default VerificationBanner;
