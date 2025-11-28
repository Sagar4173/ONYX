import React from "react";
import { EnvelopeIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";

/**
 * RegistrationSuccess Component
 * Success message displayed after user registration
 * Shows email sent confirmation and provides options to resend or return to login
 */
export const RegistrationSuccess = ({
  email,
  onSwitchToLogin,
  onResendVerification,
}) => {
  const handleResendEmail = async () => {
    try {
      await onResendVerification();
      toast.success("Verification email resent! Please check your inbox.");
    } catch (error) {
      toast.error("Failed to resend verification email");
    }
  };

  return (
    <div className="relative min-h-[500px] p-8">
      {/* Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-green-500/20 via-emerald-500/20 to-teal-500/20 rounded-full blur-3xl animate-pulse" />
        <div
          className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-blue-500/20 via-cyan-500/20 to-teal-500/20 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "1s" }}
        />
      </div>

      {/* Content */}
      <div className="relative text-center">
        {/* Success Icon */}
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full mb-6 animate-bounce">
          <CheckCircleIcon className="h-10 w-10 text-white" />
        </div>

        {/* Title */}
        <h2 className="text-3xl font-bold text-white mb-3 bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
          Registration Successful!
        </h2>

        {/* Description */}
        <p className="text-gray-300 mb-2">
          Your account has been created successfully.
        </p>
        <p className="text-gray-400 mb-6 text-sm">
          We've sent a verification email to:
        </p>

        {/* Email Display */}
        <div className="flex items-center justify-center gap-2 bg-gray-800/50 border border-gray-700/50 rounded-xl px-4 py-3 mb-6">
          <EnvelopeIcon className="h-5 w-5 text-green-400" />
          <span className="text-white font-medium">{email}</span>
        </div>

        {/* Info Box */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-6">
          <p className="text-sm text-gray-300">
            <span className="font-semibold text-blue-400">Important:</span>{" "}
            Please check your email and click the verification link to activate
            your account.
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Check your spam folder if you don't see the email within a few
            minutes.
          </p>
        </div>

        {/* Resend Button */}
        <button
          onClick={handleResendEmail}
          className="w-full mb-3 py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/25"
        >
          Resend Verification Email
        </button>

        {/* Back to Login */}
        <button
          onClick={onSwitchToLogin}
          className="text-gray-400 hover:text-white transition-colors duration-300 text-sm"
        >
          Return to Login
        </button>
      </div>
    </div>
  );
};
