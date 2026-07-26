import { useState } from "react";
import { EnvelopeIcon, ArrowRightIcon } from "@heroicons/react/24/outline";
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
    <div className="p-10">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Reset Password</h2>
        <p className="text-sm text-gray-400">Enter your email to receive reset instructions</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
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
            aria-required="true"
            autoComplete="email"
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          gradient
          rightIcon={isLoading ? undefined : <ArrowRightIcon className="w-5 h-5" />}
          isLoading={isLoading}
          className="w-full"
        >
          Send Reset Link
        </Button>
      </form>

      <div className="mt-8 text-center">
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text hover:from-cyan-300 hover:to-violet-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
        >
          ← Back to sign in
        </button>
      </div>
    </div>
  );
};
