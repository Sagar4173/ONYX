/**
 * Authentication Context Provider
 * Manages authentication state across the application
 */
import React, {
  useState,
  useEffect,
  createContext,
  useContext,
  useCallback,
} from "react";
import toast from "react-hot-toast";
import { authAPI } from "../../services/api.js";

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
      // Handle FastAPI validation errors (422)
      if (
        error.response?.status === 422 &&
        Array.isArray(error.response?.data?.detail)
      ) {
        const validationErrors = error.response.data.detail;

        // Format field names to be more readable
        const formatFieldName = (field) => {
          return field
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
        };

        // Create user-friendly error messages
        const errorMessages = validationErrors.map((err) => {
          const field = err.loc?.[err.loc.length - 1] || "field";
          const fieldName = formatFieldName(field);

          // Customize message based on error type
          if (err.type === "value_error" || err.type === "string_too_short") {
            return `${fieldName}: ${err.msg}`;
          } else if (err.type === "missing") {
            return `${fieldName} is required`;
          } else {
            return `${fieldName}: ${err.msg}`;
          }
        });

        // Show each error separately for better visibility
        errorMessages.forEach((msg) => toast.error(msg, { duration: 4000 }));
      } else {
        // Handle other error types
        const errorMessage =
          error.response?.data?.detail ||
          error.response?.data?.message ||
          "Login failed. Please check your credentials.";
        toast.error(errorMessage);
      }
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      toast.success(
        "Registration successful! Please check your email to verify your account."
      );
      return response;
    } catch (error) {
      console.log(
        "Registration error full:",
        JSON.stringify(error.response?.data, null, 2)
      );

      const errorData = error.response?.data;

      // Check for new structured error format from backend
      if (errorData?.detail?.errors && Array.isArray(errorData.detail.errors)) {
        const errors = errorData.detail.errors;
        errors.forEach((err) => {
          const fieldName = err.field
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
          toast.error(`${fieldName}: ${err.message}`);
        });
      }
      // Check if it's a string error message (Pydantic formatted)
      else if (typeof errorData?.detail === "string") {
        const detail = errorData.detail;

        // Check if it's a Pydantic validation error format
        if (detail.includes("validation error")) {
          // Extract individual field errors using regex
          const fieldErrorPattern = /(\w+)\s+Value error,\s*([^[]+)/g;
          const matches = [...detail.matchAll(fieldErrorPattern)];

          if (matches.length > 0) {
            matches.forEach((match) => {
              const fieldName = match[1]
                .split("_")
                .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ");
              const message = match[2].trim();
              toast.error(`${fieldName}: ${message}`);
            });
          } else {
            // Fallback: show the whole message cleaned up
            const cleanMessage = detail
              .split("\n")
              .filter((line) => line.includes("must be"))
              .map((line) => line.trim())
              .join(". ");
            toast.error(cleanMessage || detail);
          }
        } else {
          // Regular string error
          toast.error(detail);
        }
      }
      // Handle FastAPI validation errors (422 or 400) as array
      else if (
        (error.response?.status === 422 || error.response?.status === 400) &&
        Array.isArray(errorData?.detail)
      ) {
        const validationErrors = errorData.detail;

        // Format field names to be more readable
        const formatFieldName = (field) => {
          return field
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
        };

        // Create user-friendly error messages
        const errorMessages = validationErrors.map((err) => {
          const field = err.loc?.[err.loc.length - 1] || "field";
          const fieldName = formatFieldName(field);

          // Get the error message
          let message = err.msg || err.message || "Invalid value";

          // Remove everything after and including [type=
          message = message.split("[type=")[0].trim();

          // Remove "Value error, " prefix if present
          message = message.replace(/^Value error,\s*/i, "");

          // Remove "For further information visit https://..." suffix
          message = message.split("For further information")[0].trim();

          // Customize message based on error type
          if (err.type === "missing") {
            return `${fieldName} is required`;
          } else {
            return `${fieldName}: ${message}`;
          }
        });

        // Show each error separately for better visibility
        errorMessages.forEach((msg) => toast.error(msg));
      } else {
        // Handle other error types
        const errorMessage =
          errorData?.message || "Registration failed. Please try again.";
        toast.error(errorMessage);
      }
      throw error;
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_data");
    setUser(null);
    setIsAuthenticated(false);
    toast.success("Logged out successfully");
  }, []);

  const refreshUserProfile = async () => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
      localStorage.setItem("user_data", JSON.stringify(userData));
      return userData;
    } catch (error) {
      console.error("Failed to refresh user profile:", error);
      throw error;
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const updatedUser = await authAPI.updateProfile(profileData);
      setUser(updatedUser);
      localStorage.setItem("user_data", JSON.stringify(updatedUser));
      toast.success("Profile updated successfully!");
      return updatedUser;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Failed to update profile.";
      toast.error(errorMessage);
      throw error;
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      await authAPI.requestPasswordReset(email);
      toast.success("Password reset email sent! Check your inbox.");
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        "Failed to send reset email. Please try again.";
      toast.error(errorMessage);
      throw error;
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      await authAPI.resetPassword(token, newPassword);
      toast.success("Password reset successful! You can now login.");
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        "Failed to reset password. Link may be expired.";
      toast.error(errorMessage);
      throw error;
    }
  };

  const resendVerificationEmail = async (email) => {
    try {
      await authAPI.resendVerificationEmail(email);
      toast.success("Verification email sent! Check your inbox.");
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || "Failed to send verification email.";
      toast.error(errorMessage);
      throw error;
    }
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUserProfile,
    updateProfile,
    requestPasswordReset,
    resetPassword,
    resendVerificationEmail,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
