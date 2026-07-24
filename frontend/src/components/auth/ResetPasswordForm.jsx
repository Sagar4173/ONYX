/**
 * Enhanced Reset Password Form Component
 */
import { useState, useEffect } from "react";
import {
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  } from "@heroicons/react/24/outline";
import { ShieldCheckIcon as ShieldCheckSolid } from "@heroicons/react/24/solid";
import { Button, Input } from "../../styles/components";
import { useAuth } from "./AuthContext";
import toast from "react-hot-toast";

export const ResetPasswordForm = ({ token, onSuccess, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    password: "",
    confirm_password: ""});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false});
  const { resetPassword } = useAuth();

  // Validate password in real-time
  useEffect(() => {
    const password = formData.password;
    setPasswordValidation({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)});
  }, [formData.password]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirm_password) {
      toast.error("Passwords do not match");
      return;
    }

    const allValidationsPassed =
      Object.values(passwordValidation).every(Boolean);
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
            <ShieldCheckSolid className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent mb-2">
            Create New Password
          </h2>
          <p className="text-gray-400">
            Enter a strong password for your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="group">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <LockClosedIcon className="w-4 h-4 text-cyan-400" />
              New Password
            </label>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                value={formData.password}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, password: e.target.value }))
                }
                placeholder="Enter new password"
                required
                className="pr-12"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-600/30 z-10"
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {Object.entries({
                length: "8+ characters",
                uppercase: "Uppercase",
                lowercase: "Lowercase",
                number: "Number",
                special: "Special char"}).map(([key, label]) => (
                <div key={key} className="flex items-center gap-2">
                  <div
                    className={`h-2 w-2 rounded-full transition-colors ${
                      passwordValidation[key] ? "bg-green-500" : "bg-gray-600"
                    }`}
                  />
                  <span
                    className={`text-xs transition-colors ${
                      passwordValidation[key]
                        ? "text-green-400"
                        : "text-gray-400"
                    }`}
                  >
                    {label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="group">
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
                    confirm_password: e.target.value}))
                }
                placeholder="Confirm new password"
                required
                className="pr-12"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-600/30 z-10"
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
            {formData.confirm_password &&
              formData.password !== formData.confirm_password && (
                <p className="mt-2 text-xs text-red-400">
                  Passwords don't match
                </p>
              )}
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            gradient
            rightIcon={<ArrowRightIcon className="w-5 h-5" />}
            isLoading={isLoading}
            className="w-full"
          >
            Reset Password
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
