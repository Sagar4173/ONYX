/**
 * Authentication Components for SecureDevOps Platform
 * Handles login, registration, and user management
 */
import React, {
  useState,
  useEffect,
  createContext,
  useContext,
  useCallback,
} from "react";
import {
  UserCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { authAPI } from "../services/api.js";

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on app load
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user_data");

    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);

        // Verify token is still valid
        verifyToken(token);
      } catch (error) {
        console.error("Error parsing user data:", error);
        logout();
      }
    }

    setIsLoading(false);
  }, []);

  const verifyToken = async (token) => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
    } catch (error) {
      console.error("Token verification failed:", error);
      logout();
    }
  };

  const login = async (credentials) => {
    try {
      const data = await authAPI.login(credentials);

      // Store tokens and user data
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("user_data", JSON.stringify(data.user));

      // Set initial user data
      setUser(data.user);
      setIsAuthenticated(true);

      // Immediately refresh user profile to get latest verification status
      try {
        const updatedUser = await authAPI.getProfile();
        setUser(updatedUser);
        localStorage.setItem("user_data", JSON.stringify(updatedUser));
      } catch (profileError) {
        console.log("Could not refresh profile after login:", profileError);
        // Don't throw error, use the data from login response
      }

      toast.success(`Welcome back, ${data.user.full_name}!`);
      return data;
    } catch (error) {
      // Extract proper error message
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Login failed. Please check your credentials.";

      console.error("Login error details:", {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      });

      toast.error(errorMessage);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const data = await authAPI.register(userData);
      toast.success(
        "Account created successfully! Please check your email for verification."
      );
      return data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Registration failed";
      toast.error(errorMessage);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (token) {
        await authAPI.logout();
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear local storage regardless of API call success
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_data");

      setUser(null);
      setIsAuthenticated(false);
      toast.success("Logged out successfully");
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const data = await authAPI.updateProfile(profileData);
      setUser(data);
      localStorage.setItem("user_data", JSON.stringify(data));

      toast.success("Profile updated successfully!");
      return data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Profile update failed";
      toast.error(errorMessage);
      throw error;
    }
  };

  const changePassword = async (passwordData) => {
    try {
      await authAPI.changePassword(passwordData);
      toast.success("Password changed successfully! Please log in again.");
      logout();
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Password change failed";
      toast.error(errorMessage);
      throw error;
    }
  };

  const verifyEmail = async (token) => {
    try {
      const data = await authAPI.verifyEmail(token);
      toast.success("Email verified successfully!");

      // Always try to refresh user data after verification, regardless of current auth state
      try {
        const updatedUser = await authAPI.getProfile();
        setUser(updatedUser);
        localStorage.setItem("user_data", JSON.stringify(updatedUser));
      } catch (profileError) {
        // If getting profile fails (user not logged in), that's okay
        // The verification was still successful
        console.log(
          "User not logged in yet, verification successful but profile not updated"
        );
      }

      return data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Email verification failed";
      toast.error(errorMessage);
      throw error;
    }
  };

  const resendVerificationEmail = async () => {
    try {
      const data = await authAPI.resendVerificationEmail();
      toast.success("Verification email sent! Please check your inbox.");
      return data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to resend verification email";
      toast.error(errorMessage);
      throw error;
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      const data = await authAPI.requestPasswordReset(email);
      toast.success("Password reset link sent! Please check your email.");
      return data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to send reset link";
      toast.error(errorMessage);
      throw error;
    }
  };

  const confirmPasswordReset = async (resetData) => {
    try {
      const data = await authAPI.confirmPasswordReset(resetData);
      toast.success(
        "Password reset successfully! Please log in with your new password."
      );
      return data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Password reset failed";
      toast.error(errorMessage);
      throw error;
    }
  };

  const refreshUserProfile = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (token && isAuthenticated) {
        const updatedUser = await authAPI.getProfile();
        setUser(updatedUser);
        localStorage.setItem("user_data", JSON.stringify(updatedUser));
        return updatedUser;
      }
    } catch (error) {
      console.error("Error refreshing user profile:", error);
      throw error;
    }
  }, [isAuthenticated]);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    verifyEmail,
    resendVerificationEmail,
    requestPasswordReset,
    confirmPasswordReset,
    refreshUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Login Component
