import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import { Button, Input } from "../../styles/components";
import { useAuth } from "./AuthContext";
import toast from "react-hot-toast";

export const ResetPasswordForm = ({ token, onSuccess, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    password: "",
    confirm_password: "",
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
  const { resetPassword } = useAuth();

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
      await resetPassword(token, formData.password);
      onSuccess && onSuccess();
    } catch (error) {
      // Error is handled in the context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      className="p-10"
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
        className="text-center mb-8"
      >
        <h2 className="text-3xl font-bold text-white mb-2">Create New Password</h2>
        <p className="text-sm text-gray-400">Enter a strong password for your account</p>
      </motion.div>

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
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <LockClosedIcon className="w-4 h-4 text-cyan-400" />
            New Password
          </label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
              placeholder="Enter new password"
              required
              aria-required="true"
              autoComplete="new-password"
              className="pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-600/30 z-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
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
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <LockClosedIcon className="w-4 h-4 text-violet-400" />
            Confirm New Password
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
              placeholder="Confirm new password"
              required
              aria-required="true"
              autoComplete="new-password"
              className="pr-12"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-600/30 z-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              {showConfirmPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          {formData.confirm_password && formData.password !== formData.confirm_password && (
            <p className="mt-2 text-xs text-red-400">Passwords don't match</p>
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
            Reset Password
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
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text hover:from-cyan-300 hover:to-violet-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
        >
          ← Back to sign in
        </button>
      </motion.div>
    </motion.div>
  );
};
