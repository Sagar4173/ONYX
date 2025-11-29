import React, { useState, useEffect } from "react";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  EnvelopeIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";
import { authAPI } from "../../services/api";

/**
 * EmailVerification Component
 * Handles email verification after user clicks the verification link
 * Shows loading, success, or error states
 */
export const EmailVerification = ({ token, onSuccess, onError }) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [email, setEmail] = useState("");
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [alreadyVerified, setAlreadyVerified] = useState(false);
  const { verifyEmail: verifyEmailContext } = useAuth();

  useEffect(() => {
    if (token) {
      handleVerifyEmail(token);
    }
  }, [token]);

  const handleVerifyEmail = async (verificationToken) => {
    setIsVerifying(true);
    try {
      // Call the API directly without going through context to avoid auth issues
      const response = await authAPI.verifyEmail(verificationToken);
      setVerificationStatus("success");
      // Don't show toast here - the success component will handle the message
      onSuccess && onSuccess();
    } catch (error) {
      setVerificationStatus("error");

      // Check if it's an "already verified" error
      const errorMsg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        "Email verification failed";

      if (errorMsg.toLowerCase().includes("already verified")) {
        setVerificationStatus("success");
        // Don't show toast - success component will handle it
        onSuccess && onSuccess();
      } else {
        setErrorMessage(errorMsg);
        console.error("Email verification error:", errorMsg);
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const resendVerification = async () => {
    if (!email || !email.includes("@")) {
      toast.error("Please enter a valid email address");
      return;
    }

    setIsResending(true);
    setAlreadyVerified(false);
    try {
      const response = await authAPI.resendVerificationEmail(email);
      // Check if already verified
      if (response.message?.toLowerCase().includes("already verified")) {
        setAlreadyVerified(true);
        toast.success("Your email is already verified! You can log in now.");
      } else {
        setResendSuccess(true);
        toast.success("Verification email sent! Please check your inbox.");
      }
    } catch (error) {
      const errorMsg =
        error.response?.data?.detail || "Failed to resend verification email";
      toast.error(errorMsg);
    } finally {
      setIsResending(false);
    }
  };

  // Loading State
  if (isVerifying) {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden rounded-2xl">
          <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-full blur-3xl animate-pulse" />
        </div>

        {/* Content */}
        <div className="relative">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
            <ArrowPathIcon className="h-8 w-8 text-white animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Verifying Email
          </h2>
          <p className="text-gray-400">
            Please wait while we verify your email address...
          </p>
        </div>
      </div>
    );
  }

  // Success State
  if (verificationStatus === "success") {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden rounded-2xl">
          <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-green-500/20 via-emerald-500/20 to-teal-500/20 rounded-full blur-3xl animate-pulse" />
        </div>

        {/* Content */}
        <div className="relative">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl mb-4 animate-bounce">
            <CheckCircleIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Email Verified Successfully!
          </h2>
          <p className="text-gray-400 mb-6">
            Your account has been verified. You can now log in to access all
            features.
          </p>
          <button
            onClick={onSuccess}
            className="w-full py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/25"
          >
            Continue to Login
          </button>
        </div>
      </div>
    );
  }

  // Error State
  if (verificationStatus === "error") {
    // Show "Already Verified" state - completely different UI
    if (alreadyVerified) {
      return (
        <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
          {/* Animated Background - Green for success */}
          <div className="absolute inset-0 overflow-hidden rounded-2xl">
            <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-green-500/20 via-emerald-500/20 to-teal-500/20 rounded-full blur-3xl animate-pulse" />
          </div>

          {/* Content */}
          <div className="relative">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl mb-4">
              <CheckCircleIcon className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Already Verified!
            </h2>
            <p className="text-gray-400 mb-6">
              Your email <span className="text-white font-medium">{email}</span>{" "}
              is already verified. You can log in to your account now.
            </p>
            <button
              onClick={onError}
              className="w-full py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/25"
            >
              Go to Login
            </button>
          </div>
        </div>
      );
    }

    // Show normal error state
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden rounded-2xl">
          <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-red-500/20 via-orange-500/20 to-yellow-500/20 rounded-full blur-3xl animate-pulse" />
        </div>

        {/* Content */}
        <div className="relative">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-red-500 to-pink-600 rounded-2xl mb-4">
            <ExclamationTriangleIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Verification Failed
          </h2>
          <p className="text-gray-400 mb-4">
            {errorMessage || "The verification link is invalid or has expired."}
          </p>

          {resendSuccess ? (
            <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-center gap-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="font-semibold text-green-400">
                  Email Sent!
                </span>
              </div>
              <p className="text-sm text-gray-300">
                We've sent a new verification email to{" "}
                <span className="text-white font-medium">{email}</span>
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Please check your inbox and spam folder.
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Enter your email to receive a new verification link:
              </p>

              {/* Email Input */}
              <div className="relative mb-4">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  className="w-full pl-10 pr-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyDown={(e) => e.key === "Enter" && resendVerification()}
                />
              </div>

              <button
                onClick={resendVerification}
                disabled={isResending || !email}
                className={`w-full py-3 px-4 font-medium rounded-xl transition-all duration-300 shadow-lg flex items-center justify-center
                  ${
                    isResending || !email
                      ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 transform hover:scale-105 hover:shadow-blue-500/25"
                  }`}
              >
                {isResending ? (
                  <>
                    <ArrowPathIcon className="h-5 w-5 animate-spin mr-2" />
                    Sending...
                  </>
                ) : (
                  "Resend Verification Email"
                )}
              </button>
            </>
          )}

          <button
            onClick={onError}
            className="mt-4 text-gray-400 hover:text-white transition-colors duration-300 text-sm"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return null;
};