export const LoginForm = ({
  onSuccess,
  onSwitchToRegister,
  onSwitchToForgotPassword,
}) => {
  const [formData, setFormData] = useState({
    username_or_email: "",
    password: "",
    remember_me: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(formData);
      onSuccess && onSuccess();
    } catch (error) {
      // Error is handled in the login function
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
          <ShieldCheckIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
        <p className="text-gray-400">Sign in to your SecureDevOps account</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Email or Username
          </label>
          <input
            type="text"
            value={formData.username_or_email}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                username_or_email: e.target.value,
              }))
            }
            className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            placeholder="Enter your email or username"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, password: e.target.value }))
              }
              className="w-full px-4 py-3 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="Enter your password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.remember_me}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  remember_me: e.target.checked,
                }))
              }
              className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500/50"
            />
            <span className="ml-2 text-sm text-gray-300">Remember me</span>
          </label>

          <button
            type="button"
            onClick={onSwitchToForgotPassword}
            className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <span className="text-gray-400">Don't have an account? </span>
        <button
          onClick={onSwitchToRegister}
          className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
        >
          Create account
        </button>
      </div>
    </div>
  );
};

// Registration Component
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
      special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
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
      // Call the registration success callback to change UI state
      onRegistrationSuccess && onRegistrationSuccess(formData.email);
    } catch (error) {
      // Error is handled in the register function
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
          <UserCircleIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Create Account</h2>
        <p className="text-gray-400">Join SecureDevOps Platform</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Username
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, username: e.target.value }))
              }
              className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, full_name: e.target.value }))
              }
              className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="Full Name"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Email
          </label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, email: e.target.value }))
            }
            className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            placeholder="your@email.com"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Organization (Optional)
          </label>
          <input
            type="text"
            value={formData.organization}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, organization: e.target.value }))
            }
            className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            placeholder="Your organization"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, password: e.target.value }))
              }
              className="w-full px-4 py-3 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="Create a strong password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>

          {/* Password Requirements */}
          <div className="mt-3 space-y-1">
            {Object.entries({
              length: "At least 8 characters",
              uppercase: "One uppercase letter",
              lowercase: "One lowercase letter",
              number: "One number",
              special: "One special character",
            }).map(([key, label]) => (
              <div key={key} className="flex items-center space-x-2">
                <div
                  className={`h-2 w-2 rounded-full ${
                    passwordValidation[key] ? "bg-green-500" : "bg-gray-600"
                  }`}
                />
                <span
                  className={`text-xs ${
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
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Confirm Password
          </label>
          <div className="relative">
            <input
              type={showConfirmPassword ? "text" : "password"}
              value={formData.confirm_password}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  confirm_password: e.target.value,
                }))
              }
              className="w-full px-4 py-3 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="Confirm your password"
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
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
              <div className="mt-2 flex items-center space-x-2">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-400" />
                <span className="text-xs text-red-400">
                  Passwords do not match
                </span>
              </div>
            )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Creating account..." : "Create Account"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <span className="text-gray-400">Already have an account? </span>
        <button
          onClick={onSwitchToLogin}
          className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
        >
          Sign in
        </button>
      </div>
    </div>
  );
};

// Forgot Password Component
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
      // Error is handled in the requestPasswordReset function
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
          <ShieldCheckIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Forgot Password</h2>
        <p className="text-gray-400">Enter your email to reset your password</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Email Address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            placeholder="Enter your email address"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Sending..." : "Send Reset Link"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <span className="text-gray-400">Remember your password? </span>
        <button
          onClick={onSwitchToLogin}
          className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
        >
          Sign in
        </button>
      </div>
    </div>
  );
};

// Reset Password Component
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
  const { confirmPasswordReset } = useAuth();

  // Validate password in real-time
  useEffect(() => {
    const password = formData.password;
    setPasswordValidation({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
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
      await confirmPasswordReset({
        token,
        new_password: formData.password,
      });
      onSuccess && onSuccess();
    } catch (error) {
      // Error is handled in the confirmPasswordReset function
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
          <ShieldCheckIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Reset Password</h2>
        <p className="text-gray-400">Enter your new password</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            New Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, password: e.target.value }))
              }
              className="w-full px-4 py-3 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="Create a strong password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>

          {/* Password Requirements */}
          <div className="mt-3 space-y-1">
            {Object.entries({
              length: "At least 8 characters",
              uppercase: "One uppercase letter",
              lowercase: "One lowercase letter",
              number: "One number",
              special: "One special character",
            }).map(([key, label]) => (
              <div key={key} className="flex items-center space-x-2">
                <div
                  className={`h-2 w-2 rounded-full ${
                    passwordValidation[key] ? "bg-green-500" : "bg-gray-600"
                  }`}
                />
                <span
                  className={`text-xs ${
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
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Confirm New Password
          </label>
          <div className="relative">
            <input
              type={showConfirmPassword ? "text" : "password"}
              value={formData.confirm_password}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  confirm_password: e.target.value,
                }))
              }
              className="w-full px-4 py-3 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="Confirm your new password"
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
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
              <div className="mt-2 flex items-center space-x-2">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-400" />
                <span className="text-xs text-red-400">
                  Passwords do not match
                </span>
              </div>
            )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Resetting..." : "Reset Password"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <span className="text-gray-400">Remember your password? </span>
        <button
          onClick={onSwitchToLogin}
          className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
        >
          Sign in
        </button>
      </div>
    </div>
  );
};

