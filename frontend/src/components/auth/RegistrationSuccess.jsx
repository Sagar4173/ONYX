import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { EnvelopeIcon, CheckCircleIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";

/**
 * RegistrationSuccess Component
 * Success message displayed after user registration
 * Shows email sent confirmation and provides options to resend or return to login
 */
export const RegistrationSuccess = ({ email, onSwitchToLogin, onResendVerification }) => {
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);

  // Countdown timer effect
  useEffect(() => {
    if (cooldownSeconds > 0) {
      const timer = setTimeout(() => {
        setCooldownSeconds(cooldownSeconds - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldownSeconds]);

  const handleResendEmail = async () => {
    if (isResending || cooldownSeconds > 0) return;

    setIsResending(true);
    setResendSuccess(false);

    try {
      await onResendVerification(email);
      setResendSuccess(true);
      setCooldownSeconds(60); // 60 second cooldown before next resend
      toast.success("Verification email resent! Please check your inbox.");
    } catch (error) {
      toast.error("Failed to resend verification email");
    } finally {
      setIsResending(false);
    }
  };

  const getButtonContent = () => {
    if (isResending) {
      return (
        <>
          <ArrowPathIcon className="h-5 w-5 animate-spin mr-2" />
          Sending...
        </>
      );
    }
    if (cooldownSeconds > 0) {
      return `Resend available in ${cooldownSeconds}s`;
    }
    if (resendSuccess) {
      return (
        <>
          <CheckCircleIcon className="h-5 w-5 mr-2" />
          Email Sent! Click to Resend Again
        </>
      );
    }
    return "Resend Verification Email";
  };

  return (
    <motion.div
      className="relative min-h-[500px] p-8"
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: { transition: { staggerChildren: 0.06 } },
      }}
    >
      <motion.div
        variants={{
          hidden: { opacity: 0, y: 10 },
          visible: { opacity: 1, y: 0 },
        }}
        className="relative text-center"
      >
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
          className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-full mb-6 animate-bounce"
        >
          <CheckCircleIcon className="h-10 w-10 text-white" />
        </motion.div>

        <motion.h2
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
          className="text-3xl font-bold text-white mb-3 bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent"
        >
          Registration Successful!
        </motion.h2>

        <motion.p
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
          className="text-gray-300 mb-2"
        >
          Your account has been created successfully.
        </motion.p>
        <motion.p
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
          className="text-gray-400 mb-6 text-sm"
        >
          We've sent a verification email to:
        </motion.p>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
          className="flex items-center justify-center gap-2 bg-gray-800/50 border border-gray-700/50 rounded-xl px-4 py-3 mb-6"
        >
          <EnvelopeIcon className="h-5 w-5 text-cyan-400" />
          <span className="text-white font-medium">{email}</span>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
          className={`${
            resendSuccess
              ? "bg-cyan-500/10 border-cyan-500/30"
              : "bg-violet-500/10 border-violet-500/30"
          } border rounded-xl p-4 mb-6 transition-colors duration-300`}
        >
          {resendSuccess ? (
            <>
              <div className="flex items-center justify-center gap-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-cyan-400" />
                <span className="font-semibold text-cyan-400">Email Resent Successfully!</span>
              </div>
              <p className="text-sm text-gray-300">
                We've sent another verification email to your inbox.
              </p>
              <p className="text-xs text-gray-400 mt-2">Please check your inbox and spam folder.</p>
            </>
          ) : (
            <>
              <p className="text-sm text-gray-300">
                <span className="font-semibold text-violet-400">Important:</span> Please check your
                email and click the verification link to activate your account.
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Check your spam folder if you don't see the email within a few minutes.
              </p>
            </>
          )}
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <button
            onClick={handleResendEmail}
            disabled={isResending || cooldownSeconds > 0}
            className={`w-full mb-3 py-3 px-4 font-medium rounded-xl transition-all duration-300 shadow-lg flex items-center justify-center
              ${
                isResending || cooldownSeconds > 0
                  ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                  : resendSuccess
                    ? "bg-gradient-to-r from-violet-500 to-violet-600 text-white hover:from-violet-600 hover:to-violet-700 transform hover:scale-105 hover:shadow-violet-500/25"
                    : "bg-gradient-to-r from-cyan-500 to-violet-600 text-white hover:from-cyan-600 hover:to-violet-700 transform hover:scale-105 hover:shadow-cyan-500/25"
              }`}
          >
            {getButtonContent()}
          </button>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <button
            onClick={onSwitchToLogin}
            className="text-gray-400 hover:text-white transition-colors duration-300 text-sm"
          >
            Return to Login
          </button>
        </motion.div>
      </div>
    </div>
  );
};
