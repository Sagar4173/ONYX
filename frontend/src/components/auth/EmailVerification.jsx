import React, { useState, useEffect } from "react";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
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
  const { verifyEmail: verifyEmailContext } = useAuth();

  useEffect(() => {
    if (token) {
      handleVerifyEmail(token);
    }
  }, [token]);

  const handleVerifyEmail = async (verificationToken) => {
    setIsVerifying(true);
    try {
      // Use the context function which handles user state updates
      const response = await verifyEmailContext(verificationToken);
      setVerificationStatus("success");
      toast.success("Email verified successfully!");
      onSuccess && onSuccess();
    } catch (error) {
      setVerificationStatus("error");

      // Check if it's an "already verified" error
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Email verification failed";

      if (errorMessage.includes("already verified")) {
        setVerificationStatus("success");
        toast.success("Email is already verified! Your account is active.");
        onSuccess && onSuccess();
      } else {
        toast.error(errorMessage);
        onError && onError(errorMessage);
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const resendVerification = async () => {
    try {
      await authAPI.resendVerificationEmail();
      toast.success("Verification email sent! Please check your inbox.");
    } catch (error) {
      toast.error("Failed to resend verification email");
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
            Email Verified!
          </h2>
          <p className="text-gray-400 mb-6">
            Your account has been successfully verified. You can now access all
            features.
          </p>
          <button
            onClick={onSuccess}
            className="w-full py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/25"
          >
            Continue to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Error State
  if (verificationStatus === "error") {
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
          <p className="text-gray-400 mb-6">
            The verification link is invalid or has expired.
          </p>
          <button
            onClick={resendVerification}
            className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-blue-500/25"
          >
            Resend Verification Email
          </button>
        </div>
      </div>
    );
  }

  return null;
};