// Registration Success Component
export const RegistrationSuccess = ({
  email,
  onSwitchToLogin,
  onResendVerification,
}) => {
  const [isResending, setIsResending] = useState(false);

  const handleResendVerification = async () => {
    setIsResending(true);
    try {
      await onResendVerification();
    } catch (error) {
      // Error handled by the callback
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl mb-4">
        <CheckCircleIcon className="h-8 w-8 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">Check Your Email!</h2>
      <p className="text-gray-400 mb-6">
        We've sent a verification link to{" "}
        <span className="text-blue-400 font-medium">{email}</span>. Please check
        your inbox and click the link to activate your account.
      </p>

      <div className="space-y-4">
        <button
          onClick={handleResendVerification}
          disabled={isResending}
          className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 text-white font-medium rounded-xl hover:bg-gray-600/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isResending ? "Resending..." : "Resend Verification Email"}
        </button>

        <button
          onClick={onSwitchToLogin}
          className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
        >
          Back to Login
        </button>
      </div>
    </div>
  );
};

// Forgot Password Success Component
export const ForgotPasswordSuccess = ({ email, onSwitchToLogin }) => {
  return (
    <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
        <CheckCircleIcon className="h-8 w-8 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">Check Your Email!</h2>
      <p className="text-gray-400 mb-6">
        We've sent a password reset link to{" "}
        <span className="text-blue-400 font-medium">{email}</span>. Please check
        your inbox and follow the instructions to reset your password.
      </p>

      <button
        onClick={onSwitchToLogin}
        className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
      >
        Back to Login
      </button>
    </div>
  );
};

