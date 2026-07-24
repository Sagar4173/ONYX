/**
 * Enhanced Forgot Password Form Component
 */
import { useState } from "react";
import {
  EnvelopeIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  } from "@heroicons/react/24/outline";
import { KeyIcon as KeySolid } from "@heroicons/react/24/solid";
import { Button, Input } from "../../styles/components";
import { useAuth } from "./AuthContext";

export const ForgotPasswordForm = ({ onSuccess, onSwitchToLogin }) => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { requestPasswordReset } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await requestPasswordReset(email);
      onSuccess && onSuccess(email);
    } catch (error) {
      // Error is handled in the context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-gradient-to-br from-gray-800/90 to-gray-900/90 backdrop-blur-2xl rounded-3xl p-8 border border-gray-700/50 shadow-2xl relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" />
      <div
        className="absolute bottom-0 left-0 w-64 h-64 bg-violet-500/10 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: "1s" }}
      />

      <div className="relative z-10">
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-cyan-500 via-violet-500 to-cyan-500 rounded-3xl mb-4 shadow-lg animate-bounce"
            style={{ animationDuration: "3s" }}
          >
            <KeySolid className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent mb-2">
            Reset Password
          </h2>
          <p className="text-gray-400">
            Enter your email to receive reset instructions
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="group">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <EnvelopeIcon className="w-4 h-4 text-cyan-400" />
              Email Address
            </label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
            />
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            gradient
            rightIcon={<ArrowRightIcon className="w-5 h-5" />}
            isLoading={isLoading}
            className="w-full"
          >
            Send Reset Link
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Button
            variant="ghost"
            onClick={onSwitchToLogin}
            className="!bg-none p-0 text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text font-semibold hover:from-cyan-300 hover:to-violet-300"
          >
            ← Back to sign in
          </Button>
        </div>
      </div>
    </div>
  );
};
