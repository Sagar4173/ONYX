/**
 * Enhanced Register Form Component
 * Modern UI with real-time password validation
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  SparklesIcon,
  LockClosedIcon,
  UserIcon,
  EnvelopeIcon,
  AtSymbolIcon,
} from "@heroicons/react/24/outline";
import { Button, Input } from "../ui/StyleComponents";
import { useAuth } from "./AuthContext";
import toast from "react-hot-toast";

export const RegisterForm = ({ onSuccess: _onSuccess, onSwitchToLogin, onRegistrationSuccess }) => {
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    full_name: "",
    password: "",
    confirm_password: "",
    organization: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false,
  });
  const { register } = useAuth();

  // Validate password in real-time
  useEffect(() => {
    const password = formData.password;
    setPasswordValidation({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password),
    });
  }, [formData.password]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirm_password) {
      toast.error("Passwords do not match");
      return;
    }

    const allValidationsPassed = Object.values(passwordValidation).every(Boolean);
    if (!allValidationsPassed) {
      toast.error("Please ensure your password meets all requirements");
      return;
    }

    setIsLoading(true);

    try {
      await register({
        email: formData.email,
        username: formData.username,
        full_name: formData.full_name,
        password: formData.password,
        organization: formData.organization || undefined,
      });
      onRegistrationSuccess && onRegistrationSuccess(formData.email);
    } catch (error) {
      // Error is handled in the register function
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      className="p-6 md:p-8"
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
        className="text-center mb-6"
      >
        <h2 className="text-2xl font-bold text-white mb-1">Create Account</h2>
        <p className="text-sm text-gray-400">Join ONYX Security Platform</p>
      </motion.div>

      <motion.form
        onSubmit={handleSubmit}
        className="space-y-5"
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
          className="grid grid-cols-2 gap-4"
        >
          <div>
            <label className="flex items-center gap-1.5 text-xs font-medium text-gray-400 mb-1.5">
              <AtSymbolIcon className="w-3.5 h-3.5 text-cyan-400" />
              Username
            </label>
            <Input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData((prev) => ({ ...prev, username: e.target.value }))}
              placeholder="username"
              required
              aria-required="true"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="flex items-center gap-1.5 text-xs font-medium text-gray-400 mb-1.5">
              <UserIcon className="w-3.5 h-3.5 text-violet-400" />
              Full Name
            </label>
            <Input
              type="text"
              value={formData.full_name}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  full_name: e.target.value,
                }))
              }
              placeholder="John Doe"
              required
              aria-required="true"
              autoComplete="name"
            />
          </div>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <label className="flex items-center gap-1.5 text-xs font-medium text-gray-400 mb-1.5">
            <EnvelopeIcon className="w-3.5 h-3.5 text-cyan-400" />
            Email
          </label>
          <Input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
            placeholder="your@email.com"
            required
            aria-required="true"
            autoComplete="email"
          />
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <label className="flex items-center gap-1.5 text-xs font-medium text-gray-400 mb-1.5">
            <LockClosedIcon className="w-3.5 h-3.5 text-violet-400" />
            Password
          </label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
              placeholder="Strong password"
              required
              aria-required="true"
              autoComplete="new-password"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors z-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          {formData.password && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-2 flex flex-wrap gap-x-4 gap-y-1"
            >
              {[
                { key: "length", label: "8+ characters" },
                { key: "uppercase", label: "Uppercase" },
                { key: "lowercase", label: "Lowercase" },
                { key: "number", label: "Number" },
                { key: "special", label: "Special char" },
              ].map(({ key, label }) => (
                <div key={key} className="flex items-center gap-1.5">
                  {passwordValidation[key] ? (
                    <CheckCircleIcon className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full border border-gray-600 flex-shrink-0" />
                  )}
                  <span
                    className={`text-xs transition-colors ${
                      passwordValidation[key] ? "text-green-400" : "text-gray-500"
                    }`}
                  >
                    {label}
                  </span>
                </div>
              ))}
            </motion.div>
          )}
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <label className="flex items-center gap-1.5 text-xs font-medium text-gray-400 mb-1.5">
            <LockClosedIcon className="w-3.5 h-3.5 text-violet-400" />
            Confirm Password
          </label>
          <div className="relative">
            <Input
              type={showConfirmPassword ? "text" : "password"}
              value={formData.confirm_password}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  confirm_password: e.target.value,
                }))
              }
              placeholder="Confirm password"
              required
              aria-required="true"
              autoComplete="new-password"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors z-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
            >
              {showConfirmPassword ? (
                <EyeSlashIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          {formData.confirm_password && formData.password !== formData.confirm_password && (
            <p className="mt-1.5 text-xs text-red-400">Passwords don't match</p>
          )}
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
            Create Account
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
        <span className="text-gray-400">Already have an account? </span>
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text hover:from-cyan-300 hover:to-violet-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
        >
          Sign in
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
            <CheckCircleIcon className="w-4 h-4 text-cyan-400" />
            <span>Free Forever</span>
          </div>
          <div className="flex items-center gap-1">
            <LockClosedIcon className="w-4 h-4 text-violet-400" />
            <span>Secure</span>
          </div>
          <div className="flex items-center gap-1">
            <SparklesIcon className="w-4 h-4 text-cyan-300" />
            <span>No Credit Card</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
