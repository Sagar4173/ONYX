/**
 * Enhanced Register Form Component
 * Modern UI with real-time password validation
 */
import { useState, useEffect } from "react";
import {
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  SparklesIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";
import { UserCircleIcon as UserCircleSolid } from "@heroicons/react/24/solid";
import { Button, Input } from "../../styles/components";
import { useAuth } from "./AuthContext";
import toast from "react-hot-toast";

export const RegisterForm = ({
  onSuccess,
  onSwitchToLogin,
  onRegistrationSuccess,
}) => {
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

    const allValidationsPassed =
      Object.values(passwordValidation).every(Boolean);
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
    <div className="p-6 md:p-8 max-h-[85vh] overflow-y-auto">
      {/* Compact Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-1">Create Account</h2>
        <p className="text-sm text-gray-400">Join ONYX Security Platform</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-gray-400 mb-1.5 block">
              Username
            </label>
            <Input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, username: e.target.value }))
              }
              placeholder="username"
              required
              aria-required="true"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-400 mb-1.5 block">
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
        </div>

        <div>
          <label className="text-xs font-medium text-gray-400 mb-1.5 block">
            Email
          </label>
          <Input
            type="email"
            value={formData.email}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, email: e.target.value }))
            }
            placeholder="your@email.com"
            required
            aria-required="true"
            autoComplete="email"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-gray-400 mb-1.5 block">
            Password
          </label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, password: e.target.value }))
              }
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
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors z-10"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {Object.entries({
              length: "8+ characters",
              uppercase: "Uppercase letter",
              lowercase: "Lowercase letter",
              number: "Number",
              special: "Special character",
            }).map(([key, label]) => (
              <div key={key} className="flex items-center gap-2">
                <div
                  className={`h-2 w-2 rounded-full transition-colors ${
                    passwordValidation[key] ? "bg-green-500" : "bg-gray-600"
                  }`}
                />
                <span
                  className={`text-xs transition-colors ${
                    passwordValidation[key] ? "text-green-400" : "text-gray-400"
                  }`}
                >
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-gray-400 mb-1.5 block">
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
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors z-10"
            >
              {showConfirmPassword ? (
                <EyeSlashIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          {formData.confirm_password &&
            formData.password !== formData.confirm_password && (
              <p className="mt-1.5 text-xs text-red-400">
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
          Create Account
        </Button>
      </form>

      <div className="mt-6 text-center">
        <span className="text-gray-400">Already have an account? </span>
        <Button
          variant="ghost"
          onClick={onSwitchToLogin}
          className="!bg-none p-0 text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text font-semibold hover:from-cyan-300 hover:to-violet-300"
        >
          Sign in
        </Button>
      </div>

      {/* Trust Badges */}
      <div className="mt-8 pt-6 border-t border-gray-700/50">
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
      </div>
    </div>
  );
};
