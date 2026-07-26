/**
 * Auth Pages
 * Authentication-related page components
 */
import React from "react";
import { useLocation, useNavigate, Navigate } from "react-router-dom";
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { PageTransition } from "../../styles/components";
import toast from "react-hot-toast";
import { useAuth, AuthModal, EmailVerification } from "./index";

/**
 * Email Verification Page Component
 */
export const EmailVerificationPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get("token");

  const handleVerificationSuccess = () => {
    if (isAuthenticated) {
      navigate("/dashboard", {
        state: {
          message: "Email verified successfully!",
          from: "verification",
        },
        replace: true,
      });
    } else {
      toast.success("Email verified successfully! Please log in to access your account.");
      setTimeout(() => {
        navigate("/login", { replace: true });
      }, 2000);
    }
  };

  const handleVerificationError = () => {
    navigate("/login");
  };

  return (
    <EmailVerification
      token={token}
      onSuccess={handleVerificationSuccess}
      onError={handleVerificationError}
    />
  );
};

/**
 * Password Reset Page Component
 */
export const PasswordResetPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get("token");

  const handleResetSuccess = () => {
    navigate("/dashboard", {
      state: {
        message: "Password reset successfully! Please log in with your new password.",
      },
    });
  };

  const handleSwitchToLogin = () => {
    navigate("/login");
  };

  if (!token) {
    return (
      <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-red-500 to-red-600 rounded-2xl mb-4">
          <ExclamationTriangleIcon className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Invalid Reset Link</h2>
        <p className="text-gray-400 mb-6">The password reset link is invalid or has expired.</p>
        <button
          onClick={handleSwitchToLogin}
          className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-medium rounded-xl hover:from-cyan-600 hover:to-violet-700 transition-all"
        >
          Back to Login
        </button>
      </div>
    );
  }

  return (
    <AuthModal
      isOpen={true}
      onClose={handleSwitchToLogin}
      initialView="reset-password"
      resetToken={token}
    />
  );
};

/**
 * Auth Routing Handler
 * Handles routing for unauthenticated users
 */
export const AuthRoutingHandler = ({ authModalOpen, setAuthModalOpen }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const publicRoutes = [
    "/landing",
    "/login",
    "/register",
    "/reset-password",
    "/verify-email",
    "/legal",
    "/terms",
    "/about",
    "/docs",
  ];

  const isPublicRoute =
    location.pathname === "/" ||
    publicRoutes.some(
      (route) => location.pathname === route || location.pathname.startsWith(route + "/")
    );

  // Import pages dynamically to avoid circular deps
  const LandingPage = React.lazy(() =>
    import("../marketing").then((mod) => ({ default: mod.LandingPage }))
  );
  const DataPolicy = React.lazy(() =>
    import("../marketing").then((mod) => ({ default: mod.DataPolicy }))
  );
  const TermsOfService = React.lazy(() =>
    import("../marketing").then((mod) => ({ default: mod.TermsOfService }))
  );
  const AboutPage = React.lazy(() =>
    import("../marketing").then((mod) => ({ default: mod.AboutPage }))
  );
  const DocumentationPage = React.lazy(() =>
    import("../marketing").then((mod) => ({ default: mod.DocumentationPage }))
  );

  if (isPublicRoute) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
        <PageTransition>
          <React.Suspense
            fallback={
              <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            }
          >
            {location.pathname === "/" || location.pathname === "/landing" ? (
              <LandingPage />
            ) : location.pathname === "/login" ? (
              <div className="min-h-screen flex items-center justify-center p-4">
                <AuthModal isOpen={true} onClose={() => navigate("/")} initialView="login" />
              </div>
            ) : location.pathname === "/register" ? (
              <div className="min-h-screen flex items-center justify-center p-4">
                <AuthModal isOpen={true} onClose={() => navigate("/")} initialView="register" />
              </div>
            ) : location.pathname === "/verify-email" ? (
              <div className="min-h-screen flex items-center justify-center p-4">
                <EmailVerificationPage />
              </div>
            ) : location.pathname === "/reset-password" ? (
              <div className="min-h-screen flex items-center justify-center p-4">
                <PasswordResetPage />
              </div>
            ) : location.pathname === "/legal" ? (
              <DataPolicy />
            ) : location.pathname === "/terms" ? (
              <TermsOfService />
            ) : location.pathname === "/about" ? (
              <AboutPage />
            ) : location.pathname === "/docs" ? (
              <DocumentationPage />
            ) : null}
          </React.Suspense>
        </PageTransition>
      </div>
    );
  }

  // For non-public routes when not authenticated, redirect to landing page
  return <Navigate to="/" replace />;
};

export default {
  EmailVerificationPage,
  PasswordResetPage,
  AuthRoutingHandler,
};
