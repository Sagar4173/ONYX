import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import {
  BoltIcon,
  CodeBracketIcon,
  ServerIcon,
  ChartBarIcon,
  LockClosedIcon,
  SparklesIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "./AuthContext";
import { OnyxLogo } from "../common";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";
import { ForgotPasswordForm } from "./ForgotPasswordForm";
import { ResetPasswordForm } from "./ResetPasswordForm";
import { RegistrationSuccess } from "./RegistrationSuccess";
import { ForgotPasswordSuccess } from "./ForgotPasswordSuccess";

const FEATURE_BG = {
  cyan: "bg-cyan-500/20",
  violet: "bg-violet-500/20",
};

const FEATURE_BORDER = {
  cyan: "border-cyan-500/30",
  violet: "border-violet-500/30",
};

const FEATURE_HOVER_BG = {
  cyan: "group-hover:bg-cyan-500/30",
  violet: "group-hover:bg-violet-500/30",
};

/**
 * AuthModal Component
 * Central authentication modal that manages all auth forms and view switching
 * Handles state management for the entire authentication flow
 */
export const AuthModal = ({ isOpen, onClose, initialView = "login", resetToken = null }) => {
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

  // Handle successful login
  const handleLoginSuccess = () => {
    if (onClose) onClose();
  };

  // Handle successful registration
  const handleRegistrationSuccess = (email) => {
    setUserEmail(email);
    setCurrentView("registration-success");
  };

  // Handle successful forgot password request
  const handleForgotPasswordSuccess = (email) => {
    setUserEmail(email);
    setCurrentView("forgot-password-success");
  };

  // Handle successful password reset
  const handlePasswordResetSuccess = () => {
    setCurrentView("login");
    toast.success("Password reset successfully! Please log in with your new password.");
  };

  // Don't render if modal is closed
  if (!isOpen) return null;

  // Dynamic branding content based on current view
  const getBrandingContent = () => {
    switch (currentView) {
      case "login":
        return {
          title: "Welcome Back!",
          subtitle: "Continue Your Security Journey",
          features: [
            {
              icon: <BoltIcon className="h-6 w-6 text-cyan-400" />,
              title: "Instant Access",
              description: "Resume scanning and monitoring your projects",
              color: "cyan",
            },
            {
              icon: <ChartBarIcon className="h-6 w-6 text-violet-400" />,
              title: "Real-time Analytics",
              description: "View latest security insights and reports",
              color: "violet",
            },
            {
              icon: <ShieldCheckIcon className="h-6 w-6 text-cyan-300" />,
              title: "Active Protection",
              description: "Your projects are continuously monitored",
              color: "cyan",
            },
          ],
        };
      case "register":
        return {
          title: "Start Securing Today",
          subtitle: "Join 500+ Organizations",
          features: [
            {
              icon: <SparklesIcon className="h-6 w-6 text-cyan-400" />,
              title: "Free Forever Plan",
              description: "Get started with unlimited scans and AI analysis",
              color: "cyan",
            },
            {
              icon: <CodeBracketIcon className="h-6 w-6 text-violet-400" />,
              title: "Multi-Language Support",
              description: "Python, JavaScript, Java, C++, and 15+ more",
              color: "violet",
            },
            {
              icon: <LockClosedIcon className="h-6 w-6 text-cyan-300" />,
              title: "Enterprise Security",
              description: "SOC 2, GDPR, and HIPAA compliant platform",
              color: "cyan",
            },
          ],
        };
      case "forgot-password":
      case "reset-password":
        return {
          title: "Secure Recovery",
          subtitle: "Your Security Matters",
          features: [
            {
              icon: <ShieldCheckIcon className="h-6 w-6 text-cyan-400" />,
              title: "Encrypted Process",
              description: "End-to-end encrypted password reset",
              color: "cyan",
            },
            {
              icon: <ServerIcon className="h-6 w-6 text-violet-400" />,
              title: "Zero Knowledge",
              description: "We never see or store your password",
              color: "violet",
            },
            {
              icon: <BoltIcon className="h-6 w-6 text-cyan-300" />,
              title: "Instant Reset",
              description: "Regain access in under 2 minutes",
              color: "cyan",
            },
          ],
        };
      default:
        return {
          title: "ONYX",
          subtitle: "Security Intelligence Platform",
          features: [
            {
              icon: <BoltIcon className="h-6 w-6 text-cyan-400" />,
              title: "Real-time Scanning",
              description: "Instant vulnerability detection",
              color: "cyan",
            },
            {
              icon: <SparklesIcon className="h-6 w-6 text-violet-400" />,
              title: "AI-Powered",
              description: "Intelligent threat detection",
              color: "violet",
            },
            {
              icon: <ShieldCheckIcon className="h-6 w-6 text-cyan-300" />,
              title: "Compliance Ready",
              description: "OWASP, PCI-DSS, HIPAA support",
              color: "cyan",
            },
          ],
        };
    }
  };

  const branding = getBrandingContent();

  // Render the appropriate form based on current view
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
    <div className="fixed inset-0 z-50 overflow-hidden bg-gray-950">
      {/* Animated gradient orb (subtle) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-cyan-500/10 via-violet-500/10 to-transparent rounded-full blur-3xl animate-pulse"
          style={{ animationDuration: "8s" }}
        />
        <div
          className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-violet-500/10 via-cyan-500/10 to-transparent rounded-full blur-3xl animate-pulse"
          style={{ animationDuration: "12s", animationDelay: "2s" }}
        />
      </div>

      {/* Split Screen Layout */}
      <div className="flex h-full">
        {/* Left Side - Branding & Features */}
        <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
          {/* Animated Background */}
          <div className="absolute inset-0">
            <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-cyan-500/20 via-violet-500/20 to-cyan-500/20 rounded-full blur-3xl animate-pulse" />
            <div
              className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-violet-500/20 via-cyan-500/20 to-violet-500/20 rounded-full blur-3xl animate-pulse"
              style={{ animationDelay: "2s" }}
            />
          </div>

          {/* Content */}
          <div className="relative z-10 flex flex-col justify-center px-12 xl:px-16 text-white">
            {/* Logo & Title */}
            <div className="mb-12">
              <div className="flex items-center gap-4 mb-4">
                <OnyxLogo variant="default" className="w-16 h-16" />
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent animate-gradient">
                    {branding.title}
                  </h1>
                  <p className="text-cyan-200 text-sm">{branding.subtitle}</p>
                </div>
              </div>
              <p className="text-xl text-gray-300 leading-relaxed">
                {currentView === "login"
                  ? "Secure your applications with AI-powered vulnerability detection"
                  : currentView === "register"
                    ? "Start protecting your code in less than 2 minutes"
                    : "We'll help you regain access to your account securely"}
              </p>
            </div>

            {/* Dynamic Features Grid */}
            <div className="space-y-6">
              {branding.features.map((feature, index) => (
                <div
                  key={index}
                  className="flex items-start gap-4 group cursor-pointer transform transition-all duration-300 hover:translate-x-2"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div
                    className={`p-3 ${FEATURE_BG[feature.color] || "bg-cyan-500/20"} ${FEATURE_BORDER[feature.color] || "border-cyan-500/30"} ${FEATURE_HOVER_BG[feature.color] || "group-hover:bg-cyan-500/30"} rounded-xl border transition-colors`}
                  >
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-1">{feature.title}</h3>
                    <p className="text-gray-400 text-sm">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Stats */}
            <div className="mt-12 grid grid-cols-3 gap-6">
              <div className="text-center group hover:scale-105 transition-transform">
                <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-300 bg-clip-text text-transparent group-hover:from-cyan-300 group-hover:to-cyan-400 transition-all">
                  99.9%
                </div>
                <div className="text-sm text-gray-400 mt-1 group-hover:text-gray-300">Uptime</div>
              </div>
              <div className="text-center group hover:scale-105 transition-transform">
                <div className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-violet-300 bg-clip-text text-transparent group-hover:from-violet-300 group-hover:to-violet-400 transition-all">
                  10K+
                </div>
                <div className="text-sm text-gray-400 mt-1 group-hover:text-gray-300">
                  Scans Daily
                </div>
              </div>
              <div className="text-center group hover:scale-105 transition-transform">
                <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent group-hover:from-violet-400 group-hover:to-cyan-400 transition-all">
                  500+
                </div>
                <div className="text-sm text-gray-400 mt-1 group-hover:text-gray-300">
                  Enterprises
                </div>
              </div>
            </div>

            {/* Platform Highlight */}
            {currentView === "register" && (
              <div className="mt-8 p-4 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-cyan-500/20">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-400 to-violet-500 flex items-center justify-center text-white">
                      <ShieldCheckIcon className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-300 mb-2">
                      <span className="font-semibold text-white">
                        Enterprise-grade security scanning
                      </span>{" "}
                      with 12+ integrated scanners covering SAST, secrets detection, container
                      security, and more.
                    </p>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <CheckCircleIcon className="w-3 h-3 text-cyan-400" />
                        Free tier available
                      </span>
                      <span className="flex items-center gap-1">
                        <CheckCircleIcon className="w-3 h-3 text-cyan-400" />
                        No credit card required
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Auth Form */}
        <div className="w-full lg:w-1/2 relative overflow-y-auto">
          {/* Mobile Logo (visible on small screens) */}
          <div className="lg:hidden p-6 text-center bg-gradient-to-r from-gray-950/50 to-gray-900/50 backdrop-blur-xl border-b border-gray-800/50">
            <div className="inline-flex items-center gap-3 mb-2">
              <OnyxLogo variant="mini" className="w-10 h-10" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                ONYX
              </h1>
            </div>
            <p className="text-xs text-gray-400 tracking-widest uppercase">Security Intelligence</p>
          </div>

          {/* Form Container */}
          <div className="flex items-center justify-center min-h-full p-6 lg:p-12">
            <div className="w-full max-w-md">
              <div className="relative bg-gray-900/60 backdrop-blur-2xl border border-gray-700/40 rounded-2xl shadow-2xl shadow-cyan-500/5 overflow-hidden">
                {/* Gradient Background Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-violet-500/5 to-cyan-500/5" />

                {/* Content */}
                <div className="relative">{renderCurrentView()}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Close Button (Top Right) */}
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 bg-gray-800/50 hover:bg-violet-500/20 rounded-full transition-colors z-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
          aria-label="Close"
        >
          <XMarkIcon className="w-6 h-6 text-gray-400 hover:text-white" />
        </button>
      )}
    </div>
  );
};