// User Profile Component
export const UserProfile = ({ onClose }) => {
  const {
    user,
    updateProfile,
    changePassword,
    logout,
    resendVerificationEmail,
  } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || "",
    organization: user?.organization || "",
    department: user?.department || "",
    phone: user?.phone || "",
    timezone: user?.timezone || "UTC",
  });
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await updateProfile(profileData);
    } catch (error) {
      // Error handled in updateProfile function
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error("New passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
    } catch (error) {
      // Error handled in changePassword function
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white">User Profile</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all"
            >
              ✕
            </button>
          </div>

          {/* User Info */}
          <div className="mt-4 flex items-center space-x-4">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
              <UserCircleIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-white">{user.full_name}</h3>
              <div className="flex items-center space-x-2">
                <p className="text-sm text-gray-400">{user.email}</p>
                {user.is_email_verified ? (
                  <span className="inline-flex items-center px-2 py-0.5 text-xs bg-green-500/20 text-green-300 rounded-lg">
                    <CheckCircleIcon className="h-3 w-3 mr-1" />
                    Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-300 rounded-lg">
                    <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                    Unverified
                  </span>
                )}
              </div>
              <span className="inline-block px-2 py-1 mt-1 text-xs bg-blue-500/20 text-blue-300 rounded-lg">
                {user.role}
              </span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700/50">
          <button
            onClick={() => setActiveTab("profile")}
            className={`px-6 py-3 text-sm font-medium transition-all ${
              activeTab === "profile"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab("account")}
            className={`px-6 py-3 text-sm font-medium transition-all ${
              activeTab === "account"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Account
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`px-6 py-3 text-sm font-medium transition-all ${
              activeTab === "security"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Security
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-96">
          {activeTab === "profile" && (
            <form onSubmit={handleProfileUpdate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profileData.full_name}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        full_name: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Organization
                  </label>
                  <input
                    type="text"
                    value={profileData.organization}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        organization: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Department
                  </label>
                  <input
                    type="text"
                    value={profileData.department}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        department: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        phone: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50"
              >
                {isLoading ? "Updating..." : "Update Profile"}
              </button>
            </form>
          )}

          {activeTab === "account" && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-white">
                Account Settings
              </h3>

              {/* Email Verification Status */}
              <div className="p-4 bg-gray-700/30 rounded-xl border border-gray-600/50">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">
                      Email Verification
                    </h4>
                    <p className="text-sm text-gray-400">
                      {user.is_email_verified
                        ? "Your email address has been verified."
                        : "Please verify your email address to access all features."}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {user.is_email_verified ? (
                      <span className="inline-flex items-center px-3 py-1 text-sm bg-green-500/20 text-green-300 rounded-lg">
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        Verified
                      </span>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-3 py-1 text-sm bg-yellow-500/20 text-yellow-300 rounded-lg">
                          <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                          Unverified
                        </span>
                        <button
                          onClick={async () => {
                            try {
                              await resendVerificationEmail();
                            } catch (error) {
                              // Error handled in function
                            }
                          }}
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all"
                        >
                          Resend Email
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Account Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-700/30 rounded-xl border border-gray-600/50">
                  <h4 className="text-white font-medium mb-2">
                    Account Status
                  </h4>
                  <p className="text-sm text-gray-400">
                    Status:{" "}
                    <span className="text-green-300">
                      {user.status || "active"}
                    </span>
                  </p>
                  <p className="text-sm text-gray-400">
                    Role: <span className="text-blue-300">{user.role}</span>
                  </p>
                </div>

                <div className="p-4 bg-gray-700/30 rounded-xl border border-gray-600/50">
                  <h4 className="text-white font-medium mb-2">Member Since</h4>
                  <p className="text-sm text-gray-400">
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : "Unknown"}
                  </p>
                  <p className="text-sm text-gray-400">
                    Last Login:{" "}
                    {user.last_login
                      ? new Date(user.last_login).toLocaleDateString()
                      : "Never"}
                  </p>
                </div>
              </div>

              {/* Admin Email Test */}
              {user.role === "admin" && (
                <div className="p-4 bg-gray-700/30 rounded-xl border border-gray-600/50">
                  <h4 className="text-white font-medium mb-2">
                    Email Configuration Test
                  </h4>
                  <p className="text-sm text-gray-400 mb-3">
                    Test the email system by sending a test email to yourself.
                  </p>
                  <button
                    onClick={async () => {
                      try {
                        setIsLoading(true);
                        const result = await authAPI.testEmailConfiguration();
                        if (result.success) {
                          toast.success(
                            "Test email sent successfully! Check your inbox."
                          );
                        } else {
                          toast.error(result.message || "Email test failed");
                        }
                      } catch (error) {
                        toast.error("Failed to send test email");
                      } finally {
                        setIsLoading(false);
                      }
                    }}
                    disabled={isLoading}
                    className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all disabled:opacity-50"
                  >
                    {isLoading ? "Sending..." : "Send Test Email"}
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              <form onSubmit={handlePasswordChange} className="space-y-4">
                <h3 className="text-lg font-medium text-white">
                  Change Password
                </h3>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) =>
                      setPasswordData((prev) => ({
                        ...prev,
                        current_password: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) =>
                      setPasswordData((prev) => ({
                        ...prev,
                        new_password: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) =>
                      setPasswordData((prev) => ({
                        ...prev,
                        confirm_password: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50"
                >
                  {isLoading ? "Changing..." : "Change Password"}
                </button>
              </form>

              <div className="pt-4 border-t border-gray-700/50">
                <button
                  onClick={logout}
                  className="w-full px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-all"
                >
                  Logout from all devices
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Auth Modal Component - combines all auth forms with state management
export const AuthModal = ({
  isOpen,
  onClose,
  initialView = "login",
  resetToken = null,
}) => {
  const [currentView, setCurrentView] = useState(initialView);
  const [userEmail, setUserEmail] = useState("");
  const { resendVerificationEmail } = useAuth();

  // Reset to initial view when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      if (resetToken) {
        setCurrentView("reset-password");
      } else {
        setCurrentView(initialView);
      }
    }
  }, [isOpen, initialView, resetToken]);

  const handleLoginSuccess = () => {
    if (onClose) onClose();
  };

  const handleRegistrationSuccess = (email) => {
    setUserEmail(email);
    setCurrentView("registration-success");
  };

  const handleForgotPasswordSuccess = (email) => {
    setUserEmail(email);
    setCurrentView("forgot-password-success");
  };

  const handlePasswordResetSuccess = () => {
    setCurrentView("login");
    toast.success(
      "Password reset successfully! Please log in with your new password."
    );
  };

  if (!isOpen) return null;

  const renderCurrentView = () => {
    switch (currentView) {
      case "login":
        return (
          <LoginForm
            onSuccess={handleLoginSuccess}
            onSwitchToRegister={() => setCurrentView("register")}
            onSwitchToForgotPassword={() => setCurrentView("forgot-password")}
          />
        );
      case "register":
        return (
          <RegisterForm
            onRegistrationSuccess={handleRegistrationSuccess}
            onSwitchToLogin={() => setCurrentView("login")}
          />
        );
      case "forgot-password":
        return (
          <ForgotPasswordForm
            onSuccess={handleForgotPasswordSuccess}
            onSwitchToLogin={() => setCurrentView("login")}
          />
        );
      case "reset-password":
        return (
          <ResetPasswordForm
            token={resetToken}
            onSuccess={handlePasswordResetSuccess}
            onSwitchToLogin={() => setCurrentView("login")}
          />
        );
      case "registration-success":
        return (
          <RegistrationSuccess
            email={userEmail}
            onSwitchToLogin={() => setCurrentView("login")}
            onResendVerification={resendVerificationEmail}
          />
        );
      case "forgot-password-success":
        return (
          <ForgotPasswordSuccess
            email={userEmail}
            onSwitchToLogin={() => setCurrentView("login")}
          />
        );
      default:
        return (
          <LoginForm
            onSuccess={handleLoginSuccess}
            onSwitchToRegister={() => setCurrentView("register")}
            onSwitchToForgotPassword={() => setCurrentView("forgot-password")}
          />
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-md">
          <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl overflow-hidden">
            {/* Gradient Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10" />

            <div className="relative">{renderCurrentView()}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Email Verification Component
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

  if (isVerifying) {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-4">
          <ArrowPathIcon className="h-8 w-8 text-white animate-spin" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Verifying Email</h2>
        <p className="text-gray-400">
          Please wait while we verify your email address...
        </p>
      </div>
    );
  }

  if (verificationStatus === "success") {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl mb-4">
          <CheckCircleIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Email Verified!</h2>
        <p className="text-gray-400 mb-6">
          Your account has been successfully verified. You can now access all
          features.
        </p>
        <button
          onClick={onSuccess}
          className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
        >
          Continue to Dashboard
        </button>
      </div>
    );
  }

  if (verificationStatus === "error") {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
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
          className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all"
        >
          Resend Verification Email
        </button>
      </div>
    );
  }

  return null;
};
