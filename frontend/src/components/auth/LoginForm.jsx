/**
 * Enhanced Login Form Component
 * Modern UI with animations and glassmorphism
 * Supports Two-Factor Authentication flow
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  EnvelopeIcon,
  LockClosedIcon,
  UserIcon,
  KeyIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  DevicePhoneMobileIcon,
} from "@heroicons/react/24/outline";
import { ShieldCheckIcon as ShieldCheckSolid } from "@heroicons/react/24/solid";
import { Button, Input } from "../ui/StyleComponents";
import { useAuth } from "./AuthContext";
import toast from "react-hot-toast";

export const LoginForm = ({ onSuccess, onSwitchToRegister, onSwitchToForgotPassword }) => {
  const [formData, setFormData] = useState({
    username_or_email: "",
    password: "",
    remember_me: false,
    two_factor_code: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [twoFAEmail, setTwoFAEmail] = useState("");
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const result = await login(formData);

      // Check if 2FA is required
      if (result?.requires_2fa) {
        setRequires2FA(true);
        setTwoFAEmail(result.user_email || "your email");
        toast("Please enter your 2FA code from your authenticator app", { icon: "ℹ️" });
        setIsLoading(false);
        return;
      }

      // Login successful
      onSuccess && onSuccess();
    } catch (error) {
      // Error is handled in the login function
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setRequires2FA(false);
    setFormData((prev) => ({ ...prev, two_factor_code: "" }));
  };

  // 2FA Code Entry Form
  const twoFAView = (
    <motion.div
      key="2fa"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 md:p-10"
    >
      <div className="mb-8 text-center">
        <div className="mx-auto w-16 h-16 bg-gradient-to-br from-violet-500/20 to-cyan-500/20 rounded-2xl flex items-center justify-center mb-4">
          <DevicePhoneMobileIcon className="w-8 h-8 text-violet-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Two-Factor Authentication</h2>
        <p className="text-gray-400 text-sm">
          Enter the 6-digit code from your authenticator app for{" "}
          <span className="text-cyan-400">{twoFAEmail}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="group">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <ShieldCheckIcon className="w-4 h-4 text-violet-400" />
            Authentication Code
          </label>
          <Input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={formData.two_factor_code}
            onChange={(e) => {
              const value = e.target.value.replace(/\D/g, "");
              setFormData((prev) => ({
                ...prev,
                two_factor_code: value,
              }));
            }}
            placeholder="000000"
            autoFocus
            required
            className="text-center text-2xl tracking-[0.5em] font-mono"
          />
          <p className="mt-2 text-xs text-gray-500 text-center">
            Or enter a backup code if you've lost access to your authenticator
          </p>
        </div>

        <Button
          type="submit"
          disabled={isLoading || formData.two_factor_code.length < 6}
          gradient
          leftIcon={<ShieldCheckIcon className="w-5 h-5" />}
          isLoading={isLoading}
          className="w-full"
        >
          Verify & Sign In
        </Button>

        <Button type="button" variant="ghost" onClick={handleBack} className="w-full">
          ← Back to login
        </Button>
      </form>

      <div className="mt-6 p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl">
        <div className="flex items-start gap-3">
          <ShieldCheckSolid className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-gray-300">
            <p className="font-medium text-violet-300 mb-1">Your account is protected</p>
            <p className="text-gray-400 text-xs">
              Two-factor authentication adds an extra layer of security to your account by
              requiring a code from your authenticator app.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );

  // Standard Login Form
  const standardView = (
    <motion.div
      key="login"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 md:p-10"
    >
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Sign In</h2>
        <p className="text-gray-400">Access your ONYX security dashboard</p>
      </div>

      <motion.form
        onSubmit={handleSubmit}
        className="space-y-6"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.04 } },
        }}
      >
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
          className="group"
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <EnvelopeIcon className="w-4 h-4 text-cyan-400" />
            Email or Username
          </label>
          <Input
            type="text"
            value={formData.username_or_email}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                username_or_email: e.target.value,
              }))
            }
            leadingIcon={<UserIcon className="w-5 h-5" />}
            placeholder="Enter your email or username"
            required
            aria-required="true"
            autoComplete="username"
          />
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
          className="group"
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <LockClosedIcon className="w-4 h-4 text-violet-400" />
            Password
          </label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
              leadingIcon={<KeyIcon className="w-5 h-5" />}
              placeholder="Enter your password"
              required
              aria-required="true"
              autoComplete="current-password"
              className="pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-600/30 z-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
          className="flex items-center justify-between"
        >
          <label className="flex items-center group cursor-pointer">
            <input
              type="checkbox"
              checked={formData.remember_me}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  remember_me: e.target.checked,
                }))
              }
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-cyan-500 focus:ring-cyan-500/50 focus:ring-offset-0 transition-all cursor-pointer"
            />
            <span className="ml-2 text-sm text-gray-300 group-hover:text-white transition-colors">
              Remember me
            </span>
          </label>

          <button
            type="button"
            onClick={onSwitchToForgotPassword}
            className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors font-medium hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
          >
            Forgot password?
          </button>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <Button
            type="submit"
            disabled={isLoading}
            gradient
            rightIcon={isLoading ? undefined : <ArrowRightIcon className="w-5 h-5" />}
            isLoading={isLoading}
            className="w-full"
          >
            Sign In
          </Button>
        </motion.div>
      </motion.form>

      <motion.div
        variants={{
          hidden: { opacity: 0, y: 8 },
          visible: { opacity: 1, y: 0 },
        }}
        className="mt-8 text-center"
      >
        <span className="text-gray-400">Don't have an account? </span>
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text hover:from-cyan-300 hover:to-violet-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
        >
          Create account
        </button>
      </motion.div>

      <motion.div
        variants={{
          hidden: { opacity: 0, y: 8 },
          visible: { opacity: 1, y: 0 },
        }}
        className="mt-8 pt-6 border-t border-gray-700/50"
      >
        <div className="flex items-center justify-center gap-6 text-gray-500 text-xs">
          <div className="flex items-center gap-1">
            <ShieldCheckIcon className="w-4 h-4 text-cyan-400" />
            <span>Secure</span>
          </div>
          <div className="flex items-center gap-1">
            <LockClosedIcon className="w-4 h-4 text-violet-400" />
            <span>Encrypted</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircleIcon className="w-4 h-4 text-cyan-300" />
            <span>Verified</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );

  return (
    <AnimatePresence mode="wait">
      {requires2FA ? twoFAView : standardView}
    </AnimatePresence>
  );
};
